"""G1.R3 reconciliation contracts for stale inbox truth."""
from __future__ import annotations

from helpers import isolated_env
from eduflow.commands import health
from eduflow.store import local_facts, task_event_scanner


def test_stale_unread_moves_to_auditable_reconciliation_queue_without_marking_read():
    with isolated_env():
        message_id = local_facts.append_message(
            "worker_course",
            "manager",
            "[T-172] Please repair the current course packet.",
            priority="high",
            task_id="T-172",
        )
        local_facts.append_log(
            "worker_course",
            "say",
            "T-172 course packet repair started and the current packet was delivered.",
        )
        local_facts.upsert_status("worker_course", "进行中", "T-999 current task")

        findings = task_event_scanner.scan_manager_anomalies()
        queued = local_facts.list_inbox_reconciliation_queue()
        message = local_facts.get_message(message_id)

        assert any(
            row.get("message_id") == message_id
            and row.get("category") == "inbox_reconciliation_pending"
            for row in findings
        )
        assert message is not None
        assert message["read"] is False
        assert message["ack_state"] == "reconciliation_pending"
        assert local_facts.list_messages("worker_course", unread_only=True) == []
        assert local_facts.mark_all_read("worker_course") == 0
        preserved = local_facts.get_message(message_id)
        assert preserved is not None and preserved["read"] is False
        assert len(queued) == 1
        pending = queued[0]
        assert pending["actor"] == "task_event_scanner"
        assert pending["evidence"]
        assert pending["before"]["read"] is False
        assert pending["after"]["ack_state"] == "reconciliation_pending"
        assert health._agent_inbox_recovery_needed("worker_course") is False
        assert task_event_scanner._open_high_priority_unacked_messages("worker_course") == []
        local_facts.append_log(
            "worker_course",
            "say",
            "continuing production for T-172 after the visible delivery signal",
        )
        assert not [
            row for row in task_event_scanner.scan_manager_anomalies()
            if row.get("message_id") == message_id
            and row.get("category") == "worker_high_priority_unacked_while_producing"
        ]

        task_event_scanner.scan_manager_anomalies()
        assert len(local_facts.list_inbox_reconciliation_queue()) == 1
        status_before_reconcile = local_facts.get_status("worker_course")

        assert local_facts.reconcile_inbox_message(
            message_id,
            actor="manager",
            evidence="worker_course visible delivery signal for T-172",
        ) is True

        resolved = local_facts.get_message(message_id)
        queue = local_facts.list_inbox_reconciliation_queue()
        current_status = local_facts.get_status("worker_course")

    assert resolved is not None
    assert resolved["read"] is False
    assert resolved["ack_state"] == "reconciled"
    assert current_status is not None
    assert current_status == status_before_reconcile
    assert queue[-1]["actor"] == "manager"
    assert queue[-1]["evidence"] == "worker_course visible delivery signal for T-172"
    assert queue[-1]["before"]["ack_state"] == "reconciliation_pending"
    assert queue[-1]["after"]["ack_state"] == "reconciled"


def test_reconciliation_pending_does_not_project_or_allow_untracked_mutation():
    with isolated_env():
        local_facts.upsert_status("worker_course", "进行中", "T-999 current task")
        message_id = local_facts.append_message(
            "worker_course", "manager", "T-172 stale instruction", priority="high",
        )
        assert local_facts.mark_read(message_id)
        assert local_facts.queue_inbox_reconciliation(
            message_id,
            actor="task_event_scanner",
            evidence="newer visible task truth",
        )

        status = local_facts.get_status("worker_course")
        assert status is not None
        assert status["task"] == "T-999 current task"
        assert local_facts.update_message_delivery(message_id, "inject_failed_requires_polling") is False
        assert local_facts.prune_orphan_messages(set())["pruned"] == 0

        message = local_facts.get_message(message_id)
        queue = local_facts.list_inbox_reconciliation_queue()

    assert message is not None
    assert message["read"] is True
    assert message.get("archived") is not True
    assert len(queue) == 1
