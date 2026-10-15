from datetime import date, datetime, timezone
from typing import Optional, List, Any
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Numeric, Date, DateTime, JSON, ForeignKey

from app.database.base import Base


class Employee(Base):
    __tablename__ = "HRMS_employees"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="employee")  # 'employee' | 'admin'
    designation: Mapped[str] = mapped_column(String(255), nullable=False)
    joining_date: Mapped[date] = mapped_column(Date, nullable=False)
    basic_pay: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.00)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")  # 'active' | 'inactive' | 'pending'
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    experience: Mapped[Optional[float]] = mapped_column(Numeric(4, 1), default=0.0, nullable=True)
    dob: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    bank_details: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)
    branch: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 'visakhapatnam' | 'vizianagaram'
    hospital: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 'vizag_ivf' | 'medcy_hospitals' | 'both'
    hierarchy_level: Mapped[Optional[str]] = mapped_column(String(50), default="employee", nullable=True)
    managed_branches: Mapped[Optional[list]] = mapped_column(JSON, default=list, nullable=True)
    reporting_to: Mapped[Optional[str]] = mapped_column(String(255), ForeignKey("HRMS_employees.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    manager: Mapped[Optional["Employee"]] = relationship("Employee", remote_side=[id], backref="subordinates", foreign_keys=[reporting_to])
