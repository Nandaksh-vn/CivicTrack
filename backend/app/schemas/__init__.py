"""
CivicTrack — Schemas package
"""

from __future__ import annotations

from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.department import DepartmentOut
from app.schemas.user import AdminUserCreate, AdminUserUpdate, PublicUser, UserListResponse

__all__ = [
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    "PublicUser",
    "AdminUserCreate",
    "AdminUserUpdate",
    "UserListResponse",
    "DepartmentOut",
]
