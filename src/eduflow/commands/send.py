"""`eduflow send <to> <from> <message> [priority] [--no-inject]`

Append a message to the local inbox AND poke the recipient's tmux
pane so they know to read it.

Previously inbox-only with the doc claim "only the Feishu
router can do tmux inject". That broke peer messaging end-to-end —
manager sending to worker_cc wrote a row, but worker_cc had no way
to know unless it polled. Boss-flagged after the 全员报道 e2e where
manager.send → worker_cc went into a dead drop.

Now mirrors the router's apply pattern: append_message + tmux.inject
into the recipient's pane. Recipient's claude (or other CLI) sees a
prompt-style notification and processes inbox proactively. Pass
`--no-inject` to keep the old "silent dead-drop" behaviour for
audit-only writes (caller is putting context for later, not
expecting recipient to read NOW).
"""
from __future__ import annotations

import sys

from eduflow.agents import get_adapter, identity as _identity
from eduflow.runtime import config, lifecycle, tmux, wake
from eduflow.store import local_facts
from eduflow.util import pop_bool_flag, pop_flag, usage_error


USAGE = (
    "usage: eduflow send <to> <from> <message|--stdin> [priority] "
    "[--no-inject] [--no-memory] [--task-id <T-id>] [--revision <n>] "
    "[--supersedes-message-id <local-id>]"
)


def _touch_wake_safely(agent: str) -> None:
    """Phase 4 helper: stamp wake + active for `agent`.  Best-effort;
    never raises — `send` must remain non-blocking."""
    try:
        from eduflow.store import agent_residency
        agent_residency.touch_wake(agent)
    except Exception:
        pass


def _resolved_for_current_or_configured_runtime(agent: str) -> dict:
    """Resolve runtime for a lazy wake, preferring an explicit switch state.

    Runtime recovery can switch a lazy pane before it has an active CLI.
    The next inbox nudge must honor that persisted runtime instead of
    silently waking the agent back on its configured primary lane.
    """
    resolved = config.resolved_agent_config(agent)
    current = lifecycle.current_runtime_status(agent).get("runtime", "")
    if not current:
        return resolved
    for item in resolved.get("runtime_chain", []):
        if item.get("name") == current:
            selected = dict(resolved)
            selected.update({
                "selected_runtime": item.get("name", current),
                "cli": item.get("cli", resolved.get("cli", "claude-code")),
                "model": item.get("model", resolved.get("model", "opus")),
                "provider": item.get("provider", ""),
                "env_profile": item.get("env_profile", ""),
            })
            return selected
    return resolved


def main(argv: list[str]) -> int:
    rest = list(argv)
    no_inject = pop_bool_flag(rest, "--no-inject")
    no_memory = pop_bool_flag(rest, "--no-memory")
    task_id_arg = pop_flag(rest, "--task-id") or ""
    revision_arg = pop_flag(rest, "--revision") or "0"
    supersedes_message_id = pop_flag(rest, "--supersedes-message-id") or ""
    try:
        revision = int(revision_arg)
    except ValueError:
        return usage_error("--revision must be a non-negative integer")
    if revision < 0:
        return usage_error("--revision must be a non-negative integer")
    if len(rest) < 3:
        return usage_error(USAGE)
    to, frm = rest[0], rest[1]
    if rest[2] == "--stdin":
        message = sys.stdin.read()
    else:
        message = rest[2]
    priority = rest[3] if len(rest) > 3 else "中"
    # Prepend Memory Packet so recipient retains active constraints after /compact
    if not no_memory:
        try:
            from eduflow.memory import assemble_memory_packet, extract_task_id_from_message
            _task_id = extract_task_id_from_message(message) or task_id_arg
            _packet = assemble_memory_packet(to, task_id=_task_id)
            if _packet:
                message = f"{_packet}\n\n---\n\n{message}"
        except Exception:
            pass  # best-effort: never block send on memory failures
    local_facts.touch_heartbeat(frm)
    delivery_state = "requires_polling" if no_inject else "delivered_to_inbox"
    local_id = local_facts.append_message(
        to,
        frm,
        message,
        priority=priority,
        delivery_state=delivery_state,
        task_id=task_id_arg,
        revision=revision,
        supersedes_message_id=supersedes_message_id,
    )
    # Phase 4 (2026-07-01, P4-B 调后): stamp last_active_at ONLY for
    # warm recipients.  Resident agents never sleep so writing their
    # last_active_at is no-op + clutter; cold agents have no pane to
    # retire.  Best-effort — never block `send` on the stamp call.
    try:
        from eduflow.runtime import config as _cfg
        from eduflow.store import agent_residency
        if _cfg.load_residency_policy(to).mode == "warm":
            agent_residency.touch_active(to)
    except Exception:
        pass
    is_high_priority = local_facts.is_high_priority(priority)
    # Watch owner: current = Sophon; auto_ops kept as historical alias.
    if to in {"Sophon", "auto_ops"} and is_high_priority:
        latest = local_facts.latest_unread_message(to)
        if latest and str(latest.get("local_id") or "") == local_id:
            local_facts.record_auto_ops_min_ack(
                to, local_id, str(latest.get("content") or message or "")
            )
    if to == "worker_qbank" and is_high_priority:
        latest = local_facts.latest_unread_message(to)
        if latest and str(latest.get("local_id") or "") == local_id:
            local_facts.record_worker_stage_ack(
                to, local_id, str(latest.get("content") or message or "")
            )
    # Review owner: current = worker_review; review_course kept as alias.
    # worker_course excluded: auto-ack "接单" footprint was misread as
    # task completion, causing the agent to skip inbox processing entirely.
    if to in {"worker_review", "review_course", "worker_builder"} and is_high_priority:
        latest = local_facts.latest_unread_message(to)
        if latest and str(latest.get("local_id") or "") == local_id:
            local_facts.record_worker_stage_ack(
                to, local_id, str(latest.get("content") or message or "")
            )
    print(f"📥 inbox: {to} ← {frm}  [local_id={local_id}]")
    if no_inject:
        print("  delivery=requires_polling")
        return 0
    # Best-effort tmux inject so the recipient's pane sees a nudge to
    # read inbox. Failures here (no session, no pane, unknown adapter)
    # don't fail the command — the inbox row is still the canonical
    # record the recipient will pick up next time they re-init or
    # /clear and re-read identity.
    try:
        session = config.session_name()
        window_target = tmux.Target(session, to)
        if not tmux.has_window(window_target):
            local_facts.update_message_delivery(local_id, "awaiting_pane_or_polling")
            return 0
        target = tmux.preferred_pane_target(window_target)
        cfg = config.agent_config(to) if to in config.agent_names() else {}
        resolved = _resolved_for_current_or_configured_runtime(to)
        adapter = get_adapter(resolved.get("cli", cfg.get("cli", "claude-code")))
        # Lazy worker only: pane exists as placeholder shell, CLI hasn't
        # spawned yet. Without wake_if_dormant the inject below would land
        # in the shell, not the CLI — agent never sees the message.
        # REGRESSION 2026-05-06 host_smoke §7: lazy worker_codex received
        # a manager dispatch but pane stayed at a bare shell prompt.
        # Non-lazy agents (typically manager + active workers) are
        # ALREADY started by `eduflow up`; injecting straight in is
        # faster than the is_ready capture-pane round-trip and matches
        # the boss preference 2026-05-06: "send 主管时不需要等待他空闲,
        # 直接往 session 里面加告诉他就行了". Claude / Codex pane stash
        # injected text into the input buffer if mid-thought; it's read
        # on the next input-accept turn.
        if cfg.get("lazy") and not wake.is_ready(target, adapter):
            from eduflow.runtime import tunables
            runtime_cli = resolved.get("cli", cfg.get("cli", "claude-code"))
            runtime_model = resolved.get("model", config.agent_model(to))
            adapter = get_adapter(runtime_cli)
            resolved["agent"] = to
            spawn_prefix = lifecycle.pane_spawn_prefix_for_runtime(resolved)
            spawn_cmd = f"{spawn_prefix} {adapter.spawn_cmd(to, runtime_model)}"
            wake_timeout = float(tunables.tunable("wake.lazy_wake_timeout_s", 30.0))
            def _on_woken() -> None:
                local_facts.upsert_status(
                    to, "进行中", "responding to first message",
                )
                _touch_wake_safely(to)

            woke = wake.wake_if_dormant(
                target, adapter,
                spawn_cmd=spawn_cmd,
                init_msg=_identity.init_prompt(to),
                timeout_s=wake_timeout,
                # Phase 4 (2026-07-01): wake success also resets the
                # residency clock so the warm-agent sweep treats a
                # freshly-spawned worker as active.
                on_woken=_on_woken,
            )
            if not woke:
                # Phase 4 (2026-07-01): warm-agent wake failed within
                # the configured timeout.  Fire the ALERT so the
                # auto_ops on-watch operator (and the boss) see it
                # rather than silently piling the message into the
                # agent's unconsumed inbox.
                try:
                    from eduflow.commands import wake_alert
                    wake_alert.fire_wake_failure_alert(
                        target_agent=to,
                        failure_kind=wake_alert._FAIL_KIND_READY_TIMEOUT,
                        wake_timeout_s=wake_timeout,
                    )
                except Exception as e:
                    print(
                        f"  ⚠️ wake-failure alert dispatch failed for {to}: {e}",
                        file=sys.stderr,
                    )
        nudge = (f"📥 {frm} → {to}（{local_id}）。"
                 f"`eduflow inbox {to}` → 处理 → "
                 f"`eduflow read {local_id} --ack accepted_task` "
                 f"(返修用 `--ack accepted_revision`) → 必要时 "
                 f"`eduflow say {to} \"...\" --to user`。")
        tmux.inject(target, nudge, submit_keys=adapter.submit_keys())
        local_facts.update_message_delivery(local_id, "nudge_injected")
    except Exception as e:
        local_facts.update_message_delivery(local_id, "inject_failed_requires_polling")
        print(f"  ⚠️ tmux inject best-effort failed for {to}: {e}")
    return 0
