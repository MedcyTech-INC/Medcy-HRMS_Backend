from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.employee import Employee
from app.schemas.attendance import BreakStartRequest, BreakResponse
from app.services.break_service import break_service

router = APIRouter()


@router.post("/start", response_model=BreakResponse, status_code=status.HTTP_201_CREATED)
async def start_break(
    request: BreakStartRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Start a break session for current employee."""
    record = await break_service.start_break(db, current_user.id, request.break_type)
    return BreakResponse.model_validate(record)


@router.post("/end", response_model=BreakResponse)
async def end_break(
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """End the active break session."""
    record = await break_service.end_break(db, current_user.id)
    return BreakResponse.model_validate(record)


@router.get("/active", response_model=Optional[BreakResponse])
async def get_active_break(
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Fetch current active break if any, else returns null."""
    record = await break_service.get_active_break(db, current_user.id)
    if not record:
        return None
    return BreakResponse.model_validate(record)


@router.get("/today", response_model=List[BreakResponse])
async def get_today_breaks(
    target_date: Optional[date] = Query(None, alias="date", description="Target date (default today)"),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Fetch all breaks taken on target date."""
    records = await break_service.get_today_breaks(db, current_user.id, target_date)
    return [BreakResponse.model_validate(r) for r in records]
