from datetime import date, timedelta
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from fastapi import HTTPException, status

from app.models.leave import LeaveRequest, LeaveBalance, MonthlyLeaveQuota
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.schemas.leave import LeaveApplyRequest
from app.services.hierarchy_service import hierarchy_service


class LeaveService:
    @staticmethod
    async def apply_leave(
        db: AsyncSession,
        employee_id: str,
        data: LeaveApplyRequest
    ) -> LeaveRequest:
        """Submit a leave request for an employee."""
        if data.from_date > data.to_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="From date must be earlier than or equal to To date",
            )

        new_req = LeaveRequest(
            employee_id=employee_id,
            leave_type=data.leave_type,
            from_date=data.from_date,
            to_date=data.to_date,
            reason=data.reason,
            status="pending",
        )
        db.add(new_req)
        await db.commit()
        await db.refresh(new_req)
        return new_req

    @staticmethod
    async def approve_leave(
        db: AsyncSession,
        request_id: str,
        approver_id: str,
        admin_note: Optional[str] = None
    ) -> LeaveRequest:
        """
        Transactional leave approval:
        1. Set status to 'Approved'
        2. Deduct leave days from LeaveBalance
        3. Mark Attendance records as 'leave' for every day in range
        All operations are committed atomically.
        """
        stmt = select(LeaveRequest).where(LeaveRequest.id == request_id)
        result = await db.execute(stmt)
        leave_req = result.scalar_one_or_none()

        if not leave_req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")

        if leave_req.status == "approved":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Leave request is already approved")

        leave_req.status = "approved"
        leave_req.approved_by = approver_id
        leave_req.admin_note = admin_note or ""

        # Calculate leave duration
        diff_days = (leave_req.to_date - leave_req.from_date).days + 1

        # Update or create LeaveBalance
        bal_stmt = select(LeaveBalance).where(
            LeaveBalance.employee_id == leave_req.employee_id,
            LeaveBalance.leave_type == leave_req.leave_type,
        )
        balance = (await db.execute(bal_stmt)).scalar_one_or_none()
        if balance:
            balance.used = (balance.used or 0) + diff_days
        else:
            new_bal = LeaveBalance(
                employee_id=leave_req.employee_id,
                leave_type=leave_req.leave_type,
                total_allotted=12,
                used=diff_days,
            )
            db.add(new_bal)

        # Mark daily Attendance as 'leave'
        current = leave_req.from_date
        while current <= leave_req.to_date:
            att_stmt = select(Attendance).where(
                Attendance.employee_id == leave_req.employee_id,
                Attendance.date == current,
            )
            existing_att = (await db.execute(att_stmt)).scalars().first()
            if existing_att:
                existing_att.status = "leave"
            else:
                db.add(Attendance(
                    employee_id=leave_req.employee_id,
                    date=current,
                    status="leave",
                ))
            current += timedelta(days=1)

        await db.commit()
        await db.refresh(leave_req)
        return leave_req

    @staticmethod
    async def reject_leave(
        db: AsyncSession,
        request_id: str,
        approver_id: str,
        admin_note: Optional[str] = None
    ) -> LeaveRequest:
        """Reject a leave request."""
        stmt = select(LeaveRequest).where(LeaveRequest.id == request_id)
        result = await db.execute(stmt)
        leave_req = result.scalar_one_or_none()

        if not leave_req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")

        leave_req.status = "rejected"
        leave_req.approved_by = approver_id
        leave_req.admin_note = admin_note or ""
        await db.commit()
        await db.refresh(leave_req)
        return leave_req

    @staticmethod
    async def get_my_leaves(db: AsyncSession, employee_id: str) -> List[LeaveRequest]:
        """Fetch all leave requests for the specified employee."""
        stmt = (
            select(LeaveRequest)
            .where(LeaveRequest.employee_id == employee_id)
            .order_by(desc(LeaveRequest.submitted_at))
        )
        return list((await db.execute(stmt)).scalars().all())

    @staticmethod
    async def get_team_leaves(db: AsyncSession, viewer: Employee) -> List[LeaveRequest]:
        """Fetch leave requests for subordinates (or all for Admin)."""
        query = select(LeaveRequest).order_by(desc(LeaveRequest.submitted_at))
        if viewer.role != "admin" and viewer.id not in {"EMP-EXEC-001", "EMP-EXEC-002", "OL001"}:
            sub_ids = await hierarchy_service.get_subordinate_ids(db, viewer.id)
            query = query.where(LeaveRequest.employee_id.in_(sub_ids))

        return list((await db.execute(query)).scalars().all())

    @staticmethod
    async def get_leave_balances(db: AsyncSession, employee_id: str) -> Dict[str, dict]:
        """Return full leave balance summary for an employee."""
        stmt = select(LeaveBalance).where(LeaveBalance.employee_id == employee_id)
        balances = (await db.execute(stmt)).scalars().all()

        bal_map = {b.leave_type: {"allowed": b.total_allotted, "taken": b.used} for b in balances}
        return {
            "sick": bal_map.get("sick", {"allowed": 12, "taken": 0}),
            "casual": bal_map.get("casual", {"allowed": 12, "taken": 0}),
            "maternity": bal_map.get("maternity"),
            "paternity": bal_map.get("paternity"),
        }


leave_service = LeaveService()
