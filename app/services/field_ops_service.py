from datetime import date, datetime, timezone
from typing import List, Optional
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.field_ops import FieldSession, FieldVisit
from app.models.employee import Employee
from app.schemas.field_ops import (
    FieldSessionCreate, FieldSessionEnd, FieldSessionResponse,
    FieldVisitCreate, FieldVisitStatusUpdate, FieldVisitResponse,
)
from app.utils.haversine import haversine_distance
from app.services.hierarchy_service import HierarchyService


class FieldOpsService:
    # ── Field Sessions ──────────────────────────────────────────────────────

    @staticmethod
    async def start_session(
        db: AsyncSession,
        current_user: Employee,
        payload: FieldSessionCreate,
    ) -> FieldSessionResponse:
        # Prevent double open session on same day
        today = date.today()
        existing = await db.execute(
            select(FieldSession).where(
                FieldSession.employee_id == current_user.id,
                FieldSession.session_date == today,
                FieldSession.status == "active",
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An active field session is already open for today",
            )

        session = FieldSession(
            employee_id=current_user.id,
            session_date=today,
            status="active",
            start_latitude=payload.latitude,
            start_longitude=payload.longitude,
            start_address=payload.address,
            notes=payload.notes,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return _map_session(session)

    @staticmethod
    async def end_session(
        db: AsyncSession,
        session_id: str,
        current_user: Employee,
        payload: FieldSessionEnd,
    ) -> FieldSessionResponse:
        res = await db.execute(select(FieldSession).where(FieldSession.id == session_id))
        session = res.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Field session not found")
        if session.employee_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Not authorized")
        if session.status != "active":
            raise HTTPException(status_code=409, detail="Session is already closed")

        session.status = "completed"
        session.ended_at = datetime.now(timezone.utc)
        session.end_latitude = payload.latitude
        session.end_longitude = payload.longitude
        session.end_address = payload.address
        if payload.notes:
            session.notes = payload.notes
        await db.commit()
        await db.refresh(session)
        return _map_session(session)

    @staticmethod
    async def list_sessions(
        db: AsyncSession,
        current_user: Employee,
        employee_id: Optional[str] = None,
        session_date: Optional[date] = None,
    ) -> List[FieldSessionResponse]:
        query = select(FieldSession)

        if current_user.role != "admin":
            subordinate_ids = await HierarchyService.get_subordinate_ids(db, current_user.id)
            allowed_ids = set(subordinate_ids) | {current_user.id}
            query = query.where(FieldSession.employee_id.in_(allowed_ids))

        if employee_id:
            query = query.where(FieldSession.employee_id == employee_id)
        if session_date:
            query = query.where(FieldSession.session_date == session_date)

        query = query.order_by(FieldSession.started_at.desc())
        result = await db.execute(query)
        return [_map_session(s) for s in result.scalars().all()]

    # ── Field Visits ────────────────────────────────────────────────────────

    @staticmethod
    async def create_visit(
        db: AsyncSession,
        current_user: Employee,
        assigned_to: str,
        payload: FieldVisitCreate,
    ) -> FieldVisitResponse:
        # Verify assignee exists
        emp = await db.execute(select(Employee).where(Employee.id == assigned_to))
        if not emp.scalar_one_or_none():
            raise HTTPException(status_code=404, detail=f"Employee {assigned_to} not found")

        visit = FieldVisit(
            employee_id=assigned_to,
            assigned_by=current_user.id,
            visit_type=payload.visit_type,
            title=payload.title,
            description=payload.description,
            scheduled_date=payload.scheduled_date,
            assigned_latitude=payload.assigned_latitude,
            assigned_longitude=payload.assigned_longitude,
            assigned_address=payload.assigned_address,
            allowed_radius_meters=payload.allowed_radius_meters,
            priority=payload.priority,
            status="ASSIGNED",
            doctor_name=payload.doctor_name,
            clinic_name=payload.clinic_name,
            lab_name=payload.lab_name,
            call_type=payload.call_type,
            area=payload.area,
            time_slot=payload.time_slot,
            visit_purpose=payload.visit_purpose,
            patient_name=payload.patient_name,
            client_reference=payload.client_reference,
        )
        db.add(visit)
        await db.commit()
        await db.refresh(visit)
        return _map_visit(visit)

    @staticmethod
    async def update_visit_status(
        db: AsyncSession,
        visit_id: str,
        current_user: Employee,
        payload: FieldVisitStatusUpdate,
    ) -> FieldVisitResponse:
        res = await db.execute(select(FieldVisit).where(FieldVisit.id == visit_id))
        visit = res.scalar_one_or_none()
        if not visit:
            raise HTTPException(status_code=404, detail="Field visit not found")

        # Only assignee or admin/manager can update
        if current_user.role != "admin" and visit.employee_id != current_user.id:
            subordinate_ids = await HierarchyService.get_subordinate_ids(db, current_user.id)
            if visit.employee_id not in subordinate_ids:
                raise HTTPException(status_code=403, detail="Not authorized to update this visit")

        new_status = payload.status.upper()
        now = datetime.now(timezone.utc)

        # State machine transitions
        valid_transitions = {
            "ASSIGNED": ["EN_ROUTE", "MISSED", "CANCELLED", "RESCHEDULED"],
            "EN_ROUTE": ["ARRIVED", "MISSED", "CANCELLED"],
            "ARRIVED": ["IN_PROGRESS", "MISSED", "CANCELLED"],
            "IN_PROGRESS": ["COMPLETED", "MISSED"],
            "COMPLETED": [],
            "MISSED": ["RESCHEDULED"],
            "CANCELLED": [],
            "RESCHEDULED": ["ASSIGNED"],
        }
        allowed = valid_transitions.get(visit.status, [])
        if new_status not in allowed:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot transition from {visit.status} to {new_status}",
            )

        visit.status = new_status

        if new_status == "EN_ROUTE":
            visit.started_at = now
        elif new_status == "ARRIVED":
            visit.arrived_at = now
            if payload.latitude and payload.longitude and visit.assigned_latitude and visit.assigned_longitude:
                dist = haversine_distance(
                    float(visit.assigned_latitude), float(visit.assigned_longitude),
                    payload.latitude, payload.longitude,
                )
                visit.arrival_distance_m = int(dist)
                if dist > visit.allowed_radius_meters:
                    visit.location_exception = True
            visit.actual_latitude = payload.latitude
            visit.actual_longitude = payload.longitude
            visit.actual_address = payload.address
        elif new_status == "COMPLETED":
            visit.completed_at = now
            if visit.started_at:
                started = visit.started_at
                # Make naive datetimes timezone-aware for subtraction
                if started.tzinfo is None:
                    started = started.replace(tzinfo=timezone.utc)
                visit.duration_minutes = int((now - started).total_seconds() / 60)
            visit.completion_notes = payload.completion_notes
            visit.proof_photo_url = payload.proof_photo_url

        await db.commit()
        await db.refresh(visit)
        return _map_visit(visit)

    @staticmethod
    async def list_visits(
        db: AsyncSession,
        current_user: Employee,
        employee_id: Optional[str] = None,
        scheduled_date: Optional[date] = None,
        visit_status: Optional[str] = None,
    ) -> List[FieldVisitResponse]:
        query = select(FieldVisit)

        if current_user.role != "admin":
            subordinate_ids = await HierarchyService.get_subordinate_ids(db, current_user.id)
            allowed_ids = set(subordinate_ids) | {current_user.id}
            query = query.where(FieldVisit.employee_id.in_(allowed_ids))

        if employee_id:
            query = query.where(FieldVisit.employee_id == employee_id)
        if scheduled_date:
            query = query.where(FieldVisit.scheduled_date == scheduled_date)
        if visit_status:
            query = query.where(FieldVisit.status == visit_status.upper())

        query = query.order_by(FieldVisit.scheduled_date.desc(), FieldVisit.created_at.desc())
        result = await db.execute(query)
        return [_map_visit(v) for v in result.scalars().all()]

    @staticmethod
    async def get_visit(
        db: AsyncSession,
        visit_id: str,
        current_user: Employee,
    ) -> FieldVisitResponse:
        res = await db.execute(select(FieldVisit).where(FieldVisit.id == visit_id))
        visit = res.scalar_one_or_none()
        if not visit:
            raise HTTPException(status_code=404, detail="Field visit not found")

        if current_user.role != "admin" and visit.employee_id != current_user.id:
            subordinate_ids = await HierarchyService.get_subordinate_ids(db, current_user.id)
            if visit.employee_id not in subordinate_ids:
                raise HTTPException(status_code=403, detail="Not authorized")

        return _map_visit(visit)


# ── Mappers ───────────────────────────────────────────────────────────────────

def _map_session(s: FieldSession) -> FieldSessionResponse:
    return FieldSessionResponse(
        id=s.id,
        employee_id=s.employee_id,
        session_date=s.session_date,
        status=s.status,
        started_at=s.started_at,
        ended_at=s.ended_at,
        start_latitude=float(s.start_latitude) if s.start_latitude else None,
        start_longitude=float(s.start_longitude) if s.start_longitude else None,
        start_address=s.start_address,
        end_latitude=float(s.end_latitude) if s.end_latitude else None,
        end_longitude=float(s.end_longitude) if s.end_longitude else None,
        end_address=s.end_address,
        notes=s.notes,
        created_at=s.created_at,
    )


def _map_visit(v: FieldVisit) -> FieldVisitResponse:
    return FieldVisitResponse(
        id=v.id,
        session_id=v.session_id,
        employee_id=v.employee_id,
        assigned_by=v.assigned_by,
        visit_type=v.visit_type,
        title=v.title,
        description=v.description,
        scheduled_date=v.scheduled_date,
        assigned_address=v.assigned_address,
        priority=v.priority,
        status=v.status,
        started_at=v.started_at,
        arrived_at=v.arrived_at,
        completed_at=v.completed_at,
        actual_latitude=float(v.actual_latitude) if v.actual_latitude else None,
        actual_longitude=float(v.actual_longitude) if v.actual_longitude else None,
        actual_address=v.actual_address,
        arrival_distance_m=v.arrival_distance_m,
        duration_minutes=v.duration_minutes,
        proof_photo_url=v.proof_photo_url,
        completion_notes=v.completion_notes,
        doctor_name=v.doctor_name,
        clinic_name=v.clinic_name,
        call_type=v.call_type,
        area=v.area,
        visit_purpose=v.visit_purpose,
        approval_status=v.approval_status,
        created_at=v.created_at,
    )
