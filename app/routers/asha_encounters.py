from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.employee import Employee
from app.schemas.asha_encounter import ASHAEncounterCreate, ASHAEncounterUpdate, ASHAEncounterResponse
from app.services.asha_encounter_service import ASHAEncounterService

router = APIRouter()


@router.post("", response_model=ASHAEncounterResponse, status_code=status.HTTP_201_CREATED)
async def create_asha_encounter(
    payload: ASHAEncounterCreate,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ASHAEncounterService.create(db=db, current_user=current_user, payload=payload)


@router.get("", response_model=List[ASHAEncounterResponse])
async def list_asha_encounters(
    employee_id: Optional[str] = Query(None, alias="employeeId"),
    encounter_date: Optional[date] = Query(None, alias="encounterDate"),
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ASHAEncounterService.list_encounters(
        db=db, current_user=current_user, employee_id=employee_id, encounter_date=encounter_date
    )


@router.get("/{encounter_id}", response_model=ASHAEncounterResponse)
async def get_asha_encounter(
    encounter_id: str,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ASHAEncounterService.get_encounter(
        db=db, encounter_id=encounter_id, current_user=current_user
    )


@router.patch("/{encounter_id}", response_model=ASHAEncounterResponse)
async def update_asha_encounter(
    encounter_id: str,
    payload: ASHAEncounterUpdate,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ASHAEncounterService.update_encounter(
        db=db, encounter_id=encounter_id, current_user=current_user, payload=payload
    )
