#!/bin/sh
# Full demo reset: tear down volumes, rebuild, migrate, seed (19.4).
# WARNING: deletes the local DB + uploads volumes. Never run in production.
# Usage: ./scripts/reset.sh
set -eu
echo "[reset] stopping stack and deleting volumes (DESTRUCTIVE)..."
docker compose down -v --remove-orphans
echo "[reset] rebuilding and starting..."
docker compose up -d --build
echo "[reset] seeding demo data (idempotent)..."
docker compose run --rm seed python -m app.seed
echo "[reset] verifying overdue candidate..."
docker compose run --rm seed python -m app.seed --check
echo "[reset] done. Open http://localhost:8080 and log in with a demo account."
