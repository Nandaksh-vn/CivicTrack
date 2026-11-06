"""Domain services."""

from app.services.admin_service import (
    create_category,
    create_department,
    get_platform_activity,
    list_categories,
    list_departments,
    update_category,
    update_department,
)
from app.services.audit_service import list_audit_logs, record_audit_event
from app.services.auth_service import authenticate_user, register_citizen
from app.services.superintendent_service import (
    get_escalation_queue,
    get_timeline_events,
    record_superintendent_action,
    resolve_escalated_complaint,
)
from app.services.user_service import create_user_admin, list_users, update_user_admin

__all__ = [
    "authenticate_user",
    "register_citizen",
    "create_user_admin",
    "list_users",
    "update_user_admin",
    "get_escalation_queue",
    "get_timeline_events",
    "record_superintendent_action",
    "resolve_escalated_complaint",
    "list_departments",
    "create_department",
    "update_department",
    "list_categories",
    "create_category",
    "update_category",
    "get_platform_activity",
    "record_audit_event",
    "list_audit_logs",
]
