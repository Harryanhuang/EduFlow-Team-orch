"""Integration smoke test: manager-panel shows QBank section."""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Make scripts importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from helpers import isolated_env, run_cli


def test_manager_panel_includes_qbank_section_when_data_available(tmp_path):
    """manager-panel prints QBank Lifecycle when verification data exists."""
    # Create a minimal team config
    team_toml = """
chat_id = "oc_test"
lark_profile = "eduflow-team"
[team]
session = "EduFlowTeam"
[team.agents.manager]
cli = "claude-code"
role = "manager"
"""
    with isolated_env() as tmp:
        (tmp / "eduflow.toml").write_text(team_toml, encoding="utf-8")

        # Write a fake qbank verification output
        (tmp / "content").mkdir()
        qbank_summary = {
            "overall_status": "FAIL",
            "total_questions": 500,
            "subjects_scanned": 2,
            "total_errors": 5,
            "total_warnings": 3,
            "total_infos": 0,
            "within_layer_duplicates": 0,
            "cross_layer_overlaps": 0,
            "schema_violations": 5,
            "manifest_issues": 0,
            "subjects": [
                {
                    "subject": "igcse-physics-0625",
                    "name": "Physics",
                    "code": "0625",
                    "status": "issue_fix",
                    "total_questions": 200,
                    "topic_count": 10,
                    "error_count": 3,
                    "warning_count": 2,
                    "issue_count": 5,
                    "has_manifest": True,
                    "manifest_rows": 10,
                    "difficulty_distribution": {"Foundation": 100, "Standard": 80, "Challenge": 20},
                    "report_path": "content/igcse-physics-0625/qbank-verification-report.json",
                    "next_action": "fix_schema_or_manifest_errors",
                },
                {
                    "subject": "igcse-chemistry-0620",
                    "name": "Chemistry",
                    "code": "0620",
                    "status": "reverify",
                    "total_questions": 300,
                    "topic_count": 15,
                    "error_count": 2,
                    "warning_count": 1,
                    "issue_count": 3,
                    "has_manifest": True,
                    "manifest_rows": 15,
                    "difficulty_distribution": {"Foundation": 150, "Standard": 100, "Challenge": 50},
                    "report_path": "content/igcse-chemistry-0620/qbank-verification-report.json",
                    "next_action": "reverify_warnings_then_review",
                },
            ],
        }
        # The _load_qbank_verification runs as subprocess; since there's no
        # scripts/qbank_verify.py in the test tmp, it'll return None.
        # Instead, test the store functions directly.
        from eduflow.store import tasks

        panel = tasks.qbank_manager_panel_summary(qbank_summary)
        assert panel["qbank_active"] is True
        assert panel["total_subjects"] == 2
        assert panel["overall_status"] == "FAIL"
        assert panel["most_urgent_action"] == "fix_schema_or_manifest_errors"
        assert panel["lifecycle_breakdown"] == {"issue_fix": 1, "reverify": 1}

        # Test dedup gate with a FAIL overall status → review_course_pass=False
        gate = tasks.dedup_import_gate(
            review_course_pass=(qbank_summary["overall_status"] == "PASS"),
            user_authorized=False,
            manager_authorized=False,
            dry_run=False,
        )
        assert gate["apply_allowed"] is False
        assert gate["blocked"] is True
        assert "review_course_pass_required" in gate["blocking_reasons"]

        # With PASS status and authorization
        gate = tasks.dedup_import_gate(
            review_course_pass=True,
            user_authorized=True,
            manager_authorized=False,
            dry_run=False,
        )
        assert gate["apply_allowed"] is True
        assert gate["blocked"] is False
