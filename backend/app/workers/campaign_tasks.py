"""
Celery tasks for campaign delivery.
"""

import asyncio
import logging
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.workers.celery_app import celery_app
from app.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_campaign_task(self, campaign_id: str):
    """Send template messages to all contacts in a campaign."""
    asyncio.run(_send_campaign(campaign_id))


async def _send_campaign(campaign_id: str):
    from app.database import AsyncSessionLocal
    from app.models import Campaign, CampaignContact, Lead
    from app.services.whatsapp import wa_client

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(CampaignContact)
            .join(Lead, CampaignContact.lead_id == Lead.id)
            .where(CampaignContact.campaign_id == campaign_id)
            .where(CampaignContact.sent_at.is_(None))
            .where(CampaignContact.failed_at.is_(None))
        )
        contacts = result.scalars().all()

        campaign_result = await db.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )
        campaign = campaign_result.scalar_one_or_none()
        if not campaign:
            return

        for cc in contacts:
            lead_result = await db.execute(select(Lead).where(Lead.id == cc.lead_id))
            lead = lead_result.scalar_one_or_none()
            if not lead:
                continue
            try:
                await wa_client.send_template(
                    to=lead.phone,
                    template_name=campaign.template_name,
                    language_code=campaign.language,
                )
                cc.sent_at = datetime.utcnow()
            except Exception as e:
                logger.error(f"Template send failed for {lead.phone}: {e}")
                cc.failed_at = datetime.utcnow()
                cc.error_message = str(e)[:500]

        campaign.status = "COMPLETED"
        campaign.completed_at = datetime.utcnow()
        await db.commit()


@celery_app.task
def dispatch_scheduled_campaigns():
    """Check for campaigns that are due and kick them off."""
    asyncio.run(_dispatch_scheduled())


async def _dispatch_scheduled():
    from app.database import AsyncSessionLocal
    from app.models import Campaign

    async with AsyncSessionLocal() as db:
        now = datetime.utcnow()
        result = await db.execute(
            select(Campaign).where(
                Campaign.status == "SCHEDULED",
                Campaign.scheduled_at <= now,
            )
        )
        campaigns = result.scalars().all()
        for c in campaigns:
            c.status = "RUNNING"
            c.started_at = now
            send_campaign_task.delay(c.id)
        await db.commit()
