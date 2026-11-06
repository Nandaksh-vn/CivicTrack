#!/bin/sh
# CivicTrack backend entrypoint — migration-on-start with failure visibility.
# Set RUN_MIGRATIONS=true (default for `api`) to run `alembic upgrade head`
# before exec'ing the container command. The one-shot `migrate` service sets
# RUN_MIGRATIONS=false and runs alembic directly so `docker compose` can gate
# dependents on `service_completed_successfully`. Migration failures print
# to stderr and exit non-zero so Compose surfaces the failure immediately.
set -e

if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
  echo "[entrypoint] Running migrations: alembic upgrade head"
  attempt=1
  max_attempts=10
  until alembic upgrade head; do
    if [ "$attempt" -ge "$max_attempts" ]; then
      echo "[entrypoint] ERROR: migrations failed after ${max_attempts} attempts" >&2
      exit 1
    fi
    echo "[entrypoint] Migration attempt ${attempt} failed, retrying in 3s..." >&2
    attempt=$((attempt + 1))
    sleep 3
  done
  echo "[entrypoint] Migrations complete"
fi

exec "$@"
