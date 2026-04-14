from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey, Text, Integer
from sqlalchemy.orm import mapped_column, Mapped, relationship
from .base import Base, gen_uuid


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    template_name: Mapped[str] = mapped_column(String(100), nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en")
    status: Mapped[str] = mapped_column(String(20), default="DRAFT")
    # DRAFT | SCHEDULED | RUNNING | COMPLETED | FAILED
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_by: Mapped[str | None] = mapped_column(String(36))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    contacts: Mapped[list["CampaignContact"]] = relationship("CampaignContact", back_populates="campaign")


class CampaignContact(Base):
    __tablename__ = "campaign_contacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("campaigns.id"), nullable=False, index=True)
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id"), nullable=False)

    sent_at: Mapped[datetime | None] = mapped_column(DateTime)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime)
    replied_at: Mapped[datetime | None] = mapped_column(DateTime)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime)
    error_message: Mapped[str | None] = mapped_column(Text)

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="contacts")
