"""
CivicTrack - FastAPI application factory.

The Phase 3 skeleton exposes health/readiness probes only. Domain routers are
added in later phases without changing the application wiring.
"""
from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

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
    async def health() -> dict[str, str]:
        """Liveness probe: the process can serve requests."""
        return {"status": "ok", "version": "1.0.0"}

    @application.get("/health/ready", tags=["Health"])
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

    return application


app: FastAPI = create_app()
