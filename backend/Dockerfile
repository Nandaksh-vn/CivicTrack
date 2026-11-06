# CivicTrack Backend — multi-stage production image (19.1, DEP-004)
#
# Builder: installs dependencies into an isolated venv.
# Runtime: copies only venv + code, runs as non-root `civictrack`,
# exposes healthchecks and an entrypoint that can auto-migrate.
# Build:   docker compose build api
# Run:     see docker-compose.yml / docs/RUNBOOK.md

FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./

# Install runtime deps + project metadata into a venv that we copy wholesale.
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install "."

COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic
COPY docker-entrypoint.sh /opt/docker-entrypoint.sh

# Compile-check the package in the builder so a broken image fails fast.
RUN /opt/venv/bin/python -c "import app.main; import app.worker; import app.seed"

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:${PATH}" \
    RUN_MIGRATIONS="true"

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1001 civictrack

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app/app ./app
COPY --from=builder /app/alembic.ini ./alembic.ini
COPY --from=builder /app/alembic ./alembic
COPY --from=builder /opt/docker-entrypoint.sh /docker-entrypoint.sh

RUN mkdir -p /app/uploads \
    && chown -R civictrack:civictrack /app /opt/venv \
    && chmod +x /docker-entrypoint.sh

USER civictrack

EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

ENTRYPOINT ["/bin/sh", "/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
