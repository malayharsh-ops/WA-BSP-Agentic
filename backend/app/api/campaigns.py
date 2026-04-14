"""
Campaign CRUD and send trigger.
"""

import csv
import io
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Campaign, CampaignContact, Lead

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


class CampaignCreate(BaseModel):
    name: str
    template_name: str
    language: str = "en"
    scheduled_at: datetime | None = None


@router.get("")
async def list_campaigns(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Campaign).order_by(Campaign.created_at.desc()).limit(100)
    )
    campaigns = result.scalars().all()
    return [_serialize(c) for c in campaigns]


@router.post("")
async def create_campaign(body: CampaignCreate, db: AsyncSession = Depends(get_db)):
    c = Campaign(**body.model_dump())
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return _serialize(c)


@router.post("/{campaign_id}/contacts")
async def upload_contacts(
    campaign_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a CSV of phone numbers (column: phone).
    Auto-creates Lead records if they don't exist.
    """
    campaign = await _get_campaign(db, campaign_id)
    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))

    added = 0
    for row in reader:
        phone = (row.get("phone") or "").strip()
        if not phone:
            continue
        # Get or create lead
        result = await db.execute(select(Lead).where(Lead.phone == phone))
        lead = result.scalar_one_or_none()
        if not lead:
            lead = Lead(phone=phone, name=row.get("name", ""))
            db.add(lead)
            await db.flush()

        contact = CampaignContact(campaign_id=campaign.id, lead_id=lead.id)
        db.add(contact)
        added += 1

    await db.commit()
    return {"added": added}


@router.post("/{campaign_id}/send")
async def send_campaign(campaign_id: str, db: AsyncSession = Depends(get_db)):
    """Enqueue campaign send via Celery."""
    campaign = await _get_campaign(db, campaign_id)
    if campaign.status not in ("DRAFT", "SCHEDULED"):
        raise HTTPException(400, f"Cannot send campaign in status: {campaign.status}")

    campaign.status = "RUNNING"
    campaign.started_at = datetime.utcnow()
    await db.commit()

    from app.workers.campaign_tasks import send_campaign_task
    send_campaign_task.delay(campaign_id)

    return {"status": "queued", "campaign_id": campaign_id}


@router.get("/{campaign_id}/stats")
async def campaign_stats(campaign_id: str, db: AsyncSession = Depends(get_db)):
    await _get_campaign(db, campaign_id)
    total = await db.scalar(
        select(func.count(CampaignContact.id)).where(CampaignContact.campaign_id == campaign_id)
    )
    sent = await db.scalar(
        select(func.count(CampaignContact.id)).where(
            CampaignContact.campaign_id == campaign_id,
            CampaignContact.sent_at.isnot(None),
        )
    )
    delivered = await db.scalar(
        select(func.count(CampaignContact.id)).where(
            CampaignContact.campaign_id == campaign_id,
            CampaignContact.delivered_at.isnot(None),
        )
    )
    replied = await db.scalar(
        select(func.count(CampaignContact.id)).where(
            CampaignContact.campaign_id == campaign_id,
            CampaignContact.replied_at.isnot(None),
        )
    )
    failed = await db.scalar(
        select(func.count(CampaignContact.id)).where(
            CampaignContact.campaign_id == campaign_id,
            CampaignContact.failed_at.isnot(None),
        )
    )
    return {
        "total": total or 0,
        "sent": sent or 0,
        "delivered": delivered or 0,
        "replied": replied or 0,
        "failed": failed or 0,
    }


async def _get_campaign(db: AsyncSession, campaign_id: str) -> Campaign:
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Campaign not found")
    return c


def _serialize(c: Campaign) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "template_name": c.template_name,
        "language": c.language,
        "status": c.status,
        "scheduled_at": c.scheduled_at.isoformat() if c.scheduled_at else None,
        "started_at": c.started_at.isoformat() if c.started_at else None,
        "completed_at": c.completed_at.isoformat() if c.completed_at else None,
        "created_at": c.created_at.isoformat(),
    }
