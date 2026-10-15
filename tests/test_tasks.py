import pytest
import pytest_asyncio
from datetime import date, timedelta
import httpx
from sqlalchemy import delete
from app.main import app
from app.database.engine import engine, async_session_factory
from app.models import Base, Employee, Task
from app.utils.security import hash_password, create_access_token


@pytest_asyncio.fixture(autouse=True)
async def setup_tasks_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        await session.execute(delete(Task))
        await session.execute(
            delete(Employee).where(
                (Employee.id.in_(["EMP-TASK-ADMIN", "EMP-TASK-MGR", "EMP-TASK-REP"]))
                | (Employee.email.in_(["task.admin@medcy.com", "task.mgr@medcy.com", "task.rep@medcy.com"]))
            )
        )
        await session.commit()

    async with async_session_factory() as session:
        admin = Employee(
            id="EMP-TASK-ADMIN",
            name="Task Admin",
            email="task.admin@medcy.com",
            password=hash_password("adminpass"),
            role="admin",
            designation="Admin",
            joining_date=date(2026, 1, 1),
            status="active",
            hierarchy_level="executive",
            hospital="both",
            branch="visakhapatnam",
        )
        mgr = Employee(
            id="EMP-TASK-MGR",
            name="Field Supervisor",
            email="task.mgr@medcy.com",
            password=hash_password("mgrpass"),
            role="employee",
            designation="Supervisor",
            joining_date=date(2026, 1, 1),
            status="active",
            hierarchy_level="manager",
            hospital="medcy_hospitals",
            branch="visakhapatnam",
        )
        rep = Employee(
            id="EMP-TASK-REP",
            name="Field Representative",
            email="task.rep@medcy.com",
            password=hash_password("reppass"),
            role="employee",
            designation="Representative",
            joining_date=date(2026, 1, 1),
            status="active",
            hierarchy_level="employee",
            hospital="medcy_hospitals",
            branch="visakhapatnam",
            reporting_to="EMP-TASK-MGR",
        )
        session.add_all([admin, mgr, rep])
        await session.commit()


@pytest.mark.asyncio
async def test_task_lifecycle_and_scoping():
    admin_token = create_access_token("EMP-TASK-ADMIN", claims={"role": "admin"})
    mgr_token = create_access_token("EMP-TASK-MGR", claims={"role": "employee"})
    rep_token = create_access_token("EMP-TASK-REP", claims={"role": "employee"})
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Manager creates task for Rep
        create_res = await client.post(
            "/api/tasks",
            json={
                "title": "Visit ABC Clinic",
                "description": "Deliver sample brochure and follow up with Dr. Sharma",
                "priority": "high",
                "assignedTo": "EMP-TASK-REP",
                "dueDate": str(date.today()),
            },
            headers={"Authorization": f"Bearer {mgr_token}"},
        )
        assert create_res.status_code == 201
        task_data = create_res.json()
        task_id = task_data["id"]
        assert task_data["title"] == "Visit ABC Clinic"
        assert task_data["priority"] == "high"
        assert task_data["status"] == "in_progress"
        assert task_data["assignedTo"] == "EMP-TASK-REP"
        assert task_data["assignedEmployeeName"] == "Field Representative"
        assert task_data["createdByName"] == "Field Supervisor"

        # 2. Rep views their tasks
        rep_list_res = await client.get(
            "/api/tasks",
            headers={"Authorization": f"Bearer {rep_token}"},
        )
        assert rep_list_res.status_code == 200
        rep_tasks = rep_list_res.json()
        assert len(rep_tasks) == 1
        assert rep_tasks[0]["id"] == task_id

        # 3. Rep updates task status to 'completed' with notes
        status_res = await client.patch(
            f"/api/tasks/{task_id}/status",
            json={"status": "completed", "notes": "Samples delivered successfully."},
            headers={"Authorization": f"Bearer {rep_token}"},
        )
        assert status_res.status_code == 200
        completed_data = status_res.json()
        assert completed_data["status"] == "completed"
        assert completed_data["completedAt"] is not None
        assert completed_data["notes"] == "Samples delivered successfully."

        # 4. Manager deletes task
        del_res = await client.delete(
            f"/api/tasks/{task_id}",
            headers={"Authorization": f"Bearer {mgr_token}"},
        )
        assert del_res.status_code == 204

        # 5. Verify deleted
        get_res = await client.get(
            f"/api/tasks/{task_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_past_due_task_auto_close():
    admin_token = create_access_token("EMP-TASK-ADMIN", claims={"role": "admin"})
    transport = httpx.ASGITransport(app=app)

    # Seed an overdue task in past date directly
    past_date = date.today() - timedelta(days=2)
    async with async_session_factory() as session:
        overdue_task = Task(
            title="Old Pending Report",
            description="Submit survey from 2 days ago",
            priority="medium",
            status="in_progress",
            assigned_to="EMP-TASK-REP",
            created_by="EMP-TASK-ADMIN",
            due_date=past_date,
        )
        session.add(overdue_task)
        await session.commit()
        task_id = overdue_task.id

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Listing tasks triggers auto-closure of overdue tasks
        res = await client.get("/api/tasks", headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        tasks = res.json()
        found = [t for t in tasks if t["id"] == task_id]
        assert len(found) == 1
        assert found[0]["status"] == "incomplete"  # Auto-closed!
