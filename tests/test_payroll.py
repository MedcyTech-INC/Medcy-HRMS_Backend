import pytest
import pytest_asyncio
from datetime import date
import httpx
from sqlalchemy import delete

from app.main import app
from app.database.engine import engine, async_session_factory
from app.models import Base, Employee
from app.models.payroll import Payroll, Invoice
from app.utils.security import hash_password, create_access_token

ADMIN_ID = "EMP-PAY-ADMIN"
EMP_ID   = "EMP-PAY-EMP"


@pytest_asyncio.fixture(autouse=True)
async def setup_payroll_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        await session.execute(delete(Invoice))
        await session.execute(delete(Payroll))
        await session.execute(
            delete(Employee).where(
                Employee.email.in_(["pay.admin@medcy.com", "pay.emp@medcy.com"])
            )
        )
        await session.commit()

    async with async_session_factory() as session:
        admin = Employee(
            id=ADMIN_ID, name="Payroll Admin", email="pay.admin@medcy.com",
            password=hash_password("adminpass"), role="admin",
            designation="Director", joining_date=date(2026, 1, 1),
            status="active", hierarchy_level="executive",
            hospital="both", branch="visakhapatnam",
        )
        emp = Employee(
            id=EMP_ID, name="Field Rep", email="pay.emp@medcy.com",
            password=hash_password("emppass"), role="employee",
            designation="Representative", joining_date=date(2026, 1, 1),
            status="active", hierarchy_level="employee",
            hospital="medcy_hospitals", branch="visakhapatnam",
        )
        session.add_all([admin, emp])
        await session.commit()


@pytest.mark.asyncio
async def test_payroll_lifecycle():
    admin_token = create_access_token(ADMIN_ID, claims={"role": "admin"})
    emp_token   = create_access_token(EMP_ID,   claims={"role": "employee"})
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Admin generates payroll for employee
        create_res = await client.post(
            "/api/payroll",
            json={
                "employeeId": EMP_ID,
                "month": "2026-09",
                "basicPay": 30000.0,
                "allowances": [{"label": "HRA", "amount": 5000}],
                "deductions": [{"label": "PF", "amount": 1800}],
                "netPay": 33200.0,
                "workingDays": 26,
                "daysPresent": 25,
                "leavesTaken": 1,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert create_res.status_code == 201
        pr = create_res.json()
        payroll_id = pr["id"]
        assert pr["month"] == "2026-09"
        assert pr["netPay"] == 33200.0

        # Duplicate month is rejected
        dup_res = await client.post(
            "/api/payroll",
            json={
                "employeeId": EMP_ID, "month": "2026-09",
                "basicPay": 30000.0, "allowances": [], "deductions": [],
                "netPay": 30000.0,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert dup_res.status_code == 409

        # Employee can view their own payroll
        emp_list_res = await client.get(
            "/api/payroll",
            headers={"Authorization": f"Bearer {emp_token}"},
        )
        assert emp_list_res.status_code == 200
        payrolls = emp_list_res.json()
        assert len(payrolls) == 1
        assert payrolls[0]["employeeId"] == EMP_ID

        # Non-admin cannot generate payroll
        unauth_res = await client.post(
            "/api/payroll",
            json={
                "employeeId": EMP_ID, "month": "2026-10",
                "basicPay": 30000.0, "allowances": [], "deductions": [],
                "netPay": 30000.0,
            },
            headers={"Authorization": f"Bearer {emp_token}"},
        )
        assert unauth_res.status_code == 403


@pytest.mark.asyncio
async def test_invoice_lifecycle():
    admin_token = create_access_token(ADMIN_ID, claims={"role": "admin"})
    emp_token   = create_access_token(EMP_ID,   claims={"role": "employee"})
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Admin creates invoice
        create_res = await client.post(
            "/api/invoices",
            json={
                "invoiceNumber": "INV-2026-001",
                "clientName": "City Hospital",
                "clientDetails": "123 MG Road, Vizag",
                "items": [{"description": "Medical Supplies", "quantity": 10, "unitPrice": 500, "amount": 5000}],
                "total": 5900.0,
                "payableAmount": 5900.0,
                "taxPercent": 18.0,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert create_res.status_code == 201
        inv = create_res.json()
        assert inv["invoiceNumber"] == "INV-2026-001"
        assert inv["clientName"] == "City Hospital"

        # Duplicate invoice number rejected
        dup_res = await client.post(
            "/api/invoices",
            json={
                "invoiceNumber": "INV-2026-001",
                "clientName": "Other", "clientDetails": "Other",
                "items": [], "total": 0, "payableAmount": 0,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert dup_res.status_code == 409

        # Non-admin cannot view invoices
        unauth_res = await client.get(
            "/api/invoices",
            headers={"Authorization": f"Bearer {emp_token}"},
        )
        assert unauth_res.status_code == 403
