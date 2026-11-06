"""
CivicTrack — User Administration Service (FR-006, TRD §5.5, §9.1)
"""

from __future__ import annotations

import logging

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, joinedload

from app.core.errors import Conflict, NotFound, UnprocessableEntity
from app.core.security import hash_password, validate_password_strength
from app.models.audit import AuditLog
from app.models.department import Department
from app.models.enums import Role
from app.models.user import User
from app.schemas.user import AdminUserCreate, AdminUserUpdate

logger = logging.getLogger(__name__)


def list_users(
    db: Session,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[User], int]:
    """List users with pagination."""
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    offset = (page - 1) * page_size

    total = db.execute(select(func.count(User.id))).scalar_one()

    query = (
        select(User)
        .options(joinedload(User.department))
        .order_by(User.id.asc())
        .offset(offset)
        .limit(page_size)
    )
    users = list(db.execute(query).scalars().all())
    return users, total


def create_user_admin(db: Session, data: AdminUserCreate, admin_user_id: int | None = None) -> User:
    """
    Create a user account by administrator (FR-006).
    Enforces unique email, password policy, and exactly one active department for officers.
    """
    clean_email = data.email.strip().lower()
    clean_name = data.full_name.strip()
    clean_phone = data.phone.strip() if data.phone else None

    # Check email uniqueness
    existing = db.execute(
        select(User).where(func.lower(User.email) == clean_email)
    ).scalar_one_or_none()
    if existing is not None:
        raise Conflict(
            message="Email already registered.",
            error_code="EMAIL_ALREADY_REGISTERED",
        )

    # Department validation for officers
    department_id = data.department_id
    if data.role == Role.DEPARTMENT_OFFICER:
        if department_id is None:
            raise UnprocessableEntity(
                message="Department Officer must be assigned to an active department.",
                error_code="DEPARTMENT_REQUIRED",
            )
        dept = db.execute(
            select(Department).where(Department.id == department_id, Department.is_active.is_(True))
        ).scalar_one_or_none()
        if dept is None:
            raise UnprocessableEntity(
                message="Specified department does not exist or is inactive.",
                error_code="INVALID_DEPARTMENT",
            )
    else:
        # Non-officers do not belong to a department
        department_id = None

    validate_password_strength(data.password)
    password_hash = hash_password(data.password)

    user = User(
        full_name=clean_name,
        email=clean_email,
        password_hash=password_hash,
        phone=clean_phone,
        role=data.role,
        department_id=department_id,
        is_active=data.is_active,
    )
    db.add(user)
    db.flush()

    audit = AuditLog(
        actor_user_id=admin_user_id,
        actor_role=Role.PLATFORM_ADMIN.value,
        action="USER_CREATED",
        entity_type="USER",
        entity_id=str(user.id),
    )
    db.add(audit)
    db.commit()

    # Reload with department
    user = db.execute(
        select(User).options(joinedload(User.department)).where(User.id == user.id)
    ).scalar_one()

    logger.info("event=admin_created_user user_id=%s role=%s", user.id, user.role.value)
    return user


def update_user_admin(
    db: Session, user_id: int, data: AdminUserUpdate, admin_user_id: int | None = None
) -> User:
    """
    Update user role, department, or active status (FR-006).
    Enforces last active admin protection and department constraints.
    """
    user = db.execute(
        select(User).options(joinedload(User.department)).where(User.id == user_id)
    ).scalar_one_or_none()

    if user is None:
        raise NotFound(message="User not found.", error_code="USER_NOT_FOUND")

    # Check last active admin protection
    is_currently_active_admin = user.role == Role.PLATFORM_ADMIN and user.is_active
    will_demote = data.role is not None and data.role != Role.PLATFORM_ADMIN
    will_deactivate = data.is_active is False

    if is_currently_active_admin and (will_demote or will_deactivate):
        active_admin_count = db.execute(
            select(func.count(User.id)).where(
                User.role == Role.PLATFORM_ADMIN,
                User.is_active.is_(True),
            )
        ).scalar_one()

        if active_admin_count <= 1:
            raise Conflict(
                message="Cannot deactivate or demote the last active Platform Administrator.",
                error_code="LAST_ADMIN_PROTECTED",
            )

    new_role = data.role if data.role is not None else user.role
    new_active = data.is_active if data.is_active is not None else user.is_active
    new_dept_id = data.department_id if data.department_id is not None else user.department_id

    # If role is DEPARTMENT_OFFICER, validate department
    if new_role == Role.DEPARTMENT_OFFICER:
        if new_dept_id is None:
            raise UnprocessableEntity(
                message="Department Officer must be assigned to an active department.",
                error_code="DEPARTMENT_REQUIRED",
            )
        dept = db.execute(
            select(Department).where(Department.id == new_dept_id, Department.is_active.is_(True))
        ).scalar_one_or_none()
        if dept is None:
            raise UnprocessableEntity(
                message="Specified department does not exist or is inactive.",
                error_code="INVALID_DEPARTMENT",
            )
    else:
        new_dept_id = None

    protected = is_currently_active_admin and (will_demote or will_deactivate)

    if protected:
        other_admins = (
            select(func.count(User.id))
            .where(
                User.role == Role.PLATFORM_ADMIN,
                User.is_active.is_(True),
                User.id != user_id,
            )
            .scalar_subquery()
        )
        result = db.execute(
            update(User)
            .where(
                User.id == user_id,
                User.role == Role.PLATFORM_ADMIN,
                User.is_active.is_(True),
                other_admins >= 1,
            )
            .values(role=new_role, is_active=new_active, department_id=new_dept_id)
            .execution_options(synchronize_session=False)
        )
        if result.rowcount == 0:
            raise Conflict(
                message="Cannot deactivate or demote the last active Platform Administrator.",
                error_code="LAST_ADMIN_PROTECTED",
            )
        db.expire(user)

    action = "ROLE_CHANGED" if new_role != user.role else "USER_UPDATED"

    user.role = new_role
    user.is_active = new_active
    user.department_id = new_dept_id

    audit = AuditLog(
        actor_user_id=admin_user_id,
        actor_role=Role.PLATFORM_ADMIN.value,
        action=action,
        entity_type="USER",
        entity_id=str(user.id),
    )
    db.add(audit)
    db.commit()

    # Reload with department
    user = db.execute(
        select(User).options(joinedload(User.department)).where(User.id == user.id)
    ).scalar_one()

    logger.info(
        "event=admin_updated_user user_id=%s role=%s active=%s",
        user.id,
        user.role.value,
        user.is_active,
    )
    return user
