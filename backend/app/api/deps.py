"""
CivicTrack — API Dependencies (re-export from app.dependencies)
"""

from app.dependencies import (
    ensure_complaint_owner,
    ensure_officer_department,
    ensure_superintendent_action_allowed,
    get_current_user,
    require_roles,
)

__all__ = [
    "get_current_user",
    "require_roles",
    "ensure_complaint_owner",
    "ensure_officer_department",
    "ensure_superintendent_action_allowed",
]
