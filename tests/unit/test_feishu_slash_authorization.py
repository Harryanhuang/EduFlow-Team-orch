"""Contract tests for the G0.1 Slash RBAC boundary."""
from __future__ import annotations

from eduflow.feishu import slash
from eduflow.commands import health
from eduflow.security import authorization


def _team(*, operators=(), admins=()) -> dict:
    return {"operators": list(operators), "admins": list(admins)}


def test_member_can_execute_registered_read_only_command() -> None:
    decision = authorization.authorize_slash(
        "/help", sender_id="u_member", team=_team()
    )

    assert decision.allowed is True
    assert decision.required_role == authorization.READ_ONLY
    assert authorization.MEMBER_READ_COMMANDS == {"/help"}


def test_missing_sender_id_rejects_every_write_role() -> None:
    for command in authorization.WRITE_COMMANDS:
        decision = authorization.authorize_slash(
            command, sender_id="", team=_team(operators=("u_operator",), admins=("u_admin",))
        )
        assert decision.allowed is False, command
        assert decision.reason == "missing_sender_id", command


def test_operator_can_send_but_cannot_run_admin_command() -> None:
    team = _team(operators=("u_operator",), admins=("u_admin",))

    assert authorization.authorize_slash(
        "/send", sender_id="u_operator", team=team
    ).allowed
    denied = authorization.authorize_slash(
        "/clear", sender_id="u_operator", team=team
    )
    assert denied.allowed is False
    assert denied.reason == "admin_required"


def test_operational_read_view_is_not_in_member_allowlist() -> None:
    member = authorization.authorize_slash(
        "/tmux", sender_id="u_member", team=_team(operators=("u_operator",))
    )
    operator = authorization.authorize_slash(
        "/tmux", sender_id="u_operator", team=_team(operators=("u_operator",))
    )

    assert member.allowed is False
    assert member.reason == "operator_required"
    assert operator.allowed is True
    assert "/tmux" not in authorization.WRITE_COMMANDS


def test_team_pane_summary_requires_operator() -> None:
    member = authorization.authorize_slash(
        "/team", sender_id="u_member", team=_team(operators=("u_operator",))
    )
    operator = authorization.authorize_slash(
        "/team", sender_id="u_operator", team=_team(operators=("u_operator",))
    )

    assert member.allowed is False
    assert member.reason == "operator_required"
    assert operator.allowed is True


def test_admin_can_execute_operator_and_admin_commands() -> None:
    team = _team(admins=("u_admin",))

    assert authorization.authorize_slash(
        "/send", sender_id="u_admin", team=team
    ).allowed
    assert authorization.authorize_slash(
        "/clear", sender_id="u_admin", team=team
    ).allowed


def test_empty_or_malformed_allowlists_fail_closed() -> None:
    for team in (
        {},
        _team(),
        {"operators": "u_operator", "admins": []},
        {"operators": ["placeholder"], "admins": []},
        {"operators": [], "admins": {"actor": "u_admin"}},
    ):
        for command in authorization.WRITE_COMMANDS:
            assert not authorization.authorize_slash(
                command, sender_id="u_operator", team=team
            ).allowed, (command, team)


def test_every_slash_handler_has_an_explicit_policy() -> None:
    assert set(slash._HANDLERS) == set(authorization.COMMAND_POLICIES)
    assert authorization.WRITE_COMMANDS == {
        command
        for command, policy in authorization.COMMAND_POLICIES.items()
        if policy.mutating
    }
    assert authorization.MEMBER_READ_COMMANDS == {
        command
        for command, policy in authorization.COMMAND_POLICIES.items()
        if policy.required_role == authorization.READ_ONLY
    }


def test_send_probe_uses_fail_closed_authorization(monkeypatch) -> None:
    monkeypatch.setattr(slash, "_authorization_team", lambda: _team())

    result = slash.handle_send(sender_id="u_attacker", argv=["worker_cc", "hello"])

    assert result["allowed"] is False


def test_send_probe_allows_configured_operator(monkeypatch) -> None:
    monkeypatch.setattr(
        slash,
        "_authorization_team",
        lambda: _team(operators=("u_operator",)),
    )

    result = slash.handle_send(
        sender_id="u_operator", argv=["worker_cc", "hello"]
    )

    assert result["allowed"] is True


def test_health_warns_when_slash_roles_are_unprovisioned(monkeypatch) -> None:
    monkeypatch.setattr(
        health.tunables,
        "load",
        lambda: {"team": {"operators": ["u_<admin_feishu_id>"]}},
    )
    report = health.HealthReport()

    health._check_slash_authority(report)

    assert report.warn == 1
    assert "Slash writes fail closed" in report.lines[0]


def test_health_reports_partially_enabled_slash_roles_truthfully(monkeypatch) -> None:
    monkeypatch.setattr(
        health.tunables,
        "load",
        lambda: {"team": {"operators": ["u_operator"], "admins": []}},
    )
    report = health.HealthReport()

    health._check_slash_authority(report)

    assert report.warn == 1
    assert "/send enabled" in report.lines[0]
    assert "admin writes fail closed" in report.lines[0]
