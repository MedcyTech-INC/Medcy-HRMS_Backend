from datetime import date, datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from fastapi import HTTPException, status

from app.models.break_record import BreakRecord


class BreakService:
    @staticmethod
    async def start_break(
        db: AsyncSession,
        employee_id: str,
        break_type: str = "lunch"
    ) -> BreakRecord:
        """Start a break session for an employee."""
        today = date.today()
        now_time = datetime.now().time().replace(microsecond=0)

        # Check if already on break
        stmt = select(BreakRecord).where(
            BreakRecord.employee_id == employee_id,
            BreakRecord.date == today,
            BreakRecord.end_time.is_(None)
        )
        active_break = (await db.execute(stmt)).scalars().first()
        if active_break:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are already on an active break. Please end it first.",
            )

        new_break = BreakRecord(
            employee_id=employee_id,
            date=today,
            start_time=now_time,
        )
        db.add(new_break)
        await db.commit()
        await db.refresh(new_break)
        return new_break

    @staticmethod
    async def end_break(
        db: AsyncSession,
        employee_id: str
    ) -> BreakRecord:
        """End an active break session and compute duration."""
        today = date.today()
        now_time = datetime.now().time().replace(microsecond=0)

        stmt = select(BreakRecord).where(
            BreakRecord.employee_id == employee_id,
            BreakRecord.date == today,
            BreakRecord.end_time.is_(None)
        ).order_by(desc(BreakRecord.created_at))
        active_break = (await db.execute(stmt)).scalars().first()

        if not active_break:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active break session found to end.",
            )

        active_break.end_time = now_time
        await db.commit()
        await db.refresh(active_break)
        return active_break

    @staticmethod
    async def get_active_break(
        db: AsyncSession,
        employee_id: str
    ) -> Optional[BreakRecord]:
        """Fetch active ongoing break if any."""
        today = date.today()
        stmt = select(BreakRecord).where(
            BreakRecord.employee_id == employee_id,
            BreakRecord.date == today,
            BreakRecord.end_time.is_(None)
        )
        return (await db.execute(stmt)).scalars().first()

    @staticmethod
    async def get_today_breaks(
        db: AsyncSession,
        employee_id: str,
        target_date: Optional[date] = None
    ) -> List[BreakRecord]:
        """Fetch all breaks taken on a date."""
        query_date = target_date or date.today()
        stmt = (
            select(BreakRecord)
            .where(BreakRecord.employee_id == employee_id, BreakRecord.date == query_date)
            .order_by(BreakRecord.start_time.asc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())


break_service = BreakService()
