from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.employee import Employee
from app.schemas.task import TaskCreate, TaskUpdate, TaskStatusUpdate, TaskResponse
from app.services.task_service import TaskService

router = APIRouter()


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    assigned_to: Optional[str] = Query(None, alias="assignedTo"),
    task_date: Optional[date] = Query(None, alias="taskDate"),
    status: Optional[str] = Query(None),
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TaskService.get_tasks(
        db=db,
        current_user=current_user,
        assigned_to=assigned_to,
        task_date=task_date,
        status_filter=status,
    )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TaskService.create_task(db=db, current_user=current_user, payload=payload)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TaskService.get_task_by_id(db=db, task_id=task_id, current_user=current_user)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    payload: TaskUpdate,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TaskService.update_task(
        db=db,
        task_id=task_id,
        current_user=current_user,
        payload=payload,
    )


@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: str,
    payload: TaskStatusUpdate,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TaskService.update_status(
        db=db,
        task_id=task_id,
        current_user=current_user,
        payload=payload,
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await TaskService.delete_task(db=db, task_id=task_id, current_user=current_user)
