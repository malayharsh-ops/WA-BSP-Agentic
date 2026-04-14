"""
Handoff queue API — for the React dashboard.

GET  /handoff/queue       — list pending handoffs
POST /handoff/{id}/accept — agent accepts a handoff
POST /handoff/{id}/resolve — agent resolves a handoff
POST /handoff/{id}/send   — agent sends a message in a handed-off conversation
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import HandoffQueue, Conversation, Message, Lead
from app.services.whatsapp import wa_client

router = APIRouter(prefix="/handoff", tags=["handoff"])


class AcceptBody(BaseModel):
    agent_id: str


class ResolveBody(BaseModel):
    agent_id: str
    notes: str = ""


class SendBody(BaseModel):
    agent_id: str
    body: str


@router.get("/queue")
async def list_queue(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(HandoffQueue)
        .where(HandoffQueue.resolved_at.is_(None))
        .options(
            selectinload(HandoffQueue.conversation).selectinload(Conversation.lead),
        )
        .order_by(HandoffQueue.triggered_at.asc())
    )
    items = result.scalars().all()
    return [_serialize_handoff(h) for h in items]


@router.post("/{handoff_id}/accept")
async def accept_handoff(handoff_id: str, body: AcceptBody, db: AsyncSession = Depends(get_db)):
    h = await _get_handoff(db, handoff_id)
    if h.accepted_at:
        raise HTTPException(400, "Already accepted")
    h.accepted_at = datetime.utcnow()
    h.agent_id = body.agent_id
    await db.commit()
    return {"status": "accepted"}


@router.post("/{handoff_id}/resolve")
async def resolve_handoff(handoff_id: str, body: ResolveBody, db: AsyncSession = Depends(get_db)):
    h = await _get_handoff(db, handoff_id)
    h.resolved_at = datetime.utcnow()
    h.resolution_notes = body.notes
    h.agent_id = body.agent_id
    h.conversation.status = "CLOSED"
    await db.commit()

    # Kick off Salesforce sync via Celery
    try:
        from app.workers.followup_tasks import sync_opportunity_task
        sync_opportunity_task.delay(h.conversation.lead_id, str(h.conversation.id))
    except Exception:
        pass

    return {"status": "resolved"}


@router.post("/{handoff_id}/send")
async def agent_send(handoff_id: str, body: SendBody, db: AsyncSession = Depends(get_db)):
    """Agent sends a free-text message in a handed-off conversation."""
    h = await _get_handoff(db, handoff_id)
    conv = h.conversation
    lead = conv.lead

    msg = Message(conversation_id=conv.id, direction="OUT", body=body.body)
    db.add(msg)
    await db.commit()

    await wa_client.send_text(lead.phone, body.body)
    return {"status": "sent"}


async def _get_handoff(db: AsyncSession, handoff_id: str) -> HandoffQueue:
    result = await db.execute(
        select(HandoffQueue)
        .where(HandoffQueue.id == handoff_id)
        .options(
            selectinload(HandoffQueue.conversation).selectinload(Conversation.lead),
        )
    )
    h = result.scalar_one_or_none()
    if not h:
        raise HTTPException(404, "Handoff not found")
    return h


def _serialize_handoff(h: HandoffQueue) -> dict:
    lead = h.conversation.lead
    return {
        "id": h.id,
        "trigger_reason": h.trigger_reason,
        "triggered_at": h.triggered_at.isoformat(),
        "accepted_at": h.accepted_at.isoformat() if h.accepted_at else None,
        "resolved_at": h.resolved_at.isoformat() if h.resolved_at else None,
        "agent_id": h.agent_id,
        "conversation_id": h.conversation_id,
        "lead": {
            "id": lead.id,
            "phone": lead.phone,
            "name": lead.name,
            "language": lead.language,
            "stage": lead.stage,
            "score": lead.score,
            "project_type": lead.project_type,
            "project_location": lead.project_location,
            "material_needed": lead.material_needed,
            "volume_mt": lead.volume_mt,
        },
    }
