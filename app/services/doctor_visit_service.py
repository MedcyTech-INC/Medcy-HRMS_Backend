from datetime import date, datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.doctor_visit import DoctorVisit
from app.models.employee import Employee
from app.schemas.doctor_visit import DoctorVisitCreate, DoctorVisitUpdate, DoctorVisitResponse
from app.services.hierarchy_service import HierarchyService


class DoctorVisitService:
    @staticmethod
    async def create(
        db: AsyncSession,
        current_user: Employee,
        payload: DoctorVisitCreate,
    ) -> DoctorVisitResponse:
        visit = DoctorVisit(
            employee_id=current_user.id,
            visit_date=payload.visit_date,
            doctor_name=payload.doctor_name,
            clinic_name=payload.clinic_name,
            area=payload.area,
            time_slot=payload.time_slot,
            visit_purpose=payload.visit_purpose,
            notes=payload.notes,
            status="planned",
            approval_status="pending",
            address=payload.address,
            latitude=payload.latitude,
            longitude=payload.longitude,
        )
        db.add(visit)
        await db.commit()
        await db.refresh(visit)
        return DoctorVisitResponse.model_validate(visit)

    @staticmethod
    async def list_visits(
        db: AsyncSession,
        current_user: Employee,
        employee_id: Optional[str] = None,
        visit_date: Optional[date] = None,
    ) -> List[DoctorVisitResponse]:
        query = select(DoctorVisit)

        if current_user.role != "admin":
            subordinate_ids = await HierarchyService.get_subordinate_ids(db, current_user.id)
            allowed_ids = set(subordinate_ids) | {current_user.id}
            query = query.where(DoctorVisit.employee_id.in_(allowed_ids))

        if employee_id:
            query = query.where(DoctorVisit.employee_id == employee_id)
        if visit_date:
            query = query.where(DoctorVisit.visit_date == visit_date)

        query = query.order_by(DoctorVisit.visit_date.desc(), DoctorVisit.created_at.desc())
        result = await db.execute(query)
        return [DoctorVisitResponse.model_validate(v) for v in result.scalars().all()]

    @staticmethod
    async def get_visit(
        db: AsyncSession,
        visit_id: str,
        current_user: Employee,
    ) -> DoctorVisitResponse:
        res = await db.execute(select(DoctorVisit).where(DoctorVisit.id == visit_id))
        visit = res.scalar_one_or_none()
        if not visit:
            raise HTTPException(status_code=404, detail="Doctor visit not found")

        if current_user.role != "admin" and visit.employee_id != current_user.id:
            subordinate_ids = await HierarchyService.get_subordinate_ids(db, current_user.id)
            if visit.employee_id not in subordinate_ids:
                raise HTTPException(status_code=403, detail="Not authorized")

        return DoctorVisitResponse.model_validate(visit)

    @staticmethod
    async def update_visit(
        db: AsyncSession,
        visit_id: str,
        current_user: Employee,
        payload: DoctorVisitUpdate,
    ) -> DoctorVisitResponse:
        res = await db.execute(select(DoctorVisit).where(DoctorVisit.id == visit_id))
        visit = res.scalar_one_or_none()
        if not visit:
            raise HTTPException(status_code=404, detail="Doctor visit not found")

        # Only owner or admin can update; only admin can approve
        if current_user.role != "admin":
            if visit.employee_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not authorized")
            if payload.approval_status is not None:
                raise HTTPException(status_code=403, detail="Only admin can change approval status")

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(visit, key, value)

        if payload.approval_status == "approved":
            visit.approved_by = current_user.id

        visit.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(visit)
        return DoctorVisitResponse.model_validate(visit)
