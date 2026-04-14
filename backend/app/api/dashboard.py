"""
Dashboard analytics API.
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case

from app.database import get_db
from app.models import Lead, Conversation, HandoffQueue, Message

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/metrics")
async def get_metrics(
    days: int = Query(default=7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)

    # Total leads in period
    total_leads = await db.scalar(
        select(func.count(Lead.id)).where(Lead.created_at >= since)
    )

    # Leads by stage
    stage_rows = await db.execute(
        select(Lead.stage, func.count(Lead.id))
        .where(Lead.created_at >= since)
        .group_by(Lead.stage)
    )
    by_stage = {row[0]: row[1] for row in stage_rows}

    # Total handoffs triggered
    total_handoffs = await db.scalar(
        select(func.count(HandoffQueue.id)).where(HandoffQueue.triggered_at >= since)
    )

    # Handoffs accepted within SLA (30 min)
    sla_ok = await db.scalar(
        select(func.count(HandoffQueue.id)).where(
            HandoffQueue.triggered_at >= since,
            HandoffQueue.accepted_at.isnot(None),
            (HandoffQueue.accepted_at - HandoffQueue.triggered_at)
            <= timedelta(minutes=30),
        )
    )

    # Avg qualification score
    avg_score = await db.scalar(
        select(func.avg(Lead.score)).where(Lead.created_at >= since)
    )

    return {
        "period_days": days,
        "total_leads": total_leads or 0,
        "by_stage": by_stage,
        "hot_rate_pct": round(
            (by_stage.get("HOT", 0) / max(total_leads or 1, 1)) * 100, 1
        ),
        "total_handoffs": total_handoffs or 0,
        "sla_met": sla_ok or 0,
        "avg_score": round(float(avg_score or 0), 1),
    }


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    msgs = result.scalars().all()
    return [
        {
            "id": m.id,
            "direction": m.direction,
            "body": m.body,
            "created_at": m.created_at.isoformat(),
        }
        for m in msgs
    ]


@router.get("/leads")
async def list_leads(
    stage: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(Lead).order_by(Lead.score.desc()).limit(limit).offset(offset)
    if stage:
        q = q.where(Lead.stage == stage)
    result = await db.execute(q)
    leads = result.scalars().all()
    return [
        {
            "id": l.id,
            "phone": l.phone,
            "name": l.name,
            "language": l.language,
            "stage": l.stage,
            "score": l.score,
            "project_type": l.project_type,
            "project_location": l.project_location,
            "material_needed": l.material_needed,
            "volume_mt": l.volume_mt,
            "sf_opportunity_id": l.sf_opportunity_id,
            "created_at": l.created_at.isoformat(),
        }
        for l in leads
    ]
