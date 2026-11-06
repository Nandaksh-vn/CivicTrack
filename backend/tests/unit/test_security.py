"""
CivicTrack — Security Unit Tests (NFR-004, NFR-006)

Tests password hashing, JWT creation/decoding, and password strength validation
without requiring a database connection.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from app.core.errors import Unauthorized, UnprocessableEntity
from app.core.security import (
    _BCRYPT_ROUNDS,
    create_access_token,
    decode_access_token,
    hash_password,
    validate_password_strength,
    verify_password,
)

# ── Password strength validation ─────────────────────────────────────────────


def test_validate_password_strength_accepts_valid() -> None:
    validate_password_strength("ValidPass1")
    validate_password_strength("aB1" + "x" * 69)  # exactly 72 chars


@pytest.mark.parametrize(
    "password,error_code",
    [
        ("Short1", "WEAK_PASSWORD"),  # < 8
        ("x" * 73, "WEAK_PASSWORD"),  # > 72
        ("nodigits", "WEAK_PASSWORD"),  # no digit
        ("12345678", "WEAK_PASSWORD"),  # no letter
        ("", "WEAK_PASSWORD"),  # empty
    ],
)
def test_validate_password_strength_rejects_invalid(password: str, error_code: str) -> None:
    with pytest.raises(UnprocessableEntity) as exc:
        validate_password_strength(password)
    assert exc.value.error_code == error_code


# ── Password hashing ─────────────────────────────────────────────────────────


def test_hash_password_uses_bcrypt_cost_12() -> None:
    hashed = hash_password("Secret123")
    assert (
        hashed.startswith("$2b$12$") or hashed.startswith("$2a$12$") or hashed.startswith("$2y$12$")
    )


def test_verify_password_matching() -> None:
    hashed = hash_password("Secret123")
    assert verify_password("Secret123", hashed) is True


def test_verify_password_nonmatching() -> None:
    hashed = hash_password("Secret123")
    assert verify_password("WrongPass1", hashed) is False


def test_verify_password_malformed_hash() -> None:
    assert verify_password("Secret123", "not-a-hash") is False


def test_hash_password_rejects_weak() -> None:
    with pytest.raises(UnprocessableEntity):
        hash_password("short")


# ── JWT access tokens ────────────────────────────────────────────────────────


def test_create_access_token_round_trip() -> None:
    token, expires_in = create_access_token(user_id=42, role="CITIZEN")
    assert isinstance(token, str)
    assert expires_in > 0

    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "CITIZEN"
    assert payload["iss"] == "civictrack"
    assert payload["aud"] == "civictrack-web"
    assert "jti" in payload
    assert "iat" in payload
    assert "exp" in payload


def test_create_access_token_with_department() -> None:
    token, _ = create_access_token(user_id=7, role="DEPARTMENT_OFFICER", department_id=3)
    payload = decode_access_token(token)
    assert payload["dept"] == 3


def test_create_access_token_custom_expiry() -> None:
    token, expires_in = create_access_token(
        user_id=1, role="CITIZEN", expires_delta=timedelta(minutes=5)
    )
    assert expires_in == 300
    payload = decode_access_token(token)
    assert payload["exp"] - payload["iat"] == 300


def test_decode_expired_token_raises() -> None:
    token, _ = create_access_token(user_id=1, role="CITIZEN", expires_delta=timedelta(seconds=-10))
    with pytest.raises(Unauthorized) as exc:
        decode_access_token(token)
    assert exc.value.error_code == "TOKEN_EXPIRED"


def test_decode_tampered_token_raises() -> None:
    token, _ = create_access_token(user_id=1, role="CITIZEN")
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(Unauthorized) as exc:
        decode_access_token(tampered)
    assert exc.value.error_code == "INVALID_TOKEN"


def test_bcrypt_rounds_meets_minimum() -> None:
    assert _BCRYPT_ROUNDS >= 12
