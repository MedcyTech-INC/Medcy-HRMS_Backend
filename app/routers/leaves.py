from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import require_min_level
from app.models.employee import Employee
from app.schemas.leave import (
    LeaveApplyRequest,
    LeaveApproveRequest,
    LeaveRequestResponse,
    LeaveBalanceResponse,
)
from app.services.leave_service import leave_service

router = APIRouter()


@router.post("/apply", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
async def apply_leave(
    request: LeaveApplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Submit a leave request for current employee."""
    record = await leave_service.apply_leave(db, current_user.id, request)
    return LeaveRequestResponse.model_validate(record)


@router.get("/my-requests", response_model=List[LeaveRequestResponse])
async def get_my_leaves(
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Fetch current user's leave requests."""
    records = await leave_service.get_my_leaves(db, current_user.id)
    return [LeaveRequestResponse.model_validate(r) for r in records]


@router.get("/team-requests", response_model=List[LeaveRequestResponse])
async def get_team_leaves(
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_min_level("team_lead")),
):
    """Fetch subordinate leave requests for approval (Managers/Admins only)."""
    records = await leave_service.get_team_leaves(db, current_user)
    return [LeaveRequestResponse.model_validate(r) for r in records]


@router.patch("/{request_id}/approve", response_model=LeaveRequestResponse)
async def approve_leave(
    request_id: str,
    body: Optional[LeaveApproveRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_min_level("team_lead")),
):
    """
    Atomically approve leave:
    1. Updates request status
    2. Deducts balance
    3. Marks attendance as 'leave'
    """
    note = body.admin_note if body else None
    record = await leave_service.approve_leave(db, request_id, current_user.id, admin_note=note)
    return LeaveRequestResponse.model_validate(record)


@router.patch("/{request_id}/reject", response_model=LeaveRequestResponse)
async def reject_leave(
    request_id: str,
    body: Optional[LeaveApproveRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_min_level("team_lead")),
):
    """Reject a leave request."""
    note = body.admin_note if body else None
    record = await leave_service.reject_leave(db, request_id, current_user.id, admin_note=note)
    return LeaveRequestResponse.model_validate(record)


@router.get("/balances/{emp_id}", response_model=LeaveBalanceResponse)
async def get_leave_balances(
    emp_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Get leave balance summary for an employee."""
    bal = await leave_service.get_leave_balances(db, emp_id)
    return LeaveBalanceResponse.model_validate(bal)
