import pytest
import pytest_asyncio
from datetime import date
import httpx
from sqlalchemy import delete
from app.main import app
from app.database.engine import engine, async_session_factory
from app.models import Base, Employee, Attendance, BreakRecord, OfficeLocation
from app.utils.security import hash_password, create_access_token


@pytest_asyncio.fixture(autouse=True)
async def setup_attendance_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Clean existing test attendance & breaks
    async with async_session_factory() as session:
        await session.execute(delete(Attendance))
        await session.execute(delete(BreakRecord))
        await session.execute(delete(OfficeLocation))
        await session.execute(delete(Employee).where(Employee.id.in_(["EMP-ATT-001"])))
        await session.commit()

    # Seed test employee and office location
    async with async_session_factory() as session:
        emp = Employee(
            id="EMP-ATT-001",
            name="Attendance Tester",
            email="tester@medcy.com",
            password=hash_password("testpass"),
            role="employee",
            designation="Field Officer",
            joining_date=date(2026, 1, 1),
            basic_pay=30000.0,
            status="active",
            hierarchy_level="employee",
            hospital="medcy_hospitals",
            branch="visakhapatnam",
        )
        office = OfficeLocation(
            id="OFFICE-VIZAG-HQ",
            name="Medcy Vizag HQ",
            latitude=17.6868,
            longitude=83.2185,
            radius_meters=100,
            is_active=True,
        )
        session.add(emp)
        session.add(office)
        await session.commit()

    yield


@pytest.mark.asyncio
async def test_clock_in_geofence_enforcement():
    token = create_access_token("EMP-ATT-001")
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Deny punch outside geofence (20km away) for in_office punch
        far_res = await client.post(
            "/api/attendance/clock-in",
            json={
                "latitude": 17.8500,
                "longitude": 83.3500,
                "punchType": "in_office",
                "location": "Far Away Site"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert far_res.status_code == 400
        assert "Check-in denied" in far_res.json()["detail"]

        # 2. Allow punch inside geofence (within 100m of office)
        near_res = await client.post(
            "/api/attendance/clock-in",
            json={
                "latitude": 17.68685,
                "longitude": 83.21855,
                "punchType": "in_office",
                "location": "Vizag HQ Lobby"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert near_res.status_code == 201
        data = near_res.json()
        assert data["employeeId"] == "EMP-ATT-001"
        assert data["status"] == "present"
        assert data["sessionNumber"] == 1

        # 3. Reject duplicate punch-in while session active
        dup_res = await client.post(
            "/api/attendance/clock-in",
            json={"latitude": 17.6868, "longitude": 83.2185},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert dup_res.status_code == 400
        assert "already checked in" in dup_res.json()["detail"]

        # 4. Clock-out successfully
        out_res = await client.post(
            "/api/attendance/clock-out",
            json={"latitude": 17.6868, "longitude": 83.2185},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert out_res.status_code == 200
        out_data = out_res.json()
        assert out_data["checkOutTime"] is not None

        # 5. Out of office punch allowed anywhere
        out_of_office_res = await client.post(
            "/api/attendance/clock-in",
            json={
                "latitude": 18.2000,
                "longitude": 83.5000,
                "punchType": "out_of_office",
                "punchNote": "Camp at Srikakulam"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert out_of_office_res.status_code == 201
        assert out_of_office_res.json()["sessionNumber"] == 2


@pytest.mark.asyncio
async def test_breaks_lifecycle():
    token = create_access_token("EMP-ATT-001")
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. No active break initially
        act_res = await client.get("/api/breaks/active", headers={"Authorization": f"Bearer {token}"})
        assert act_res.status_code == 200
        assert act_res.json() is None

        # 2. Start lunch break
        start_res = await client.post(
            "/api/breaks/start",
            json={"breakType": "lunch"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert start_res.status_code == 201
        break_data = start_res.json()
        assert break_data["employeeId"] == "EMP-ATT-001"
        assert break_data["endTime"] is None

        # 3. Cannot start another break while active
        dup_res = await client.post(
            "/api/breaks/start",
            json={"breakType": "tea"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert dup_res.status_code == 400

        # 4. End active break
        end_res = await client.post("/api/breaks/end", headers={"Authorization": f"Bearer {token}"})
        assert end_res.status_code == 200
        assert end_res.json()["endTime"] is not None

        # 5. Fetch today's break list
        today_res = await client.get("/api/breaks/today", headers={"Authorization": f"Bearer {token}"})
        assert today_res.status_code == 200
        assert len(today_res.json()) == 1
