"""Tests for `eduflow watchdog` daemon's alert wiring.

Mostly covers `_make_alert_fn` — the rest of the daemon (signal handler,
supervise loop, pidlock acquire) is exercised by the existing
test_runtime_watchdog.py.
"""
from __future__ import annotations

from helpers import attr_patch, isolated_env
from eduflow.commands import watchdog as cmd_watchdog
from eduflow.feishu import chat as feishu_chat
from eduflow.runtime import tmux, paths
import json


def test_make_alert_fn_returns_none_when_chat_id_unset():
    """No chat target → no alert fn → supervise gets None default
    (which it tolerates; cooldowns happen but no chat delivery)."""
    with isolated_env():
        assert cmd_watchdog._make_alert_fn() is None


def test_make_alert_fn_sends_red_card_on_cooldown():
    """Round-98: cooldown alert is a red Feishu card (visually distinct
    from /team /health cards) instead of plain text."""
    cards_sent = []

    def fake_send_card(chat_id, card, **kw):
        cards_sent.append({"chat_id": chat_id, "card": card, **kw})
        return {"message_id": "om_alert"}

    with isolated_env(team={"agents": {"manager": {}}},
                      runtime_config={"chat_id": "oc_x",
                                       "lark_profile": "p"}), \
            attr_patch(feishu_chat, send_card=fake_send_card):
        alert = cmd_watchdog._make_alert_fn()
        assert alert is not None
        alert("router", 3, 600)

    assert len(cards_sent) == 1
    sent = cards_sent[0]
    assert sent["chat_id"] == "oc_x"
    assert sent["profile"] == "p"
    assert sent["as_user"] is False
    card = sent["card"]
    assert card["header"]["template"] == "red"
    title = card["header"]["title"]["content"]
    assert "router" in title and "cooldown" in title
    body = card["body"]["elements"][0]["content"]
    assert "router" in body
    assert "600s" in body
    assert "3" in body
    assert "eduflow health" in body


def test_make_alert_fn_falls_back_to_text_when_card_send_fails():
    """A broken card path mustn't lose the alert — fall back to send_text
    so the operator at least sees something in chat."""
    text_sent = []

    def card_boom(chat_id, card, **kw):
        raise RuntimeError("card schema rejected by Feishu")

    def fake_send_text(chat_id, text, **kw):
        text_sent.append({"chat_id": chat_id, "text": text, **kw})
        return {"message_id": "om_fallback"}

    with isolated_env(team={"agents": {"manager": {}}},
                      runtime_config={"chat_id": "oc_x"}), \
            attr_patch(feishu_chat, send_card=card_boom,
                       send_text=fake_send_text):
        alert = cmd_watchdog._make_alert_fn()
        alert("router", 5, 300)

    assert len(text_sent) == 1
    assert "router" in text_sent[0]["text"]
    assert "300s" in text_sent[0]["text"]


def test_make_alert_fn_uses_lark_profile_from_runtime_config():
    """Profile must thread through send_card so the right bot identity
    sends the alert (not whichever profile happens to be the default)."""
    captured = []

    def fake_send_card(chat_id, card, **kw):
        captured.append(kw.get("profile"))
        return {"message_id": "om_x"}

    with isolated_env(team={"agents": {"manager": {}}},
                      runtime_config={"chat_id": "oc_x",
                                       "lark_profile": "team_alpha"}), \
            attr_patch(feishu_chat, send_card=fake_send_card):
        alert = cmd_watchdog._make_alert_fn()
        alert("router", 1, 60)

    assert captured == ["team_alpha"]


def test_detect_runtime_failure_reason_prefers_rate_limit():
    class _Adapter:
        def ready_markers(self):
            return ["bypass permissions on"]

        def rate_limit_markers(self):
            return ["Approaching usage limit"]

    target = tmux.Target("S", "worker")
    with attr_patch(cmd_watchdog.tmux, capture_pane=lambda *a, **kw: "Approaching usage limit\n"), \
            attr_patch(cmd_watchdog.wake, is_rate_limited=lambda *a, **kw: True):
        reason = cmd_watchdog._detect_runtime_failure_reason(target, _Adapter())
    assert reason == "rate_limit"


def test_detect_runtime_failure_ignores_stale_marker_before_ready_prompt():
    class _Adapter:
        def ready_markers(self):
            return ["bypass permissions on"]

        def rate_limit_markers(self):
            return []

    target = tmux.Target("S", "worker")
    stale = (
        "Invalid auth credentials\n"
        "provider unavailable\n"
        "────────────────\n"
        "❯\n"
        "  ⏵⏵ bypass permissions on (shift+tab to cycle) · gh auth login\n"
    )
    with attr_patch(cmd_watchdog.tmux, capture_pane=lambda *a, **kw: stale), \
            attr_patch(cmd_watchdog.wake, is_rate_limited=lambda *a, **kw: False):
        reason = cmd_watchdog._detect_runtime_failure_reason(target, _Adapter())
    assert reason == ""


def test_detect_runtime_failure_ignores_stale_rate_limit_before_ready_prompt():
    class _Adapter:
        def ready_markers(self):
            return ["bypass permissions on"]

        def rate_limit_markers(self):
            return ["Approaching usage limit"]

    target = tmux.Target("S", "worker")
    stale = (
        "Approaching usage limit\n"
        "────────────────\n"
        "❯\n"
        "  ⏵⏵ bypass permissions on (shift+tab to cycle) · gh auth login\n"
    )
    with attr_patch(cmd_watchdog.tmux, capture_pane=lambda *a, **kw: stale):
        reason = cmd_watchdog._detect_runtime_failure_reason(target, _Adapter())
    assert reason == ""


def test_detect_runtime_failure_flags_repetitive_tool_calls_after_ready_prompt():
    class _Adapter:
        def ready_markers(self):
            return ["bypass permissions on"]

        def rate_limit_markers(self):
            return []

    target = tmux.Target("S", "manager")
    text = (
        "❯\n"
        "  ⏵⏵ bypass permissions on (shift+tab to cycle)\n"
        "API Error: 400 <400> InternalError.Algo.InvalidParameter: "
        "Repetitive tool calls detected in the conversation history.\n"
    )
    with attr_patch(cmd_watchdog.tmux, capture_pane=lambda *a, **kw: text), \
            attr_patch(cmd_watchdog.wake, is_rate_limited=lambda *a, **kw: False):
        reason = cmd_watchdog._detect_runtime_failure_reason(target, _Adapter())
    assert reason == "conversation_history_corrupt"


def test_guard_agent_runtimes_switches_fallback_when_marker_detected():
    team = {"session": "S", "agents": {"worker_a": {"runtime": "primary"}}}
    switches = []

    class _Adapter:
        def ready_markers(self):
            return ["ready"]

        def rate_limit_markers(self):
            return []

    def fake_execute(agent, target, current_runtime, reason, **kw):
        switches.append((agent, str(target), current_runtime, reason, kw.get("trigger")))
        return {
            "outcome": "ready",
            "to_runtime": "backup",
            "best_outcome": "ready",
            "attempts": [{"to_runtime": "backup", "outcome": "ready",
                          "env_ok": True, "smoke_ok": True, "pool_id": "", "ts": 100.0}],
            "events": [],
            "exhausted": False,
            "pool_switched": True,
        }

    with isolated_env(team=team) as tmp:
        (tmp / "eduflow.toml").write_text("""
[team]
session = "S"

[team.agents.worker_a]
runtime = "primary"
role = "worker"

[runtime_registry.primary]
cli = "claude-code"
model = "sonnet"
fallback_to = "backup"
switch_on = ["auth_failure"]

[runtime_registry.backup]
cli = "codex-cli"
model = "gpt-5.5"
switch_on = ["auth_failure"]
""", encoding="utf-8")
        from eduflow.runtime import failover as failover_mod
        with attr_patch(cmd_watchdog.tmux,
                        has_session=lambda s: True,
                        has_window=lambda t: True,
                        capture_pane=lambda t, lines=120: "Invalid auth credentials\n"), \
                attr_patch(cmd_watchdog, get_adapter=lambda cli: _Adapter()), \
                attr_patch(cmd_watchdog.lifecycle,
                           current_runtime_status=lambda agent: {"runtime": "primary"}), \
                attr_patch(failover_mod, execute_fallback_loop=fake_execute), \
                attr_patch(cmd_watchdog.wake, is_rate_limited=lambda *a, **kw: False):
            cmd_watchdog._guard_agent_runtimes()
    assert len(switches) == 1
    agent, target_str, current, reason, trigger = switches[0]
    assert agent == "worker_a"
    assert current == "primary"
    assert reason == "auth_failure"
    assert trigger == "watchdog"


def test_notify_runtime_switch_sends_text_when_enabled():
    sent = []

    def fake_send_text(chat_id, text, **kw):
        sent.append((chat_id, text, kw))
        return {"message_id": "om_1"}

    with isolated_env(runtime_config={"chat_id": "oc_x", "lark_profile": "p"}) as tmp:
        (tmp / "eduflow.toml").write_text("""
[runtime_guard.notify]
default = "manager"
""", encoding="utf-8")
        with attr_patch(feishu_chat, send_text=fake_send_text):
            cmd_watchdog._notify_runtime_switch("worker_a", "primary", "backup", "auth_failure")
    assert len(sent) == 1
    assert sent[0][0] == "oc_x"
    assert "worker_a" in sent[0][1]
    assert "primary -> backup" in sent[0][1]


def test_auto_ops_presence_posts_half_hour_brief_when_due():
    sent = []

    def fake_send_card(chat_id, card, **kw):
        sent.append({"chat_id": chat_id, "card": card, **kw})
        return {"message_id": "om_presence"}

    with isolated_env(runtime_config={"chat_id": "oc_x", "lark_profile": "p"}) as tmp:
        (tmp / "eduflow.toml").write_text("""
[auto_ops]
presence_enabled = true
presence_interval_s = 1800
""", encoding="utf-8")
        from eduflow.store import local_facts
        local_facts.upsert_status("manager", "待命", "ready")
        local_facts.upsert_status("worker_course", "进行中", "Physics topic outline")
        with attr_patch(feishu_chat, send_card=fake_send_card):
            assert cmd_watchdog._maybe_emit_auto_ops_presence(2000.0) is True
    assert len(sent) == 1
    assert sent[0]["chat_id"] == "oc_x"
    assert sent[0]["profile"] == "p"
    body = sent[0]["card"]["body"]["elements"][0]["content"]
    assert "运行态简报" in body
    assert "worker_course" in body


def test_auto_ops_presence_is_throttled_by_interval():
    sent = []

    def fake_send_card(chat_id, card, **kw):
        sent.append({"chat_id": chat_id, "card": card, **kw})
        return {"message_id": "om_presence"}

    with isolated_env(runtime_config={"chat_id": "oc_x"}) as tmp:
        (tmp / "eduflow.toml").write_text("""
[auto_ops]
presence_enabled = true
presence_interval_s = 1800
""", encoding="utf-8")
        with attr_patch(feishu_chat, send_card=fake_send_card):
            assert cmd_watchdog._maybe_emit_auto_ops_presence(2000.0) is True
            assert cmd_watchdog._maybe_emit_auto_ops_presence(2100.0) is False
    assert len(sent) == 1


def test_record_switch_enters_cooldown_after_threshold():
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text("""
[runtime_guard.cooldown]
max_switches = 2
window_s = 600
cooldown_s = 900
""", encoding="utf-8")
        hit, _ = cmd_watchdog._record_switch_and_check_cooldown("worker_a", 1000.0)
        assert hit is False
        hit, _ = cmd_watchdog._record_switch_and_check_cooldown("worker_a", 1100.0)
        assert hit is True
        data = json.loads(paths.runtime_guard_state_file().read_text(encoding="utf-8"))
        row = data["agents"]["worker_a"]
        assert row["needs_manager_action"] is True
        assert row["cooldown_until"] == 2000.0


def test_record_switch_carries_manager_policy_into_guard_state():
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text("""
[runtime_guard.manager_policy]
default = "pause"

[runtime_guard.cooldown]
max_switches = 1
window_s = 600
cooldown_s = 900
""", encoding="utf-8")
        hit, _ = cmd_watchdog._record_switch_and_check_cooldown("worker_a", 1000.0)
        assert hit is True
        data = json.loads(paths.runtime_guard_state_file().read_text(encoding="utf-8"))
        assert data["agents"]["worker_a"]["manager_policy"] == "pause"


def test_guard_agent_runtimes_marks_escalation_when_fallback_missing():
    team = {"session": "S", "agents": {"worker_a": {"runtime": "primary"}}}

    class _Adapter:
        def ready_markers(self):
            return ["ready"]

        def rate_limit_markers(self):
            return []

    with isolated_env(team=team) as tmp:
        (tmp / "eduflow.toml").write_text("""
[team]
session = "S"

[team.agents.worker_a]
runtime = "primary"
role = "worker"

[runtime_registry.primary]
cli = "claude-code"
model = "sonnet"
switch_on = ["auth_failure"]
""", encoding="utf-8")
        with attr_patch(cmd_watchdog.tmux,
                        has_session=lambda s: True,
                        has_window=lambda t: True,
                        capture_pane=lambda t, lines=120: "Invalid auth credentials\n"), \
                attr_patch(cmd_watchdog, get_adapter=lambda cli: _Adapter()), \
                attr_patch(cmd_watchdog.lifecycle,
                           current_runtime_status=lambda agent: {"runtime": "primary"}), \
                attr_patch(cmd_watchdog.wake, is_rate_limited=lambda *a, **kw: False):
            cmd_watchdog._guard_agent_runtimes()
        data = json.loads(paths.runtime_guard_state_file().read_text(encoding="utf-8"))
        row = data["agents"]["worker_a"]
        assert row["escalation_needed"] is True
        assert row["escalation_reason"] == "fallback_chain_exhausted"
        assert row["last_switch_outcome"] == "fallback_exhausted"


def test_guard_agent_runtimes_marks_auto_switched_recovered_on_success():
    team = {"session": "S", "agents": {"worker_a": {"runtime": "primary"}}}

    class _Adapter:
        def ready_markers(self):
            return ["ready"]

        def rate_limit_markers(self):
            return []

    with isolated_env(team=team) as tmp:
        (tmp / "eduflow.toml").write_text("""
[team]
session = "S"

[team.agents.worker_a]
runtime = "primary"
role = "worker"

[runtime_registry.primary]
cli = "claude-code"
model = "sonnet"
fallback_to = "backup"
switch_on = ["auth_failure"]

[runtime_registry.backup]
cli = "codex-cli"
model = "gpt-5.5"
switch_on = ["auth_failure"]
""", encoding="utf-8")
        with attr_patch(cmd_watchdog.tmux,
                        has_session=lambda s: True,
                        has_window=lambda t: True,
                        capture_pane=lambda t, lines=120: "Invalid auth credentials\n"), \
                attr_patch(cmd_watchdog, get_adapter=lambda cli: _Adapter()), \
                attr_patch(cmd_watchdog.lifecycle,
                           current_runtime_status=lambda agent: {"runtime": "primary"}), \
                attr_patch(cmd_watchdog.wake, is_rate_limited=lambda *a, **kw: False):
            cmd_watchdog._guard_agent_runtimes()
        data = json.loads(paths.runtime_guard_state_file().read_text(encoding="utf-8"))
        row = data["agents"]["worker_a"]
        assert row["escalation_needed"] is True
        assert row["escalation_reason"] == "fallback_chain_exhausted"
        assert row["last_switch_outcome"] == "fallback_exhausted"


def test_guard_agent_runtimes_marks_auto_switched_recovered_on_success():
    team = {"session": "S", "agents": {"worker_a": {"runtime": "primary"}}}

    class _Adapter:
        def ready_markers(self):
            return ["ready"]

        def rate_limit_markers(self):
            return []

    def fake_execute(agent, target, current_runtime, reason, **kw):
        return {
            "outcome": "ready",
            "to_runtime": "backup",
            "best_outcome": "ready",
            "attempts": [{"to_runtime": "backup", "outcome": "ready",
                          "env_ok": True, "smoke_ok": True, "pool_id": "", "ts": 100.0}],
            "events": [],
            "exhausted": False,
            "pool_switched": True,
        }

    with isolated_env(team=team) as tmp:
        (tmp / "eduflow.toml").write_text("""
[team]
session = "S"

[team.agents.worker_a]
runtime = "primary"
role = "worker"

[runtime_registry.primary]
cli = "claude-code"
model = "sonnet"
fallback_to = "backup"
switch_on = ["auth_failure"]

[runtime_registry.backup]
cli = "codex-cli"
model = "gpt-5.5"
switch_on = ["auth_failure"]
""", encoding="utf-8")
        from eduflow.runtime import failover as failover_mod
        with attr_patch(cmd_watchdog.tmux,
                        has_session=lambda s: True,
                        has_window=lambda t: True,
                        capture_pane=lambda t, lines=120: "Invalid auth credentials\n"), \
                attr_patch(cmd_watchdog, get_adapter=lambda cli: _Adapter()), \
                attr_patch(cmd_watchdog.lifecycle,
                           current_runtime_status=lambda agent: {"runtime": "primary"}), \
                attr_patch(failover_mod, execute_fallback_loop=fake_execute), \
                attr_patch(cmd_watchdog.wake, is_rate_limited=lambda *a, **kw: False):
            cmd_watchdog._guard_agent_runtimes()
        data = json.loads(paths.runtime_guard_state_file().read_text(encoding="utf-8"))
        row = data["agents"]["worker_a"]
        assert row["last_switch_outcome"] == "ready"
        assert row["from_runtime"] == "primary"
        assert row["to_runtime"] == "backup"
        assert row["escalation_needed"] is False
