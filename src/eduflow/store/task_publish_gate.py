"""Business-level publish gate for flow-task events.

This layer decides whether a store-produced task event is worth sending
to the chat audience. It does not read `chat.publish.*` tunables and it
does not trust actor-supplied diffs; callers must pass the event row
emitted by `store.tasks`.
"""
from __future__ import annotations

from eduflow.store import task_evidence_account
from eduflow.util import now_ms


_REQUIRED_EVENT_KEYS = frozenset({
    "event_id",
    "task_id",
    "kind",
    "before",
    "after",
    "changes",
    "created_at",
})
_VALID_EVENT_KINDS = frozenset({"created", "transition"})
CADENCE_ACTION_TAXONOMY = frozenset({
    "send_now",
    "delay_and_wait",
    "merge_with_next_update",
    "suppress_duplicate_update",
    "suppress_low_signal_update",
})
WORKER_WAITING_DELAY_MS = 15 * 60 * 1000
PUBLISH_REASON_TAXONOMY = frozenset({
    "invalid_store_event",
    "non_user_target",
    "created_internal_only",
    "internal_assignment",
    "progress_internal_only",
    "review_internal_only",
    "manager_action_internal_only",
    "rejected_internal_only",
    "delivered_to_user",
    "closeout_evidence_missing",
    "worker_accepted",
    "worker_started",
    "worker_waiting_on_manager",
    "worker_completed_handed_to_manager",
    "user_explanation_scope_pending",
    "user_explanation_material_pending",
    "user_explanation_direction_pending",
    "user_explanation_revision_in_progress",
    "transition_silent",
    "dedup_suppressed",
})
MANAGER_RESPONSE_TAXONOMY = frozenset({
    "internal_only",
    "worker_reassurance",
    "final_result_delivered",
    "manager_problem_scope_pending",
    "manager_problem_material_pending",
    "manager_problem_direction_pending",
    "manager_problem_revision_in_progress",
    "generic_manager_update_fallback",
})
_USER_EXPLANATION_ALLOWED_REVIEW_REASONS = {
    "missing_scope_confirmation": "user_explanation_scope_pending",
    "missing_required_artifact": "user_explanation_material_pending",
    "missing_owner_decision": "user_explanation_direction_pending",
}
_MANAGER_RESPONSE_BY_REASON = {
    "delivered_to_user": "final_result_delivered",
    "user_explanation_scope_pending": "manager_problem_scope_pending",
    "user_explanation_material_pending": "manager_problem_material_pending",
    "user_explanation_direction_pending": "manager_problem_direction_pending",
    "user_explanation_revision_in_progress": "manager_problem_revision_in_progress",
}
_MANAGER_RESPONSE_BY_REVIEW_REASON = {
    "approved_for_delivery": "final_result_delivered",
    "missing_scope_confirmation": "manager_problem_scope_pending",
    "missing_required_artifact": "manager_problem_material_pending",
    "missing_owner_decision": "manager_problem_direction_pending",
    "changes_requested": "manager_problem_revision_in_progress",
    "quality_not_met": "manager_problem_revision_in_progress",
}
CLOSE_LOOP_STATE_TAXONOMY = frozenset({
    "open",
    "manager_result_closed",
    "manager_problem_closed",
    "worker_reassurance_suppressed_after_close",
    "reopen_after_new_meaningful_change",
})


def _changed_to_status(event: dict, to_status: str) -> bool:
    changes = event.get("meaningful_changes") or event.get("changes") or {}
    status_change = changes.get("status") or {}
    return str(status_change.get("after") or "") == to_status


def _changed_reviewer_only(event: dict) -> bool:
    changes = event.get("meaningful_changes") or event.get("changes") or {}
    keys = set(changes)
    return bool(keys) and keys.issubset({"reviewer", "latest_turn_summary"})


def _is_real_waiting_on_manager_event(event: dict, after: dict) -> bool:
    return (
        str(after.get("status") or "") == "blocked"
        and bool(after.get("needs_manager_action"))
        and str(after.get("verdict") or "") == "manager_action"
        and _changed_to_status(event, "blocked")
    )


def _is_real_completed_handoff_event(event: dict, after: dict) -> bool:
    return (
        str(after.get("status") or "") == "submitted_for_review"
        and _changed_to_status(event, "submitted_for_review")
    )


def _target_role(name: str) -> str:
    if name == "manager":
        return "manager"
    if name == "user" or not name:
        return "user"
    if name.startswith("worker"):
        return "worker"
    return "user"


def _invalid_decision(event: dict, *, sender: str, to_target: str,
                      reason: str) -> dict:
    normalized = reason
    if reason.startswith("invalid_store_event:"):
        normalized = "invalid_store_event"
    return {
        "publish": False,
        "reason": normalized,
        "reason_detail": reason,
        "sender": sender,
        "to_target": to_target,
        "task_id": event.get("task_id", ""),
        "event_kind": event.get("kind", ""),
        "status": "",
        "cadence_action": "suppress_low_signal_update",
        "cadence_reason": "invalid_store_event",
        "close_loop_state": "open",
        "close_loop_reason": "",
    }

# ── Package 8: Dedup cache & P0 anomaly protection ──────────────

# P0 anomaly reason markers that must NEVER be suppressed by dedup.
_P0_ANOMALY_REASONS = frozenset({
    "workflow_gate_anomaly",
    "ack_desync",
    "task_truth_drift",
    "runtime_fallback_failure",
    "subject_closeout_verifier_fail",
    "qbank_needs_review",
    "qbank_needs_user_authorization",
})

# Internal-only delivery lanes that bypass dedup entirely.
_INTERNAL_LANES = frozenset({"internal_only"})


class DedupCache:
    """Short-window dedup for user-visible chat cards.

    Maps ``(task_id, stage, normalized_content_hash)`` → ``expires_at_ms``.
    Only consulted for decisions where ``delivery_lane`` is user-visible;
    internal-only events and P0 anomalies bypass the cache altogether.
    """

    def __init__(self, window_ms: int = 90_000) -> None:
        self._window_ms = int(window_ms)
        self._entries: dict[tuple[str, str, str], int] = {}

    @staticmethod
    def _normalize(text: str) -> str:
        """Collapse whitespace so ``"a  b"`` and ``"a b"`` match."""
        return " ".join(str(text or "").split())

    @staticmethod
    def _content_key(content: str) -> str:
        """Derive a short hashable key from normalized content.

        We hash the content rather than storing the full string so the
        cache stays small even for long messages."""
        return DedupCache._normalize(content)

    def is_duplicate(self, task_id: str, stage: str, content: str) -> bool:
        """True if this (task_id, stage, content) was seen within the window.

        Side-effect: records the key on first sight so the *next* call
        with the same key returns True."""
        now = now_ms()
        key = (str(task_id), str(stage), self._content_key(content))
        expires = self._entries.get(key)
        if expires is not None and now < expires:
            return True
        self._entries[key] = now + self._window_ms
        return False

    def prune_expired(self) -> int:
        """Remove expired entries. Returns count of pruned entries."""
        now = now_ms()
        expired = [k for k, v in self._entries.items() if now >= v]
        for k in expired:
            del self._entries[k]
        return len(expired)

    def __len__(self) -> int:
        return len(self._entries)


def should_dedup_check(decision: dict, event: dict | None = None) -> bool:
    """Return True only if the decision is a candidate for dedup checking.

    Internal-only lanes and P0 anomaly reasons must NEVER be checked
    against the dedup cache — they must always pass through unchanged.
    """
    lane = str(decision.get("delivery_lane") or "")
    if lane in _INTERNAL_LANES:
        return False
    reason = str(decision.get("reason") or "")
    if reason in _P0_ANOMALY_REASONS:
        return False
    reason_detail = str(decision.get("reason_detail") or "")
    if reason_detail in _P0_ANOMALY_REASONS:
        return False
    # Also gate on the event itself — a P0 anomaly marker on the
    # underlying task event must bypass dedup even when the publish
    # reason doesn't carry the P0 tag directly.
    if event is not None and _is_P0_anomaly(event):
        return False
    return True


def _is_P0_anomaly(event: dict, after: dict | None = None) -> bool:
    """Check whether the event carries a P0 anomaly that must never be
    suppressed by dedup or visual filtering."""
    after = after or event.get("after") or {}
    verdict = str(after.get("verdict") or "")
    review_reason = str(after.get("review_reason") or "").strip()
    status = str(after.get("status") or "")

    # Direct anomaly markers on the task
    anomaly_field = str(after.get("anomaly_kind") or after.get("anomaly") or "")
    if anomaly_field in _P0_ANOMALY_REASONS:
        return True

    # qbank-specific P0 states
    # These are QBank lifecycle states, set on the 'qbank_lifecycle_state'
    # or 'closeout_status' field rather than review_reason.
    qbank_state = str(after.get("qbank_lifecycle_state") or after.get("closeout_status") or "")
    if qbank_state in ("needs_review", "needs_user_authorization"):
        return True

    # Closeout verifier failure
    closeout = str(after.get("closeout_status") or after.get("closeout_verdict") or "")
    if "verifier_fail" in closeout or "closeout_failed" in closeout:
        return True

    # Runtime / watchdog anomalies
    if str(after.get("runtime_status") or "") == "fallback_failure":
        return True

    return False


# Module-level dedup cache with default 90-second window.
_dedup_cache = DedupCache(window_ms=90_000)


def _apply_dedup_if_needed(decision: dict, event: dict | None = None,
                           task: dict | None = None) -> dict:
    """Optionally suppress a publish=True decision based on the dedup cache.

    Returns the decision unchanged if dedup is not applicable; otherwise
    returns a copy with ``publish=False`` and reason ``dedup_suppressed``.
    """
    if not decision.get("publish"):
        return decision
    if not should_dedup_check(decision, event=event):
        return decision

    task_id = str(decision.get("task_id") or "")
    # Stage comes from the event's after snapshot or the task dict
    after = (event or {}).get("after") or {}
    stage = str(
        after.get("stage")
        or (task or {}).get("stage")
        or ""
    )
    content = f"{decision.get('reason') or ''}|{decision.get('status') or ''}|{decision.get('delivery_lane') or ''}"

    if _dedup_cache.is_duplicate(task_id, stage, content):
        suppressed = dict(decision)
        suppressed["publish"] = False
        suppressed["reason"] = "dedup_suppressed"
        suppressed["cadence_action"] = "suppress_duplicate_update"
        suppressed["cadence_reason"] = "dedup_user_visible_window"
        return suppressed
    return decision


def _decision(event: dict, *, publish: bool, reason: str, sender: str,
              to_target: str, status: str,
              audience_policy: str = "internal_only",
              delivery_lane: str = "internal_only",
              cadence_action: str = "suppress_low_signal_update",
              cadence_reason: str = "internal_only",
              manager_response_type: str = "internal_only",
              close_loop_state: str = "open",
              close_loop_reason: str = "") -> dict:
    return {
        "publish": publish,
        "reason": reason,
        "reason_detail": reason,
        "sender": sender,
        "to_target": to_target,
        "task_id": event["task_id"],
        "event_kind": event["kind"],
        "status": status,
        "audience_policy": audience_policy,
        "delivery_lane": delivery_lane,
        "cadence_action": cadence_action,
        "cadence_reason": cadence_reason,
        "manager_response_type": manager_response_type,
        "close_loop_state": close_loop_state,
        "close_loop_reason": close_loop_reason,
    }


def _requires_closeout_evidence_account(task: dict) -> bool:
    title = str(task.get("title") or "")
    description = str(task.get("description") or "")
    summary = str(task.get("latest_turn_summary") or "")
    workflow_id = str(task.get("workflow_id") or "")
    text = " ".join((title, description, summary))
    return (
        bool(workflow_id)
        or "IGCSE" in text
        or "正式完成" in text
        or "closeout" in text.lower()
        or "全学科" in text
        or "全部 10 批次" in text
    )


def validate_store_event(event: dict) -> tuple[bool, str]:
    missing = sorted(_REQUIRED_EVENT_KEYS - set(event))
    if missing:
        return False, f"missing_keys:{','.join(missing)}"
    if event.get("kind") not in _VALID_EVENT_KINDS:
        return False, f"invalid_kind:{event.get('kind')}"
    if not isinstance(event.get("task_id"), str) or not event.get("task_id"):
        return False, "invalid_task_id"
    if not isinstance(event.get("changes"), dict):
        return False, "invalid_changes"
    kind = event["kind"]
    before = event.get("before")
    after = event.get("after")
    if kind == "created":
        if before is not None:
            return False, "created_before_must_be_none"
        if not isinstance(after, dict):
            return False, "created_after_must_be_dict"
        return True, "ok"
    if not isinstance(before, dict):
        return False, "transition_before_must_be_dict"
    if not isinstance(after, dict):
        return False, "transition_after_must_be_dict"
    return True, "ok"


def decide_task_event_publish(event: dict, *, sender: str,
                              to_target: str) -> dict:
    """Return a structured business decision for a task event.

    Current v1 policy is intentionally narrow:
    - flow-task creation stays internal
    - internal assignment/progress transitions stay internal
    - ``delivered`` is publish-worthy to the user audience

    Package 8: publish=True decisions are gated through the dedup cache
    before being returned. P0 anomalies and internal-only events always
    bypass dedup.
    """
    ok, reason = validate_store_event(event)
    if not ok:
        return _invalid_decision(event, sender=sender, to_target=to_target,
                                 reason=f"invalid_store_event:{reason}")

    after = event.get("after") or {}
    status = str(after.get("status") or "")
    target_role = _target_role(to_target)
    verdict = str(after.get("verdict") or "")
    needs_manager_action = bool(after.get("needs_manager_action"))
    review_reason = str(after.get("review_reason") or "").strip()

    if target_role != "user":
        return _decision(
            event,
            publish=False,
            reason="non_user_target",
            sender=sender,
            to_target=to_target,
            status=status,
            audience_policy="internal_only",
            delivery_lane="internal_only",
            cadence_action="suppress_low_signal_update",
            cadence_reason="non_user_target",
            manager_response_type="internal_only",
        )

    if event["kind"] == "created":
        return _apply_dedup_if_needed(_decision(
            event,
            publish=True,
            reason="worker_accepted",
            sender=sender,
            to_target=to_target,
            status=status,
            audience_policy="worker_reassurance",
            delivery_lane="worker_reassurance",
            cadence_action="send_now",
            cadence_reason="fresh_worker_acceptance",
            manager_response_type="worker_reassurance",
        ), event=event)

    if _is_real_completed_handoff_event(event, after):
        return _apply_dedup_if_needed(_decision(
            event,
            publish=True,
            reason="worker_completed_handed_to_manager",
            sender=sender,
            to_target=to_target,
            status=status,
            audience_policy="worker_reassurance",
            delivery_lane="worker_reassurance",
            cadence_action="send_now",
            cadence_reason="worker_finished_and_handed_off",
            manager_response_type="worker_reassurance",
        ), event=event)

    if _is_real_waiting_on_manager_event(event, after):
        event_created_at = int(event.get("created_at") or 0)
        is_fresh_wait = (now_ms() - event_created_at) < WORKER_WAITING_DELAY_MS
        decision = _decision(
            event,
            publish=not is_fresh_wait,
            reason="worker_waiting_on_manager",
            sender=sender,
            to_target=to_target,
            status=status,
            audience_policy="worker_reassurance",
            delivery_lane="worker_reassurance",
            cadence_action=(
                "delay_and_wait" if is_fresh_wait else "send_now"
            ),
            cadence_reason=(
                "fresh_manager_action_wait"
                if is_fresh_wait
                else "manager_action_wait_became_user_visible"
            ),
            manager_response_type="worker_reassurance",
        )
        if decision["publish"]:
            return _apply_dedup_if_needed(decision, event=event)
        return decision

    if needs_manager_action or verdict == "manager_action":
        reason = _USER_EXPLANATION_ALLOWED_REVIEW_REASONS.get(
            review_reason,
            "manager_action_internal_only",
        )
        return _decision(
            event,
            publish=False,
            reason=reason,
            sender=sender,
            to_target=to_target,
            status=status,
            audience_policy=(
                "manager_summary_only"
                if reason != "manager_action_internal_only"
                else "internal_only"
            ),
            delivery_lane=(
                "manager_problem"
                if reason != "manager_action_internal_only"
                else "internal_only"
            ),
            cadence_action="suppress_low_signal_update",
            cadence_reason="manager_only_problem_signal",
            manager_response_type=_MANAGER_RESPONSE_BY_REASON.get(
                reason,
                "generic_manager_update_fallback",
            ),
        )

    if verdict == "rejected":
        return _decision(
            event,
            publish=False,
            reason="rejected_internal_only",
            sender=sender,
            to_target=to_target,
            status=status,
            audience_policy="internal_only",
            delivery_lane="internal_only",
            cadence_action="suppress_low_signal_update",
            cadence_reason="rejected_internal_only",
            manager_response_type="internal_only",
        )

    if status == "assigned":
        publish, reason, audience_policy, delivery_lane, cadence_action, cadence_reason, manager_response_type = (
            False, "internal_assignment", "internal_only", "internal_only",
            "suppress_low_signal_update", "internal_assignment", "internal_only"
        )
    elif status == "in_progress":
        if _changed_reviewer_only(event):
            publish, reason, audience_policy, delivery_lane, cadence_action, cadence_reason, manager_response_type = (
                False, "progress_internal_only", "internal_only", "internal_only",
                "suppress_low_signal_update", "reviewer_assignment_during_progress", "internal_only"
            )
        else:
            publish, reason, audience_policy, delivery_lane, cadence_action, cadence_reason, manager_response_type = (
                True, "worker_started", "worker_reassurance", "worker_reassurance",
                "send_now", "fresh_worker_start", "worker_reassurance"
            )
    elif status == "submitted_for_review":
        publish, reason, audience_policy, delivery_lane, cadence_action, cadence_reason, manager_response_type = (
            False, "review_internal_only", "internal_only", "internal_only",
            "suppress_low_signal_update", "review_internal_only", "internal_only"
        )
    elif status == "delivered":
        account = task_evidence_account.build_evidence_account(after)
        if (not _requires_closeout_evidence_account(after)) or account["closeout_ready"]:
            publish, reason, audience_policy, delivery_lane, cadence_action, cadence_reason, manager_response_type = (
                True, "delivered_to_user", "formal_delivery", "manager_result",
                "send_now", "manager_result_ready", "final_result_delivered"
            )
        else:
            publish, reason, audience_policy, delivery_lane, cadence_action, cadence_reason, manager_response_type = (
                False, "closeout_evidence_missing", "internal_only", "internal_only",
                "suppress_low_signal_update", "evidence_account_not_ready", "internal_only"
            )
    else:
        publish, reason, audience_policy, delivery_lane, cadence_action, cadence_reason, manager_response_type = (
            False, "transition_silent", "internal_only", "internal_only",
            "suppress_low_signal_update", "transition_silent",
            _MANAGER_RESPONSE_BY_REVIEW_REASON.get(review_reason, "internal_only")
        )
    decision = _decision(
        event,
        publish=publish,
        reason=reason,
        sender=sender,
        to_target=to_target,
        status=status,
        audience_policy=audience_policy,
        delivery_lane=delivery_lane,
        cadence_action=cadence_action,
        cadence_reason=cadence_reason,
        manager_response_type=manager_response_type,
    )
    if decision["publish"]:
        return _apply_dedup_if_needed(decision, event=event)
    return decision
