from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import require_role
from app.models.employee import Employee
from app.schemas.advance import AdvanceApplyRequest, AdvanceResponse
from app.services.advance_service import advance_service

router = APIRouter()


@router.post("/request", response_model=AdvanceResponse, status_code=status.HTTP_201_CREATED)
async def request_advance(
    request: AdvanceApplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Submit a salary advance request."""
    record = await advance_service.apply_advance(db, current_user.id, request)
    return AdvanceResponse.model_validate(record)


@router.get("", response_model=List[AdvanceResponse])
async def list_advances(
    employee_id: Optional[str] = Query(None, alias="employeeId", description="Filter by employee"),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """List advance requests (Scoped by hierarchy)."""
    records = await advance_service.list_advances(db, current_user, employee_id=employee_id)
    return [AdvanceResponse.model_validate(r) for r in records]


@router.patch("/{request_id}/approve", response_model=AdvanceResponse)
async def approve_advance(
    request_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("admin")),
):
    """Approve an advance request and initialize repayment installments (Admin only)."""
    record = await advance_service.approve_advance(db, request_id, current_user.id)
    return AdvanceResponse.model_validate(record)


@router.patch("/{request_id}/reject", response_model=AdvanceResponse)
async def reject_advance(
    request_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("admin")),
):
    """Reject an advance request (Admin only)."""
    record = await advance_service.reject_advance(db, request_id, current_user.id)
    return AdvanceResponse.model_validate(record)
