"""
CivicTrack — Administration Schemas (TRD §8.8, FR-046..FR-050)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Priority, Status
from app.schemas.department import DepartmentOut

# ── Department Schemas (FR-046) ───────────────────────────────────────────────


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    code: str = Field(min_length=2, max_length=30)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool = True


class DepartmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    code: str | None = Field(default=None, min_length=2, max_length=30)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class DepartmentDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    description: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ── Category Schemas (FR-047) ─────────────────────────────────────────────────


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    code: str = Field(min_length=2, max_length=40)
    description: str | None = Field(default=None, max_length=500)
    department_id: int
    default_priority: Priority = Priority.MEDIUM
    is_active: bool = True


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    code: str | None = Field(default=None, min_length=2, max_length=40)
    description: str | None = Field(default=None, max_length=500)
    department_id: int | None = None
    default_priority: Priority | None = None
    is_active: bool | None = None


class CategoryDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    description: str | None = None
    department_id: int
    department: DepartmentOut
    default_priority: Priority
    is_active: bool
    created_at: datetime
    updated_at: datetime
    note: str | None = None


# ── Platform Activity Schemas (FR-048) ────────────────────────────────────────


class DepartmentActivityItem(BaseModel):
    id: int
    name: str
    open: int
    escalated: int


class RecentEventItem(BaseModel):
    complaint_id: int | None = None
    complaint_number: str
    event_type: str = "STATUS_CHANGE"
    from_status: Status | None = None
    to_status: Status
    actor: str | None = None
    note: str | None = None
    created_at: datetime


class PlatformActivityResponse(BaseModel):
    by_status: dict[str, int]
    by_department: list[DepartmentActivityItem]
    escalations_total: int
    escalation_window_minutes: int
    demo_mode: bool
    recent_events: list[RecentEventItem]


# ── Audit Log Schemas (FR-049, FR-050) ────────────────────────────────────────


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_user_id: int | None = None
    actor_role: str | None = None
    action: str
    entity_type: str
    entity_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogOut]
    page: int
    page_size: int
    total: int
    total_pages: int
