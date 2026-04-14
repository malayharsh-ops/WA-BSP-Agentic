from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import mapped_column, Mapped, relationship
from .base import Base, gen_uuid


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id"), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(20), default="whatsapp")
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    # ACTIVE | PAUSED | HANDED_OFF | CLOSED

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    lead: Mapped["Lead"] = relationship("Lead", back_populates="conversations")  # noqa
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="conversation", order_by="Message.created_at")
    handoff: Mapped["HandoffQueue | None"] = relationship("HandoffQueue", back_populates="conversation", uselist=False)  # noqa


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id"), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(3))  # IN | OUT
    body: Mapped[str] = mapped_column(Text)
    template_name: Mapped[str | None] = mapped_column(String(100))
    wa_message_id: Mapped[str | None] = mapped_column(String(100))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
