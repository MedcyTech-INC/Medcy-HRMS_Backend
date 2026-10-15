import uuid
from datetime import date, datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Date, Text, Numeric, Boolean, DateTime, JSON, ForeignKey, UniqueConstraint

from app.database.base import Base


class Payroll(Base):
    __tablename__ = "HRMS_payroll"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id: Mapped[str] = mapped_column(String(255), ForeignKey("HRMS_employees.id", ondelete="CASCADE"), nullable=False, index=True)
    month: Mapped[str] = mapped_column(String(7), nullable=False, index=True)  # 'YYYY-MM'
    basic_pay: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    allowances: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    deductions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    net_pay: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    advance_money_taken: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    advance_money_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    working_days: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    days_present: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    leaves_taken: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    employee: Mapped["Employee"] = relationship("Employee", backref="payrolls")

    __table_args__ = (
        UniqueConstraint("employee_id", "month", name="unique_employee_payroll_month"),
    )


class PayrollConfig(Base):
    __tablename__ = "HRMS_payroll_config"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    config_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    config_value: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    label: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class Invoice(Base):
    __tablename__ = "HRMS_invoices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_number: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_details: Mapped[str] = mapped_column(Text, nullable=False)
    items: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    total: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    payable_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    tax_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=18.00, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
