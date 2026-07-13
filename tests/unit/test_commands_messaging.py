"""Tests for `eduflow send / inbox / read` commands.

Goes through run_cli([...]) so we exercise the dispatch + handler
contract end-to-end (without spawning a subprocess).
"""
from __future__ import annotations

import io
import shlex

from helpers import attr_patch
from helpers import isolated_env, run_cli
from eduflow.store import local_facts


def test_send_writes_inbox_and_prints_local_id():
    with isolated_env():
        rc, out, err = run_cli(["send", "worker", "manager", "do task X"])
        assert rc == 0, err
        assert "inbox: worker ← manager" in out
        assert "local_id=msg_" in out

        rows = local_facts.list_messages("worker")
        assert len(rows) == 1
        assert rows[0]["content"] == "do task X"
        assert rows[0]["from"] == "manager"


def test_send_touches_sender_heartbeat():
    with isolated_env():
        run_cli(["send", "worker", "manager", "do X"])
        assert local_facts.get_heartbeat("manager") is not None


def test_send_to_auto_ops_high_priority_records_min_ack_visibility():
    with isolated_env():
        rc, _, err = run_cli([
            "send",
            "auto_ops",
            "manager",
            "当前卡在哪一拍，谁卡住了，当前最大协作缺口是什么",
            "高",
            "--no-inject",
        ])
        assert rc == 0, err
        snap = local_facts.get_status("auto_ops")
        assert snap is not None
        assert snap["status"] == "进行中"
        assert "盯盘中" in snap["task"]
        assert local_facts.get_heartbeat("auto_ops") is not None
        logs = local_facts.list_logs("auto_ops")
        assert len(logs) == 1
        assert logs[0]["type"] == "ack"


def test_send_to_auto_ops_does_not_hide_unrelated_high_priority_messages():
    with isolated_env():
        run_cli([
            "send", "auto_ops", "manager",
            "只回三行状态包：当前真实状态", "高", "--no-inject",
        ])
        rc, _, err = run_cli([
            "send", "auto_ops", "manager",
            "当前卡在 manager 消费，先 ACK 再继续盯盘", "高", "--no-inject",
        ])
        assert rc == 0, err
        unread = local_facts.list_messages("auto_ops", unread_only=True)
        assert len(unread) == 2
        assert any("当前真实状态" in row["content"] for row in unread)
        assert any("manager 消费" in row["content"] for row in unread)
        snap = local_facts.get_status("auto_ops")
        assert snap is not None
        assert "manager 消费" in snap["task"]


def test_send_to_worker_qbank_high_priority_records_followup_visibility():
    with isolated_env():
        rc, _, err = run_cli([
            "send",
            "worker_qbank",
            "manager",
            "请基于 Batch 7 最新通过结果继续做 qbank follow-up",
            "高",
            "--no-inject",
        ])
        assert rc == 0, err
        snap = local_facts.get_status("worker_qbank")
        assert snap is not None
        assert snap["status"] == "已接单"
        assert "题库校验已接单" in snap["task"]
        assert local_facts.get_heartbeat("worker_qbank") is not None
        logs = local_facts.list_logs("worker_qbank")
        assert len(logs) == 1
        assert logs[0]["type"] == "qbank_followup"


def test_send_to_worker_qbank_accepts_english_high_priority_for_visibility():
    with isolated_env():
        rc, _, err = run_cli([
            "send",
            "worker_qbank",
            "codex",
            "请给 qbank 当前任务一个最小接单状态包",
            "high",
            "--no-inject",
        ])
        assert rc == 0, err
        snap = local_facts.get_status("worker_qbank")
        assert snap is not None
        assert snap["status"] == "已接单"
        assert "qbank 当前任务" in snap["task"]
        logs = local_facts.list_logs("worker_qbank")
        assert len(logs) == 1
        assert logs[0]["type"] == "qbank_followup"


def test_send_to_worker_course_high_priority_stays_unread():
    """worker_course was removed from auto-ack (send.py) because the
    system-generated "接单" footprint was misread as task completion,
    causing the agent to skip inbox processing entirely.  High-priority
    messages must stay genuinely unread until the agent reads them."""
    with isolated_env():
        rc, _, err = run_cli([
            "send",
            "worker_course",
            "manager",
            "请继续 Mathematics 0580 当前批次生产",
            "高",
            "--no-inject",
        ])
        assert rc == 0, err
        # Message stays unread — no auto-ack
        unread = local_facts.list_messages("worker_course", unread_only=True)
        assert len(unread) == 1
        assert "Mathematics 0580" in unread[0]["content"]
        # No stage ack log written by send itself
        logs = local_facts.list_logs("worker_course")
        assert logs == []  # auto-ack removed; agent produces its own logs when it processes


def test_send_explicitly_supersedes_a_previous_message_without_marking_it_read():
    with isolated_env():
        run_cli([
            "send", "worker_course", "manager", "T-172 original instruction", "高",
            "--task-id", "T-172", "--no-inject",
        ])
        original = local_facts.list_messages("worker_course")[0]["local_id"]

        rc, _, err = run_cli([
            "send", "worker_course", "manager", "T-172 corrected instruction", "高",
            "--task-id", "T-172", "--supersedes-message-id", original, "--no-inject",
        ])

        assert rc == 0, err
        old = local_facts.get_message(original)
        assert old is not None
        assert old["read"] is False
        assert old["superseded"] is True
        unread = local_facts.list_messages("worker_course", unread_only=True)
        assert len(unread) == 1
        assert "corrected instruction" in unread[0]["content"]


def test_send_to_review_course_high_priority_records_stage_ack_visibility():
    with isolated_env():
        rc, _, err = run_cli([
            "send",
            "review_course",
            "manager",
            "请 review Mathematics 0580 当前交付",
            "高",
            "--no-inject",
        ])
        assert rc == 0, err
        snap = local_facts.get_status("review_course")
        assert snap is not None
        assert snap["status"] == "已接单"
        assert "课程 review 已接单" in snap["task"]
        logs = local_facts.list_logs("review_course")
        assert len(logs) == 1
        assert logs[0]["type"] == "review_course_stage_ack"


def test_send_to_worker_builder_high_priority_records_stage_ack_visibility():
    with isolated_env():
        rc, _, err = run_cli([
            "send",
            "worker_builder",
            "manager",
            "请沉淀 Mathematics 0580 生产经验为 skill",
            "高",
            "--no-inject",
        ])
        assert rc == 0, err
        snap = local_facts.get_status("worker_builder")
        assert snap is not None
        assert snap["status"] == "已接单"
        assert "builder 已接单" in snap["task"]
        logs = local_facts.list_logs("worker_builder")
        assert len(logs) == 1
        assert logs[0]["type"] == "worker_builder_stage_ack"


def test_send_to_worker_qbank_does_not_hide_unrelated_high_priority_messages():
    with isolated_env():
        run_cli([
            "send", "worker_qbank", "manager",
            "先看 Batch 6 的最小 qbank verdict", "高", "--no-inject",
        ])
        rc, _, err = run_cli([
            "send", "worker_qbank", "manager",
            "请基于 Batch 7 最新通过结果继续做 qbank follow-up", "高", "--no-inject",
        ])
        assert rc == 0, err
        unread = local_facts.list_messages("worker_qbank", unread_only=True)
        assert len(unread) == 2
        assert any("Batch 6" in row["content"] for row in unread)
        assert any("Batch 7" in row["content"] for row in unread)
        snap = local_facts.get_status("worker_qbank")
        assert snap is not None
        assert "Batch 7" in snap["task"]


def test_inbox_touches_agent_heartbeat():
    with isolated_env():
        run_cli(["inbox", "worker"])
        assert local_facts.get_heartbeat("worker") is not None


def test_send_priority_param_threads_through():
    with isolated_env():
        run_cli(["send", "a", "b", "msg", "高"])
        rows = local_facts.list_messages("a")
        assert rows[0]["priority"] == "高"


def test_send_stdin_preserves_shell_sensitive_message_text():
    from eduflow.commands import send as send_mod

    payload = "Fee is $55,800; formula=`=SUM(A1:A3)`; keep $HOME literal."
    with isolated_env(), attr_patch(send_mod.sys, stdin=io.StringIO(payload)):
        rc, out, err = run_cli(["send", "worker", "manager", "--stdin", "高", "--no-inject"])
        assert rc == 0, err
        assert "inbox: worker ← manager" in out
        rows = local_facts.list_messages("worker")
        assert rows[0]["content"] == payload
        assert rows[0]["priority"] == "高"


def test_send_missing_args_returns_one_with_usage_to_stderr():
    rc, out, err = run_cli(["send", "only-one-arg"])
    assert rc == 1
    assert "usage: eduflow send" in err


def test_send_no_inject_flag_skips_pane_inject_after_R168():
    """R168: `--no-inject` opts out of the new auto-inject behaviour
    so audit-only writes (caller is parking context for later, not
    expecting recipient to act NOW) stay silent. Inbox row still
    written; recipient won't be pinged."""
    with isolated_env():
        rc, out, _ = run_cli(["send", "worker", "manager", "x", "--no-inject"])
        assert rc == 0
        assert "inbox: worker ← manager" in out
        assert "delivery=requires_polling" in out
        rows = local_facts.list_messages("worker")
        assert len(rows) == 1
        assert rows[0]["delivery_state"] == "requires_polling"


def test_send_default_inject_best_effort_when_no_tmux():
    """Without a live tmux session, the inject step is best-effort —
    `has_window` returns False (or the wrapper raises) and the command
    still returns 0 with the inbox row landed. No noisy stderr."""
    with isolated_env():
        rc, out, err = run_cli(["send", "worker", "manager", "x"])
        assert rc == 0
        assert "inbox: worker ← manager" in out
        rows = local_facts.list_messages("worker")
        assert len(rows) == 1


def test_send_skips_wake_for_non_lazy_agent():
    """Boss-flagged 2026-05-06: 给 manager 发消息不需要等他空闲, 直接
    inject 就行 (claude pane stash input buffer 自己处理). 只 lazy 员
    工才走 wake_if_dormant. 验证: 给一个 has_window=False 的 non-lazy
    agent 发消息时, send 既不调 wake.is_ready 也不调 wake_if_dormant."""
    from helpers import attr_patch
    from eduflow.runtime import wake, tmux
    calls = {"is_ready": 0, "wake_if_dormant": 0}
    def fake_is_ready(*a, **kw):
        calls["is_ready"] += 1
        return True
    def fake_wake(*a, **kw):
        calls["wake_if_dormant"] += 1
    with isolated_env(team={"agents": {"manager": {"cli": "claude-code"}}}):
        with attr_patch(wake, is_ready=fake_is_ready,
                        wake_if_dormant=fake_wake):
            with attr_patch(tmux, has_window=lambda *a, **kw: False):
                rc, _, _ = run_cli(["send", "manager", "boss", "hi"])
    assert rc == 0
    # has_window=False 提前 return 0 → wake 调用 0 次
    assert calls["is_ready"] == 0
    assert calls["wake_if_dormant"] == 0


def test_send_calls_wake_only_for_lazy_agent():
    """Lazy agent: pane 是 placeholder shell 还没 spawn CLI, 必须 wake_
    if_dormant 否则 inject 落到 shell 不是 CLI."""
    from helpers import attr_patch
    from eduflow.runtime import wake, tmux, lifecycle
    calls = {"is_ready": 0, "wake_if_dormant": 0}
    def fake_is_ready(*a, **kw):
        calls["is_ready"] += 1
        return False  # not ready → triggers wake
    def fake_wake(*a, **kw):
        calls["wake_if_dormant"] += 1
    with isolated_env(team={"agents": {"worker_lazy": {
            "cli": "claude-code", "lazy": True}}}):
        with attr_patch(wake, is_ready=fake_is_ready,
                        wake_if_dormant=fake_wake):
            with attr_patch(tmux,
                            has_window=lambda *a, **kw: True,
                            inject=lambda *a, **kw: None):
                with attr_patch(lifecycle,
                                pane_env_prefix=lambda: "X=Y"):
                    rc, _, _ = run_cli(
                        ["send", "worker_lazy", "manager", "hi"])
    assert rc == 0
    assert calls["is_ready"] == 1
    assert calls["wake_if_dormant"] == 1


def test_send_lazy_wake_uses_runtime_env_profile_prefix():
    """Lazy send wake path must honor the resolved runtime env_profile,
    otherwise Anthropic-compatible gateway vars never reach the first
    spawned pane and the agent falls back to direct Claude auth/network."""
    from helpers import attr_patch
    from eduflow.runtime import wake, tmux

    captured: dict[str, str] = {}

    def fake_is_ready(*a, **kw):
        return False

    def fake_wake(*a, **kw):
        captured["spawn_cmd"] = kw.get("spawn_cmd", "")

    team_toml = """
chat_id = "oc_demo"
lark_profile = "eduflow-team"

[runtime_registry.ops_primary]
cli = "claude-code"
model = "sonnet"
provider = "anthropic-proxy"
env_profile = "claude_proxy_primary"

[env_profiles.claude_proxy_primary]
ANTHROPIC_BASE_URL = "https://coding.dashscope.aliyuncs.com/apps/anthropic"
ANTHROPIC_MODEL = "qwen3.7-plus"

[team]
session = "EduFlowTeam"

[team.agents.anna]
runtime = "ops_primary"
cli = "claude-code"
lazy = true
role = "assistant"
"""
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(team_toml, encoding="utf-8")
        with attr_patch(wake, is_ready=fake_is_ready, wake_if_dormant=fake_wake):
                with attr_patch(tmux,
                                has_window=lambda *a, **kw: True,
                                inject=lambda *a, **kw: None):
                    rc, _, _ = run_cli(["send", "anna", "manager", "ping"])
        env_files = list((tmp / "state" / "spawn-env").iterdir())
        assert len(env_files) == 1
        env_file = env_files[0]
        env_contents = env_file.read_text(encoding="utf-8")
    assert rc == 0
    assert str(env_file) in captured["spawn_cmd"]
    assert "ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic" not in captured["spawn_cmd"]
    assert "ANTHROPIC_MODEL=qwen3.7-plus" not in captured["spawn_cmd"]
    assert "ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic" in env_contents
    assert "ANTHROPIC_MODEL=qwen3.7-plus" in env_contents


def test_send_lazy_wake_prefers_persisted_switched_runtime():
    """If a lazy agent was manually/automatically switched, the next
    message should wake that selected runtime instead of the configured
    primary lane.
    """
    from helpers import attr_patch
    from eduflow.runtime import wake, tmux, paths
    from eduflow.util import write_json

    captured: dict[str, str] = {}

    def fake_is_ready(*a, **kw):
        return False

    def fake_wake(*a, **kw):
        captured["spawn_cmd"] = kw.get("spawn_cmd", "")

    team_toml = """
chat_id = "oc_demo"
lark_profile = "eduflow-team"

[runtime_registry.ops_primary]
cli = "claude-code"
model = "sonnet"
fallback_to = "ops_backup_qoder_qwen_max"

[runtime_registry.ops_backup_qoder_qwen_max]
cli = "qoderclicn"
model = "Qwen3.7-Max"
provider = "qoder"
switch_on = ["rate_limit", "auth_failure"]

[team]
session = "EduFlowTeam"

[team.agents.auto_ops]
runtime = "ops_primary"
lazy = true
role = "ops"
"""
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(team_toml, encoding="utf-8")
        write_json(paths.runtime_status_file(), {
            "agents": {
                "auto_ops": {
                    "runtime": "ops_backup_qoder_qwen_max",
                    "cli": "qoderclicn",
                    "model": "Qwen3.7-Max",
                    "provider": "qoder",
                    "env_profile": "",
                    "reason": "manual_failover_to_qoderclicn_qwen_max",
                }
            }
        })
        with attr_patch(wake, is_ready=fake_is_ready, wake_if_dormant=fake_wake):
            with attr_patch(tmux,
                            has_window=lambda *a, **kw: True,
                            inject=lambda *a, **kw: None):
                rc, _, err = run_cli(["send", "auto_ops", "manager", "ping", "高"])
    assert rc == 0, err
    argv = shlex.split(captured["spawn_cmd"])
    assert any(part == "qoderclicn" or part.endswith("/qoderclicn") for part in argv)
    assert "--model Qwen3.7-Max" in captured["spawn_cmd"]


def test_inbox_lists_unread_with_local_id_and_returns_zero():
    with isolated_env():
        run_cli(["send", "w", "m", "first"])
        run_cli(["send", "w", "m", "second"])
        rc, out, _ = run_cli(["inbox", "w"])
        assert rc == 0
        assert "📬 w: 2 unread" in out
        assert "first" in out and "second" in out


def test_inbox_empty_prints_no_unread():
    with isolated_env():
        rc, out, _ = run_cli(["inbox", "nobody"])
        assert rc == 0
        assert "📭 nobody: no unread messages" in out


def test_read_marks_then_inbox_drops_it():
    with isolated_env():
        run_cli(["send", "w", "m", "task A"])
        msgs = local_facts.list_messages("w")
        local_id = msgs[0]["local_id"]

        rc, out, _ = run_cli(["read", local_id])
        assert rc == 0
        assert "marked read" in out

        rc, out, _ = run_cli(["inbox", "w"])
        assert rc == 0
        assert "📭 w: no unread messages" in out


def test_read_ack_records_worker_revision_acceptance_without_confusing_plain_read():
    with isolated_env():
        run_cli(["send", "worker_course", "review_course", "minor fix 7.5"])
        local_id = local_facts.list_messages("worker_course")[0]["local_id"]

        rc, out, err = run_cli([
            "read", local_id,
            "--ack", "accepted_revision",
            "--topic", "Accounting 7.5",
            "--file", "IGCSE Accounting QA.md",
            "--issue", "fix amount expansion",
        ])
        assert rc == 0, err
        assert "ack=accepted_revision" in out
        row = local_facts.get_message(local_id)
        assert row is not None
        assert row["read"] is True
        assert row["ack_state"] == "agent_acknowledged"
        assert row["ack_kind"] == "accepted_revision"
        assert row["ack_details"]["topic"] == "Accounting 7.5"
        assert row["ack_details"]["files"] == ["IGCSE Accounting QA.md"]
        assert row["ack_details"]["issues"] == ["fix amount expansion"]
        snap = local_facts.get_status("worker_course")
        assert snap is not None
        assert snap["status"] == "已接单"
        assert "课程主线已接单" in snap["task"]
        logs = local_facts.list_logs("worker_course")
        assert len(logs) == 1
        assert logs[0]["type"] == "worker_course_stage_ack"


def test_read_ack_started_task_upgrades_visibility_to_in_progress():
    with isolated_env():
        run_cli(["send", "worker_builder", "manager", "请开始整理 live 在岗感修复经验", "高", "--no-inject"])
        local_id = local_facts.list_messages("worker_builder")[0]["local_id"]

        rc, out, err = run_cli(["read", local_id, "--ack", "started_task"])
        assert rc == 0, err
        assert "ack=started_task" in out
        row = local_facts.get_message(local_id)
        assert row is not None
        assert row["ack_state"] == "action_started"
        snap = local_facts.get_status("worker_builder")
        assert snap is not None
        assert snap["status"] == "进行中"
        assert "builder 开始处理" in snap["task"]
        logs = local_facts.list_logs("worker_builder")
        assert len(logs) == 2
        assert logs[-1]["type"] == "worker_builder_started"


def test_read_ack_completed_and_reconciled_are_available_from_cli():
    with isolated_env():
        run_cli(["send", "manager", "worker_course", "Physics 0625 Batch 6 已完成待收口", "高", "--no-inject"])
        local_id = local_facts.list_messages("manager")[0]["local_id"]

        rc, out, err = run_cli(["read", local_id, "--ack", "completed"])
        assert rc == 0, err
        assert "ack=completed" in out
        row = local_facts.get_message(local_id)
        assert row is not None
        assert row["ack_state"] == "completed"

        reconciliation_id = local_facts.append_message(
            "manager", "worker_course", "Physics 0625 stale completion handoff", priority="高",
        )
        assert local_facts.queue_inbox_reconciliation(
            reconciliation_id,
            actor="task_event_scanner",
            evidence="newer task closeout exists",
        )
        rc, out, err = run_cli([
            "read", reconciliation_id, "--ack", "reconciled",
            "--actor", "manager", "--evidence", "newer task closeout exists",
        ])
        assert rc == 0, err
        assert "reconciled without marking read" in out
        row = local_facts.get_message(reconciliation_id)
        assert row is not None
        assert row["ack_state"] == "reconciled"


def test_read_reconciled_requires_evidence_and_preserves_unread_bit():
    with isolated_env():
        run_cli(["send", "worker_course", "manager", "T-172 stale instruction", "高", "--no-inject"])
        local_id = local_facts.list_messages("worker_course")[0]["local_id"]
        assert local_facts.queue_inbox_reconciliation(
            local_id,
            actor="task_event_scanner",
            evidence="later worker process visibility",
        )

        rc, _, err = run_cli(["read", local_id, "--ack", "reconciled"])
        assert rc == 1
        assert "--actor and --evidence" in err
        pending = local_facts.get_message(local_id)
        assert pending is not None and pending["read"] is False

        rc, _, err = run_cli(["read", local_id])
        assert rc == 1
        assert "queued for reconciliation" in err
        rc, _, err = run_cli(["read", local_id, "--ack", "accepted_task"])
        assert rc == 1
        assert "queued for reconciliation" in err
        pending = local_facts.get_message(local_id)
        assert pending is not None and pending["ack_state"] == "reconciliation_pending"

        rc, out, err = run_cli([
            "read", local_id, "--ack", "reconciled",
            "--actor", "manager",
            "--evidence", "worker_course delivered T-172",
        ])
        assert rc == 0, err
        assert "reconciled without marking read" in out
        resolved = local_facts.get_message(local_id)
        assert resolved is not None
        assert resolved["read"] is False
        assert resolved["ack_state"] == "reconciled"


def test_inbox_shows_delivery_state_for_unread_messages():
    with isolated_env():
        run_cli(["send", "manager", "codex", "测试高优消息", "高", "--no-inject"])
        rc, out, err = run_cli(["inbox", "manager"])
        assert rc == 0, err
        assert "delivery=requires_polling" in out


def test_read_unknown_id_returns_one():
    with isolated_env():
        rc, _, err = run_cli(["read", "msg_does_not_exist"])
        assert rc == 1
        assert "no such message" in err


def test_say_allows_worker_accepted_reassurance_even_when_worker_to_user_disabled():
    from helpers import attr_patch
    calls = []

    def fake_send_card(chat_id, card, **kwargs):
        calls.append({"chat_id": chat_id, "card": card, "kwargs": kwargs})
        return {"message_id": "om_1"}

    team_toml = """
chat_id = "oc_demo"
lark_profile = "eduflow-team"

[team]
session = "EduFlowTeam"

[team.agents.worker_course]
cli = "claude-code"
role = "course worker"

[chat.publish]
worker_to_user = false
"""
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(team_toml, encoding="utf-8")
        from eduflow.feishu import chat as feishu_chat
        with attr_patch(feishu_chat, send_card=fake_send_card):
            rc, out, _ = run_cli([
                "say", "worker_course",
                "课程研发任务已接单：IGCSE Physics Motion and Forces micro-outline（T-2）",
                "--to", "user",
            ])
    assert rc == 0
    assert "→ main chat" in out
    assert len(calls) == 1


def test_say_allows_stage_surface_reassurance_even_when_worker_to_user_disabled():
    from helpers import attr_patch
    calls = []

    def fake_send_card(chat_id, card, **kwargs):
        calls.append({"chat_id": chat_id, "card": card, "kwargs": kwargs})
        return {"message_id": "om_1"}

    team_toml = """
chat_id = "oc_demo"
lark_profile = "eduflow-team"

[team]
session = "EduFlowTeam"

[team.agents.worker_builder]
cli = "claude-code"
role = "builder worker"

[chat.publish]
worker_to_user = false
"""
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(team_toml, encoding="utf-8")
        from eduflow.feishu import chat as feishu_chat
        with attr_patch(feishu_chat, send_card=fake_send_card):
            rc, out, _ = run_cli([
                "say", "worker_builder",
                "builder 已接单：沉淀 Mathematics 0580 生产经验（T-7）",
                "--to", "user",
            ])
    assert rc == 0
    assert "→ main chat" in out
    assert len(calls) == 1


def test_say_allows_worker_progress_presence_when_worker_to_user_disabled():
    from helpers import attr_patch
    calls = []

    def fake_send_card(chat_id, card, **kwargs):
        calls.append({"chat_id": chat_id, "card": card, "kwargs": kwargs})
        return {"message_id": "om_1"}

    team_toml = """
chat_id = "oc_demo"
lark_profile = "eduflow-team"

[team]
session = "EduFlowTeam"

[team.agents.worker_course]
cli = "claude-code"
role = "course worker"

[chat.publish]
worker_to_user = false
"""
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(team_toml, encoding="utf-8")
        from eduflow.feishu import chat as feishu_chat
        with attr_patch(feishu_chat, send_card=fake_send_card):
            rc, out, _ = run_cli([
                "say", "worker_course",
                "阶段进度：已完成 syllabus 对齐，正在补 topic evidence。",
                "--to", "user",
            ])
    assert rc == 0
    assert "→ main chat" in out
    assert len(calls) == 1


def test_say_allows_auto_ops_presence_when_worker_to_user_disabled():
    from helpers import attr_patch
    calls = []

    def fake_send_card(chat_id, card, **kwargs):
        calls.append({"chat_id": chat_id, "card": card, "kwargs": kwargs})
        return {"message_id": "om_1"}

    team_toml = """
chat_id = "oc_demo"
lark_profile = "eduflow-team"

[team]
session = "EduFlowTeam"

[team.agents.auto_ops]
cli = "claude-code"
role = "ops worker"

[chat.publish]
worker_to_user = false
"""
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(team_toml, encoding="utf-8")
        from eduflow.feishu import chat as feishu_chat
        with attr_patch(feishu_chat, send_card=fake_send_card):
            rc, out, _ = run_cli([
                "say", "auto_ops",
                "发现异常：worker_course 外显陈旧，已回报 manager。",
                "--to", "user",
            ])
    assert rc == 0
    assert "→ main chat" in out
    assert len(calls) == 1


def test_say_silences_auto_ops_periodic_brief_after_phase5_convergence():
    """Phase 5 (2026-07-01) 主群体验收敛: the old 30-min "运行态简报"
    presence signal is NO LONGER whitelisted through worker_to_user=
    false.  auto_ops presence is now stage-driven ([auto_ops].
    stage_driven) — periodic no-news briefs stay out of the main chat.
    """
    from helpers import attr_patch
    calls = []

    def fake_send_card(chat_id, card, **kwargs):
        calls.append({"chat_id": chat_id, "card": card, "kwargs": kwargs})
        return {"message_id": "om_1"}

    team_toml = """
chat_id = "oc_demo"
lark_profile = "eduflow-team"

[team]
session = "EduFlowTeam"

[team.agents.auto_ops]
cli = "claude-code"
role = "ops worker"

[chat.publish]
worker_to_user = false
"""
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(team_toml, encoding="utf-8")
        from eduflow.feishu import chat as feishu_chat
        with attr_patch(feishu_chat, send_card=fake_send_card):
            rc, out, _ = run_cli([
                "say", "auto_ops",
                "运行态简报：manager 在线；worker_course 进行中；review_course 待命。",
                "--to", "user",
            ])
    assert rc == 0
    # Phase 5: this periodic brief is now silenced (logged only).
    assert "silenced" in out
    assert calls == []


def test_say_still_allows_auto_ops_anomaly_after_phase5_convergence():
    """Phase 5: real anomalies still reach the main chat — only
    the no-news presence briefs were trimmed."""
    from helpers import attr_patch
    calls = []

    def fake_send_card(chat_id, card, **kwargs):
        calls.append({"chat_id": chat_id, "card": card, "kwargs": kwargs})
        return {"message_id": "om_1"}

    team_toml = """
chat_id = "oc_demo"
lark_profile = "eduflow-team"

[team]
session = "EduFlowTeam"

[team.agents.auto_ops]
cli = "claude-code"
role = "ops worker"

[chat.publish]
worker_to_user = false
"""
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(team_toml, encoding="utf-8")
        from eduflow.feishu import chat as feishu_chat
        with attr_patch(feishu_chat, send_card=fake_send_card):
            rc, out, _ = run_cli([
                "say", "auto_ops",
                "发现异常：worker_course 外显陈旧，已回报 manager。",
                "--to", "user",
            ])
    assert rc == 0
    assert "→ main chat" in out
    assert len(calls) == 1


def test_say_keeps_non_whitelisted_worker_message_silenced_when_worker_to_user_disabled():
    from helpers import attr_patch
    calls = []

    def fake_send_card(chat_id, card, **kwargs):
        calls.append({"chat_id": chat_id, "card": card, "kwargs": kwargs})
        return {"message_id": "om_1"}

    team_toml = """
chat_id = "oc_demo"
lark_profile = "eduflow-team"

[team]
session = "EduFlowTeam"

[team.agents.worker_course]
cli = "claude-code"
role = "course worker"

[chat.publish]
worker_to_user = false
"""
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(team_toml, encoding="utf-8")
        from eduflow.feishu import chat as feishu_chat
        with attr_patch(feishu_chat, send_card=fake_send_card):
            rc, out, _ = run_cli([
                "say", "worker_course",
                "课程研发任务处理中：IGCSE Physics Motion and Forces micro-outline（T-2）",
                "--to", "user",
            ])
    assert rc == 0
    assert "silenced" in out
    assert calls == []


def test_say_worker_review_can_send_review_card():
    from helpers import attr_patch, isolated_env, run_cli
    from eduflow.feishu import chat as feishu_chat

    calls = []

    def fake_send_card(chat_id, card, **kwargs):
        calls.append({"chat_id": chat_id, "card": card})
        return {"message_id": "om_test"}

    body = (
        "任务:T-1\n"
        "verdict:通过\n"
        "证据:local\n"
        "问题项:无\n"
        "下一步:manager 收口\n"
        "需要老板介入:否"
    )
    with isolated_env(
        team={"agents": {"worker_review": {"role": "review worker", "color": "green"}}},
        runtime_config={"chat_id": "oc_test", "lark_profile": ""},
    ):
        with attr_patch(feishu_chat, send_card=fake_send_card):
            rc, _, err = run_cli([
                "say", "worker_review", body, "--card", "REVIEW",
            ])
    assert rc == 0, err
    assert len(calls) == 1
    assert "[REVIEW]" in calls[0]["card"]["header"]["title"]["content"]


def test_say_sophon_can_send_alert_card():
    from helpers import attr_patch, isolated_env, run_cli
    from eduflow.feishu import chat as feishu_chat

    calls = []

    def fake_send_card(chat_id, card, **kwargs):
        calls.append({"chat_id": chat_id, "card": card})
        return {"message_id": "om_test"}

    body = (
        "异常类型:runtime\n"
        "影响范围:manager\n"
        "已自动处理:已切换\n"
        "当前状态:恢复中\n"
        "需要谁处理:manager\n"
        "需要老板介入:否"
    )
    with isolated_env(
        team={"agents": {"Sophon": {"role": "watch", "color": "red"}}},
        runtime_config={"chat_id": "oc_test", "lark_profile": ""},
    ):
        with attr_patch(feishu_chat, send_card=fake_send_card):
            rc, _, err = run_cli([
                "say", "Sophon", body, "--card", "ALERT",
            ])
    assert rc == 0, err
    assert len(calls) == 1
    assert "[ALERT]" in calls[0]["card"]["header"]["title"]["content"]


def test_say_silences_sophon_noisy_text_when_worker_to_user_disabled():
    """Structured ALERT cards bypass worker_to_user, but ordinary Sophon
    text still follows the worker_to_user suppression whitelist."""
    from helpers import attr_patch, isolated_env, run_cli
    from eduflow.feishu import chat as feishu_chat

    calls = []

    def fake_send_card(chat_id, card, **kwargs):
        calls.append({"chat_id": chat_id, "card": card})
        return {"message_id": "om_test"}

    team_toml = """
chat_id = "oc_demo"
lark_profile = "eduflow-team"

[team]
session = "EduFlowTeam"

[team.agents.Sophon]
cli = "claude-code"
role = "watch"

[chat.publish]
worker_to_user = false
"""
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(team_toml, encoding="utf-8")
        with attr_patch(feishu_chat, send_card=fake_send_card):
            rc, out, _ = run_cli([
                "say", "Sophon",
                "运行态简报：manager 在线；worker_course 进行中；review_course 待命。",
                "--to", "user",
            ])
    assert rc == 0
    assert "silenced" in out
    assert calls == []


def test_say_allows_review_blocker_reassurance_when_worker_to_user_disabled():
    from helpers import attr_patch
    calls = []

    def fake_send_card(chat_id, card, **kwargs):
        calls.append({"chat_id": chat_id, "card": card, "kwargs": kwargs})
        return {"message_id": "om_1"}

    team_toml = """
chat_id = "oc_demo"
lark_profile = "eduflow-team"

[team]
session = "EduFlowTeam"

[team.agents.review_course]
cli = "claude-code"
role = "review worker"

[chat.publish]
worker_to_user = false
"""
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(team_toml, encoding="utf-8")
        from eduflow.feishu import chat as feishu_chat
        with attr_patch(feishu_chat, send_card=fake_send_card):
            rc, out, _ = run_cli([
                "say", "review_course",
                "review 当前卡在证据包缺失：files_sampled 还不全，先等补齐再继续。",
                "--to", "user",
            ])
    assert rc == 0
    assert "→ main chat" in out
    assert len(calls) == 1


def test_say_allows_builder_started_reassurance_when_worker_to_user_disabled():
    from helpers import attr_patch
    calls = []

    def fake_send_card(chat_id, card, **kwargs):
        calls.append({"chat_id": chat_id, "card": card, "kwargs": kwargs})
        return {"message_id": "om_1"}

    team_toml = """
chat_id = "oc_demo"
lark_profile = "eduflow-team"

[team]
session = "EduFlowTeam"

[team.agents.worker_builder]
cli = "claude-code"
role = "builder worker"

[chat.publish]
worker_to_user = false
"""
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(team_toml, encoding="utf-8")
        from eduflow.feishu import chat as feishu_chat
        with attr_patch(feishu_chat, send_card=fake_send_card):
            rc, out, _ = run_cli([
                "say", "worker_builder",
                "builder 已开始处理：正在排查 worker_course inbox ACK 异常。",
                "--to", "user",
            ])
    assert rc == 0
    assert "→ main chat" in out
    assert len(calls) == 1


def test_say_allows_review_started_reassurance_when_worker_to_user_disabled():
    from helpers import attr_patch
    calls = []

    def fake_send_card(chat_id, card, **kwargs):
        calls.append({"chat_id": chat_id, "card": card, "kwargs": kwargs})
        return {"message_id": "om_1"}

    team_toml = """
chat_id = "oc_demo"
lark_profile = "eduflow-team"

[team]
session = "EduFlowTeam"

[team.agents.review_course]
cli = "claude-code"
role = "review worker"

[chat.publish]
worker_to_user = false
"""
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(team_toml, encoding="utf-8")
        from eduflow.feishu import chat as feishu_chat
        with attr_patch(feishu_chat, send_card=fake_send_card):
            rc, out, _ = run_cli([
                "say", "review_course",
                "开始复核 Physics 0625 Batch 2+，先核对 items 映射与难度分布。",
                "--to", "user",
            ])
    assert rc == 0
    assert "→ main chat" in out
    assert len(calls) == 1
