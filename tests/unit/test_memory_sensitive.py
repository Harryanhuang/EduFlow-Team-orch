"""Tests for sensitive data encryption and session management."""
from __future__ import annotations

import pytest

from eduflow.memory import db, sensitive


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
