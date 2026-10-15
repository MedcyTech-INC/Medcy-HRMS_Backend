from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from fastapi import HTTPException, status

from app.models.employee import Employee
from app.models.audit_log import AuditLog
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.services.hierarchy_service import hierarchy_service
from app.utils.security import hash_password


class EmployeeService:
    @staticmethod
    async def list_employees(
        db: AsyncSession,
        viewer: Employee,
        hospital: Optional[str] = None,
        branch: Optional[str] = None,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[Employee], int]:
        """Fetch employees scoped by viewer's hierarchy permissions and filters."""
        query = select(Employee)

        # 1. Apply Hierarchy Scoping
        if viewer.role != "admin" and viewer.id not in {"EMP-EXEC-001", "EMP-EXEC-002", "OL001"}:
            subordinate_ids = await hierarchy_service.get_subordinate_ids(db, viewer.id)
            allowed_ids = set(subordinate_ids)
            allowed_ids.add(viewer.id)
            query = query.where(Employee.id.in_(allowed_ids))

        # 2. Apply Filters
        if hospital:
            query = query.where(or_(Employee.hospital == hospital, Employee.hospital == "both"))
        if branch:
            query = query.where(Employee.branch == branch)
        if status_filter:
            query = query.where(Employee.status == status_filter)
        if search:
            search_pattern = f"%{search.strip().lower()}%"
            query = query.where(
                or_(
                    func.lower(Employee.name).like(search_pattern),
                    func.lower(Employee.email).like(search_pattern),
                    func.lower(Employee.designation).like(search_pattern),
                    func.lower(Employee.id).like(search_pattern),
                )
            )

        # 3. Total Count
        count_query = select(func.count()).select_from(query.subquery())
        total_count = (await db.execute(count_query)).scalar_one()

        # 4. Pagination
        query = query.order_by(Employee.name.asc()).offset(offset).limit(limit)
        result = await db.execute(query)
        employees = result.scalars().all()

        return list(employees), total_count

    @staticmethod
    async def get_employee_by_id(
        db: AsyncSession,
        employee_id: str,
        viewer: Employee
    ) -> Employee:
        """Fetch single employee verifying hierarchy authorization."""
        can_access = await hierarchy_service.can_access_employee(db, viewer, employee_id)
        if not can_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this employee record",
            )

        stmt = select(Employee).where(Employee.id == employee_id)
        result = await db.execute(stmt)
        emp = result.scalar_one_or_none()

        if not emp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

        return emp

    @staticmethod
    async def create_employee(
        db: AsyncSession,
        data: EmployeeCreate,
        creator: Employee
    ) -> Employee:
        """Create a new employee with hashed password and audit trail."""
        # Check ID collision
        id_stmt = select(Employee).where(Employee.id == data.id)
        if (await db.execute(id_stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Employee ID already exists")

        # Check Email collision
        email_stmt = select(Employee).where(Employee.email == data.email.lower())
        if (await db.execute(email_stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        new_emp = Employee(
            id=data.id,
            name=data.name,
            email=data.email.lower(),
            password=hash_password(data.password),
            designation=data.designation,
            joining_date=data.joining_date,
            basic_pay=data.basic_pay,
            role=data.role,
            status=data.status,
            phone=data.phone,
            gender=data.gender,
            dob=data.dob,
            experience=data.experience,
            hospital=data.hospital,
            branch=data.branch,
            hierarchy_level=data.hierarchy_level,
            managed_branches=data.managed_branches or [],
            reporting_to=data.reporting_to,
            bank_details=data.bank_details.model_dump() if data.bank_details else {},
        )
        db.add(new_emp)

        # Audit Log
        audit = AuditLog(
            actor_id=creator.id,
            action="EMPLOYEE_CREATED",
            resource_type="employee",
            resource_id=data.id,
            new_value={"name": data.name, "email": data.email, "role": data.role},
        )
        db.add(audit)

        await db.commit()
        await db.refresh(new_emp)
        return new_emp

    @staticmethod
    async def update_employee(
        db: AsyncSession,
        employee_id: str,
        data: EmployeeUpdate,
        actor: Employee
    ) -> Employee:
        """Update employee details with audit trail."""
        emp = await EmployeeService.get_employee_by_id(db, employee_id, actor)

        update_data = data.model_dump(exclude_unset=True)
        old_snapshot = {"name": emp.name, "designation": emp.designation, "basic_pay": float(emp.basic_pay)}

        for field, value in update_data.items():
            if field == "bank_details" and value is not None:
                setattr(emp, "bank_details", value)
            elif hasattr(emp, field):
                setattr(emp, field, value)

        # Audit Log
        audit = AuditLog(
            actor_id=actor.id,
            action="EMPLOYEE_UPDATED",
            resource_type="employee",
            resource_id=employee_id,
            old_value=old_snapshot,
            new_value=update_data,
        )
        db.add(audit)

        await db.commit()
        await db.refresh(emp)
        return emp

    @staticmethod
    async def delete_employee(
        db: AsyncSession,
        employee_id: str,
        actor: Employee
    ) -> None:
        """Soft-delete an employee by setting status to inactive."""
        emp = await EmployeeService.get_employee_by_id(db, employee_id, actor)
        emp.status = "inactive"

        audit = AuditLog(
            actor_id=actor.id,
            action="EMPLOYEE_DEACTIVATED",
            resource_type="employee",
            resource_id=employee_id,
        )
        db.add(audit)
        await db.commit()


employee_service = EmployeeService()
