"""Verified migration helpers for legacy password-direct sensitive storage."""
from __future__ import annotations

import base64
import hashlib
import json
import os
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from uuid import uuid4


@dataclass(frozen=True)
class LegacySnapshot:
    """An immutable pre-write backup of the legacy configuration and records."""

    config: dict[str, object]
    records: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class MigrationBackup:
    """Paths and checksum for a durable pre-migration encrypted-state backup."""

    state_path: Path
    report_path: Path
    checksum: str
    migration_id: str


def _json_value(value: object) -> object:
    if isinstance(value, bytes):
        return {"base64": base64.b64encode(value).decode("ascii")}
    return value


def _database_path(conn) -> Path:
    for _sequence, name, path in conn.execute("PRAGMA database_list"):
        if name == "main" and path:
            return Path(path)
    raise RuntimeError("sensitive migration requires a file-backed database")


def _atomic_write(path: Path, content: bytes) -> None:
    tmp_path = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
        os.chmod(path, 0o600)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def write_durable_legacy_backup(conn, snapshot: LegacySnapshot) -> MigrationBackup:
    """Persist a restrictive encrypted-state backup and verification report before writes."""
    database_path = _database_path(conn)
    backup_dir = database_path.parent / f"{database_path.stem}.sensitive-migration-backups"
    backup_dir.mkdir(mode=0o700, exist_ok=True)
    os.chmod(backup_dir, 0o700)
    migration_id = uuid4().hex
    state = {
        "format": "eduflow-sensitive-legacy-backup-v1",
        "migration_id": migration_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config": {key: _json_value(value) for key, value in snapshot.config.items()},
        "records": [
            {key: _json_value(value) for key, value in record.items()}
            for record in snapshot.records
        ],
    }
    encoded_state = json.dumps(state, sort_keys=True, separators=(",", ":")).encode("utf-8")
    checksum = hashlib.sha256(encoded_state).hexdigest()
    state_path = backup_dir / f"{migration_id}.json"
    report_path = backup_dir / f"{migration_id}.report.json"
    _atomic_write(state_path, encoded_state)
    return MigrationBackup(
        state_path=state_path,
        report_path=report_path,
        checksum=checksum,
        migration_id=migration_id,
    )


def finalize_verified_migration_report(
    backup: MigrationBackup, snapshot: LegacySnapshot
) -> None:
    """Persist proof only after all migrated rows have been reread and verified."""
    report = {
        "format": "eduflow-sensitive-migration-report-v1",
        "migration_id": backup.migration_id,
        "encrypted_state_sha256": backup.checksum,
        "verification_status": "verified",
        "verified_record_count": len(snapshot.records),
        "verified_at": datetime.now(timezone.utc).isoformat(),
    }
    _atomic_write(
        backup.report_path,
        json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    )


def snapshot_legacy_storage(conn) -> LegacySnapshot:
    """Read the complete legacy state before any migration mutation begins."""
    config = conn.execute(
        "SELECT * FROM sensitive_config WHERE id='singleton'"
    ).fetchone()
    records = conn.execute("SELECT * FROM sensitive_memory_items ORDER BY id").fetchall()
    return LegacySnapshot(
        config=dict(config),
        records=tuple(
            {
                key: bytes(value) if isinstance(value, memoryview) else value
                for key, value in dict(record).items()
            }
            for record in records
        ),
    )


def prepare_verified_record_migration(
    snapshot: LegacySnapshot,
    legacy_key: bytes,
    dek: bytes,
    *,
    encrypt: Callable[[bytes, bytes], tuple[bytes, bytes, bytes]],
    decrypt: Callable[[bytes, bytes, bytes, bytes], bytes],
) -> tuple[tuple[bytes, bytes, bytes, str], ...]:
    """Prepare and verify every replacement without mutating the database."""
    replacements = []
    for record in snapshot.records:
        plaintext = decrypt(
            legacy_key,
            record["encrypted_data"],
            record["nonce"],
            record["tag"],
        )
        ciphertext, nonce, tag = encrypt(dek, plaintext)
        if decrypt(dek, ciphertext, nonce, tag) != plaintext:
            raise RuntimeError("sensitive migration verification failed")
        replacements.append((ciphertext, nonce, tag, record["id"]))
    return tuple(replacements)


def verify_persisted_record_migration(
    conn,
    snapshot: LegacySnapshot,
    legacy_key: bytes,
    dek: bytes,
    *,
    decrypt: Callable[[bytes, bytes, bytes, bytes], bytes],
) -> None:
    """Re-read every persisted replacement and compare it with the legacy plaintext."""
    for record in snapshot.records:
        migrated = conn.execute(
            "SELECT encrypted_data, nonce, tag FROM sensitive_memory_items WHERE id=?",
            (record["id"],),
        ).fetchone()
        if not migrated:
            raise RuntimeError("sensitive migration verification failed")
        legacy_plaintext = decrypt(
            legacy_key,
            record["encrypted_data"],
            record["nonce"],
            record["tag"],
        )
        migrated_plaintext = decrypt(
            dek,
            migrated["encrypted_data"],
            migrated["nonce"],
            migrated["tag"],
        )
        if migrated_plaintext != legacy_plaintext:
            raise RuntimeError("sensitive migration verification failed")
