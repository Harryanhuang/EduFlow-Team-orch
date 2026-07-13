"""Apply a router Decision: write inbox rows + (best-effort) inject panes.

Separated from `router.classify_event` so the routing decision stays a
pure function and the side-effecting "apply" step is the only place that
touches the store and tmux.

`apply` branches on `decision.action`:

  DROP       no-op (`DeliveryReport(skipped=True)`)
  SLASH      `_apply_slash`: dispatch via `feishu/slash.dispatch` →
             reply is `str` or `dict` (interactive cards). dict →
             `chat.send_card`, str → `chat.send_text`. Pane never
             touched, no LLM runs.
  BROADCAST  same as ROUTE but targets are all non-sender agents
  ROUTE      per-target: `_write_inbox` (always; flock-serialised) +
             `_inject_to_pane` (best-effort; skipped when `wake.is_rate_limited`
             returns True so the inbox row stays the canonical record).

Returns a `DeliveryReport` so callers can log / surface partial-success
without inspecting hand-rolled tuples. Lists in the report:
  written / injected / failed_inject / rate_limited (per agent),
  skipped (DROP), slash_reply (SLASH text-form replies only).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable
import inspect

from eduflow.agents import adapter_for_agent as _default_adapter_for_agent
from eduflow.agents import identity as _identity
from eduflow.feishu import chat as _chat
from eduflow.feishu import lark as _lark
from eduflow.feishu import slash as _slash
from eduflow.feishu.router import Action, Decision
from eduflow.runtime import config, tmux, wake, lifecycle
from eduflow.store import local_facts, message_delivery
from eduflow.util import env_str


@dataclass
class DeliveryReport:
    written: list[str] = field(default_factory=list)        # inbox row landed
    injected: list[str] = field(default_factory=list)       # pane received text
    failed_inject: list[str] = field(default_factory=list)
    rate_limited: list[str] = field(default_factory=list)   # inbox kept, inject skipped
    skipped: bool = False                                    # True iff decision was DROP
    slash_reply: str = ""                                    # set when action=SLASH
    # G0.2 acknowledgement contract.  ``durable_success`` means every
    # canonical target record exists (or a Slash reply was published);
    # pane injection remains explicitly best-effort.
    durable_success: bool = False
    retryable_failure: bool = False
    terminal_failure: bool = False
    failure_reason: str = ""


@dataclass(frozen=True)
class _Deps:
    adapter_for_agent: Callable
    tmux_inject: Callable
    append_message: Callable
    session: str


def _resolve_deps(adapter_lookup, tmux_inject, append_message, session) -> _Deps:
    """Fill in production defaults for any None collaborator."""
    return _Deps(
        adapter_for_agent=adapter_lookup or _default_adapter_for_agent,
        tmux_inject=tmux_inject or tmux.inject,
        append_message=append_message or local_facts.append_message,
        session=session or config.session_name(),
    )


def _runtime_adapter_for_agent(adapter_lookup: Callable, agent: str,
                               runtime_name: str = ""):
    """Best-effort runtime-aware adapter lookup.

    Production uses `agents.adapter_for_agent(agent, runtime_name=...)`, but
    tests and older call sites may still pass a one-arg stub. Accept both.
    """
    if runtime_name:
        try:
            sig = inspect.signature(adapter_lookup)
            if "runtime_name" in sig.parameters:
                return adapter_lookup(agent, runtime_name=runtime_name)
            if len(sig.parameters) >= 2:
                return adapter_lookup(agent, runtime_name)
        except (TypeError, ValueError):
            pass
    return adapter_lookup(agent)


def _append_inbox(agent: str, sender: str, decision: Decision, deps: _Deps):
    """Call either the current or a legacy injected inbox writer.

    Test collaborators and third-party callers predating G0.2 may accept
    only the old three positional arguments.  Production receives the
    exact per-message/per-target idempotency key.
    """
    kwargs = {
        "source_message_id": decision.msg_id,
        "delivery_key": f"feishu:{decision.msg_id}:{agent}",
    }
    try:
        sig = inspect.signature(deps.append_message)
        accepts_kwargs = any(
            param.kind is inspect.Parameter.VAR_KEYWORD
            for param in sig.parameters.values()
        )
        supports_key = accepts_kwargs or "delivery_key" in sig.parameters
    except (TypeError, ValueError):
        supports_key = True
    if supports_key:
        return deps.append_message(agent, sender, decision.text, **kwargs)
    return deps.append_message(agent, sender, decision.text)


def _write_inbox(agent: str, sender: str, decision: Decision,
                 deps: _Deps, report: DeliveryReport) -> str:
    """Returns the local_id on success, "" on failure (failure is
    also logged to the report). The caller threads the local_id into
    the pane-inject wrapper so the agent knows which row to mark
    `eduflow read` after replying."""
    try:
        local_id = _append_inbox(agent, sender, decision, deps)
    except Exception as e:
        print(f"  ⚠️ inbox write failed for {agent}: {e}")
        report.failure_reason = "inbox_write_failed"
        return ""
    try:
        message_delivery.record_target_persisted(decision, agent, str(local_id or ""))
    except Exception as e:
        # The inbox row is idempotent, so retrying safely repairs this
        # missing ledger edge.  Do not ACK until it is auditable.
        print(f"  ⚠️ delivery ledger write failed for {agent}: {e}")
        report.failure_reason = "delivery_ledger_write_failed"
        return ""
    report.written.append(agent)
    return local_id or ""


def _build_wake_args(agent: str, adapter) -> dict:
    """Kwargs for wake_fn: spawn_cmd, init_msg, on_woken.

    Wrapping the lazy-wake setup keeps `_inject_to_pane` focused on its
    actual job (deliver text) and isolates the cross-module wiring
    (lifecycle.pane_env_prefix, identity.init_prompt, status upsert).
    """
    from eduflow.runtime import tunables
    try:
        resolved = config.resolved_agent_config(agent)
        spawn_prefix = lifecycle.pane_spawn_prefix_for_runtime(resolved)
        model = config.agent_model(agent)
    except KeyError:
        spawn_prefix = lifecycle.pane_env_prefix()
        model = env_str("EDUFLOW_DEFAULT_MODEL") or "opus"
    spawn_cmd = f"{spawn_prefix} {adapter.spawn_cmd(agent, model)}"
    return {
        "spawn_cmd": spawn_cmd,
        "init_msg": _identity.init_prompt(agent),
        "timeout_s": float(tunables.tunable("wake.lazy_wake_timeout_s", 30.0)),
        # Flip status from "待命" to "进行中" so `eduflow team` reflects
        # reality once the lazy pane actually wakes up.
        "on_woken": lambda: local_facts.upsert_status(
            agent, "进行中", "responding to first message"),
    }


# Heuristic: if the boss message asks for a summary / report-back / status
# coordinated through manager, workers should also send the result to
# manager (not just `say` to chat) so manager's inbox pings and they can
# follow up. manager's pane doesn't see chat messages — only its own
# inbox + dispatched messages — so without this hint the dispatch +
# summarize loop stalls (boss saw this 2026-05-05 in a Round C dry-run:
# manager dispatched, worker counted, posted to chat, manager never
# learned and never summarized).
_SUMMARY_CUE_TOKENS = (
    "汇总", "汇报", "总结", "报告",
    "summarize", "summary", "report back",
    "manager 跟进", "manager 综合",
)


def _wants_manager_summary(text: str) -> bool:
    low = text.lower()
    return any(tok.lower() in low for tok in _SUMMARY_CUE_TOKENS)


def _compose_inject_text(agent: str, decision: Decision,
                         local_id: str = "") -> str:
    """Prepend a short routing-context header to the chat message before
    injecting it into the agent's pane.

    Without this header, claude treats raw injected text as a normal
    user prompt and replies in-pane (which the boss can't see). The
    hint primes the agent to:
      1. Reply via the correct channel (`eduflow say` for chat-
         originated; `eduflow send` for peer messages).
      2. Mark the inbox row `read` afterward (deliver knows the
         local_id since it just appended the row) so the inbox
         doesn't accumulate unread rows.
      3. If the message hints at manager-summary follow-up, non-
         manager agents are also told to `eduflow send manager`
         so manager's inbox pings — manager's pane is blind to
         chat-only `say` events otherwise."""
    sender = decision.sender or "user"
    read_hint = (
        f" 接单时用 `eduflow read {local_id} --ack accepted_task`；"
        f"返修用 `--ack accepted_revision`；开始执行后可改记"
        f" `--ack started_task`。"
        if local_id else ""
    )
    summary_hint = ""
    if (agent != "manager"
            and _wants_manager_summary(decision.text)):
        summary_hint = (f" 这条似乎需要 manager 汇总，处理完后**额外**"
                        f"发一句 `eduflow send manager {agent} \"<结果>\"` "
                        f"让 manager inbox 知道你的进度。")
    # 简短引导 — 长解释属于 identity.md 的职责，不是每次注入都重复一遍。
    # 关键指示：哪个频道回 + 怎么 mark read（如果 local_id 已知）+ 是否需
    # 要 send manager 让其汇总。具体命令格式 / --to 选择交给 identity 教。
    if sender == "user" or not sender:
        reply_order = (
            "必须先真正发出可见回复，再标记 ACK；不要只 `read --ack`，"
            "不要停在草稿或反问“要不要我发”。"
        )
        hint = (f"[群聊·老板] 用 `eduflow say {agent} \"...\" --to user` "
                f"回群。{reply_order}{summary_hint}{read_hint}")
    else:
        hint = (f"[同事·{sender}] 回 `eduflow send {sender} {agent} "
                f"\"...\"`；要公告到群用 `eduflow say {agent} "
                f"\"...\" --to user`。{read_hint}")
    return f"{hint}\n\n{decision.text}"


def _inject_to_pane(agent: str, decision: Decision,
                    deps: _Deps, wake_fn: Callable | None,
                    local_id: str = "") -> str:
    """Deliver `decision.text` to the agent's pane (wrapped with a
    routing-context hint so the agent posts replies via `eduflow
    say` instead of answering in pane). `local_id` is appended to the
    hint so the agent knows which inbox row to mark read.

    Returns a DeliveryReport field name: 'injected' / 'failed_inject' /
    'rate_limited'.
    """
    window_target = tmux.Target(deps.session, agent)
    target = tmux.preferred_pane_target(window_target)
    try:
        runtime_snap = lifecycle.current_runtime_status(agent)
        try:
            current_runtime = runtime_snap.get("runtime") or config.resolved_agent_config(agent).get("selected_runtime", "inline")
        except KeyError:
            current_runtime = runtime_snap.get("runtime") or "inline"
        adapter = _runtime_adapter_for_agent(
            deps.adapter_for_agent,
            agent,
            str(current_runtime),
        )
        pane_text = tmux.capture_pane(target, lines=80)
        from eduflow.runtime import failure_detector
        switch_reason = failure_detector.detect_failure(
            target, adapter, pane_text=pane_text,
        )
        if switch_reason:
            from eduflow.runtime import failover
            result = failover.execute_fallback_loop(
                agent,
                target,
                str(current_runtime),
                switch_reason,
                trigger="deliver",
            )
            outcome = result["outcome"]
            to_runtime = result["to_runtime"]
            if outcome in {lifecycle.READY, lifecycle.READY_NO_INIT}:
                adapter = _runtime_adapter_for_agent(
                    deps.adapter_for_agent,
                    agent,
                    str(to_runtime),
                )
            elif outcome in {lifecycle.ENV_DRIFT, lifecycle.SMOKE_FAILED,
                             lifecycle.READY_UNPROVEN}:
                # Partial success — message still needs to land. The
                # runtime guard will re-probe next tick.
                adapter = _runtime_adapter_for_agent(
                    deps.adapter_for_agent,
                    agent,
                    str(to_runtime),
                )
                print(f"  ⚠️ {agent} switched {current_runtime} -> {to_runtime} "
                      f"on {switch_reason} but outcome={outcome}; injecting anyway")
            else:
                print(f"  ⚠️ {agent} runtime switch failed on {switch_reason} "
                      f"(best={result['best_outcome']}, attempts={len(result['attempts'])})")
            if outcome != lifecycle.READY and switch_reason == "rate_limit":
                # Best-effort: the message stays in the inbox for the next
                # recovery attempt. Original behavior was to return
                # "rate_limited" when no fallback was available; keep that
                # path for full failures so the inbox row isn't lost.
                if outcome not in {lifecycle.READY, lifecycle.READY_NO_INIT,
                                    lifecycle.ENV_DRIFT, lifecycle.SMOKE_FAILED,
                                    lifecycle.READY_UNPROVEN}:
                    print(f"  ⏸  {agent} rate-limited; inbox row kept, inject skipped")
                    return "rate_limited"
        if wake_fn is not None and not wake.is_ready(target, adapter):
            if not wake_fn(target, adapter, **_build_wake_args(agent, adapter)):
                print(f"  ⚠️ {agent} pane not ready; injecting anyway")
        text = _compose_inject_text(agent, decision, local_id=local_id)
        ok = deps.tmux_inject(target, text, submit_keys=adapter.submit_keys())
    except Exception as e:
        print(f"  ⚠️ inject error for {agent}: {e}")
        return "failed_inject"
    return "injected" if ok else "failed_inject"


def apply(decision: Decision, *,
          adapter_for_agent: Callable | None = None,
          tmux_inject: Callable | None = None,
          append_message: Callable | None = None,
          wake_fn: Callable | None = None,
          session: str | None = None,
          team_agents: list[str] | None = None,
          lazy_agents: frozenset[str] | None = None,
          slash_dispatch: Callable | None = None,
          chat_send: Callable | None = None,
          chat_send_card: Callable | None = None,
          chat_id: str | None = None,
          profile: str | None = None) -> DeliveryReport:
    """Apply `decision`. Side-effects per action:

    DROP       — no-op (skipped=True).
    SLASH      — dispatch via slash registry, post reply to chat as bot.
                 Zero pane touches.
    BROADCAST  — same as ROUTE but targets are all non-sender agents.
    ROUTE      — write inbox row + tmux inject for each target.

    All collaborators are injectable for tests; production defaults read
    from the real modules.
    """
    if decision.is_drop():
        return DeliveryReport(skipped=True)

    deps = _resolve_deps(adapter_for_agent, tmux_inject, append_message, session)

    if decision.action is Action.SLASH:
        return _apply_slash(decision, deps,
                            team_agents=team_agents,
                            lazy_agents=lazy_agents,
                            slash_dispatch=slash_dispatch,
                            chat_send=chat_send,
                            chat_send_card=chat_send_card,
                            chat_id=chat_id,
                            profile=profile)

    sender = decision.sender or "user"
    report = DeliveryReport()
    for agent in decision.targets:
        local_id = _write_inbox(agent, sender, decision, deps, report)
        if not local_id:
            continue
        outcome = _inject_to_pane(agent, decision, deps, wake_fn,
                                   local_id=local_id)
        getattr(report, outcome).append(agent)
    if not decision.targets:
        report.terminal_failure = True
        report.failure_reason = "route_without_target"
    elif len(report.written) == len(decision.targets):
        # Inbox persistence is the durable transport boundary.  A delayed,
        # rate-limited, or failed pane injection leaves the canonical row
        # available for the next agent wake/recovery cycle.
        report.durable_success = True
    else:
        report.retryable_failure = True
        if not report.failure_reason:
            report.failure_reason = "inbox_write_failed"
    return report


def _apply_slash(decision: Decision, deps: _Deps, *,
                 team_agents: list[str] | None,
                 lazy_agents: frozenset[str] | None,
                 slash_dispatch: Callable | None,
                 chat_send: Callable | None,
                 chat_send_card: Callable | None,
                 chat_id: str | None,
                 profile: str | None) -> DeliveryReport:
    """Run slash command at router level (zero LLM) and post reply to chat
    as bot. Pane is never touched.

    Round-79: dispatch may now return a dict (Feishu card schema) — branch
    on type to call chat.send_card instead of chat.send_text. `reply_to`
    only applies to the text path; cards don't support thread-reply.
    """
    report = DeliveryReport()
    try:
        reply = message_delivery.cached_slash_reply(decision.msg_id)
    except Exception as e:
        print(f"  ⚠️ slash reply ledger unavailable for {decision.msg_id}: {e}")
        report.retryable_failure = True
        report.failure_reason = "slash_reply_ledger_unavailable"
        return report

    if reply is None:
        try:
            execution = message_delivery.begin_slash_execution(decision)
        except Exception as e:
            print(f"  ⚠️ slash execution ledger unavailable for {decision.msg_id}: {e}")
            report.retryable_failure = True
            report.failure_reason = "slash_execution_ledger_unavailable"
            return report
        if execution == "recovery_required":
            report.retryable_failure = True
            report.failure_reason = "slash_execution_recovery_required"
            return report
        if execution == "reply_ready":
            reply = message_delivery.cached_slash_reply(decision.msg_id)
        else:
            dispatch = slash_dispatch or _slash.dispatch
            ctx = _slash.SlashContext(
                team_agents=team_agents or config.agent_names(),
                session=deps.session,
                lazy_agents=lazy_agents if lazy_agents is not None else frozenset(),
                sender_id=decision.sender_id,
            )
            try:
                reply = dispatch(decision.text, ctx)
            except Exception as e:
                print(f"  ⚠️ slash dispatch failed for {decision.msg_id}: {e}")
                report.retryable_failure = True
                report.failure_reason = "slash_dispatch_failed"
                return report
            try:
                message_delivery.cache_slash_reply(decision, reply)
            except Exception as e:
                print(f"  ⚠️ slash reply could not be journaled for {decision.msg_id}: {e}")
                report.retryable_failure = True
                report.failure_reason = "slash_reply_journal_failed"
                return report

    if reply is None:
        report.retryable_failure = True
        report.failure_reason = "slash_reply_unavailable"
        return report

    report.slash_reply = reply if isinstance(reply, str) else ""
    chat = chat_id if chat_id is not None else config.chat_id()
    if not chat:
        preview = (reply[:200] if isinstance(reply, str)
                   else str(reply)[:200])
        print(f"  ⚠️ slash reply ready but chat_id unset; reply suppressed:\n{preview}")
        report.retryable_failure = True
        report.failure_reason = "slash_chat_unconfigured"
        return report
    prof = profile if profile is not None else config.lark_profile()
    try:
        publication = message_delivery.begin_slash_publication(decision)
    except Exception as e:
        print(f"  ⚠️ slash publication ledger unavailable for {decision.msg_id}: {e}")
        report.retryable_failure = True
        report.failure_reason = "slash_publication_ledger_unavailable"
        return report
    if publication == "published":
        report.durable_success = True
        return report
    if publication != "publish":
        # A process may have died after reserving publication but before the
        # Feishu result was durably recorded. Retrying would risk posting a
        # second control-plane response, so let the delivery ledger send it
        # through the auditable dead-letter/manual-recovery path instead.
        report.retryable_failure = True
        report.failure_reason = "slash_publication_recovery_required"
        return report
    uses_default_transport = (
        chat_send_card is None if isinstance(reply, dict) else chat_send is None
    )
    try:
        if isinstance(reply, dict):
            send_card = chat_send_card or _chat.send_card
            result = send_card(chat, reply, profile=prof, as_user=False)
        else:
            send_text = chat_send or _chat.send_text
            result = send_text(chat, reply, profile=prof, as_user=False,
                               reply_to=decision.msg_id)
    except Exception as e:
        print(f"  ⚠️ slash reply for {decision.msg_id} raised: {e}")
        if isinstance(e, TimeoutError):
            report.retryable_failure = True
            report.failure_reason = "slash_publication_recovery_required"
            return report
        try:
            message_delivery.release_slash_publication_for_retry(
                decision, "slash_reply_not_posted")
        except Exception:
            report.failure_reason = "slash_publication_recovery_required"
            report.retryable_failure = True
            return report
        report.retryable_failure = True
        report.failure_reason = "slash_reply_not_posted"
        return report
    if result is None:
        # chat.send_text/send_card already logged the underlying failure.
        # Surface a one-line warning here so router.log makes it obvious
        # the slash dispatch ran but the reply never landed in chat.
        print(f"  ⚠️ slash dispatched OK but chat reply for {decision.msg_id} failed to post")
        if uses_default_transport and _lark.last_failure_kind() == "ambiguous":
            report.retryable_failure = True
            report.failure_reason = "slash_publication_recovery_required"
            return report
        try:
            message_delivery.release_slash_publication_for_retry(
                decision, "slash_reply_not_posted")
        except Exception:
            report.failure_reason = "slash_publication_recovery_required"
            report.retryable_failure = True
            return report
        report.retryable_failure = True
        report.failure_reason = "slash_reply_not_posted"
        return report
    try:
        publication_id = ""
        if isinstance(result, dict):
            publication_id = str(result.get("message_id") or "")
        message_delivery.mark_slash_published(decision, publication_id)
    except Exception as e:
        print(f"  ⚠️ slash publication audit failed for {decision.msg_id}: {e}")
        report.retryable_failure = True
        report.failure_reason = "slash_publication_recovery_required"
        return report
    report.durable_success = True
    return report
