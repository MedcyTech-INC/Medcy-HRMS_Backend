from typing import Set
from fastapi import Depends, HTTPException, status
from app.dependencies.auth import get_current_user
from app.models.employee import Employee

# Hierarchy ranks ordered from lowest to highest privilege
HIERARCHY_RANK = {
    "employee": 1,
    "team_lead": 2,
    "manager": 3,
    "senior_manager": 4,
    "executive": 5,
}

# Master Executive bypass IDs (always have full administrative authority)
EXEMPT_ADMIN_IDS: Set[str] = {"EMP-EXEC-001", "EMP-EXEC-002", "OL001"}


def require_role(*allowed_roles: str):
    """Dependency that ensures the authenticated employee has one of the specified roles."""
    async def _role_guard(current_user: Employee = Depends(get_current_user)) -> Employee:
        if current_user.id in EXEMPT_ADMIN_IDS or current_user.role == "admin":
            return current_user

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this operation",
            )
        return current_user

    return _role_guard


def require_min_level(min_level: str):
    """Dependency checking that the user's hierarchy rank is at or above the required minimum level."""
    async def _level_guard(current_user: Employee = Depends(get_current_user)) -> Employee:
        if current_user.id in EXEMPT_ADMIN_IDS:
            return current_user

        user_level = current_user.hierarchy_level or "employee"
        user_rank = HIERARCHY_RANK.get(user_level, 1)
        required_rank = HIERARCHY_RANK.get(min_level, 1)

        if user_rank < required_rank and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires minimum hierarchy rank: {min_level}",
            )
        return current_user

    return _level_guard
