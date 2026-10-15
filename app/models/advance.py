import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Numeric, Integer, Text, DateTime, ForeignKey

from app.database.base import Base


class AdvanceRequest(Base):
    __tablename__ = "HRMS_advance_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id: Mapped[str] = mapped_column(String(255), ForeignKey("HRMS_employees.id", ondelete="CASCADE"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    advance_type: Mapped[str] = mapped_column(String(50), default="salary", nullable=False)  # 'salary' | 'medical'
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # 'pending' | 'approved' | 'rejected' | 'deducted'
    repayment_months: Mapped[int] = mapped_column(Integer, default=2, nullable=False)  # 2 | 3 | 5
    monthly_installment: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    installments_remaining: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    deducted_in_month: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # 'YYYY-MM'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    employee: Mapped["Employee"] = relationship("Employee", backref="advance_requests")
