import uuid
from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Date, Text, Integer, DateTime, ForeignKey

from app.database.base import Base


class ASHAEncounter(Base):
    __tablename__ = "HRMS_asha_encounters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id: Mapped[str] = mapped_column(String(255), ForeignKey("HRMS_employees.id", ondelete="CASCADE"), nullable=False, index=True)
    asha_name: Mapped[str] = mapped_column(String(255), nullable=False)
    village: Mapped[str] = mapped_column(String(255), nullable=False)
    encounter_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False, index=True)
    referrals_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    hospital_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    employee: Mapped["Employee"] = relationship("Employee", backref="asha_encounters")
