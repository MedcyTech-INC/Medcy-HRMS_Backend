from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import require_role
from app.models.employee import Employee
from app.schemas.employee import EmployeeResponse, EmployeeCreate, EmployeeUpdate
from app.services.employee_service import employee_service
from app.services.hierarchy_service import hierarchy_service

router = APIRouter()


@router.get("", response_model=List[EmployeeResponse])
async def list_employees(
    hospital: Optional[str] = Query(None, description="Filter by hospital (vizag_ivf | medcy_hospitals | both)"),
    branch: Optional[str] = Query(None, description="Filter by branch (visakhapatnam | vizianagaram)"),
    status: Optional[str] = Query(None, description="Filter by status (active | inactive | pending)"),
    search: Optional[str] = Query(None, description="Search by name, email, designation, or ID"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """
    List employees scoped by hierarchy permissions and filters.
    Managers see subordinates; Admins see all; Employees see self.
    """
    employees, _ = await employee_service.list_employees(
        db,
        viewer=current_user,
        hospital=hospital,
        branch=branch,
        status_filter=status,
        search=search,
        limit=limit,
        offset=offset,
    )
    return [EmployeeResponse.model_validate(e) for e in employees]


@router.get("/org-chart")
async def get_org_chart(
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Return full organizational hierarchy tree structure."""
    return await hierarchy_service.build_org_tree(db)


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee_by_id(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Get single employee profile, enforcing hierarchy access check."""
    emp = await employee_service.get_employee_by_id(db, employee_id, viewer=current_user)
    return EmployeeResponse.model_validate(emp)


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    data: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("admin")),
):
    """Create a new employee (Admin only). Password is automatically hashed with bcrypt."""
    created = await employee_service.create_employee(db, data, creator=current_user)
    return EmployeeResponse.model_validate(created)


@router.patch("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: str,
    data: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("admin")),
):
    """Update employee details (Admin only)."""
    updated = await employee_service.update_employee(db, employee_id, data, actor=current_user)
    return EmployeeResponse.model_validate(updated)


@router.delete("/{employee_id}", status_code=status.HTTP_200_OK)
async def delete_employee(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(require_role("admin")),
):
    """Deactivate employee (Admin only)."""
    await employee_service.delete_employee(db, employee_id, actor=current_user)
    return {"message": f"Employee {employee_id} deactivated successfully"}
