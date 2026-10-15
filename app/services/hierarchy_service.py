from typing import List, Set, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from app.models.employee import Employee


class HierarchyService:
    @staticmethod
    async def get_subordinate_ids(db: AsyncSession, manager_id: str) -> List[str]:
        """
        Recursively resolve all employee IDs that report to a given manager.
        Uses recursive CTE on the reporting_to column (supported on both PostgreSQL and SQLite).
        """
        cte_query = text("""
            WITH RECURSIVE subordinates AS (
                SELECT id FROM "HRMS_employees" WHERE reporting_to = :manager_id
                UNION ALL
                SELECT e.id FROM "HRMS_employees" e
                INNER JOIN subordinates s ON e.reporting_to = s.id
            )
            SELECT id FROM subordinates
        """)
        result = await db.execute(cte_query, {"manager_id": manager_id})
        return [row[0] for row in result.fetchall()]

    @staticmethod
    async def can_access_employee(
        db: AsyncSession,
        viewer: Employee,
        target_employee_id: str
    ) -> bool:
        """
        Check if the viewer has administrative or hierarchical permission to access target_employee.
        - Admins and Directors can access anyone.
        - An employee can always access their own record.
        - Managers/Team leads can access anyone in their subordinate tree.
        """
        if viewer.role == "admin" or viewer.id in {"EMP-EXEC-001", "EMP-EXEC-002", "OL001"}:
            return True

        if viewer.id == target_employee_id:
            return True

        subordinates = await HierarchyService.get_subordinate_ids(db, viewer.id)
        return target_employee_id in subordinates

    @staticmethod
    async def build_org_tree(db: AsyncSession, root_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Build a hierarchical tree structure of employees for the org chart view."""
        stmt = select(Employee).where(Employee.status == "active")
        result = await db.execute(stmt)
        employees = result.scalars().all()

        emp_map = {e.id: {
            "id": e.id,
            "name": e.name,
            "email": e.email,
            "designation": e.designation,
            "role": e.role,
            "hierarchyLevel": e.hierarchy_level,
            "hospital": e.hospital,
            "branch": e.branch,
            "reportingTo": e.reporting_to,
            "children": []
        } for e in employees}

        tree = []
        for emp in employees:
            node = emp_map[emp.id]
            if emp.reporting_to and emp.reporting_to in emp_map:
                emp_map[emp.reporting_to]["children"].append(node)
            else:
                if not root_id or emp.id == root_id:
                    tree.append(node)

        return tree


hierarchy_service = HierarchyService()
