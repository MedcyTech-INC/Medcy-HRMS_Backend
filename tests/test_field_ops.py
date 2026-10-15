import pytest
import pytest_asyncio
from datetime import date
import httpx
from sqlalchemy import delete

from app.main import app
from app.database.engine import engine, async_session_factory
from app.models import Base, Employee
from app.utils.security import hash_password, create_access_token

ADMIN_ID = "EMP-FO-ADMIN"
MGR_ID   = "EMP-FO-MGR"
REP_ID   = "EMP-FO-REP"


@pytest_asyncio.fixture(autouse=True)
async def setup_field_ops_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        # Clean up related tables in dependency order
        from app.models.field_ops import FieldVisit, FieldSession, FieldVisitEvent, FieldVisitProof
        from app.models.doctor_visit import DoctorVisit
        from app.models.asha_encounter import ASHAEncounter
        await session.execute(delete(FieldVisitProof))
        await session.execute(delete(FieldVisitEvent))
        await session.execute(delete(FieldVisit))
        await session.execute(delete(FieldSession))
        await session.execute(delete(DoctorVisit))
        await session.execute(delete(ASHAEncounter))
        await session.execute(
            delete(Employee).where(
                Employee.email.in_([
                    "fo.admin@medcy.com", "fo.mgr@medcy.com", "fo.rep@medcy.com"
                ])
            )
        )
        await session.commit()

    async with async_session_factory() as session:
        admin = Employee(
            id=ADMIN_ID, name="FO Admin", email="fo.admin@medcy.com",
            password=hash_password("adminpass"), role="admin",
            designation="Admin", joining_date=date(2026, 1, 1),
            status="active", hierarchy_level="executive",
            hospital="both", branch="visakhapatnam",
        )
        mgr = Employee(
            id=MGR_ID, name="FO Manager", email="fo.mgr@medcy.com",
            password=hash_password("mgrpass"), role="employee",
            designation="Supervisor", joining_date=date(2026, 1, 1),
            status="active", hierarchy_level="manager",
            hospital="medcy_hospitals", branch="visakhapatnam",
        )
        rep = Employee(
            id=REP_ID, name="FO Representative", email="fo.rep@medcy.com",
            password=hash_password("reppass"), role="employee",
            designation="Representative", joining_date=date(2026, 1, 1),
            status="active", hierarchy_level="employee",
            hospital="medcy_hospitals", branch="visakhapatnam",
            reporting_to=MGR_ID,
        )
        session.add_all([admin, mgr, rep])
        await session.commit()


# ── Field Sessions ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_field_session_lifecycle():
    rep_token = create_access_token(REP_ID, claims={"role": "employee"})
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Start session
        start_res = await client.post(
            "/api/field-ops/sessions/start",
            json={"latitude": 17.6868, "longitude": 83.2185, "address": "MVP Colony, VSP"},
            headers={"Authorization": f"Bearer {rep_token}"},
        )
        assert start_res.status_code == 201
        session_data = start_res.json()
        session_id = session_data["id"]
        assert session_data["status"] == "active"
        assert session_data["employeeId"] == REP_ID

        # Can't open a second session same day
        dup_res = await client.post(
            "/api/field-ops/sessions/start",
            json={"latitude": 17.6868, "longitude": 83.2185},
            headers={"Authorization": f"Bearer {rep_token}"},
        )
        assert dup_res.status_code == 409

        # End session
        end_res = await client.post(
            f"/api/field-ops/sessions/{session_id}/end",
            json={"latitude": 17.7000, "longitude": 83.2300, "address": "Home"},
            headers={"Authorization": f"Bearer {rep_token}"},
        )
        assert end_res.status_code == 200
        ended_data = end_res.json()
        assert ended_data["status"] == "completed"
        assert ended_data["endedAt"] is not None


# ── Field Visit State Machine ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_field_visit_state_machine():
    admin_token = create_access_token(ADMIN_ID, claims={"role": "admin"})
    rep_token   = create_access_token(REP_ID,   claims={"role": "employee"})
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Admin creates a visit for the rep
        create_res = await client.post(
            "/api/field-ops/visits",
            params={"assignedTo": REP_ID},
            json={
                "title": "Visit City Pharmacy",
                "visitType": "DOCTOR",
                "scheduledDate": str(date.today()),
                "doctorName": "Dr. Reddy",
                "assignedLatitude": 17.6868,
                "assignedLongitude": 83.2185,
                "allowedRadiusMeters": 500,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert create_res.status_code == 201
        visit = create_res.json()
        visit_id = visit["id"]
        assert visit["status"] == "ASSIGNED"
        assert visit["doctorName"] == "Dr. Reddy"

        # Rep moves to EN_ROUTE
        en_route_res = await client.patch(
            f"/api/field-ops/visits/{visit_id}/status",
            json={"status": "EN_ROUTE"},
            headers={"Authorization": f"Bearer {rep_token}"},
        )
        assert en_route_res.status_code == 200
        assert en_route_res.json()["status"] == "EN_ROUTE"

        # Invalid state jump (EN_ROUTE -> COMPLETED) should fail
        bad_res = await client.patch(
            f"/api/field-ops/visits/{visit_id}/status",
            json={"status": "COMPLETED"},
            headers={"Authorization": f"Bearer {rep_token}"},
        )
        assert bad_res.status_code == 409

        # Rep arrives within radius
        arrived_res = await client.patch(
            f"/api/field-ops/visits/{visit_id}/status",
            json={"status": "ARRIVED", "latitude": 17.6868, "longitude": 83.2185},
            headers={"Authorization": f"Bearer {rep_token}"},
        )
        assert arrived_res.status_code == 200
        assert arrived_res.json()["status"] == "ARRIVED"

        # IN_PROGRESS
        in_prog_res = await client.patch(
            f"/api/field-ops/visits/{visit_id}/status",
            json={"status": "IN_PROGRESS"},
            headers={"Authorization": f"Bearer {rep_token}"},
        )
        assert in_prog_res.status_code == 200

        # COMPLETED
        comp_res = await client.patch(
            f"/api/field-ops/visits/{visit_id}/status",
            json={"status": "COMPLETED", "completionNotes": "Samples delivered"},
            headers={"Authorization": f"Bearer {rep_token}"},
        )
        assert comp_res.status_code == 200
        comp_data = comp_res.json()
        assert comp_data["status"] == "COMPLETED"
        assert comp_data["completedAt"] is not None
        assert comp_data["completionNotes"] == "Samples delivered"


# ── Doctor Visits ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_doctor_visit_crud_and_approval():
    rep_token   = create_access_token(REP_ID,   claims={"role": "employee"})
    admin_token = create_access_token(ADMIN_ID, claims={"role": "admin"})
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Rep logs a doctor visit
        create_res = await client.post(
            "/api/doctor-visits",
            json={"visitDate": str(date.today()), "doctorName": "Dr. Rao", "clinicName": "City Clinic"},
            headers={"Authorization": f"Bearer {rep_token}"},
        )
        assert create_res.status_code == 201
        dv = create_res.json()
        dv_id = dv["id"]
        assert dv["status"] == "planned"
        assert dv["approvalStatus"] == "pending"
        assert dv["doctorName"] == "Dr. Rao"

        # Admin approves
        approve_res = await client.patch(
            f"/api/doctor-visits/{dv_id}",
            json={"approvalStatus": "approved"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert approve_res.status_code == 200
        assert approve_res.json()["approvalStatus"] == "approved"
        assert approve_res.json()["approvedBy"] == ADMIN_ID


# ── ASHA Encounters ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_asha_encounter_lifecycle():
    rep_token = create_access_token(REP_ID, claims={"role": "employee"})
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Create encounter
        create_res = await client.post(
            "/api/asha-encounters",
            json={
                "ashaName": "Sunita Devi",
                "village": "Kommadi",
                "encounterDate": str(date.today()),
                "referralsCount": 3,
                "hospitalName": "Medcy Hospital",
            },
            headers={"Authorization": f"Bearer {rep_token}"},
        )
        assert create_res.status_code == 201
        enc = create_res.json()
        enc_id = enc["id"]
        assert enc["ashaName"] == "Sunita Devi"
        assert enc["referralsCount"] == 3

        # Update referrals count
        update_res = await client.patch(
            f"/api/asha-encounters/{enc_id}",
            json={"referralsCount": 5, "notes": "Follow-up scheduled"},
            headers={"Authorization": f"Bearer {rep_token}"},
        )
        assert update_res.status_code == 200
        assert update_res.json()["referralsCount"] == 5
        assert update_res.json()["notes"] == "Follow-up scheduled"

        # List by employee
        list_res = await client.get(
            "/api/asha-encounters",
            params={"employeeId": REP_ID},
            headers={"Authorization": f"Bearer {rep_token}"},
        )
        assert list_res.status_code == 200
        assert len(list_res.json()) == 1
