"""Local file-backed fact store for EduFlow.

One source of truth on a host for:
- inbox       (per-agent message queue, JSON)
- status      (latest per-agent status snapshot, JSON)
- heartbeats  (last-seen-active timestamp per agent, JSON)
- log         (append-only event log, JSONL)

Sister module: `store/memory.py` holds per-agent **durable
memory** — curated entries an agent re-reads on wake (via identity init
prompt). Logs are audit trail (every action; verbose; not re-read);
memory is the curated subset.

All paths derive from `$EDUFLOW_STATE_DIR` re-read on every call so tests
get isolation by setting the env, no monkey-patching required. All JSON
writes go through `util.write_json` (atomic tmp+rename via flock).

`list_logs` shares the same JSONL parser as `memory.list_recent` — both
go through `util.read_jsonl`, which silently drops corrupt lines
left by a half-written previous crash so the file stays forward-readable.

Originally pulled from the old `eduflow.storage.local_facts` (~187 LOC).
Each public function corresponds to one CLI surface: `eduflow send` →
`append_message`, `inbox` → `list_messages`, `read` → `mark_read`,
`status` → `upsert_status` / `get_status`, `team` → `list_all_statuses`
+ `all_heartbeats`, `log`/`workspace` → `append_log` / `list_logs`.
"""
from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

from eduflow.runtime.paths import facts_dir as _facts_dir
from eduflow.util import flock, now_ms, read_json, read_jsonl, write_json


def _inbox_file() -> Path:
    return _facts_dir() / "inbox.json"


def _status_file() -> Path:
    return _facts_dir() / "status.json"


def _log_file() -> Path:
    return _facts_dir() / "logs.jsonl"


def _new_id(prefix: str) -> str:
    return f"{prefix}_{now_ms()}_{uuid.uuid4().hex[:10]}"


def _locked():
    return flock(_facts_dir() / ".facts.lock")


_WEAK_STATUS_TASKS = {
    "ready",
    "initializing",
}

_IDLE_STATUSES = {
    "待命",
    "空闲",
    "ready",
    "idle",
}

_DIRECT_VISIBILITY_AGENTS = {
    "worker_course",
    "review_course",
    "worker_builder",
    "worker_qbank",
    "auto_ops",
}

_PROCESS_VISIBILITY_STALE_MS = 10 * 60 * 1000
_AUTO_OPS_VISIBILITY_STALE_MS = 30 * 60 * 1000


def _is_weak_idle_surface(status: str, task: str) -> bool:
    normalized_task = " ".join(str(task or "").strip().split()).lower()
    return (
        str(status or "") in _IDLE_STATUSES
        or normalized_task in _WEAK_STATUS_TASKS
        or "lazy: cli starts on first message" in normalized_task
    )


def provider_quota_block_evidence(agent: str, *, after: int = 0) -> dict | None:
    """Return recent manager evidence that a provider quota blocks an agent.

    This is a status projection input, not an agent action. It must never
    claim the agent accepted, started, or completed work; it only surfaces a
    credible runtime blocker that explains why direct process signals stopped.
    """
    agent = str(agent or "").strip()
    if agent not in {"worker_builder", "worker_course", "worker_qbank"}:
        return None
    for row in reversed(list_logs("manager", limit=30)):
        created_at = int(row.get("created_at") or 0)
        if created_at < after:
            continue
        if str(row.get("type") or "") not in {"say", "task", "task_completed"}:
            continue
        content = str(row.get("content") or "")
        lowered = content.lower()
        if agent not in content:
            continue
        if "qoder" not in lowered:
            continue
        if not any(marker in lowered for marker in ("credits exhausted", "forbidden", "code=112")):
            continue
        if not any(marker in lowered for marker in ("无法执行", "cannot execute", "provider-level", "额度")):
            continue
        return dict(row)
    return None


def runtime_guard_block_evidence(agent: str) -> dict | None:
    """Return runtime-guard evidence that an agent cannot consume work.

    Runtime guard is an operator/runtime signal, not agent progress. Surfacing
    it prevents a broken pane from looking like a normal unread inbox item.
    """
    agent = str(agent or "").strip()
    if not agent:
        return None
    data = read_json(_facts_dir() / "runtime-guard-state.json", {"agents": {}})
    row = dict(data.get("agents", {}).get(agent) or {})
    if not row:
        return None
    if not (bool(row.get("escalation_needed")) or bool(row.get("needs_manager_action"))):
        return None
    return row


def is_high_priority(value: str) -> bool:
    normalized = str(value or "").strip().lower()
    return normalized in {"高", "high", "urgent", "p0", "p1"}


def _runtime_watchdog_recovered() -> bool:
    """Return True when router and watchdog are both currently alive.

    Imported lazily to keep local_facts usable in small test fixtures and to
    avoid making status projection depend on runtime modules unless needed.
    """
    try:
        from eduflow.runtime import watchdog as runtime_watchdog
    except Exception:
        return False
    specs = {
        spec.name: spec
        for spec in runtime_watchdog.all_known_specs()
        if spec.name in {"router", "watchdog"}
    }
    for name in ("router", "watchdog"):
        spec = specs.get(name)
        if spec is None or not spec.pid_file.exists() or not runtime_watchdog.is_alive(spec):
            return False
    return True


def _runtime_repair_message_resolved_by_watchdog_recovery(msg: dict) -> bool:
    content = str(msg.get("content") or "")
    lowered = content.lower()
    if not any(marker in lowered for marker in ("watchdog", "router")):
        return False
    if not any(marker in content for marker in ("修复", "恢复", "排查", "重启", "兜底保障", "未启动", "缺失", "no pid file")):
        return False
    return _runtime_watchdog_recovered() or _runtime_repair_message_resolved_by_later_closeout(msg)


def _runtime_repair_message_resolved_by_later_closeout(msg: dict) -> bool:
    created_at = int(msg.get("created_at") or 0)
    for agent in ("auto_ops", "manager", "worker_builder"):
        for row in list_logs(agent, limit=50):
            if int(row.get("created_at") or 0) < created_at:
                continue
            if str(row.get("type") or "") not in {"say", "task_completed", "task"}:
                continue
            content = str(row.get("content") or "")
            lowered = content.lower()
            if (
                ("watchdog 已恢复" in content or "watchdog 修复闭环" in content)
                and ("health 全绿" in content or "alive" in lowered or "pid" in lowered)
            ):
                return True
    return False


def _builder_runtime_course_message_resolved_by_later_closeout(msg: dict) -> bool:
    if str(msg.get("to") or "") != "worker_builder":
        return False
    content = str(msg.get("content") or "")
    lowered = content.lower()
    if not any(marker in lowered for marker in ("worker_course", "qoder", "runtime", "stale")):
        return False
    if not any(marker in content for marker in ("纠偏", "排查", "阻断", "验证", "修复", "respawn")):
        return False
    created_at = int(msg.get("created_at") or 0)
    for agent in ("manager", "worker_course", "review_course"):
        for row in list_logs(agent, limit=50):
            if int(row.get("created_at") or 0) < created_at:
                continue
            if str(row.get("type") or "") not in {"say", "task_completed"}:
                continue
            row_content = str(row.get("content") or "")
            row_lowered = row_content.lower()
            if (
                "closeout" in row_lowered
                or "pass" in row_lowered
                or "已交付" in row_content
                or "已完成并交给 manager" in row_content
            ):
                return True
    return False


# ── inbox ─────────────────────────────────────────────────────────────


def append_message(to: str, frm: str, content: str, *,
                   priority: str = "中", task_id: str = "",
                   delivery_state: str = "delivered_to_inbox") -> str:
    """Append a message to the inbox; return its local id."""
    with _locked():
        path = _inbox_file()
        data = read_json(path, {"messages": []})
        now = now_ms()
        normalized = str(content or "").strip()
        # Minimal backlog-collapsing for repeated high-priority nudges.
        # Keep only the newest unread "current truth / status packet" style
        # message for a recipient instead of letting near-duplicate operator
        # nudges pile up forever.
        if is_high_priority(priority) and normalized:
            lowered = normalized.lower()
            collapse_markers = (
                "三行状态包",
                "最小状态包",
                "只看当前真相",
                "不要补旧账",
                "当前最大协作缺口",
                "当前真实状态",
                "batch 6",
            )
            if any(marker in normalized or marker in lowered for marker in collapse_markers):
                for msg in data.get("messages", []):
                    if (
                        msg.get("to") == to
                        and not msg.get("read")
                        and is_high_priority(str(msg.get("priority") or ""))
                    ):
                        old = str(msg.get("content") or "")
                        old_low = old.lower()
                        if any(marker in old or marker in old_low for marker in collapse_markers):
                            msg["read"] = True
                            msg["read_at"] = now
        local_id = _new_id("msg")
        data.setdefault("messages", []).append({
            "local_id": local_id,
            "to": to,
            "from": frm,
            "content": str(content or ""),
            "priority": priority,
            "task_id": task_id,
            "created_at": now,
            "delivery_state": str(delivery_state or "delivered_to_inbox"),
            "read": False,
            "read_at": None,
            "ack_state": "pending",
            "ack_kind": "",
            "ack_at": None,
            "ack_details": {},
            "action_started_at": None,
            "failed_reason": "",
        })
        write_json(path, data)
        return local_id


def get_message(local_id: str) -> dict | None:
    data = read_json(_inbox_file(), {"messages": []})
    for msg in data.get("messages", []):
        if msg.get("local_id") == local_id:
            return dict(msg)
    return None


def latest_unread_message(agent: str) -> dict | None:
    """Return the freshest unread inbox message for `agent`, if any."""
    rows = list_messages(agent, unread_only=True)
    if not rows:
        return None
    return rows[-1]


def list_messages(agent: str, *, unread_only: bool = False) -> list[dict]:
    data = read_json(_inbox_file(), {"messages": []})
    rows = [m for m in data.get("messages", []) if m.get("to") == agent]
    if unread_only:
        rows = [m for m in rows if not m.get("read")]
    return sorted(rows, key=lambda m: m.get("created_at", 0))


def list_all_messages() -> list[dict]:
    data = read_json(_inbox_file(), {"messages": []})
    return sorted(data.get("messages", []), key=lambda m: m.get("created_at", 0))


def _latest_unread_message_after(agent: str, updated_at: int) -> dict | None:
    rows = [
        m for m in list_messages(agent, unread_only=True)
        if int(m.get("created_at") or 0) >= updated_at
        and not _runtime_repair_message_resolved_by_watchdog_recovery(m)
    ]
    if not rows:
        return None
    return rows[-1]


def _message_has_local_visibility_ref(agent: str, local_id: str) -> bool:
    ref = f"inbox:{local_id}"
    visible_kinds = {
        "ack",
        "qbank_followup",
        "worker_course_stage_ack",
        "worker_course_started",
        "review_course_stage_ack",
        "review_course_started",
        "worker_builder_stage_ack",
        "worker_builder_started",
        "worker_stage_ack",
        "worker_started",
    }
    for row in list_logs(agent, limit=20):
        if str(row.get("ref") or "") != ref:
            continue
        if str(row.get("type") or "") in visible_kinds:
            return True
    return False


def _latest_unread_high_message_after(agent: str, updated_at: int) -> dict | None:
    rows = [
        m for m in list_messages(agent, unread_only=True)
        if int(m.get("created_at") or 0) >= updated_at
        and is_high_priority(str(m.get("priority") or ""))
        and not _message_has_local_visibility_ref(agent, str(m.get("local_id") or ""))
        and not _runtime_repair_message_resolved_by_watchdog_recovery(m)
    ]
    if not rows:
        return None
    return rows[-1]


def _agent_has_direct_visibility_after(agent: str, created_at: int) -> bool:
    for row in list_logs(agent, limit=12):
        if int(row.get("created_at") or 0) < created_at:
            continue
        kind = str(row.get("type") or "")
        if kind in {
            "say",
            "worker_course_started",
            "review_course_started",
            "worker_builder_started",
            "worker_started",
            "qbank_followup",
            "task_completed",
        }:
            return True
    return False


def _visibility_keywords(text: str) -> set[str]:
    lowered = str(text or "").lower()
    keywords: set[str] = set()
    markers = {
        "qbank": (
            "qbank", "题库", "去重", "dedup", "manifest", "验证",
            "renumber", "collision", "canonical", "round2", "true_dup",
            "id_collision", "v3",
        ),
        "review": ("review", "复核", "verdict", "gate"),
        "business": ("business studies", "0450", "t-10"),
        "economics": ("economics", "0455"),
        "physics": ("physics", "0625"),
        "chemistry": ("chemistry", "0620"),
        "accounting": ("accounting", "0452"),
        "biology": ("biology", "0610"),
        "runtime": (
            "router", "watchdog", "hermes", "runtime", "pidlock",
            "respawn", "path", "cli", "qoder", "health", "tmux",
        ),
    }
    for key, tokens in markers.items():
        if any(token in lowered for token in tokens):
            keywords.add(key)
    return keywords


def _visibility_tokens(text: str) -> set[str]:
    value = str(text or "").lower()
    tokens: set[str] = set()
    for pattern in (
        r"\bt-\d+\b",
        r"\bbatch\s*\d+\b",
        r"\b\d{4}\b",
        r"\b\d+\.\d+\b",
    ):
        tokens.update(re.findall(pattern, value))
    return {" ".join(token.split()) for token in tokens if token.strip()}


def _agent_has_related_visibility_after(agent: str, created_at: int, content: str) -> bool:
    expected = _visibility_keywords(content)
    expected_tokens = _visibility_tokens(content)
    if not expected and not expected_tokens:
        return _agent_has_direct_visibility_after(agent, created_at)
    if "runtime" in expected:
        required = {"runtime"}
    elif "qbank" in expected:
        required = {"qbank"}
    else:
        required = expected
    since = max(created_at - 1000, 0)
    for row in list_logs(agent, limit=12):
        if int(row.get("created_at") or 0) < since:
            continue
        kind = str(row.get("type") or "")
        if kind not in {
            "say",
            "worker_course_started",
            "review_course_started",
            "worker_builder_started",
            "worker_started",
            "qbank_followup",
            "task_completed",
            "task",
        }:
            continue
        row_content = str(row.get("content") or "")
        if required & _visibility_keywords(row_content):
            return True
        if expected_tokens and expected_tokens & _visibility_tokens(row_content):
            return True
    return False


def _agent_status_has_related_visibility_after(agent: str, created_at: int, content: str) -> bool:
    expected = _visibility_keywords(content)
    expected_tokens = _visibility_tokens(content)
    for status in (get_raw_status(agent) or {}, get_status(agent) or {}):
        updated_at = int(status.get("updated_at") or 0)
        if updated_at < max(created_at - 1000, 0):
            continue
        if str(status.get("status") or "") not in {"已接单", "进行中", "已交付", "已完成", "空闲", "待命"}:
            continue
        status_text = f"{status.get('task') or ''} {status.get('blocker') or ''}"
        if not status_text.strip():
            continue
        if not expected and not expected_tokens:
            return True
        if expected & _visibility_keywords(status_text):
            return True
        if expected_tokens and expected_tokens & _visibility_tokens(status_text):
            return True
    return False


def _message_has_sender_visibility(msg: dict) -> bool:
    """Worker reports to manager can be proved by the worker's own surface.

    A high-priority completion/process report sent *to* manager should not
    make manager look stalled just because manager did not ACK the report.
    The report is externally credible when the sending agent also emitted a
    related say/log at the same point in time.
    """
    if str(msg.get("to") or "") != "manager":
        return False
    sender = str(msg.get("from") or "")
    if sender not in _DIRECT_VISIBILITY_AGENTS:
        return False
    content = str(msg.get("content") or "")
    if not content.strip():
        return False
    created_at = int(msg.get("created_at") or 0)
    since = max(created_at - 1000, 0)
    return (
        _agent_has_related_visibility_after(sender, since, content)
        or _agent_status_has_related_visibility_after(sender, since, content)
    )


def _message_superseded_by_external_course_verdict(msg: dict) -> bool:
    """Suppress stale worker_course read-unacked prompts after real verdicts.

    Some course repairs are reported by review_course/manager rather than the
    worker's own `say` path. That should not keep the live surface stuck at
    "已读待确认" after a later PASS/closeout proves the task moved on.
    """
    if str(msg.get("to") or "") != "worker_course":
        return False
    content = str(msg.get("content") or "")
    tokens = _subject_tokens_from_text(content)
    if not tokens:
        return False
    created_at = int(msg.get("created_at") or 0)
    since = max(created_at - 1000, 0)
    for agent in ("review_course", "manager"):
        for row in list_logs(agent, limit=30):
            row_created = int(row.get("created_at") or 0)
            if row_created < since:
                continue
            if str(row.get("type") or "") not in {"say", "task_completed"}:
                continue
            row_content = str(row.get("content") or "")
            lowered = row_content.lower()
            has_terminal_signal = (
                "pass" in lowered
                or "closeout" in lowered
                or "闭环" in row_content
                or "可 closeout" in row_content
            )
            if not has_terminal_signal:
                continue
            if any(token in row_content or token.lower() in lowered for token in tokens):
                return True
    return False


def _latest_read_unacked_high_message_after(agent: str, updated_at: int) -> dict | None:
    rows = []
    for msg in list_messages(agent):
        created_at = int(msg.get("created_at") or 0)
        if created_at < updated_at:
            continue
        if not is_high_priority(str(msg.get("priority") or "")):
            continue
        if not bool(msg.get("read")):
            continue
        if str(msg.get("ack_state") or "pending") in {
            "agent_acknowledged",
            "action_started",
            "completed",
            "reconciled",
        }:
            continue
        if _runtime_repair_message_resolved_by_watchdog_recovery(msg):
            continue
        if _builder_runtime_course_message_resolved_by_later_closeout(msg):
            continue
        if _message_has_sender_visibility(msg):
            continue
        if _agent_has_related_visibility_after(agent, created_at, str(msg.get("content") or "")):
            continue
        if _message_superseded_by_external_course_verdict(msg):
            continue
        rows.append(msg)
    if not rows:
        return None
    return rows[-1]


def mark_read(local_id: str) -> bool:
    with _locked():
        path = _inbox_file()
        data = read_json(path, {"messages": []})
        for msg in data.get("messages", []):
            if msg.get("local_id") == local_id:
                msg["read"] = True
                if not msg.get("read_at"):
                    msg["read_at"] = now_ms()
                write_json(path, data)
                return True
    return False


def update_message_delivery(local_id: str, delivery_state: str) -> bool:
    normalized = str(delivery_state or "").strip()
    if not normalized:
        return False
    with _locked():
        path = _inbox_file()
        data = read_json(path, {"messages": []})
        for msg in data.get("messages", []):
            if msg.get("local_id") != local_id:
                continue
            msg["delivery_state"] = normalized
            write_json(path, data)
            return True
    return False


def record_message_ack(local_id: str, kind: str, **details) -> bool:
    """Record an explicit agent ACK/action state for one inbox message.

    `read` only says the message was consumed from the inbox UI. This helper
    records the stronger state needed by unattended production: accepted,
    started, or accepted a revision with enough context to audit the handoff.
    """
    normalized = str(kind or "").strip()
    if not normalized:
        return False
    visibility_msg: dict | None = None
    with _locked():
        path = _inbox_file()
        data = read_json(path, {"messages": []})
        now = now_ms()
        for msg in data.get("messages", []):
            if msg.get("local_id") != local_id:
                continue
            msg["ack_kind"] = normalized
            msg["ack_at"] = now
            msg["ack_details"] = {
                k: v for k, v in details.items()
                if v not in (None, "", [], {})
            }
            if normalized in {"started_task", "action_started"}:
                msg["ack_state"] = "action_started"
                msg["action_started_at"] = now
            elif normalized == "completed":
                msg["ack_state"] = "completed"
            elif normalized == "reconciled":
                msg["ack_state"] = "reconciled"
            elif normalized == "failed_due_to_runtime":
                msg["ack_state"] = "failed_due_to_runtime"
                if details.get("reason"):
                    msg["failed_reason"] = str(details.get("reason"))
            else:
                msg["ack_state"] = "agent_acknowledged"
            visibility_msg = dict(msg)
            write_json(path, data)
            break
    if visibility_msg is None:
        return False
    _sync_explicit_ack_visibility(visibility_msg, normalized, visibility_msg.get("ack_at") or now_ms())
    return True


def _sync_explicit_ack_visibility(msg: dict, kind: str, now: int) -> None:
    """Mirror an explicit inbox ACK into the lightweight status surfaces.

    `eduflow read --ack ...` is the first trustworthy signal that the
    agent actually saw the task. Once that happens, leaving status at a
    stale old task (or generic `ready`) makes the live surface look dead.
    """
    agent = str(msg.get("to") or "").strip()
    local_id = str(msg.get("local_id") or "").strip()
    content = str(msg.get("content") or "")
    if not agent or not local_id:
        return
    touch_heartbeat(agent)
    if agent == "auto_ops":
        record_auto_ops_min_ack(agent, local_id, content)
        return
    if agent == "worker_qbank":
        record_worker_qbank_followup(
            agent,
            local_id,
            content,
            started=kind in {"started_task", "action_started"},
        )
        return
    if agent in {"worker_course", "review_course", "worker_builder"}:
        record_worker_stage_ack(
            agent,
            local_id,
            content,
            started=kind in {"started_task", "action_started"},
        )
        return
    if kind == "completed":
        upsert_status(agent, "已完成", f"已完成：{content[:120]}" if content else "已完成：当前高优任务")
        append_log(agent, "ack", f"完成 ACK：{content[:160]}", ref=f"inbox:{local_id}")
        return
    if kind == "reconciled":
        upsert_status(agent, "已对账", f"已对账：{content[:120]}" if content else "已对账：当前高优任务")
        append_log(agent, "ack", f"对账 ACK：{content[:160]}", ref=f"inbox:{local_id}")
        return
    if kind not in {"accepted_task", "accepted_revision", "started_task", "action_started"}:
        return
    task = _task_from_ack(agent, content, started=kind in {"started_task", "action_started"})
    upsert_status(
        agent,
        "进行中" if kind in {"started_task", "action_started"} else "已接单",
        task,
    )
    ref = f"inbox:{local_id}"
    latest = list_logs(agent, limit=1)
    if latest:
        row = latest[-1]
        if (
            str(row.get("type") or "") == "ack"
            and str(row.get("ref") or "") == ref
        ):
            return
    append_log(agent, "ack", f"显式 ACK：{task}", ref=ref)


def _task_from_ack(agent: str, content: str, *, started: bool) -> str:
    normalized = " ".join(str(content or "").strip().split())
    prefix = "已开始处理" if started else "已接单"
    if normalized:
        return f"{prefix}：{normalized[:120]}"
    return f"{prefix}：{agent} 当前高优任务"


def mark_all_read(agent: str, *, keep_last_unread: int = 0) -> int:
    """Mark unread messages for `agent` as read and return count changed.

    `keep_last_unread=1` is useful for collapsing historical backlog while
    preserving the newest current instruction for the agent to act on.
    """
    with _locked():
        path = _inbox_file()
        data = read_json(path, {"messages": []})
        unread = [
            m for m in data.get("messages", [])
            if m.get("to") == agent and not m.get("read")
        ]
        unread = sorted(unread, key=lambda m: m.get("created_at", 0))
        to_mark = unread[:-keep_last_unread] if keep_last_unread > 0 else unread
        if not to_mark:
            return 0
        now = now_ms()
        changed = 0
        ids = {m.get("local_id") for m in to_mark}
        for msg in data.get("messages", []):
            if msg.get("local_id") in ids and not msg.get("read"):
                msg["read"] = True
                msg["read_at"] = now
                changed += 1
        if changed:
            write_json(path, data)
        return changed


def record_auto_ops_min_ack(agent: str, local_id: str, content: str) -> None:
    """Persist the smallest visible ACK footprint for auto_ops-like watchers.

    This is intentionally lightweight: one status row, one heartbeat, one
    workspace fact. It does not claim the task is solved; it only makes
    "I received the current high-priority supervision task and I'm on watch"
    visible immediately.
    """
    if not str(agent or "").strip() or not str(local_id or "").strip():
        return
    normalized = " ".join(str(content or "").strip().split())
    task = "盯盘中：已收到当前高优监督任务"
    if normalized:
        task = f"盯盘中：{normalized[:120]}"
    upsert_status(agent, "进行中", task)
    touch_heartbeat(agent)
    ref = f"inbox:{local_id}"
    latest = list_logs(agent, limit=1)
    if latest:
        row = latest[-1]
        if (
            str(row.get("type") or "") == "ack"
            and str(row.get("ref") or "") == ref
        ):
            return
    append_log(
        agent,
        "ack",
        f"最小 ACK：已收到当前高优监督任务，先盯当前主线，再继续值班。{task}",
        ref=ref,
    )


def record_worker_qbank_followup(
    agent: str,
    local_id: str,
    content: str,
    *,
    started: bool = False,
) -> None:
    """Persist a minimal visible follow-up footprint for qbank lane."""
    if not str(agent or "").strip() or not str(local_id or "").strip():
        return
    normalized = " ".join(str(content or "").strip().split())
    task = "题库校验已接单：已收到当前批次任务"
    if normalized:
        task = f"{'题库校验跟进中' if started else '题库校验已接单'}：{normalized[:120]}"
    upsert_status(agent, "进行中" if started else "已接单", task)
    touch_heartbeat(agent)
    ref = f"inbox:{local_id}"
    latest = list_logs(agent, limit=1)
    if latest:
        row = latest[-1]
        if (
            str(row.get("type") or "") == "qbank_followup"
            and str(row.get("ref") or "") == ref
        ):
            return
    append_log(
        agent,
        "qbank_followup",
        (
            "过程跟进：已开始基于最新批次校验题库可用性。"
            if started
            else "最小跟进：已收到当前批次 qbank follow-up，等待继续处理。"
        ) + task,
        ref=ref,
    )


def record_worker_stage_ack(
    agent: str,
    local_id: str,
    content: str,
    *,
    started: bool = False,
) -> None:
    """Persist a minimal visible footprint for normal worker/reviewer lanes."""
    if not str(agent or "").strip() or not str(local_id or "").strip():
        return
    normalized = " ".join(str(content or "").strip().split())
    if agent == "worker_course":
        kind = "worker_course_started" if started else "worker_course_stage_ack"
        prefix = "课程主线开始处理" if started else "课程主线已接单"
        detail = "当前学科/批次任务开始推进" if started else "已收到当前学科/批次任务"
    elif agent == "review_course":
        kind = "review_course_started" if started else "review_course_stage_ack"
        prefix = "课程 review 开始处理" if started else "课程 review 已接单"
        detail = "当前 review 任务开始推进" if started else "已收到当前 review 任务"
    elif agent == "worker_builder":
        kind = "worker_builder_started" if started else "worker_builder_stage_ack"
        prefix = "builder 开始处理" if started else "builder 已接单"
        detail = "经验沉淀/模板沉淀任务开始推进" if started else "已收到经验沉淀/模板沉淀任务"
    elif agent == "worker_qbank":
        kind = "qbank_followup"
        prefix = "题库校验跟进中" if started else "题库校验已接单"
        detail = "当前批次 qbank 校验任务开始推进" if started else "已收到当前批次 qbank 校验任务"
    else:
        kind = "worker_started" if started else "worker_stage_ack"
        prefix = "worker 开始处理" if started else "worker 已接单"
        detail = "当前任务开始推进" if started else "已收到当前任务"
    task = f"{prefix}：{detail}"
    if normalized:
        task = f"{prefix}：{normalized[:120]}"
    upsert_status(agent, "进行中" if started else "已接单", task)
    touch_heartbeat(agent)
    ref = f"inbox:{local_id}"
    latest = list_logs(agent, limit=1)
    if latest:
        row = latest[-1]
        if (
            str(row.get("type") or "") == kind
            and str(row.get("ref") or "") == ref
        ):
            return
    append_log(
        agent,
        kind,
        f"{'开始处理' if started else '最小阶段 ACK'}：{task}",
        ref=ref,
    )


# ── status ────────────────────────────────────────────────────────────


def upsert_status(agent: str, status: str, task: str, *, blocker: str = "") -> None:
    with _locked():
        path = _status_file()
        data = read_json(path, {"agents": {}})
        data.setdefault("agents", {})[agent] = {
            "agent": agent,
            "status": status,
            "task": task,
            "blocker": blocker,
            "updated_at": now_ms(),
        }
        write_json(path, data)


def _derive_status_from_log(row: dict, *, fallback_status: str) -> tuple[str, str] | None:
    agent = str(row.get("agent") or "")
    kind = str(row.get("type") or "")
    content = str(row.get("content") or "").strip()
    if not content:
        return None
    lowered = content.lower()
    if kind in {"worker_course_stage_ack", "review_course_stage_ack", "worker_builder_stage_ack"}:
        return ("已接单", content)
    if kind in {"worker_course_started", "review_course_started", "worker_builder_started"}:
        return ("进行中", content)
    if kind == "qbank_followup":
        if "已接单" in content:
            return ("已接单", content)
        return ("进行中", content)
    if kind == "task_completed":
        return ("已交付", content)
    if (
        "已完成并交给 manager" in content
        or "已完成并交给manager" in content
        or "已完成并交付" in content
        or "已交付" in content
        or "ready for review" in lowered
        or "sending to review_course" in lowered
        or "submitted for review" in lowered
        or "submitted to review" in lowered
        or "交给 review_course" in content
        or "交给manager" in content
        or "交给 manager" in content
        or "complete." in lowered
        or " complete:" in lowered
        or lowered.endswith(" complete")
    ):
        return ("已交付", content)
    if "已开始处理" in content or "正在执行" in content or "复核中" in content:
        return ("进行中", content)
    if "待命" in content or "保持待命" in content or "盯盘待命" in content:
        return ("待命", content)
    if any(token in content for token in ("开始复核", "已开始复核", "开始生产", "已开始生产", "正在分析", "正在处理中", "当前卡在", "处理中但卡在")):
        return ("进行中", content)
    if (
        agent in {"worker_course", "review_course", "worker_builder", "worker_qbank", "auto_ops"}
        and (
            "已接单" in content
            or "收到最新指令" in content
            or "收到 Business Studies" in content
        )
    ):
        return ("已接单", content)
    if kind in {"ack", "decision"}:
        return (fallback_status, content)
    if kind == "say":
        return (fallback_status, content)
    if "pass" in lowered or "通过" in content:
        return (fallback_status, content)
    return None


def _project_status_from_task_text(status: str, task: str) -> str:
    if status != "进行中":
        return status
    if any(marker in task for marker in ("待命后续", "待后续", "等待后续", "待新任务")):
        return "待命"
    return status


def _subject_tokens_from_text(text: str) -> tuple[str, ...]:
    value = str(text or "")
    tokens: list[str] = []
    tid = re.search(r"\bT-\d+\b", value)
    if tid:
        tokens.append(tid.group(0))
    batch = re.search(r"\bBatch\s*\d+\b", value, re.IGNORECASE)
    if batch:
        tokens.append(" ".join(batch.group(0).split()))
    subject = re.search(r"(?:IGCSE\s+)?[A-Za-z][A-Za-z ]+\s+\d{4}", value)
    if subject:
        tokens.append(subject.group(0).strip())
        tokens.append(subject.group(0).replace("IGCSE ", "").strip())
    seen: set[str] = set()
    output: list[str] = []
    for token in tokens:
        normalized = " ".join(token.split())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        output.append(normalized)
    return tuple(output)


def _latest_review_pass_after(task: str, updated_at: int) -> dict | None:
    tokens = _subject_tokens_from_text(task)
    if not tokens:
        return None
    for row in list_logs("review_course", limit=30):
        created_at = int(row.get("created_at") or 0)
        if created_at < updated_at:
            continue
        if str(row.get("type") or "") != "say":
            continue
        content = str(row.get("content") or "")
        lowered = content.lower()
        if "pass" not in lowered:
            continue
        if not ("verdict" in lowered or "可发布" in content or "复检结果" in content):
            continue
        if any(token in content or token.lower() in lowered for token in tokens):
            return row
    return None


def _latest_manager_closeout_after(task: str, updated_at: int) -> dict | None:
    tokens = _subject_tokens_from_text(task)
    if not tokens:
        return None
    for row in list_logs("manager", limit=30):
        created_at = int(row.get("created_at") or 0)
        if created_at < updated_at:
            continue
        if str(row.get("type") or "") != "say":
            continue
        content = str(row.get("content") or "")
        lowered = content.lower()
        if not ("closeout" in lowered or "正式 pass" in lowered or "正式 PASS" in content):
            continue
        if any(token in content or token.lower() in lowered for token in tokens):
            return row
    return None


def _project_waiting_review_after_pass(row: dict) -> dict | None:
    agent = str(row.get("agent") or "")
    task = str(row.get("task") or "")
    if agent != "worker_course":
        return None
    if not any(marker in task for marker in ("等待 review", "等待 review_course", "待 review", "待复检", "等待复检")):
        return None
    pass_log = _latest_review_pass_after(task, int(row.get("updated_at") or 0))
    if pass_log is None:
        return None
    content = str(pass_log.get("content") or "")
    first_line = " ".join(content.split())[:120]
    return {
        **row,
        "status": "空闲",
        "task": f"已交付：review_course 已 PASS，等待 manager 收口/下一步。{first_line}",
        "updated_at": int(pass_log.get("created_at") or row.get("updated_at") or 0),
    }


def _project_course_after_visible_closeout(row: dict) -> dict | None:
    agent = str(row.get("agent") or "")
    task = str(row.get("task") or "")
    status = str(row.get("status") or "")
    if agent != "worker_course" or status != "进行中":
        return None
    closeout_log = _latest_manager_closeout_after(task, int(row.get("updated_at") or 0))
    if closeout_log is None:
        return None
    content = str(closeout_log.get("content") or "")
    first_line = " ".join(content.split())[:120]
    return {
        **row,
        "status": "空闲",
        "task": f"已交付：manager 已 closeout，待下一步。{first_line}",
        "updated_at": int(closeout_log.get("created_at") or row.get("updated_at") or 0),
    }


def _project_worker_course_from_newer_self_log(row: dict) -> dict | None:
    agent = str(row.get("agent") or "")
    if agent != "worker_course":
        return None
    updated_at = int(row.get("updated_at") or 0)
    for latest in reversed(list_logs(agent, limit=12)):
        latest_ts = int(latest.get("created_at") or 0)
        if latest_ts < updated_at:
            continue
        derived = _derive_status_from_log(latest, fallback_status=str(row.get("status") or ""))
        if derived is None:
            continue
        status, derived_task = derived
        if latest_ts == updated_at and status == str(row.get("status") or ""):
            continue
        return {
            **row,
            "status": status,
            "task": derived_task,
            "updated_at": latest_ts,
        }
    return None


def _project_qbank_delivered_waiting_next(row: dict) -> dict | None:
    agent = str(row.get("agent") or "")
    task = str(row.get("task") or "")
    if agent != "worker_qbank":
        return None
    waiting_markers = (
        "等待审批", "等待批准", "待审批", "待批准", "方案可执行",
        "待命中", "inbox空",
    )
    if not any(marker in task for marker in waiting_markers):
        return None
    if not any(marker in task for marker in ("已交付", "完成", "PASS", "pass", "待命中", "待命")):
        return None
    return {
        **row,
        "status": "已交付",
        "task": task,
    }


def _project_auto_ops_runtime_recovered(row: dict) -> dict | None:
    agent = str(row.get("agent") or "")
    if agent != "auto_ops":
        return None
    task = " ".join(str(row.get("task") or "").split())
    if not task:
        return None
    if not any(marker in task for marker in ("watchdog持续缺失", "watchdog 持续缺失", "watchdog_alive=false")):
        return None
    if not _runtime_watchdog_recovered():
        return None
    return {
        **row,
        "status": "进行中",
        "task": (
            "盯盘中：router/watchdog 当前已恢复，旧 watchdog 缺失告警已过期；"
            "继续观察 hermes-supervisor / 后续 runtime 告警。"
        ),
    }


def _project_facts_process_visibility_stale(row: dict) -> dict | None:
    agent = str(row.get("agent") or "")
    if agent not in _DIRECT_VISIBILITY_AGENTS:
        return None
    status = str(row.get("status") or "")
    if status not in {"已接单", "进行中"}:
        return None
    task = " ".join(str(row.get("task") or "").split())
    if agent == "auto_ops" and any(marker in task for marker in ("继续盯盘", "盯盘待命", "持续盯盘", "值守")):
        return None
    updated_at = int(row.get("updated_at") or 0)
    latest_log_at = 0
    for latest in list_logs(agent, limit=12):
        if str(latest.get("type") or "") not in {
            "say",
            "worker_course_started",
            "review_course_started",
            "worker_builder_started",
            "worker_started",
            "qbank_followup",
            "task_completed",
            "task",
            "status_update",
        }:
            continue
        latest_log_at = max(latest_log_at, int(latest.get("created_at") or 0))
    # Consider heartbeat as a direct process signal: any eduflow CLI call
    # (say, send, inbox, read, log, status) touches heartbeat.  If it is
    # fresh the agent is demonstrably alive even if it hasn't emitted a
    # qualifying log entry recently (e.g. deep in a tmux workflow that
    # only calls `eduflow say` for progress pings, not `eduflow status`).
    hb = get_heartbeat(agent) or 0
    last_signal = max(updated_at, latest_log_at, hb)
    if not last_signal:
        return None
    age_ms = max(now_ms() - last_signal, 0)
    stale_after_ms = (
        _AUTO_OPS_VISIBILITY_STALE_MS
        if agent == "auto_ops"
        else _PROCESS_VISIBILITY_STALE_MS
    )
    if age_ms < stale_after_ms:
        return None
    task = re.sub(
        r"^外显陈旧：[^。]+。", "",
        task,
    ).strip()
    return {
        **row,
        "task": (
            f"外显陈旧：{agent} 上次直接过程信号约 {age_ms // 60000} 分钟前；"
            f"原状态={status}。{task[:160]}"
        ),
    }


def _project_provider_quota_block(row: dict) -> dict | None:
    agent = str(row.get("agent") or "")
    if agent not in {"worker_builder", "worker_course", "worker_qbank"}:
        return None
    status = str(row.get("status") or "")
    updated_at = int(row.get("updated_at") or 0)
    evidence = provider_quota_block_evidence(agent, after=updated_at)
    if evidence is None:
        return None
    current_task = re.sub(
        r"^外显陈旧：[^。]+。", "",
        " ".join(str(row.get("task") or "").split()),
    ).strip()
    evidence_text = " ".join(str(evidence.get("content") or "").split())
    detail = current_task or evidence_text
    prefix = "上一交付线索" if status in {"已交付", "已完成"} else "原任务线索"
    return {
        **row,
        "status": "受阻",
        "task": (
            f"运行时受阻：manager 已核实 {agent} 所在 Qoder provider "
            f"Credits exhausted/FORBIDDEN，当前不能执行或产生真实过程信号；"
            f"保留{prefix}：{detail[:140]}"
        ),
        "blocker": "Qoder provider credits exhausted",
        "updated_at": int(evidence.get("created_at") or updated_at),
    }


def _project_runtime_guard_block(row: dict) -> dict | None:
    agent = str(row.get("agent") or "")
    if not agent:
        return None
    status = str(row.get("status") or "")
    if status in {"已交付", "已完成"}:
        return None
    evidence = runtime_guard_block_evidence(agent)
    if evidence is None:
        return None
    pending = latest_unread_message(agent)
    pending_text = ""
    if pending is not None and is_high_priority(str(pending.get("priority") or "")):
        pending_text = " ".join(str(pending.get("content") or "").split())[:120]
    failure = str(evidence.get("last_failure_reason") or "runtime_unavailable")
    outcome = str(evidence.get("last_switch_outcome") or "")
    escalation = str(evidence.get("escalation_reason") or "")
    blocker = "runtime guard escalation"
    if failure:
        blocker = f"{blocker}: {failure}"
    detail = f"{failure}"
    if outcome:
        detail += f" / {outcome}"
    if escalation:
        detail += f" / {escalation}"
    task = f"运行时受阻：{agent} runtime guard 已升级（{detail}），当前不能可靠消费 inbox"
    if pending_text:
        task += f"；待处理高优任务：{pending_text}"
    return {
        **row,
        "status": "受阻",
        "task": task,
        "blocker": blocker,
        "updated_at": int(pending.get("created_at") or row.get("updated_at") or 0) if pending else int(row.get("updated_at") or 0),
    }


def _project_manager_from_newer_worker_visibility(row: dict) -> dict | None:
    agent = str(row.get("agent") or "")
    if agent != "manager":
        return None
    status = str(row.get("status") or "")
    task = str(row.get("task") or "")
    allow_process_projection = True
    if status not in _IDLE_STATUSES and task not in _WEAK_STATUS_TASKS:
        if not any(marker in task for marker in ("等待老板", "等老板", "等待下一", "待下一", "待新任务")):
            allow_process_projection = False
    manager_updated_at = int(row.get("updated_at") or 0)
    candidates: list[dict] = []
    for worker in ("worker_course", "worker_qbank", "review_course", "worker_builder"):
        worker_status = get_status(worker) or {}
        if not worker_status:
            worker_status = _project_status_row({
                "agent": worker,
                "status": "待命",
                "task": "ready",
                "blocker": "",
                "updated_at": 0,
            })
        worker_updated_at = int(worker_status.get("updated_at") or 0)
        if worker_updated_at <= manager_updated_at:
            continue
        worker_state = str(worker_status.get("status") or "")
        if worker_state not in {"已接单", "进行中", "已交付", "已完成"}:
            continue
        is_delivery = worker_state in {"已交付", "已完成"}
        if not is_delivery and not allow_process_projection:
            continue
        worker_task = " ".join(str(worker_status.get("task") or "").split())
        if not worker_task or worker_task in _WEAK_STATUS_TASKS:
            continue
        if is_delivery and not (
            worker == "review_course"
            or "VERDICT" in worker_task
            or "PASS" in worker_task
            or "pass" in worker_task.lower()
            or "已完成并交给 manager" in worker_task
            or "已完成并交给manager" in worker_task
        ):
            continue
        candidates.append({
            "agent": worker,
            "status": worker_state,
            "task": worker_task,
            "updated_at": worker_updated_at,
        })
    if not candidates:
        return None
    latest = max(candidates, key=lambda item: int(item.get("updated_at") or 0))
    latest_state = str(latest.get("status") or "")
    if latest_state in {"已交付", "已完成"}:
        return {
            **row,
            "status": "进行中",
            "task": (
                f"团队待收口：来自 {latest['agent']} 的最新交付外显，"
                f"{latest_state} — {latest['task'][:160]}；等待 manager closeout/派下一步"
            ),
            "updated_at": int(latest.get("updated_at") or manager_updated_at),
        }
    return {
        **row,
        "status": "进行中",
        "task": (
            f"团队推进中：来自 {latest['agent']} 的最新外显，"
            f"{latest['status']} — {latest['task'][:160]}"
        ),
        "updated_at": int(latest.get("updated_at") or manager_updated_at),
    }


def _project_manager_from_team_blockers(row: dict) -> dict | None:
    agent = str(row.get("agent") or "")
    if agent != "manager":
        return None
    status = str(row.get("status") or "")
    task = str(row.get("task") or "")
    if not _is_weak_idle_surface(status, task):
        if not any(marker in task for marker in ("等老板", "等待老板", "等老板新指令", "等待新指令", "待新任务")):
            return None
    blockers: list[dict] = []
    for worker in ("anna", "worker_builder", "worker_qbank", "worker_course"):
        worker_status = get_status(worker) or {}
        if str(worker_status.get("status") or "") != "受阻":
            continue
        blocker = str(worker_status.get("blocker") or "").strip()
        worker_task = " ".join(str(worker_status.get("task") or "").split())
        blockers.append({
            "agent": worker,
            "blocker": blocker,
            "task": worker_task,
            "updated_at": int(worker_status.get("updated_at") or 0),
        })
    if not blockers:
        return None
    blockers = sorted(blockers, key=lambda item: item["agent"])
    summary = "；".join(
        f"{item['agent']}={item['blocker'] or item['task'][:60]}"
        for item in blockers
    )
    latest_at = max(int(row.get("updated_at") or 0), *(item["updated_at"] for item in blockers))
    for latest in list_logs("manager", limit=6):
        content = str(latest.get("content") or "")
        if not any(marker in content for marker in (
            "runtime_unhealthy",
            "agent_failover_escalation",
            "运行监督异常",
        )):
            continue
        latest_at = max(latest_at, int(latest.get("created_at") or 0))
    return {
        **row,
        "status": "受阻",
        "task": f"团队阻塞待处理：{summary}",
        "blocker": "team runtime blockers",
        "updated_at": latest_at,
    }


def _project_status_row(row: dict) -> dict:
    projected = dict(row or {})
    agent = str(projected.get("agent") or "")
    task = str(projected.get("task") or "")
    if not agent:
        return projected
    updated_at = int(projected.get("updated_at") or 0)
    status = str(projected.get("status") or "")
    projected["status"] = _project_status_from_task_text(status, task)
    status = str(projected.get("status") or "")

    worker_course_self_projection = _project_worker_course_from_newer_self_log(projected)
    if worker_course_self_projection is not None:
        projected = worker_course_self_projection
        updated_at = int(projected.get("updated_at") or updated_at)
        status = str(projected.get("status") or status)
        task = str(projected.get("task") or task)

    provider_quota_projection = _project_provider_quota_block(projected)
    if provider_quota_projection is not None:
        return provider_quota_projection

    runtime_guard_projection = _project_runtime_guard_block(projected)
    if runtime_guard_projection is not None:
        return runtime_guard_projection

    read_unacked = _latest_read_unacked_high_message_after(agent, updated_at)
    if read_unacked is not None:
        content = " ".join(str(read_unacked.get("content") or "").strip().split())
        projected["status"] = "已读待确认"
        projected["task"] = (
            f"已读待确认：高优任务已读但尚未 ACK/started。{content[:120]}"
            if content
            else "已读待确认：高优任务已读但尚未 ACK/started"
        )
        projected["updated_at"] = int(read_unacked.get("created_at") or updated_at)
        return projected

    high_unread_after = 0 if _is_weak_idle_surface(status, task) else updated_at
    unread_high = _latest_unread_high_message_after(agent, high_unread_after)
    if unread_high is not None:
        content = " ".join(str(unread_high.get("content") or "").strip().split())
        projected["status"] = "待接单"
        projected["task"] = (
            f"待接单：有新的高优任务未读。{content[:120]}"
            if content
            else "待接单：有新的高优任务未读"
        )
        projected["updated_at"] = int(unread_high.get("created_at") or updated_at)
        return projected

    if _is_weak_idle_surface(status, task):
        unread = _latest_unread_message_after(agent, 0)
        if unread is not None:
            content = " ".join(str(unread.get("content") or "").strip().split())
            projected["status"] = "待接单"
            projected["task"] = (
                f"待接单：{content[:120]}"
                if content
                else "待接单：有新未读任务"
            )
            projected["updated_at"] = int(unread.get("created_at") or updated_at)
            return projected

    waiting_review_projection = _project_waiting_review_after_pass(projected)
    if waiting_review_projection is not None:
        return waiting_review_projection

    course_closeout_projection = _project_course_after_visible_closeout(projected)
    if course_closeout_projection is not None:
        return course_closeout_projection

    qbank_delivered_waiting_projection = _project_qbank_delivered_waiting_next(projected)
    if qbank_delivered_waiting_projection is not None:
        projected = qbank_delivered_waiting_projection

    auto_ops_recovered_projection = _project_auto_ops_runtime_recovered(projected)
    if auto_ops_recovered_projection is not None:
        projected = auto_ops_recovered_projection
        updated_at = int(projected.get("updated_at") or updated_at)
        status = str(projected.get("status") or status)
        task = str(projected.get("task") or task)

    manager_worker_projection = _project_manager_from_newer_worker_visibility(projected)
    if manager_worker_projection is not None:
        projected = manager_worker_projection
        updated_at = int(projected.get("updated_at") or updated_at)
        status = str(projected.get("status") or status)
        task = str(projected.get("task") or task)

    manager_blocker_projection = _project_manager_from_team_blockers(projected)
    if manager_blocker_projection is not None:
        projected = manager_blocker_projection
        updated_at = int(projected.get("updated_at") or updated_at)
        status = str(projected.get("status") or status)
        task = str(projected.get("task") or task)

    latest_rows = list_logs(agent, limit=6)
    if not latest_rows:
        facts_stale_projection = _project_facts_process_visibility_stale(projected)
        if facts_stale_projection is not None:
            projected = facts_stale_projection
        return projected
    fallback_status = str(projected.get("status") or "")
    for latest in reversed(latest_rows):
        latest_ts = int(latest.get("created_at") or 0)
        if latest_ts < updated_at and task not in _WEAK_STATUS_TASKS:
            continue
        if task not in _WEAK_STATUS_TASKS and status not in _IDLE_STATUSES and latest_ts <= updated_at:
            continue
        derived = _derive_status_from_log(latest, fallback_status=fallback_status)
        if derived is None:
            continue
        status, derived_task = derived
        projected["status"] = status
        projected["task"] = derived_task
        projected["updated_at"] = latest_ts
        break
    facts_stale_projection = _project_facts_process_visibility_stale(projected)
    if facts_stale_projection is not None:
        projected = facts_stale_projection
    return projected


def get_status(agent: str) -> dict | None:
    row = read_json(_status_file(), {"agents": {}}).get("agents", {}).get(agent)
    if row is None:
        return None
    return _project_status_row(row)


def get_raw_status(agent: str) -> dict | None:
    row = read_json(_status_file(), {"agents": {}}).get("agents", {}).get(agent)
    if row is None:
        return None
    return dict(row)


def list_all_statuses() -> list[dict]:
    """Latest status row for every agent that ever upserted, sorted by name."""
    data = read_json(_status_file(), {"agents": {}})
    return [_project_status_row(data["agents"][a]) for a in sorted(data.get("agents", {}))]


# ── heartbeats ────────────────────────────────────────────────────────


def _heartbeat_file() -> Path:
    return _facts_dir() / "heartbeats.json"


def touch_heartbeat(agent: str) -> None:
    """Record `agent` as alive right now. Cheap and best-effort —
    failures (disk full, permission denied, flock contention timeout)
    are swallowed with a stderr warning rather than raised. Heartbeat
    is auxiliary; killing `eduflow send` or `eduflow inbox`
    because we couldn't update a freshness timestamp would be an
    unhelpful trade-off.
    """
    if not agent:
        return
    try:
        with _locked():
            path = _heartbeat_file()
            data = read_json(path, {})
            data[agent] = now_ms()
            write_json(path, data)
    except OSError as e:
        # OSError covers PermissionError, FileNotFoundError on lock dir,
        # No-space-left-on-device. ValueError / JSON errors are NOT
        # caught here — those mean a corrupt heartbeat file and the
        # operator should see them.
        import sys
        print(f"  ⚠️ heartbeat write failed for {agent}: {e}", file=sys.stderr)


def get_heartbeat(agent: str) -> int | None:
    return read_json(_heartbeat_file(), {}).get(agent)


def all_heartbeats() -> dict[str, int]:
    return dict(read_json(_heartbeat_file(), {}))


# ── log ───────────────────────────────────────────────────────────────


def append_log(agent: str, kind: str, content: str, *, ref: str = "") -> str:
    local_id = _new_id("log")
    row = {
        "local_id": local_id,
        "agent": agent,
        "type": kind,
        "content": str(content or ""),
        "ref": ref,
        "created_at": now_ms(),
    }
    with _locked():
        path = _log_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return local_id


def _legacy_body_log_agent(row: dict) -> str:
    """Recover agent ownership for logs written before `say --body` parsing.

    Older CLI parsing treated `--body` as the agent name, so real worker
    surface lines such as `[worker_course] ...` were present but invisible to
    per-agent status projection. We only infer from explicit bracket prefixes
    to avoid reclassifying arbitrary malformed logs.
    """
    if str(row.get("agent") or "") != "--body":
        return ""
    content = str(row.get("content") or "").strip()
    match = re.match(r"^\[(worker_course|worker_qbank|review_course|worker_builder|auto_ops)(?:\s*(?:→|->).*)?\]", content)
    if not match:
        return ""
    return match.group(1)


def _log_belongs_to_agent(row: dict, agent: str) -> bool:
    if row.get("agent") == agent:
        return True
    return _legacy_body_log_agent(row) == agent


def list_logs(agent: str, *, limit: int = 20) -> list[dict]:
    """Return up to `limit` most recent log entries for `agent`,
    oldest-first. Round-90: corrupt lines (half-written from a crash)
    are now silently skipped instead of raising — same behavior as
    store/memory."""
    rows = [r for r in read_jsonl(_log_file()) if _log_belongs_to_agent(r, agent)]
    return rows[-limit:]
