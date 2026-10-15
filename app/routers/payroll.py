from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.employee import Employee
from app.schemas.payroll import PayrollCreate, PayrollResponse, InvoiceCreate, InvoiceResponse
from app.services.payroll_service import PayrollService, InvoiceService

router = APIRouter()


# ── Payroll ───────────────────────────────────────────────────────────────────

@router.post("/payroll", response_model=PayrollResponse, status_code=status.HTTP_201_CREATED)
async def generate_payroll(
    payload: PayrollCreate,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PayrollService.generate_payroll(db=db, current_user=current_user, payload=payload)


@router.get("/payroll", response_model=List[PayrollResponse])
async def list_payrolls(
    employee_id: Optional[str] = Query(None, alias="employeeId"),
    month: Optional[str] = Query(None),
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PayrollService.list_payrolls(
        db=db, current_user=current_user, employee_id=employee_id, month=month
    )


@router.get("/payroll/{payroll_id}", response_model=PayrollResponse)
async def get_payroll(
    payroll_id: str,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PayrollService.get_payroll(db=db, payroll_id=payroll_id, current_user=current_user)


# ── Invoices ──────────────────────────────────────────────────────────────────

@router.post("/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    payload: InvoiceCreate,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await InvoiceService.create_invoice(db=db, current_user=current_user, payload=payload)


@router.get("/invoices", response_model=List[InvoiceResponse])
async def list_invoices(
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await InvoiceService.list_invoices(db=db, current_user=current_user)


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await InvoiceService.get_invoice(db=db, invoice_id=invoice_id, current_user=current_user)
