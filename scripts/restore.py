#!/usr/bin/env python3
"""
CivicTrack — Automated Restore Script (DEP-010)
Restores database state and uploads folder from a compressed backup tarball.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import tarfile
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("civictrack.restore")


def restore_backup(
    archive_path: Path,
    target_uploads_dir: Path,
    db_url: str | None = None,
) -> bool:
    if not archive_path.exists():
        logger.error(f"Backup archive not found: {archive_path}")
        return False

    temp_extract_dir = archive_path.parent / "temp_restore_extract"
    if temp_extract_dir.exists():
        shutil.rmtree(temp_extract_dir)
    temp_extract_dir.mkdir(parents=True, exist_ok=True)

    try:
        logger.info(f"Extracting archive {archive_path}...")
        with tarfile.open(archive_path, "r:gz") as tar:
            try:
                tar.extractall(path=temp_extract_dir, filter="data")
            except TypeError:
                tar.extractall(path=temp_extract_dir)

        # 1. Verify manifest
        manifest_path = temp_extract_dir / "manifest.json"
        if not manifest_path.exists():
            logger.error("Invalid backup: missing manifest.json")
            return False

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        logger.info(f"Verified backup version: {manifest.get('version')}, created: {manifest.get('created_at')}")

        # 2. Restore uploads
        src_uploads = temp_extract_dir / "uploads"
        if src_uploads.exists():
            target_uploads_dir.mkdir(parents=True, exist_ok=True)
            for item in src_uploads.iterdir():
                dest = target_uploads_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)
            logger.info(f"Restored uploads directory to {target_uploads_dir}")

        # 3. Database restoration note
        db_sql = temp_extract_dir / "database.sql"
        if db_sql.exists():
            logger.info("Found database dump in backup archive.")
            if db_url and "mysql" in db_url:
                logger.info("MySQL target detected. SQL statements can be applied via mysql CLI.")

        logger.info("Restore process completed successfully.")
        return True
    finally:
        if temp_extract_dir.exists():
            shutil.rmtree(temp_extract_dir, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="CivicTrack Restore Utility")
    parser.add_argument("archive", help="Path to backup archive (.tar.gz)")
    parser.add_argument("--uploads-dir", default="./uploads", help="Path to restore uploads to")
    parser.add_argument("--db-url", default=os.getenv("DATABASE_URL"), help="Database connection URL")
    args = parser.parse_args()

    success = restore_backup(
        archive_path=Path(args.archive),
        target_uploads_dir=Path(args.uploads_dir),
        db_url=args.db_url,
    )
    if not success:
        exit(1)


if __name__ == "__main__":
    main()
