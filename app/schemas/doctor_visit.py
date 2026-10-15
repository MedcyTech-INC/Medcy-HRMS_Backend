from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DoctorVisitCreate(BaseModel):
    visit_date: date = Field(..., alias="visitDate")
    doctor_name: str = Field(..., alias="doctorName")
    clinic_name: Optional[str] = Field(None, alias="clinicName")
    area: Optional[str] = None
    time_slot: Optional[str] = Field(None, alias="timeSlot")
    visit_purpose: Optional[str] = Field(None, alias="visitPurpose")
    notes: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    model_config = ConfigDict(populate_by_name=True)


class DoctorVisitUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    approval_status: Optional[str] = Field(None, alias="approvalStatus")
    rejection_reason: Optional[str] = Field(None, alias="rejectionReason")

    model_config = ConfigDict(populate_by_name=True)


class DoctorVisitResponse(BaseModel):
    id: str
    employee_id: str = Field(..., alias="employeeId")
    visit_date: date = Field(..., alias="visitDate")
    doctor_name: str = Field(..., alias="doctorName")
    clinic_name: Optional[str] = Field(None, alias="clinicName")
    area: Optional[str] = None
    time_slot: Optional[str] = Field(None, alias="timeSlot")
    visit_purpose: Optional[str] = Field(None, alias="visitPurpose")
    status: str
    notes: Optional[str] = None
    approval_status: Optional[str] = Field(None, alias="approvalStatus")
    approved_by: Optional[str] = Field(None, alias="approvedBy")
    rejection_reason: Optional[str] = Field(None, alias="rejectionReason")
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
