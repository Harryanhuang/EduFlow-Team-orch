"""Feishu event-subscribe loop: NDJSON line iterator → routed delivery.

The pure event-loop function `process_lines` reads NDJSON lines from an
iterator (fed by `lark-cli event +subscribe --compact` stdout in
production, or a fixture list in tests), parses each into a normalised
event dict, classifies it, and applies the decision.

Returns a tally of (handled, dropped) so callers can log heartbeat.
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from typing import Callable, Iterable

from eduflow.feishu.deliver import DeliveryReport, apply
from eduflow.feishu.router import Decision, classify_event
from eduflow.runtime import human_takeover
from eduflow.store import message_delivery


@dataclass
class LoopStats:
    handled: int = 0
    dropped: int = 0
    drops_by_reason: Counter = field(default_factory=Counter)
    seen_msg_ids: set[str] = field(default_factory=set)


def _normalise(raw: dict) -> dict:
    """Normalize a lark-cli event payload to the flat shape classify_event wants.

    Two shapes seen in the wild:

    * Modern (lark-cli 1.0.21+ with --compact): top-level flat dict —
      `{chat_id, content, sender_id, message_id, message_type, type, ...}`
      where `content` is either a plain string or a JSON-encoded
      `{"text": "..."}`.
    * Legacy / non-compact: Feishu webhook shape wrapped in `{event: {...}}`
      with nested `message: {chat_id, content, ...}` and
      `sender: {sender_id: {open_id: ...}}`. The original rebuild only
      handled this; round 3 smoke proved live lark-cli has switched to
      the flat shape.

    Handle both. For each field, prefer the legacy nested location
    if present (so old fixtures keep working) then fall back to the
    flat top-level field.
    """
    # Unwrap if the payload is webhook-style with .event
    if "event" in raw and isinstance(raw["event"], dict):
        ev = dict(raw["event"])
    else:
        ev = dict(raw)
    msg = ev.get("message") or {}
    sender = ev.get("sender") or {}

    msg_type = (msg.get("message_type")
                or ev.get("message_type")
                or ev.get("msg_type", "text"))

    # Content: legacy puts it under msg.content, modern at ev.content.
    # In either form it might be JSON-encoded ({"text": "..."} for text,
    # {"image_key": "..."} for image, {"file_key": ..., "file_name": ...}
    # for file) or plain text.
    content = msg.get("content") if msg else ev.get("content")
    text = _extract_text(content, msg_type) or ev.get("text", "")

    # sender_type identifies bot vs human. Modern lark-cli payload has
    # `sender_type: "user" | "app"` flat at top; webhook-shape and
    # chat-messages-list both put it inside `sender.sender_type` /
    # `sender.id_type`. Needed for bot-self detection so manager's
    # own cards don't loop back into manager's inbox via catchup
    # (host_smoke 2026-05-06: 7 forward loops before this caught).
    sender_type = (sender.get("sender_type")
                   or sender.get("id_type")
                   or ev.get("sender_type", ""))
    return {
        "message_id": msg.get("message_id") or ev.get("message_id", ""),
        "chat_id": msg.get("chat_id") or ev.get("chat_id", ""),
        "sender_id": (sender.get("sender_id", {}).get("open_id")
                      or sender.get("id")
                      or ev.get("sender_id", "")),
        "sender_type": sender_type,
        "text": text,
        "msg_type": msg_type,
        "create_time": msg.get("create_time") or ev.get("create_time", ""),
    }


def _extract_text(content, msg_type: str) -> str:
    """Reduce a Feishu message content payload to a plain-text representation
    classify_event can route on.

    - text: returns the literal "text" field (or the raw string if not JSON).
    - image: returns "[image: image_key=<key>]" so the message routes
      instead of getting dropped as "empty".
    - file: returns "[file: <file_name>]" or "[file: file_key=<key>]".
    - audio / sticker / unknown: returns "[<msg_type>]" placeholder.

    Workers receiving these placeholders can use the message_id to fetch
    the actual binary via `lark-cli im +messages-resources-download` if
    they need it; the router's job is just to deliver the route + placeholder
    so the worker pane is aware something arrived.
    """
    if not isinstance(content, str):
        return ""
    try:
        data = json.loads(content) or {}
    except json.JSONDecodeError:
        # Plain string content (legacy variant)
        return content
    if msg_type == "image":
        key = data.get("image_key", "")
        return f"[image: image_key={key}]" if key else "[image]"
    if msg_type == "file":
        name = data.get("file_name") or ""
        key = data.get("file_key", "")
        if name and key:
            return f"[file: {name} (file_key={key})]"
        if name:
            return f"[file: {name}]"
        return f"[file: file_key={key}]" if key else "[file]"
    if msg_type == "audio":
        key = data.get("file_key", "")
        return f"[audio: file_key={key}]" if key else "[audio]"
    if msg_type == "sticker":
        key = data.get("file_key", "")
        return f"[sticker: {key}]" if key else "[sticker]"
    if msg_type == "post":
        # 飞书富文本: 图片 + 文字混合. content 形如:
        #   {"title": "...", "content": [[el, el], [el, ...], ...]}
        # 每个 element 是 {"tag": "text"|"img"|"a"|"at"|"file"|..., ...}
        # 把所有段落拼成多行文本, 图片 / 文件等非文字 element 用 placeholder
        # 表达, 这样 LLM 能看到"老板发了一张图 + 这段文字"的全貌.
        return _post_to_text(data)
    # Default: text or unknown — try common .text field, then .content,
    # then leave empty so callers can fall back to ev.get("text").
    return data.get("text") or data.get("content") or ""


def _post_to_text(data: dict) -> str:
    """Flatten a Feishu `post` (rich text) message body into plain text.

    Mixed image/file + text messages come through as `msg_type=post`;
    `_extract_text` delegates here. Each paragraph in `content` is a
    list of inline elements (text / img / a / at / file / mention).
    Returns one line per paragraph, with non-text elements rendered
    as `[image: ...]` / `[file: ...]` / `<text> (<href>)` placeholders
    so workers can either react to the text+image combo verbally or
    fetch the binary via `lark-cli im +messages-resources-download
    <message_id>` if they need the actual bytes.
    """
    title = (data.get("title") or "").strip()
    paragraphs = data.get("content") or []
    if not isinstance(paragraphs, list):
        return title
    lines: list[str] = []
    for para in paragraphs:
        if not isinstance(para, list):
            continue
        bits: list[str] = []
        for el in para:
            if not isinstance(el, dict):
                continue
            tag = el.get("tag", "")
            if tag == "text" or tag == "md":
                bits.append(str(el.get("text", "")))
            elif tag == "img":
                key = el.get("image_key", "")
                bits.append(f"[image: image_key={key}]" if key else "[image]")
            elif tag == "media":
                key = el.get("file_key") or el.get("image_key", "")
                bits.append(f"[media: {key}]" if key else "[media]")
            elif tag == "file":
                name = el.get("file_name") or ""
                key = el.get("file_key", "")
                if name and key:
                    bits.append(f"[file: {name} (file_key={key})]")
                elif name:
                    bits.append(f"[file: {name}]")
                else:
                    bits.append(f"[file: file_key={key}]" if key else "[file]")
            elif tag == "a":
                t = el.get("text") or el.get("href", "")
                href = el.get("href", "")
                bits.append(f"{t} ({href})" if t and href else (t or href))
            elif tag == "at":
                uid = el.get("user_id", "") or el.get("user_name", "")
                bits.append(f"@{uid}" if uid else "@?")
            else:
                # 未知 tag — 透传成 placeholder 别丢
                txt = el.get("text") or ""
                bits.append(txt or f"[{tag}]")
        line = "".join(bits).strip()
        if line:
            lines.append(line)
    body = "\n".join(lines).strip()
    if title and body:
        return f"{title}\n\n{body}"
    return title or body


def _record_drop(stats: LoopStats, reason: str) -> None:
    stats.dropped += 1
    stats.drops_by_reason[reason] += 1


def _advance_progress(decision: Decision, stats: LoopStats,
                      on_progress: Callable | None) -> bool:
    """Commit the router cursor before placing an event in dedup state."""
    if on_progress is None:
        return True
    try:
        on_progress(decision, stats)
    except Exception as e:
        print(f"  ⚠️ on_progress callback failed on {decision.msg_id}: {e}")
        return False
    return True


def _remember_handled(decision: Decision, stats: LoopStats) -> None:
    if decision.msg_id:
        stats.seen_msg_ids.add(decision.msg_id)
    stats.handled += 1


def _prepare_delivery(decision: Decision) -> dict | None:
    """Journal an event before it can cause a side effect."""
    try:
        return message_delivery.prepare(decision)
    except Exception as e:
        print(f"  ⚠️ delivery ledger unavailable for {decision.msg_id}: {e}")
        return None


def _finish_ack_only(decision: Decision, *, status: str,
                     on_progress: Callable | None, stats: LoopStats) -> None:
    """Advance cursor/seen without repeating an already durable delivery."""
    if not _advance_progress(decision, stats, on_progress):
        _record_drop(stats, "ack_progress_failed")
        return
    if status == "delivered":
        try:
            message_delivery.record_acknowledged(decision)
        except Exception as e:
            print(f"  ⚠️ delivery ACK audit failed for {decision.msg_id}: {e}")
    _remember_handled(decision, stats)


def _apply_decision(decision: Decision, *, apply_fn: Callable,
                    on_progress: Callable | None, stats: LoopStats,
                    force_claim: bool = False,
                    restart_recovery: bool = False) -> None:
    """Apply one non-drop decision and accept it only after a durable ACK."""
    try:
        if message_delivery.automation_hold_active():
            _record_drop(stats, "automation_hold")
            return
    except Exception as e:
        print(f"  ⚠️ automation hold check failed for {decision.msg_id}: {e}")
        _record_drop(stats, "delivery_ledger_error")
        return
    prepared = _prepare_delivery(decision)
    if prepared is None:
        _record_drop(stats, "delivery_ledger_error")
        return
    previous_status = str(prepared.get("status") or "")
    if previous_status in {"delivered", "terminal", "dead_letter"}:
        _finish_ack_only(
            decision,
            status=previous_status,
            on_progress=on_progress,
            stats=stats,
        )
        return
    try:
        takeover_generation = human_takeover.ensure_automation_allowed()
    except (human_takeover.AutomationBlocked, human_takeover.StaleGeneration):
        try:
            message_delivery.defer_for_human_takeover(decision)
        except Exception as e:
            print(f"  ⚠️ takeover deferral failed for {decision.msg_id}: {e}")
            _record_drop(stats, "delivery_ledger_error")
            return
        _record_drop(stats, "human_takeover")
        return
    try:
        lease_token = message_delivery.claim_delivery(
            decision,
            force=force_claim,
            break_existing_lease=restart_recovery,
        )
    except Exception as e:
        print(f"  ⚠️ delivery lease unavailable for {decision.msg_id}: {e}")
        _record_drop(stats, "delivery_ledger_error")
        return
    if not lease_token:
        _record_drop(stats, "delivery_inflight")
        return
    try:
        # Re-check after the lease is acquired: an administrator can enter
        # takeover in the small window between the first guard and apply.
        human_takeover.ensure_automation_allowed(
            expected_generation=takeover_generation,
        )
    except (human_takeover.AutomationBlocked, human_takeover.StaleGeneration):
        try:
            message_delivery.defer_for_human_takeover(decision)
        except Exception as e:
            print(f"  ⚠️ takeover deferral failed for {decision.msg_id}: {e}")
            _record_drop(stats, "delivery_ledger_error")
            return
        _record_drop(stats, "human_takeover")
        return
    try:
        report = apply_fn(decision)
    except Exception as e:
        print(f"  ⚠️ apply_fn raised on {decision.msg_id}: {e}")
        try:
            message_delivery.record_retryable_failure(
                decision, "apply_error", lease_token=lease_token)
        except Exception:
            pass
        _record_drop(stats, "apply_error")
        return

    # Cursor/seen advance only from the explicit DeliveryReport contract.
    # A legacy ``None`` callback is unproven delivery and must fail closed.
    if not isinstance(report, DeliveryReport):
        report = DeliveryReport(
            retryable_failure=True,
            failure_reason="invalid_delivery_report",
        )
    durable_success = report.durable_success
    retryable_failure = report.retryable_failure
    terminal_failure = report.terminal_failure
    failure_reason = report.failure_reason or "delivery_unconfirmed"
    dead_letter = False

    if retryable_failure or not (durable_success or terminal_failure):
        try:
            retry_state = message_delivery.record_retryable_failure(
                decision, failure_reason, lease_token=lease_token)
        except Exception as e:
            print(f"  ⚠️ delivery retry state failed for {decision.msg_id}: {e}")
            _record_drop(stats, "delivery_ledger_error")
            return
        if retry_state.get("lease_lost"):
            _record_drop(stats, "delivery_inflight")
            return
        if not retry_state.get("dead_letter"):
            _record_drop(stats, "delivery_retryable")
            return
        dead_letter = True
        terminal_failure = True
        durable_success = False
        failure_reason = "retry_limit_exceeded"
        try:
            human_takeover.enter(
                reason=f"message delivery retry limit exceeded: {retry_state.get('failure_reason') or 'unknown'}",
                source="message_delivery",
                actor="system",
            )
        except Exception as e:
            print(f"  ⚠️ could not enter human takeover for {decision.msg_id}: {e}")
            try:
                message_delivery.enter_automation_hold(
                    "human_takeover_persistence_failed",
                )
            except Exception as hold_error:
                print(f"  ⚠️ emergency automation hold persistence failed: {hold_error}")
            _record_drop(stats, "automation_hold")
            return

    if terminal_failure and not dead_letter:
        try:
            message_delivery.record_terminal(decision, failure_reason)
        except Exception as e:
            print(f"  ⚠️ terminal delivery audit failed for {decision.msg_id}: {e}")
            _record_drop(stats, "delivery_ledger_error")
            return

    if durable_success:
        try:
            delivered = message_delivery.record_delivered(
                decision, lease_token=lease_token)
        except Exception as e:
            print(f"  ⚠️ durable delivery state failed for {decision.msg_id}: {e}")
            _record_drop(stats, "delivery_ledger_error")
            return
        if not delivered:
            _record_drop(stats, "delivery_inflight")
            return

    # A cursor failure keeps the canonical message replayable.  Both the
    # inbox key and cached Slash reply make that replay safe. A completed
    # delivery moves to ``delivered`` first, so startup recovery can retry
    # only this ACK phase without sending another reply.
    if not _advance_progress(decision, stats, on_progress):
        _record_drop(stats, "ack_progress_failed")
        return

    if durable_success:
        try:
            message_delivery.record_acknowledged(decision)
        except Exception as e:
            # The cursor is already durable; preserve liveness but make the
            # audit gap explicit in the router log.
            print(f"  ⚠️ delivery ACK audit failed for {decision.msg_id}: {e}")
    _remember_handled(decision, stats)


def process_lines(lines: Iterable[str], *,
                  team_agents: list[str],
                  chat_id: str = "",
                  bot_id: str = "",
                  default_target: str = "manager",
                  apply_fn: Callable = apply,
                  on_progress: Callable | None = None,
                  on_line_received: Callable | None = None,
                  seen_msg_ids: set[str] | None = None) -> LoopStats:
    """Run the subscribe loop over `lines` (one Feishu event JSON each).

    Designed to be exited by exhausting the iterator.  The production
    daemon wraps a never-ending Popen stdout iterator; tests pass a list.

    `seen_msg_ids` lets the caller seed the dedup set across calls /
    process restarts. Used by the router to persist seen ids to
    state/router.seen.json so catchup-after-restart doesn't re-apply
    messages that were already handled before the restart (host_smoke
    2026-05-06: same /tmux manager card forwarded into manager inbox
    every ~3.5min as router self-restarted).
    """
    stats = LoopStats()
    if seen_msg_ids is not None:
        stats.seen_msg_ids = seen_msg_ids
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        # Subscribe-aliveness ping: fire on every non-empty stdout line,
        # before classification. Even DROPs (bot_self / dedup / bad_json)
        # prove the lark-cli WebSocket is still emitting; only by counting
        # raw lines, not 'successfully handled events', can the watchdog
        # tell quiet-but-alive apart from silent-stall. Caught 2026-05-08
        # host smoke: chats with mostly bot self-talk would trip the 600s
        # stall threshold even though subscribe was healthy.
        if on_line_received is not None:
            try:
                on_line_received()
            except Exception:
                pass  # never let a callback bug kill the subscribe loop
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            _record_drop(stats, "bad_json")
            continue
        event = _normalise(payload)
        decision = classify_event(
            event,
            team_agents=team_agents,
            chat_id=chat_id,
            bot_id=bot_id,
            seen_msg_ids=stats.seen_msg_ids,
            default_target=default_target,
        )
        if decision.is_drop():
            # Dedup drops were already durably accepted by an earlier pass;
            # do not regress the cursor with their older timestamp.  Other
            # classifier drops are terminal outcomes and must advance the
            # cursor/seen state so catchup cannot resurrect them forever.
            if decision.reason not in {"dedup", "duplicate message_id"}:
                if _prepare_delivery(decision):
                    try:
                        message_delivery.record_terminal(
                            decision, decision.reason or "terminal_drop")
                    except Exception as e:
                        print(f"  ⚠️ terminal drop audit failed on {decision.msg_id}: {e}")
                    else:
                        if _advance_progress(decision, stats, on_progress):
                            if decision.msg_id:
                                stats.seen_msg_ids.add(decision.msg_id)
            _record_drop(stats, decision.reason or "drop")
            continue
        _apply_decision(
            decision,
            apply_fn=apply_fn,
            on_progress=on_progress,
            stats=stats,
            force_claim=False,
        )
    return stats


def process_pending_decisions(decisions: Iterable[Decision], *,
                              apply_fn: Callable = apply,
                              on_progress: Callable | None = None,
                              seen_msg_ids: set[str] | None = None,
                              restart_recovery: bool = False) -> LoopStats:
    """Replay journaled deliveries before the live subscription begins.

    These decisions were classified and persisted during an earlier router
    run, so replay bypasses live-event classification and its ``seen``
    check.  This is what protects a fresh deployment's first failed event:
    there may be no catchup cursor yet, but the delivery ledger still has
    the exact decision to resume.
    """
    stats = LoopStats()
    if seen_msg_ids is not None:
        stats.seen_msg_ids = seen_msg_ids
    for decision in decisions:
        _apply_decision(
            decision,
            apply_fn=apply_fn,
            on_progress=on_progress,
            stats=stats,
            force_claim=True,
            restart_recovery=restart_recovery,
        )
    return stats


def process_pending_acknowledgements(decisions: Iterable[Decision], *,
                                     on_progress: Callable | None = None,
                                     seen_msg_ids: set[str] | None = None) -> LoopStats:
    """Recover cursor/seen ACKs without re-running delivery side effects."""
    stats = LoopStats()
    if seen_msg_ids is not None:
        stats.seen_msg_ids = seen_msg_ids
    for decision in decisions:
        status = message_delivery.status(decision.msg_id)
        if status not in {"delivered", "terminal", "dead_letter"}:
            continue
        _finish_ack_only(
            decision,
            status=status,
            on_progress=on_progress,
            stats=stats,
        )
    return stats
