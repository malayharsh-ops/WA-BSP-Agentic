from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import mapped_column, Mapped, relationship
from .base import Base, gen_uuid


class HandoffQueue(Base):
    __tablename__ = "handoff_queue"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id"), nullable=False, unique=True, index=True)
    agent_id: Mapped[str | None] = mapped_column(String(36))
    trigger_reason: Mapped[str] = mapped_column(String(50))
    # HIGH_SCORE | CUSTOMER_REQUEST | LOOP_ESCALATION

    triggered_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    resolution_notes: Mapped[str | None] = mapped_column(Text)

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="handoff")  # noqa
