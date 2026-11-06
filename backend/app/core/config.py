"""
CivicTrack - application settings.

Environment variables are the single source of truth. TRD section 19 names are
canonical; compatibility aliases are accepted for the names used by the Phase 3
tooling (`APP_ENV`, `JWT_SECRET_KEY`, `ESCALATION_INTERVAL_SECONDS`,
`INTERNAL_API_TOKEN`).
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

_PRODUCTION_SLA_MINUTES = 10_080  # seven calendar days: BR-06, BR-19


class Settings(BaseSettings):
    """Validated runtime configuration loaded from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    # -- Application ---------------------------------------------------------
    environment: Literal["development", "demo", "staging", "production"] = Field(
        default="development",
        validation_alias=AliasChoices("ENVIRONMENT", "APP_ENV"),
    )
    app_timezone: str = "Asia/Kolkata"
    log_level: str = "INFO"
    cors_origins: str = Field(
        default="http://localhost:8080,http://localhost:5173",
        validation_alias=AliasChoices("CORS_ORIGINS", "FRONTEND_URL"),
    )

    # -- Database ------------------------------------------------------------
    database_url: str = Field(
        default="mysql+pymysql://civictrack:civictrack_pass@db:3306/civictrack",
        description="SQLAlchemy sync DSN for MySQL via PyMySQL",
    )

    # -- Authentication ------------------------------------------------------
    jwt_secret: str = Field(
        default="CHANGE_ME_generate_a_32_byte_hex_secret_before_production",
        validation_alias=AliasChoices("JWT_SECRET", "JWT_SECRET_KEY"),
        description="HMAC-SHA256 signing secret; at least 32 characters in production",
    )
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = Field(
        default=480,
        ge=1,
        le=1440,
        validation_alias=AliasChoices("JWT_EXPIRES_MINUTES"),
        description="Access token lifetime; 480 minutes = 8 hours",
    )

    # -- Escalation / SLA ----------------------------------------------------
    escalation_window_minutes: int = Field(default=_PRODUCTION_SLA_MINUTES, ge=1, le=525_600)
    allow_demo_escalation: bool = False
    escalation_check_seconds: int = Field(
        default=60,
        ge=5,
        le=3_600,
        validation_alias=AliasChoices("ESCALATION_CHECK_SECONDS", "ESCALATION_INTERVAL_SECONDS"),
    )
    escalation_batch_size: int = Field(default=100, ge=1, le=1_000)

    # -- Internal API --------------------------------------------------------
    internal_trigger_token: str = Field(
        default="CHANGE_ME_internal_token",
        validation_alias=AliasChoices("INTERNAL_TRIGGER_TOKEN", "INTERNAL_API_TOKEN"),
        description="Token for token-protected /internal/* endpoints",
    )

    # -- Uploads -------------------------------------------------------------
    upload_dir: str = "/app/uploads"
    max_upload_mb: int = Field(default=5, ge=1, le=50)
    max_images_per_complaint: int = Field(default=10, ge=1, le=50)
    max_images_per_submission: int = Field(default=3, ge=1, le=10)
    upload_allowed_mime_types: str = "image/jpeg,image/png,image/webp"

    # -- Seed / P1 -----------------------------------------------------------
    seed_demo_data: bool = False
    seed_password: str = "Demo@12345"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    enable_ai_features: bool = False

    # -- Derived helpers -----------------------------------------------------
    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def demo_mode(self) -> bool:
        """True only when a non-default window is explicitly enabled."""
        return (
            self.allow_demo_escalation and self.escalation_window_minutes != _PRODUCTION_SLA_MINUTES
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def allowed_mime_types(self) -> list[str]:
        return [
            value.strip() for value in self.upload_allowed_mime_types.split(",") if value.strip()
        ]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @field_validator("app_timezone")
    @classmethod
    def _validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except Exception as exc:  # noqa: BLE001 - normalized to a config error
            raise ValueError(f"APP_TIMEZONE is not a valid IANA timezone: {value}") from exc
        return value

    @field_validator("jwt_algorithm")
    @classmethod
    def _validate_jwt_algorithm(cls, value: str) -> str:
        if value != "HS256":
            raise ValueError("JWT_ALGORITHM must be HS256")
        return value

    @model_validator(mode="after")
    def _validate_safety(self) -> Settings:
        """Apply the demo-window guard and refuse unsafe production startup."""
        if (
            self.escalation_window_minutes != _PRODUCTION_SLA_MINUTES
            and not self.allow_demo_escalation
        ):
            logger.error(
                "Non-default ESCALATION_WINDOW_MINUTES=%s without "
                "ALLOW_DEMO_ESCALATION=true; reverting to production default %s minutes.",
                self.escalation_window_minutes,
                _PRODUCTION_SLA_MINUTES,
            )
            object.__setattr__(self, "escalation_window_minutes", _PRODUCTION_SLA_MINUTES)

        problems: list[str] = []
        if self.is_production:
            if self.jwt_secret.startswith("CHANGE_ME") or len(self.jwt_secret) < 32:
                problems.append(
                    "JWT_SECRET must be a non-placeholder secret of at least 32 characters"
                )
            if (
                self.internal_trigger_token.startswith("CHANGE_ME")
                or len(self.internal_trigger_token) < 32
            ):
                problems.append(
                    "INTERNAL_TRIGGER_TOKEN must be a non-placeholder secret of at least 32 characters"
                )
            if "civictrack_pass" in self.database_url or "CHANGE_ME" in self.database_url:
                problems.append("DATABASE_URL must not use the development placeholder credentials")
            if self.allow_demo_escalation:
                problems.append("ALLOW_DEMO_ESCALATION must be false in production")

        if problems:
            if self.is_production:
                raise ValueError(
                    "Refusing to start in production with unsafe configuration:\n"
                    + "\n".join(f"  - {problem}" for problem in problems)
                )
            for problem in problems:
                logger.warning("Unsafe configuration (non-production): %s", problem)

        if self.allow_demo_escalation:
            logger.warning(
                "DEMO ESCALATION MODE ENABLED: effective window=%s minutes. "
                "This must not be used in production.",
                self.escalation_window_minutes,
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached settings singleton."""
    return Settings()


settings: Settings = get_settings()
