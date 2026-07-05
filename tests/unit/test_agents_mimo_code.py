"""Tests for agents/mimo_code.py — MiMoCode adapter shape."""
from __future__ import annotations

import shlex

from eduflow.agents import get_adapter, known_clis
from eduflow.agents.base import OPENAI_COMPAT_AUTH
from eduflow.agents.mimo_code import MimoCodeAdapter


def test_spawn_cmd_uses_mimo_and_model():
    cmd = MimoCodeAdapter().spawn_cmd("manager", "openai/gpt-5.5")
    argv = shlex.split(cmd)
    assert argv[0] == "MIMO_AGENT=manager"
    assert argv[1] == "mimo"
    assert "--trust" in argv
    assert "--never-ask" in argv
    assert "--model" in argv
    assert "openai/gpt-5.5" in argv


def test_ready_markers_include_brand_and_prompt():
    markers = MimoCodeAdapter().ready_markers()
    assert "MiMoCode" in markers
    assert "Xiaomi" in markers
    assert "❯" in markers


def test_process_name_and_auth_slots():
    adapter = MimoCodeAdapter()
    assert adapter.process_name() == "mimo"
    assert adapter.auth_slots() == OPENAI_COMPAT_AUTH


def test_registered_in_known_clis_with_alias():
    assert "mimo-code" in known_clis()
    assert "mimo-cli" in known_clis()
    assert isinstance(get_adapter("mimo-code"), MimoCodeAdapter)
    assert get_adapter("mimo-code") is get_adapter("mimo-cli")
