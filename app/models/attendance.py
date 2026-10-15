import uuid
from datetime import date, time, datetime, timezone
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Date, Time, Text, Integer, DateTime, ForeignKey, UniqueConstraint

from app.database.base import Base


class Attendance(Base):
    __tablename__ = "HRMS_attendance"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id: Mapped[str] = mapped_column(String(255), ForeignKey("HRMS_employees.id", ondelete="CASCADE"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(100), nullable=False)  # 'present' | 'absent' | 'half-day' | 'leave' | etc.
    check_in_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    check_out_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    check_in_location: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    check_in_lat_lng: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    check_in_photo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    check_out_photo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    punch_type: Mapped[Optional[str]] = mapped_column(String(50), default="in_office", nullable=True)  # 'in_office' | 'out_of_office'
    punch_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    session_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    employee: Mapped["Employee"] = relationship("Employee", backref="attendances")

    __table_args__ = (
        UniqueConstraint("employee_id", "date", "session_number", name="unique_employee_date_session"),
    )
