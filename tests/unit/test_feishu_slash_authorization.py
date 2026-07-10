"""Authorization tests for slash commands.

Task 5.3: /send is restricted to configured operators.
"""
from __future__ import annotations

from eduflow.feishu import slash


def test_send_rejected_for_unauthorized_user(monkeypatch):
    monkeypatch.setattr(slash, "_operator_ids", lambda: {"u_admin"})
    result = slash.handle_send(sender_id="u_attacker", argv=["worker_cc", "hello"])
    assert isinstance(result, dict)
    assert result.get("allowed") is False


def test_send_allowed_for_operator(monkeypatch):
    monkeypatch.setattr(slash, "_operator_ids", lambda: {"u_admin"})
    result = slash.handle_send(sender_id="u_admin", argv=["worker_cc", "hello"])
    assert result.get("allowed") is True
