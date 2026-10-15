from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.employee import Employee
from app.schemas.doctor_visit import DoctorVisitCreate, DoctorVisitUpdate, DoctorVisitResponse
from app.services.doctor_visit_service import DoctorVisitService

router = APIRouter()


@router.post("", response_model=DoctorVisitResponse, status_code=status.HTTP_201_CREATED)
async def create_doctor_visit(
    payload: DoctorVisitCreate,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await DoctorVisitService.create(db=db, current_user=current_user, payload=payload)


@router.get("", response_model=List[DoctorVisitResponse])
async def list_doctor_visits(
    employee_id: Optional[str] = Query(None, alias="employeeId"),
    visit_date: Optional[date] = Query(None, alias="visitDate"),
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await DoctorVisitService.list_visits(
        db=db, current_user=current_user, employee_id=employee_id, visit_date=visit_date
    )


@router.get("/{visit_id}", response_model=DoctorVisitResponse)
async def get_doctor_visit(
    visit_id: str,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await DoctorVisitService.get_visit(db=db, visit_id=visit_id, current_user=current_user)


@router.patch("/{visit_id}", response_model=DoctorVisitResponse)
async def update_doctor_visit(
    visit_id: str,
    payload: DoctorVisitUpdate,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await DoctorVisitService.update_visit(
        db=db, visit_id=visit_id, current_user=current_user, payload=payload
    )
