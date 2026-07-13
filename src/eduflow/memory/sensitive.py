"""Sensitive data encryption and session management for EduFlow Memory.

Provides password-protected encrypted storage for sensitive memories (API keys,
SSH credentials, etc.) with a one-time recovery key.

Design:
  - A random DEK encrypts sensitive memories with AES-256-GCM
  - Password and recovery key independently wrap that DEK
  - Session unlock lasts 60 minutes
  - Audit logging with automatic sensitive field redaction
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone

from eduflow.memory.db import get_conn, init_schema
from eduflow.memory import sensitive_migration

# Session timeout: 60 minutes
SESSION_TIMEOUT_S = 3600

# PBKDF2 iterations (OWASP recommended)
PBKDF2_ITERATIONS = 480_000
ENVELOPE_VERSION = 3
PASSWORD_VERIFIER_VERSION = 2

# Password policy
MIN_PASSWORD_LEN = 6

# In-memory session state (per-process)
_unlocked_until: float = 0.0
_derived_key: bytes = b""
_session_generation: int = -1


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _next_id(now: str) -> str:
    date_part = now[:10].replace("-", "")
    prefix = f"SM-{date_part}-"
    conn = get_conn()
    row = conn.execute(
        "SELECT MAX(CAST(SUBSTR(id, ?) AS INTEGER)) FROM sensitive_memory_items WHERE id LIKE ?",
        (len(prefix) + 1, f"{prefix}%"),
    ).fetchone()
    seq = (row[0] or 0) + 1
    return f"SM-{date_part}-{seq:03d}"


# ── Cryptographic primitives ────────────────────────────────────────

def _generate_salt() -> bytes:
    """Generate 32-byte random salt."""
    return os.urandom(32)


def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive 256-bit key from password using PBKDF2."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations=PBKDF2_ITERATIONS,
        dklen=32,
    )


def _hash_password(password: str, salt: bytes) -> str:
    """Create a domain-separated password verifier for storage."""
    root = _derive_key(password, salt)
    verifier = hmac.new(
        root, b"eduflow sensitive v3 password verifier", hashlib.sha256
    ).digest()
    return base64.b64encode(verifier).decode("ascii")


def _hash_password_legacy(password: str, salt: bytes) -> str:
    """Match the pre-V3 verifier, which was also the old encryption key."""
    return base64.b64encode(_derive_key(password, salt)).decode("ascii")


def _derive_password_kek(password: str, salt: bytes) -> bytes:
    """Derive a DEK-wrapping KEK that cannot be reconstructed from the verifier."""
    root = _derive_key(password, salt)
    return hmac.new(
        root, b"eduflow sensitive v3 password kek", hashlib.sha256
    ).digest()


def _verify_password(password: str, stored_hash: str, salt: bytes) -> bool:
    """Verify password against stored hash."""
    computed = _hash_password(password, salt)
    return hmac.compare_digest(computed, stored_hash)


def _verify_legacy_password(password: str, stored_hash: str, salt: bytes) -> bool:
    return hmac.compare_digest(_hash_password_legacy(password, salt), stored_hash)


def _generate_recovery_key() -> str:
    """Generate a printable, high-entropy recovery secret."""
    return base64.urlsafe_b64encode(os.urandom(32)).decode("ascii")


def _derive_recovery_kek(recovery_key: str, salt: bytes) -> bytes:
    return _derive_key(recovery_key, salt)


def _migrate_legacy_storage(conn, row, password: str) -> tuple[bytes, str]:
    """Atomically replace password-direct records after full verification."""
    del row
    conn.execute("BEGIN IMMEDIATE")
    try:
        config = conn.execute(
            "SELECT * FROM sensitive_config WHERE id='singleton'"
        ).fetchone()
        if not config:
            raise RuntimeError("Sensitive storage not configured")
        legacy_salt = base64.b64decode(config["salt"])
        if not _verify_legacy_password(password, config["password_hash"], legacy_salt):
            raise ValueError("Invalid password")
        legacy_key = _derive_key(password, legacy_salt)
        snapshot = sensitive_migration.snapshot_legacy_storage(conn)
        backup = sensitive_migration.write_durable_legacy_backup(conn, snapshot)
        dek = os.urandom(32)
        replacements = sensitive_migration.prepare_verified_record_migration(
            snapshot, legacy_key, dek, encrypt=_encrypt, decrypt=_decrypt
        )
        recovery_key = _generate_recovery_key()
        recovery_salt = _generate_salt()
        password_wrapped_dek, password_wrap_nonce, password_wrap_tag = _encrypt(
            _derive_password_kek(password, legacy_salt), dek
        )
        recovery_wrapped_dek, recovery_wrap_nonce, recovery_wrap_tag = _encrypt(
            _derive_recovery_kek(recovery_key, recovery_salt), dek
        )
        for ciphertext, nonce, tag, memory_id in replacements:
            conn.execute(
                """UPDATE sensitive_memory_items
                   SET encrypted_data=?, nonce=?, tag=?, updated_at=? WHERE id=?""",
                (ciphertext, nonce, tag, _now_iso(), memory_id),
            )
        conn.execute(
            """UPDATE sensitive_config
               SET password_hash=?, schema_version=?, password_verifier_version=?,
                   envelope_generation=envelope_generation + 1,
                   questions_json='[]', password_wrapped_dek=?,
                   password_wrap_nonce=?, password_wrap_tag=?, recovery_salt=?,
                   recovery_wrapped_dek=?, recovery_wrap_nonce=?, recovery_wrap_tag=?,
                   updated_at=? WHERE id='singleton'""",
            (_hash_password(password, legacy_salt), ENVELOPE_VERSION,
             PASSWORD_VERIFIER_VERSION, password_wrapped_dek, password_wrap_nonce, password_wrap_tag,
             base64.b64encode(recovery_salt).decode("ascii"), recovery_wrapped_dek,
             recovery_wrap_nonce, recovery_wrap_tag, _now_iso()),
        )
        sensitive_migration.verify_persisted_record_migration(
            conn, snapshot, legacy_key, dek, decrypt=_decrypt
        )
        sensitive_migration.finalize_verified_migration_report(backup, snapshot)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return dek, recovery_key


def _upgrade_v2_envelope(conn, password: str) -> bytes:
    """Replace V2's leaked verifier/key material without rewriting records."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute(
            "SELECT * FROM sensitive_config WHERE id='singleton'"
        ).fetchone()
        if not row or row["schema_version"] != 2:
            raise RuntimeError("sensitive storage changed during upgrade; retry")
        salt = base64.b64decode(row["salt"])
        if not _verify_legacy_password(password, row["password_hash"], salt):
            raise ValueError("Invalid password")
        dek = _decrypt(
            _derive_key(password, salt), row["password_wrapped_dek"],
            row["password_wrap_nonce"], row["password_wrap_tag"],
        )
        wrapped_dek, wrap_nonce, wrap_tag = _encrypt(
            _derive_password_kek(password, salt), dek
        )
        conn.execute(
            """UPDATE sensitive_config
               SET password_hash=?, schema_version=?, password_verifier_version=?,
                   envelope_generation=envelope_generation + 1,
                   password_wrapped_dek=?, password_wrap_nonce=?, password_wrap_tag=?,
                   updated_at=? WHERE id='singleton'""",
            (_hash_password(password, salt), ENVELOPE_VERSION,
             PASSWORD_VERIFIER_VERSION, wrapped_dek, wrap_nonce, wrap_tag, _now_iso()),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return dek


def _encrypt(key: bytes, plaintext: bytes) -> tuple[bytes, bytes, bytes]:
    """Encrypt with AES-256-GCM. Returns (ciphertext, nonce, tag)."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        raise RuntimeError("authenticated encryption unavailable") from None
    nonce = os.urandom(12)
    ciphertext_and_tag = AESGCM(key).encrypt(nonce, plaintext, None)
    return ciphertext_and_tag[:-16], nonce, ciphertext_and_tag[-16:]


def _decrypt(key: bytes, ciphertext: bytes, nonce: bytes, tag: bytes) -> bytes:
    """Decrypt AES-256-GCM."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        raise RuntimeError("authenticated encryption unavailable") from None
    try:
        return AESGCM(key).decrypt(nonce, ciphertext + tag, None)
    except Exception:
        raise RuntimeError("sensitive data integrity check failed") from None


# ── Password management ─────────────────────────────────────────────

def is_configured() -> bool:
    """Check if sensitive storage has been set up (password configured)."""
    init_schema()
    conn = get_conn()
    row = conn.execute("SELECT COUNT(*) FROM sensitive_config").fetchone()
    return (row[0] or 0) > 0


def setup_password(password: str, questions: list[dict] | None = None) -> dict:
    """Set up password-protected storage and issue a one-time recovery key.

    Args:
        password: User password (min 6 chars)
        questions: Ignored legacy argument retained only for API compatibility.
    """
    if len(password) < MIN_PASSWORD_LEN:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LEN} characters")

    init_schema()
    salt = _generate_salt()
    password_hash = _hash_password(password, salt)
    dek = os.urandom(32)
    password_wrapped_dek, password_wrap_nonce, password_wrap_tag = _encrypt(
        _derive_password_kek(password, salt), dek
    )
    recovery_key = _generate_recovery_key()
    recovery_salt = _generate_salt()
    recovery_wrapped_dek, recovery_wrap_nonce, recovery_wrap_tag = _encrypt(
        _derive_recovery_kek(recovery_key, recovery_salt), dek
    )
    now = _now_iso()

    conn = get_conn()
    try:
        conn.execute("BEGIN IMMEDIATE")
        if conn.execute(
            "SELECT 1 FROM sensitive_config WHERE id='singleton'"
        ).fetchone():
            raise RuntimeError("Sensitive storage already configured")
        conn.execute(
        """INSERT INTO sensitive_config
           (id, password_hash, salt, questions_json, schema_version, password_verifier_version, envelope_generation,
            password_wrapped_dek, password_wrap_nonce, password_wrap_tag,
            recovery_salt, recovery_wrapped_dek, recovery_wrap_nonce, recovery_wrap_tag,
            created_at, updated_at)
           VALUES ('singleton', ?, ?, '[]', ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (password_hash, base64.b64encode(salt).decode("ascii"),
         ENVELOPE_VERSION, PASSWORD_VERIFIER_VERSION,
         password_wrapped_dek, password_wrap_nonce, password_wrap_tag,
         base64.b64encode(recovery_salt).decode("ascii"), recovery_wrapped_dek,
         recovery_wrap_nonce, recovery_wrap_tag, now, now),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {"recovery_key": recovery_key}


def change_password(old_password: str, new_password: str) -> None:
    """Change password by rewrapping the DEK without rewriting records."""
    if len(new_password) < MIN_PASSWORD_LEN:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LEN} characters")

    init_schema()
    conn = get_conn()
    row = conn.execute("SELECT * FROM sensitive_config WHERE id='singleton'").fetchone()
    if not row:
        raise RuntimeError("Sensitive storage not configured")

    salt = base64.b64decode(row["salt"])
    if row["schema_version"] < ENVELOPE_VERSION:
        raise RuntimeError("sensitive storage migration required before changing password")
    if not _verify_password(old_password, row["password_hash"], salt):
        raise ValueError("Invalid current password")

    old_kek = _derive_password_kek(old_password, salt)
    dek = _decrypt(
        old_kek,
        row["password_wrapped_dek"],
        row["password_wrap_nonce"],
        row["password_wrap_tag"],
    )
    new_salt = _generate_salt()
    new_hash = _hash_password(new_password, new_salt)
    wrapped_dek, wrap_nonce, wrap_tag = _encrypt(_derive_password_kek(new_password, new_salt), dek)
    try:
        conn.execute("BEGIN IMMEDIATE")
        result = conn.execute(
            """UPDATE sensitive_config
               SET password_hash=?, salt=?, password_verifier_version=?, envelope_generation=envelope_generation + 1,
                   password_wrapped_dek=?, password_wrap_nonce=?,
                   password_wrap_tag=?, updated_at=?
               WHERE id='singleton' AND updated_at=?""",
            (new_hash, base64.b64encode(new_salt).decode("ascii"), PASSWORD_VERIFIER_VERSION, wrapped_dek,
             wrap_nonce, wrap_tag, _now_iso(), row["updated_at"]),
        )
        if result.rowcount != 1:
            raise RuntimeError("sensitive storage changed during password update; retry")
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    # Update session with new key
    global _derived_key, _unlocked_until, _session_generation
    _derived_key = dek
    _session_generation = conn.execute(
        "SELECT envelope_generation FROM sensitive_config WHERE id='singleton'"
    ).fetchone()["envelope_generation"]
    _unlocked_until = time.time() + SESSION_TIMEOUT_S


def recover_with_key(recovery_key: str, new_password: str) -> None:
    """Set a new password by rewrapping the DEK with the recovery key."""
    if len(new_password) < MIN_PASSWORD_LEN:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LEN} characters")

    init_schema()
    conn = get_conn()
    row = conn.execute("SELECT * FROM sensitive_config WHERE id='singleton'").fetchone()
    if not row:
        raise RuntimeError("Sensitive storage not configured")
    if row["schema_version"] < 2:
        raise RuntimeError("sensitive storage migration required before recovery")

    try:
        recovery_salt = base64.b64decode(row["recovery_salt"])
        dek = _decrypt(
            _derive_recovery_kek(recovery_key, recovery_salt),
            row["recovery_wrapped_dek"],
            row["recovery_wrap_nonce"],
            row["recovery_wrap_tag"],
        )
    except RuntimeError:
        _audit_log("sensitive_recovery_failed", {"reason": "invalid_recovery_key"})
        raise ValueError("Invalid recovery key") from None

    new_salt = _generate_salt()
    password_hash = _hash_password(new_password, new_salt)
    wrapped_dek, wrap_nonce, wrap_tag = _encrypt(_derive_password_kek(new_password, new_salt), dek)
    try:
        conn.execute("BEGIN IMMEDIATE")
        result = conn.execute(
            """UPDATE sensitive_config
               SET password_hash=?, salt=?, schema_version=?, password_verifier_version=?,
                   envelope_generation=envelope_generation + 1, password_wrapped_dek=?, password_wrap_nonce=?,
                   password_wrap_tag=?, updated_at=?
               WHERE id='singleton' AND updated_at=?""",
            (password_hash, base64.b64encode(new_salt).decode("ascii"), ENVELOPE_VERSION,
             PASSWORD_VERIFIER_VERSION, wrapped_dek,
             wrap_nonce, wrap_tag, _now_iso(), row["updated_at"]),
        )
        if result.rowcount != 1:
            raise RuntimeError("sensitive storage changed during password recovery; retry")
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    global _derived_key, _unlocked_until, _session_generation
    _derived_key = dek
    _session_generation = conn.execute(
        "SELECT envelope_generation FROM sensitive_config WHERE id='singleton'"
    ).fetchone()["envelope_generation"]
    _unlocked_until = time.time() + SESSION_TIMEOUT_S
    _audit_log("sensitive_password_recovered", {"method": "recovery_key"})


def unlock(password: str) -> dict:
    """Unlock sensitive storage. Returns session info.

    Raises ValueError if password is wrong.
    """
    global _unlocked_until, _derived_key, _session_generation

    init_schema()
    conn = get_conn()
    row = conn.execute("SELECT * FROM sensitive_config WHERE id='singleton'").fetchone()
    if not row:
        raise RuntimeError("Sensitive storage not configured. Run: eduflow memory sensitive setup")

    salt = base64.b64decode(row["salt"])
    legacy_envelope = row["schema_version"] < ENVELOPE_VERSION
    verifier = _verify_legacy_password if legacy_envelope else _verify_password
    if not verifier(password, row["password_hash"], salt):
        _audit_log("sensitive_unlock_failed", {"reason": "invalid_password"})
        raise ValueError("Invalid password")

    recovery_key = ""
    if row["schema_version"] < 2:
        _derived_key, recovery_key = _migrate_legacy_storage(conn, row, password)
    elif row["schema_version"] < ENVELOPE_VERSION:
        _derived_key = _upgrade_v2_envelope(conn, password)
    else:
        _derived_key = _decrypt(
            _derive_password_kek(password, salt),
            row["password_wrapped_dek"],
            row["password_wrap_nonce"],
            row["password_wrap_tag"],
        )
    _session_generation = get_conn().execute(
        "SELECT envelope_generation FROM sensitive_config WHERE id='singleton'"
    ).fetchone()["envelope_generation"]
    _unlocked_until = time.time() + SESSION_TIMEOUT_S

    _audit_log("sensitive_unlocked", {"expires_in": SESSION_TIMEOUT_S})
    result = {"status": "unlocked", "expires_in": SESSION_TIMEOUT_S}
    if recovery_key:
        result["recovery_key"] = recovery_key
    return result


def lock() -> None:
    """Immediately lock sensitive storage."""
    global _unlocked_until, _derived_key, _session_generation
    _unlocked_until = 0.0
    _derived_key = b""
    _session_generation = -1
    _audit_log("sensitive_locked", {})


def is_unlocked() -> bool:
    """Check if session is currently unlocked."""
    return time.time() < _unlocked_until and bool(_derived_key)


def status() -> dict:
    """Return current lock status."""
    remaining = max(0.0, _unlocked_until - time.time())
    return {
        "unlocked": remaining > 0,
        "expires_in": int(remaining),
        "configured": is_configured(),
    }


def recover(answers: dict[str, str], new_password: str) -> None:
    """Reject retired security-question recovery without inspecting answers."""
    del answers, new_password
    raise RuntimeError("security-question recovery is permanently disabled; use a recovery key")


def get_security_questions() -> list[str]:
    """Security questions are retired and must never be exposed again."""
    return []


# ── Sensitive memory CRUD ───────────────────────────────────────────

def add_sensitive(
    scope: str,
    kind: str,
    content: str,
    *,
    created_by: str = "",
) -> str:
    """Add a new sensitive memory item (encrypted).

    Returns the sensitive memory ID.
    """
    if not is_unlocked():
        raise PermissionError("Sensitive storage is locked. Unlock first.")

    init_schema()
    conn = get_conn()
    session_key = _derived_key
    session_generation = _session_generation
    try:
        conn.execute("BEGIN IMMEDIATE")
        config = conn.execute(
            "SELECT schema_version, envelope_generation FROM sensitive_config WHERE id='singleton'"
        ).fetchone()
        if (
            not config
            or config["schema_version"] != ENVELOPE_VERSION
            or config["envelope_generation"] != session_generation
        ):
            raise PermissionError("Sensitive storage session is stale. Unlock again.")
        now = _now_iso()
        mid = _next_id(now)
        plaintext = json.dumps({
            "content": content,
            "created_by": created_by,
            "created_at": now,
        }, ensure_ascii=False).encode("utf-8")
        ct, nonce, tag = _encrypt(session_key, plaintext)
        conn.execute(
            """INSERT INTO sensitive_memory_items
               (id, scope, kind, encrypted_data, nonce, tag, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, 'confirmed', ?, ?)""",
            (mid, scope, kind, ct, nonce, tag, now, now),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    _audit_log("sensitive_added", {"memory_id": mid, "scope": scope, "kind": kind})
    return mid


def get_sensitive(memory_id: str) -> dict | None:
    """Get and decrypt a sensitive memory item."""
    if not is_unlocked():
        raise PermissionError("Sensitive storage is locked. Unlock first.")

    init_schema()
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM sensitive_memory_items WHERE id = ?", (memory_id,)
    ).fetchone()
    if not row:
        return None

    # Decrypt
    plaintext = _decrypt(_derived_key, row["encrypted_data"], row["nonce"], row["tag"])
    data = json.loads(plaintext.decode("utf-8"))

    _audit_log("sensitive_accessed", {"memory_id": memory_id})

    return {
        "id": row["id"],
        "scope": row["scope"],
        "kind": row["kind"],
        "content": data["content"],
        "status": row["status"],
        "created_by": data.get("created_by", ""),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "sensitive": True,
    }


def list_sensitive(
    scope: str | None = None,
    kind: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """List sensitive memory items (without decrypting content)."""
    if not is_unlocked():
        raise PermissionError("Sensitive storage is locked. Unlock first.")

    init_schema()
    conn = get_conn()
    query = "SELECT id, scope, kind, status, created_at, updated_at FROM sensitive_memory_items WHERE 1=1"
    params: list = []
    if scope:
        query += " AND scope = ?"
        params.append(scope)
    if kind:
        query += " AND kind = ?"
        params.append(kind)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    return [
        {
            "id": r["id"],
            "scope": r["scope"],
            "kind": r["kind"],
            "status": r["status"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
            "content": "[ENCRYPTED]",
            "sensitive": True,
        }
        for r in rows
    ]


def search_sensitive(query: str, limit: int = 20) -> list[dict]:
    """Search sensitive memories by decrypting and matching content.

    This is expensive (decrypts all items) but necessary for search.
    """
    if not is_unlocked():
        raise PermissionError("Sensitive storage is locked. Unlock first.")

    init_schema()
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM sensitive_memory_items WHERE status='confirmed' ORDER BY created_at DESC"
    ).fetchall()

    results = []
    query_lower = query.lower()
    for row in rows:
        try:
            plaintext = _decrypt(_derived_key, row["encrypted_data"], row["nonce"], row["tag"])
            data = json.loads(plaintext.decode("utf-8"))
            content = data.get("content", "")
            if query_lower in content.lower():
                results.append({
                    "id": row["id"],
                    "scope": row["scope"],
                    "kind": row["kind"],
                    "content": content,
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "sensitive": True,
                })
                if len(results) >= limit:
                    break
        except Exception:
            raise RuntimeError("sensitive data integrity check failed") from None

    _audit_log("sensitive_searched", {"query": query[:50], "results": len(results)})
    return results


def delete_sensitive(memory_id: str) -> bool:
    """Delete a sensitive memory item."""
    if not is_unlocked():
        raise PermissionError("Sensitive storage is locked. Unlock first.")

    init_schema()
    conn = get_conn()
    cur = conn.execute(
        "DELETE FROM sensitive_memory_items WHERE id = ?", (memory_id,)
    )
    conn.commit()

    if cur.rowcount > 0:
        _audit_log("sensitive_deleted", {"memory_id": memory_id})
        return True
    return False


def export_sensitive_json() -> list[dict]:
    """Export all sensitive memories as decrypted JSON (for re-encryption)."""
    if not is_unlocked():
        raise PermissionError("Sensitive storage is locked. Unlock first.")

    init_schema()
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM sensitive_memory_items WHERE status='confirmed' ORDER BY created_at"
    ).fetchall()

    items = []
    for row in rows:
        try:
            plaintext = _decrypt(_derived_key, row["encrypted_data"], row["nonce"], row["tag"])
            data = json.loads(plaintext.decode("utf-8"))
            items.append({
                "id": row["id"],
                "scope": row["scope"],
                "kind": row["kind"],
                "content": data["content"],
                "created_by": data.get("created_by", ""),
                "created_at": row["created_at"],
            })
        except Exception:
            raise RuntimeError("sensitive data integrity check failed") from None

    return items


# ── Audit logging ───────────────────────────────────────────────────

_SENSITIVE_FIELDS = frozenset({"password", "answer", "token", "api_key", "secret"})


def _audit_log(action: str, details: dict) -> None:
    """Append audit record with automatic sensitive field redaction."""
    sanitized = {}
    for k, v in details.items():
        if k.lower() in _SENSITIVE_FIELDS:
            sanitized[k] = "***REDACTED***"
        else:
            sanitized[k] = v

    record = {
        "ts": _now_iso(),
        "action": action,
        **sanitized,
    }
    try:
        from pathlib import Path
        log_path = Path.home() / ".eduflow" / "audit.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass
