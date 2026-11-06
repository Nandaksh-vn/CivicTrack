#!/bin/bash
set -euo pipefail

# CivicTrack Database and Uploads Restore Script (DEP-010)
if [ -z "${1:-}" ]; then
  echo "Usage: $0 <path-to-backup-tar.gz>"
  exit 1
fi

ARCHIVE="$1"
UPLOADS_DIR="${UPLOADS_DIR:-./uploads}"

python3 scripts/restore.py "${ARCHIVE}" --uploads-dir "${UPLOADS_DIR}"
echo "[RESTORE] Completed successfully from ${ARCHIVE}"

