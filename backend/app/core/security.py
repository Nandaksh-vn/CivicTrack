"""
CivicTrack — Security utilities (TRD §9, NFR-004, NFR-006)
Bcrypt password hashing (cost >= 12) and PyJWT bearer token creation and verification.
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.config import settings
from app.core.errors import Unauthorized, UnprocessableEntity

_PASSWORD_LETTER_REGEX = re.compile(r"[a-zA-Z]")
_PASSWORD_DIGIT_REGEX = re.compile(r"\d")
_BCRYPT_ROUNDS = 12
_JWT_ISSUER = "civictrack"
_JWT_AUDIENCE = "civictrack-web"


def validate_password_strength(password: str) -> None:
    """
    Enforce password policy:
    - 8 to 72 characters
    - At least one letter
    - At least one digit
    """
    if not (8 <= len(password) <= 72):
        raise UnprocessableEntity(
            message="Password must be between 8 and 72 characters long.",
            error_code="WEAK_PASSWORD",
        )
    if not _PASSWORD_LETTER_REGEX.search(password):
        raise UnprocessableEntity(
            message="Password must contain at least one letter.",
            error_code="WEAK_PASSWORD",
        )
    if not _PASSWORD_DIGIT_REGEX.search(password):
        raise UnprocessableEntity(
            message="Password must contain at least one digit.",
            error_code="WEAK_PASSWORD",
        )


def hash_password(plain_password: str) -> str:
    """Hash password with bcrypt at cost >= 12."""
    validate_password_strength(plain_password)
    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Constant-time verification of password against bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def create_access_token(
    user_id: int,
    role: str,
    department_id: int | None = None,
    expires_delta: timedelta | None = None,
) -> tuple[str, int]:
    """
    Issue an 8-hour JWT access token with standard claims.
    Returns (token_string, expires_in_seconds).
    """
    now = datetime.now(UTC)
    if expires_delta is not None:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.jwt_expires_minutes)

    expires_in_seconds = int((expire - now).total_seconds())

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": str(role),
        "dept": department_id,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid.uuid4()),
        "iss": _JWT_ISSUER,
        "aud": _JWT_AUDIENCE,
    }

    token = jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return token, expires_in_seconds


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and verify JWT signature, issuer, audience, and expiration.
    Raises Unauthorized if invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            issuer=_JWT_ISSUER,
            audience=_JWT_AUDIENCE,
        )
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise Unauthorized(
            message="Token has expired. Please log in again.",
            error_code="TOKEN_EXPIRED",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise Unauthorized(
            message="Invalid authentication token.",
            error_code="INVALID_TOKEN",
        ) from exc
