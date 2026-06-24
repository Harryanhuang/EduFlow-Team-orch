"""Tests for agents/qoder_cli_cn.py — Qoder CLI CN adapter shape."""
from __future__ import annotations

import shlex

from eduflow.agents import get_adapter, known_clis
from eduflow.agents.qoder_cli_cn import QoderCliCnAdapter


def test_spawn_cmd_uses_qoderclicn_and_model():
    cmd = QoderCliCnAdapter().spawn_cmd("auto_ops", "Qwen3.7-Max")
    argv = shlex.split(cmd)
    assert argv[0].endswith("/qoderclicn") or argv[0] == "qoderclicn"
    assert "--dangerously-skip-permissions" in cmd
    assert "--name auto_ops" in cmd
    assert "--model Qwen3.7-Max" in cmd


def test_spawn_cmd_quotes_agent_name():
    cmd = QoderCliCnAdapter().spawn_cmd("auto ops", "Qwen3.7-Max")
    assert "'auto ops'" in cmd or "auto\\ ops" in cmd


def test_ready_markers_include_qoder_prompt():
    markers = QoderCliCnAdapter().ready_markers()
    assert "Qoder CLI CN" in markers
    assert "❯" in markers


def test_busy_markers_cover_thinking_and_spinner():
    busy = QoderCliCnAdapter().busy_markers()
    assert "Thinking" in busy
    assert "⣾" in busy


def test_rate_limit_markers_cover_chinese_and_english():
    markers = QoderCliCnAdapter().rate_limit_markers()
    assert any("rate limit" in m for m in markers)
    assert any("请求过于频繁" in m for m in markers)
    assert "429" in markers


def test_process_name_is_qoderclicn():
    assert QoderCliCnAdapter().process_name() == "qoderclicn"


def test_qoderclicn_and_alias_resolve_to_same_adapter():
    a = get_adapter("qoderclicn")
    b = get_adapter("qoder-cli-cn")
    assert isinstance(a, QoderCliCnAdapter)
    assert isinstance(b, QoderCliCnAdapter)
    assert a is b


def test_registered_in_known_clis():
    names = known_clis()
    assert "qoderclicn" in names
    assert "qoder-cli-cn" in names
