"""
Celery tasks for follow-ups and Salesforce sync.
"""

import asyncio
import logging
from datetime import datetime

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=5, default_retry_delay=300)
def sync_opportunity_task(self, lead_id: str, conversation_id: str):
    """Create/update Salesforce Opportunity after handoff resolution."""
    asyncio.run(_sync_opportunity(lead_id, conversation_id))


async def _sync_opportunity(lead_id: str, conversation_id: str):
    from app.database import AsyncSessionLocal
    from app.models import Lead
    from app.services.salesforce import sf_client
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Lead).where(Lead.id == lead_id))
        lead = result.scalar_one_or_none()
        if not lead:
            return

        lead_data = {
            "phone": lead.phone,
            "name": lead.name,
            "score": lead.score,
            "project_type": lead.project_type,
            "project_location": lead.project_location,
            "material_needed": lead.material_needed,
            "volume_mt": lead.volume_mt,
            "conversation_id": conversation_id,
        }
        sf_id = sf_client.upsert_opportunity(lead_data)
        if sf_id:
            lead.sf_opportunity_id = sf_id
            lead.sf_synced_at = datetime.utcnow()
            await db.commit()
            logger.info(f"SF sync OK for lead {lead_id}: {sf_id}")
        else:
            logger.warning(f"SF sync returned no ID for lead {lead_id}")


@celery_app.task
def retry_failed_sf_syncs():
    """Retry Salesforce syncs for resolved handoffs without an SF ID."""
    asyncio.run(_retry_failed())


async def _retry_failed():
    from app.database import AsyncSessionLocal
    from app.models import HandoffQueue, Lead, Conversation
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(HandoffQueue)
            .where(
                HandoffQueue.resolved_at.isnot(None),
            )
            .options(
                selectinload(HandoffQueue.conversation).selectinload(Conversation.lead)
            )
        )
        handoffs = result.scalars().all()
        for h in handoffs:
            lead = h.conversation.lead
            if not lead.sf_opportunity_id:
                sync_opportunity_task.delay(lead.id, h.conversation_id)
