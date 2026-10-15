import uuid
from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Date, Text, Integer, DateTime, ForeignKey, UniqueConstraint

from app.database.base import Base


class LeaveRequest(Base):
    __tablename__ = "HRMS_leave_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id: Mapped[str] = mapped_column(String(255), ForeignKey("HRMS_employees.id", ondelete="CASCADE"), nullable=False, index=True)
    leave_type: Mapped[str] = mapped_column(String(100), nullable=False)  # 'sick' | 'casual' | 'maternity' | 'paternity' | 'monthly'
    from_date: Mapped[date] = mapped_column(Date, nullable=False)
    to_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # 'pending' | 'approved' | 'rejected'
    submitted_at: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    admin_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    employee: Mapped["Employee"] = relationship("Employee", backref="leave_requests")


class LeaveBalance(Base):
    __tablename__ = "HRMS_leave_balances"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id: Mapped[str] = mapped_column(String(255), ForeignKey("HRMS_employees.id", ondelete="CASCADE"), nullable=False, index=True)
    leave_type: Mapped[str] = mapped_column(String(100), nullable=False)  # 'sick' | 'casual' | 'maternity' | 'paternity'
    total_allotted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("employee_id", "leave_type", name="unique_employee_leave_type"),
    )


class MonthlyLeaveQuota(Base):
    __tablename__ = "HRMS_monthly_leave_quota"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id: Mapped[str] = mapped_column(String(255), ForeignKey("HRMS_employees.id", ondelete="CASCADE"), nullable=False, index=True)
    month: Mapped[str] = mapped_column(String(7), nullable=False)  # 'YYYY-MM'
    allotted: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("employee_id", "month", name="unique_emp_month"),
    )


class MissedPunch(Base):
    __tablename__ = "HRMS_missed_punches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id: Mapped[str] = mapped_column(String(255), ForeignKey("HRMS_employees.id", ondelete="CASCADE"), nullable=False, index=True)
    missed_date: Mapped[date] = mapped_column(Date, nullable=False)
    punch_type: Mapped[str] = mapped_column(String(10), nullable=False)  # 'in' | 'out'
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    admin_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
