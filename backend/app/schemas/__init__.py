"""
CivicTrack — Schemas package
"""

from __future__ import annotations

from app.schemas.admin import (
    AuditLogListResponse,
    AuditLogOut,
    CategoryCreate,
    CategoryDetailOut,
    CategoryUpdate,
    DepartmentActivityItem,
    DepartmentCreate,
    DepartmentDetailOut,
    DepartmentUpdate,
    PlatformActivityResponse,
    RecentEventItem,
)
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.department import DepartmentOut
from app.schemas.superintendent import (
    ComplaintDetailResponse,
    EscalatedComplaintItem,
    EscalationQueueResponse,
    EscalationQueueSummary,
    PublicOfficerOut,
    ResolveComplaintRequest,
    ResolveComplaintResponse,
    SuperintendentActionCreate,
    SuperintendentActionResponse,
    TimelineEventOut,
)
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
    "PublicOfficerOut",
    "DepartmentCreate",
    "DepartmentUpdate",
    "DepartmentDetailOut",
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryDetailOut",
    "DepartmentActivityItem",
    "RecentEventItem",
    "PlatformActivityResponse",
    "AuditLogOut",
    "AuditLogListResponse",
    "EscalatedComplaintItem",
    "EscalationQueueSummary",
    "EscalationQueueResponse",
    "SuperintendentActionCreate",
    "SuperintendentActionResponse",
    "ResolveComplaintRequest",
    "ResolveComplaintResponse",
    "TimelineEventOut",
    "ComplaintDetailResponse",
]
