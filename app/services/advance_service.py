from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from fastapi import HTTPException, status

from app.models.advance import AdvanceRequest
from app.models.employee import Employee
from app.schemas.advance import AdvanceApplyRequest
from app.services.hierarchy_service import hierarchy_service


class AdvanceService:
    @staticmethod
    async def apply_advance(
        db: AsyncSession,
        employee_id: str,
        data: AdvanceApplyRequest
    ) -> AdvanceRequest:
        """Submit a salary/medical advance request with installment calculation."""
        installment = round(data.amount / data.repayment_months, 2)
        new_advance = AdvanceRequest(
            employee_id=employee_id,
            amount=data.amount,
            reason=data.reason,
            advance_type=data.advance_type,
            status="pending",
            repayment_months=data.repayment_months,
            monthly_installment=installment,
            installments_remaining=data.repayment_months,
        )
        db.add(new_advance)
        await db.commit()
        await db.refresh(new_advance)
        return new_advance

    @staticmethod
    async def approve_advance(
        db: AsyncSession,
        request_id: str,
        approver_id: str
    ) -> AdvanceRequest:
        """Approve an advance request and initialize repayment schedule."""
        stmt = select(AdvanceRequest).where(AdvanceRequest.id == request_id)
        result = await db.execute(stmt)
        advance = result.scalar_one_or_none()

        if not advance:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Advance request not found")

        advance.status = "approved"
        advance.approved_at = datetime.now(timezone.utc)
        advance.installments_remaining = advance.repayment_months

        await db.commit()
        await db.refresh(advance)
        return advance

    @staticmethod
    async def reject_advance(
        db: AsyncSession,
        request_id: str,
        approver_id: str
    ) -> AdvanceRequest:
        """Reject an advance request."""
        stmt = select(AdvanceRequest).where(AdvanceRequest.id == request_id)
        result = await db.execute(stmt)
        advance = result.scalar_one_or_none()

        if not advance:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Advance request not found")

        advance.status = "rejected"
        await db.commit()
        await db.refresh(advance)
        return advance

    @staticmethod
    async def list_advances(
        db: AsyncSession,
        viewer: Employee,
        employee_id: Optional[str] = None
    ) -> List[AdvanceRequest]:
        """List advance requests with role and hierarchy scoping."""
        query = select(AdvanceRequest).order_by(desc(AdvanceRequest.submitted_at))

        if employee_id:
            can_access = await hierarchy_service.can_access_employee(db, viewer, employee_id)
            if not can_access:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
            query = query.where(AdvanceRequest.employee_id == employee_id)
        elif viewer.role != "admin" and viewer.id not in {"EMP-EXEC-001", "EMP-EXEC-002", "OL001"}:
            sub_ids = await hierarchy_service.get_subordinate_ids(db, viewer.id)
            allowed_ids = set(sub_ids) | {viewer.id}
            query = query.where(AdvanceRequest.employee_id.in_(allowed_ids))

        return list((await db.execute(query)).scalars().all())


advance_service = AdvanceService()
