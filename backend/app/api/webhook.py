"""
Meta WhatsApp Cloud API webhook.

GET  /webhook  — verify token challenge
POST /webhook  — inbound message events
"""

import hashlib
import hmac
import logging
from fastapi import APIRouter, Request, Response, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.models import Lead, Conversation, Message, HandoffQueue
from app.agent import run_priya, detect_language, stage_from_score
from app.services.redis_session import session_store
from app.services.whatsapp import wa_client

router = APIRouter(prefix="/webhook", tags=["webhook"])
logger = logging.getLogger(__name__)


@router.get("")
async def verify_webhook(request: Request):
    """Meta webhook verification (GET challenge)."""
    params = request.query_params
    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == settings.meta_verify_token
    ):
        return Response(content=params.get("hub.challenge", ""), media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("")
async def receive_message(request: Request, db: AsyncSession = Depends(get_db)):
    """Process inbound WhatsApp message events."""
    body = await request.body()
    _verify_signature(request, body)

    data = await request.json()
    entry = data.get("entry", [{}])[0]
    changes = entry.get("changes", [{}])[0]
    value = changes.get("value", {})

    # Handle status updates (delivered, read) — ack and return
    if value.get("statuses"):
        return {"status": "ok"}

    messages = value.get("messages", [])
    if not messages:
        return {"status": "ok"}

    msg = messages[0]
    if msg.get("type") != "text":
        # Non-text messages — acknowledge only
        return {"status": "ok"}

    phone = msg["from"]
    text = msg["text"]["body"]
    wa_msg_id = msg["id"]

    # Mark as read immediately
    try:
        await wa_client.mark_read(wa_msg_id)
    except Exception:
        pass

    # Get or create Lead
    lead = await _get_or_create_lead(db, phone)

    # Get or create active Conversation
    conversation = await _get_or_create_conversation(db, lead.id)

    # Persist inbound message
    inbound = Message(
        conversation_id=conversation.id,
        direction="IN",
        body=text,
        wa_message_id=wa_msg_id,
    )
    db.add(inbound)
    await db.flush()

    # Load session from Redis
    session = await session_store.get(phone)

    # Detect and persist language on first message
    if not session.get("language") or session["language"] == "hi":
        session["language"] = detect_language(text)
        lead.language = session["language"]

    # Block if conversation is handed off — don't run the bot
    if conversation.status == "HANDED_OFF":
        await db.commit()
        return {"status": "ok"}

    # Run Priya
    try:
        reply, should_handoff = await run_priya(phone, text, session)
    except Exception as e:
        logger.error(f"Priya failed for {phone}: {e}")
        reply = "Maafi chahti hun, ek baar phir try karein."
        should_handoff = False

    # Persist outbound message
    outbound = Message(
        conversation_id=conversation.id,
        direction="OUT",
        body=reply,
    )
    db.add(outbound)

    # Update lead score/stage
    score = session.get("score", 0)
    lead.score = score
    lead.stage = stage_from_score(score)

    # Persist collected fields
    collected = session.get("collected", {})
    for field in ("project_type", "project_location", "material_needed", "volume_mt", "is_decision_maker"):
        if collected.get(field) is not None:
            setattr(lead, field, collected[field])
    if collected.get("timeline_days") is not None:
        lead.timeline_days = collected["timeline_days"]

    # Trigger handoff if needed
    if should_handoff and conversation.status == "ACTIVE":
        conversation.status = "HANDED_OFF"
        trigger_reason = "LOOP_ESCALATION" if session.get("loop_escalated") else "HIGH_SCORE"
        handoff = HandoffQueue(
            conversation_id=conversation.id,
            trigger_reason=trigger_reason,
        )
        db.add(handoff)

    await db.commit()
    await session_store.save(phone, session)

    # Send reply
    try:
        await wa_client.send_text(phone, reply)
    except Exception as e:
        logger.error(f"Failed to send WA message to {phone}: {e}")

    return {"status": "ok"}


async def _get_or_create_lead(db: AsyncSession, phone: str) -> Lead:
    result = await db.execute(select(Lead).where(Lead.phone == phone))
    lead = result.scalar_one_or_none()
    if not lead:
        lead = Lead(phone=phone)
        db.add(lead)
        await db.flush()
    return lead


async def _get_or_create_conversation(db: AsyncSession, lead_id: str) -> Conversation:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.lead_id == lead_id)
        .where(Conversation.status.in_(["ACTIVE", "HANDED_OFF"]))
        .order_by(Conversation.created_at.desc())
    )
    conv = result.scalar_one_or_none()
    if not conv:
        conv = Conversation(lead_id=lead_id)
        db.add(conv)
        await db.flush()
    return conv


def _verify_signature(request: Request, body: bytes) -> None:
    """Verify Meta X-Hub-Signature-256 header."""
    if not settings.meta_app_secret:
        return  # Skip in development
    sig_header = request.headers.get("X-Hub-Signature-256", "")
    if not sig_header.startswith("sha256="):
        raise HTTPException(status_code=403, detail="Missing signature")
    expected = "sha256=" + hmac.new(
        settings.meta_app_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(sig_header, expected):
        raise HTTPException(status_code=403, detail="Invalid signature")
