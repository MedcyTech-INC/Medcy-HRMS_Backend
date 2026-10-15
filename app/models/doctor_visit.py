import uuid
from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Date, Text, Numeric, DateTime, ForeignKey

from app.database.base import Base


class DoctorVisit(Base):
    __tablename__ = "HRMS_doctor_visits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id: Mapped[str] = mapped_column(String(255), ForeignKey("HRMS_employees.id", ondelete="CASCADE"), nullable=False, index=True)
    visit_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    doctor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    clinic_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    area: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    time_slot: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    visit_purpose: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="planned", nullable=False)  # 'planned' | 'completed' | 'missed' | 'rescheduled'
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approval_status: Mapped[Optional[str]] = mapped_column(String(50), default="pending", nullable=True)  # 'pending' | 'approved' | 'post_review' | 'rejected'
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    employee: Mapped["Employee"] = relationship("Employee", backref="doctor_visits")
