#!/bin/sh
# Idempotent demo seed (19.4). Requires the stack to be up with migrations applied.
# Usage: ./scripts/seed.sh [--check] [--reset]
set -eu
docker compose run --rm seed python -m app.seed "$@"
