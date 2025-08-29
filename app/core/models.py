
from typing import Optional
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, func
from .db import Base

class Incident(Base):
    __tablename__ = "incidents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    cluster_key: Mapped[str] = mapped_column(String(255), index=True)
    summary: Mapped[str] = mapped_column(Text)
    count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="open")
    last_seen: Mapped["DateTime"] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    events = relationship("Event", back_populates="incident")

class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(100), index=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    raw: Mapped[str] = mapped_column(Text)
    normalized: Mapped[str] = mapped_column(Text)
    redacted: Mapped[str] = mapped_column(Text)
    residency_tag: Mapped[str] = mapped_column(String(4))
    cluster_key: Mapped[str] = mapped_column(String(255), index=True)
    created_at: Mapped["DateTime"] = mapped_column(DateTime, server_default=func.now())
    incident_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("incidents.id"), index=True, nullable=True)
    incident = relationship("Incident", back_populates="events")

class Approval(Base):
    __tablename__ = "approvals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    incident_id: Mapped[int] = mapped_column(Integer, ForeignKey("incidents.id"), index=True)
    action_name: Mapped[str] = mapped_column(String(255))
    approved_by: Mapped[str] = mapped_column(String(100), default="human@operator")
    approved_at: Mapped["DateTime"] = mapped_column(DateTime, server_default=func.now())
    notes: Mapped[str] = mapped_column(Text, default="")
