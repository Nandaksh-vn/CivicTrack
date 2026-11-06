"""
CivicTrack — Administrator API Router (FR-006, TRD §8.8)
"""

from __future__ import annotations

import math

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.enums import Role
from app.models.user import User
from app.schemas.user import AdminUserCreate, AdminUserUpdate, PublicUser, UserListResponse
from app.services.user_service import create_user_admin, list_users, update_user_admin

router = APIRouter(tags=["Administration"])


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
    """
    List user accounts (FR-006). Accessible by Platform Administrator only.
    """
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


@router.post(
    "/categories",
    status_code=status.HTTP_201_CREATED,
    summary="Create a category (Admin only)",
)
def create_category(
    _: User = Depends(require_roles(Role.PLATFORM_ADMIN)),
) -> dict[str, str]:
    """Stub endpoint for category creation guarded by PLATFORM_ADMIN."""
    return {"status": "created"}
