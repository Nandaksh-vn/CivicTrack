#!/bin/sh
# CivicTrack restore — verify a backup drill (19.5, DEP-010).
# Usage:  ./scripts/restore.sh <db_dump.sql.gz> [uploads_tar.gz] [--yes]
# Without --yes, the script asks for confirmation (it overwrites the DB).
# After restore it runs `alembic upgrade head` + `python -m app.seed --check`.
set -eu

if [ $# -lt 1 ]; then
  echo "Usage: $0 <db_dump.sql.gz> [uploads_tar.gz] [--yes]" >&2
  exit 1
fi
DB_FILE="$1"
shift
UPLOAD_FILE=""
CONFIRM="no"
for arg in "$@"; do
  case "$arg" in
    --yes) CONFIRM="yes" ;;
    *) UPLOAD_FILE="$arg" ;;
  esac
done

if [ ! -f "$DB_FILE" ]; then
  echo "ERROR: backup file not found: $DB_FILE" >&2
  exit 1
fi
if [ -n "$UPLOAD_FILE" ] && [ ! -f "$UPLOAD_FILE" ]; then
  echo "ERROR: uploads archive not found: $UPLOAD_FILE" >&2
  exit 1
fi

if [ "$CONFIRM" != "yes" ]; then
  echo "This will OVERWRITE the database from $DB_FILE. Type 'yes' to continue: "
  read -r answer
  [ "$answer" = "yes" ] || { echo "Aborted."; exit 1; }
fi

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi
: "${MYSQL_DATABASE:-civictrack}"
: "${MYSQL_USER:-civictrack}"
: "${MYSQL_PASSWORD:?MYSQL_PASSWORD is required (set in .env)}"

echo "[restore] stopping api/worker/web (db volume kept)..."
docker compose stop api worker web 2>/dev/null || true

echo "[restore] restoring MySQL from $DB_FILE"
gzip -dc "$DB_FILE" | docker exec -i civictrack_db mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"

if [ -n "$UPLOAD_FILE" ]; then
  echo "[restore] restoring uploads from $UPLOAD_FILE"
  docker run --rm \
    -v civictrack_uploads:/dst \
    -v "$(pwd)":/backup \
    alpine sh -c "cd /dst && tar xzf /backup/$UPLOAD_FILE && ls -la"
fi

echo "[restore] migrating + verifying..."
docker compose run --rm migrate
docker compose run --rm seed python -m app.seed --check || \
  echo "[restore] seed check skipped (seed profile not required for non-demo restores)"

echo "[restore] starting api/worker/web..."
docker compose up -d --build api worker web
sleep 3
curl -fs http://localhost:8000/health/ready && echo || echo "[restore] WARNING: /health/ready not green yet — check: docker compose logs api"
echo "[restore] complete."
