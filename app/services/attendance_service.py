from datetime import date, datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from fastapi import HTTPException, status

from app.models.attendance import Attendance
from app.models.employee import Employee
from app.services.geofence_service import geofence_service
from app.services.hierarchy_service import hierarchy_service


class AttendanceService:
    @staticmethod
    async def clock_in(
        db: AsyncSession,
        employee_id: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        accuracy_meters: Optional[float] = None,
        location: Optional[str] = None,
        photo_url: Optional[str] = None,
        punch_type: str = "in_office",
        punch_note: Optional[str] = None,
    ) -> Attendance:
        """
        Clock in an employee with server-side anti-spoofing geofence verification.
        Replaces client-side haversine math.
        """
        # 1. Server-side Geofence Enforcement for in-office punches
        if punch_type == "in_office" and latitude is not None and longitude is not None:
            geo_res = await geofence_service.validate_location(
                db, latitude, longitude, accuracy_meters
            )
            if not geo_res.allowed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"You are {geo_res.distance_meters}m from {geo_res.nearest_office_name or 'the office'}. Check-in denied.",
                )

        today = date.today()
        now_time = datetime.now().time().replace(microsecond=0)

        # 2. Check current sessions today to determine session_number
        stmt = (
            select(Attendance)
            .where(Attendance.employee_id == employee_id, Attendance.date == today)
            .order_by(desc(Attendance.session_number))
        )
        existing_sessions = (await db.execute(stmt)).scalars().all()

        # Check if already clocked in with no clock-out
        if existing_sessions and existing_sessions[0].check_out_time is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are already checked in. Please check out before starting a new session.",
            )

        next_session_number = (existing_sessions[0].session_number + 1) if existing_sessions else 1
        lat_lng_str = f"{latitude},{longitude}" if (latitude is not None and longitude is not None) else None

        record = Attendance(
            employee_id=employee_id,
            date=today,
            status="present",
            check_in_time=now_time,
            check_in_location=location,
            check_in_lat_lng=lat_lng_str,
            check_in_photo_url=photo_url,
            punch_type=punch_type,
            punch_note=punch_note,
            session_number=next_session_number,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record

    @staticmethod
    async def clock_out(
        db: AsyncSession,
        employee_id: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        location: Optional[str] = None,
        photo_url: Optional[str] = None,
    ) -> Attendance:
        """Clock out the employee's active session and compute total duration."""
        today = date.today()
        now_time = datetime.now().time().replace(microsecond=0)

        stmt = (
            select(Attendance)
            .where(
                Attendance.employee_id == employee_id,
                Attendance.date == today,
                Attendance.check_out_time.is_(None)
            )
            .order_by(desc(Attendance.session_number))
        )
        active_record = (await db.execute(stmt)).scalars().first()

        if not active_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active check-in session found for today to clock out from.",
            )

        active_record.check_out_time = now_time
        active_record.check_out_photo_url = photo_url

        # Compute total hours
        if active_record.check_in_time:
            t_in = datetime.combine(today, active_record.check_in_time)
            t_out = datetime.combine(today, now_time)
            total_sec = max(0, (t_out - t_in).total_seconds())
            active_record.total_hours = round(total_sec / 3600.0, 2)

        await db.commit()
        await db.refresh(active_record)
        return active_record

    @staticmethod
    async def get_today_sessions(
        db: AsyncSession,
        employee_id: str,
        target_date: Optional[date] = None
    ) -> List[Attendance]:
        """Fetch all attendance sessions for a specific date."""
        query_date = target_date or date.today()
        stmt = (
            select(Attendance)
            .where(Attendance.employee_id == employee_id, Attendance.date == query_date)
            .order_by(Attendance.session_number.asc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_today_locations(
        db: AsyncSession,
        viewer: Employee,
        target_date: Optional[date] = None
    ) -> List[dict]:
        """Admin/Manager dashboard: Returns GPS pins for all employee check-ins today."""
        query_date = target_date or date.today()
        query = (
            select(Attendance, Employee.name)
            .join(Employee, Attendance.employee_id == Employee.id)
            .where(Attendance.date == query_date, Attendance.check_in_lat_lng.is_not(None))
        )

        if viewer.role != "admin" and viewer.id not in {"EMP-EXEC-001", "EMP-EXEC-002", "OL001"}:
            sub_ids = await hierarchy_service.get_subordinate_ids(db, viewer.id)
            allowed_ids = set(sub_ids) | {viewer.id}
            query = query.where(Attendance.employee_id.in_(allowed_ids))

        rows = (await db.execute(query)).all()
        pins = []
        for att, emp_name in rows:
            if att.check_in_lat_lng and "," in att.check_in_lat_lng:
                try:
                    parts = att.check_in_lat_lng.split(",")
                    lat, lng = float(parts[0].strip()), float(parts[1].strip())
                    pins.append({
                        "employeeId": att.employee_id,
                        "employeeName": emp_name,
                        "latitude": lat,
                        "longitude": lng,
                        "locationName": att.check_in_location,
                        "checkInTime": att.check_in_time.isoformat() if att.check_in_time else None,
                        "photoUrl": att.check_in_photo_url,
                    })
                except Exception:
                    continue
        return pins


attendance_service = AttendanceService()
