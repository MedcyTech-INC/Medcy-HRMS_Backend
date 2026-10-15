from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.employee import Employee
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    ChangePasswordRequest,
)
from app.schemas.employee import EmployeeResponse
from app.services.auth_service import auth_service

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate employee and issue JWT access token + secure refresh token.
    Replaces: frontend plain text password matching in browser.
    """
    user = await auth_service.authenticate_user(db, request.email, request.password)
    access_token, refresh_token = await auth_service.create_tokens_for_user(
        db, user, device_info=request.device_info
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=EmployeeResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Rotate refresh token and issue a fresh access token.
    Prevents token replay attacks with automatic revocation of used tokens.
    """
    access_token, new_refresh_token, user = await auth_service.refresh_access_token(
        db, request.refresh_token
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        user=EmployeeResponse.model_validate(user),
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Revoke the user's refresh token on logout."""
    await auth_service.revoke_refresh_token(db, request.refresh_token)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=EmployeeResponse)
async def get_my_profile(
    current_user: Employee = Depends(get_current_user)
):
    """Return the currently authenticated employee's full profile."""
    return EmployeeResponse.model_validate(current_user)


@router.patch("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    request: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Change password with server-side bcrypt re-hashing."""
    await auth_service.change_password(
        db,
        user_id=current_user.id,
        current_password=request.current_password,
        new_password=request.new_password,
    )
    return {"message": "Password changed successfully"}
