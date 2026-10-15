import uuid
from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Date, Text, DateTime, ForeignKey

from app.database.base import Base


class Task(Base):
    __tablename__ = "HRMS_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(50), default="medium", nullable=False)  # 'low' | 'medium' | 'high' | 'urgent'
    status: Mapped[str] = mapped_column(String(50), default="in_progress", nullable=False)  # 'in_progress' | 'completed' | 'incomplete'
    assigned_to: Mapped[Optional[str]] = mapped_column(String(255), ForeignKey("HRMS_employees.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(255), ForeignKey("HRMS_employees.id", ondelete="SET NULL"), nullable=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, default="", nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    assignee: Mapped[Optional["Employee"]] = relationship("Employee", foreign_keys=[assigned_to], backref="assigned_tasks")
    creator: Mapped[Optional["Employee"]] = relationship("Employee", foreign_keys=[created_by], backref="created_tasks")
