"""Tests for name validation enforced before adapter spawn commands.

Task 3.2: agent/model names must be validated before any pane spawn
side-effect so malformed names can never reach adapter.spawn_cmd().
"""
from __future__ import annotations

import pytest

from eduflow.runtime import lifecycle, tmux
from eduflow.runtime.names import InvalidNameError
from helpers import isolated_env, tmux_patch


def test_spawn_rejects_bad_agent_name():
    """A semicolon in the agent name must be rejected before tmux.spawn_agent
    is invoked."""
    team = {"agents": {"bad;agent": {"cli": "claude-code", "model": "opus"}}}
    spawn_calls = []
    with isolated_env(team=team), tmux_patch(
            spawn_agent=lambda target, cmd: spawn_calls.append((str(target), cmd)) or True):
        with pytest.raises(InvalidNameError):
            lifecycle.provision_pane("bad;agent", tmux.Target("S", "bad;agent"))
    assert not spawn_calls


def test_spawn_rejects_bad_model_name():
    """A slash in the model name must be rejected before tmux.spawn_agent
    is invoked."""
    team = {"agents": {"alice": {"cli": "claude-code", "model": "evil/model"}}}
    spawn_calls = []
    with isolated_env(team=team), tmux_patch(
            spawn_agent=lambda target, cmd: spawn_calls.append((str(target), cmd)) or True):
        with pytest.raises(InvalidNameError):
            lifecycle.provision_pane("alice", tmux.Target("S", "alice"))
    assert not spawn_calls
