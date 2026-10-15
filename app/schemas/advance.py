from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class AdvanceApplyRequest(BaseModel):
    amount: float = Field(gt=0)
    reason: str
    advance_type: Literal["salary", "medical"] = Field(default="salary", alias="advanceType")
    repayment_months: Literal[2, 3, 5] = Field(default=2, alias="repaymentMonths")

    model_config = ConfigDict(populate_by_name=True)


class AdvanceResponse(BaseModel):
    id: str
    employee_id: str = Field(alias="employeeId")
    amount: float
    reason: str
    advance_type: str = Field(alias="advanceType")
    status: str
    repayment_months: int = Field(alias="repaymentMonths")
    monthly_installment: float = Field(alias="monthlyInstallment")
    installments_remaining: int = Field(alias="installmentsRemaining")
    submitted_at: datetime = Field(alias="submittedAt")
    approved_at: Optional[datetime] = Field(default=None, alias="approvedAt")
    deducted_in_month: Optional[str] = Field(default=None, alias="deductedInMonth")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )
