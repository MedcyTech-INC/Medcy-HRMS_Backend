import pytest
from datetime import date
from sqlalchemy import select, delete
from app.database.engine import engine, async_session_factory
from app.models import Base, Employee


@pytest.mark.asyncio
async def test_create_tables_and_employee_model():
    # 1. Create tables in test database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. Insert test employee (clean previous if any)
    async with async_session_factory() as session:
        await session.execute(delete(Employee).where(Employee.id == "EMP-TEST-001"))
        await session.commit()
        emp = Employee(
            id="EMP-TEST-001",
            name="Test User",
            email="test@medcy.com",
            password="hashed_test_password",
            role="employee",
            designation="Software Engineer",
            joining_date=date(2026, 1, 1),
            basic_pay=50000.00,
            status="active",
            hierarchy_level="employee",
            hospital="medcy_hospitals",
            branch="visakhapatnam",
        )
        session.add(emp)
        await session.commit()

    # 3. Query employee back
    async with async_session_factory() as session:
        result = await session.execute(select(Employee).where(Employee.id == "EMP-TEST-001"))
        fetched = result.scalar_one_or_none()
        assert fetched is not None
        assert fetched.name == "Test User"
        assert fetched.email == "test@medcy.com"
        assert fetched.basic_pay == 50000.00
