from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.payroll import Payroll, Invoice
from app.models.employee import Employee
from app.schemas.payroll import PayrollCreate, PayrollResponse, InvoiceCreate, InvoiceResponse
from app.services.hierarchy_service import HierarchyService


class PayrollService:
    @staticmethod
    async def generate_payroll(
        db: AsyncSession,
        current_user: Employee,
        payload: PayrollCreate,
    ) -> PayrollResponse:
        # Only admin can generate payroll
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Only admin can generate payroll")

        # Verify employee exists
        emp_res = await db.execute(select(Employee).where(Employee.id == payload.employee_id))
        if not emp_res.scalar_one_or_none():
            raise HTTPException(status_code=404, detail=f"Employee {payload.employee_id} not found")

        # Check for duplicate month
        existing = await db.execute(
            select(Payroll).where(
                Payroll.employee_id == payload.employee_id,
                Payroll.month == payload.month,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail=f"Payroll for employee {payload.employee_id} for {payload.month} already exists",
            )

        payroll = Payroll(
            employee_id=payload.employee_id,
            month=payload.month,
            basic_pay=payload.basic_pay,
            allowances=payload.allowances,
            deductions=payload.deductions,
            net_pay=payload.net_pay,
            advance_money_taken=payload.advance_money_taken,
            advance_money_amount=payload.advance_money_amount,
            working_days=payload.working_days,
            days_present=payload.days_present,
            leaves_taken=payload.leaves_taken,
        )
        db.add(payroll)
        await db.commit()
        await db.refresh(payroll)
        return PayrollResponse.model_validate(payroll)

    @staticmethod
    async def list_payrolls(
        db: AsyncSession,
        current_user: Employee,
        employee_id: Optional[str] = None,
        month: Optional[str] = None,
    ) -> List[PayrollResponse]:
        query = select(Payroll)

        if current_user.role != "admin":
            # Employees can only see their own payroll
            query = query.where(Payroll.employee_id == current_user.id)
        elif employee_id:
            query = query.where(Payroll.employee_id == employee_id)

        if month:
            query = query.where(Payroll.month == month)

        query = query.order_by(Payroll.month.desc())
        result = await db.execute(query)
        return [PayrollResponse.model_validate(p) for p in result.scalars().all()]

    @staticmethod
    async def get_payroll(
        db: AsyncSession,
        payroll_id: str,
        current_user: Employee,
    ) -> PayrollResponse:
        res = await db.execute(select(Payroll).where(Payroll.id == payroll_id))
        payroll = res.scalar_one_or_none()
        if not payroll:
            raise HTTPException(status_code=404, detail="Payroll record not found")

        if current_user.role != "admin" and payroll.employee_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this payroll")

        return PayrollResponse.model_validate(payroll)


class InvoiceService:
    @staticmethod
    async def create_invoice(
        db: AsyncSession,
        current_user: Employee,
        payload: InvoiceCreate,
    ) -> InvoiceResponse:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Only admin can create invoices")

        existing = await db.execute(
            select(Invoice).where(Invoice.invoice_number == payload.invoice_number)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail=f"Invoice #{payload.invoice_number} already exists")

        invoice = Invoice(
            invoice_number=payload.invoice_number,
            client_name=payload.client_name,
            client_details=payload.client_details,
            items=payload.items,
            total=payload.total,
            payable_amount=payload.payable_amount,
            created_by=current_user.id,
            due_date=payload.due_date,
            tax_percent=payload.tax_percent,
        )
        db.add(invoice)
        await db.commit()
        await db.refresh(invoice)
        return InvoiceResponse.model_validate(invoice)

    @staticmethod
    async def list_invoices(
        db: AsyncSession,
        current_user: Employee,
    ) -> List[InvoiceResponse]:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Only admin can view invoices")

        result = await db.execute(select(Invoice).order_by(Invoice.created_at.desc()))
        return [InvoiceResponse.model_validate(inv) for inv in result.scalars().all()]

    @staticmethod
    async def get_invoice(
        db: AsyncSession,
        invoice_id: str,
        current_user: Employee,
    ) -> InvoiceResponse:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Only admin can view invoices")

        res = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
        invoice = res.scalar_one_or_none()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        return InvoiceResponse.model_validate(invoice)
