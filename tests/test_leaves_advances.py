import pytest
import pytest_asyncio
from datetime import date
import httpx
from sqlalchemy import delete, select
from app.main import app
from app.database.engine import engine, async_session_factory
from app.models import Base, Employee, LeaveRequest, LeaveBalance, Attendance, AdvanceRequest
from app.utils.security import hash_password, create_access_token


@pytest_asyncio.fixture(autouse=True)
async def setup_leaves_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Clean existing test data
    async with async_session_factory() as session:
        await session.execute(delete(LeaveRequest))
        await session.execute(delete(LeaveBalance))
        await session.execute(delete(Attendance))
        await session.execute(delete(AdvanceRequest))
        await session.execute(
            delete(Employee).where(
                (Employee.id.in_(["EMP-LEAVE-MGR", "EMP-LEAVE-USER", "EMP-LEAVE-ADMIN"]))
                | (Employee.email.in_(["leave.admin@medcy.com", "approver@medcy.com", "applicant@medcy.com"]))
            )
        )
        await session.commit()

    # Seed manager, employee, and admin
    async with async_session_factory() as session:
        admin = Employee(
            id="EMP-LEAVE-ADMIN",
            name="Payroll Director",
            email="leave.admin@medcy.com",
            password=hash_password("adminpass"),
            role="admin",
            designation="Director",
            joining_date=date(2026, 1, 1),
            basic_pay=100000.0,
            status="active",
            hierarchy_level="executive",
            hospital="both",
            branch="visakhapatnam",
        )
        mgr = Employee(
            id="EMP-LEAVE-MGR",
            name="Leave Approver",
            email="approver@medcy.com",
            password=hash_password("mgrpass"),
            role="employee",
            designation="Team Lead",
            joining_date=date(2026, 1, 1),
            basic_pay=50000.0,
            status="active",
            hierarchy_level="team_lead",
            hospital="medcy_hospitals",
            branch="visakhapatnam",
        )
        emp = Employee(
            id="EMP-LEAVE-USER",
            name="Leave Applicant",
            email="applicant@medcy.com",
            password=hash_password("userpass"),
            role="employee",
            designation="Field Rep",
            joining_date=date(2026, 1, 1),
            basic_pay=30000.0,
            status="active",
            hierarchy_level="employee",
            hospital="medcy_hospitals",
            branch="visakhapatnam",
            reporting_to="EMP-LEAVE-MGR",
        )
        session.add_all([admin, mgr, emp])
        await session.commit()

    yield


@pytest.mark.asyncio
async def test_atomic_leave_application_and_approval():
    user_token = create_access_token("EMP-LEAVE-USER", claims={"role": "employee", "hierarchy_level": "employee"})
    mgr_token = create_access_token("EMP-LEAVE-MGR", claims={"role": "employee", "hierarchy_level": "team_lead"})
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Apply for 3 days of sick leave
        apply_res = await client.post(
            "/api/leaves/apply",
            json={
                "type": "sick",
                "fromDate": "2026-04-10",
                "toDate": "2026-04-12",
                "reason": "Viral fever and rest advice"
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert apply_res.status_code == 201
        leave_id = apply_res.json()["id"]
        assert apply_res.json()["status"] == "pending"

        # 2. Team Lead fetches pending requests
        team_res = await client.get("/api/leaves/team-requests", headers={"Authorization": f"Bearer {mgr_token}"})
        assert team_res.status_code == 200
        req_ids = [r["id"] for r in team_res.json()]
        assert leave_id in req_ids

        # 3. Team Lead approves the leave
        approve_res = await client.patch(
            f"/api/leaves/{leave_id}/approve",
            json={"adminNote": "Approved, take care."},
            headers={"Authorization": f"Bearer {mgr_token}"}
        )
        assert approve_res.status_code == 200
        assert approve_res.json()["status"] == "approved"

    # 4. Verify ATOMIC Database updates directly
    async with async_session_factory() as session:
        # Verify LeaveBalance deduction
        bal_res = await session.execute(
            select(LeaveBalance).where(LeaveBalance.employee_id == "EMP-LEAVE-USER", LeaveBalance.leave_type == "sick")
        )
        balance = bal_res.scalar_one_or_none()
        assert balance is not None
        assert balance.used == 3  # 3 days deducted!

        # Verify Attendance records automatically populated with status='leave'
        att_res = await session.execute(
            select(Attendance).where(Attendance.employee_id == "EMP-LEAVE-USER").order_by(Attendance.date.asc())
        )
        attendances = att_res.scalars().all()
        assert len(attendances) == 3
        for att in attendances:
            assert att.status == "leave"


@pytest.mark.asyncio
async def test_salary_advance_lifecycle():
    user_token = create_access_token("EMP-LEAVE-USER", claims={"role": "employee"})
    admin_token = create_access_token("EMP-LEAVE-ADMIN", claims={"role": "admin"})
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Employee applies for advance
        req_res = await client.post(
            "/api/advances/request",
            json={
                "amount": 10000.0,
                "reason": "Family emergency",
                "advanceType": "salary",
                "repaymentMonths": 2
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert req_res.status_code == 201
        adv_data = req_res.json()
        assert adv_data["monthlyInstallment"] == 5000.0
        assert adv_data["status"] == "pending"
        adv_id = adv_data["id"]

        # 2. Admin approves advance
        app_res = await client.patch(
            f"/api/advances/{adv_id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert app_res.status_code == 200
        assert app_res.json()["status"] == "approved"
        assert app_res.json()["installmentsRemaining"] == 2
