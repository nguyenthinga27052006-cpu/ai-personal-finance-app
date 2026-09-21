from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.auth.security import normalize_email, validate_password


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str
    display_name: str | None = Field(default=None, max_length=120)
    security_pin: str | None = Field(default=None, pattern=r"^\d{6}$")

    @field_validator("email")
    @classmethod
    def normalize_email_value(cls, value: str) -> str:
        normalized = normalize_email(value)
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("Invalid email address")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password_value(cls, value: str) -> str:
        return validate_password(value)


class ResetPasswordWithPinRequest(BaseModel):
    email: str
    security_pin: str = Field(pattern=r"^\d{6}$")
    new_password: str

    @field_validator("email")
    @classmethod
    def normalize_email_value(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("new_password")
    @classmethod
    def validate_password_value(cls, value: str) -> str:
        return validate_password(value)


class UpdatePinRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_pin: str = Field(pattern=r"^\d{6}$")


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email_value(cls, value: str) -> str:
        return normalize_email(value)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    display_name: str | None
    role: str = "USER"
    default_currency: str
    timezone: str
    locale: str
    status: str
    created_at: datetime


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str
    user: UserResponse


class MessageResponse(BaseModel):
    message: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password_value(cls, value: str) -> str:
        return validate_password(value)
