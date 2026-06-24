"""Tests for QBank lifecycle / verifier / dedup gate (Package 7)."""
from __future__ import annotations

import json
from pathlib import Path

from helpers import isolated_env
from eduflow.store import tasks


# ── qbank_verify.py auto-discovery ─────────────────────────────────

def test_discover_igcse_subjects_finds_known_dirs(tmp_path):
    from scripts.qbank_verify import discover_igcse_subjects

    content = tmp_path / "content"
    content.mkdir()
    (content / "igcse-physics-0625").mkdir()
    (content / "igcse-chemistry-0620").mkdir()
    (content / "igcse-mathematics-0580").mkdir()
    (content / "random-folder").mkdir()
    (content / "qbank-dedup-dryrun-plan.md").write_text("placeholder")

    subjects = discover_igcse_subjects(content)
    assert "igcse-physics-0625" in subjects
    assert "igcse-chemistry-0620" in subjects
    assert "igcse-mathematics-0580" in subjects
    assert "random-folder" not in subjects
    assert subjects["igcse-physics-0625"]["code"] == "0625"
    assert subjects["igcse-physics-0625"]["name"] == "Physics"


def test_discover_igcse_subjects_handles_empty_dir(tmp_path):
    from scripts.qbank_verify import discover_igcse_subjects

    content = tmp_path / "content"
    content.mkdir()
    subjects = discover_igcse_subjects(content)
    assert subjects == {}


def test_discover_igcse_subjects_handles_missing_dir():
    from scripts.qbank_verify import discover_igcse_subjects

    subjects = discover_igcse_subjects(Path("/nonexistent/path/content"))
    assert subjects == {}


# ── compact JSON summary ───────────────────────────────────────────

def test_build_compact_summary_produces_compact_output():
    from scripts.qbank_verify import build_compact_summary, SubjectReport

    report = SubjectReport(slug="igcse-physics-0625", name="Physics", code="0625",
                           total_questions=50, topic_count=5,
                           has_manifest=True, manifest_rows=50,
                           difficulty_dist={"Foundation": 20, "Standard": 20, "Challenge": 10})
    issues = []
    summary = build_compact_summary([report], issues, [])
    assert summary["overall_status"] == "PASS"
    assert summary["subjects_scanned"] == 1
    subjects = summary["subjects"]
    assert len(subjects) == 1
    subj = subjects[0]
    assert subj["subject"] == "igcse-physics-0625"
    assert subj["status"] == "ready_for_import"
    assert subj["next_action"] == "needs_user_authorization"
    # Compact: no detail_items in default JSON
    assert "detail_items" not in summary


def test_build_compact_summary_with_errors():
    from scripts.qbank_verify import build_compact_summary, Issue, SubjectReport

    report = SubjectReport(slug="igcse-physics-0625", name="Physics", code="0625",
                           total_questions=10, topic_count=2,
                           has_manifest=False)
    issues = [
        Issue("error", "schema", "igcse-physics-0625", "qa/topic1.md", "Missing Answer"),
        Issue("error", "schema", "igcse-physics-0625", "qa/topic1.md", "Invalid difficulty"),
    ]
    summary = build_compact_summary([report], issues, [])
    assert summary["overall_status"] == "FAIL"
    subj = summary["subjects"][0]
    assert subj["status"] == "issue_fix"
    assert subj["next_action"] == "fix_schema_or_manifest_errors"
    assert subj["error_count"] == 2


def test_build_compact_summary_no_manifest_no_errors():
    from scripts.qbank_verify import build_compact_summary, SubjectReport

    report = SubjectReport(slug="igcse-economics-0455", name="Economics", code="0455",
                           total_questions=50, topic_count=5,
                           has_manifest=False)
    summary = build_compact_summary([report], [], [])
    subj = summary["subjects"][0]
    assert subj["status"] == "needs_review"
    assert subj["next_action"] == "review_course_review_required"


def test_build_compact_summary_empty_subject():
    from scripts.qbank_verify import build_compact_summary, SubjectReport

    report = SubjectReport(slug="igcse-biology-0610", name="Biology", code="0610",
                           total_questions=0, topic_count=0,
                           has_manifest=False)
    summary = build_compact_summary([report], [], [])
    subj = summary["subjects"][0]
    assert subj["status"] == "empty"
    assert subj["next_action"] == "no_qa_found_check_content"


# ── QBank lifecycle states ─────────────────────────────────────────

def test_qbank_lifecycle_status_scan_state():
    status = tasks.qbank_lifecycle_status("igcse-physics-0625", None)
    assert status["lifecycle_state"] == "scan"
    assert status["next_action"] == "run_qbank_verify"
    assert status["needs_review"] is True
    assert status["ready_for_import"] is False


def test_qbank_lifecycle_status_issue_fix():
    summary = {
        "overall_status": "FAIL",
        "total_errors": 5,
        "total_warnings": 2,
        "total_questions": 50,
        "subjects_scanned": 1,
        "manifest_issues": 1,
    }
    status = tasks.qbank_lifecycle_status("igcse-physics-0625", summary)
    assert status["lifecycle_state"] == "issue_fix"
    assert status["needs_review"] is True


def test_qbank_lifecycle_status_reverify():
    summary = {
        "overall_status": "PASS",
        "total_errors": 0,
        "total_warnings": 3,
        "total_questions": 100,
        "subjects_scanned": 1,
        "manifest_issues": 1,
    }
    status = tasks.qbank_lifecycle_status("igcse-physics-0625", summary)
    assert status["lifecycle_state"] == "reverify"
    assert status["next_action"] == "review_course_reverify_subject"


def test_qbank_lifecycle_status_ready_for_import():
    summary = {
        "overall_status": "PASS",
        "total_errors": 0,
        "total_warnings": 0,
        "total_questions": 100,
        "subjects_scanned": 1,
        "manifest_issues": 0,
    }
    status = tasks.qbank_lifecycle_status("igcse-physics-0625", summary)
    assert status["lifecycle_state"] == "ready_for_import"
    assert status["needs_review"] is False
    assert status["needs_user_authorization"] is True
    assert status["review_course_pass"] is True


def test_qbank_lifecycle_status_scan_with_zero_questions():
    summary = {
        "overall_status": "PASS",
        "total_errors": 0,
        "total_warnings": 0,
        "total_questions": 0,
        "subjects_scanned": 0,
        "manifest_issues": 0,
    }
    status = tasks.qbank_lifecycle_status("igcse-biology-0610", summary)
    assert status["lifecycle_state"] == "scan"


# ── dedup/import gate ──────────────────────────────────────────────

def test_dedup_import_gate_dry_run_always_allowed():
    gate = tasks.dedup_import_gate(
        review_course_pass=False,
        user_authorized=False,
        manager_authorized=False,
        dry_run=True,
    )
    assert gate["apply_allowed"] is False
    assert gate["blocked"] is False
    assert gate["mode"] == "dry_run"
    assert gate["next_action"] == "review_dry_run_results_then_authorize"


def test_dedup_import_gate_blocked_no_pass_no_auth():
    gate = tasks.dedup_import_gate(
        review_course_pass=False,
        user_authorized=False,
        manager_authorized=False,
        dry_run=False,
    )
    assert gate["apply_allowed"] is False
    assert gate["blocked"] is True
    assert "review_course_pass_required" in gate["blocking_reasons"]
    assert "user_or_manager_authorization_required" in gate["blocking_reasons"]
    assert gate["next_action"] == "complete_review_course_then_authorize"


def test_dedup_import_gate_blocked_pass_but_no_auth():
    gate = tasks.dedup_import_gate(
        review_course_pass=True,
        user_authorized=False,
        manager_authorized=False,
        dry_run=False,
    )
    assert gate["apply_allowed"] is False
    assert gate["blocked"] is True
    assert "review_course_pass_required" not in gate["blocking_reasons"]
    assert "user_or_manager_authorization_required" in gate["blocking_reasons"]
    assert gate["next_action"] == "request_manager_or_user_authorization"


def test_dedup_import_gate_blocked_no_pass_but_auth():
    gate = tasks.dedup_import_gate(
        review_course_pass=False,
        user_authorized=True,
        manager_authorized=False,
        dry_run=False,
    )
    assert gate["apply_allowed"] is False
    assert gate["blocked"] is True
    assert "review_course_pass_required" in gate["blocking_reasons"]
    assert "user_or_manager_authorization_required" not in gate["blocking_reasons"]
    assert gate["next_action"] == "complete_review_course_pass"


def test_dedup_import_gate_allowed_with_pass_and_user_auth():
    gate = tasks.dedup_import_gate(
        review_course_pass=True,
        user_authorized=True,
        manager_authorized=False,
        dry_run=False,
    )
    assert gate["apply_allowed"] is True
    assert gate["blocked"] is False
    assert gate["mode"] == "apply"
    assert gate["blocking_reasons"] == []


def test_dedup_import_gate_allowed_with_pass_and_manager_auth():
    gate = tasks.dedup_import_gate(
        review_course_pass=True,
        user_authorized=False,
        manager_authorized=True,
        dry_run=False,
    )
    assert gate["apply_allowed"] is True
    assert gate["blocked"] is False
    assert gate["mode"] == "apply"


# ── manager-panel QBank summary ────────────────────────────────────

def test_qbank_manager_panel_summary_no_data():
    panel = tasks.qbank_manager_panel_summary(None)
    assert panel["qbank_active"] is False
    assert panel["most_urgent_action"] == "run_qbank_verify_for_status"


def test_qbank_manager_panel_summary_with_data():
    summary = {
        "overall_status": "PASS",
        "total_errors": 0,
        "total_warnings": 1,
        "subjects": [
            {"subject": "igcse-physics-0625", "name": "Physics", "status": "ready_for_import",
             "total_questions": 100, "error_count": 0, "warning_count": 0},
            {"subject": "igcse-chemistry-0620", "name": "Chemistry", "status": "issue_fix",
             "total_questions": 50, "error_count": 3, "warning_count": 2},
        ],
    }
    panel = tasks.qbank_manager_panel_summary(summary)
    assert panel["qbank_active"] is True
    assert panel["total_subjects"] == 2
    assert panel["most_urgent_action"] == "fix_schema_or_manifest_errors"
    assert "issue_fix" in panel["lifecycle_breakdown"]
    assert "ready_for_import" in panel["lifecycle_breakdown"]


def test_qbank_manager_panel_summary_most_urgent_issue_fix():
    summary = {
        "overall_status": "FAIL",
        "total_errors": 5,
        "total_warnings": 0,
        "subjects": [
            {"subject": "igcse-physics-0625", "name": "Physics", "status": "issue_fix",
             "total_questions": 50, "error_count": 5, "warning_count": 0},
            {"subject": "igcse-chemistry-0620", "name": "Chemistry", "status": "ready_for_import",
             "total_questions": 100, "error_count": 0, "warning_count": 0},
        ],
    }
    panel = tasks.qbank_manager_panel_summary(summary)
    # issue_fix (priority 0) is more urgent than ready_for_import (priority 4)
    assert panel["most_urgent_action"] == "fix_schema_or_manifest_errors"


def test_qbank_lifecycle_next_actions_are_complete():
    for state in tasks.QBANK_LIFECYCLE_STATES:
        assert state in tasks.QBANK_LIFECYCLE_NEXT_ACTIONS, f"missing next_action for {state}"


# ── verify task stage supports qbank ───────────────────────────────

def test_qbank_stage_allows_standard_flow_statuses():
    """QBank stage must allow the standard flow statuses (queued, assigned, etc.)."""
    from eduflow.store.tasks import FLOW_ALLOWED_STAGE_STATUSES, canonical_stage

    allowed = FLOW_ALLOWED_STAGE_STATUSES.get("qbank")
    assert allowed is not None, "qbank stage must be in FLOW_ALLOWED_STAGE_STATUSES"
    assert "queued" in allowed
    assert "assigned" in allowed
    assert "in_progress" in allowed
    assert "blocked" in allowed
    assert "delivered" in allowed
    assert "cancelled" in allowed


def test_qbank_stage_is_registered():
    from eduflow.store.tasks import FLOW_STAGES

    assert "qbank" in FLOW_STAGES


# ── add to test_commands_messaging.py: QBank authorization gate test ──

def test_qbank_authorization_blocked_without_review_pass():
    """Dedup/import apply must be blocked when review_course hasn't passed."""
    gate = tasks.dedup_import_gate(
        review_course_pass=False,
        user_authorized=False,
        manager_authorized=False,
        dry_run=False,
    )
    assert gate["apply_allowed"] is False
    assert gate["blocked"] is True
    assert "review_course_pass_required" in gate["blocking_reasons"]
    assert "user_or_manager_authorization_required" in gate["blocking_reasons"]


def test_qbank_dry_run_is_not_authorization():
    """Dry-run must never count as authorization."""
    gate = tasks.dedup_import_gate(
        review_course_pass=True,
        user_authorized=False,
        manager_authorized=False,
        dry_run=True,
    )
    assert gate["apply_allowed"] is False
    assert gate["mode"] == "dry_run"
    assert gate["blocked"] is False


def test_qbank_apply_allowed_with_pass_and_authorization():
    """All conditions met → apply allowed."""
    gate = tasks.dedup_import_gate(
        review_course_pass=True,
        user_authorized=True,
        manager_authorized=False,
        dry_run=False,
    )
    assert gate["apply_allowed"] is True
    assert gate["blocked"] is False


def test_qbank_manager_panel_shows_blocked_dedup_gate():
    """Manager panel dedup gate summary for a FAILed verification."""
    summary = {
        "overall_status": "FAIL",
        "total_errors": 3,
        "total_warnings": 1,
        "subjects": [
            {"subject": "igcse-chemistry-0620", "name": "Chemistry", "status": "issue_fix",
             "total_questions": 50, "error_count": 3, "warning_count": 1},
        ],
    }
    panel = tasks.qbank_manager_panel_summary(summary)
    assert panel["overall_status"] == "FAIL"
    assert panel["total_errors"] == 3
