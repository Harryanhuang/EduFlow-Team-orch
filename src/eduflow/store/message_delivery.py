"""Durable delivery ledger for inbound Feishu messages.

The router's cursor is only an optimisation.  This ledger is the recovery
anchor for messages that were received but could not yet be acknowledged,
including a fresh deployment's first failed event.  Every mutation is
serialized and atomically persisted; each record retains a compact audit
trail so retry and dead-letter decisions remain explainable.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any
import uuid

from eduflow.runtime import paths
from eduflow.util import env_str, file_lock, now_ms, read_json, write_json


_DEFAULT_MAX_ATTEMPTS = 3
_RETRY_BASE_DELAY_MS = 5_000
_RETRY_MAX_DELAY_MS = 60_000
_DELIVERY_LEASE_MS = 5 * 60_000
_AUTOMATION_HOLD_PATHS: set[str] = set()


def _file():
    return paths.message_delivery_file()


def _hold_key() -> str:
    return str(_file())


def _timeout() -> float:
    raw = env_str("EDUFLOW_MESSAGE_DELIVERY_LOCK_TIMEOUT_S").strip()
    try:
        return float(raw) if raw else 5.0
    except ValueError:
        return 5.0


def _max_attempts() -> int:
    raw = env_str("EDUFLOW_MESSAGE_DELIVERY_MAX_ATTEMPTS").strip()
    try:
        return max(1, int(raw)) if raw else _DEFAULT_MAX_ATTEMPTS
    except ValueError:
        return _DEFAULT_MAX_ATTEMPTS


def _retry_delay_ms(attempts: int) -> int:
    """Bounded exponential retry delay; three failures settle within 35s."""
    exponent = max(0, int(attempts) - 1)
    return min(_RETRY_MAX_DELAY_MS, _RETRY_BASE_DELAY_MS * (2 ** exponent))


def _locked():
    return file_lock(_file(), timeout=_timeout())


def _load() -> dict[str, Any]:
    data = read_json(_file(), {"version": 1, "records": {}})
    if not isinstance(data, dict):
        return {"version": 1, "records": {}}
    records = data.get("records")
    if not isinstance(records, dict):
        data["records"] = {}
    data.setdefault("version", 1)
    return data


def automation_hold_active() -> bool:
    """Return whether a failed takeover transition has halted automation."""
    if _hold_key() in _AUTOMATION_HOLD_PATHS:
        return True
    with _locked():
        hold = _load().get("automation_hold")
        return bool(isinstance(hold, dict) and hold.get("active") is True)


def enter_automation_hold(reason: str) -> None:
    """Fail closed when the primary human-takeover state cannot persist."""
    key = _hold_key()
    # Set the in-process latch first: even a second storage failure cannot
    # permit more side effects in this router process.
    _AUTOMATION_HOLD_PATHS.add(key)
    with _locked():
        data = _load()
        data["automation_hold"] = {
            "active": True,
            "reason": str(reason or "human_takeover_persistence_failed"),
            "at": now_ms(),
        }
        data.setdefault("automation_audit", []).append({
            "event": "automation_hold_entered",
            "at": now_ms(),
            "reason": data["automation_hold"]["reason"],
        })
        write_json(_file(), data)


def clear_automation_hold(*, actor: str, reason: str) -> bool:
    """Clear the emergency latch after an explicit administrator recovery."""
    if not actor or not reason:
        raise ValueError("actor and reason are required to clear automation hold")
    with _locked():
        data = _load()
        hold = data.get("automation_hold")
        if not isinstance(hold, dict) or hold.get("active") is not True:
            return False
        data["automation_hold"] = {"active": False, "reason": "", "at": now_ms()}
        data.setdefault("automation_audit", []).append({
            "event": "automation_hold_cleared",
            "at": now_ms(),
            "actor": actor,
            "reason": reason,
        })
        write_json(_file(), data)
    _AUTOMATION_HOLD_PATHS.discard(_hold_key())
    return True


def _decision_data(decision) -> dict[str, Any]:
    action = getattr(decision, "action", "")
    return {
        "action": str(getattr(action, "value", action) or ""),
        "targets": list(getattr(decision, "targets", []) or []),
        "sender": str(getattr(decision, "sender", "") or ""),
        "text": str(getattr(decision, "text", "") or ""),
        "msg_id": str(getattr(decision, "msg_id", "") or ""),
        "reason": str(getattr(decision, "reason", "") or ""),
        "create_time": str(getattr(decision, "create_time", "") or ""),
        "sender_id": str(getattr(decision, "sender_id", "") or ""),
        "user_language": str(getattr(decision, "user_language", "") or ""),
        "schedule_intent": bool(getattr(decision, "schedule_intent", False)),
    }


def _new_record(decision) -> dict[str, Any]:
    payload = _decision_data(decision)
    now = now_ms()
    return {
        "message_id": payload["msg_id"],
        "status": "received",
        "attempts": 0,
        "next_retry_at": 0,
        "retry_lease_until": 0,
        "delivery_lease_token": "",
        "failure_reason": "",
        "decision": payload,
        "targets": {
            target: {"status": "pending", "local_id": ""}
            for target in payload["targets"]
        },
        "slash": {"status": "pending", "reply": None},
        "created_at": now,
        "updated_at": now,
        "audit": [{"event": "received", "at": now}],
    }


def _audit(record: dict[str, Any], event: str, **details) -> None:
    now = now_ms()
    row = {"event": event, "at": now}
    row.update({key: value for key, value in details.items() if value not in (None, "")})
    record.setdefault("audit", []).append(row)
    record["updated_at"] = now


def _record_for(data: dict[str, Any], decision) -> dict[str, Any] | None:
    message_id = str(getattr(decision, "msg_id", "") or "")
    if not message_id:
        return None
    records = data.setdefault("records", {})
    existing = records.get(message_id)
    if isinstance(existing, dict):
        return existing
    record = _new_record(decision)
    records[message_id] = record
    return record


def _owns_lease(record: dict[str, Any], lease_token: str | None) -> bool:
    return not lease_token or record.get("delivery_lease_token") == lease_token


def prepare(decision) -> dict[str, Any]:
    """Journal a classified event before any side effect is attempted."""
    with _locked():
        data = _load()
        record = _record_for(data, decision)
        if record is not None:
            # Preserve the original payload for audit, but fill in a target
            # introduced by a backward-compatible replay payload.
            for target in _decision_data(decision)["targets"]:
                record.setdefault("targets", {}).setdefault(
                    target, {"status": "pending", "local_id": ""})
            _audit(record, "prepared")
            write_json(_file(), data)
            return deepcopy(record)
        return {}


def record_target_persisted(decision, target: str, local_id: str) -> None:
    """Record a canonical inbox row for one delivery target."""
    with _locked():
        data = _load()
        record = _record_for(data, decision)
        if record is None:
            return
        targets = record.setdefault("targets", {})
        target_state = targets.setdefault(target, {"status": "pending", "local_id": ""})
        target_state["status"] = "persisted"
        target_state["local_id"] = str(local_id or target_state.get("local_id") or "")
        _audit(record, "target_persisted", target=target, local_id=target_state["local_id"])
        write_json(_file(), data)


def cached_slash_reply(message_id: str):
    """Return a persisted Slash reply, or ``None`` when none is available."""
    if not message_id:
        return None
    with _locked():
        record = _load().get("records", {}).get(message_id)
        if not isinstance(record, dict):
            return None
        slash = record.get("slash") or {}
        if slash.get("status") not in {
            "reply_ready", "publication_in_flight", "published",
        }:
            return None
        return deepcopy(slash.get("reply"))


def begin_slash_execution(decision) -> str:
    """Reserve one Slash execution.

    ``reply_ready`` means a previous execution completed and only message
    publication must be retried.  ``recovery_required`` intentionally
    refuses to re-run a side-effecting command whose earlier execution
    outcome was interrupted before its reply could be durably recorded.
    """
    with _locked():
        data = _load()
        record = _record_for(data, decision)
        if record is None:
            return "execute"
        slash = record.setdefault("slash", {"status": "pending", "reply": None})
        status = str(slash.get("status") or "pending")
        if status == "reply_ready":
            return "reply_ready"
        if status == "executing":
            return "recovery_required"
        slash["status"] = "executing"
        _audit(record, "slash_execution_started")
        write_json(_file(), data)
        return "execute"


def cache_slash_reply(decision, reply) -> None:
    """Persist the completed Slash reply before attempting Feishu send."""
    with _locked():
        data = _load()
        record = _record_for(data, decision)
        if record is None:
            return
        record["slash"] = {"status": "reply_ready", "reply": deepcopy(reply)}
        _audit(record, "slash_reply_cached")
        write_json(_file(), data)


def begin_slash_publication(decision) -> str:
    """Reserve exactly one attempt to publish a cached Slash reply.

    An external chat send cannot be atomically coupled to this local ledger.
    If a process crashes while publication is in flight, recovery refuses to
    send again and routes the event to dead-letter rather than risk a second
    control-plane reply.
    """
    with _locked():
        data = _load()
        record = _record_for(data, decision)
        if record is None:
            return "recovery_required"
        slash = record.setdefault("slash", {"status": "pending", "reply": None})
        status = str(slash.get("status") or "pending")
        if status == "published":
            return "published"
        if status == "reply_ready":
            slash["status"] = "publication_in_flight"
            _audit(record, "slash_publication_started")
            write_json(_file(), data)
            return "publish"
        return "recovery_required"


def release_slash_publication_for_retry(decision, reason: str) -> None:
    """Return a confirmed failed send to the safe cached-reply retry state."""
    with _locked():
        data = _load()
        record = _record_for(data, decision)
        if record is None:
            return
        slash = record.setdefault("slash", {"status": "pending", "reply": None})
        if slash.get("reply") is not None:
            slash["status"] = "reply_ready"
        _audit(record, "slash_publication_retryable", reason=reason)
        write_json(_file(), data)


def mark_slash_published(decision, publication_id: str = "") -> None:
    """Persist a confirmed Feishu publication before router ACK progress."""
    with _locked():
        data = _load()
        record = _record_for(data, decision)
        if record is None:
            return
        slash = record.setdefault("slash", {"status": "pending", "reply": None})
        slash["status"] = "published"
        slash["publication_id"] = str(publication_id or "")
        _audit(record, "slash_published", publication_id=slash["publication_id"])
        write_json(_file(), data)


def record_delivered(decision, *, outcome: str = "durable_success",
                     lease_token: str | None = None) -> bool:
    """Persist a completed delivery before attempting router cursor ACK."""
    with _locked():
        data = _load()
        record = _record_for(data, decision)
        if record is None:
            return False
        if not _owns_lease(record, lease_token):
            return False
        record["status"] = "delivered"
        record["next_retry_at"] = 0
        record["retry_lease_until"] = 0
        record["delivery_lease_token"] = ""
        record["failure_reason"] = ""
        _audit(record, "delivered", outcome=outcome)
        write_json(_file(), data)
        return True


def record_acknowledged(decision, *, outcome: str = "durable_success") -> None:
    with _locked():
        data = _load()
        record = _record_for(data, decision)
        if record is None:
            return
        record["status"] = "acknowledged"
        record["next_retry_at"] = 0
        record["retry_lease_until"] = 0
        record["delivery_lease_token"] = ""
        record["failure_reason"] = ""
        _audit(record, "acknowledged", outcome=outcome)
        write_json(_file(), data)


def record_terminal(decision, reason: str) -> None:
    with _locked():
        data = _load()
        record = _record_for(data, decision)
        if record is None:
            return
        record["status"] = "terminal"
        record["next_retry_at"] = 0
        record["retry_lease_until"] = 0
        record["delivery_lease_token"] = ""
        record["failure_reason"] = str(reason or "terminal_failure")
        _audit(record, "terminal", reason=record["failure_reason"])
        write_json(_file(), data)


def record_retryable_failure(decision, reason: str,
                             *, lease_token: str | None = None) -> dict[str, Any]:
    """Increment attempts and return the resulting retry/dead-letter state."""
    with _locked():
        data = _load()
        record = _record_for(data, decision)
        if record is None:
            return {"dead_letter": False, "attempts": 0}
        if not _owns_lease(record, lease_token):
            return {"dead_letter": False, "attempts": int(record.get("attempts") or 0),
                    "lease_lost": True}
        attempts = int(record.get("attempts") or 0) + 1
        now = now_ms()
        record["attempts"] = attempts
        record["failure_reason"] = str(reason or "delivery_unconfirmed")
        dead_letter = attempts >= _max_attempts()
        record["status"] = "dead_letter" if dead_letter else "retrying"
        record["next_retry_at"] = 0 if dead_letter else now + _retry_delay_ms(attempts)
        record["retry_lease_until"] = 0
        record["delivery_lease_token"] = ""
        _audit(record, "dead_letter" if dead_letter else "retry_scheduled",
               attempts=attempts, reason=record["failure_reason"])
        write_json(_file(), data)
        return {"dead_letter": dead_letter, "attempts": attempts,
                "failure_reason": record["failure_reason"]}


def defer_for_human_takeover(decision) -> None:
    """Keep ingress durable while a human has paused automation.

    Takeover is not a delivery failure, so it never consumes retry attempts
    or auto-dead-letters an otherwise healthy message.
    """
    with _locked():
        data = _load()
        record = _record_for(data, decision)
        if record is None or record.get("status") not in {"received", "retrying"}:
            return
        record["status"] = "retrying"
        record["next_retry_at"] = now_ms() + _RETRY_BASE_DELAY_MS
        record["retry_lease_until"] = 0
        record["delivery_lease_token"] = ""
        _audit(record, "automation_deferred_human_takeover")
        write_json(_file(), data)


def list_dead_letters() -> list[dict[str, Any]]:
    with _locked():
        records = _load().get("records", {})
        rows = [deepcopy(row) for row in records.values()
                if isinstance(row, dict) and row.get("status") == "dead_letter"]
    return sorted(rows, key=lambda row: int(row.get("updated_at") or 0))


def audit_events(message_id: str) -> list[dict[str, Any]]:
    with _locked():
        record = _load().get("records", {}).get(message_id)
        if not isinstance(record, dict):
            return []
        return deepcopy(list(record.get("audit") or []))


def replay_dead_letter(message_id: str, *, actor: str, reason: str):
    """Reopen a dead-letter record and return its original Decision.

    The caller deliberately owns when to send the returned decision back
    through the delivery loop.  This function never fires a command or a
    network request itself.
    """
    if not actor or not reason:
        raise ValueError("actor and reason are required for dead-letter replay")
    with _locked():
        data = _load()
        record = data.get("records", {}).get(message_id)
        if not isinstance(record, dict) or record.get("status") != "dead_letter":
            return None
        slash = record.get("slash") or {}
        if slash.get("status") in {"executing", "publication_in_flight"}:
            _audit(record, "dead_letter_replay_refused",
                   reason="slash_execution_or_publication_uncertain")
            write_json(_file(), data)
            return None
        record["status"] = "retrying"
        record["attempts"] = 0
        record["next_retry_at"] = 0
        record["retry_lease_until"] = 0
        record["delivery_lease_token"] = ""
        record["failure_reason"] = ""
        _audit(record, "dead_letter_replayed", actor=actor, reason=reason)
        write_json(_file(), data)
        payload = deepcopy(record.get("decision") or {})
    return _decision_from_data(payload)


def resolve_uncertain_slash(message_id: str, *, actor: str, reason: str) -> bool:
    """Close a dead-letter whose Slash outcome cannot be safely retried.

    This is an explicit human-takeover acknowledgement, not a resend.  The
    original command handler is never invoked again and the durable audit
    records who accepted the unresolved external publication boundary.
    """
    if not actor or not reason:
        raise ValueError("actor and reason are required for uncertain Slash resolution")
    with _locked():
        data = _load()
        record = data.get("records", {}).get(message_id)
        if not isinstance(record, dict) or record.get("status") != "dead_letter":
            return False
        slash = record.get("slash") or {}
        if slash.get("status") not in {"executing", "publication_in_flight"}:
            return False
        record["status"] = "terminal"
        record["failure_reason"] = "human_resolved_uncertain_slash"
        record["next_retry_at"] = 0
        record["retry_lease_until"] = 0
        record["delivery_lease_token"] = ""
        _audit(record, "uncertain_slash_resolved", actor=actor, reason=reason)
        write_json(_file(), data)
        return True


def _records_to_decisions(records: list[dict[str, Any]]) -> list:
    payloads = [deepcopy(row.get("decision") or {}) for row in records]
    return [_decision_from_data(payload) for payload in payloads if payload.get("msg_id")]


def pending_decisions() -> list:
    """Return delivery work that survived a crash before durable delivery."""
    with _locked():
        records = _load().get("records", {})
        rows = [row for row in records.values()
                if isinstance(row, dict) and row.get("status") in {"received", "retrying"}]
    return _records_to_decisions(sorted(rows, key=lambda row: int(row.get("created_at") or 0)))


def claim_delivery(decision, *, now: int | None = None, force: bool = False,
                   break_existing_lease: bool = False) -> str:
    """Atomically acquire the one lease allowed to perform delivery work.

    Both live ingress and the retry worker call this before ``apply``.  A
    second contender returns an empty token and must not inject a pane, run a
    Slash handler, or consume a retry attempt.
    """
    now_value = now_ms() if now is None else int(now)
    with _locked():
        data = _load()
        record = _record_for(data, decision)
        if record is None or record.get("status") not in {"received", "retrying"}:
            return ""
        if (not force and record.get("status") == "retrying"
                and int(record.get("next_retry_at") or 0) > now_value):
            return ""
        if (not break_existing_lease
                and int(record.get("retry_lease_until") or 0) > now_value):
            return ""
        token = uuid.uuid4().hex
        record["delivery_lease_token"] = token
        record["retry_lease_until"] = now_value + _DELIVERY_LEASE_MS
        _audit(record, "delivery_claimed")
        write_json(_file(), data)
        return token


def claim_due_retry_decisions(*, now: int | None = None) -> list:
    """Select due retries; execution still requires ``claim_delivery``."""
    now_value = now_ms() if now is None else int(now)
    with _locked():
        records = _load().get("records", {})
        rows: list[dict[str, Any]] = []
        for record in records.values():
            if not isinstance(record, dict) or record.get("status") != "retrying":
                continue
            if int(record.get("next_retry_at") or 0) > now_value:
                continue
            if int(record.get("retry_lease_until") or 0) > now_value:
                continue
            rows.append(deepcopy(record))
    return _records_to_decisions(sorted(rows, key=lambda row: int(row.get("created_at") or 0)))


def pending_acknowledgements() -> list:
    """Return delivery results that only need cursor/seen acknowledgement."""
    with _locked():
        records = _load().get("records", {})
        rows = [row for row in records.values()
                if isinstance(row, dict) and row.get("status") in {
                    "delivered", "terminal", "dead_letter",
                }]
    return _records_to_decisions(sorted(rows, key=lambda row: int(row.get("created_at") or 0)))


def status(message_id: str) -> str:
    with _locked():
        record = _load().get("records", {}).get(message_id)
        return str(record.get("status") or "") if isinstance(record, dict) else ""


def _decision_from_data(payload: dict[str, Any]):
    from eduflow.feishu.router import Action, Decision
    action_value = str(payload.get("action") or Action.ROUTE.value)
    try:
        action = Action(action_value)
    except ValueError:
        action = Action.ROUTE
    return Decision(
        action=action,
        targets=list(payload.get("targets") or []),
        sender=str(payload.get("sender") or ""),
        text=str(payload.get("text") or ""),
        msg_id=str(payload.get("msg_id") or ""),
        reason=str(payload.get("reason") or ""),
        create_time=str(payload.get("create_time") or ""),
        sender_id=str(payload.get("sender_id") or ""),
        user_language=str(payload.get("user_language") or ""),
        schedule_intent=bool(payload.get("schedule_intent")),
    )
