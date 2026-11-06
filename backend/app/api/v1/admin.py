"""
CivicTrack — Administrator API Router (FR-006, FR-046..FR-050, TRD §8.8)
"""

from __future__ import annotations

import math
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.enums import Role
from app.models.user import User
from app.schemas.admin import (
    AuditLogListResponse,
    CategoryCreate,
    CategoryDetailOut,
    CategoryUpdate,
    DepartmentCreate,
    DepartmentDetailOut,
    DepartmentUpdate,
    PlatformActivityResponse,
)
from app.schemas.user import AdminUserCreate, AdminUserUpdate, PublicUser, UserListResponse
from app.services.admin_service import (
    create_category as create_category_service,
)
from app.services.admin_service import (
    create_department as create_department_service,
)
from app.services.admin_service import (
    get_platform_activity as get_platform_activity_service,
)
from app.services.admin_service import (
    list_categories as list_categories_service,
)
from app.services.admin_service import (
    list_departments as list_departments_service,
)
from app.services.admin_service import (
    update_category as update_category_service,
)
from app.services.admin_service import (
    update_department as update_department_service,
)
from app.services.audit_service import list_audit_logs as list_audit_logs_service
from app.services.user_service import create_user_admin, list_users, update_user_admin

router = APIRouter(tags=["Administration"])


# ── User Administration (FR-006) ──────────────────────────────────────────────


@router.get(
    "/users",
    status_code=status.HTTP_200_OK,
    response_model=UserListResponse,
    summary="List all users with pagination",
)
def get_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: User = Depends(require_roles(Role.PLATFORM_ADMIN)),
    db: Session = Depends(get_db),
) -> UserListResponse:
    """List user accounts (FR-006). Accessible by Platform Administrator only."""
    users, total = list_users(db=db, page=page, page_size=page_size)
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return UserListResponse(
        items=[PublicUser.model_validate(u) for u in users],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
    response_model=PublicUser,
    summary="Create a user (Officer or Admin)",
)
def create_user(
    data: AdminUserCreate,
    current_admin: User = Depends(require_roles(Role.PLATFORM_ADMIN)),
    db: Session = Depends(get_db),
) -> PublicUser:
    """
    Create a user account by administrator (FR-006).
    Enforces role constraints and active department for officers.
    """
    user = create_user_admin(db=db, data=data, admin_user_id=current_admin.id)
    return PublicUser.model_validate(user)


@router.patch(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=PublicUser,
    summary="Update user role, department, or active status",
)
def update_user(
    user_id: int,
    data: AdminUserUpdate,
    current_admin: User = Depends(require_roles(Role.PLATFORM_ADMIN)),
    db: Session = Depends(get_db),
) -> PublicUser:
    """
    Update user account by administrator (FR-006).
    Blocks deactivating or demoting the last active Platform Administrator.
    """
    user = update_user_admin(db=db, user_id=user_id, data=data, admin_user_id=current_admin.id)
    return PublicUser.model_validate(user)


# ── Department Management (FR-046, BR-15, US-ADM-02) ─────────────────────────


@router.get(
    "/departments",
    status_code=status.HTTP_200_OK,
    response_model=list[DepartmentDetailOut],
    summary="List all departments",
)
def get_departments(
    is_active: bool | None = Query(default=None),
    _: User = Depends(require_roles(Role.PLATFORM_ADMIN)),
    db: Session = Depends(get_db),
) -> list[DepartmentDetailOut]:
    """List all departments with is_active flag (FR-046)."""
    departments = list_departments_service(db=db, is_active=is_active)
    return [DepartmentDetailOut.model_validate(d) for d in departments]


@router.post(
    "/departments",
    status_code=status.HTTP_201_CREATED,
    response_model=DepartmentDetailOut,
    summary="Create a department",
)
def create_department(
    data: DepartmentCreate,
    request: Request,
    current_admin: User = Depends(require_roles(Role.PLATFORM_ADMIN)),
    db: Session = Depends(get_db),
) -> DepartmentDetailOut:
    """Create a new department (FR-046)."""
    dept = create_department_service(
        db=db,
        data=data,
        actor=current_admin,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return DepartmentDetailOut.model_validate(dept)


@router.patch(
    "/departments/{dept_id}",
    status_code=status.HTTP_200_OK,
    response_model=DepartmentDetailOut,
    summary="Update or deactivate a department",
)
def update_department(
    dept_id: int,
    data: DepartmentUpdate,
    request: Request,
    current_admin: User = Depends(require_roles(Role.PLATFORM_ADMIN)),
    db: Session = Depends(get_db),
) -> DepartmentDetailOut:
    """
    Update department metadata or active status (FR-046).
    Blocks deactivation if active categories or active officers reference it (BR-15).
    """
    dept = update_department_service(
        db=db,
        dept_id=dept_id,
        data=data,
        actor=current_admin,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return DepartmentDetailOut.model_validate(dept)


# ── Category Management (FR-047, US-ADM-03) ───────────────────────────────────


@router.get(
    "/categories",
    status_code=status.HTTP_200_OK,
    response_model=list[CategoryDetailOut],
    summary="List complaint categories",
)
def get_categories(
    department_id: int | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    _: User = Depends(require_roles(Role.PLATFORM_ADMIN)),
    db: Session = Depends(get_db),
) -> list[CategoryDetailOut]:
    """List complaint categories with joined department (FR-047)."""
    return list_categories_service(db=db, department_id=department_id, is_active=is_active)


@router.post(
    "/categories",
    status_code=status.HTTP_201_CREATED,
    response_model=CategoryDetailOut,
    summary="Create a complaint category",
)
def create_category(
    data: CategoryCreate,
    request: Request,
    current_admin: User = Depends(require_roles(Role.PLATFORM_ADMIN)),
    db: Session = Depends(get_db),
) -> CategoryDetailOut:
    """
    Create a new complaint category mapped to an active department (FR-047, TRD §8.8).
    """
    return create_category_service(
        db=db,
        data=data,
        actor=current_admin,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.patch(
    "/categories/{category_id}",
    status_code=status.HTTP_200_OK,
    response_model=CategoryDetailOut,
    summary="Update or remap a complaint category",
)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    request: Request,
    current_admin: User = Depends(require_roles(Role.PLATFORM_ADMIN)),
    db: Session = Depends(get_db),
) -> CategoryDetailOut:
    """
    Update category or remap department (FR-047, TRD §8.8).
    Department remapping requires target department to be active.
    Remap affects future complaints only.
    """
    return update_category_service(
        db=db,
        category_id=category_id,
        data=data,
        actor=current_admin,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


# ── Platform Activity (FR-048, US-ADM-04) ─────────────────────────────────────


@router.get(
    "/activity",
    status_code=status.HTTP_200_OK,
    response_model=PlatformActivityResponse,
    summary="Platform operational activity metrics",
)
def get_activity(
    _: User = Depends(require_roles(Role.PLATFORM_ADMIN)),
    db: Session = Depends(get_db),
) -> PlatformActivityResponse:
    """
    Platform activity: counts by status, counts by department, total escalations,
    and 20 recent timeline events (FR-048, TRD §8.8).
    """
    return get_platform_activity_service(db=db)


# ── Audit Logs (FR-049, FR-050, US-ADM-05, NFR-008, NFR-019) ─────────────────


@router.get(
    "/audit-logs",
    status_code=status.HTTP_200_OK,
    response_model=AuditLogListResponse,
    summary="List audit logs with filters and pagination",
)
def get_audit_logs(
    actor_user_id: int | None = Query(default=None),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    from_param: datetime | None = Query(default=None, alias="from"),
    from_date_param: datetime | None = Query(default=None, alias="from_date"),
    to_param: datetime | None = Query(default=None, alias="to"),
    to_date_param: datetime | None = Query(default=None, alias="to_date"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: User = Depends(require_roles(Role.PLATFORM_ADMIN)),
    db: Session = Depends(get_db),
) -> AuditLogListResponse:
    """
    List audit logs filtered by actor, action, entity type, and date range (FR-049).
    Read-only, paginated, newest first.
    """
    from_date = from_param or from_date_param
    to_date = to_param or to_date_param

    items, total = list_audit_logs_service(
        db=db,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return AuditLogListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )
