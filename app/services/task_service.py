from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import select, or_, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, aliased
from fastapi import HTTPException, status

from app.models.task import Task
from app.models.employee import Employee
from app.schemas.task import TaskCreate, TaskUpdate, TaskStatusUpdate, TaskResponse
from app.services.hierarchy_service import HierarchyService


class TaskService:
    @staticmethod
    async def get_tasks(
        db: AsyncSession,
        current_user: Employee,
        assigned_to: Optional[str] = None,
        task_date: Optional[date] = None,
        status_filter: Optional[str] = None,
    ) -> List[TaskResponse]:
        today = date.today()

        # Auto-close past in_progress tasks
        await db.execute(
            update(Task)
            .where(Task.status == "in_progress", Task.due_date < today)
            .values(status="incomplete", updated_at=datetime.now(timezone.utc))
        )
        await db.commit()

        # Build scope
        Assignee = aliased(Employee, name="assignee_emp")
        Creator = aliased(Employee, name="creator_emp")

        query = (
            select(
                Task,
                Assignee.name.label("assigned_employee_name"),
                Creator.name.label("created_by_name"),
            )
            .outerjoin(Assignee, Task.assigned_to == Assignee.id)
            .outerjoin(Creator, Task.created_by == Creator.id)
        )

        if current_user.role != "admin":
            subordinate_ids = await HierarchyService.get_subordinate_ids(db, current_user.id)
            allowed_ids = set(subordinate_ids) | {current_user.id}

            query = query.where(
                or_(
                    Task.assigned_to.in_(allowed_ids),
                    Task.created_by == current_user.id,
                )
            )

        if assigned_to:
            query = query.where(Task.assigned_to == assigned_to)
        if task_date:
            query = query.where(Task.due_date == task_date)
        if status_filter:
            query = query.where(Task.status == status_filter)

        query = query.order_by(Task.created_at.desc())
        result = await db.execute(query)
        rows = result.all()

        responses: List[TaskResponse] = []
        for task, assignee_name, creator_name in rows:
            responses.append(
                TaskResponse(
                    id=task.id,
                    title=task.title,
                    description=task.description,
                    priority=task.priority,
                    status=task.status,
                    task_date=task.due_date,
                    due_date=task.due_date,
                    assigned_to=task.assigned_to,
                    assigned_employee_name=assignee_name,
                    created_by=task.created_by,
                    created_by_name=creator_name,
                    completed_at=task.completed_at,
                    notes=task.notes or "",
                    created_at=task.created_at,
                    updated_at=task.updated_at,
                )
            )
        return responses

    @staticmethod
    async def get_task_by_id(
        db: AsyncSession,
        task_id: str,
        current_user: Employee,
    ) -> TaskResponse:
        Assignee = aliased(Employee, name="assignee_emp")
        Creator = aliased(Employee, name="creator_emp")

        query = (
            select(
                Task,
                Assignee.name.label("assigned_employee_name"),
                Creator.name.label("created_by_name"),
            )
            .outerjoin(Assignee, Task.assigned_to == Assignee.id)
            .outerjoin(Creator, Task.created_by == Creator.id)
            .where(Task.id == task_id)
        )
        res = await db.execute(query)
        row = res.first()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found",
            )
        task, assignee_name, creator_name = row

        if current_user.role != "admin":
            subordinate_ids = await HierarchyService.get_subordinate_ids(db, current_user.id)
            allowed_ids = set(subordinate_ids) | {current_user.id}
            if task.assigned_to not in allowed_ids and task.created_by != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this task",
                )

        return TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            priority=task.priority,
            status=task.status,
            task_date=task.due_date,
            due_date=task.due_date,
            assigned_to=task.assigned_to,
            assigned_employee_name=assignee_name,
            created_by=task.created_by,
            created_by_name=creator_name,
            completed_at=task.completed_at,
            notes=task.notes or "",
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    @staticmethod
    async def create_task(
        db: AsyncSession,
        current_user: Employee,
        payload: TaskCreate,
    ) -> TaskResponse:
        today = date.today()
        task_date = payload.task_date or payload.due_date or today
        description = payload.description or payload.title or ""
        title = payload.title or (
            description[:77] + "..." if len(description) > 80 else description or "Work Assignment"
        )

        if payload.assigned_to:
            emp_res = await db.execute(select(Employee).where(Employee.id == payload.assigned_to))
            if not emp_res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Assignee employee {payload.assigned_to} not found",
                )

        completed_at = datetime.now(timezone.utc) if payload.status == "completed" else None

        task = Task(
            title=title,
            description=description,
            priority=payload.priority,
            status=payload.status,
            assigned_to=payload.assigned_to,
            created_by=current_user.id,
            due_date=task_date,
            notes=payload.notes or "",
            completed_at=completed_at,
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)

        return await TaskService.get_task_by_id(db, task.id, current_user)

    @staticmethod
    async def update_task(
        db: AsyncSession,
        task_id: str,
        current_user: Employee,
        payload: TaskUpdate,
    ) -> TaskResponse:
        res = await db.execute(select(Task).where(Task.id == task_id))
        task = res.scalar_one_or_none()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found",
            )

        # Authorization check
        if current_user.role != "admin" and task.created_by != current_user.id:
            subordinate_ids = await HierarchyService.get_subordinate_ids(db, current_user.id)
            if task.assigned_to not in subordinate_ids and task.assigned_to != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to edit this task",
                )

        update_data = payload.model_dump(exclude_unset=True)

        if "description" in update_data:
            desc = update_data["description"]
            task.description = desc
            if "title" not in update_data or not update_data["title"]:
                task.title = desc[:77] + "..." if len(desc) > 80 else desc

        if "title" in update_data and update_data["title"]:
            task.title = update_data["title"]

        if "priority" in update_data and update_data["priority"]:
            task.priority = update_data["priority"]

        if "status" in update_data and update_data["status"]:
            new_status = update_data["status"]
            task.status = new_status
            if new_status == "completed":
                task.completed_at = datetime.now(timezone.utc)
            else:
                task.completed_at = None

        if "assigned_to" in update_data:
            task.assigned_to = update_data["assigned_to"]

        if "task_date" in update_data and update_data["task_date"]:
            task.due_date = update_data["task_date"]
        elif "due_date" in update_data and update_data["due_date"]:
            task.due_date = update_data["due_date"]

        if "notes" in update_data and update_data["notes"] is not None:
            task.notes = update_data["notes"]

        task.updated_at = datetime.now(timezone.utc)
        await db.commit()

        return await TaskService.get_task_by_id(db, task.id, current_user)

    @staticmethod
    async def update_status(
        db: AsyncSession,
        task_id: str,
        current_user: Employee,
        payload: TaskStatusUpdate,
    ) -> TaskResponse:
        res = await db.execute(select(Task).where(Task.id == task_id))
        task = res.scalar_one_or_none()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found",
            )

        # Assignee, creator, managers, or admin can update status
        if current_user.role != "admin" and task.assigned_to != current_user.id and task.created_by != current_user.id:
            subordinate_ids = await HierarchyService.get_subordinate_ids(db, current_user.id)
            if task.assigned_to not in subordinate_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update status of this task",
                )

        task.status = payload.status
        if payload.status == "completed":
            task.completed_at = datetime.now(timezone.utc)
        else:
            task.completed_at = None

        if payload.notes is not None:
            task.notes = payload.notes

        task.updated_at = datetime.now(timezone.utc)
        await db.commit()

        return await TaskService.get_task_by_id(db, task.id, current_user)

    @staticmethod
    async def delete_task(
        db: AsyncSession,
        task_id: str,
        current_user: Employee,
    ) -> None:
        res = await db.execute(select(Task).where(Task.id == task_id))
        task = res.scalar_one_or_none()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found",
            )

        if current_user.role != "admin" and task.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the task creator or an administrator can delete this task",
            )

        await db.delete(task)
        await db.commit()
