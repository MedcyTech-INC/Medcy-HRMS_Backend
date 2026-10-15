import pytest
import pytest_asyncio
from datetime import date
import httpx
from sqlalchemy import delete
from app.main import app
from app.database.engine import engine, async_session_factory
from app.models import Base, Employee
from app.utils.security import hash_password, create_access_token


@pytest_asyncio.fixture(autouse=True)
async def setup_employees_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Clean existing test employees
    async with async_session_factory() as session:
        await session.execute(delete(Employee).where(Employee.id.like("EMP-TEST-%")))
        await session.commit()

    # Seed hierarchy: Admin (Director) -> Manager -> 2 Employees, plus unrelated Employee
    async with async_session_factory() as session:
        admin = Employee(
            id="EMP-TEST-ADMIN",
            name="Super Admin",
            email="admin@medcy.com",
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
        manager = Employee(
            id="EMP-TEST-MGR",
            name="Team Manager",
            email="manager@medcy.com",
            password=hash_password("mgrpass"),
            role="employee",
            designation="Branch Manager",
            joining_date=date(2026, 1, 1),
            basic_pay=60000.0,
            status="active",
            hierarchy_level="manager",
            hospital="medcy_hospitals",
            branch="visakhapatnam",
            reporting_to="EMP-TEST-ADMIN",
        )
        sub1 = Employee(
            id="EMP-TEST-SUB1",
            name="Subordinate One",
            email="sub1@medcy.com",
            password=hash_password("sub1pass"),
            role="employee",
            designation="Field Rep",
            joining_date=date(2026, 1, 1),
            basic_pay=30000.0,
            status="active",
            hierarchy_level="employee",
            hospital="medcy_hospitals",
            branch="visakhapatnam",
            reporting_to="EMP-TEST-MGR",
        )
        other_emp = Employee(
            id="EMP-TEST-OTHER",
            name="Other Team Rep",
            email="other@medcy.com",
            password=hash_password("otherpass"),
            role="employee",
            designation="Field Rep",
            joining_date=date(2026, 1, 1),
            basic_pay=30000.0,
            status="active",
            hierarchy_level="employee",
            hospital="vizag_ivf",
            branch="vizianagaram",
            reporting_to=None,
        )
        session.add_all([admin, manager, sub1, other_emp])
        await session.commit()

    yield


@pytest.mark.asyncio
async def test_admin_lists_all_employees():
    admin_token = create_access_token("EMP-TEST-ADMIN", claims={"role": "admin", "hierarchy_level": "executive"})
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/employees", headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        ids = [e["id"] for e in res.json()]
        assert "EMP-TEST-ADMIN" in ids
        assert "EMP-TEST-MGR" in ids
        assert "EMP-TEST-SUB1" in ids
        assert "EMP-TEST-OTHER" in ids


@pytest.mark.asyncio
async def test_manager_lists_subordinates_only():
    mgr_token = create_access_token("EMP-TEST-MGR", claims={"role": "employee", "hierarchy_level": "manager"})
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/employees", headers={"Authorization": f"Bearer {mgr_token}"})
        assert res.status_code == 200
        ids = [e["id"] for e in res.json()]
        assert "EMP-TEST-MGR" in ids
        assert "EMP-TEST-SUB1" in ids
        # Cannot see unrelated employee
        assert "EMP-TEST-OTHER" not in ids


@pytest.mark.asyncio
async def test_employee_can_only_see_self():
    emp_token = create_access_token("EMP-TEST-SUB1", claims={"role": "employee", "hierarchy_level": "employee"})
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/employees", headers={"Authorization": f"Bearer {emp_token}"})
        assert res.status_code == 200
        ids = [e["id"] for e in res.json()]
        assert ids == ["EMP-TEST-SUB1"]


@pytest.mark.asyncio
async def test_admin_creates_and_updates_employee():
    admin_token = create_access_token("EMP-TEST-ADMIN", claims={"role": "admin", "hierarchy_level": "executive"})
    emp_token = create_access_token("EMP-TEST-SUB1", claims={"role": "employee", "hierarchy_level": "employee"})
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Non-admin cannot create
        forbidden_res = await client.post(
            "/api/employees",
            json={
                "id": "EMP-TEST-NEW",
                "name": "New Candidate",
                "email": "candidate@medcy.com",
                "password": "secretpassword",
                "designation": "Intern",
                "joiningDate": "2026-02-01",
                "basicSalary": 25000,
                "role": "employee",
                "status": "active"
            },
            headers={"Authorization": f"Bearer {emp_token}"}
        )
        assert forbidden_res.status_code == 403

        # 2. Admin creates employee
        create_res = await client.post(
            "/api/employees",
            json={
                "id": "EMP-TEST-NEW",
                "name": "New Candidate",
                "email": "candidate@medcy.com",
                "password": "secretpassword",
                "designation": "Intern",
                "joiningDate": "2026-02-01",
                "basicSalary": 25000,
                "role": "employee",
                "status": "active",
                "hospital": "medcy_hospitals",
                "branch": "visakhapatnam"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert create_res.status_code == 201
        data = create_res.json()
        assert data["id"] == "EMP-TEST-NEW"
        assert data["name"] == "New Candidate"
        assert data["basicSalary"] == 25000

        # 3. Admin updates employee
        update_res = await client.patch(
            "/api/employees/EMP-TEST-NEW",
            json={"designation": "Junior Officer", "basicSalary": 32000},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert update_res.status_code == 200
        up_data = update_res.json()
        assert up_data["designation"] == "Junior Officer"
        assert up_data["basicSalary"] == 32000


@pytest.mark.asyncio
async def test_org_chart():
    admin_token = create_access_token("EMP-TEST-ADMIN", claims={"role": "admin"})
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/employees/org-chart", headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        tree = res.json()
        assert len(tree) > 0
