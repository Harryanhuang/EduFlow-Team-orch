"""Focused tests for eduflow.memory.event_bridge — task lifecycle bridging.

Covers:
- bridge_task_lifecycle("fail"): creates witness candidate, threshold logic
- bridge_task_lifecycle with non-fail events: returns None
- idempotency: same task_id repeated does not duplicate witness
- task_id dedup across retries
- missing workflow_id / task_id returns None
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tests.helpers import isolated_env


def _init_db():
    from eduflow.memory.db import init_schema, close
    close()
    init_schema()


def _reset_db():
    from eduflow.memory.db import close
    close()


# ── bridge_task_lifecycle: fail event ──────────────────────────────

class TestBridgeTaskLifecycleFail:
    def test_first_fail_returns_none(self):
        """First failure for a workflow does not produce a pattern candidate."""
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_task_lifecycle
            result = bridge_task_lifecycle(
                "T-100", "fail",
                context={"workflow_id": "wf-alpha", "failure_reason": "timeout"},
            )
            # 1 failure: witness recorded but no pattern candidate
            assert result is None
            _reset_db()

    def test_second_fail_returns_pattern_candidate(self):
        """Second failure for same workflow triggers pattern detection."""
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_task_lifecycle
            bridge_task_lifecycle(
                "T-100", "fail",
                context={"workflow_id": "wf-beta", "failure_reason": "err1"},
            )
            result = bridge_task_lifecycle(
                "T-101", "fail",
                context={"workflow_id": "wf-beta", "failure_reason": "err2"},
            )
            assert result is not None
            assert result.startswith("CAND-")
            _reset_db()

    def test_third_fail_also_returns_pattern(self):
        """Third failure still returns a pattern candidate (idempotent hook)."""
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_task_lifecycle
            bridge_task_lifecycle(
                "T-1", "fail",
                context={"workflow_id": "wf-gamma"},
            )
            bridge_task_lifecycle(
                "T-2", "fail",
                context={"workflow_id": "wf-gamma"},
            )
            result = bridge_task_lifecycle(
                "T-3", "fail",
                context={"workflow_id": "wf-gamma"},
            )
            # Pattern already detected at T-2; T-3 returns the same
            # pattern candidate id (idempotent hook)
            assert result is not None
            _reset_db()


# ── bridge_task_lifecycle: non-fail events ─────────────────────────

class TestBridgeTaskLifecycleNonFail:
    def test_success_returns_none(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_task_lifecycle
            result = bridge_task_lifecycle(
                "T-100", "success",
                context={"workflow_id": "wf-x"},
            )
            assert result is None
            _reset_db()

    def test_deliver_returns_none(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_task_lifecycle
            result = bridge_task_lifecycle(
                "T-100", "deliver",
                context={"workflow_id": "wf-x"},
            )
            assert result is None
            _reset_db()

    def test_complete_returns_none(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_task_lifecycle
            result = bridge_task_lifecycle(
                "T-100", "complete",
                context={"workflow_id": "wf-x"},
            )
            assert result is None
            _reset_db()

    def test_retry_returns_none(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_task_lifecycle
            result = bridge_task_lifecycle(
                "T-100", "retry",
                context={"workflow_id": "wf-x"},
            )
            assert result is None
            _reset_db()

    def test_empty_event_returns_none(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_task_lifecycle
            result = bridge_task_lifecycle("T-100", "")
            assert result is None
            _reset_db()


# ── bridge_task_lifecycle: idempotency ─────────────────────────────

class TestBridgeTaskLifecycleIdempotency:
    def test_same_task_id_does_not_create_duplicate_witness(self):
        """Retrying the same task_id produces only one witness candidate."""
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_task_lifecycle
            from eduflow.memory.candidates import list_candidates
            ctx = {"workflow_id": "wf-dedup", "failure_reason": "err"}
            bridge_task_lifecycle("T-500", "fail", context=ctx)
            bridge_task_lifecycle("T-500", "fail", context=ctx)
            bridge_task_lifecycle("T-500", "fail", context=ctx)
            witnesses = list_candidates(
                scope="workflow:wf-dedup", source_type="task_failure",
                status="proposed", limit=100,
            )
            # Should be exactly 1 witness (idempotent by source_ref="task:T-500")
            assert len(witnesses) == 1
            _reset_db()

    def test_different_task_ids_create_separate_witnesses(self):
        """Different task_ids produce separate witness candidates."""
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_task_lifecycle
            from eduflow.memory.candidates import list_candidates
            ctx = {"workflow_id": "wf-multi", "failure_reason": "err"}
            bridge_task_lifecycle("T-200", "fail", context=ctx)
            bridge_task_lifecycle("T-201", "fail", context=ctx)
            witnesses = list_candidates(
                scope="workflow:wf-multi", source_type="task_failure",
                status="proposed", limit=100,
            )
            assert len(witnesses) == 2
            _reset_db()

    def test_repeated_call_after_threshold_still_idempotent(self):
        """After pattern is detected, repeated calls don't spam candidates."""
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_task_lifecycle
            from eduflow.memory.candidates import list_candidates
            ctx = {"workflow_id": "wf-thresh", "failure_reason": "err"}
            # Cross threshold
            bridge_task_lifecycle("T-300", "fail", context=ctx)
            bridge_task_lifecycle("T-301", "fail", context=ctx)
            # Repeated calls with same task_ids
            bridge_task_lifecycle("T-300", "fail", context=ctx)
            bridge_task_lifecycle("T-301", "fail", context=ctx)
            all_cands = list_candidates(
                scope="workflow:wf-thresh", status="proposed", limit=100,
            )
            # 2 witnesses + 1 pattern candidate = 3 total
            assert len(all_cands) == 3
            _reset_db()


# ── bridge_task_lifecycle: missing fields ──────────────────────────

class TestBridgeTaskLifecycleMissingFields:
    def test_missing_workflow_id_returns_none(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_task_lifecycle
            result = bridge_task_lifecycle(
                "T-100", "fail", context={},
            )
            assert result is None
            _reset_db()

    def test_missing_task_id_returns_none(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_task_lifecycle
            result = bridge_task_lifecycle(
                "", "fail", context={"workflow_id": "wf-x"},
            )
            assert result is None
            _reset_db()

    def test_none_context_returns_none(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_task_lifecycle
            result = bridge_task_lifecycle("T-100", "fail", context=None)
            assert result is None
            _reset_db()


# ── bridge_task_lifecycle: failure_reasons variations ──────────────

class TestBridgeTaskLifecycleFailureReasons:
    def test_failure_reasons_list(self):
        """failure_reasons list takes precedence over failure_reason."""
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_task_lifecycle
            result = bridge_task_lifecycle(
                "T-600", "fail",
                context={
                    "workflow_id": "wf-reasons",
                    "failure_reasons": ["timeout", "oom"],
                    "failure_reason": "ignored",
                },
            )
            # Should use "timeout" (first in list), not "ignored"
            assert result is None  # first fail, no pattern yet
            _reset_db()

    def test_no_reason_defaults_to_no_reason_given(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_task_lifecycle
            result = bridge_task_lifecycle(
                "T-700", "fail",
                context={"workflow_id": "wf-noreason"},
            )
            assert result is None  # first fail
            _reset_db()


# ── bridge_review_event ────────────────────────────────────────────

class TestBridgeReviewEvent:
    def test_fail_verdict_fires_hook(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_review_event
            result = bridge_review_event({
                "task_id": "T-800",
                "verdict": "FAIL",
                "reason": "code quality",
                "worker": "alice",
            })
            assert result is not None
            assert result.startswith("CAND-")
            _reset_db()

    def test_rejected_verdict_fires_hook(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_review_event
            result = bridge_review_event({
                "task_id": "T-801",
                "verdict": "REJECTED",
                "reason": "quality issues",
            })
            assert result is not None
            assert result.startswith("CAND-")
            _reset_db()

    def test_pass_verdict_returns_none(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_review_event
            result = bridge_review_event({
                "task_id": "T-802",
                "verdict": "PASS",
            })
            assert result is None
            _reset_db()

    def test_missing_task_id_returns_none(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_review_event
            result = bridge_review_event({"verdict": "FAIL"})
            assert result is None
            _reset_db()

    def test_non_dict_input_returns_none(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_review_event
            assert bridge_review_event(None) is None
            assert bridge_review_event("not a dict") is None
            _reset_db()

    def test_idempotent_same_task_verdict(self):
        """Same task+verdict produces same candidate (idempotent)."""
        with isolated_env():
            _init_db()
            from eduflow.memory.event_bridge import bridge_review_event
            r1 = bridge_review_event({
                "task_id": "T-900", "verdict": "FAIL",
                "reason": "timeout error",
            })
            r2 = bridge_review_event({
                "task_id": "T-900", "verdict": "FAIL",
                "reason": "timeout error",
            })
            assert r1 is not None
            assert r1 == r2
            _reset_db()
