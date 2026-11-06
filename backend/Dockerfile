# CivicTrack Backend - production image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libffi-dev \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1001 civictrack

COPY pyproject.toml ./
COPY app ./app

RUN pip install --upgrade pip \
    && pip install --no-cache-dir . \
    && rm -rf /root/.cache/pip

COPY alembic.ini ./
COPY alembic ./alembic

RUN mkdir -p /app/uploads && chown -R civictrack:civictrack /app

USER civictrack

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
