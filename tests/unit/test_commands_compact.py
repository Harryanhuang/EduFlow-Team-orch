"""Tests for `eduflow compact`."""
from __future__ import annotations

from helpers import attr_patch, isolated_env, run_cli, tmux_patch
from eduflow.commands import compact as compact_cmd


_TEAM = {"session": "S", "agents": {"manager": {}, "worker_cc": {}}}


def test_compact_injects_literal_compact_then_identity():
    injected = []

    def fake_inject(target, text, **kw):
        injected.append((str(target), text))
        return True

    with isolated_env(team=_TEAM), tmux_patch(
        has_session=lambda session: True,
        has_window=lambda target: True,
        inject=fake_inject,
        capture_pane=lambda target, lines=20: "",
    ), attr_patch(compact_cmd.time, sleep=lambda seconds: None):
        rc, out, _ = run_cli(["compact", "worker_cc", "--delay", "0"])

    assert rc == 0
    assert injected[0] == ("S:worker_cc", "/compact")
    assert injected[1][0] == "S:worker_cc"
    assert "You are worker_cc" in injected[1][1]
    assert "injected literal /compact" in out
    assert "re-injected identity" in out


def test_compact_no_reidentify_only_injects_compact():
    injected = []

    def fake_inject(target, text, **kw):
        injected.append((str(target), text))
        return True

    with isolated_env(team=_TEAM), tmux_patch(
        has_session=lambda session: True,
        has_window=lambda target: True,
        inject=fake_inject,
        capture_pane=lambda target, lines=20: "",
    ), attr_patch(compact_cmd.time, sleep=lambda seconds: None):
        rc, out, _ = run_cli(["compact", "worker_cc", "--no-reidentify"])

    assert rc == 0
    assert injected == [("S:worker_cc", "/compact")]
    assert "injected literal /compact" in out


def test_compact_rejection_marker_skips_identity():
    injected = []

    def fake_inject(target, text, **kw):
        injected.append((str(target), text))
        return True

    with isolated_env(team=_TEAM), tmux_patch(
        has_session=lambda session: True,
        has_window=lambda target: True,
        inject=fake_inject,
        capture_pane=lambda target, lines=20: "It can't be triggered from inside a response",
    ), attr_patch(compact_cmd.time, sleep=lambda seconds: None):
        rc, _, err = run_cli(["compact", "worker_cc"])

    assert rc == 1
    assert injected == [("S:worker_cc", "/compact")]
    assert "rejected" in err
