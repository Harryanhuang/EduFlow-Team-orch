"""P1: independent D scheduler store persistence.

Tests the scheduler domain's JSON-backed store:
- D IDs are independent from T IDs
- rules persist with version/CAS semantics
- occurrences are idempotent by D-<id>:scheduled_at_utc
- cancel retains audit history
- illegal status transitions raise ValueError
"""
from __future__ import annotations

import json

import pytest

from helpers import isolated_env
from eduflow.runtime import paths
from eduflow.store import scheduled_tasks


# ── D-ID independence ────────────────────────────────────────────────


def test_d_id_sequence_starts_at_one_and_independent_of_tasks():
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="daily standup summary",
            artifact="summary.md",
            frequency="daily",
            timezone="Asia/Shanghai",
            next_due_utc="2026-07-12T08:00:00Z",
        )
        assert did == "D-1"
        meta = json.loads(paths.scheduler_meta_file().read_text(encoding="utf-8"))
        assert meta["last_id"] == 1
        assert not (paths.state_dir() / "tasks.json").exists()


def test_d_ids_increment_and_do_not_reuse():
    with isolated_env():
        assert scheduled_tasks.create_rule(
            target="a", artifact="a.md", frequency="once",
            timezone="UTC", next_due_utc="2026-07-12T08:00:00Z",
        ) == "D-1"
        assert scheduled_tasks.create_rule(
            target="b", artifact="b.md", frequency="daily",
            timezone="UTC", next_due_utc="2026-07-12T09:00:00Z",
        ) == "D-2"


# ── rule persistence shape ───────────────────────────────────────────


def test_rule_has_required_fields():
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="weekly report",
            artifact="report.pdf",
            frequency="weekly",
            timezone="Asia/Shanghai",
            next_due_utc="2026-07-13T10:00:00Z",
            capacity=2,
        )
        rule = scheduled_tasks.get_rule(did)
        assert rule["id"] == did
        assert rule["version"] == 1
        assert rule["target"] == "weekly report"
        assert rule["artifact"] == "report.pdf"
        assert rule["frequency"] == "weekly"
        assert rule["timezone"] == "Asia/Shanghai"
        assert rule["next_due_utc"] == "2026-07-13T10:00:00Z"
        assert rule["status"] == "active"
        assert rule["capacity"] == 2
        assert "workflow_state" in rule
        assert "created_at" in rule
        assert "updated_at" in rule


# ── CAS / version conflict ───────────────────────────────────────────


def test_update_rule_requires_matching_version():
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="once",
            timezone="UTC", next_due_utc="2026-07-12T08:00:00Z",
        )
        with pytest.raises(scheduled_tasks.VersionConflict):
            scheduled_tasks.update_rule(did, {"capacity": 3}, expected_version=99)
        rule = scheduled_tasks.get_rule(did)
        assert rule["version"] == 1
        assert rule["capacity"] == 1


def test_update_rule_increments_version_and_persists():
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc="2026-07-12T08:00:00Z",
        )
        updated = scheduled_tasks.update_rule(
            did, {"capacity": 2, "next_due_utc": "2026-07-13T08:00:00Z"},
            expected_version=1,
        )
        assert updated["version"] == 2
        assert updated["capacity"] == 2
        rule = scheduled_tasks.get_rule(did)
        assert rule["version"] == 2


# ── status transitions ───────────────────────────────────────────────


def test_rule_starts_active_and_can_pause_and_resume():
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc="2026-07-12T08:00:00Z",
        )
        scheduled_tasks.pause_rule(did, expected_version=1)
        rule = scheduled_tasks.get_rule(did)
        assert rule["status"] == "paused"
        assert rule["version"] == 2

        scheduled_tasks.resume_rule(did, expected_version=2)
        rule = scheduled_tasks.get_rule(did)
        assert rule["status"] == "active"
        assert rule["version"] == 3


def test_illegal_status_transitions_raise():
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="once",
            timezone="UTC", next_due_utc="2026-07-12T08:00:00Z",
        )
        scheduled_tasks.cancel_rule(did, expected_version=1)
        with pytest.raises(ValueError):
            scheduled_tasks.resume_rule(did, expected_version=2)
        with pytest.raises(ValueError):
            scheduled_tasks.pause_rule(did, expected_version=2)


# ── cancel retains audit history ─────────────────────────────────────


def test_cancel_retains_rule_record_and_sets_cancelled_at():
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc="2026-07-12T08:00:00Z",
        )
        before = scheduled_tasks.get_rule(did)
        scheduled_tasks.cancel_rule(did, expected_version=1)
        after = scheduled_tasks.get_rule(did)
        assert after["status"] == "cancelled"
        assert after["cancelled_at"] is not None
        assert after["cancelled_at"] >= before["created_at"]
        assert after["version"] == 2
        # Record is retained, not deleted.
        assert len(scheduled_tasks.list_rules()) == 1


# ── occurrence idempotency ───────────────────────────────────────────


def test_occurrence_key_is_rule_id_and_scheduled_at_utc():
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc="2026-07-12T08:00:00Z",
        )
        key = scheduled_tasks.create_occurrence(
            did, scheduled_at_utc="2026-07-12T08:00:00Z",
        )
        assert key == "D-1:2026-07-12T08:00:00Z"


def test_duplicate_occurrence_creation_is_idempotent():
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc="2026-07-12T08:00:00Z",
        )
        key1 = scheduled_tasks.create_occurrence(
            did, scheduled_at_utc="2026-07-12T08:00:00Z",
        )
        key2 = scheduled_tasks.create_occurrence(
            did, scheduled_at_utc="2026-07-12T08:00:00Z",
        )
        assert key1 == key2
        assert len(scheduled_tasks.list_occurrences()) == 1


# ── separate persistence files ───────────────────────────────────────


def test_scheduler_uses_separate_files():
    with isolated_env():
        did = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="once",
            timezone="UTC", next_due_utc="2026-07-12T08:00:00Z",
        )
        scheduled_tasks.create_occurrence(
            did, scheduled_at_utc="2026-07-12T08:00:00Z",
        )
        scheduled_tasks.append_notification(did, "manager", "due_soon")
        scheduled_tasks.touch_heartbeat()

        assert paths.scheduler_rules_file().exists()
        assert paths.scheduler_occurrences_file().exists()
        assert paths.scheduler_notifications_file().exists()
        assert paths.scheduler_heartbeat_file().exists()
        # Must never touch tasks.py metadata or tasks.json.
        assert not (paths.state_dir() / "tasks.json").exists()


def test_tasks_json_unaffected_by_scheduler_writes():
    with isolated_env():
        from eduflow.store import tasks as task_store
        tid = task_store.create("worker", "ordinary task")
        scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="once",
            timezone="UTC", next_due_utc="2026-07-12T08:00:00Z",
        )
        data = json.loads((paths.state_dir() / "tasks.json").read_text(encoding="utf-8"))
        assert data["_meta"]["last_id"] == 1
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["id"] == tid
