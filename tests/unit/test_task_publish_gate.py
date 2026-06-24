"""Tests for business-level task publish decisions."""
from __future__ import annotations

from helpers import isolated_env
from eduflow.store import task_publish_gate, tasks


def test_gate_silences_created_event_for_user():
    with isolated_env():
        tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        event = tasks.list_task_events()[-1]
        decision = task_publish_gate.decide_task_event_publish(
            event,
            sender="manager",
            to_target="user",
        )
        assert decision["publish"] is True
        assert decision["reason"] == "worker_accepted"
        assert decision["delivery_lane"] == "worker_reassurance"


def test_gate_silences_assigned_transition_for_user():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        event = tasks.list_task_events()[-1]
        decision = task_publish_gate.decide_task_event_publish(
            event,
            sender="manager",
            to_target="user",
        )
        assert decision["publish"] is False
        assert decision["reason"] == "internal_assignment"
        assert decision["status"] == "assigned"


def test_gate_publishes_delivered_transition_to_user():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker")
        tasks.transition_flow(tid, to_status="submitted_for_review", actor="worker")
        tasks.transition_flow(tid, to_status="delivered", actor="reviewer")
        event = tasks.list_task_events()[-1]
        decision = task_publish_gate.decide_task_event_publish(
            event,
            sender="worker_course",
            to_target="user",
        )
        assert decision["publish"] is True
        assert decision["reason"] == "delivered_to_user"
        assert decision["status"] == "delivered"
        assert decision["delivery_lane"] == "manager_result"
        assert decision["manager_response_type"] == "final_result_delivered"
        assert decision["close_loop_state"] == "open"


def test_gate_publishes_in_progress_as_worker_reassurance():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        event = tasks.list_task_events()[-1]
        decision = task_publish_gate.decide_task_event_publish(
            event,
            sender="worker_course",
            to_target="user",
        )
        assert decision["publish"] is True
        assert decision["reason"] == "worker_started"
        assert decision["audience_policy"] == "worker_reassurance"
        assert decision["delivery_lane"] == "worker_reassurance"


def test_gate_suppresses_reviewer_assignment_during_in_progress_as_low_signal():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        event = tasks.list_task_events()[-1]
        decision = task_publish_gate.decide_task_event_publish(
            event,
            sender="manager",
            to_target="user",
        )
        assert decision["publish"] is False
        assert decision["reason"] == "progress_internal_only"
        assert decision["cadence_action"] == "suppress_low_signal_update"
        assert decision["cadence_reason"] == "reviewer_assignment_during_progress"


def test_gate_publishes_submitted_for_review_as_worker_completed_handoff():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        event = tasks.list_task_events()[-1]
        decision = task_publish_gate.decide_task_event_publish(
            event,
            sender="worker_course",
            to_target="user",
        )
        assert decision["publish"] is True
        assert decision["reason"] == "worker_completed_handed_to_manager"
        assert decision["audience_policy"] == "worker_reassurance"
        assert decision["delivery_lane"] == "worker_reassurance"
        assert decision["cadence_action"] == "send_now"
        assert decision["close_loop_state"] == "open"


def test_gate_publishes_manager_action_block_as_worker_waiting_on_manager():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.assign_reviewer(tid, reviewer="reviewer_amy", actor="manager")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="manager_action",
            actor="reviewer_amy",
            review_reason="missing_scope_confirmation",
            manager_action_type="clarify_scope",
        )
        event = tasks.list_task_events()[-1]
        decision = task_publish_gate.decide_task_event_publish(
            event,
            sender="reviewer_amy",
            to_target="user",
        )
        assert decision["publish"] is False
        assert decision["reason"] == "worker_waiting_on_manager"
        assert decision["audience_policy"] == "worker_reassurance"
        assert decision["delivery_lane"] == "worker_reassurance"
        assert decision["cadence_action"] == "delay_and_wait"


def test_gate_keeps_manager_action_internal_for_user():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker")
        tasks.assign_reviewer(tid, reviewer="reviewer_amy", actor="manager")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(tid, outcome="manager_action", actor="reviewer_amy")
        event = tasks.list_task_events()[-1]
        decision = task_publish_gate.decide_task_event_publish(
            event,
            sender="reviewer_amy",
            to_target="user",
        )
        assert decision["publish"] is False
        assert decision["reason"] == "worker_waiting_on_manager"
        assert decision["audience_policy"] == "worker_reassurance"
        assert decision["cadence_action"] == "delay_and_wait"


def test_gate_allows_scope_pending_manager_action_as_user_explanation():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.assign_reviewer(tid, reviewer="reviewer_amy", actor="manager")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="manager_action",
            actor="reviewer_amy",
            review_reason="missing_scope_confirmation",
            manager_action_type="clarify_scope",
        )
        event = tasks.list_task_events()[-1]
        decision = task_publish_gate.decide_task_event_publish(
            event,
            sender="reviewer_amy",
            to_target="user",
        )
        assert decision["publish"] is False
        assert decision["reason"] == "worker_waiting_on_manager"
        assert decision["audience_policy"] == "worker_reassurance"
        assert decision["cadence_action"] == "delay_and_wait"
        assert decision["manager_response_type"] == "worker_reassurance"


def test_gate_allows_direction_pending_manager_action_as_user_explanation():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_school",
            "School Contact",
            stage="school",
            owner="worker_school",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_school")
        tasks.assign_reviewer(tid, reviewer="reviewer_cindy", actor="manager")
        tasks.submit_for_review(tid, actor="worker_school")
        tasks.review_flow(
            tid,
            outcome="manager_action",
            actor="reviewer_cindy",
            review_reason="missing_owner_decision",
            manager_action_type="choose_direction",
        )
        event = tasks.list_task_events()[-1]
        decision = task_publish_gate.decide_task_event_publish(
            event,
            sender="reviewer_cindy",
            to_target="user",
        )
        assert decision["publish"] is False
        assert decision["reason"] == "worker_waiting_on_manager"
        assert decision["audience_policy"] == "worker_reassurance"
        assert decision["cadence_action"] == "delay_and_wait"
        assert decision["manager_response_type"] == "worker_reassurance"


def test_gate_assigns_manager_problem_taxonomy_for_internal_problem_reason():
    with isolated_env():
        event = {
            "event_id": "te-1",
            "task_id": "T-1",
            "kind": "transition",
            "before": {"status": "submitted_for_review"},
            "after": {
                "status": "blocked",
                "needs_manager_action": True,
                "verdict": "manager_action",
                "review_reason": "missing_required_artifact",
            },
            "changes": {},
            "created_at": 1,
        }
        decision = task_publish_gate.decide_task_event_publish(
            event,
            sender="reviewer_amy",
            to_target="user",
        )
        assert decision["manager_response_type"] == "manager_problem_material_pending"


def test_gate_keeps_reject_internal_even_when_changes_requested():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.assign_reviewer(tid, reviewer="reviewer_amy", actor="manager")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="reject",
            actor="reviewer_amy",
            review_reason="changes_requested",
        )
        event = tasks.list_task_events()[-1]
        decision = task_publish_gate.decide_task_event_publish(
            event,
            sender="reviewer_amy",
            to_target="user",
        )
        assert decision["publish"] is False
        assert decision["reason"] == "rejected_internal_only"
        assert decision["audience_policy"] == "internal_only"


def test_gate_rejects_non_store_event_without_diff_shape():
    event = {
        "task_id": "T-1",
        "kind": "transition",
        "actor": "worker_course",
        "after": {"status": "delivered"},
    }
    decision = task_publish_gate.decide_task_event_publish(
        event,
        sender="worker_course",
        to_target="user",
    )
    assert decision["publish"] is False
    assert decision["reason"] == "invalid_store_event"
    assert decision["reason_detail"].startswith("invalid_store_event:")


def test_gate_keeps_non_user_targets_internal():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Draft Unit 1 outline",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker")
        tasks.transition_flow(tid, to_status="submitted_for_review", actor="worker")
        tasks.transition_flow(tid, to_status="delivered", actor="reviewer")
        event = tasks.list_task_events()[-1]
        decision = task_publish_gate.decide_task_event_publish(
            event,
            sender="worker_course",
            to_target="manager",
        )
        assert decision["publish"] is False
        assert decision["reason"] == "non_user_target"


def test_gate_silences_manager_action_verdict_for_user():
    """Test that manager_action verdict generates publish=False with correct reason."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Physics 0625 Batch 5",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")

        # Use review_flow to create a proper event with manager_action
        tasks.review_flow(
            tid,
            outcome="manager_action",
            actor="review_course",
            review_reason="missing_scope_confirmation",
            manager_action_type="clarify_scope",
        )
        event = tasks.list_task_events()[-1]
        decision = task_publish_gate.decide_task_event_publish(
            event,
            sender="review_course",
            to_target="user",
        )

        assert decision["publish"] is False
        assert "manager_action" in str(decision.get("reason", "")) or decision.get("reason") == "worker_waiting_on_manager"


def test_gate_publishes_worker_completed_for_in_progress_to_submitted():
    """Test transition from in_progress to submitted_for_review generates correct reason."""
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Business Studies 0450 Batch 2",
            stage="curriculum",
            owner="worker_course",
            creator="manager",
        )
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")

        # Capture the submit_for_review event
        tasks.submit_for_review(tid, actor="worker_course")
        event = tasks.list_task_events()[-1]

        decision = task_publish_gate.decide_task_event_publish(
            event,
            sender="worker_course",
            to_target="user",
        )

        # Should generate worker_completed_handed_to_manager reason
        assert decision["publish"] is True
        assert decision["reason"] == "worker_completed_handed_to_manager"
        assert decision["audience_policy"] == "worker_reassurance"
        assert decision["delivery_lane"] == "worker_reassurance"


# ── Package 8: DedupCache regression tests ──────────────────────────
# These tests validate the dedup contract: same task_id+stage+content
# is suppressed within the window, but different tasks/stages/content
# and P0 anomalies always pass through.


def _make_test_decision(task_id="T-dedup-1", stage="curriculum",
                        reason="delivered_to_user", delivery_lane="manager_result"):
    """Minimal decision dict shaped like decide_task_event_publish output."""
    return {
        "publish": True,
        "reason": reason,
        "reason_detail": reason,
        "task_id": task_id,
        "event_kind": "transition",
        "status": "delivered",
        "delivery_lane": delivery_lane,
    }


def test_dedup_blocks_same_content_within_window():
    """Same task_id + stage + normalized_content within the dedup window
    must be recognised as a duplicate (is_duplicate returns True)."""
    from eduflow.store.task_publish_gate import DedupCache

    cache = DedupCache(window_ms=120_000)
    task_id = "T-dedup-1"
    stage = "curriculum"
    content = "课程研发已完成并交付：Unit 1 大纲（T-dedup-1）"

    # First call: cache miss
    assert cache.is_duplicate(task_id, stage, content) is False
    # Second call with exact same key: cache hit (within window)
    assert cache.is_duplicate(task_id, stage, content) is True


def test_dedup_allows_same_content_after_window_expires():
    """After the dedup window expires, the same content must be allowed
    through again (is_duplicate returns False after the TTL)."""
    import time
    from eduflow.store.task_publish_gate import DedupCache

    window_ms = 400
    cache = DedupCache(window_ms=window_ms)
    task_id = "T-dedup-2"
    stage = "curriculum"
    content = "课程研发已完成并交付：Unit 2 大纲（T-dedup-2）"

    assert cache.is_duplicate(task_id, stage, content) is False
    assert cache.is_duplicate(task_id, stage, content) is True

    # Advance past the window
    time.sleep(window_ms / 1000.0 + 0.05)

    # After expiry, same content is no longer a duplicate
    assert cache.is_duplicate(task_id, stage, content) is False


def test_dedup_allows_different_task_id():
    """Different task_id with same stage+content must NOT be deduped."""
    from eduflow.store.task_publish_gate import DedupCache

    cache = DedupCache(window_ms=120_000)
    stage = "curriculum"
    content = "课程研发已完成并交付：Unit 1 大纲（T-dedup-1）"

    assert cache.is_duplicate("T-A", stage, content) is False
    assert cache.is_duplicate("T-B", stage, content) is False
    # T-A again → duplicate of T-A
    assert cache.is_duplicate("T-A", stage, content) is True
    # T-B again → duplicate of T-B (not confused with T-A)
    assert cache.is_duplicate("T-B", stage, content) is True


def test_dedup_allows_different_stage():
    """Different stage with same task_id+content must NOT be deduped."""
    from eduflow.store.task_publish_gate import DedupCache

    cache = DedupCache(window_ms=120_000)
    task_id = "T-dedup-3"
    content = "已完成并交付：Same Content（T-dedup-3）"

    assert cache.is_duplicate(task_id, "curriculum", content) is False
    assert cache.is_duplicate(task_id, "review", content) is False
    assert cache.is_duplicate(task_id, "curriculum", content) is True
    # Different stage → not a duplicate
    assert cache.is_duplicate(task_id, "qbank", content) is False


def test_dedup_allows_different_content():
    """Different content with same task_id+stage must NOT be deduped."""
    from eduflow.store.task_publish_gate import DedupCache

    cache = DedupCache(window_ms=120_000)
    task_id = "T-dedup-4"
    stage = "curriculum"

    assert cache.is_duplicate(task_id, stage, "第一版本：内容A") is False
    assert cache.is_duplicate(task_id, stage, "第二版本：内容B") is False
    assert cache.is_duplicate(task_id, stage, "第一版本：内容A") is True
    assert cache.is_duplicate(task_id, stage, "第三版本：内容C") is False


def test_dedup_never_suppresses_internal_only_events():
    """Events with delivery_lane='internal_only' must bypass the dedup
    cache entirely — should_dedup_check returns False."""
    from eduflow.store.task_publish_gate import should_dedup_check

    decision_internal = _make_test_decision(delivery_lane="internal_only")
    assert should_dedup_check(decision_internal) is False


def test_dedup_never_suppresses_P0_anomaly_events():
    """P0 anomaly events (workflow_gate anomaly, ACK desync, truth drift,
    runtime fallback, closeout verifier fail, qbank needs_review) must
    never be checked against the dedup cache."""
    from eduflow.store.task_publish_gate import should_dedup_check

    P0_REASONS = [
        "workflow_gate_anomaly",
        "ack_desync",
        "task_truth_drift",
        "runtime_fallback_failure",
        "subject_closeout_verifier_fail",
        "qbank_needs_review",
        "qbank_needs_user_authorization",
    ]
    for reason in P0_REASONS:
        decision = _make_test_decision(reason=reason,
                                       delivery_lane="manager_result")
        assert should_dedup_check(decision) is False, \
            f"P0 anomaly '{reason}' must bypass dedup check"


def test_dedup_cache_prunes_expired_entries():
    """Cache prune_expired() removes entries past their window."""
    import time
    from eduflow.store.task_publish_gate import DedupCache

    window_ms = 200
    cache = DedupCache(window_ms=window_ms)

    assert cache.is_duplicate("T-1", "curriculum", "content-A") is False
    assert cache.is_duplicate("T-2", "review", "content-B") is False
    assert cache.is_duplicate("T-3", "qbank", "content-C") is False
    assert len(cache) == 3

    # Verify duplicate within window
    assert cache.is_duplicate("T-1", "curriculum", "content-A") is True

    # Advance past window + prune
    time.sleep(window_ms / 1000.0 + 0.1)
    pruned = cache.prune_expired()
    assert pruned == 3
    assert len(cache) == 0

    # After prune, all entries should be fresh again
    assert cache.is_duplicate("T-1", "curriculum", "content-A") is False


def test_dedup_normalizes_content_whitespace():
    """Whitespace is normalised so ``'a  b'`` and ``'a b'`` are treated
    as identical content for dedup purposes."""
    from eduflow.store.task_publish_gate import DedupCache

    cache = DedupCache(window_ms=120_000)
    task_id = "T-dedup-ws"
    stage = "curriculum"

    assert cache.is_duplicate(task_id, stage, "  content with  spaces  ") is False
    # Normalised version treated as duplicate
    assert cache.is_duplicate(task_id, stage, "content with spaces") is True
    # Tabs / newlines also normalised
    assert cache.is_duplicate(task_id, stage, "\tcontent with spaces\n") is True
