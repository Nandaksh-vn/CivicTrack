"""
CivicTrack — Authentication Service (FR-001, FR-002, FR-003, TRD §5.5)
"""

from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.errors import Conflict, Unauthorized
from app.core.security import (
    create_access_token,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.models.audit import AuditLog
from app.models.enums import Role
from app.models.user import User

logger = logging.getLogger(__name__)

# Pre-computed dummy bcrypt hash (cost 12) for constant-time comparison on nonexistent user
_DUMMY_BCRYPT_HASH = "$2b$12$e8Y6l1XNP5o5c1Hw3jTjVuQyN5J0t.8P2YVn9M3R4kK6q0K0J1Wmi"


def register_citizen(
    db: Session,
    full_name: str,
    email: str,
    password: str,
    phone: str | None = None,
) -> tuple[User, str, int]:
    """
    Register a new Citizen account (FR-001).
    Enforces unique case-insensitive email, password rules, role=CITIZEN, is_active=True.
    Returns (user, token, expires_in_seconds).
    """
    clean_email = email.strip().lower()
    clean_name = full_name.strip()
    clean_phone = phone.strip() if phone else None

    # Check for email uniqueness
    existing_user = db.execute(
        select(User).where(func.lower(User.email) == clean_email)
    ).scalar_one_or_none()

    if existing_user is not None:
        raise Conflict(
            message="Email already registered.",
            error_code="EMAIL_ALREADY_REGISTERED",
        )

    # Validate and hash password
    validate_password_strength(password)
    password_hash = hash_password(password)

    user = User(
        full_name=clean_name,
        email=clean_email,
        password_hash=password_hash,
        phone=clean_phone,
        role=Role.CITIZEN,
        department_id=None,
        is_active=True,
    )
    db.add(user)
    db.flush()

    audit = AuditLog(
        actor_user_id=user.id,
        actor_role=user.role.value,
        action="USER_REGISTERED",
        entity_type="USER",
        entity_id=str(user.id),
    )
    db.add(audit)
    db.commit()
    db.refresh(user)

    logger.info("event=citizen_registered user_id=%s role=%s", user.id, user.role.value)

    token, expires_in = create_access_token(
        user_id=user.id,
        role=user.role.value,
        department_id=None,
    )
    return user, token, expires_in


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> tuple[User, str, int]:
    """
    Authenticate active user with email and password (FR-002, FR-003).
    Returns generic 401 on bad password, missing email, or inactive user.
    Uses constant-time comparison.
    """
    clean_email = email.strip().lower()

    user = db.execute(
        select(User)
        .options(joinedload(User.department))
        .where(func.lower(User.email) == clean_email)
    ).scalar_one_or_none()

    if user is None:
        # Prevent user-enumeration timing attack by verifying against dummy hash
        verify_password(password, _DUMMY_BCRYPT_HASH)
        logger.warning("event=auth_failed reason=user_not_found email=%s", clean_email)
        try:
            audit = AuditLog(
                actor_user_id=None,
                actor_role=None,
                action="AUTH_LOGIN_FAILED",
                entity_type="AUTH",
                entity_id=clean_email,
            )
            db.add(audit)
            db.commit()
        except Exception:
            db.rollback()
        raise Unauthorized(
            message="Invalid email or password.",
            error_code="INVALID_CREDENTIALS",
        )

    # Verify password constant-time
    if not verify_password(password, user.password_hash):
        logger.warning("event=auth_failed reason=invalid_password user_id=%s", user.id)
        try:
            audit = AuditLog(
                actor_user_id=user.id,
                actor_role=user.role.value,
                action="AUTH_LOGIN_FAILED",
                entity_type="AUTH",
                entity_id=str(user.id),
            )
            db.add(audit)
            db.commit()
        except Exception:
            db.rollback()
        raise Unauthorized(
            message="Invalid email or password.",
            error_code="INVALID_CREDENTIALS",
        )

    # Inactive check returns the exact same 401 error message as bad password
    if not user.is_active:
        logger.warning("event=auth_failed reason=inactive_user user_id=%s", user.id)
        try:
            audit = AuditLog(
                actor_user_id=user.id,
                actor_role=user.role.value,
                action="AUTH_LOGIN_FAILED",
                entity_type="AUTH",
                entity_id=str(user.id),
            )
            db.add(audit)
            db.commit()
        except Exception:
            db.rollback()
        raise Unauthorized(
            message="Invalid email or password.",
            error_code="INVALID_CREDENTIALS",
        )

    try:
        audit = AuditLog(
            actor_user_id=user.id,
            actor_role=user.role.value,
            action="AUTH_LOGIN_SUCCESS",
            entity_type="AUTH",
            entity_id=str(user.id),
        )
        db.add(audit)
        db.commit()
    except Exception:
        db.rollback()

    logger.info("event=auth_success user_id=%s role=%s", user.id, user.role.value)

    token, expires_in = create_access_token(
        user_id=user.id,
        role=user.role.value,
        department_id=user.department_id,
    )
    return user, token, expires_in
