from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_default_escalation_window_is_seven_days() -> None:
    settings = Settings(_env_file=None)

    assert settings.escalation_window_minutes == 10_080
    assert settings.demo_mode is False


def test_non_default_window_is_reverted_without_demo_flag() -> None:
    settings = Settings(
        _env_file=None,
        escalation_window_minutes=2,
        allow_demo_escalation=False,
    )

    assert settings.escalation_window_minutes == 10_080
    assert settings.demo_mode is False


def test_non_default_window_is_kept_with_demo_flag() -> None:
    settings = Settings(
        _env_file=None,
        escalation_window_minutes=2,
        allow_demo_escalation=True,
    )

    assert settings.escalation_window_minutes == 2
    assert settings.demo_mode is True


def test_cors_origins_are_split_and_trimmed() -> None:
    settings = Settings(
        _env_file=None,
        cors_origins=" http://localhost:5173 , http://localhost:8080 ",
    )

    assert settings.cors_origin_list == [
        "http://localhost:5173",
        "http://localhost:8080",
    ]


def test_compatibility_aliases_are_read_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JWT_SECRET", "a" * 32)
    monkeypatch.setenv("INTERNAL_API_TOKEN", "b" * 32)
    monkeypatch.setenv("ESCALATION_INTERVAL_SECONDS", "15")
    monkeypatch.setenv("APP_ENV", "demo")

    settings = Settings(_env_file=None)

    assert settings.jwt_secret == "a" * 32
    assert settings.internal_trigger_token == "b" * 32
    assert settings.escalation_check_seconds == 15
    assert settings.environment == "demo"


def test_production_rejects_placeholder_secrets() -> None:
    with pytest.raises(ValidationError, match="Refusing to start in production"):
        Settings(
            _env_file=None,
            environment="production",
            jwt_secret="short",
            internal_trigger_token="short",
        )


def test_production_accepts_safe_configuration() -> None:
    settings = Settings(
        _env_file=None,
        environment="production",
        jwt_secret="a" * 32,
        internal_trigger_token="b" * 32,
        database_url="mysql+pymysql://civictrack:strong@db:3306/civictrack",
    )

    assert settings.is_production is True
    assert settings.demo_mode is False
