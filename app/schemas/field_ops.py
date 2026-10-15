from datetime import date, datetime, time
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field

# ── Field Session ─────────────────────────────────────────────────────────────

class FieldSessionCreate(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    notes: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class FieldSessionEnd(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    notes: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class FieldSessionResponse(BaseModel):
    id: str
    employee_id: str = Field(..., alias="employeeId")
    session_date: date = Field(..., alias="sessionDate")
    status: str
    started_at: datetime = Field(..., alias="startedAt")
    ended_at: Optional[datetime] = Field(None, alias="endedAt")
    start_latitude: Optional[float] = Field(None, alias="startLatitude")
    start_longitude: Optional[float] = Field(None, alias="startLongitude")
    start_address: Optional[str] = Field(None, alias="startAddress")
    end_latitude: Optional[float] = Field(None, alias="endLatitude")
    end_longitude: Optional[float] = Field(None, alias="endLongitude")
    end_address: Optional[str] = Field(None, alias="endAddress")
    notes: Optional[str] = None
    created_at: datetime = Field(..., alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ── Field Visit ───────────────────────────────────────────────────────────────

VisitStatus = Literal["ASSIGNED", "EN_ROUTE", "ARRIVED", "IN_PROGRESS", "COMPLETED", "MISSED", "CANCELLED", "RESCHEDULED"]


class FieldVisitCreate(BaseModel):
    title: str
    description: Optional[str] = None
    visit_type: str = Field("OTHER", alias="visitType")
    scheduled_date: date = Field(..., alias="scheduledDate")
    scheduled_start: Optional[str] = Field(None, alias="scheduledStart")  # HH:MM
    scheduled_end: Optional[str] = Field(None, alias="scheduledEnd")
    assigned_latitude: Optional[float] = Field(None, alias="assignedLatitude")
    assigned_longitude: Optional[float] = Field(None, alias="assignedLongitude")
    assigned_address: Optional[str] = Field(None, alias="assignedAddress")
    allowed_radius_meters: int = Field(150, alias="allowedRadiusMeters")
    priority: str = "normal"
    doctor_name: Optional[str] = Field(None, alias="doctorName")
    clinic_name: Optional[str] = Field(None, alias="clinicName")
    lab_name: Optional[str] = Field(None, alias="labName")
    call_type: Optional[str] = Field(None, alias="callType")
    area: Optional[str] = None
    time_slot: Optional[str] = Field(None, alias="timeSlot")
    visit_purpose: Optional[str] = Field(None, alias="visitPurpose")
    patient_name: Optional[str] = Field(None, alias="patientName")
    client_reference: Optional[str] = Field(None, alias="clientReference")

    model_config = ConfigDict(populate_by_name=True)


class FieldVisitStatusUpdate(BaseModel):
    status: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    completion_notes: Optional[str] = Field(None, alias="completionNotes")
    proof_photo_url: Optional[str] = Field(None, alias="proofPhotoUrl")

    model_config = ConfigDict(populate_by_name=True)


class FieldVisitResponse(BaseModel):
    id: str
    session_id: Optional[str] = Field(None, alias="sessionId")
    employee_id: str = Field(..., alias="employeeId")
    assigned_by: Optional[str] = Field(None, alias="assignedBy")
    visit_type: str = Field(..., alias="visitType")
    title: str
    description: Optional[str] = None
    scheduled_date: date = Field(..., alias="scheduledDate")
    assigned_address: Optional[str] = Field(None, alias="assignedAddress")
    priority: str
    status: str
    started_at: Optional[datetime] = Field(None, alias="startedAt")
    arrived_at: Optional[datetime] = Field(None, alias="arrivedAt")
    completed_at: Optional[datetime] = Field(None, alias="completedAt")
    actual_latitude: Optional[float] = Field(None, alias="actualLatitude")
    actual_longitude: Optional[float] = Field(None, alias="actualLongitude")
    actual_address: Optional[str] = Field(None, alias="actualAddress")
    arrival_distance_m: Optional[int] = Field(None, alias="arrivalDistanceM")
    duration_minutes: Optional[int] = Field(None, alias="durationMinutes")
    proof_photo_url: Optional[str] = Field(None, alias="proofPhotoUrl")
    completion_notes: Optional[str] = Field(None, alias="completionNotes")
    doctor_name: Optional[str] = Field(None, alias="doctorName")
    clinic_name: Optional[str] = Field(None, alias="clinicName")
    call_type: Optional[str] = Field(None, alias="callType")
    area: Optional[str] = None
    visit_purpose: Optional[str] = Field(None, alias="visitPurpose")
    approval_status: Optional[str] = Field(None, alias="approvalStatus")
    created_at: datetime = Field(..., alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
