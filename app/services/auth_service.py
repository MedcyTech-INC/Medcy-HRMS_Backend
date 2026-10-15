from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status

from app.config import settings
from app.models.employee import Employee
from app.models.refresh_token import RefreshToken
from app.utils.security import (
    verify_password,
    hash_password,
    create_access_token,
    generate_refresh_token_string,
    hash_token_string,
)


class AuthService:
    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        email: str,
        password: str
    ) -> Employee:
        """Authenticate an employee by email and password, auto-migrating plain passwords to bcrypt."""
        clean_email = email.strip().lower()
        stmt = select(Employee).where(Employee.email == clean_email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is {user.status}. Please contact administrator.",
            )

        if not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Seamless password migration: if password wasn't hashed with bcrypt yet, hash it now!
        if not user.password.startswith(("$2b$", "$2a$", "$2y$")):
            user.password = hash_password(password)
            await db.commit()
            await db.refresh(user)

        return user

    @staticmethod
    async def create_tokens_for_user(
        db: AsyncSession,
        user: Employee,
        device_info: Optional[str] = None
    ) -> Tuple[str, str]:
        """Generate a signed JWT access token and persist a rotated refresh token."""
        claims = {
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "hierarchy_level": user.hierarchy_level or "employee",
            "hospital": user.hospital,
            "branch": user.branch,
        }
        access_token = create_access_token(subject=user.id, claims=claims)

        raw_refresh_token = generate_refresh_token_string()
        token_hash = hash_token_string(raw_refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_record = RefreshToken(
            employee_id=user.id,
            token_hash=token_hash,
            device_info=device_info,
            expires_at=expires_at,
            revoked=False,
        )
        db.add(refresh_record)
        await db.commit()

        return access_token, raw_refresh_token

    @staticmethod
    async def refresh_access_token(
        db: AsyncSession,
        raw_refresh_token: str
    ) -> Tuple[str, str, Employee]:
        """Rotate refresh token and issue a fresh access token."""
        token_hash = hash_token_string(raw_refresh_token)
        now = datetime.now(timezone.utc)

        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,
            RefreshToken.expires_at > now,
        )
        result = await db.execute(stmt)
        token_record = result.scalar_one_or_none()

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        # Fetch associated employee
        emp_stmt = select(Employee).where(Employee.id == token_record.employee_id)
        emp_result = await db.execute(emp_stmt)
        user = emp_result.scalar_one_or_none()

        if not user or user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive or not found",
            )

        # Revoke the used refresh token (Token Rotation pattern)
        token_record.revoked = True

        # Generate fresh tokens
        access_token, new_refresh_token = await AuthService.create_tokens_for_user(
            db, user, device_info=token_record.device_info
        )

        return access_token, new_refresh_token, user

    @staticmethod
    async def revoke_refresh_token(db: AsyncSession, raw_refresh_token: str) -> None:
        """Revoke a refresh token on logout."""
        token_hash = hash_token_string(raw_refresh_token)
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(revoked=True)
        )
        await db.execute(stmt)
        await db.commit()

    @staticmethod
    async def change_password(
        db: AsyncSession,
        user_id: str,
        current_password: str,
        new_password: str
    ) -> None:
        """Verify current password and set new bcrypt hashed password."""
        stmt = select(Employee).where(Employee.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if not verify_password(current_password, user.password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect current password")

        user.password = hash_password(new_password)
        await db.commit()


auth_service = AuthService()
