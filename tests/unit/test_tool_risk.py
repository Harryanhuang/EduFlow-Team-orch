"""Tests for store/tool_risk.py and `task tool-risk` CLI surface.

Package 3: deterministic, read-only risk classifier. The classifier does
NOT block or modify any command — it only returns a structured verdict
so manager/operator-facing surfaces can warn before destructive intents.
"""
from __future__ import annotations

import json
import shlex

import pytest

from helpers import isolated_env, run_cli
from eduflow.store import tool_risk


# ── store: classify ───────────────────────────────────────────────


def test_classify_read_only_command_is_low():
    for cmd in (
        "eduflow task loop-status T-1",
        "eduflow task evidence-explain T-1 --json",
        "eduflow task loop-contract T-1 --json",
        "eduflow task get T-1",
        "eduflow task list",
        "eduflow task tool-risk --command \"eduflow task loop-status T-1\"",
        "eduflow status worker_course",
        "eduflow read T-1",
    ):
        verdict = tool_risk.classify(cmd)
        assert verdict["risk_level"] == "Low", f"{cmd} should be Low, got {verdict}"
        assert verdict["access_mode"] == "auto"
        assert verdict["requires_preflight"] is False
        assert verdict["requires_human_confirm"] is False


def test_classify_medium_local_writes():
    for cmd in (
        "eduflow task create worker_course \"do thing\"",
        "eduflow task update T-1 --status 进行中",
        "eduflow task done T-1",
        "eduflow log worker_course \"x\"",
    ):
        verdict = tool_risk.classify(cmd)
        assert verdict["risk_level"] == "Medium", f"{cmd} should be Medium, got {verdict}"
        assert verdict["access_mode"] == "auto"


def test_classify_high_send_message():
    for cmd in (
        "eduflow send worker_course manager \"please fix q1\"",
        "eduflow send worker_course manager \"please fix q1\" 高",
    ):
        verdict = tool_risk.classify(cmd)
        assert verdict["risk_level"] == "High", f"{cmd} should be High, got {verdict}"
        assert verdict["access_mode"] == "auto_review"
        assert verdict["requires_preflight"] is True
        assert verdict["requires_human_confirm"] is False


def test_classify_high_say_to_user():
    verdict = tool_risk.classify('eduflow say manager "TODO" --to user')
    assert verdict["risk_level"] == "High"
    assert verdict["access_mode"] == "auto_review"
    assert "say" in verdict["reason"] or "user" in verdict["reason"]


def test_classify_high_dispatch_and_review():
    for cmd in (
        "eduflow task dispatch worker_course \"IGCSE Bio\" --stage curriculum --owner worker_course",
        "eduflow task review T-1 --actor review_course --reject",
        "eduflow task reidentify worker_course",
        "eduflow task assign-reviewer T-1 --reviewer review_course",
        "eduflow task submit-review T-1 --actor worker_course",
    ):
        verdict = tool_risk.classify(cmd)
        assert verdict["risk_level"] == "High", f"{cmd} should be High, got {verdict}"
        assert verdict["requires_preflight"] is True


def test_classify_critical_destructive():
    for cmd in (
        "eduflow reset",
        "eduflow down",
        "eduflow fire worker_course",
        "eduflow hire worker_builder",
        "eduflow task archive T-1 --older-than 90d",
        "eduflow task archive-schedule --enable true",
        "rm -rf .eduflow-team-state",
        "rm -rf /tmp/foo",
        "rm -rf $EDUFLOW_STATE_DIR",
    ):
        verdict = tool_risk.classify(cmd)
        assert verdict["risk_level"] == "Critical", f"{cmd} should be Critical, got {verdict}"
        assert verdict["access_mode"] == "manager_only"
        assert verdict["requires_human_confirm"] is True
        assert verdict["requires_preflight"] is True


def test_classify_critical_external_deploy():
    verdict = tool_risk.classify("kubectl apply -f production.yaml")
    assert verdict["risk_level"] == "Critical"


def test_classify_unknown_command_defaults_to_medium():
    verdict = tool_risk.classify("eduflow unknown-thing T-1 --json")
    assert verdict["risk_level"] == "Medium"


def test_classify_empty_command_returns_low():
    verdict = tool_risk.classify("")
    assert verdict["risk_level"] == "Low"
    assert verdict["reason"] != ""


def test_classify_combined_command_takes_highest_level():
    verdict = tool_risk.classify(
        "eduflow task loop-status T-1 && eduflow send worker_course manager \"urgent\" 高"
    )
    assert verdict["risk_level"] == "High"


def test_classify_combined_command_with_rm_takes_critical():
    verdict = tool_risk.classify(
        "eduflow task get T-1 && rm -rf .eduflow-team-state"
    )
    assert verdict["risk_level"] == "Critical"


def test_classify_result_schema_is_stable():
    verdict = tool_risk.classify("eduflow task get T-1")
    assert set(verdict.keys()) == {
        "risk_level", "access_mode", "reason",
        "requires_preflight", "requires_human_confirm",
    }


def test_classify_access_mode_matches_risk():
    mapping = {
        "Low": "auto",
        "Medium": "auto",
        "High": "auto_review",
        "Critical": "manager_only",
    }
    for cmd, expected in (
        ("eduflow task get T-1", "Low"),
        ("eduflow task update T-1 --status 进行中", "Medium"),
        ("eduflow send worker_course manager \"x\" 高", "High"),
        ("eduflow reset", "Critical"),
    ):
        verdict = tool_risk.classify(cmd)
        assert verdict["risk_level"] == expected
        assert verdict["access_mode"] == mapping[expected], (
            f"access_mode mismatch for {cmd}"
        )


# ── CLI: task tool-risk ───────────────────────────────────────────


def test_cli_tool_risk_json_mode():
    with isolated_env():
        rc, out, err = run_cli([
            "task", "tool-risk",
            "--command", "eduflow send worker_course manager \"fix q1\" 高",
            "--json",
        ])
        assert rc == 0, err
        payload = json.loads(out)
        assert "tool_risk" in payload
        verdict = payload["tool_risk"]
        assert verdict["risk_level"] == "High"
        assert verdict["access_mode"] == "auto_review"


def test_cli_tool_risk_text_mode():
    with isolated_env():
        rc, out, err = run_cli([
            "task", "tool-risk",
            "--command", "eduflow reset",
        ])
        assert rc == 0, err
        for needle in (
            "risk_level:",
            "access_mode:",
            "reason:",
            "requires_preflight:",
            "requires_human_confirm:",
        ):
            assert needle in out, f"missing text field: {needle}"
        assert "Critical" in out


def test_cli_tool_risk_missing_command_returns_usage_error():
    with isolated_env():
        rc, out, err = run_cli(["task", "tool-risk"])
        assert rc != 0


def test_cli_tool_risk_does_not_mutate_state():
    with isolated_env():
        from eduflow.store import local_facts, tasks
        tasks.create("worker", "do thing")
        before_inbox = local_facts.list_all_messages()
        run_cli([
            "task", "tool-risk",
            "--command", "eduflow reset",
        ])
        run_cli([
            "task", "tool-risk",
            "--command", "eduflow send worker_course manager \"x\" 高",
        ])
        after_inbox = local_facts.list_all_messages()
        assert len(before_inbox) == len(after_inbox)


# ── coverage matrix smoke ────────────────────────────────────────


@pytest.mark.parametrize("cmd,expected_level", [
    ("eduflow task evidence-explain T-1 --json", "Low"),
    ("eduflow task loop-status T-1", "Low"),
    ("eduflow task loop-contract T-1 --json", "Low"),
    ("eduflow task get T-1", "Low"),
    ("eduflow task create w \"t\"", "Medium"),
    ("eduflow task update T-1 --status 进行中", "Medium"),
    ("eduflow send worker_course manager \"x\" 高", "High"),
    ('eduflow say manager "x" --to user', "High"),
    ("eduflow task review T-1 --actor review_course --approve", "High"),
    ("eduflow task reidentify worker_course", "High"),
    ("eduflow reset", "Critical"),
    ("eduflow down", "Critical"),
    ("eduflow fire worker_course", "Critical"),
    ("rm -rf .eduflow-team-state", "Critical"),
])
def test_classify_coverage_matrix(cmd, expected_level):
    verdict = tool_risk.classify(cmd)
    assert verdict["risk_level"] == expected_level, (
        f"{cmd}: expected {expected_level}, got {verdict}"
    )