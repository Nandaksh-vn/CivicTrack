"""
CivicTrack - FastAPI application factory.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1 import admin, auth, complaints, department, internal, superintendent
from app.core.config import settings
from app.core.errors import AppError
from app.core.logging import configure_logging
from app.db.session import engine

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    logger.info(
        "event=startup environment=%s demo_mode=%s escalation_window_minutes=%s",
        settings.environment,
        settings.demo_mode,
        settings.escalation_window_minutes,
    )
    yield
    logger.info("event=shutdown")


def create_app() -> FastAPI:
    application = FastAPI(
        title="CivicTrack API",
        description="Community Problem Reporting and Resolution Platform",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    @application.middleware("http")
    async def request_id_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @application.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": "VALIDATION_ERROR",
                "message": "Validation failed.",
                "details": jsonable_encoder(exc.errors()),
            },
        )

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
                "details": None,
            },
        )

    @application.get("/health", tags=["Health"])
    @application.get("/health/live", tags=["Health"])
    @application.get("/api/v1/health", tags=["Health"])
    @application.get("/api/v1/health/live", tags=["Health"])
    async def health() -> dict[str, str]:
        """Liveness probe: the process can serve requests."""
        return {"status": "ok", "version": "1.0.0"}

    @application.get("/health/ready", tags=["Health"])
    @application.get("/api/v1/health/ready", tags=["Health"])
    async def readiness() -> JSONResponse:
        """Readiness probe: the API can reach the database."""
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except Exception as exc:  # noqa: BLE001 - probe must report any DB failure
            logger.error("event=readiness_failed error=%s", type(exc).__name__)
            return JSONResponse(
                status_code=503,
                content={"status": "not ready", "db": "unavailable"},
            )
        return JSONResponse(status_code=200, content={"status": "ready", "db": "ok"})

    # ── API Routers ───────────────────────────────────────────────────────────
    # Mount with /api/v1 prefix (TRD canonical)
    application.include_router(auth.router, prefix="/api/v1/auth")
    application.include_router(admin.router, prefix="/api/v1/admin")
    application.include_router(complaints.router, prefix="/api/v1/complaints")
    application.include_router(department.router, prefix="/api/v1/department")
    application.include_router(superintendent.router, prefix="/api/v1/superintendent")
    application.include_router(internal.router, prefix="/api/v1/internal")

    # Mount with root prefixes for compatibility
    application.include_router(auth.router, prefix="/auth")
    application.include_router(admin.router, prefix="/admin")
    application.include_router(complaints.router, prefix="/complaints")
    application.include_router(department.router, prefix="/department")
    application.include_router(superintendent.router, prefix="/superintendent")

    return application


app: FastAPI = create_app()
