from datetime import date, datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field

TaskPriority = Literal["low", "medium", "high", "urgent"]
TaskStatus = Literal["in_progress", "completed", "incomplete"]


class TaskCreate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: TaskPriority = "medium"
    status: TaskStatus = "in_progress"
    assigned_to: Optional[str] = Field(None, alias="assignedTo")
    task_date: Optional[date] = Field(None, alias="taskDate")
    due_date: Optional[date] = Field(None, alias="dueDate")
    notes: Optional[str] = ""

    model_config = ConfigDict(populate_by_name=True)


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    assigned_to: Optional[str] = Field(None, alias="assignedTo")
    task_date: Optional[date] = Field(None, alias="taskDate")
    due_date: Optional[date] = Field(None, alias="dueDate")
    notes: Optional[str] = None
    completed_at: Optional[datetime] = Field(None, alias="completedAt")

    model_config = ConfigDict(populate_by_name=True)


class TaskStatusUpdate(BaseModel):
    status: TaskStatus
    notes: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    priority: str
    status: str
    task_date: Optional[date] = Field(None, alias="taskDate")
    due_date: Optional[date] = Field(None, alias="dueDate")
    assigned_to: Optional[str] = Field(None, alias="assignedTo")
    assigned_employee_name: Optional[str] = Field(None, alias="assignedEmployeeName")
    created_by: Optional[str] = Field(None, alias="createdBy")
    created_by_name: Optional[str] = Field(None, alias="createdByName")
    completed_at: Optional[datetime] = Field(None, alias="completedAt")
    notes: Optional[str] = ""
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
