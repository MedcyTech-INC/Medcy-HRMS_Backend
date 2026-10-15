from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.employee import Employee
from app.schemas.field_ops import (
    FieldSessionCreate, FieldSessionEnd, FieldSessionResponse,
    FieldVisitCreate, FieldVisitStatusUpdate, FieldVisitResponse,
)
from app.services.field_ops_service import FieldOpsService

router = APIRouter()


# ── Field Sessions ─────────────────────────────────────────────────────────────

@router.post("/sessions/start", response_model=FieldSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_field_session(
    payload: FieldSessionCreate,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FieldOpsService.start_session(db=db, current_user=current_user, payload=payload)


@router.post("/sessions/{session_id}/end", response_model=FieldSessionResponse)
async def end_field_session(
    session_id: str,
    payload: FieldSessionEnd,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FieldOpsService.end_session(
        db=db, session_id=session_id, current_user=current_user, payload=payload
    )


@router.get("/sessions", response_model=List[FieldSessionResponse])
async def list_field_sessions(
    employee_id: Optional[str] = Query(None, alias="employeeId"),
    session_date: Optional[date] = Query(None, alias="sessionDate"),
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FieldOpsService.list_sessions(
        db=db, current_user=current_user, employee_id=employee_id, session_date=session_date
    )


# ── Field Visits ───────────────────────────────────────────────────────────────

@router.post("/visits", response_model=FieldVisitResponse, status_code=status.HTTP_201_CREATED)
async def create_field_visit(
    assigned_to: str = Query(..., alias="assignedTo"),
    payload: FieldVisitCreate = ...,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FieldOpsService.create_visit(
        db=db, current_user=current_user, assigned_to=assigned_to, payload=payload
    )


@router.get("/visits", response_model=List[FieldVisitResponse])
async def list_field_visits(
    employee_id: Optional[str] = Query(None, alias="employeeId"),
    scheduled_date: Optional[date] = Query(None, alias="scheduledDate"),
    visit_status: Optional[str] = Query(None, alias="status"),
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FieldOpsService.list_visits(
        db=db,
        current_user=current_user,
        employee_id=employee_id,
        scheduled_date=scheduled_date,
        visit_status=visit_status,
    )


@router.get("/visits/{visit_id}", response_model=FieldVisitResponse)
async def get_field_visit(
    visit_id: str,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FieldOpsService.get_visit(db=db, visit_id=visit_id, current_user=current_user)


@router.patch("/visits/{visit_id}/status", response_model=FieldVisitResponse)
async def update_visit_status(
    visit_id: str,
    payload: FieldVisitStatusUpdate,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FieldOpsService.update_visit_status(
        db=db, visit_id=visit_id, current_user=current_user, payload=payload
    )
