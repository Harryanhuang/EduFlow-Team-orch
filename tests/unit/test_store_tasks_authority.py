"""Tests for Package 3: Review Verdict Authority.

This package makes `review_course`'s latest structured verdict the hard
gate for subject closeout. Older PASSes cannot override newer FAILs;
partial-scope PASSes (QQL-only, items-only, manifest, package) cannot
satisfy full_subject closeout; and manager-actions / manager-panel must
not emit a "正式收口" suggestion when the gate is false.
"""
from __future__ import annotations

from helpers import isolated_env
from eduflow.store import local_facts, task_event_scanner, tasks


FULL_SUBJECT_EVIDENCE = {
    "files_sampled": ["Q-1.md"],
    "q_ids_checked": ["Q-1"],
    "calculation_or_concept_checks": ["checked"],
    "path_naming_result": "pass",
    "qa_count": 300,
    "item_count": 300,
    "workflow_id": "igcse-subject-launch",
    "task_id": "T-1",
    "batch_range": "1",
    "items_count": 300,
    "qql_count": 300,
    "manifest_evidence": "manifest.csv",
}


def _make_approved_subject(*, title="IGCSE Biology 0610", evidence=None,
                            verdict_target=None):
    # Append a subject completion marker so the closeout gate recognizes
    # this as a subject closeout candidate.
    title = f"{title} 正式完成"
    tid = tasks.create_flow(
        "worker_course", title,
        stage="curriculum", owner="worker_course", creator="manager",
        description="Subject final batch 正式完成",
    )
    tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
    tasks.transition_flow(tid, to_status="assigned", actor="manager")
    tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
    tasks.submit_for_review(tid, actor="worker_course")
    tasks.review_flow(
        tid, outcome="approve", actor="review_course",
        review_reason="approved_for_delivery",
        verdict_target=verdict_target or title,
        evidence_packet=evidence or FULL_SUBJECT_EVIDENCE,
    )
    return tid


def _make_reviewed_then_rejected(*, title="IGCSE Biology 0610"):
    """Create a subject with an old full_subject PASS followed by a new FAIL.

    The flow state machine does not allow delivered -> in_progress, so we
    directly mutate the task row to simulate a second review handoff. The
    key invariant under test is that `latest_authoritative_verdict` (the
    newest review event) wins over any older PASS.
    """
    tid = _make_approved_subject(title=title)
    data = tasks._load()
    task = next(t for t in data["tasks"] if t["id"] == tid)
    # Preserve an old approved verdict in the event log, then reset the
    # task to submitted_for_review so review_flow can record a new FAIL.
    old_verdict = task["latest_authoritative_verdict"]
    old_verdict["verdict_target"] = title
    old_verdict["verdict_scope"] = "full_subject"
    task["status"] = "submitted_for_review"
    task["verdict"] = "pending"
    task["blocking_reason"] = ""
    task["manager_action_type"] = ""
    task["review_reason"] = ""
    task["latest_turn_summary"] = "worker repaired items and resubmitted"
    task["closeout_status"] = ""
    task["completed_at"] = None
    tasks._save(data)

    # Latest verdict: FAIL on items layer
    tasks.review_flow(
        tid, outcome="reject", actor="review_course",
        review_reason="changes_requested",
        latest_turn_summary="items layer incomplete",
        verdict_target="items only",
        required_fix=["expand per-topic items to 9", "fix QQL-to-items mapping"],
        blocking_files=["items/T1.1.md", "items/T1.2.md"],
    )
    return tid


def test_latest_review_fail_blocks_old_pass_closeout():
    """An older approved verdict must not authorize closeout once review_course
    has issued a newer FAIL.
    """
    with isolated_env():
        tid = _make_reviewed_then_rejected()
        gate = tasks.subject_closeout_status(tasks.get(tid))
        assert gate["closeout_status"] == "closeout_blocked_review_not_approved"
        assert gate["closeout_gate_review_approved"] is False
        assert "latest_verdict_rejected" in gate["verdict_authority_reasons"]

        # manager_closeout_subject must refuse
        try:
            tasks.manager_closeout_subject(tid, actor="manager",
                                           skip_subject_verifier=True)
        except ValueError as exc:
            assert "not ready" in str(exc)
        else:
            raise AssertionError("expected closeout to be blocked by latest FAIL")


def test_qql_only_pass_cannot_satisfy_full_subject_closeout():
    """A reviewer PASS scoped to QQL only is not authoritative for subject closeout."""
    with isolated_env():
        tid = _make_approved_subject(
            title="IGCSE Biology 0610",
            verdict_target="QQL only",
            evidence=FULL_SUBJECT_EVIDENCE,
        )
        gate = tasks.subject_closeout_status(tasks.get(tid))
        assert gate["verdict_scope"] == "qql_only"
        assert gate["closeout_status"] == "closeout_blocked_review_not_approved"
        assert gate["closeout_gate_review_approved"] is False
        assert any("verdict_scope_insufficient" in r
                   for r in gate["verdict_authority_reasons"])


def test_items_layer_fail_blocks_subject_closeout():
    """items-layer FAIL must prevent subject closeout even if QQL layer passed before."""
    with isolated_env():
        tid = _make_reviewed_then_rejected(title="IGCSE Biology 0610")
        row = tasks.get(tid)
        latest = row["latest_authoritative_verdict"]
        assert latest["verdict"] == "rejected"
        assert latest["verdict_scope"] == "items_only"
        assert latest["required_fix"] == [
            "expand per-topic items to 9", "fix QQL-to-items mapping"
        ]
        assert latest["blocking_files"] == [
            "items/T1.1.md", "items/T1.2.md"
        ]


def test_worker_self_repair_does_not_supersede_latest_fail():
    """Worker '已修好' log after a reviewer FAIL must not clear the verdict."""
    with isolated_env():
        tid = _make_reviewed_then_rejected(title="IGCSE Biology 0610")
        # Simulate worker self-reporting repair without a new review
        local_facts.append_log(
            "worker_course", "say",
            "Biology 0610 已修好，items 文件已补齐。",
        )
        findings = task_event_scanner.scan_manager_anomalies()
        conflict = [
            f for f in findings
            if f.get("task_id") == tid
            and f.get("category") == "review_truth_conflict"
            and f.get("subtype") == "worker_self_repair_supersedes_latest_fail"
        ]
        assert len(conflict) == 1
        assert conflict[0]["recommended_action"] == "require_review_course_re_review_before_closeout"

        # Closeout is still blocked
        gate = tasks.subject_closeout_status(tasks.get(tid))
        assert gate["closeout_status"] == "closeout_blocked_review_not_approved"


def test_manager_actions_suppresses_closeout_text_when_gate_false():
    """manager-actions must not print a '正式收口' suggestion when the latest
    authoritative verdict blocks closeout.
    """
    with isolated_env():
        tid = _make_reviewed_then_rejected(title="IGCSE Biology 0610")
        findings = task_event_scanner.scan_manager_anomalies()
        action_packets = [
            f.get("action_packet") for f in findings
            if f.get("task_id") == tid and f.get("action_packet")
        ]
        closeout_packets = [
            p for p in action_packets
            if p.get("action_code") == "manager_formal_closeout"
        ]
        assert closeout_packets == [], (
            "manager_formal_closeout action should not be emitted when latest verdict is FAIL"
        )
        # Instead, a blocker/re-review action is emitted
        blocker = [
            p for p in action_packets
            if p.get("action_code") == "wait_for_worker_repair_and_re_review"
        ]
        assert len(blocker) == 1
        assert blocker[0]["apply_allowed"] is False
        assert "不得" in blocker[0]["suggested_brief"] or "返修" in blocker[0]["suggested_brief"]


def test_task_state_reflects_latest_authoritative_verdict():
    """The task row must carry the latest authoritative verdict struct, and
    downstream surfaces must read it instead of the static verdict field.
    """
    with isolated_env():
        tid = _make_reviewed_then_rejected(title="IGCSE Biology 0610")
        row = tasks.get(tid)
        latest = row.get("latest_authoritative_verdict") or {}
        assert latest["outcome"] == "reject"
        assert latest["verdict"] == "rejected"
        assert latest["verdict_scope"] == "items_only"
        assert latest["reviewer"] == "review_course"
        assert latest["is_authoritative"] is True
        # Evidence snapshot is captured
        assert "evidence_snapshot" in row
        assert "evidence_snapshot_hash" in row
        # Required fix / blocking files survive
        assert row.get("required_fix") == latest["required_fix"]
        assert row.get("blocking_files") == latest["blocking_files"]


def test_full_subject_pass_authorizes_closeout():
    """A full_subject approved verdict still authorizes closeout when all
    other gates are satisfied.
    """
    with isolated_env():
        tid = _make_approved_subject(
            title="IGCSE Biology 0610",
            verdict_target="IGCSE Biology 0610",
            evidence=FULL_SUBJECT_EVIDENCE,
        )
        gate = tasks.subject_closeout_status(tasks.get(tid))
        assert gate["verdict_scope"] == "full_subject"
        assert gate["closeout_status"] == "closeout_ready"
        assert gate["closeout_gate_review_approved"] is True

        ok = tasks.manager_closeout_subject(tid, actor="manager",
                                            skip_subject_verifier=True)
        assert ok is True
        assert tasks.get(tid)["closeout_status"] == "closeout_completed"


def test_manager_closeout_signal_with_latest_fail_is_blocked():
    """Even if manager logs a formal closeout signal in chat, the latest FAIL
    prevents the action packet from advertising closeout.
    """
    with isolated_env():
        tid = _make_reviewed_then_rejected(title="IGCSE Biology 0610")
        local_facts.append_log(
            "manager", "say",
            "Biology 0610 正式闭环，进入下一学科。",
        )
        findings = task_event_scanner.scan_manager_anomalies()
        visible_conflict = [
            f for f in findings
            if f.get("task_id") == tid
            and f.get("category") == "review_truth_conflict"
            and f.get("subtype") == "visible_closeout_contradicts_latest_fail"
        ]
        assert len(visible_conflict) == 1
        assert visible_conflict[0]["severity"] == "error"
        assert visible_conflict[0]["live_blocker"] is True


def test_manager_closeout_signal_after_latest_fail_downgrades_action():
    """Codex HIGH #1: when manager logs a closeout signal but the latest
    authoritative verdict is FAIL, the manager-actions surface must
    surface a `wait_for_*` / re-review action, NOT a contradictory
    `manager_formal_closeout` packet.
    """
    with isolated_env():
        tid = _make_reviewed_then_rejected(title="IGCSE Biology 0610")
        local_facts.append_log(
            "manager", "say",
            "Biology 0610 正式闭环，进入下一学科。",
        )
        findings = task_event_scanner.scan_manager_anomalies()
        manager_closeout_finding = [
            f for f in findings
            if f.get("task_id") == tid
            and f.get("category") == "manager_closeout_but_task_pending"
        ]
        assert len(manager_closeout_finding) >= 1
        # The Codex fix routes the action to a wait / re-review path
        # instead of advertising manager_formal_closeout.
        packet = manager_closeout_finding[0].get("action_packet") or {}
        assert packet.get("action_code") != "manager_formal_closeout"
        assert packet.get("action_code") in {
            "wait_for_worker_repair_and_re_review",
            "resolve_manager_action_then_re_review",
            "request_full_subject_review_recheck",
            "reconcile_review_truth_with_latest_verdict",
        }
        assert packet.get("apply_allowed") is False
        assert "不得" in packet.get("suggested_brief", "") or \
               "返修" in packet.get("suggested_brief", "")


def test_qql_items_combined_target_is_not_full_subject():
    """Codex MEDIUM #2: 'QQL + items' combined review covers two of
    three layers; it must NOT promote to `full_subject`. The closeout
    gate should refuse subject closeout because manifest is missing.
    Package 3 follow-up: the verdict_scope is now the recognized
    `qql_items` (not empty), so the manager-actions surface can
    explain "QQL+items reviewed, manifest layer still pending".
    """
    with isolated_env():
        tid = _make_approved_subject(
            title="IGCSE Biology 0610",
            verdict_target="QQL + items layer",
            evidence=FULL_SUBJECT_EVIDENCE,
        )
        gate = tasks.subject_closeout_status(tasks.get(tid))
        assert gate["verdict_scope"] == "qql_items"
        assert gate["closeout_gate_review_approved"] is False
        assert gate["closeout_status"] == "closeout_blocked_review_not_approved"
        # `verdict_scope_insufficient:qql_items` blocks closeout
        # because qql_items is NOT in SUBJECT_CLOSEOUT_AUTHORITATIVE_SCOPES.
        assert any("verdict_scope_insufficient:qql_items" in r
                   for r in gate["verdict_authority_reasons"])


def test_qql_items_scope_is_recognized_but_not_authoritative():
    """Package 3 follow-up: 'QQL + items' is now the recognized
    `qql_items` scope (added to VERDICT_SCOPES). The reviewer can
    see this scope in the task state and manager panel, but the
    closeout gate still refuses subject closeout.
    """
    with isolated_env():
        # Direct unit test of the derivation helper.
        from eduflow.store import tasks as _t
        assert _t.derive_verdict_scope_from_target("QQL + items layer") == "qql_items"
        assert _t.derive_verdict_scope_from_target("QQL+items") == "qql_items"
        assert _t.derive_verdict_scope_from_target("QQL and items") == "qql_items"
        # "qql_items" is a recognized scope but NOT authoritative.
        assert "qql_items" in _t.VERDICT_SCOPES
        assert "qql_items" not in _t.SUBJECT_CLOSEOUT_AUTHORITATIVE_SCOPES
        # An end-to-end task with qql_items verdict still has
        # closeout blocked.
        tid = _make_approved_subject(
            title="IGCSE Biology 0610",
            verdict_target="QQL + items",
            evidence=FULL_SUBJECT_EVIDENCE,
        )
        t = tasks.get(tid)
        assert t["verdict_scope"] == "qql_items"
        assert tasks.is_verdict_authoritative_for_closeout(t) is False
        gate = tasks.subject_closeout_status(t)
        assert gate["closeout_status"] == "closeout_blocked_review_not_approved"


def test_legacy_approved_without_verdict_target_is_flagged():
    """Codex MEDIUM #3: a legacy approved task without verdict_target
    or latest_authoritative_verdict must NOT silently become
    full_subject. The closeout gate must surface the missing scope
    as an explicit blocker reason.
    """
    with isolated_env():
        # Create + directly transition to delivered with approved verdict
        # but NO verdict_target, NO latest_authoritative_verdict.
        # We use the private _load/_save helpers because the public
        # review_flow() requires verdict_target to set scope.
        tid = tasks.create_flow(
            "worker_course", "IGCSE Biology 0610 正式完成",
            stage="curriculum", owner="worker_course", creator="manager",
            description="Subject final batch 正式完成",
        )
        data = tasks._load()
        task = next(t for t in data["tasks"] if t["id"] == tid)
        task["status"] = "delivered"
        task["verdict"] = "approved"
        # Intentionally leave verdict_target="" and
        # latest_authoritative_verdict={}.
        tasks._save(data)

        gate = tasks.subject_closeout_status(tasks.get(tid))
        assert gate["verdict_scope"] == ""
        assert gate["closeout_gate_review_approved"] is False
        assert "missing_verdict_target_on_approved_task" in gate["verdict_authority_reasons"]
        # Manager-actions must surface a re-declare-scope action, not
        # a manager_formal_closeout packet.
        findings = task_event_scanner.scan_manager_anomalies()
        # Find any finding tagged with the legacy approved reason.
        latest_truth = [
            f for f in findings
            if f.get("task_id") == tid
            and f.get("category") == "review_truth_conflict"
            and f.get("subtype") == "missing_verdict_target_on_approved_task"
        ]
        assert len(latest_truth) == 1
        assert latest_truth[0]["severity"] == "warn"


def test_visible_closeout_conflict_and_manager_closeout_action_are_complementary():
    """When manager 口头宣布 closeout AND latest verdict is FAIL,
    two findings fire on the same task with distinct purposes:

    - `review_truth_conflict / visible_closeout_contradicts_latest_fail`
      is the ALERT (severity=error, live_blocker=True). It tells the
      operator "chat contradicts structured truth". It carries no
      action_packet so it doesn't appear in the manager-actions
      action list, but it does appear in the manager-panel
      "Anomalies (non-actionable)" section.

    - `manager_closeout_but_task_pending / blocked_by_latest_verdict`
      is the ACTION. It carries an action_packet (e.g.
      `wait_for_worker_repair_and_re_review`) with apply_allowed=False.
      It appears in the manager-actions list AND in the panel
      "Next Executable Actions" section.

    The two are complementary, not redundant. Both surface because
    the alert explains WHY and the action explains WHAT TO DO NEXT.
    """
    with isolated_env():
        tid = _make_reviewed_then_rejected(title="IGCSE Biology 0610")
        local_facts.append_log(
            "manager", "say",
            "Biology 0610 正式闭环，进入下一学科。",
        )
        findings = task_event_scanner.scan_manager_anomalies()
        task_findings = [f for f in findings if f.get("task_id") == tid]

        # Alert: review_truth_conflict / visible_closeout_contradicts_latest_fail
        alert = [
            f for f in task_findings
            if f.get("category") == "review_truth_conflict"
            and f.get("subtype") == "visible_closeout_contradicts_latest_fail"
        ]
        assert len(alert) == 1
        assert alert[0]["severity"] == "error"
        assert alert[0]["live_blocker"] is True
        # Alert carries no action_packet.
        assert alert[0].get("action_packet") is None

        # Action: manager_closeout_but_task_pending / blocked_by_latest_verdict
        action = [
            f for f in task_findings
            if f.get("category") == "manager_closeout_but_task_pending"
            and f.get("subtype") == "blocked_by_latest_verdict"
        ]
        assert len(action) == 1
        # Action carries an action_packet for the operator to act on.
        assert action[0].get("action_packet") is not None
        assert action[0]["action_packet"]["action_code"] != "manager_formal_closeout"

        # The two findings carry distinct recommended_action values:
        # alert = "acknowledge_latest_fail_and_block_closeout_until_re_review"
        # action = "wait_for_worker_repair_and_re_review" (or similar blocker)
        assert alert[0]["recommended_action"] != action[0]["recommended_action"]
