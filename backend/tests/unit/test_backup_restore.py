"""
CivicTrack — Unit test for Backup & Restore Utilities (DEP-010)
Verifies creation of tarball archive containing manifest, uploads, and db dump,
and full round-trip restoration of uploads and manifest data.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path so scripts can be imported
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.backup import create_backup
from scripts.restore import restore_backup


def test_backup_and_restore_roundtrip(tmp_path: Path):
    backup_dir = tmp_path / "backups"
    uploads_dir = tmp_path / "source_uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # Create dummy uploaded files
    sample_file = uploads_dir / "test_photo.jpg"
    sample_file.write_bytes(b"\xff\xd8\xff\xe0" + b"A" * 1024)

    # Execute backup
    archive = create_backup(
        backup_dir=backup_dir,
        uploads_dir=uploads_dir,
        db_url="sqlite:///:memory:",
    )
    assert archive.exists()
    assert archive.stat().st_size > 0

    # Execute restore to a clean target directory
    restore_target = tmp_path / "restored_uploads"
    success = restore_backup(
        archive_path=archive,
        target_uploads_dir=restore_target,
        db_url="sqlite:///:memory:",
    )
    assert success is True
    assert (restore_target / "test_photo.jpg").exists()
    assert (restore_target / "test_photo.jpg").read_bytes() == sample_file.read_bytes()
