#!/bin/sh
# CivicTrack backup — MySQL dump + uploads tarball (19.5, DEP-010).
# Usage:  ./scripts/backup.sh [output_dir]
# Output: <output_dir>/civictrack_db_<timestamp>.sql.gz
#         <output_dir>/civictrack_uploads_<timestamp>.tar.gz
# Retention: keep backups for 30 days; NEVER hard-delete complaint data
# (NFR-019). Prune manually once retention expires; backups are append-only.
set -eu

OUT_DIR="${1:-./backups}"
mkdir -p "$OUT_DIR"

# Load DB credentials from .env (Compose env contract).
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi
: "${MYSQL_DATABASE:-civictrack}"
: "${MYSQL_USER:-civictrack}"
: "${MYSQL_PASSWORD:?MYSQL_PASSWORD is required (set in .env)}"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DB_FILE="$OUT_DIR/civictrack_db_${STAMP}.sql.gz"
UPLOAD_FILE="$OUT_DIR/civictrack_uploads_${STAMP}.tar.gz"

echo "[backup] dumping MySQL -> $DB_FILE"
# --no-tablespaces: the app DB user lacks PROCESS (MySQL 8.4 dumps tablespace
# metadata by default, which would fail the backup).
docker exec civictrack_db mysqldump --no-tablespaces -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
  | gzip > "$DB_FILE"
echo "[backup] dumping uploads volume -> $UPLOAD_FILE"
docker run --rm \
  -v civictrack_uploads:/src:ro \
  -v "$(pwd)/$OUT_DIR":/dst \
  alpine tar czf "/dst/civictrack_uploads_${STAMP}.tar.gz" -C /src .

echo "[backup] complete:"
ls -lh "$DB_FILE" "$UPLOAD_FILE"
echo "[backup] restore with: ./scripts/restore.sh $OUT_DIR/civictrack_db_${STAMP}.sql.gz $UPLOAD_FILE"
