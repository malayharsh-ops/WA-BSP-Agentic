from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func, Boolean
from sqlalchemy.orm import mapped_column, Mapped, relationship
from .base import Base, gen_uuid


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(200))
    language: Mapped[str] = mapped_column(String(10), default="en")

    # Qualification
    stage: Mapped[str] = mapped_column(String(20), default="NEW")
    # NEW | WARM | HOT | DISQUALIFIED
    score: Mapped[int] = mapped_column(Integer, default=0)

    # Collected data (stored as JSON-ish columns for simplicity)
    project_type: Mapped[str | None] = mapped_column(String(50))
    project_location: Mapped[str | None] = mapped_column(String(200))
    material_needed: Mapped[str | None] = mapped_column(String(200))
    volume_mt: Mapped[str | None] = mapped_column(String(50))
    timeline_days: Mapped[int | None] = mapped_column(Integer)
    is_decision_maker: Mapped[bool | None] = mapped_column(Boolean)

    # Salesforce
    sf_opportunity_id: Mapped[str | None] = mapped_column(String(100))
    sf_synced_at: Mapped[datetime | None] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    conversations: Mapped[list["Conversation"]] = relationship("Conversation", back_populates="lead")  # noqa
