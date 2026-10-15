from datetime import date, datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.asha_encounter import ASHAEncounter
from app.models.employee import Employee
from app.schemas.asha_encounter import ASHAEncounterCreate, ASHAEncounterUpdate, ASHAEncounterResponse
from app.services.hierarchy_service import HierarchyService


class ASHAEncounterService:
    @staticmethod
    async def create(
        db: AsyncSession,
        current_user: Employee,
        payload: ASHAEncounterCreate,
    ) -> ASHAEncounterResponse:
        encounter = ASHAEncounter(
            employee_id=current_user.id,
            asha_name=payload.asha_name,
            village=payload.village,
            encounter_date=payload.encounter_date or date.today(),
            referrals_count=payload.referrals_count,
            hospital_name=payload.hospital_name,
            notes=payload.notes,
        )
        db.add(encounter)
        await db.commit()
        await db.refresh(encounter)
        return ASHAEncounterResponse.model_validate(encounter)

    @staticmethod
    async def list_encounters(
        db: AsyncSession,
        current_user: Employee,
        employee_id: Optional[str] = None,
        encounter_date: Optional[date] = None,
    ) -> List[ASHAEncounterResponse]:
        query = select(ASHAEncounter)

        if current_user.role != "admin":
            subordinate_ids = await HierarchyService.get_subordinate_ids(db, current_user.id)
            allowed_ids = set(subordinate_ids) | {current_user.id}
            query = query.where(ASHAEncounter.employee_id.in_(allowed_ids))

        if employee_id:
            query = query.where(ASHAEncounter.employee_id == employee_id)
        if encounter_date:
            query = query.where(ASHAEncounter.encounter_date == encounter_date)

        query = query.order_by(ASHAEncounter.encounter_date.desc(), ASHAEncounter.created_at.desc())
        result = await db.execute(query)
        return [ASHAEncounterResponse.model_validate(e) for e in result.scalars().all()]

    @staticmethod
    async def get_encounter(
        db: AsyncSession,
        encounter_id: str,
        current_user: Employee,
    ) -> ASHAEncounterResponse:
        res = await db.execute(select(ASHAEncounter).where(ASHAEncounter.id == encounter_id))
        enc = res.scalar_one_or_none()
        if not enc:
            raise HTTPException(status_code=404, detail="ASHA encounter not found")

        if current_user.role != "admin" and enc.employee_id != current_user.id:
            subordinate_ids = await HierarchyService.get_subordinate_ids(db, current_user.id)
            if enc.employee_id not in subordinate_ids:
                raise HTTPException(status_code=403, detail="Not authorized")

        return ASHAEncounterResponse.model_validate(enc)

    @staticmethod
    async def update_encounter(
        db: AsyncSession,
        encounter_id: str,
        current_user: Employee,
        payload: ASHAEncounterUpdate,
    ) -> ASHAEncounterResponse:
        res = await db.execute(select(ASHAEncounter).where(ASHAEncounter.id == encounter_id))
        enc = res.scalar_one_or_none()
        if not enc:
            raise HTTPException(status_code=404, detail="ASHA encounter not found")

        if current_user.role != "admin" and enc.employee_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(enc, key, value)

        enc.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(enc)
        return ASHAEncounterResponse.model_validate(enc)
