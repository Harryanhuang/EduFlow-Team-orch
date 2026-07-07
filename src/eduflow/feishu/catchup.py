"""Router catchup-on-restart.

When the router daemon dies (Ctrl-C, OOM, host reboot), the live
`event +subscribe` stream resumes from the moment we re-attach — any
messages the boss sent during the gap are silently lost.

This module bridges that gap:

* `read_cursor` / `write_cursor` persist the last successfully-classified
  message into `state_dir/router.cursor`.
* `pending_lines` calls `chat-messages-list`, filters to messages newer
  than the cursor, and emits NDJSON lines in the same shape the live
  subscribe loop produces — so `subscribe.process_lines` replays them
  without caring whether the source was a Popen pipe or this catchup.

Cursor advances on every classified Decision (route or drop), so a
crash mid-apply means we re-encounter the message and lean on
process_lines' dedup set to skip duplicates.

Two response shapes seen in the wild from `lark-cli im +chat-messages-list`
Specifically:
  - older / fixture: `{body: {content: "..."}, create_time: "<epoch-ms>"}`
  - lark-cli 1.0.21 live: `{content: "...", create_time: "2026-05-03 18:53"}`
The shape-normalisation helpers below accept both.
"""
from __future__ import annotations

import datetime as _dt
import json
from typing import Callable, Iterable

from eduflow.feishu import chat as _chat
from eduflow.feishu.router import Decision
from eduflow.runtime import paths
from eduflow.util import env_str, read_json, warn, write_json


# ── cursor persistence ─────────────────────────────────────────


def read_cursor() -> dict:
    """Return the persisted cursor or {} (missing / corrupt / blank file)."""
    try:
        return read_json(paths.router_cursor_file(), {})
    except json.JSONDecodeError:
        return {}


def write_cursor(message_id: str, create_time: str) -> None:
    """Persist the last-seen message marker. No-op if either field is empty.

    Also stores `create_time_ms`, the epoch-ms reading of `create_time`
    taken now. lark-cli can render minute strings in process-local time,
    so the string alone is ambiguous across TZ changes.
    """
    if not message_id or not create_time:
        return
    write_json(paths.router_cursor_file(),
               {"message_id": message_id, "create_time": str(create_time),
                "create_time_ms": _to_epoch_ms(create_time)})


def record_decision(decision: Decision) -> None:
    """Advance cursor from a classified Decision (drop or route)."""
    write_cursor(decision.msg_id, decision.create_time)


# ── replay ────────────────────────────────────────────────────


def _extract_content(fei_msg: dict) -> str:
    """Pick content out of either lark-cli response shape:

    Live (lark-cli 1.0.21+): `{"content": "<text>"}`
    Older / fixtures: `{"body": {"content": "<text>"}}`

    Falls back to "" if neither is present."""
    body = fei_msg.get("body") or {}
    return body.get("content") or fei_msg.get("content") or ""


def _msg_to_event_line(fei_msg: dict) -> str:
    """Convert a chat-messages-list row into one NDJSON line matching
    `lark-cli event +subscribe --compact` shape.

    Carries sender.id_type into the event so subscribe._normalise can
    surface sender_type to classify_event — without it bot-self
    detection misses bot-sent cards on the catchup path and forwards
    manager's own ack cards back into manager's inbox every restart
    (host_smoke 2026-05-06: 7 loops in one session)."""
    sender = fei_msg.get("sender") or {}
    payload = {
        "event": {
            "message": {
                "message_id": fei_msg.get("message_id", ""),
                "chat_id": fei_msg.get("chat_id", ""),
                "message_type": fei_msg.get("msg_type", "text"),
                "content": _extract_content(fei_msg),
                "create_time": fei_msg.get("create_time", ""),
            },
            "sender": {
                "sender_id": {"open_id": sender.get("id", "")},
                "sender_type": sender.get("sender_type")
                                or sender.get("id_type", ""),
            },
        }
    }
    return json.dumps(payload, ensure_ascii=False)


def _to_epoch_ms(create_time: object) -> int:
    """Coerce a chat-messages-list create_time into epoch ms.

    Accepts:
      - int / numeric str: passed through (already epoch ms)
      - "YYYY-MM-DD HH:MM" or "YYYY-MM-DD HH:MM:SS" (lark-cli 1.0.21
        live shape): parsed as local time → epoch ms
    Returns 0 when uninterpretable so `_newer_than` treats the row
    as older than any non-zero cursor (i.e. "skip safely")."""
    if not create_time:
        return 0
    s = str(create_time).strip()
    if s.isdigit():
        return int(s)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return int(_dt.datetime.strptime(s, fmt).timestamp() * 1000)
        except ValueError:
            continue
    return 0


_DEFAULT_CATCHUP_LOOKBACK_MS = 120_000


def _newer_than(messages: Iterable[dict], cursor_create_time: str, *,
                cursor_ms: int = 0,
                lookback_ms: int = _DEFAULT_CATCHUP_LOOKBACK_MS) -> list[dict]:
    """Filter `messages` to those at-or-after `cursor minute - lookback`.

    Two precision realms collide here. Cursor is set from the LIVE event
    `create_time` (lark-cli WebSocket → millisecond precision string).
    `messages` come from `chat-messages-list` REST (minute precision
    string like "2026-05-06 14:08", parses to the floor of that minute).
    A strict `>` or even bare `>=` comparison loses the minute the
    cursor is in: cursor 14:08:32.107 vs REST 14:08:00 → REST < cursor
    → every message that shares the cursor's minute is dropped.

    Floor the cutoff to the minute boundary so REST messages in the same
    minute as the cursor are kept, then step back by `lookback_ms` so an
    out-of-order message slightly older than the high-water cursor is not
    filtered out forever. Re-applied messages are harmless: persisted
    router.seen and process-level dedup drop them later.

    Bad/missing create_time (parses to 0) gets dropped — never include
    rows we can't timestamp, even when there's no cursor.
    """
    raw_cutoff = cursor_ms or _to_epoch_ms(cursor_create_time)
    minute_floor = (raw_cutoff // 60_000) * 60_000
    cutoff = minute_floor - max(0, lookback_ms)
    def keep(m: dict) -> bool:
        ts = _to_epoch_ms(m.get("create_time"))
        return ts > 0 and ts >= cutoff
    ordered = list(messages)
    ordered.reverse()
    fresh = [m for m in ordered if keep(m)]
    fresh.sort(key=lambda m: _to_epoch_ms(m.get("create_time")))
    return fresh


def pending_lines(chat_id: str, *,
                  profile: str = "",
                  page_size: int = 50,
                  list_fn: Callable | None = None,
                  meta: dict | None = None) -> list[str]:
    """Return NDJSON lines for messages newer than the saved cursor.

    Oldest-first so process_lines applies them in chronological order.
    `list_fn` is injectable for tests; in production it goes through
    `feishu.chat.list_recent`. `meta` gets `dropped_stale` when backlog
    is capped.
    """
    cursor = read_cursor()
    cursor_ct = str(cursor.get("create_time") or "")
    try:
        cursor_ms = int(cursor.get("create_time_ms") or 0)
    except (TypeError, ValueError):
        cursor_ms = 0
    # Fresh deploy (no cursor): don't replay arbitrary chat history.
    # Otherwise a fresh `eduflow up` would re-fire every message in
    # the recent 50 — including dispatches from a previous team that
    # would now have manager re-doing tasks the boss already cleared.
    # The live subscribe stream picks up from "now" forward; the first
    # real event writes a cursor so subsequent restarts correctly catch
    # up just the gap between cursor and now.
    if not cursor_ct:
        return []
    if list_fn is None:
        # Honor send_as cascade so bot-only deployments don't trip
        # `need_user_authorization` from `chat-messages-list --as user`
        # (chat.list_recent's historical default). Mirrors `say`'s resolver:
        # legacy env EDUFLOW_LARK_SEND_AS first, then tunables
        # `feishu.send_as`, default "user" (preserve pre-tunables behaviour
        # where bare deployments without env had user-OAuth ready).
        legacy = env_str("EDUFLOW_LARK_SEND_AS").lower()
        if legacy:
            as_value = legacy
        else:
            from eduflow.runtime import tunables
            as_value = str(tunables.tunable("feishu.send_as", "user")).lower()
        as_user = as_value != "bot"
        def list_fn():
            return _chat.list_recent(chat_id, profile=profile,
                                     page_size=page_size, as_user=as_user)
    raw = list_fn()
    if raw is None:
        warn("⚠️ catchup: 拉历史消息失败（鉴权/代理？）—— 本次补漏跳过；"
             "bot-only 部署请确认 send_as=bot 或用户 OAuth 就绪")
        return []
    fresh = _newer_than(raw, cursor_ct, cursor_ms=cursor_ms,
                        lookback_ms=_catchup_lookback_ms())
    cap = _catchup_max_messages()
    if cap > 0 and len(fresh) > cap:
        dropped = len(fresh) - cap
        fresh = fresh[-cap:]
        newest = fresh[-1]
        write_cursor(newest.get("message_id", ""),
                     str(newest.get("create_time", "")))
        warn(f"⚠️ catchup backlog exceeded cap {cap}: skipping {dropped} "
             f"stale message(s), replaying most recent {cap}, cursor seeded forward")
        if meta is not None:
            meta["dropped_stale"] = dropped
    return [_msg_to_event_line(m) for m in fresh]


def _catchup_lookback_ms() -> int:
    try:
        from eduflow.runtime import tunables
        return int(tunables.tunable("router.catchup_lookback_ms",
                                    _DEFAULT_CATCHUP_LOOKBACK_MS))
    except Exception:
        return _DEFAULT_CATCHUP_LOOKBACK_MS


_DEFAULT_CATCHUP_MAX_MESSAGES = 30


def _catchup_max_messages() -> int:
    try:
        from eduflow.runtime import tunables
        return int(tunables.tunable("router.catchup_max_messages",
                                    _DEFAULT_CATCHUP_MAX_MESSAGES))
    except Exception:
        return _DEFAULT_CATCHUP_MAX_MESSAGES


def recent_window_lines(chat_id: str, *, window_seconds: int = 30,
                       profile: str = "",
                       list_fn: Callable | None = None) -> list[str]:
    """T-137: backfill the last N seconds of chat history, ignoring cursor.

    Used by router to close the 5s respawn window where events can be
    dropped. The regular `pending_lines` only returns messages newer
    than the cursor, but if the router died right after writing a
    cursor and a new message arrived during the gap, the cursor
    advance silently swallowed it. This function pulls the last
    window_seconds of history regardless of cursor, so respawn cycles
    can recover events that arrived during downtime.
    """
    if list_fn is None:
        from eduflow.feishu import chat as _chat
        legacy = env_str("EDUFLOW_LARK_SEND_AS").lower()
        if legacy:
            as_value = legacy
        else:
            from eduflow.runtime import tunables
            as_value = str(tunables.tunable("feishu.send_as", "user")).lower()
        as_user = as_value != "bot"
        def list_fn():
            return _chat.list_recent(chat_id, profile=profile,
                                     page_size=50, as_user=as_user)
    msgs = list_fn() or []
    import time as _time
    cutoff_ms = int(_time.time() * 1000) - int(window_seconds) * 1000
    fresh = []
    for m in msgs:
        ct = m.get("create_time") or ""
        try:
            ct_ms = int(ct)
        except (TypeError, ValueError):
            continue
        if ct_ms >= cutoff_ms:
            fresh.append(m)
    return [_msg_to_event_line(m) for m in fresh]
