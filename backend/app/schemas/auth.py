"""
CivicTrack — Authentication Schemas (TRD §8.3, FR-001, FR-002)
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.user import PublicUser

_PHONE_REGEX = re.compile(r"^[0-9+\s\-]{7,20}$")
_EMAIL_REGEX = re.compile(r"^[\w\.\+\-]+@[\w\-]+(\.[\w\-]+)+$")


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=3, max_length=190)
    password: str = Field(min_length=8, max_length=72)
    phone: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not _EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email address format.")
        return clean

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is not None:
            v_clean = v.strip()
            if v_clean and not _PHONE_REGEX.match(v_clean):
                raise ValueError(
                    "Phone number must be 7 to 20 characters and contain only digits, +, spaces, or dashes."
                )
            return v_clean or None
        return None


class LoginRequest(BaseModel):
    email: str = Field(min_length=1, max_length=190)
    password: str = Field(min_length=1, max_length=72)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not _EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email address format.")
        return clean


class TokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    token: str
    token_type: str = "bearer"
    expires_in: int
    user: PublicUser
