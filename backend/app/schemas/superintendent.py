"""
CivicTrack — Superintendent Schemas (TRD §8.6, FR-035..041)
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import OfficerActionType, Status
from app.schemas.department import DepartmentOut


class PublicOfficerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str


class EscalatedComplaintItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    complaint_number: str
    title: str
    department: DepartmentOut
    accepted_at: datetime | None = None
    resolution_due_at: datetime | None = None
    escalated_at: datetime | None = None
    overdue_seconds: int = 0
    current_overdue_seconds: int = 0
    status: Status
    last_action_at: datetime | None = None


class EscalationQueueSummary(BaseModel):
    open: int
    oldest_overdue_seconds: int


class EscalationQueueResponse(BaseModel):
    items: list[EscalatedComplaintItem]
    summary: EscalationQueueSummary
    page: int
    page_size: int
    total: int
    total_pages: int


class SuperintendentActionCreate(BaseModel):
    action_type: OfficerActionType
    note: str = Field(min_length=5, max_length=2000)
    directed_department_id: int | None = None


class SuperintendentActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    complaint_id: int
    action_type: OfficerActionType
    note: str
    directed_department: DepartmentOut | None = None
    officer: PublicOfficerOut
    created_at: datetime
    notifications_created: list[str] = ["NT-06"]


class ResolveComplaintRequest(BaseModel):
    note: str = Field(min_length=10, max_length=2000)


class ResolveComplaintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    complaint_number: str
    status: Status
    resolved_at: datetime
    resolved_by: PublicOfficerOut
    resolution_note: str
    notifications_created: list[str] = ["NT-07"]


class TimelineEventOut(BaseModel):
    event_type: str
    created_at: datetime
    actor_name: str | None = None
    actor_role: str | None = None
    note: str | None = None
    from_status: str | None = None
    to_status: str | None = None
    details: dict | None = None


class ComplaintDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    complaint_number: str
    title: str
    description: str
    location_text: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    status: Status
    department: DepartmentOut
    citizen_id: int
    submitted_at: datetime
    accepted_at: datetime | None = None
    resolution_due_at: datetime | None = None
    escalated_at: datetime | None = None
    overdue_seconds: int | None = None
    current_overdue_seconds: int | None = None
    resolved_at: datetime | None = None
    resolved_by: PublicOfficerOut | None = None
    resolution_note: str | None = None
    rejected_at: datetime | None = None
    rejection_reason: str | None = None
