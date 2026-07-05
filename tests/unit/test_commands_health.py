"""Tests for `eduflow health`."""
from __future__ import annotations

import json
import os
import shutil
import time

from helpers import attr_patch, env_patch, isolated_env, run_cli, tmux_patch
from eduflow.runtime import paths
from eduflow.runtime import tmux as tmux_mod
from eduflow.util import write_json


def _stub_tmux(*, session_alive: bool, panes_with_cli: list[str] = (),
               panes_without_cli: list[str] = (),
               pane_text: dict[str, str] | None = None):
    """Replace tmux.has_session/has_window/capture_pane for health probing."""
    all_panes = list(panes_with_cli) + list(panes_without_cli)
    pane_text = pane_text or {}

    def capture_pane(target, lines=80):
        if target.window in pane_text:
            return pane_text[target.window]
        if target.window in panes_with_cli:
            return "bypass permissions on\n? for shortcuts\n>"
        return "$ "

    return tmux_patch(
        has_session=lambda s: session_alive,
        has_window=lambda target: target.window in all_panes,
        capture_pane=capture_pane,
    )


# ── happy path ──────────────────────────────────────────────────


def test_health_all_green_returns_zero():
    """No reds AND no warnings → green footer."""
    team = {"session": "S", "agents": {"manager": {"cli": "claude-code"}}}
    rc_cfg = {"chat_id": "oc_x", "lark_profile": "prod"}
    with isolated_env(team=team, runtime_config=rc_cfg), _stub_tmux(
            session_alive=True, panes_with_cli=["manager"]), \
            env_patch(HTTPS_PROXY=None, HTTP_PROXY=None):
        rc, out, _ = run_cli(["health"])
        assert rc == 0
        assert "team config" in out
        assert "chat_id: oc_x" in out
        assert "lark_profile: prod" in out
        assert "tmux session: S" in out
        assert "manager: pane ready" in out
        # Daemons / cursor lines are ⚠️ / ℹ️ in this isolated test rig
        # (no pid files); footer should report warnings, not "all green"
        assert "no errors" in out
        assert "warning" in out


# ── red checks ──────────────────────────────────────────────────


def test_health_returns_one_when_session_down():
    team = {"session": "S", "agents": {"manager": {}}}
    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), _stub_tmux(
            session_alive=False):
        rc, out, _ = run_cli(["health"])
        assert rc == 1
        assert "tmux session S not running" in out


def test_health_returns_one_when_chat_id_blank():
    team = {"session": "S", "agents": {"manager": {}}}
    with isolated_env(team=team, runtime_config={"chat_id": ""}), _stub_tmux(
            session_alive=True, panes_with_cli=["manager"]):
        rc, out, _ = run_cli(["health"])
        assert rc == 1
        assert "chat_id is empty" in out


def test_health_returns_one_when_team_config_missing():
    """No eduflow.toml AND no team.json → can't deploy. Health
    surfaces this as a red so the operator sees it before running up."""
    with isolated_env(runtime_config={"chat_id": "oc_x"}), _stub_tmux(
            session_alive=True):
        # don't call isolated_env(team=...) so neither config file exists
        rc, out, _ = run_cli(["health"])
        assert rc == 1
        assert "team config missing" in out


def test_health_returns_one_when_pane_window_missing():
    team = {"session": "S", "agents": {"manager": {}, "missing_w": {}}}
    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), _stub_tmux(
            session_alive=True, panes_with_cli=["manager"]):
        rc, out, _ = run_cli(["health"])
        assert rc == 1
        assert "missing_w: no tmux window" in out


# ── warnings (non-fatal) ────────────────────────────────────────


def test_health_warns_when_pane_up_but_no_cli_marker():
    team = {"session": "S", "agents": {"manager": {}}}
    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), _stub_tmux(
            session_alive=True, panes_with_cli=[], panes_without_cli=["manager"]):
        rc, out, _ = run_cli(["health"])
        assert rc == 0  # warning only
        assert "CLI not ready yet" in out


def test_health_lazy_pane_without_marker_is_green():
    """A pane marked lazy in team.json is expected to have no ready marker
    until first message. Don't yellow-flag the operator over expected state."""
    team = {"session": "S", "agents": {"sleeper": {"cli": "claude-code", "lazy": True}}}
    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), _stub_tmux(
            session_alive=True, panes_with_cli=[], panes_without_cli=["sleeper"]):
        rc, out, _ = run_cli(["health"])
        assert rc == 0
        assert "lazy pane" in out
        assert "CLI not ready yet" not in out


def test_health_daemon_stability_reports_each_flapping_daemon_log():
    """Stability output should not be router-only when other daemon logs flap."""
    team = {"session": "S", "agents": {"manager": {"cli": "claude-code"}}}
    rc_cfg = {"chat_id": "oc_x", "lark_profile": "prod"}
    with isolated_env(team=team, runtime_config=rc_cfg), _stub_tmux(
            session_alive=True, panes_with_cli=["manager"]), \
            env_patch(HTTPS_PROXY=None, HTTP_PROXY=None):
        paths.ensure_state_dir()
        paths.router_log_file().write_text("ok\n", encoding="utf-8")
        paths.task_publish_log_file().write_text(
            "\n".join("respawn task-publish" for _ in range(4)),
            encoding="utf-8",
        )
        paths.watchdog_log_file().write_text(
            "\n".join("respawn watchdog" for _ in range(3)),
            encoding="utf-8",
        )

        rc, out, _ = run_cli(["health"])

        assert rc == 0
        assert "task-publish stability" in out
        assert "watchdog stability" in out
        assert "possible flapping" in out


def test_health_daemon_stability_ignores_old_log_activity():
    team = {"session": "S", "agents": {"manager": {"cli": "claude-code"}}}
    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), _stub_tmux(
            session_alive=True, panes_with_cli=["manager"]), \
            env_patch(HTTPS_PROXY=None, HTTP_PROXY=None):
        paths.ensure_state_dir()
        paths.watchdog_log_file().write_text(
            "\n".join("respawn watchdog" for _ in range(20)),
            encoding="utf-8",
        )
        old = time.time() - 3 * 3600
        os.utime(paths.watchdog_log_file(), (old, old))
        rc, out, _ = run_cli(["health"])

    assert rc == 0
    assert "watchdog stability: no recent daemon log activity" in out
    assert "watchdog stability: 20 respawns" not in out


def test_health_watchdog_stability_ignores_router_respawn_lines():
    team = {"session": "S", "agents": {"manager": {"cli": "claude-code"}}}
    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), _stub_tmux(
            session_alive=True, panes_with_cli=["manager"]), \
            env_patch(HTTPS_PROXY=None, HTTP_PROXY=None):
        paths.ensure_state_dir()
        paths.watchdog_log_file().write_text(
            "\n".join("🔁 router respawned (fail_count was 0)" for _ in range(20)),
            encoding="utf-8",
        )
        rc, out, _ = run_cli(["health"])

    assert rc == 0
    assert "watchdog stability: no respawns in recent log" in out
    assert "watchdog stability: 20 respawns" not in out


def test_health_stall_reason_is_info_when_router_recovered():
    team = {"session": "S", "agents": {"manager": {"cli": "claude-code"}}}
    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), _stub_tmux(
            session_alive=True, panes_with_cli=["manager"]), \
            env_patch(HTTPS_PROXY=None, HTTP_PROXY=None):
        paths.ensure_state_dir()
        paths.router_pid_file().write_text("12345", encoding="utf-8")
        paths.router_stall_reason_file().write_text(json.dumps({
            "reason": "subscribe_idle",
            "detail": "idle=1801s threshold=1800s",
            "ts": time.time(),
        }), encoding="utf-8")
        from eduflow.commands import health as health_cmd
        with attr_patch(health_cmd.pidlock, pid_alive=lambda pid: pid == 12345):
            rc, out, _ = run_cli(["health"])

    assert rc == 0
    assert "router stall reason: last recovered subscribe_idle" in out
    assert "⚠️ router stall reason: subscribe_idle" not in out


def test_health_skips_env_drift_for_clean_lazy_pane():
    team_toml = """
chat_id = "oc_demo"

[runtime_registry.ops_primary]
cli = "claude-code"
model = "sonnet"
provider = "anthropic-proxy"
env_profile = "proxy"

[env_profiles.proxy]
ANTHROPIC_BASE_URL = "https://proxy.example/anthropic"
ANTHROPIC_MODEL = "model-x"

[team]
session = "S"

[team.agents.anna]
runtime = "ops_primary"
lazy = true
"""
    with isolated_env() as tmp, env_patch(HTTPS_PROXY=None, HTTP_PROXY=None):
        (tmp / "eduflow.toml").write_text(team_toml, encoding="utf-8")
        write_json(paths.runtime_status_file(), {
            "agents": {
                "anna": {
                    "runtime": "ops_primary",
                    "cli": "claude-code",
                    "model": "sonnet",
                    "provider": "anthropic-proxy",
                    "env_profile": "proxy",
                }
            }
        })
        with _stub_tmux(session_alive=True, panes_without_cli=["anna"]):
            rc, out, _ = run_cli(["health"])
    assert rc == 0
    assert "anna: lazy pane" in out
    assert "runtime_status_env_drift: anna" not in out


def test_health_warns_when_lazy_pane_contains_stale_cli_output():
    team = {"session": "S", "agents": {"sleeper": {"cli": "claude-code", "lazy": True}}}
    stale = "old work\n■ stream disconnected before completion: error sending request\n›"
    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), _stub_tmux(
            session_alive=True, panes_without_cli=["sleeper"],
            pane_text={"sleeper": stale}):
        rc, out, _ = run_cli(["health"])
        assert rc == 0
        assert "sleeper: stale lazy pane" in out
        assert "lazy pane (CLI starts on first message)" not in out


def test_health_probes_switched_runtime_adapter_ready_marker():
    team_toml = """
chat_id = "oc_demo"

[runtime_registry.ops_primary]
cli = "claude-code"
model = "sonnet"
fallback_to = "ops_backup_qoder_qwen_max"

[runtime_registry.ops_backup_qoder_qwen_max]
cli = "qoderclicn"
model = "Qwen3.7-Max"
provider = "qoder"

[team]
session = "EduFlowTeam"

[team.agents.auto_ops]
runtime = "ops_primary"
lazy = false
"""
    with isolated_env() as tmp, env_patch(HTTPS_PROXY=None, HTTP_PROXY=None):
        (tmp / "eduflow.toml").write_text(team_toml, encoding="utf-8")
        write_json(paths.runtime_status_file(), {
            "agents": {
                "auto_ops": {
                    "runtime": "ops_backup_qoder_qwen_max",
                    "cli": "qoderclicn",
                    "model": "Qwen3.7-Max",
                    "provider": "qoder",
                }
            }
        })
        with tmux_patch(
            has_session=lambda s: True,
            has_window=lambda target: target.window == "auto_ops",
            capture_pane=lambda target, lines=80: "Qoder CLI CN\nQwen3.7-Max Model\n",
        ), _stub_which({"qoderclicn"}):
            rc, out, _ = run_cli(["health"])
    assert rc == 0
    assert "qoderclicn:" in out
    assert "auto_ops: pane ready (qoderclicn)" in out
    assert "runtime=ops_backup_qoder_qwen_max provider=qoder model=Qwen3.7-Max" in out
    assert "CLI not ready yet" not in out


def test_health_treats_live_codex_idle_footer_as_ready():
    team = {"session": "S", "agents": {"worker_qbank": {"cli": "codex-cli", "lazy": False}}}
    footer_only = (
        "• Ran eduflow status worker_qbank 进行中 \"ready\"\n"
        "  └ ✅ worker_qbank → 进行中: ready\n\n"
        "›\n\n"
        "  gpt-5.5 medium · /Volumes/Halobster/Codex相关/EduFlow-Team-orch\n"
    )
    panes = [tmux_mod.PaneInfo(index="0", active=True, current_command="node", start_command="")]
    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), _stub_tmux(
            session_alive=True, panes_without_cli=["worker_qbank"],
            pane_text={"worker_qbank": footer_only}), _stub_which({"codex"}), \
            attr_patch(tmux_mod, list_panes=lambda target: panes):
        rc, out, _ = run_cli(["health"])
    assert rc == 0
    assert "worker_qbank: pane ready (codex-cli)" in out
    assert "CLI not ready yet" not in out


def test_health_treats_codex_bypass_footer_as_ready():
    team = {"session": "S", "agents": {"manager": {"cli": "codex-cli", "lazy": False}}}
    text = (
        "──────────────────────────────────────────────── manager ──\n"
        "❯\n\n"
        "────────────────────────────────────────────────────────────\n"
        "  ⏵⏵ bypass permissions on (shift+tab to cycle)\n"
    )
    panes = [tmux_mod.PaneInfo(index="0", active=True, current_command="node", start_command="")]
    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), _stub_tmux(
            session_alive=True,
            panes_with_cli=["manager"],
            pane_text={"manager": text}), _stub_which({"codex"}), \
            attr_patch(tmux_mod, list_panes=lambda target: panes):
        rc, out, _ = run_cli(["health"])
    assert rc == 0
    assert "manager: pane ready (codex-cli)" in out
    assert "CLI not ready yet" not in out


def test_health_does_not_trust_stale_codex_bypass_footer_without_live_codex_process():
    team = {"session": "S", "agents": {"manager": {"cli": "codex-cli", "lazy": False}}}
    stale = "old Codex scrollback\n  ⏵⏵ bypass permissions on (shift+tab to cycle)\n$ "
    panes = [tmux_mod.PaneInfo(index="0", active=True, current_command="zsh", start_command="")]
    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), _stub_tmux(
            session_alive=True,
            panes_without_cli=["manager"],
            pane_text={"manager": stale}), _stub_which({"codex"}), \
            attr_patch(tmux_mod, list_panes=lambda target: panes):
        rc, out, _ = run_cli(["health"])
    assert rc == 0
    assert "manager: pane up but CLI not ready yet" in out


def test_health_distinguishes_pane_ready_from_context_guard_risk():
    from eduflow.store import local_facts

    team = {"session": "S", "agents": {"worker_course": {"cli": "claude-code", "lazy": False}}}
    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), _stub_tmux(
            session_alive=True,
            panes_with_cli=["worker_course"],
            pane_text={"worker_course": "bypass permissions on\n100% context used\n>"}):
        local_facts.append_message(
            "worker_course",
            "manager",
            "P0: read inbox before continuing Physics 0625.",
            priority="高",
        )
        write_json(paths.runtime_status_file(), {
            "agents": {
                "worker_course": {
                    "runtime": "course_primary",
                    "cli": "claude-code",
                    "model": "sonnet",
                    "provider": "anthropic-proxy",
                    "env_ok": True,
                    "smoke_ok": True,
                    "inbox_verified": False,
                }
            }
        })

        rc, out, _ = run_cli(["health"])

    assert rc == 1
    assert "worker_course: pane ready (claude-code)" in out
    assert "worker_course: context_exhausted" in out
    assert "worker_course: ready_unproven" in out
    assert "inbox_recovery_needed=true" in out


def test_health_warns_before_context_exhaustion_thresholds():
    team = {
        "session": "S",
        "agents": {
            "worker_course": {"cli": "claude-code", "lazy": False},
            "review_course": {"cli": "claude-code", "lazy": False},
        },
    }
    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), _stub_tmux(
            session_alive=True,
            panes_with_cli=["worker_course", "review_course"],
            pane_text={
                "worker_course": "bypass permissions on\ncontext: 85.0% (222k/262k)\n>",
                "review_course": "bypass permissions on\ncontext: 92.5% (242k/262k)\n>",
            }):
        rc, out, _ = run_cli(["health"])

    assert rc == 0
    assert "worker_course: context_usage_warning" in out
    assert "context_usage=85%" in out
    assert "review_course: context_compact_recommended" in out
    assert "context_usage=92.5%" in out
    assert "context_exhausted" not in out


def test_health_does_not_trust_stale_codex_footer_without_live_codex_process():
    team = {"session": "S", "agents": {"worker_qbank": {"cli": "codex-cli", "lazy": False}}}
    stale_footer = "old Codex scrollback\n  gpt-5.5 medium · /repo\n$ "
    panes = [tmux_mod.PaneInfo(index="0", active=True, current_command="zsh", start_command="")]
    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), _stub_tmux(
            session_alive=True, panes_without_cli=["worker_qbank"],
            pane_text={"worker_qbank": stale_footer}), _stub_which({"codex"}), \
            attr_patch(tmux_mod, list_panes=lambda target: panes):
        rc, out, _ = run_cli(["health"])
    assert rc == 0
    assert "worker_qbank: pane up but CLI not ready yet" in out


def test_health_warns_when_runtime_status_env_profile_drifts_from_live_env():
    team_toml = """
chat_id = "oc_demo"

[runtime_registry.course_backup]
cli = "claude-code"
model = "deepseek-v4-pro"
provider = "deepseek"
env_profile = "deepseek_profile"

[env_profiles.deepseek_profile]
ANTHROPIC_BASE_URL = "https://api.deepseek.com/anthropic"
ANTHROPIC_MODEL = "deepseek-v4-pro"

[team]
session = "EduFlowTeam"

[team.agents.worker_course]
runtime = "course_backup"
lazy = false
"""
    from eduflow.commands import health as health_mod

    with isolated_env() as tmp, env_patch(HTTPS_PROXY=None, HTTP_PROXY=None):
        (tmp / "eduflow.toml").write_text(team_toml, encoding="utf-8")
        write_json(paths.runtime_status_file(), {
            "agents": {
                "worker_course": {
                    "runtime": "course_backup",
                    "cli": "claude-code",
                    "model": "deepseek-v4-pro",
                    "provider": "deepseek",
                    "env_profile": "deepseek_profile",
                    # Pre-populate proved-ready cache so the operational
                    # readiness section takes the cache path and doesn't
                    # re-probe (this test is about the drift warning,
                    # not the readiness verdict).
                    "env_ok": True,
                    "smoke_ok": True,
                    "verified_at": 1700000000.0,
                }
            }
        })
        with tmux_patch(
            has_session=lambda s: True,
            has_window=lambda target: target.window == "worker_course",
            capture_pane=lambda target, lines=80: "bypass permissions on\n? for shortcuts\n>",
        ), _stub_which({"claude"}), attr_patch(
            health_mod._verify_mod,
            verify_live_env_matches_profile=lambda target, name: (
                False,
                ["ANTHROPIC_BASE_URL expected=https://api.deepseek.com/anthropic live=<missing>",
                 "ANTHROPIC_MODEL expected=deepseek-v4-pro live=claude-opus-4-6"],
            ),
        ):
            rc, out, _ = run_cli(["health"])
    assert rc == 0
    assert "runtime_status_env_drift: worker_course" in out
    assert "ANTHROPIC_BASE_URL expected=https://api.deepseek.com/anthropic live=<missing>" in out
    assert "ANTHROPIC_MODEL expected=deepseek-v4-pro live=claude-opus-4-6" in out


def test_health_delegates_env_drift_to_verify_module():
    """Health used to carry its own `_pane_live_env` + env-key tuple which
    silently drifted from `runtime.verify` (7 keys vs verify's 10). Now
    `_check_runtime_env_drift` delegates to `verify.verify_live_env_matches_profile`
    — pin the delegation so the duplication does not come back."""
    from eduflow.commands import health as health_mod
    from eduflow.runtime import verify as verify_mod
    # Sanity: health no longer has its own duplicate helpers.
    assert not hasattr(health_mod, "_pane_live_env")
    assert not hasattr(health_mod, "_profile_env_from_ps")
    # Sanity: health's key set is verify's key set (same object, not a copy).
    assert health_mod._PROFILE_ENV_KEYS is verify_mod.PROFILE_ENV_KEYS
    # Sanity: verify still exposes the function health delegates to.
    assert callable(verify_mod.verify_live_env_matches_profile)


def test_health_warns_when_lark_profile_blank():
    team = {"session": "S", "agents": {"manager": {}}}
    with isolated_env(team=team, runtime_config={"chat_id": "oc_x", "lark_profile": ""}), _stub_tmux(
            session_alive=True, panes_with_cli=["manager"]):
        rc, out, _ = run_cli(["health"])
        assert rc == 0
        assert "lark_profile blank" in out


def test_health_warns_when_router_pid_missing():
    team = {"session": "S", "agents": {"manager": {}}}
    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), _stub_tmux(
            session_alive=True, panes_with_cli=["manager"]):
        rc, out, _ = run_cli(["health"])
        assert rc == 0
        assert "router: no pid file" in out
        assert "task-publish: no pid file" in out


def test_health_info_when_cursor_empty():
    """Empty cursor on first run is informational, not a warning — it only
    advances on inbound events, not self-originated say calls."""
    team = {"session": "S", "agents": {"manager": {}}}
    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), _stub_tmux(
            session_alive=True, panes_with_cli=["manager"]):
        rc, out, _ = run_cli(["health"])
        assert rc == 0
        assert "router cursor: empty" in out
        assert "ℹ️" in out  # info marker, not warn marker
        # ensure "advances on first inbound event" is in the cursor line
        assert "first inbound event" in out


# ── memory section (round-132) ──────────────────────────────────


def test_health_memory_section_info_when_no_entries():
    """Round-132: the memory section is informational. No agent has
    written entries yet → an `ℹ️` line saying so. Section header
    visible regardless."""
    team = {"session": "S", "agents": {"manager": {}}}
    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), \
            _stub_tmux(session_alive=True, panes_with_cli=["manager"]):
        rc, out, _ = run_cli(["health"])
        assert rc == 0
        assert "memory:" in out
        assert "no agent has written entries yet" in out


def test_health_memory_section_lists_agents_with_entries():
    """When agents have written memory, list them inline (one-liner if
    ≤5 agents). Doesn't change the rc — informational only."""
    from eduflow.store import memory
    team = {"session": "S",
            "agents": {"manager": {}, "worker_cc": {}}}
    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), \
            _stub_tmux(session_alive=True,
                       panes_with_cli=["manager", "worker_cc"]):
        memory.append("manager", "decision", "x")
        memory.append("worker_cc", "note", "y")
        rc, out, _ = run_cli(["health"])
        assert rc == 0
        assert "memory: 2 agent(s) with entries" in out
        assert "manager" in out and "worker_cc" in out


def test_health_shows_runtime_guard_needs_manager_action():
    team = {"session": "S", "agents": {"manager": {}}}
    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), \
            _stub_tmux(session_alive=True, panes_with_cli=["manager"]):
        path = paths.runtime_guard_state_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "agents": {
                "worker_a": {
                    "cooldown_until": 9999999999,
                    "needs_manager_action": True,
                }
            }
        }), encoding="utf-8")
        rc, out, _ = run_cli(["health"])
        assert rc == 0
        assert "runtime guard:" in out
        assert "runtime guard cooldown: worker_a" in out
        assert "runtime guard needs_manager_action: worker_a" in out


def test_health_shows_runtime_guard_escalation_details():
    team = {"session": "S", "agents": {"manager": {}}}
    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), \
            _stub_tmux(session_alive=True, panes_with_cli=["manager"]):
        path = paths.runtime_guard_state_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "agents": {
                "worker_a": {
                    "needs_manager_action": True,
                    "escalation_needed": True,
                    "last_failure_reason": "rate_limit",
                    "last_switch_outcome": "fallback_exhausted",
                    "from_runtime": "primary",
                    "to_runtime": "backup",
                    "escalation_reason": "fallback_chain_exhausted",
                }
            }
        }), encoding="utf-8")
        rc, out, _ = run_cli(["health"])
        assert rc == 0
        assert "runtime guard escalation_needed: worker_a" in out
        assert "failure=rate_limit" in out
        assert "outcome=fallback_exhausted" in out
        assert "route=primary->backup" in out
        assert "escalation=fallback_chain_exhausted" in out


# ── binaries / env ──────────────────────────────────────────────


def _stub_which(present: set[str]):
    """shutil.which replacement: returns a fake path for names in `present`,
    None for everything else. Doesn't fall through to the real PATH."""
    return attr_patch(
        shutil,
        which=lambda name, *a, **kw: f"/usr/bin/{name}" if name in present else None,
    )


def test_health_red_when_binary_missing():
    team = {"session": "S", "agents": {"m": {"cli": "claude-code"}}}
    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), _stub_tmux(
            session_alive=True, panes_with_cli=["m"]), _stub_which(set()):
        rc, out, _ = run_cli(["health"])
        assert rc == 1
        assert "claude: not on PATH" in out


def test_health_green_when_binaries_present():
    team = {"session": "S", "agents": {"m": {"cli": "claude-code"}}}
    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), _stub_tmux(
            session_alive=True, panes_with_cli=["m"]), _stub_which({"claude"}):
        rc, out, _ = run_cli(["health"])
        assert "claude: /usr/bin/claude" in out


def test_health_warns_when_proxy_set_without_no_proxy():
    team = {"session": "S", "agents": {"m": {}}}
    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), _stub_tmux(
            session_alive=True, panes_with_cli=["m"]), \
            env_patch(HTTPS_PROXY="http://proxy:7890", LARK_CLI_NO_PROXY=None):
        rc, out, _ = run_cli(["health"])
        assert "HTTPS_PROXY=http://proxy:7890 set without LARK_CLI_NO_PROXY" in out


def test_health_silent_when_proxy_unset():
    team = {"session": "S", "agents": {"m": {}}}
    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), _stub_tmux(
            session_alive=True, panes_with_cli=["m"]), \
            env_patch(HTTPS_PROXY=None, HTTP_PROXY=None):
        rc, out, _ = run_cli(["health"])
        assert "HTTPS_PROXY" not in out



def test_health_info_when_proxy_set_with_no_proxy_flag():
    """HTTPS_PROXY set + LARK_CLI_NO_PROXY=1 → informational ℹ️ rather
    than warning ⚠️. The wrapper strips proxy at lark.subprocess_env(),
    so this is intentional + harmless — but the env var still shows
    so operators don't get confused why their proxy isn't applying."""
    team = {"session": "S", "agents": {"m": {}}}
    with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), _stub_tmux(
            session_alive=True, panes_with_cli=["m"]), \
            env_patch(HTTPS_PROXY="http://proxy:7890", LARK_CLI_NO_PROXY="1"):
        rc, out, _ = run_cli(["health"])
        assert "HTTPS_PROXY set" in out
        assert "wrapper will strip" in out
        # Confirm it's INFO not WARNING — the test would also fire a
        # warning on bad emoji selection, so check the explicit string.
        assert "ℹ️" in out


def test_health_no_proxy_flag_truthy_variants_all_recognised():
    """LARK_CLI_NO_PROXY accepts 1/true/yes/on (case-insensitive). Make
    sure the ℹ️ branch fires for the full set, not just the literal '1'."""
    team = {"session": "S", "agents": {"m": {}}}
    for truthy in ("1", "true", "True", "YES", "on"):
        with isolated_env(team=team, runtime_config={"chat_id": "oc_x"}), \
                _stub_tmux(session_alive=True, panes_with_cli=["m"]), \
                env_patch(HTTPS_PROXY="http://p", LARK_CLI_NO_PROXY=truthy):
            rc, out, _ = run_cli(["health"])
            assert "wrapper will strip" in out, (
                f"LARK_CLI_NO_PROXY={truthy!r} should be recognised as truthy")


# ── help ────────────────────────────────────────────────────────


def test_health_help():
    rc, out, _ = run_cli(["health", "--help"])
    assert rc == 0
    assert "usage: eduflow health" in out


# ── --json mode ─────────────────────────────────────────────────


def test_health_json_emits_machine_readable_object():
    """--json dumps {ok, bad, warn, lines} so smoke conductors can
    branch on `ok` without grepping the formatted output."""
    import json as _json
    team = {"session": "S", "agents": {"manager": {"cli": "claude-code"}}}
    rc_cfg = {"chat_id": "oc_x", "lark_profile": "prod"}
    with isolated_env(team=team, runtime_config=rc_cfg), _stub_tmux(
            session_alive=True, panes_with_cli=["manager"]), \
            env_patch(HTTPS_PROXY=None, HTTP_PROXY=None):
        rc, out, _ = run_cli(["health", "--json"])
        # No reds → exit 0
        assert rc == 0
        data = _json.loads(out)
        assert isinstance(data, dict)
        assert data["ok"] is True
        assert data["bad"] == 0
        assert data["warn"] >= 0
        assert isinstance(data["lines"], list)
        assert any("team config" in line for line in data["lines"])


def test_health_json_with_bad_check_returns_one_and_ok_false():
    """When a check fails, JSON mode still exits 1 and ok=False."""
    import json as _json
    # team.json missing → red
    rc_cfg = {"chat_id": "oc_x"}
    with isolated_env(runtime_config=rc_cfg), _stub_tmux(session_alive=False):
        rc, out, _ = run_cli(["health", "--json"])
        assert rc == 1
        data = _json.loads(out)
        assert data["ok"] is False
        assert data["bad"] >= 1


def test_health_json_unknown_args_returns_one():
    """Mistyped flag should fail loudly, not silently accept."""
    rc, _, err = run_cli(["health", "--lol"])
    assert rc == 1
    assert "unexpected args" in err
