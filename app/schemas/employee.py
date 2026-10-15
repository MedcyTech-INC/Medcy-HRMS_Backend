from datetime import date, datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, EmailStr


class BankDetailsSchema(BaseModel):
    accountNumber: Optional[str] = None
    bankName: Optional[str] = None
    ifsc: Optional[str] = None
    accountType: Optional[Literal["savings", "current"]] = None

    model_config = ConfigDict(populate_by_name=True)


class EmployeeBase(BaseModel):
    name: str
    email: EmailStr
    designation: str
    joining_date: date = Field(alias="joiningDate")
    basic_pay: float = Field(default=0.0, alias="basicSalary")
    role: Literal["employee", "admin"] = "employee"
    status: Literal["active", "inactive", "pending"] = "active"
    phone: Optional[str] = None
    gender: Optional[Literal["male", "female", "other"]] = None
    dob: Optional[date] = None
    experience: Optional[float] = 0.0
    hospital: Optional[Literal["vizag_ivf", "medcy_hospitals", "both"]] = None
    branch: Optional[Literal["visakhapatnam", "vizianagaram"]] = None
    hierarchy_level: Optional[Literal["employee", "team_lead", "manager", "senior_manager", "executive"]] = Field(
        default="employee",
        alias="hierarchyLevel"
    )
    managed_branches: Optional[List[str]] = Field(default_factory=list, alias="managedBranches")
    reporting_to: Optional[str] = Field(default=None, alias="reportingTo")
    bank_details: Optional[BankDetailsSchema] = Field(default=None, alias="bankDetails")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )


class EmployeeCreate(EmployeeBase):
    id: str
    password: str = Field(min_length=6)


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    designation: Optional[str] = None
    joining_date: Optional[date] = Field(default=None, alias="joiningDate")
    basic_pay: Optional[float] = Field(default=None, alias="basicSalary")
    role: Optional[Literal["employee", "admin"]] = None
    status: Optional[Literal["active", "inactive", "pending"]] = None
    phone: Optional[str] = None
    gender: Optional[Literal["male", "female", "other"]] = None
    dob: Optional[date] = None
    experience: Optional[float] = None
    hospital: Optional[Literal["vizag_ivf", "medcy_hospitals", "both"]] = None
    branch: Optional[Literal["visakhapatnam", "vizianagaram"]] = None
    hierarchy_level: Optional[Literal["employee", "team_lead", "manager", "senior_manager", "executive"]] = Field(
        default=None,
        alias="hierarchyLevel"
    )
    managed_branches: Optional[List[str]] = Field(default=None, alias="managedBranches")
    reporting_to: Optional[str] = Field(default=None, alias="reportingTo")
    bank_details: Optional[BankDetailsSchema] = Field(default=None, alias="bankDetails")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )


class EmployeeResponse(EmployeeBase):
    id: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )
