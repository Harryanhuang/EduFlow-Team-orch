"""P8: D scheduled-task workflow evolution.

Workflow evolution is observation + promotion only — it never
dispatches agents, never writes T tasks, and never promotes a
candidate into the active workflow registry on its own. Manager
confirmation is external; this module records, scores, demotes, and
flags.

Phases:
    exploration ─≥5 stable completions→ candidate
                                      │
                                  approve (manager closeout)
                                      ▼
                                   approved ─2 consecutive dev/fail→ exploration
"""
from __future__ import annotations

import pytest

from helpers import isolated_env
from eduflow.runtime import paths
from eduflow.scheduling import workflow_evolution
from eduflow.store import scheduled_tasks


# ── helpers ──────────────────────────────────────────────────────────


def _utc(year, month, day, hour=0, minute=0):
    return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:00Z"


def _ms(year, month, day, hour=0, minute=0):
    from datetime import datetime, timezone
    dt = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _new_rule(
    *,
    rule_id_hint="D-test",
    target="weekly summary",
    artifact="summary.md",
):
    return scheduled_tasks.create_rule(
        target=target,
        artifact=artifact,
        frequency="weekly",
        timezone="Asia/Shanghai",
        next_due_utc=_utc(2026, 7, 13, 10, 0),
        created_by="user",
        status="active",
    )


_STABLE_AGENTS = ["worker_course", "review_course"]


def _record(
    rid, *, occ_idx,
    agents=None,
    result="done",
    target="weekly summary",
    artifact="summary.md",
    role="manager",
    failure_pattern="",
):
    return workflow_evolution.record_outcome(
        rid,
        occurrence_key=f"{rid}:2026-07-{13 + occ_idx:02d}T10:00:00Z",
        scheduled_at_utc=f"2026-07-{13 + occ_idx:02d}T10:00:00Z",
        result=result,
        agents=agents if agents is not None else _STABLE_AGENTS,
        artifact=artifact,
        target=target,
        role=role,
        failure_pattern=failure_pattern,
    )


def _promote_through_candidate(rid, *, approved_at=None):
    """Drive 5 stable completions → candidate → approved."""
    for i in range(5):
        _record(rid, occ_idx=i)
    payload = workflow_evolution.candidate_payload(rid)
    workflow_evolution.approve_candidate(
        rid, actor="manager", approved_at=approved_at,
    )
    return payload


# ── initial state ─────────────────────────────────────────────────────


def test_initial_phase_is_exploration():
    with isolated_env():
        rid = _new_rule()
        record = _record(rid, occ_idx=0)
        # Phase is exploration immediately after first outcome.
        # No candidate / approved yet — manager has not closed out.
        assert record["phase"] == "exploration"
        assert record["candidate"] is None
        assert record["approved"] is None
        assert record["deviation_streak"]["count"] == 0
        assert len(record["completion_history"]) == 1


def test_evolution_status_none_for_unknown_rule():
    with isolated_env():
        assert workflow_evolution.evolution_status("D-missing") is None


# ── record_outcome ────────────────────────────────────────────────────


def test_record_outcome_appends_history_with_signature():
    with isolated_env():
        rid = _new_rule()
        record = _record(rid, occ_idx=0)
        assert len(record["completion_history"]) == 1
        entry = record["completion_history"][0]
        assert entry["signature"] == (
            "weekly summary|summary.md|manager|worker_course,review_course"
        )
        assert entry["result"] == "done"


def test_record_outcome_rejects_invalid_result():
    with isolated_env():
        rid = _new_rule()
        with pytest.raises(ValueError):
            workflow_evolution.record_outcome(
                rid, occurrence_key="x", scheduled_at_utc="y", result="bogus",
            )


def test_record_outcome_rejects_empty_rule_id():
    with isolated_env():
        with pytest.raises(ValueError):
            workflow_evolution.record_outcome(
                "", occurrence_key="x", scheduled_at_utc="y", result="done",
            )


# ── candidate_payload: stability algorithm ───────────────────────────


def test_candidate_payload_returns_none_below_threshold():
    with isolated_env():
        rid = _new_rule()
        for i in range(4):
            _record(rid, occ_idx=i)
        assert workflow_evolution.candidate_payload(rid) is None
        assert workflow_evolution.evolution_status(rid)["phase"] == "exploration"


def test_candidate_payload_emits_at_five_stable_completions():
    with isolated_env():
        rid = _new_rule()
        for i in range(5):
            _record(rid, occ_idx=i)
        payload = workflow_evolution.candidate_payload(rid)
        assert payload is not None
        assert payload["target"] == "weekly summary"
        assert payload["artifact"] == "summary.md"
        assert payload["role"] == "manager"
        assert payload["agents"] == _STABLE_AGENTS
        assert "manager ->" in payload["primary_chain"]
        assert "-> manager" in payload["primary_chain"]
        assert "worker_course" in payload["primary_chain"]
        assert "review_course" in payload["primary_chain"]
        assert len(payload["evidence_occurrence_keys"]) == 5
        # Candidate boundary is part of the payload.
        assert "frozen snapshot" in payload["boundary"].lower() or (
            "snapshot" in payload["boundary"].lower()
        )
        # Phase advanced to candidate and stored.
        record = workflow_evolution.evolution_status(rid)
        assert record["phase"] == "candidate"
        assert record["candidate"]["workflow_id_hint"] == payload["workflow_id_hint"]


def test_candidate_blocks_on_signature_drift_in_last_five():
    """The candidate algorithm looks at the LAST 5 completions only.
    Drift anywhere in that window disqualifies promotion."""
    with isolated_env():
        rid = _new_rule()
        # 5 stable → candidate would normally emit, but the last
        # entry drifts the lane agents.
        _record(rid, occ_idx=0, agents=["worker_course", "review_course"])
        _record(rid, occ_idx=1, agents=["worker_course", "review_course"])
        _record(rid, occ_idx=2, agents=["worker_course", "review_course"])
        _record(rid, occ_idx=3, agents=["worker_course", "review_course"])
        _record(rid, occ_idx=4, agents=["worker_qbank"])  # drift
        assert workflow_evolution.candidate_payload(rid) is None
        assert workflow_evolution.evolution_status(rid)["phase"] == "exploration"


def test_candidate_blocks_on_repeat_failure_pattern():
    """A failure_pattern that repeats ≥2 times in the last 5
    completions indicates an unresolved repeat failure — block."""
    with isolated_env():
        rid = _new_rule()
        for i in range(5):
            _record(
                rid, occ_idx=i,
                failure_pattern="timeout" if i in {0, 1} else "",
            )
        assert workflow_evolution.candidate_payload(rid) is None
        assert workflow_evolution.evolution_status(rid)["phase"] == "exploration"


def test_candidate_does_not_promote_when_phase_is_approved():
    with isolated_env():
        rid = _new_rule()
        payload = _promote_through_candidate(rid)
        # After approval, candidate_payload should NOT re-emit
        # (the rule is past candidate phase).
        assert workflow_evolution.candidate_payload(rid) is None


def test_candidate_payload_is_idempotent_in_candidate_phase():
    with isolated_env():
        rid = _new_rule()
        for i in range(5):
            _record(rid, occ_idx=i)
        first = workflow_evolution.candidate_payload(rid)
        second = workflow_evolution.candidate_payload(rid)
        assert first is not None
        assert second is not None
        assert first["workflow_id_hint"] == second["workflow_id_hint"]
        assert first["evidence_occurrence_keys"] == second["evidence_occurrence_keys"]


# ── approve_candidate (manager closeout → approved / frozen) ─────────


def test_approve_candidate_records_frozen_snapshot():
    with isolated_env():
        rid = _new_rule()
        for i in range(5):
            _record(rid, occ_idx=i)
        payload = workflow_evolution.candidate_payload(rid)
        record = workflow_evolution.approve_candidate(rid, actor="manager")
        assert record["phase"] == "approved"
        approved = record["approved"]
        assert approved["frozen_signature"] == payload["stable_signature"]
        assert approved["frozen_target"] == "weekly summary"
        assert approved["frozen_artifact"] == "summary.md"
        assert approved["frozen_role"] == "manager"
        assert approved["frozen_agents"] == _STABLE_AGENTS
        assert approved["approved_by"] == "manager"
        # health_review counters reset on approval.
        assert record["health_review"]["since_review_count"] == 0
        # frozen_snapshot returns the approved asset dict.
        snap = workflow_evolution.frozen_snapshot(rid)
        assert snap["frozen_signature"] == payload["stable_signature"]


def test_approve_candidate_requires_actor():
    with isolated_env():
        rid = _new_rule()
        with pytest.raises(ValueError):
            workflow_evolution.approve_candidate(rid, actor="")


def test_approve_candidate_rejects_non_candidate_phase():
    with isolated_env():
        rid = _new_rule()
        # Seed the record so we can observe the "exploration" reject path.
        _record(rid, occ_idx=0)
        # Rule is still in exploration (no candidate built yet).
        with pytest.raises(workflow_evolution.PhaseError):
            workflow_evolution.approve_candidate(rid, actor="manager")


def test_approve_candidate_rejects_twice():
    with isolated_env():
        rid = _new_rule()
        _promote_through_candidate(rid)
        with pytest.raises(workflow_evolution.PhaseError):
            workflow_evolution.approve_candidate(rid, actor="manager")


def test_approved_workflow_does_not_auto_dispatch_on_next_outcome():
    """After approval, record_outcome still records but the phase must
    stay `approved` until demotion — never auto-advance."""
    with isolated_env():
        rid = _new_rule()
        _promote_through_candidate(rid)
        for i in range(3):
            _record(rid, occ_idx=5 + i)
        record = workflow_evolution.evolution_status(rid)
        assert record["phase"] == "approved"
        assert len(record["completion_history"]) == 8


# ── demotion logic ────────────────────────────────────────────────────


def test_approved_workflow_two_consecutive_signature_deviations_demote():
    with isolated_env():
        rid = _new_rule()
        _promote_through_candidate(rid)
        # First deviation — lane signature differs from frozen.
        _record(rid, occ_idx=5, agents=["worker_qbank"])
        record = workflow_evolution.evolution_status(rid)
        assert record["phase"] == "approved"
        assert record["deviation_streak"]["count"] == 1
        # Second consecutive deviation → auto-demote back to exploration.
        _record(rid, occ_idx=6, agents=["auto_ops"])
        record = workflow_evolution.evolution_status(rid)
        assert record["phase"] == "exploration"
        # Audit list captures the demotion event.
        assert len(record["demotions"]) == 1
        assert "consecutive" in record["demotions"][0]["reason"]
        # Notification written to the manager_ops ledger.
        notifications = scheduled_tasks.list_notifications(
            rule_id=rid, kind="workflow_demoted",
        )
        assert len(notifications) == 1
        assert notifications[0]["recipient"] == "user"


def test_approved_workflow_one_deviation_does_not_demote():
    with isolated_env():
        rid = _new_rule()
        _promote_through_candidate(rid)
        _record(rid, occ_idx=5, agents=["worker_qbank"])  # deviation 1
        record = workflow_evolution.evolution_status(rid)
        assert record["phase"] == "approved"
        assert record["deviation_streak"]["count"] == 1


def test_clean_done_resets_deviation_streak_after_one_deviation():
    with isolated_env():
        rid = _new_rule()
        _promote_through_candidate(rid)
        _record(rid, occ_idx=5, agents=["worker_qbank"])  # deviation 1
        _record(rid, occ_idx=6, agents=_STABLE_AGENTS, result="done")
        record = workflow_evolution.evolution_status(rid)
        # Streak reset by the successful done; phase stays approved.
        assert record["phase"] == "approved"
        assert record["deviation_streak"]["count"] == 0


def test_two_consecutive_failures_demote_approved_workflow():
    with isolated_env():
        rid = _new_rule()
        _promote_through_candidate(rid)
        _record(rid, occ_idx=5, result="failed", failure_pattern="timeout")
        record = workflow_evolution.evolution_status(rid)
        assert record["phase"] == "approved"
        assert record["deviation_streak"]["count"] == 1
        _record(rid, occ_idx=6, result="failed", failure_pattern="timeout")
        record = workflow_evolution.evolution_status(rid)
        assert record["phase"] == "exploration"
        assert len(record["demotions"]) == 1


def test_skipped_outcome_is_neutral_and_does_not_count_as_deviation():
    with isolated_env():
        rid = _new_rule()
        _promote_through_candidate(rid)
        _record(rid, occ_idx=5, result="skipped")
        record = workflow_evolution.evolution_status(rid)
        assert record["phase"] == "approved"
        assert record["deviation_streak"]["count"] == 0


def test_cancelled_outcome_does_not_count_as_deviation():
    with isolated_env():
        rid = _new_rule()
        _promote_through_candidate(rid)
        _record(rid, occ_idx=5, result="cancelled")
        record = workflow_evolution.evolution_status(rid)
        assert record["phase"] == "approved"
        assert record["deviation_streak"]["count"] == 0


def test_record_deviation_helper_increments_streak():
    """Manager / operator can flag a deviation explicitly outside
    the signature comparison. Counts only in approved phase."""
    with isolated_env():
        rid = _new_rule()
        _promote_through_candidate(rid)
        workflow_evolution.record_deviation(rid, note="manager called this a deviation")
        record = workflow_evolution.evolution_status(rid)
        assert record["deviation_streak"]["count"] == 1
        assert record["deviation_streak"]["last_kind"] == "explicit"
        workflow_evolution.record_deviation(rid, note="second explicit")
        record = workflow_evolution.evolution_status(rid)
        assert record["phase"] == "exploration"
        assert len(record["demotions"]) == 1


def test_deviation_streak_does_not_apply_in_exploration_phase():
    with isolated_env():
        rid = _new_rule()
        # No 5-stable threshold reached; phase is still exploration.
        _record(rid, occ_idx=0, result="failed", failure_pattern="boom")
        record = workflow_evolution.evolution_status(rid)
        assert record["phase"] == "exploration"
        assert record["deviation_streak"]["count"] == 0


# ── demotion + re-exploration ─────────────────────────────────────────


def test_demoted_rule_can_re_enter_candidate_with_new_stable_runs():
    with isolated_env():
        rid = _new_rule()
        _promote_through_candidate(rid)
        _record(rid, occ_idx=5, agents=["worker_qbank"])
        _record(rid, occ_idx=6, agents=["auto_ops"])
        record = workflow_evolution.evolution_status(rid)
        assert record["phase"] == "exploration"
        # 5 new stable completions form the new last-5 window.
        for i in range(5):
            _record(rid, occ_idx=7 + i, agents=_STABLE_AGENTS)
        payload = workflow_evolution.candidate_payload(rid)
        assert payload is not None
        assert payload["stable_signature"] == (
            "weekly summary|summary.md|manager|worker_course,review_course"
        )
        record = workflow_evolution.evolution_status(rid)
        assert record["phase"] == "candidate"
        # Demotion audit is preserved.
        assert len(record["demotions"]) == 1


# ── health review (30 days OR 10 successes) ──────────────────────────


def test_health_review_due_after_30_days():
    with isolated_env():
        rid = _new_rule()
        before = _ms(2026, 7, 13, 11, 0)
        _promote_through_candidate(rid, approved_at=before)
        # 29 days later — not due.
        assert not workflow_evolution.health_review_due(
            rid, now=before + 29 * 86400 * 1000
        )
        # 31 days later — due.
        assert workflow_evolution.health_review_due(
            rid, now=before + 31 * 86400 * 1000
        )


def test_health_review_due_after_10_successful_runs():
    with isolated_env():
        rid = _new_rule()
        approved_at = _ms(2026, 7, 13, 11, 0)
        _promote_through_candidate(rid, approved_at=approved_at)
        # 10 clean dones → counter at threshold.
        for i in range(10):
            _record(rid, occ_idx=5 + i, result="done", agents=_STABLE_AGENTS)
        future = approved_at + 5 * 86400 * 1000  # 5 days after approval
        assert workflow_evolution.health_review_due(rid, now=future)


def test_health_review_not_due_in_other_phases():
    with isolated_env():
        rid = _new_rule()
        # 5 stable completions but still in exploration.
        for i in range(5):
            _record(rid, occ_idx=i)
        future = _ms(2026, 8, 1, 0, 0)
        assert not workflow_evolution.health_review_due(rid, now=future)


def test_record_health_review_resets_window_and_count():
    with isolated_env():
        rid = _new_rule()
        approved_at = _ms(2026, 7, 13, 11, 0)
        _promote_through_candidate(rid, approved_at=approved_at)
        for i in range(10):
            _record(rid, occ_idx=5 + i, result="done", agents=_STABLE_AGENTS)
        review_now = approved_at + 7 * 86400 * 1000  # 7 days after approval
        assert workflow_evolution.health_review_due(rid, now=review_now)
        workflow_evolution.record_health_review(
            rid, actor="manager", now=review_now,
        )
        # After the review, no longer due at the same moment.
        assert not workflow_evolution.health_review_due(rid, now=review_now)
        # Counter was reset; need 10 more runs to trigger again.
        for i in range(9):
            _record(rid, occ_idx=20 + i, result="done", agents=_STABLE_AGENTS)
        assert not workflow_evolution.health_review_due(rid, now=review_now)


def test_record_health_review_requires_actor():
    with isolated_env():
        rid = _new_rule()
        _promote_through_candidate(rid)
        with pytest.raises(ValueError):
            workflow_evolution.record_health_review(
                rid, actor="", now=_ms(2026, 7, 14, 0, 0),
            )


# ── boundary guarantees ──────────────────────────────────────────────


def test_workflow_evolution_does_not_import_commands_workflow():
    """P8 MUST NOT treat worker_builder T work as D execution.
    The module must therefore not import from eduflow.commands.workflow
    or from the T task store."""
    import eduflow.scheduling.workflow_evolution as we
    src = open(we.__file__, encoding="utf-8").read()
    assert "eduflow.commands" not in src
    assert "from eduflow.store import tasks" not in src
    assert "store.tasks" not in src


def test_evolution_file_lives_under_scheduler_dir():
    with isolated_env():
        rid = _new_rule()
        _record(rid, occ_idx=0)
        p = workflow_evolution._evolution_file()
        assert str(paths.scheduler_dir()) in str(p)
        # Must NOT live under facts/ (which is the T / team lane).
        assert str(paths.facts_dir()) not in str(p)


def test_workflow_evolution_persists_under_state_dir():
    with isolated_env():
        rid = _new_rule()
        _record(rid, occ_idx=0)
        p = workflow_evolution._evolution_file()
        assert str(paths.state_dir()) in str(p)


def test_evolution_persists_across_reload():
    with isolated_env():
        rid = _new_rule()
        _record(rid, occ_idx=0)
        _record(rid, occ_idx=1)
        # Reload by re-instantiating — read through file.
        record = workflow_evolution.evolution_status(rid)
        assert len(record["completion_history"]) == 2
        record_b = workflow_evolution.evolution_status(rid)
        assert record == record_b


# ── frozen_snapshot contract ─────────────────────────────────────────


def test_frozen_snapshot_none_for_unapproved_rule():
    with isolated_env():
        rid = _new_rule()
        assert workflow_evolution.frozen_snapshot(rid) is None
        for i in range(5):
            _record(rid, occ_idx=i)
        workflow_evolution.candidate_payload(rid)
        # candidate but not approved yet → still no frozen snapshot.
        assert workflow_evolution.frozen_snapshot(rid) is None


def test_frozen_snapshot_preserved_across_subsequent_outcomes():
    with isolated_env():
        rid = _new_rule()
        _promote_through_candidate(rid)
        snap_before = dict(workflow_evolution.frozen_snapshot(rid))
        # Outcomes after approval do NOT mutate the frozen snapshot.
        _record(rid, occ_idx=5, result="done", agents=_STABLE_AGENTS)
        _record(rid, occ_idx=6, result="done", agents=_STABLE_AGENTS)
        snap_after = workflow_evolution.frozen_snapshot(rid)
        assert snap_after == snap_before
