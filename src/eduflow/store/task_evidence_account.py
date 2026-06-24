"""Evidence ledger derivation for flow-task closeout decisions."""
from __future__ import annotations

from typing import Any


CRITICAL_EVIDENCE_FIELDS = (
    "workflow_id",
    "task_id",
    "batch_range",
    "items_count",
    "qql_count",
    "manifest_evidence",
)

_READY_QBANK_STATES = frozenset({"qbank_ready", "ready_for_import", "needs_user_authorization"})
_BLOCKING_RECOMMENDATIONS = frozenset({
    "manager_formal_closeout",
    "select_next_subject",
    "continue_next_batch",
    "dispatch_next_subject_worker_course",
    "approve_subject_for_qbank_seed",
})
_TARGET_SUBJECT_CODES = frozenset({
    "0452", "0455", "0478", "0580", "0606", "0610", "0620", "0625", "0653",
})


def _as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _first_present(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def _packet(task: dict) -> dict:
    value = task.get("evidence_packet") or {}
    return value if isinstance(value, dict) else {}


def _snapshot(task: dict) -> dict:
    value = task.get("evidence_snapshot") or {}
    return value if isinstance(value, dict) else {}


def _latest(task: dict) -> dict:
    value = task.get("latest_authoritative_verdict") or {}
    return value if isinstance(value, dict) else {}


def _verifier(verifier_result: dict | None) -> dict:
    value = verifier_result or {}
    return value if isinstance(value, dict) else {}


def _manifest_value(packet: dict, snapshot: dict, verifier: dict) -> tuple[Any, str]:
    value = _first_present(
        packet.get("manifest_evidence"),
        packet.get("manifest_rows"),
        packet.get("manifest_covered_count"),
        snapshot.get("manifest_evidence"),
        snapshot.get("manifest_rows"),
        verifier.get("manifest_rows"),
    )
    if value is packet.get("manifest_evidence"):
        return value, "evidence_packet.manifest_evidence"
    if value is packet.get("manifest_rows"):
        return value, "evidence_packet.manifest_rows"
    if value is packet.get("manifest_covered_count"):
        return value, "evidence_packet.manifest_covered_count"
    if value is snapshot.get("manifest_evidence"):
        return value, "evidence_snapshot.manifest_evidence"
    if value is snapshot.get("manifest_rows"):
        return value, "evidence_snapshot.manifest_rows"
    if value is verifier.get("manifest_rows"):
        return value, "subject_verifier.manifest_rows"
    return None, "source_missing"


def _source_for_count(name: str, packet: dict, snapshot: dict, verifier: dict) -> tuple[int | None, str]:
    aliases = {
        "items_count": ("items_count", "item_count"),
        "qql_count": ("qql_count", "qa_count"),
    }
    for key in aliases[name]:
        value = _as_int(packet.get(key))
        if value is not None:
            return value, f"evidence_packet.{key}"
    for key in aliases[name]:
        value = _as_int(snapshot.get(key))
        if value is not None:
            return value, f"evidence_snapshot.{key}"
    for key in aliases[name]:
        value = _as_int(verifier.get(key))
        if value is not None:
            return value, f"subject_verifier.{key}"
    return None, "source_missing"


def _manifest_rows(value: Any) -> int | None:
    if isinstance(value, dict):
        for key in ("rows", "manifest_rows", "count", "items_count"):
            parsed = _as_int(value.get(key))
            if parsed is not None:
                return parsed
        return None
    if isinstance(value, (list, tuple, set)):
        return None
    return _as_int(value)


def _manifest_rows_from_sources(packet: dict, snapshot: dict, verifier: dict, fallback: Any) -> int | None:
    for source in (packet, snapshot, verifier):
        for key in ("manifest_rows", "manifest_covered_count", "items_mapping_count"):
            parsed = _as_int(source.get(key))
            if parsed is not None:
                return parsed
    parsed = _manifest_rows(fallback)
    if parsed is not None:
        return parsed
    return None


def _scope_value(task: dict, packet: dict) -> str:
    return str(
        _first_present(
            packet.get("batch_range"),
            task.get("scope_topic"),
            task.get("verdict_target"),
            task.get("title"),
        )
        or ""
    )


def _subject_code(text: str) -> str:
    import re
    match = re.search(r"\b(\d{4})\b", str(text or ""))
    return match.group(1) if match else ""


def requires_strict_account(task: dict | None) -> bool:
    task = task or {}
    packet = _packet(task)
    workflow_id = str(task.get("workflow_id") or packet.get("workflow_id") or "")
    text = " ".join(
        str(task.get(key) or "")
        for key in ("title", "description", "latest_turn_summary", "scope_topic", "verdict_target")
    )
    code = _subject_code(text)
    if code in _TARGET_SUBJECT_CODES:
        return True
    if workflow_id and code != "0450":
        return True
    return False


def _verdict_source(latest: dict, task: dict) -> str:
    if latest:
        reviewer = str(latest.get("reviewer") or "-")
        at_ms = int(latest.get("at_ms") or 0)
        return f"latest_authoritative_verdict:{reviewer}:{at_ms}"
    if str(task.get("verdict") or ""):
        return "task.verdict"
    return "source_missing"


def _qbank_state(task: dict, packet: dict) -> tuple[str, str]:
    qbank = task.get("qbank") or {}
    if not isinstance(qbank, dict):
        qbank = {}
    state = str(
        _first_present(
            qbank.get("lifecycle_state"),
            task.get("qbank_lifecycle_state"),
            qbank.get("status"),
            task.get("qbank_status"),
            packet.get("qbank_readiness"),
        )
        or ""
    )
    if state:
        if qbank.get("lifecycle_state"):
            return state, "task.qbank.lifecycle_state"
        if task.get("qbank_lifecycle_state"):
            return state, "task.qbank_lifecycle_state"
        if qbank.get("status"):
            return state, "task.qbank.status"
        if task.get("qbank_status"):
            return state, "task.qbank_status"
        return state, "evidence_packet.qbank_readiness"
    return "", "source_missing"


def _legacy_full_subject_machine_evidence(
    task: dict,
    *,
    packet: dict,
    latest: dict,
    items_count: int | None,
    qql_count: int | None,
    manifest_evidence: Any,
    manifest_rows: int | None,
) -> dict:
    """Return legacy closeout evidence compatibility for pre-account tasks.

    Older Package 1-5 review packets used qa_count/item_count plus sampled
    files/checks, without the Package 6 account fields. That is enough only
    when the latest review is an approved full-subject verdict and both QQL
    and items counts are explicitly present. `items_mapping_count` may explain
    manifest coverage, but it never stands in for real item evidence here.
    """
    latest_verdict = str(latest.get("verdict") or task.get("verdict") or "")
    latest_scope = str(latest.get("verdict_scope") or task.get("verdict_scope") or "")
    if latest_verdict != "approved" or latest_scope != "full_subject":
        return {"applies": False}
    if items_count is None or items_count <= 0 or qql_count is None or qql_count <= 0:
        return {"applies": False}
    has_machine_trace = any(
        packet.get(key)
        for key in (
            "files_sampled",
            "q_ids_checked",
            "calculation_or_concept_checks",
            "path_naming_result",
        )
    )
    if not has_machine_trace:
        return {"applies": False}
    if manifest_rows is not None:
        return {
            "applies": True,
            "manifest_evidence": (
                manifest_evidence
                if manifest_evidence not in (None, "", [], {})
                else "legacy_review_packet"
            ),
            "manifest_rows": manifest_rows,
            "manifest_source": "legacy_review_packet.existing_manifest_rows",
        }
    mapping_rows = _as_int(packet.get("items_mapping_count"))
    if mapping_rows is None:
        mapping_rows = items_count if items_count == qql_count else None
    if mapping_rows is None or mapping_rows <= 0:
        return {"applies": False}
    return {
        "applies": True,
        "manifest_evidence": (
            manifest_evidence
            if manifest_evidence not in (None, "", [], {})
            else "legacy_review_packet"
        ),
        "manifest_rows": mapping_rows,
        "manifest_source": (
            "evidence_packet.items_mapping_count"
            if _as_int(packet.get("items_mapping_count")) is not None
            else "legacy_review_packet.counts_match"
        ),
    }


def _recommended_action(missing: list[str], conflicts: list[str], *, active_revision: bool) -> str:
    if active_revision:
        return "clear_revision_priority_before_closeout_or_rollover"
    if conflicts:
        return "resolve_evidence_account_conflict"
    if missing:
        return "complete_closeout_evidence_account"
    return "manager_formal_closeout"


def build_evidence_account(
    task: dict | None,
    *,
    verifier_result: dict | None = None,
    scanner_anomalies: list[dict] | None = None,
    closeout_status: dict | None = None,
    active_revision_priority: bool = False,
) -> dict:
    """Build a structured account that explains closeout readiness.

    The account is intentionally derived from existing task/verifier/gate
    fields. It does not execute verification or mutate workflow state.
    """
    task = task or {}
    packet = _packet(task)
    snapshot = _snapshot(task)
    latest = _latest(task)
    verifier = _verifier(verifier_result)
    if not verifier and isinstance(task.get("verifier_result"), dict):
        verifier = task.get("verifier_result") or {}
    if not verifier and isinstance(task.get("verifier"), dict):
        verifier = task.get("verifier") or {}
    gate = closeout_status or {}
    anomalies = scanner_anomalies or []

    workflow_id = str(task.get("workflow_id") or packet.get("workflow_id") or "")
    task_id = str(task.get("id") or packet.get("task_id") or "")
    scope = _scope_value(task, packet)
    items_count, items_source = _source_for_count("items_count", packet, snapshot, verifier)
    qql_count, qql_source = _source_for_count("qql_count", packet, snapshot, verifier)
    manifest_evidence, manifest_source = _manifest_value(packet, snapshot, verifier)
    manifest_rows = _manifest_rows_from_sources(packet, snapshot, verifier, manifest_evidence)
    declared_scope = _first_present(
        packet.get("batch_range"),
        task.get("scope_topic"),
        task.get("verdict_target"),
    )
    legacy = _legacy_full_subject_machine_evidence(
        task,
        packet=packet,
        latest=latest,
        items_count=items_count,
        qql_count=qql_count,
        manifest_evidence=manifest_evidence,
        manifest_rows=manifest_rows,
    )
    if legacy.get("applies"):
        manifest_evidence = legacy["manifest_evidence"]
        manifest_rows = int(legacy["manifest_rows"])
        manifest_source = str(legacy["manifest_source"])
    strict = requires_strict_account(task)
    if strict and "items_count" not in packet and "items_count" not in snapshot:
        explicit_items = _as_int(verifier.get("items_count"))
        if explicit_items is not None:
            items_count = explicit_items
            items_source = "subject_verifier.items_count"
    if strict and "qql_count" not in packet and "qql_count" not in snapshot:
        explicit_qql = _as_int(verifier.get("qql_count"))
        if explicit_qql is not None:
            qql_count = explicit_qql
            qql_source = "subject_verifier.qql_count"

    latest_verdict = str(latest.get("verdict") or task.get("verdict") or "")
    latest_outcome = str(latest.get("outcome") or "")
    latest_scope = str(latest.get("verdict_scope") or task.get("verdict_scope") or "")
    subject_verifier_status = str(verifier.get("status") or "")
    subject_verifier_source = "subject_verifier" if verifier else (
        "task.verifier_result" if isinstance(task.get("verifier_result"), dict) else "source_missing"
    )
    qbank_state, qbank_source = _qbank_state(task, packet)

    missing: list[str] = []
    conflicts: list[str] = []

    if not workflow_id:
        missing.append("workflow_id")
    if not task_id:
        missing.append("task_id")
    if not declared_scope:
        missing.append("batch_range_or_scope")
    if items_count is None or items_count <= 0:
        missing.append("items_count")
    if qql_count is None or qql_count <= 0:
        missing.append("qql_count")
    if manifest_evidence in (None, "", [], {}):
        missing.append("manifest_evidence")
    if manifest_rows is None:
        missing.append("manifest_rows")
    if not latest:
        missing.append("latest_authoritative_review_verdict")
    if strict and not subject_verifier_status and not legacy.get("applies"):
        missing.append("subject_verifier_status")

    if latest and latest_verdict != "approved":
        conflicts.append(f"latest_review_verdict_blocks_closeout:{latest_verdict or latest_outcome or 'unknown'}")
    if latest and latest_scope and latest_scope != "full_subject":
        conflicts.append(f"latest_review_scope_insufficient:{latest_scope}")
    if subject_verifier_status in {"fail", "warn"}:
        conflicts.append(f"subject_verifier_{subject_verifier_status}")
    if verifier.get("scope") and verifier.get("scope") != "subject":
        conflicts.append(f"subject_verifier_scope_is_{verifier.get('scope')}")
    if items_count is not None and qql_count is not None and items_count != qql_count:
        conflicts.append(f"items_qql_count_drift:items={items_count}:qql={qql_count}")
    if qql_count is not None and manifest_rows is not None and qql_count != manifest_rows:
        conflicts.append(f"qql_manifest_count_drift:qql={qql_count}:manifest={manifest_rows}")
    if items_count is not None and manifest_rows is not None and items_count != manifest_rows:
        conflicts.append(f"items_manifest_count_drift:items={items_count}:manifest={manifest_rows}")
    if manifest_rows is not None and (items_count is None or qql_count is None):
        conflicts.append("manifest_only_completion_untrusted")
    if qbank_state and qbank_state not in _READY_QBANK_STATES:
        conflicts.append(f"qbank_not_ready:{qbank_state}")
    if active_revision_priority or str(task.get("revision_priority") or ""):
        conflicts.append(f"revision_priority_active:{task.get('revision_priority') or 'active'}")

    for row in anomalies:
        category = str(row.get("category") or "")
        if category in {"stale_execution_context", "evidence_account_conflict"}:
            conflicts.append(category)
        elif category in {"evidence_packet_incomplete", "evidence_account_incomplete"}:
            missing.append(category)

    missing = list(dict.fromkeys(missing))
    conflicts = list(dict.fromkeys(conflicts))
    closeout_ready = not missing and not conflicts
    recommended = _recommended_action(
        missing,
        conflicts,
        active_revision=active_revision_priority or bool(str(task.get("revision_priority") or "")),
    )

    # Derive tier status from evidence depth (mirrors tasks._derive_tier_status).
    tier_status = str(task.get("tier_status") or "")
    if not tier_status:
        workflow_id = str(task.get("workflow_id") or "")
        verdict = str(latest.get("verdict") or task.get("verdict") or "")
        scope = str(latest.get("verdict_scope") or task.get("verdict_scope") or "")
        qbank_ready = qbank_state in _READY_QBANK_STATES
        is_ap = "ap" in workflow_id.lower() or "ap-" in (task.get("title") or "").lower()
        if verdict == "approved":
            if qbank_ready and scope == "full_subject":
                tier_status = "qbank_agent_ready"
            elif scope == "full_subject":
                tier_status = "subject_sample_ready"
            elif scope in {"unit", "package"} or "unit" in (task.get("title") or "").lower():
                tier_status = "unit_package_ready"
            else:
                tier_status = "unit_seed_ready"
        elif is_ap:
            tier_status = "unit_seed_ready"

    return {
        "workflow_id": workflow_id,
        "task_id": task_id,
        "stage": str(task.get("stage") or ""),
        "status": str(task.get("status") or ""),
        "verdict": str(task.get("verdict") or ""),
        "batch_range": str(packet.get("batch_range") or ""),
        "scope": scope,
        "tier_status": tier_status,
        "items_count": items_count,
        "items_source": items_source,
        "qql_count": qql_count,
        "qql_source": qql_source,
        "manifest_evidence": manifest_evidence,
        "manifest_rows": manifest_rows,
        "manifest_source": manifest_source,
        "latest_authoritative_review_verdict": latest,
        "latest_authoritative_review_verdict_source": _verdict_source(latest, task),
        "subject_verifier_status": subject_verifier_status,
        "subject_verifier_source": subject_verifier_source,
        "qbank_readiness": qbank_state,
        "qbank_readiness_source": qbank_source,
        "missing_evidence": missing,
        "conflicting_evidence": conflicts,
        "closeout_ready": closeout_ready,
        "recommended_action": recommended,
        "closeout_status": str(gate.get("closeout_status") or ""),
    }


def closeout_recommendation_allowed(account: dict, action_code: str) -> bool:
    """Return False when an account should suppress closeout/rollover actions."""
    if action_code not in _BLOCKING_RECOMMENDATIONS:
        return True
    return bool(account.get("closeout_ready"))
