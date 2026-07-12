"""Phase 4 — wake-failure ALERT path (rev 2).

Plan 2026-07-01 §设计三:
    wake 超过阈值或失败 → 发 ALERT

`commands/send.py`'s wake_if_dormant path can fail three ways, each
mapped to a `_FAIL_KIND_*` constant:
  - `ready_marker_timeout`: CLI never showed the ready marker.
  - `no_pane`: tmux window doesn't exist (lazy pane or 之前 fire 了)。
  - `spawn_failed`: tmux respawn / spawn returned False.

All three mean the sender's message landed in the inbox but the
warm-agent's CLI never came back up.

# 模板选择 per kind (调后)

    ready_marker_timeout  → red    (严重,pane 还在但 CLI 没起来)
    no_pane               → yellow (中度,pane 被 fire 过)
    spawn_failed          → red    (严重,连 spawn 都失败)

# Channel (调后)

The default `chat_id=""` arg now resolves via
`config.supervisor_chat_id()` so ALERTs go to the supervisor / 维修
channel instead of the main 老板 channel by default.  Pass an
explicit `chat_id` to override (Phase 4 P4-A choice).

# Sender (调后)

The card is sent on behalf of `manager`, not `auto_ops`.  Reason:
the validator in `cards_v2_schema` allows both to send ALERT, but
manager is the formal ops owner — when the boss asks "why did you
warn me," they want a face, not a bot.  auto_ops is preserved as
audit-log author (`append_log("auto_ops", "alert", ...)`).

# 30-min dedup (调后)

`(target_agent, failure_kind)` pairs that fired within the last
30 minutes return `deduped=True` without re-sending the card.
Audit log still records each attempt so the boss can grep history.
"""
from __future__ import annotations

import time
from typing import Callable

from eduflow.feishu import chat as feishu_chat
from eduflow.runtime import config
from eduflow.store import local_facts


_FAIL_KIND_READY_TIMEOUT = "ready_marker_timeout"
_FAIL_KIND_NO_PANE = "no_pane"
_FAIL_KIND_SPAWN_FAILED = "spawn_failed"

_ALL_KINDS = (
    _FAIL_KIND_READY_TIMEOUT,
    _FAIL_KIND_NO_PANE,
    _FAIL_KIND_SPAWN_FAILED,
)

# 调后: kind → 模板颜色 (red / yellow 双轨)
_TEMPLATE_BY_KIND: dict[str, str] = {
    _FAIL_KIND_READY_TIMEOUT: "red",
    _FAIL_KIND_NO_PANE: "yellow",
    _FAIL_KIND_SPAWN_FAILED: "red",
}

# 调后: 30 分钟 dedup 窗口 (默认 1800s,可通过 tunable 覆盖)
_DEFAULT_DEDUP_WINDOW_S = 1800

# 调后: no_chat_id 不再 silent — 返回 errno 标识 "ERR_NO_CHAT_ID"
ERR_NO_CHAT_ID = "ERR_NO_CHAT_ID"
ERR_SEND_FAILED = "ERR_SEND_FAILED"


def _normalise_kind(kind: str) -> str:
    if kind in _ALL_KINDS:
        return kind
    return _FAIL_KIND_SPAWN_FAILED


def _recent_fired(agent: str, kind: str, *, now_s: float,
                  window_s: float = _DEFAULT_DEDUP_WINDOW_S) -> bool:
    """30 分钟 dedup: 扫描 auto_ops 日志,在窗口内已有同 (agent, kind)
    的 alert 记录则返回 True。日志扫的代价低(默认 limit=50)。"""
    import re as _re
    pattern = _re.compile(
        _re.escape(f"({_normalise_kind(kind)}"),
    )
    for row in local_facts.list_logs("auto_ops", limit=80):
        if row.get("type") != "alert":
            continue
        content = str(row.get("content") or "")
        if f"wake 失败: {agent}" not in content:
            continue
        if not pattern.search(content):
            continue
        created_at_ms = int(row.get("created_at") or 0)
        if created_at_ms <= 0:
            continue
        age_s = now_s - (created_at_ms / 1000.0)
        if 0 <= age_s <= window_s:
            return True
    return False




def build_wake_failure_card(
    *,
    target_agent: str,
    failure_kind: str,
    wake_timeout_s: float,
    chat_id: str = "",
    now_s: float | None = None,
) -> dict:
    """Feishu v2 ALERT card for the wake failure.

    字段顺序按"调用方最先需要看的"重排:
      1. 异常类型 (是什么错)
      2. 当前状态 (现在怎样)
      3. 影响范围 (谁受影响)
      4. 已自动处理 (系统做了什么)
      5. 下一步 (30 分钟 dedup 复述,如启用了 dedup)
      6. 需要谁处理 / 需要老板介入

    模板颜色按 `_TEMPLATE_BY_KIND` 选;调后 no_pane → yellow,
    其它两个 → red。
    """
    kind = _normalise_kind(failure_kind)
    template = _TEMPLATE_BY_KIND.get(kind, "red")
    timestamp = time.strftime(
        "%Y-%m-%d %H:%M:%S 北京时间", time.localtime(now_s or time.time()),
    )
    next_step = (
        "30 分钟内同 (agent, kind) 不重发 ALERT,"
        " 如仍 ready_marker_timeout 才会再发一次"
        if True else ""  # dedup 一律开启的 v1 行为
    )
    body_lines = [
        f"**异常类型**：温备 agent wake 失败 ({kind}) @ {timestamp}",
        f"**当前状态**：{target_agent} pane 状态待 runtime_guard 二次探测",
        f"**影响范围**：{target_agent} 当前不能消费 inbox,新消息只进 inbox 不进 pane",
        "**已自动处理**：已写入 local_facts.append_log + agent_residency.touch_sleep 触发重复 sweep",
        f"**下一步**：{next_step}",
        "**需要谁处理**：manager (派单给 worker_builder 维修)",
        "**需要老板介入**：否",
    ]
    title = f"[ALERT][wake] manager · wake 失败: {target_agent}"
    return {
        "schema": "2.0",
        "header": {
            "title": {"content": title, "tag": "plain_text"},
            "template": template,
        },
        "body": {"elements": [
            {"tag": "markdown", "content": "\n".join(body_lines)},
        ]},
    }


def fire_wake_failure_alert(
    *,
    target_agent: str,
    failure_kind: str,
    wake_timeout_s: float,
    chat_id: str = "",
    send_card: Callable | None = None,
    now: float | None = None,
    dedup: bool = True,
) -> dict:
    """Fire the wake-failure ALERT.

    调后三件:
      * default chat_id = supervisor_chat_id() (而不是 main)
      * sender = manager(走 cards 路径),audit log author = auto_ops
      * no_chat_id 时返回 {"errno": ERR_NO_CHAT_ID, ...} 而不是 silent

    Returns a structured result with:
      - kind, template
      - chat_id, delivered, errno, deduped
      - title (给上游日志用)
    Side effects (always):
      - local_facts.append_log("auto_ops", "alert", ...)
      - agent_residency.touch_sleep(target_agent)
    Side effects (only when delivered):
      - feishu_chat.send_card(chat_id, card)
    """
    from eduflow.store import agent_residency

    when = float(now if now is not None else time.time())
    kind = _normalise_kind(failure_kind)

    result: dict = {
        "agent": target_agent,
        "kind": kind,
        "template": _TEMPLATE_BY_KIND.get(kind, "red"),
        "chat_id": "",
        "delivered": False,
        "deduped": False,
        "errno": "",
        "title": "",
    }

    if dedup and _recent_fired(target_agent, kind, now_s=when):
        result["deduped"] = True
        # Audit log keeps the dedup attempt so the boss can grep history.
        local_facts.append_log(
            "auto_ops", "alert",
            f"wake 失败(dedup): {target_agent} ({kind})",
            ref=f"wake:{target_agent}:{int(when)}",
            created_at_ms=int(when * 1000),
        )
        return result

    card = build_wake_failure_card(
        target_agent=target_agent,
        failure_kind=kind,
        wake_timeout_s=wake_timeout_s,
        chat_id=chat_id,
        now_s=when,
    )
    result["title"] = card["header"]["title"]["content"]

    # Audit log (auto_ops author; P4-A choice — auto_ops 留痕,manager 当 sender)
    local_facts.append_log(
        "auto_ops", "alert",
        f"wake 失败: {target_agent} ({kind}, timeout={wake_timeout_s:.0f}s)",
        ref=f"wake:{target_agent}:{int(when)}",
        created_at_ms=int(when * 1000),
    )

    try:
        agent_residency.touch_sleep(target_agent, when=when)
    except Exception:
        pass

    # Channel resolution: explicit chat_id > supervisor > main
    target_chat = chat_id
    if not target_chat:
        try:
            target_chat = config.supervisor_chat_id() or ""
        except Exception:
            target_chat = ""
        if not target_chat:
            try:
                target_chat = config.chat_id() or ""
            except Exception:
                target_chat = ""
    result["chat_id"] = target_chat
    if not target_chat:
        result["errno"] = ERR_NO_CHAT_ID
        return result
    try:
        _send = send_card or feishu_chat.send_card
        chat_result = _send(target_chat, card)
        result["delivered"] = bool(chat_result)
        if not result["delivered"]:
            result["errno"] = ERR_SEND_FAILED
    except Exception as e:
        result["errno"] = f"{ERR_SEND_FAILED}:{e}"
    return result
