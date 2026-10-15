from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ASHAEncounterCreate(BaseModel):
    asha_name: str = Field(..., alias="ashaName")
    village: str
    encounter_date: Optional[date] = Field(None, alias="encounterDate")
    referrals_count: int = Field(0, alias="referralsCount")
    hospital_name: Optional[str] = Field(None, alias="hospitalName")
    notes: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class ASHAEncounterUpdate(BaseModel):
    referrals_count: Optional[int] = Field(None, alias="referralsCount")
    hospital_name: Optional[str] = Field(None, alias="hospitalName")
    notes: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class ASHAEncounterResponse(BaseModel):
    id: str
    employee_id: str = Field(..., alias="employeeId")
    asha_name: str = Field(..., alias="ashaName")
    village: str
    encounter_date: date = Field(..., alias="encounterDate")
    referrals_count: int = Field(..., alias="referralsCount")
    hospital_name: Optional[str] = Field(None, alias="hospitalName")
    notes: Optional[str] = None
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
