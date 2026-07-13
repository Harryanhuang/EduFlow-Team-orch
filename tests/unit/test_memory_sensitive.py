"""Tests for sensitive data encryption and session management."""
from __future__ import annotations

from datetime import datetime, timezone
import builtins

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


_PASSWORD = "testpass123"
_QUESTIONS = [
    {"question": "What is your pet's name?", "answer": "fluffy"},
    {"question": "What city were you born in?", "answer": "beijing"},
    {"question": "What is your mother's maiden name?", "answer": "smith"},
]


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


def test_change_password_keeps_all_records_on_tampered_later_record():
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

    with pytest.raises(RuntimeError, match="integrity check failed"):
        sensitive.change_password(_PASSWORD, "newpassword456")

    sensitive.lock()
    sensitive.unlock(_PASSWORD)
    assert sensitive.get_sensitive(first_id)["content"] == "first secret"


def test_change_password_rolls_back_on_later_write_failure(monkeypatch):
    sensitive.setup_password(_PASSWORD, _QUESTIONS)
    sensitive.unlock(_PASSWORD)
    first_id = sensitive.add_sensitive("team", "note", "first secret")
    second_id = sensitive.add_sensitive("team", "note", "second secret")
    calls = 0

    def fail_before_second_update():
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("simulated write failure")
        return "2026-01-01T00:00:00+00:00"

    monkeypatch.setattr(sensitive, "_now_iso", fail_before_second_update)
    with pytest.raises(RuntimeError, match="simulated write failure"):
        sensitive.change_password(_PASSWORD, "newpassword456")

    sensitive.lock()
    sensitive.unlock(_PASSWORD)
    assert sensitive.get_sensitive(first_id)["content"] == "first secret"
    assert sensitive.get_sensitive(second_id)["content"] == "second secret"
    sensitive.lock()
    with pytest.raises(ValueError):
        sensitive.unlock("newpassword456")


def test_recover_with_security_questions():
    sensitive.setup_password(_PASSWORD, _QUESTIONS)

    # Correct answers (2 of 3)
    answers = {"q0": "fluffy", "q1": "beijing", "q2": "wrong"}
    new_pw = "recovered789"
    sensitive.recover(answers, new_pw)

    # New password should work
    sensitive.unlock(new_pw)
    assert sensitive.is_unlocked()


def test_recover_with_wrong_answers():
    sensitive.setup_password(_PASSWORD, _QUESTIONS)

    # Only 1 correct answer
    answers = {"q0": "fluffy", "q1": "wrong", "q2": "wrong"}
    with pytest.raises(ValueError, match="Need 2 correct answers"):
        sensitive.recover(answers, "newpw123")


def test_recovery_refuses_to_rekey_existing_encrypted_records_without_migration():
    sensitive.setup_password(_PASSWORD, _QUESTIONS)
    sensitive.unlock(_PASSWORD)
    memory_id = sensitive.add_sensitive("team", "note", "unit-test-secret")
    sensitive.lock()

    with pytest.raises(RuntimeError, match="explicit migration"):
        sensitive.recover({"q0": "fluffy", "q1": "beijing"}, "recovered789")

    sensitive.unlock(_PASSWORD)
    assert sensitive.get_sensitive(memory_id)["content"] == "unit-test-secret"


def test_get_security_questions():
    sensitive.setup_password(_PASSWORD, _QUESTIONS)
    questions = sensitive.get_security_questions()
    assert len(questions) == 3
    assert questions[0] == "What is your pet's name?"


def test_password_complexity():
    with pytest.raises(ValueError, match="at least 6"):
        sensitive.setup_password("short", _QUESTIONS)


def test_questions_count():
    with pytest.raises(ValueError, match="At least 3"):
        sensitive.setup_password("longpassword", [{"question": "q", "answer": "a"}])


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
