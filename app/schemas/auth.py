from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from app.schemas.employee import EmployeeResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    device_info: Optional[str] = Field(default=None, alias="deviceInfo")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: EmployeeResponse


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)
