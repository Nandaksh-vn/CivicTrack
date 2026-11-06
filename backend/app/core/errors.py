"""
CivicTrack — Error taxonomy and exception hierarchy (TRD §2.6)
All service-layer exceptions derive from AppError; routers never raise HTTP
exceptions directly — they let the central exception handler convert them.
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base class for all application errors."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred."

    def __init__(
        self,
        message: str | None = None,
        error_code: str | None = None,
        details: Any = None,
    ) -> None:
        self.message = message or self.__class__.message
        self.error_code = error_code or self.__class__.error_code
        self.details = details
        super().__init__(self.message)


class BadRequest(AppError):
    status_code = 400
    error_code = "BAD_REQUEST"
    message = "Bad request."


class Unauthorized(AppError):
    status_code = 401
    error_code = "UNAUTHORIZED"
    message = "Authentication required."


class Forbidden(AppError):
    status_code = 403
    error_code = "FORBIDDEN"
    message = "You do not have permission to perform this action."


class NotFound(AppError):
    status_code = 404
    error_code = "NOT_FOUND"
    message = "Resource not found."


class Conflict(AppError):
    status_code = 409
    error_code = "CONFLICT"
    message = "Request conflicts with the current state of the resource."


class UnprocessableEntity(AppError):
    status_code = 422
    error_code = "UNPROCESSABLE_ENTITY"
    message = "Validation failed."


class InternalError(AppError):
    status_code = 500
    error_code = "INTERNAL_ERROR"
    message = "An unexpected error occurred."
