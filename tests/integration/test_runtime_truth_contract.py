"""Cross-module contracts for runtime readiness evidence."""
from __future__ import annotations

import time

from helpers import isolated_env
from eduflow.commands import runtime_verify
from eduflow.runtime import paths, tmux, verify
from eduflow.store import local_facts
from eduflow.util import write_json


def test_proved_ready_requires_the_current_inbox_to_be_consumed(monkeypatch):
    with isolated_env():
        write_json(paths.runtime_status_file(), {
            "agents": {
                "worker_a": {
                    "runtime": "primary",
                    "cli": "claude-code",
                    "env_profile": "",
                    "env_ok": True,
                    "smoke_ok": True,
                    "verified_at": time.time(),
                }
            }
        })
        monkeypatch.setattr(runtime_verify.config, "load_team", lambda: {"session": "S"})
        monkeypatch.setattr(tmux, "has_session", lambda _session: True)
        monkeypatch.setattr(tmux, "has_window", lambda _target: True)
        monkeypatch.setattr(
            tmux,
            "list_panes",
            lambda _target: [tmux.PaneInfo("0", True, "claude", "claude --model test")],
        )
        monkeypatch.setattr(tmux, "capture_pane", lambda *_args, **_kwargs: "bypass permissions on")
        monkeypatch.setattr(verify, "verify_live_env_matches_profile", lambda *_args: (True, []))
        monkeypatch.setattr(runtime_verify, "_pane_failure_scan", lambda *_args: (True, []))

        message_id = local_facts.append_message(
            "worker_a", "manager", "runtime readiness probe", priority="高"
        )
        pending = runtime_verify.compute_verdict("worker_a")
        assert pending["verdict"] == "inbox_not_consumed"
        assert pending["inbox_state"] == "not_consumed"

        assert local_facts.mark_read(message_id) is True
        assert local_facts.record_message_ack(message_id, "accepted_task") is True
        consumed = runtime_verify.compute_verdict("worker_a")
        assert consumed["verdict"] == "proved_ready"
        assert consumed["inbox_state"] == "no_pending"
