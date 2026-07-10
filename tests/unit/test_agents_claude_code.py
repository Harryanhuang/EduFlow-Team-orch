"""Tests for agents/claude_code.py — Claude Code adapter shape."""
from __future__ import annotations

import shlex

from eduflow.agents.claude_code import ClaudeCodeAdapter


def test_spawn_cmd_quotes_model_and_agent():
    adapter = ClaudeCodeAdapter()
    cmd = adapter.spawn_cmd(agent="a; echo pwned", model="claude-sonnet-5; echo pwned")
    assert shlex.quote("a; echo pwned") in cmd
    assert shlex.quote("claude-sonnet-5; echo pwned") in cmd
