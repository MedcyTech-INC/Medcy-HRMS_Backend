from datetime import date, time
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class ClockInRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy_meters: Optional[float] = Field(default=None, alias="accuracyMeters")
    location: Optional[str] = None
    photo_url: Optional[str] = Field(default=None, alias="photoUrl")
    punch_type: Literal["in_office", "out_of_office"] = Field(default="in_office", alias="punchType")
    punch_note: Optional[str] = Field(default=None, alias="punchNote")

    model_config = ConfigDict(populate_by_name=True)


class ClockOutRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location: Optional[str] = None
    photo_url: Optional[str] = Field(default=None, alias="photoUrl")

    model_config = ConfigDict(populate_by_name=True)


class AttendanceResponse(BaseModel):
    id: str
    employee_id: str = Field(alias="employeeId")
    date: date
    status: str
    check_in_time: Optional[time] = Field(default=None, alias="checkInTime")
    check_out_time: Optional[time] = Field(default=None, alias="checkOutTime")
    total_hours: Optional[float] = Field(default=None, alias="totalHours")
    check_in_location: Optional[str] = Field(default=None, alias="checkInLocation")
    check_in_lat_lng: Optional[str] = Field(default=None, alias="checkInLatLng")
    photo_url: Optional[str] = Field(default=None, alias="photoUrl")
    check_out_photo_url: Optional[str] = Field(default=None, alias="checkOutPhotoUrl")
    punch_type: Optional[str] = Field(default="in_office", alias="punchType")
    punch_note: Optional[str] = Field(default=None, alias="punchNote")
    session_number: int = Field(default=1, alias="sessionNumber")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )


class BreakStartRequest(BaseModel):
    break_type: Literal["lunch", "tea", "personal"] = Field(default="lunch", alias="breakType")

    model_config = ConfigDict(populate_by_name=True)


class BreakResponse(BaseModel):
    id: str
    employee_id: str = Field(alias="employeeId")
    date: date
    start_time: time = Field(alias="startTime")
    end_time: Optional[time] = Field(default=None, alias="endTime")
    duration_minutes: Optional[int] = Field(default=None, alias="durationMinutes")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )


class CheckInLocationPinResponse(BaseModel):
    employee_id: str = Field(alias="employeeId")
    employee_name: str = Field(alias="employeeName")
    latitude: float
    longitude: float
    location_name: Optional[str] = Field(default=None, alias="locationName")
    check_in_time: Optional[str] = Field(default=None, alias="checkInTime")
    photo_url: Optional[str] = Field(default=None, alias="photoUrl")

    model_config = ConfigDict(populate_by_name=True)
