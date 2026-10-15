from datetime import date
from typing import Optional, Literal, Dict
from pydantic import BaseModel, Field, ConfigDict


class LeaveApplyRequest(BaseModel):
    leave_type: Literal["sick", "casual", "maternity", "paternity", "monthly"] = Field(alias="type")
    from_date: date = Field(alias="fromDate")
    to_date: date = Field(alias="toDate")
    reason: str

    model_config = ConfigDict(populate_by_name=True)


class LeaveApproveRequest(BaseModel):
    admin_note: Optional[str] = Field(default=None, alias="adminNote")

    model_config = ConfigDict(populate_by_name=True)


class LeaveRequestResponse(BaseModel):
    id: str
    employee_id: str = Field(alias="employeeId")
    leave_type: str = Field(alias="type")
    from_date: date = Field(alias="fromDate")
    to_date: date = Field(alias="toDate")
    reason: Optional[str] = None
    status: str
    submitted_at: date = Field(alias="submittedAt")
    admin_note: Optional[str] = Field(default=None, alias="adminNote")
    approved_by: Optional[str] = Field(default=None, alias="approvedBy")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )


class LeaveBalanceDetail(BaseModel):
    allowed: int
    taken: int


class LeaveBalanceResponse(BaseModel):
    sick: LeaveBalanceDetail
    casual: LeaveBalanceDetail
    maternity: Optional[LeaveBalanceDetail] = None
    paternity: Optional[LeaveBalanceDetail] = None

    model_config = ConfigDict(populate_by_name=True)
