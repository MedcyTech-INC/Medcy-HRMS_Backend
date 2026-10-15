from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ── Payroll ───────────────────────────────────────────────────────────────────

class PayrollCreate(BaseModel):
    employee_id: str = Field(..., alias="employeeId")
    month: str  # 'YYYY-MM'
    basic_pay: float = Field(..., alias="basicPay")
    allowances: List[Dict[str, Any]] = []
    deductions: List[Dict[str, Any]] = []
    net_pay: float = Field(..., alias="netPay")
    advance_money_taken: bool = Field(False, alias="advanceMoneyTaken")
    advance_money_amount: float = Field(0.0, alias="advanceMoneyAmount")
    working_days: Optional[float] = Field(None, alias="workingDays")
    days_present: Optional[float] = Field(None, alias="daysPresent")
    leaves_taken: Optional[float] = Field(None, alias="leavesTaken")

    model_config = ConfigDict(populate_by_name=True)


class PayrollResponse(BaseModel):
    id: str
    employee_id: str = Field(..., alias="employeeId")
    month: str
    basic_pay: float = Field(..., alias="basicPay")
    allowances: List[Dict[str, Any]]
    deductions: List[Dict[str, Any]]
    net_pay: float = Field(..., alias="netPay")
    advance_money_taken: bool = Field(..., alias="advanceMoneyTaken")
    advance_money_amount: float = Field(..., alias="advanceMoneyAmount")
    working_days: Optional[float] = Field(None, alias="workingDays")
    days_present: Optional[float] = Field(None, alias="daysPresent")
    leaves_taken: Optional[float] = Field(None, alias="leavesTaken")
    created_at: datetime = Field(..., alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ── Invoice ───────────────────────────────────────────────────────────────────

class InvoiceItem(BaseModel):
    description: str
    quantity: float
    unit_price: float = Field(..., alias="unitPrice")
    amount: float

    model_config = ConfigDict(populate_by_name=True)


class InvoiceCreate(BaseModel):
    invoice_number: str = Field(..., alias="invoiceNumber")
    client_name: str = Field(..., alias="clientName")
    client_details: str = Field(..., alias="clientDetails")
    items: List[Dict[str, Any]]
    total: float
    payable_amount: float = Field(..., alias="payableAmount")
    due_date: Optional[str] = Field(None, alias="dueDate")
    tax_percent: float = Field(18.0, alias="taxPercent")

    model_config = ConfigDict(populate_by_name=True)


class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str = Field(..., alias="invoiceNumber")
    client_name: str = Field(..., alias="clientName")
    client_details: str = Field(..., alias="clientDetails")
    items: List[Dict[str, Any]]
    total: float
    payable_amount: float = Field(..., alias="payableAmount")
    created_by: Optional[str] = Field(None, alias="createdBy")
    due_date: Optional[Any] = Field(None, alias="dueDate")
    tax_percent: float = Field(..., alias="taxPercent")
    created_at: datetime = Field(..., alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
