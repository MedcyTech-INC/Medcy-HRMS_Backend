import pytest
import pytest_asyncio
from datetime import date
import httpx
from sqlalchemy import delete
from app.main import app
from app.database.engine import engine, async_session_factory
from app.models import Base, Employee, RefreshToken
from app.utils.security import hash_password


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Clean previous test users/tokens
    async with async_session_factory() as session:
        await session.execute(delete(RefreshToken))
        await session.execute(delete(Employee).where(Employee.id.in_(["EMP-AUTH-001", "EMP-AUTH-002"])))
        await session.commit()

    # Seed test users
    async with async_session_factory() as session:
        # Active employee
        emp = Employee(
            id="EMP-AUTH-001",
            name="Alice Walker",
            email="alice@medcy.com",
            password=hash_password("securepassword123"),
            role="employee",
            designation="Field Rep",
            joining_date=date(2026, 1, 1),
            basic_pay=35000.0,
            status="active",
            hierarchy_level="employee",
            hospital="medcy_hospitals",
            branch="visakhapatnam",
        )
        # Inactive employee
        inactive = Employee(
            id="EMP-AUTH-002",
            name="Bob Terminated",
            email="bob@medcy.com",
            password=hash_password("bobpassword123"),
            role="employee",
            designation="Former Rep",
            joining_date=date(2026, 1, 1),
            basic_pay=30000.0,
            status="inactive",
            hierarchy_level="employee",
            hospital="medcy_hospitals",
            branch="visakhapatnam",
        )
        session.add(emp)
        session.add(inactive)
        await session.commit()

    yield


@pytest.mark.asyncio
async def test_auth_login_success():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/auth/login", json={
            "email": "alice@medcy.com",
            "password": "securepassword123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["id"] == "EMP-AUTH-001"
        assert data["user"]["email"] == "alice@medcy.com"
        assert data["user"]["role"] == "employee"


@pytest.mark.asyncio
async def test_auth_login_wrong_password():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/auth/login", json={
            "email": "alice@medcy.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_auth_login_inactive_user():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/auth/login", json={
            "email": "bob@medcy.com",
            "password": "bobpassword123"
        })
        assert response.status_code == 403
        assert "inactive" in response.json()["detail"]


@pytest.mark.asyncio
async def test_auth_me_endpoint_with_valid_and_invalid_tokens():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Login to get token
        login_res = await client.post("/api/auth/login", json={
            "email": "alice@medcy.com",
            "password": "securepassword123"
        })
        token = login_res.json()["access_token"]

        # 2. Access /api/auth/me with valid Bearer token
        me_res = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["id"] == "EMP-AUTH-001"
        assert me_data["name"] == "Alice Walker"

        # 3. Access without token -> 401
        unauth_res = await client.get("/api/auth/me")
        assert unauth_res.status_code == 401

        # 4. Access with forged token -> 401
        forged_res = await client.get("/api/auth/me", headers={"Authorization": "Bearer forged.invalid.token"})
        assert forged_res.status_code == 401


@pytest.mark.asyncio
async def test_auth_token_refresh_and_logout():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Login
        login_res = await client.post("/api/auth/login", json={
            "email": "alice@medcy.com",
            "password": "securepassword123"
        })
        refresh_token = login_res.json()["refresh_token"]

        # 2. Refresh token
        refresh_res = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        assert refresh_res.status_code == 200
        new_data = refresh_res.json()
        new_access_token = new_data["access_token"]
        new_refresh_token = new_data["refresh_token"]
        assert new_refresh_token != refresh_token

        # 3. Old refresh token cannot be reused
        reuse_res = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        assert reuse_res.status_code == 401

        # 4. Logout with new refresh token
        logout_res = await client.post(
            "/api/auth/logout",
            json={"refresh_token": new_refresh_token},
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert logout_res.status_code == 200

        # 5. Revoked token fails on refresh
        fail_res = await client.post("/api/auth/refresh", json={"refresh_token": new_refresh_token})
        assert fail_res.status_code == 401


@pytest.mark.asyncio
async def test_auth_change_password():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Login
        login_res = await client.post("/api/auth/login", json={
            "email": "alice@medcy.com",
            "password": "securepassword123"
        })
        token = login_res.json()["access_token"]

        # 2. Change password
        ch_res = await client.patch(
            "/api/auth/change-password",
            json={
                "current_password": "securepassword123",
                "new_password": "newsupersecretpass456"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert ch_res.status_code == 200

        # 3. Old password no longer works
        old_login = await client.post("/api/auth/login", json={
            "email": "alice@medcy.com",
            "password": "securepassword123"
        })
        assert old_login.status_code == 401

        # 4. New password works
        new_login = await client.post("/api/auth/login", json={
            "email": "alice@medcy.com",
            "password": "newsupersecretpass456"
        })
        assert new_login.status_code == 200
