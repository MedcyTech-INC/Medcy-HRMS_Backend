import uuid
from datetime import date, time, datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Date, Time, Text, Integer, Numeric, Boolean, DateTime, JSON, ForeignKey

from app.database.base import Base


class FieldSession(Base):
    __tablename__ = "HRMS_field_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id: Mapped[str] = mapped_column(String(255), ForeignKey("HRMS_employees.id", ondelete="CASCADE"), nullable=False, index=True)
    session_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)  # 'active' | 'completed' | 'cancelled'
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    start_latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    start_longitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    start_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    end_latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    end_longitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    end_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class FieldVisit(Base):
    __tablename__ = "HRMS_field_visits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("HRMS_field_sessions.id", ondelete="SET NULL"), nullable=True)
    employee_id: Mapped[str] = mapped_column(String(255), ForeignKey("HRMS_employees.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by: Mapped[Optional[str]] = mapped_column(String(255), ForeignKey("HRMS_employees.id", ondelete="SET NULL"), nullable=True)
    visit_type: Mapped[str] = mapped_column(String(100), default="OTHER", nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    scheduled_start: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    scheduled_end: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    assigned_latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    assigned_longitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    assigned_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    allowed_radius_meters: Mapped[int] = mapped_column(Integer, default=150, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="normal", nullable=False)  # 'low' | 'normal' | 'high' | 'urgent'
    status: Mapped[str] = mapped_column(String(50), default="ASSIGNED", nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    arrived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    actual_longitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    actual_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    arrival_distance_m: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    proof_photo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completion_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    patient_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    client_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    location_exception: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    doctor_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    clinic_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    lab_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    call_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 'RMP' | 'LAB' | 'DOCTOR' | 'OTHER'
    area: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    time_slot: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    visit_purpose: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approval_status: Mapped[Optional[str]] = mapped_column(String(50), default="pending", nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reschedule_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class FieldVisitEvent(Base):
    __tablename__ = "HRMS_field_visit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visit_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("HRMS_field_visits.id", ondelete="CASCADE"), nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("HRMS_field_sessions.id", ondelete="SET NULL"), nullable=True)
    employee_id: Mapped[str] = mapped_column(String(255), ForeignKey("HRMS_employees.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    accuracy_m: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, default=dict, nullable=True)
    synced: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class FieldVisitProof(Base):
    __tablename__ = "HRMS_field_visit_proofs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visit_id: Mapped[str] = mapped_column(String(36), ForeignKey("HRMS_field_visits.id", ondelete="CASCADE"), nullable=False, index=True)
    proof_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'photo' | 'note' | 'signature' | 'otp' | 'document'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
