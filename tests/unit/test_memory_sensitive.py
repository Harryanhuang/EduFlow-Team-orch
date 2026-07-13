"""Tests for sensitive data encryption and session management."""
from __future__ import annotations

from datetime import datetime, timezone
import builtins
import base64
import json

import pytest

from eduflow.commands import memory_cli
from eduflow.memory import db, sensitive
from eduflow.memory import obsidian_export


@pytest.fixture(autouse=True)
def _clean_sensitive(tmp_path, monkeypatch):
    """Use a temporary DB for each test."""
    db_path = tmp_path / "test_memory.db"
    conn = db.sqlite3.connect(str(db_path), timeout=5.0)
    conn.row_factory = db.sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")

    db._local.conn = conn
    db.init_schema()
    yield
    conn.close()
    db._local.conn = None
    # Reset session state
    sensitive._unlocked_until = 0.0
    sensitive._derived_key = b""
    sensitive._session_generation = -1


_PASSWORD = "testpass123"
_QUESTIONS = [
    {"question": "What is your pet's name?", "answer": "fluffy"},
    {"question": "What city were you born in?", "answer": "beijing"},
    {"question": "What is your mother's maiden name?", "answer": "smith"},
]


def _insert_legacy_sensitive_record(content: str = "legacy secret") -> str:
    """Create the pre-D1 password-direct layout without using product setup."""
    salt = sensitive._generate_salt()
    legacy_key = sensitive._derive_key(_PASSWORD, salt)
    now = "2026-07-13T00:00:00+00:00"
    payload = json.dumps({"content": content, "created_at": now}).encode("utf-8")
    ciphertext, nonce, tag = sensitive._encrypt(legacy_key, payload)
    conn = db.get_conn()
    conn.execute(
        """INSERT INTO sensitive_config
           (id, password_hash, salt, questions_json, created_at, updated_at)
           VALUES ('singleton', ?, ?, '[]', ?, ?)""",
        (sensitive._hash_password_legacy(_PASSWORD, salt), base64.b64encode(salt).decode("ascii"), now, now),
    )
    memory_id = "SM-20260713-001"
    conn.execute(
        """INSERT INTO sensitive_memory_items
           (id, scope, kind, encrypted_data, nonce, tag, status, created_at, updated_at)
           VALUES (?, 'team', 'note', ?, ?, ?, 'confirmed', ?, ?)""",
        (memory_id, ciphertext, nonce, tag, now, now),
    )
    conn.commit()
    return memory_id


def _replace_with_exact_pre_d1_sensitive_schema() -> None:
    """Restore the physical sensitive tables that existed before the DEK upgrade."""
    conn = db.get_conn()
    conn.execute("DROP TABLE sensitive_memory_items")
    conn.execute("DROP TABLE sensitive_config")
    conn.executescript(
        """
        CREATE TABLE sensitive_config (
            id TEXT PRIMARY KEY DEFAULT 'singleton',
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            questions_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE sensitive_memory_items (
            id TEXT PRIMARY KEY,
            scope TEXT NOT NULL,
            kind TEXT NOT NULL,
            encrypted_data BLOB NOT NULL,
            nonce BLOB NOT NULL,
            tag BLOB NOT NULL,
            status TEXT NOT NULL DEFAULT 'confirmed',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
    )
    conn.commit()


def test_setup_and_is_configured():
    assert not sensitive.is_configured()
    sensitive.setup_password(_PASSWORD, _QUESTIONS)
    assert sensitive.is_configured()


def test_unlock_with_correct_password():
    sensitive.setup_password(_PASSWORD, _QUESTIONS)
    result = sensitive.unlock(_PASSWORD)
    assert result["status"] == "unlocked"
    assert result["expires_in"] == 3600
    assert sensitive.is_unlocked()


def test_unlock_with_wrong_password():
    sensitive.setup_password(_PASSWORD, _QUESTIONS)
    with pytest.raises(ValueError):
        sensitive.unlock("wrongpassword")
    assert not sensitive.is_unlocked()


def test_lock():
    sensitive.setup_password(_PASSWORD, _QUESTIONS)
    sensitive.unlock(_PASSWORD)
    assert sensitive.is_unlocked()
    sensitive.lock()
    assert not sensitive.is_unlocked()


def test_status():
    s = sensitive.status()
    assert not s["unlocked"]
    assert not s["configured"]

    sensitive.setup_password(_PASSWORD, _QUESTIONS)
    s = sensitive.status()
    assert not s["unlocked"]
    assert s["configured"]

    sensitive.unlock(_PASSWORD)
    s = sensitive.status()
    assert s["unlocked"]
    assert s["expires_in"] > 0


def test_add_and_get_sensitive():
    sensitive.setup_password(_PASSWORD, _QUESTIONS)
    sensitive.unlock(_PASSWORD)

    mid = sensitive.add_sensitive("team", "note", "my ssh password: secret123")
    assert mid.startswith("SM-")

    m = sensitive.get_sensitive(mid)
    assert m is not None
    assert m["content"] == "my ssh password: secret123"
    assert m["sensitive"] is True
    assert m["scope"] == "team"


def test_list_sensitive():
    sensitive.setup_password(_PASSWORD, _QUESTIONS)
    sensitive.unlock(_PASSWORD)

    sensitive.add_sensitive("team", "note", "item 1")
    sensitive.add_sensitive("team", "api_key", "item 2")
    sensitive.add_sensitive("lane:course", "note", "item 3")

    items = sensitive.list_sensitive()
    assert len(items) == 3
    # Content should be masked in list
    assert all(i["content"] == "[ENCRYPTED]" for i in items)


def test_list_sensitive_with_scope_filter():
    sensitive.setup_password(_PASSWORD, _QUESTIONS)
    sensitive.unlock(_PASSWORD)

    sensitive.add_sensitive("team", "note", "item 1")
    sensitive.add_sensitive("lane:course", "note", "item 2")

    items = sensitive.list_sensitive(scope="team")
    assert len(items) == 1


def test_search_sensitive():
    sensitive.setup_password(_PASSWORD, _QUESTIONS)
    sensitive.unlock(_PASSWORD)

    sensitive.add_sensitive("team", "note", "SSH password for production server")
    sensitive.add_sensitive("team", "note", "API key for OpenAI")

    results = sensitive.search_sensitive("SSH")
    assert len(results) == 1
    assert "SSH" in results[0]["content"]

    results = sensitive.search_sensitive("api key")
    assert len(results) == 1
    assert "OpenAI" in results[0]["content"]


def test_delete_sensitive():
    sensitive.setup_password(_PASSWORD, _QUESTIONS)
    sensitive.unlock(_PASSWORD)

    mid = sensitive.add_sensitive("team", "note", "temporary secret")
    assert sensitive.get_sensitive(mid) is not None

    assert sensitive.delete_sensitive(mid) is True
    assert sensitive.get_sensitive(mid) is None


def test_operations_blocked_when_locked():
    sensitive.setup_password(_PASSWORD, _QUESTIONS)

    with pytest.raises(PermissionError):
        sensitive.add_sensitive("team", "note", "test")

    with pytest.raises(PermissionError):
        sensitive.get_sensitive("SM-00000000-001")

    with pytest.raises(PermissionError):
        sensitive.list_sensitive()

    with pytest.raises(PermissionError):
        sensitive.search_sensitive("test")


def test_add_sensitive_rejects_a_stale_envelope_session():
    sensitive.setup_password(_PASSWORD)
    sensitive.unlock(_PASSWORD)
    db.get_conn().execute(
        "UPDATE sensitive_config SET envelope_generation=envelope_generation + 1 WHERE id='singleton'"
    )
    db.get_conn().commit()

    with pytest.raises(PermissionError, match="session is stale"):
        sensitive.add_sensitive("team", "note", "must not use stale encryption key")


def test_change_password():
    sensitive.setup_password(_PASSWORD, _QUESTIONS)
    sensitive.unlock(_PASSWORD)
    mid = sensitive.add_sensitive("team", "note", "secret data")

    # Change password
    new_pw = "newpassword456"
    sensitive.change_password(_PASSWORD, new_pw)

    # Old password should not work
    sensitive.lock()
    with pytest.raises(ValueError):
        sensitive.unlock(_PASSWORD)

    # New password should work and data should be accessible
    sensitive.unlock(new_pw)
    m = sensitive.get_sensitive(mid)
    assert m["content"] == "secret data"


def test_change_password_rewraps_dek_without_reencrypting_100_records():
    """A password rotation changes only the password wrapper around the DEK."""
    sensitive.setup_password(_PASSWORD)
    sensitive.unlock(_PASSWORD)
    memory_ids = [
        sensitive.add_sensitive("team", "note", f"secret data {index}")
        for index in range(100)
    ]
    conn = db.get_conn()
    before = {
        row["id"]: (bytes(row["encrypted_data"]), bytes(row["nonce"]), bytes(row["tag"]))
        for row in conn.execute(
            "SELECT id, encrypted_data, nonce, tag FROM sensitive_memory_items"
        )
    }

    new_password = "newpassword456"
    sensitive.change_password(_PASSWORD, new_password)

    after = {
        row["id"]: (bytes(row["encrypted_data"]), bytes(row["nonce"]), bytes(row["tag"]))
        for row in conn.execute(
            "SELECT id, encrypted_data, nonce, tag FROM sensitive_memory_items"
        )
    }
    assert after == before

    sensitive.lock()
    with pytest.raises(ValueError, match="Invalid password"):
        sensitive.unlock(_PASSWORD)
    sensitive.unlock(new_password)
    assert [sensitive.get_sensitive(memory_id)["content"] for memory_id in memory_ids] == [
        f"secret data {index}" for index in range(100)
    ]


def test_database_password_verifier_cannot_unwrap_the_dek():
    sensitive.setup_password(_PASSWORD)
    row = db.get_conn().execute(
        """SELECT password_hash, password_wrapped_dek, password_wrap_nonce,
                  password_wrap_tag FROM sensitive_config WHERE id='singleton'"""
    ).fetchone()

    with pytest.raises(RuntimeError, match="integrity check failed"):
        sensitive._decrypt(
            base64.b64decode(row["password_hash"]),
            row["password_wrapped_dek"],
            row["password_wrap_nonce"],
            row["password_wrap_tag"],
        )


def test_unlock_upgrades_insecure_v2_envelope_without_rewriting_records():
    sensitive.setup_password(_PASSWORD)
    sensitive.unlock(_PASSWORD)
    memory_id = sensitive.add_sensitive("team", "note", "v2 migration secret")
    conn = db.get_conn()
    item_before = tuple(conn.execute(
        "SELECT encrypted_data, nonce, tag FROM sensitive_memory_items WHERE id=?", (memory_id,)
    ).fetchone())
    config = conn.execute("SELECT * FROM sensitive_config WHERE id='singleton'").fetchone()
    salt = base64.b64decode(config["salt"])
    wrapped_dek, wrap_nonce, wrap_tag = sensitive._encrypt(
        sensitive._derive_key(_PASSWORD, salt), sensitive._derived_key
    )
    conn.execute(
        """UPDATE sensitive_config
           SET password_hash=?, schema_version=2, password_verifier_version=1,
               password_wrapped_dek=?, password_wrap_nonce=?, password_wrap_tag=?
           WHERE id='singleton'""",
        (sensitive._hash_password_legacy(_PASSWORD, salt), wrapped_dek, wrap_nonce, wrap_tag),
    )
    conn.commit()
    sensitive.lock()

    sensitive.unlock(_PASSWORD)

    upgraded = conn.execute("SELECT * FROM sensitive_config WHERE id='singleton'").fetchone()
    assert upgraded["schema_version"] == sensitive.ENVELOPE_VERSION
    assert tuple(conn.execute(
        "SELECT encrypted_data, nonce, tag FROM sensitive_memory_items WHERE id=?", (memory_id,)
    ).fetchone()) == item_before
    with pytest.raises(RuntimeError, match="integrity check failed"):
        sensitive._decrypt(
            base64.b64decode(upgraded["password_hash"]),
            upgraded["password_wrapped_dek"],
            upgraded["password_wrap_nonce"],
            upgraded["password_wrap_tag"],
        )


def test_recovery_key_restores_access_to_existing_encrypted_records():
    setup = sensitive.setup_password(_PASSWORD)
    recovery_key = setup["recovery_key"]
    sensitive.unlock(_PASSWORD)
    memory_ids = [
        sensitive.add_sensitive("team", "note", f"recoverable secret {index}")
        for index in range(3)
    ]
    sensitive.lock()

    sensitive.recover_with_key(recovery_key, "recoveredpassword456")

    with pytest.raises(ValueError, match="Invalid password"):
        sensitive.unlock(_PASSWORD)
    sensitive.unlock("recoveredpassword456")
    assert [sensitive.get_sensitive(memory_id)["content"] for memory_id in memory_ids] == [
        f"recoverable secret {index}" for index in range(3)
    ]


def test_recovery_key_is_issued_once_and_not_stored_in_plaintext():
    setup = sensitive.setup_password(_PASSWORD)
    recovery_key = setup["recovery_key"]
    config_values = tuple(
        db.get_conn().execute("SELECT * FROM sensitive_config WHERE id='singleton'").fetchone()
    )

    assert recovery_key not in repr(config_values)
    with pytest.raises(RuntimeError, match="already configured"):
        sensitive.setup_password("anotherpassword456")
    sensitive.unlock(_PASSWORD)
    sensitive.lock()
    assert "recovery_key" not in sensitive.unlock(_PASSWORD)


def test_invalid_recovery_key_does_not_change_the_current_password():
    sensitive.setup_password(_PASSWORD)

    with pytest.raises(ValueError, match="Invalid recovery key"):
        sensitive.recover_with_key("not-the-recovery-key", "recoveredpassword456")

    sensitive.unlock(_PASSWORD)
    sensitive.lock()
    with pytest.raises(ValueError, match="Invalid password"):
        sensitive.unlock("recoveredpassword456")


def test_unlock_migrates_legacy_records_to_a_verified_dek_envelope(tmp_path):
    memory_id = _insert_legacy_sensitive_record()

    sensitive.unlock(_PASSWORD)

    assert sensitive.get_sensitive(memory_id)["content"] == "legacy secret"
    config = db.get_conn().execute(
        "SELECT schema_version, password_wrapped_dek FROM sensitive_config WHERE id='singleton'"
    ).fetchone()
    assert config["schema_version"] == sensitive.ENVELOPE_VERSION
    assert config["password_wrapped_dek"]
    backup_dir = tmp_path / "test_memory.sensitive-migration-backups"
    backups = [path for path in backup_dir.glob("*.json") if not path.name.endswith(".report.json")]
    reports = list(backup_dir.glob("*.report.json"))
    assert len(backups) == 1
    assert len(reports) == 1
    assert "legacy secret" not in backups[0].read_text(encoding="utf-8")
    assert oct(backups[0].stat().st_mode & 0o777) == "0o600"
    backup = json.loads(backups[0].read_text(encoding="utf-8"))
    assert backup["records"][0]["scope"] == "team"
    assert backup["records"][0]["kind"] == "note"
    report = json.loads(reports[0].read_text(encoding="utf-8"))
    assert report["verification_status"] == "verified"
    assert report["verified_record_count"] == 1


def test_unlock_migrates_an_actual_pre_d1_table_before_reading_envelope_fields():
    _replace_with_exact_pre_d1_sensitive_schema()
    memory_id = _insert_legacy_sensitive_record("physical legacy secret")
    conn = db.get_conn()
    assert "schema_version" not in {
        row["name"] for row in conn.execute("PRAGMA table_info(sensitive_config)")
    }

    sensitive.unlock(_PASSWORD)

    assert sensitive.get_sensitive(memory_id)["content"] == "physical legacy secret"


def test_interrupted_legacy_migration_preserves_the_original_decryptable_data(monkeypatch):
    memory_id = _insert_legacy_sensitive_record()
    conn = db.get_conn()
    before_config = tuple(
        conn.execute("SELECT * FROM sensitive_config WHERE id='singleton'").fetchone()
    )
    before_record = tuple(
        conn.execute(
            "SELECT encrypted_data, nonce, tag, updated_at FROM sensitive_memory_items WHERE id=?",
            (memory_id,),
        ).fetchone()
    )

    def interrupt_migration():
        raise RuntimeError("simulated interrupted migration")

    monkeypatch.setattr(sensitive, "_now_iso", interrupt_migration)
    with pytest.raises(RuntimeError, match="simulated interrupted migration"):
        sensitive.unlock(_PASSWORD)

    assert tuple(conn.execute("SELECT * FROM sensitive_config WHERE id='singleton'").fetchone()) == before_config
    assert tuple(
        conn.execute(
            "SELECT encrypted_data, nonce, tag, updated_at FROM sensitive_memory_items WHERE id=?",
            (memory_id,),
        ).fetchone()
    ) == before_record
    salt = base64.b64decode(conn.execute(
        "SELECT salt FROM sensitive_config WHERE id='singleton'"
    ).fetchone()["salt"])
    record = conn.execute(
        "SELECT encrypted_data, nonce, tag FROM sensitive_memory_items WHERE id=?", (memory_id,)
    ).fetchone()
    plaintext = sensitive._decrypt(
        sensitive._derive_key(_PASSWORD, salt),
        record["encrypted_data"], record["nonce"], record["tag"],
    )
    assert json.loads(plaintext)["content"] == "legacy secret"


def test_legacy_migration_backup_failure_preserves_original_decryptable_data(monkeypatch):
    memory_id = _insert_legacy_sensitive_record()
    conn = db.get_conn()
    before_config = tuple(
        conn.execute("SELECT * FROM sensitive_config WHERE id='singleton'").fetchone()
    )

    def fail_backup(*_args, **_kwargs):
        raise OSError("simulated backup failure")

    monkeypatch.setattr(
        sensitive.sensitive_migration, "write_durable_legacy_backup", fail_backup, raising=False
    )
    with pytest.raises(OSError, match="simulated backup failure"):
        sensitive.unlock(_PASSWORD)

    assert tuple(conn.execute("SELECT * FROM sensitive_config WHERE id='singleton'").fetchone()) == before_config
    record = conn.execute(
        "SELECT encrypted_data, nonce, tag FROM sensitive_memory_items WHERE id=?", (memory_id,)
    ).fetchone()
    salt = base64.b64decode(conn.execute(
        "SELECT salt FROM sensitive_config WHERE id='singleton'"
    ).fetchone()["salt"])
    assert json.loads(sensitive._decrypt(
        sensitive._derive_key(_PASSWORD, salt), record["encrypted_data"], record["nonce"], record["tag"]
    ))["content"] == "legacy secret"


def test_legacy_migration_holds_write_lock_before_snapshot(monkeypatch):
    _insert_legacy_sensitive_record()
    original_snapshot = sensitive.sensitive_migration.snapshot_legacy_storage

    def snapshot_under_write_lock(conn):
        assert conn.in_transaction
        return original_snapshot(conn)

    monkeypatch.setattr(
        sensitive.sensitive_migration, "snapshot_legacy_storage", snapshot_under_write_lock
    )
    sensitive.unlock(_PASSWORD)


def test_failed_post_write_migration_verification_rolls_back_to_legacy_data(monkeypatch):
    memory_id = _insert_legacy_sensitive_record()
    conn = db.get_conn()
    before_config = tuple(
        conn.execute("SELECT * FROM sensitive_config WHERE id='singleton'").fetchone()
    )

    def fail_verification(*_args, **_kwargs):
        raise RuntimeError("simulated persisted verification failure")

    monkeypatch.setattr(
        sensitive.sensitive_migration, "verify_persisted_record_migration", fail_verification
    )
    with pytest.raises(RuntimeError, match="simulated persisted verification failure"):
        sensitive.unlock(_PASSWORD)

    assert tuple(conn.execute("SELECT * FROM sensitive_config WHERE id='singleton'").fetchone()) == before_config
    salt = base64.b64decode(conn.execute(
        "SELECT salt FROM sensitive_config WHERE id='singleton'"
    ).fetchone()["salt"])
    record = conn.execute(
        "SELECT encrypted_data, nonce, tag FROM sensitive_memory_items WHERE id=?", (memory_id,)
    ).fetchone()
    assert json.loads(sensitive._decrypt(
        sensitive._derive_key(_PASSWORD, salt), record["encrypted_data"], record["nonce"], record["tag"]
    ))["content"] == "legacy secret"


def test_sensitive_setup_cli_displays_recovery_key_without_security_questions(
    monkeypatch, capsys
):
    responses = iter([_PASSWORD, _PASSWORD])
    monkeypatch.setattr("getpass.getpass", lambda _prompt: next(responses))
    monkeypatch.setattr(
        "builtins.input",
        lambda _prompt: pytest.fail("setup must not ask security questions"),
    )

    assert memory_cli._cmd_sensitive_setup([]) == 0

    output = capsys.readouterr().out
    assert "Recovery key" in output
    assert "Security questions" not in output


def test_sensitive_recovery_cli_rejects_recovery_keys_passed_in_argv(capsys):
    assert memory_cli._cmd_sensitive_recover(["must-not-use-command-line-key"]) == 1
    captured = capsys.readouterr()
    assert "usage:" in captured.out + captured.err


def test_change_password_keeps_tampered_record_detectable_without_rewriting_others():
    sensitive.setup_password(_PASSWORD, _QUESTIONS)
    sensitive.unlock(_PASSWORD)
    first_id = sensitive.add_sensitive("team", "note", "first secret")
    second_id = sensitive.add_sensitive("team", "note", "second secret")
    conn = db.get_conn()
    second = conn.execute(
        "SELECT tag FROM sensitive_memory_items WHERE id = ?", (second_id,)
    ).fetchone()
    tag = bytes(second["tag"])
    conn.execute(
        "UPDATE sensitive_memory_items SET tag = ? WHERE id = ?",
        (bytes([tag[0] ^ 1]) + tag[1:], second_id),
    )
    conn.commit()

    sensitive.change_password(_PASSWORD, "newpassword456")

    sensitive.lock()
    sensitive.unlock("newpassword456")
    assert sensitive.get_sensitive(first_id)["content"] == "first secret"
    with pytest.raises(RuntimeError, match="integrity check failed"):
        sensitive.get_sensitive(second_id)


def test_change_password_does_not_touch_sensitive_record_timestamps():
    sensitive.setup_password(_PASSWORD, _QUESTIONS)
    sensitive.unlock(_PASSWORD)
    first_id = sensitive.add_sensitive("team", "note", "first secret")
    second_id = sensitive.add_sensitive("team", "note", "second secret")
    conn = db.get_conn()
    before = {
        row["id"]: row["updated_at"]
        for row in conn.execute(
            "SELECT id, updated_at FROM sensitive_memory_items WHERE id IN (?, ?)",
            (first_id, second_id),
        )
    }

    sensitive.change_password(_PASSWORD, "newpassword456")

    after = {
        row["id"]: row["updated_at"]
        for row in conn.execute(
            "SELECT id, updated_at FROM sensitive_memory_items WHERE id IN (?, ?)",
            (first_id, second_id),
        )
    }
    assert after == before


def test_password_change_rejects_a_concurrent_config_update(monkeypatch):
    sensitive.setup_password(_PASSWORD)
    conn = db.get_conn()
    original_encrypt = sensitive._encrypt

    def encrypt_after_competing_update(key, plaintext):
        conn.execute(
            "UPDATE sensitive_config SET updated_at='concurrent-update' WHERE id='singleton'"
        )
        conn.commit()
        return original_encrypt(key, plaintext)

    monkeypatch.setattr(sensitive, "_encrypt", encrypt_after_competing_update)
    with pytest.raises(RuntimeError, match="changed during password update"):
        sensitive.change_password(_PASSWORD, "newpassword456")


def test_recovery_rejects_a_concurrent_config_update(monkeypatch):
    recovery_key = sensitive.setup_password(_PASSWORD)["recovery_key"]
    conn = db.get_conn()
    original_encrypt = sensitive._encrypt

    def encrypt_after_competing_update(key, plaintext):
        conn.execute(
            "UPDATE sensitive_config SET updated_at='concurrent-update' WHERE id='singleton'"
        )
        conn.commit()
        return original_encrypt(key, plaintext)

    monkeypatch.setattr(sensitive, "_encrypt", encrypt_after_competing_update)
    with pytest.raises(RuntimeError, match="changed during password recovery"):
        sensitive.recover_with_key(recovery_key, "recoveredpassword456")


def test_security_question_recovery_is_permanently_disabled():
    sensitive.setup_password(_PASSWORD, _QUESTIONS)

    answers = {"q0": "fluffy", "q1": "beijing", "q2": "wrong"}
    with pytest.raises(RuntimeError, match="disabled"):
        sensitive.recover(answers, "recovered789")


def test_get_security_questions():
    sensitive.setup_password(_PASSWORD, _QUESTIONS)
    assert sensitive.get_security_questions() == []


def test_password_complexity():
    with pytest.raises(ValueError, match="at least 6"):
        sensitive.setup_password("short", _QUESTIONS)


def test_setup_does_not_require_legacy_security_questions():
    assert sensitive.setup_password("longpassword")["recovery_key"]


def test_encrypt_refuses_when_authenticated_crypto_dependency_is_unavailable(monkeypatch):
    original_import = builtins.__import__

    def missing_aead(name, *args, **kwargs):
        if name == "cryptography.hazmat.primitives.ciphers.aead":
            raise ImportError("simulated missing cryptography")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", missing_aead)
    with pytest.raises(RuntimeError, match="authenticated encryption unavailable"):
        sensitive._encrypt(b"k" * 32, b"unit-test-plaintext")


@pytest.mark.parametrize("part", ["ciphertext", "nonce", "tag"])
def test_decrypt_rejects_tampered_authenticated_components_without_disclosure(part):
    key = b"k" * 32
    plaintext = b"unit-test-plaintext"
    ciphertext, nonce, tag = sensitive._encrypt(key, plaintext)
    values = {"ciphertext": ciphertext, "nonce": nonce, "tag": tag}
    original = values[part]
    values[part] = bytes([original[0] ^ 1]) + original[1:]

    with pytest.raises(RuntimeError, match="integrity check failed") as exc_info:
        sensitive._decrypt(key, values["ciphertext"], values["nonce"], values["tag"])

    detail = str(exc_info.value)
    assert plaintext.decode() not in detail
    assert key.hex() not in detail
    assert ciphertext.hex() not in detail


def test_sensitive_search_and_export_fail_closed_on_corrupt_record():
    sensitive.setup_password(_PASSWORD, _QUESTIONS)
    sensitive.unlock(_PASSWORD)
    memory_id = sensitive.add_sensitive("team", "note", "unit-test-secret")
    conn = db.get_conn()
    row = conn.execute(
        "SELECT tag FROM sensitive_memory_items WHERE id = ?", (memory_id,)
    ).fetchone()
    tag = bytes(row["tag"])
    conn.execute(
        "UPDATE sensitive_memory_items SET tag = ? WHERE id = ?",
        (bytes([tag[0] ^ 1]) + tag[1:], memory_id),
    )
    conn.commit()

    with pytest.raises(RuntimeError, match="integrity check failed"):
        sensitive.search_sensitive("unit-test")
    with pytest.raises(RuntimeError, match="integrity check failed"):
        sensitive.export_sensitive_json()


def test_sensitive_export_readme_records_an_iso_timestamp(tmp_path, monkeypatch):
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            assert tz is timezone.utc
            return cls(2026, 7, 12, 13, 10, 35, tzinfo=timezone.utc)

    export_root = tmp_path / "obsidian"
    export_root.mkdir()
    monkeypatch.setattr(sensitive, "is_unlocked", lambda: True)
    monkeypatch.setattr(
        sensitive,
        "export_sensitive_json",
        lambda: [{"memory_id": "SM-1", "content": "encrypted payload"}],
    )
    monkeypatch.setattr(sensitive, "_derived_key", b"session-key")
    monkeypatch.setattr(obsidian_export, "export_root", lambda: export_root)
    monkeypatch.setattr(memory_cli, "datetime", FixedDateTime)

    assert memory_cli._cmd_sensitive_export([]) == 0
    readme = (export_root / "sensitive" / "README.md").read_text(encoding="utf-8")
    assert "导出时间: 2026-07-12T13:10:35+00:00" in readme
    assert "条目数: 1" in readme
