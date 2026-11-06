"""
CivicTrack — Authentication and RBAC Dependencies (TRD §5.4, RBAC-01..08)
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.errors import Conflict, Forbidden, Unauthorized
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.complaint import Complaint
from app.models.enums import Role, Status
from app.models.user import User

logger = logging.getLogger(__name__)

# auto_error=False allows returning custom Unauthorized instead of default FastAPI 403/401
_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate JWT bearer token, load user from DB, and reject inactive users (RBAC-06).
    """
    if credentials is None or not credentials.credentials:
        raise Unauthorized(
            message="Authentication required.",
            error_code="UNAUTHORIZED",
        )

    token = credentials.credentials
    payload = decode_access_token(token)

    sub = payload.get("sub")
    if not sub:
        raise Unauthorized(
            message="Invalid token claims.",
            error_code="INVALID_TOKEN",
        )

    try:
        user_id = int(sub)
    except (ValueError, TypeError) as exc:
        raise Unauthorized(
            message="Invalid token subject.",
            error_code="INVALID_TOKEN",
        ) from exc

    user = db.execute(
        select(User).options(joinedload(User.department)).where(User.id == user_id)
    ).scalar_one_or_none()

    if user is None:
        raise Unauthorized(
            message="User associated with token no longer exists.",
            error_code="USER_NOT_FOUND",
        )

    if not user.is_active:
        raise Unauthorized(
            message="Account has been deactivated.",
            error_code="INACTIVE_ACCOUNT",
        )

    return user


def require_roles(*allowed_roles: Role) -> Callable[[User, Request, Session], User]:
    """
    Dependency factory that checks whether current_user has one of the allowed roles (RBAC-01).
    Logs an audit entry upon denial (RBAC-08) and raises HTTP 403 Forbidden.
    """

    def role_checker(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        if current_user.role not in allowed_roles:
            # Audit denied attempt (RBAC-08)
            try:
                audit = AuditLog(
                    actor_user_id=current_user.id,
                    actor_role=current_user.role.value,
                    action="RBAC_DENIED",
                    entity_type="ROUTE",
                    entity_id=request.url.path,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    metadata_json=json.dumps({"method": request.method, "path": request.url.path}),
                )
                db.add(audit)
                db.commit()
            except Exception as exc:
                db.rollback()
                logger.error("Failed to write RBAC audit log: %s", exc)

            logger.warning(
                "event=rbac_denied user_id=%s role=%s path=%s method=%s",
                current_user.id,
                current_user.role.value,
                request.url.path,
                request.method,
            )
            raise Forbidden(
                message="You do not have permission to perform this action.",
                error_code="FORBIDDEN",
            )
        return current_user

    return role_checker


# ── Object Scope Guards (RBAC-02, RBAC-03, RBAC-05, AC-14) ─────────────────


def ensure_complaint_owner(complaint: Complaint, user: User) -> None:
    """Enforce that Citizens can only access their own complaints (RBAC-03)."""
    if user.role == Role.CITIZEN and complaint.citizen_id != user.id:
        raise Forbidden(
            message="You do not have permission to access this complaint.",
            error_code="FORBIDDEN",
        )


def ensure_officer_department(complaint: Complaint, user: User) -> None:
    """Enforce that Department Officers only access complaints in their department (RBAC-02, AC-14)."""
    if user.role == Role.DEPARTMENT_OFFICER:
        if user.department_id is None or complaint.department_id != user.department_id:
            raise Forbidden(
                message="You do not have permission to access another department's complaint.",
                error_code="FORBIDDEN",
            )


def ensure_superintendent_action_allowed(complaint: Complaint, user: User) -> None:
    """Enforce that Superintendents only act on ESCALATED complaints (RBAC-05)."""
    if user.role == Role.SUPERINTENDENT_OFFICER:
        if complaint.status != Status.ESCALATED:
            raise Conflict(
                message="Superintendent can only act on escalated complaints.",
                error_code="INVALID_TRANSITION",
            )
