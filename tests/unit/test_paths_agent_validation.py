"""Path-traversal guard: agent names are validated before filesystem paths are built."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from eduflow.agents import claude_code
from eduflow.agents.identity import identity_path
from eduflow.runtime.lifecycle import _ensure_claude_agent_home
from eduflow.runtime.names import InvalidNameError
from eduflow.store.memory import _agent_dir


def test_identity_path_rejects_traversal():
    with pytest.raises(InvalidNameError):
        identity_path("../etc")


def test_memory_agent_dir_rejects_traversal():
    with pytest.raises(InvalidNameError):
        _agent_dir("../etc")


def test_ensure_claude_agent_home_rejects_traversal(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(
            claude_code, "agent_home", lambda _agent: str(Path(tmp) / "safe")
        )
        with pytest.raises(InvalidNameError):
            _ensure_claude_agent_home("../etc")
