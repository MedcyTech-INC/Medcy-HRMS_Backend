from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import require_min_level
from app.models.employee import Employee
from app.schemas.attendance import (
    ClockInRequest,
    ClockOutRequest,
    AttendanceResponse,
    CheckInLocationPinResponse,
)
from app.services.attendance_service import attendance_service

router = APIRouter()


@router.post("/clock-in", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
async def clock_in(
    request: ClockInRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """
    Clock in the current user. Server-side anti-spoofing geofence validation is enforced for in_office punches.
    Replaces: frontend client-side haversine validation.
    """
    record = await attendance_service.clock_in(
        db,
        employee_id=current_user.id,
        latitude=request.latitude,
        longitude=request.longitude,
        accuracy_meters=request.accuracy_meters,
        location=request.location,
        photo_url=request.photo_url,
        punch_type=request.punch_type,
        punch_note=request.punch_note,
    )
    return AttendanceResponse.model_validate(record)


@router.post("/clock-out", response_model=AttendanceResponse)
async def clock_out(
    request: ClockOutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Clock out the current user's active session and record duration."""
    record = await attendance_service.clock_out(
        db,
        employee_id=current_user.id,
        latitude=request.latitude,
        longitude=request.longitude,
        location=request.location,
        photo_url=request.photo_url,
    )
    return AttendanceResponse.model_validate(record)


@router.get("/today", response_model=List[AttendanceResponse])
async def get_today_sessions(
    target_date: Optional[date] = Query(None, alias="date", description="Target date (default today)"),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Get the current authenticated user's attendance sessions for today."""
    records = await attendance_service.get_today_sessions(db, current_user.id, target_date)
    return [AttendanceResponse.model_validate(r) for r in records]


@router.get("/today/locations", response_model=List[CheckInLocationPinResponse])
async def get_today_check_in_locations(
    target_date: Optional[date] = Query(None, alias="date", description="Target date (default today)"),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """
    Manager & Admin live map pins for all subordinate check-ins.
    Replaces: frontend direct Supabase query with unconstrained access.
    """
    pins = await attendance_service.get_today_locations(db, current_user, target_date)
    return [CheckInLocationPinResponse.model_validate(p) for p in pins]
