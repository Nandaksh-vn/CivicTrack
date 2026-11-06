#!/bin/bash
set -euo pipefail

# CivicTrack Database and Uploads Backup Script (DEP-010)
BACKUP_DIR="${BACKUP_DIR:-./backups}"
UPLOADS_DIR="${UPLOADS_DIR:-./uploads}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
ARCHIVE="${BACKUP_DIR}/civictrack_backup_${TIMESTAMP}.tar.gz"

mkdir -p "${BACKUP_DIR}"
python3 scripts/backup.py --backup-dir "${BACKUP_DIR}" --uploads-dir "${UPLOADS_DIR}"
echo "[BACKUP] Done: ${ARCHIVE}"

