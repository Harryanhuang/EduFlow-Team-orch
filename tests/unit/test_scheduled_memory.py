"""P7: D scheduler decision-grade memory writes + graceful degrade.

D scheduler writes ONLY decision-grade summaries to memory:
  * rule_summary      — when a draft rule is created/confirmed
  * workflow_start    — when manager dispatches (status -> running)
  * workflow_stop     — when occurrence reaches done / failed / cancelled / skipped
  * major_failure     — when fail_pause_occurrence is invoked
  * user_preference   — when user records an explicit preference for the rule

Routine tick / reminder / wait events NEVER write to memory.
Memory subsystem failure must NOT break the scheduler (graceful degrade).
T memory behaviour must remain unchanged — D summaries use a separate
scope (`scheduler:rule:<D-id>`) and never mix into T capsule rows.
"""
from __future__ import annotations

import json

import pytest

from helpers import isolated_env
from eduflow.scheduling import engine, manager_ops
from eduflow.store import scheduled_tasks


def _ms(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> int:
    from datetime import datetime, timezone
    dt = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _utc(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> str:
    return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:00Z"


def _init_db():
    from eduflow.memory import db
    db.close()
    db.init_schema()


def _reset_db():
    from eduflow.memory import db
    db.close()


def _d_summary_items(rule_id: str | None = None) -> list[dict]:
    """Return all memory_items with metadata.summary_kind set (D scheduler
    summary records).  Filters by rule_id when provided."""
    from eduflow.memory.items import list_memories
    items = list_memories(kind="decision", status="confirmed", limit=200)
    out = []
    for m in items:
        scope = m.get("scope", "")
        if not scope.startswith("scheduler:rule:"):
            continue
        if rule_id is not None and not scope.endswith(f":{rule_id}"):
            continue
        meta = m.get("metadata_json")
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except Exception:
                meta = {}
        meta = meta or {}
        if meta.get("summary_kind"):
            m["_metadata"] = meta
            out.append(m)
    return out


# ── allowed kinds ────────────────────────────────────────────────────


def test_d_scheduler_summary_kinds_are_exactly_the_five():
    from eduflow.memory.capsules import D_SCHEDULER_ALLOWED_KINDS
    assert D_SCHEDULER_ALLOWED_KINDS == frozenset({
        "rule_summary",
        "workflow_start",
        "workflow_stop",
        "major_failure",
        "user_preference",
    })


def test_write_d_scheduler_summary_accepts_only_decision_grade_kinds():
    with isolated_env():
        _init_db()
        from eduflow.memory.capsules import write_d_scheduler_summary
        # All five decision-grade kinds accepted.
        for kind in ("rule_summary", "workflow_start", "workflow_stop",
                     "major_failure", "user_preference"):
            mid = write_d_scheduler_summary(
                rule_id="D-1", summary_kind=kind, content=f"{kind} text",
            )
            assert mid  # non-empty memory ID
        # Routine / non-decision-grade kinds rejected.
        for bad in ("tick", "reminder", "wait", "routine", ""):
            with pytest.raises(ValueError):
                write_d_scheduler_summary(
                    rule_id="D-1", summary_kind=bad, content="noise",
                )
        _reset_db()


def test_write_d_scheduler_summary_persists_to_separate_scope():
    with isolated_env():
        _init_db()
        from eduflow.memory.capsules import write_d_scheduler_summary, get_d_scheduler_summaries
        write_d_scheduler_summary(
            rule_id="D-7", summary_kind="rule_summary",
            content="weekly report at 10am Asia/Shanghai",
        )
        rows = get_d_scheduler_summaries("D-7")
        assert len(rows) == 1
        assert rows[0]["scope"] == "scheduler:rule:D-7"
        assert rows[0]["kind"] == "decision"
        assert rows[0]["content"] == "weekly report at 10am Asia/Shanghai"
        meta = json.loads(rows[0]["metadata_json"])
        assert meta["summary_kind"] == "rule_summary"
        _reset_db()


# ── T memory isolation ───────────────────────────────────────────────


def test_d_scheduler_summary_does_not_mix_into_t_capsules():
    """T capsule storage (task_capsules table) must remain untouched by
    D scheduler summary writes.  T capsules are keyed by T-<n>."""
    with isolated_env():
        _init_db()
        from eduflow.memory.capsules import (
            write_d_scheduler_summary,
            upsert_capsule,
            get_capsule,
        )
        # Create a real T capsule.
        upsert_capsule("T-1", goal="verify capsule isolation", current_status="in_progress")
        t_cap = get_capsule("T-1")
        assert t_cap["goal"] == "verify capsule isolation"

        # Write a D scheduler summary.
        write_d_scheduler_summary(
            rule_id="D-1", summary_kind="rule_summary",
            content="daily standup at 8am",
        )

        # T capsule must be untouched.
        t_cap_after = get_capsule("T-1")
        assert t_cap_after["goal"] == "verify capsule isolation"
        # And no T-1 capsule was created for D-1.
        assert get_capsule("D-1") is None
        _reset_db()


def test_d_scheduler_summary_does_not_pollute_t_packet_assembly():
    """Calling assemble_memory_packet('alice', task_id='T-1') for a T task
    must NOT surface D scheduler summaries in the rendered packet."""
    with isolated_env():
        _init_db()
        from eduflow.memory.capsules import (
            write_d_scheduler_summary,
            upsert_capsule,
        )
        from eduflow.memory.packet import assemble_memory_packet

        # A T capsule + a D scheduler summary.
        upsert_capsule("T-1", goal="build X", current_status="in_progress")
        write_d_scheduler_summary(
            rule_id="D-1", summary_kind="rule_summary",
            content="daily standup at 8am",
        )

        packet = assemble_memory_packet("alice", task_id="T-1")
        assert "build X" in packet
        assert "daily standup at 8am" not in packet
        _reset_db()


# ── scheduler: routine events must NOT write to memory ──────────────


def test_scheduler_tick_does_not_write_to_memory():
    """The scheduler tick routine must NEVER write a D summary."""
    with isolated_env():
        _init_db()
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        engine.tick(_ms(2026, 7, 12, 8, 1))  # second tick (no-op)
        rows = _d_summary_items(rid)
        assert rows == []
        _reset_db()


def test_notification_reminders_do_not_write_to_memory():
    """Cadence reminders (manager_reminder / user_notification) must
    NEVER produce a D scheduler summary record."""
    with isolated_env():
        _init_db()
        from eduflow.scheduling import notifications
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        notifications.compute_reminder_actions(now_ms=_ms(2026, 7, 12, 9, 0))
        notifications.compute_reminder_actions(now_ms=_ms(2026, 7, 12, 10, 0))
        rows = _d_summary_items(rid)
        assert rows == []
        _reset_db()


# ── decision-grade writes happen at the right moments ───────────────


def test_confirm_draft_writes_rule_summary():
    with isolated_env():
        _init_db()
        rid = manager_ops.create_draft_rule(
            target="weekly summary",
            artifact="summary.md",
            frequency="weekly",
            timezone="Asia/Shanghai",
            next_due_utc=_utc(2026, 7, 13, 10, 0),
            created_by="alice",
        )
        # Confirm draft — must produce a rule_summary record.
        manager_ops.confirm_draft_rule(rid, actor="alice", actor_role="user")
        rows = _d_summary_items(rid)
        assert len(rows) >= 1
        kinds = [r["_metadata"]["summary_kind"] for r in rows]
        assert "rule_summary" in kinds
        # Content references the rule target.
        content_blob = " ".join(r.get("content", "") for r in rows)
        assert "weekly summary" in content_blob
        _reset_db()


def test_dispatch_writes_workflow_start_summary():
    with isolated_env():
        _init_db()
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        key = f"{rid}:2026-07-12T08:00:00Z"
        manager_ops.confirm_occurrence(key, actor="manager", actor_role="manager")
        manager_ops.choose_lane(key, agent="worker_course", actor="manager", actor_role="manager")
        manager_ops.re_dispatch(key, actor="manager", actor_role="manager")
        rows = _d_summary_items(rid)
        kinds = [r["_metadata"]["summary_kind"] for r in rows]
        assert "workflow_start" in kinds
        _reset_db()


def test_fail_pause_writes_major_failure_and_workflow_stop_summaries():
    with isolated_env():
        _init_db()
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        key = f"{rid}:2026-07-12T08:00:00Z"
        manager_ops.fail_pause_occurrence(
            key, actor="manager", actor_role="manager",
            reason="worker blocked",
        )
        rows = _d_summary_items(rid)
        kinds = [r["_metadata"]["summary_kind"] for r in rows]
        # Both decision-grade kinds must be recorded for a major failure.
        assert "major_failure" in kinds
        assert "workflow_stop" in kinds
        content_blob = " ".join(r.get("content", "") for r in rows)
        assert "worker blocked" in content_blob
        _reset_db()


def test_skip_writes_workflow_stop_summary_only():
    """Skipping an occurrence is a soft stop — writes workflow_stop but
    NOT major_failure."""
    with isolated_env():
        _init_db()
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        engine.tick(_ms(2026, 7, 12, 8, 0))
        key = f"{rid}:2026-07-12T08:00:00Z"
        manager_ops.skip_occurrence(key, actor="manager", actor_role="manager", reason="holiday")
        rows = _d_summary_items(rid)
        kinds = [r["_metadata"]["summary_kind"] for r in rows]
        assert "workflow_stop" in kinds
        assert "major_failure" not in kinds
        _reset_db()


# ── memory failure does NOT break scheduler ─────────────────────────


def test_memory_failure_does_not_break_confirm_draft(monkeypatch):
    """If the memory subsystem raises, confirm_draft_rule must still
    succeed and the rule must remain active."""
    with isolated_env():
        _init_db()

        # Force every memory write to raise.  memory_bridge re-resolves
        # the writer lazily, so patching the source module is enough.
        from eduflow.memory import capsules as mem_capsules

        def _boom(*a, **kw):
            raise RuntimeError("memory db locked")
        monkeypatch.setattr(mem_capsules, "write_d_scheduler_summary", _boom)

        rid = manager_ops.create_draft_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
            created_by="alice",
        )
        # Must not raise despite memory outage.
        rule = manager_ops.confirm_draft_rule(rid, actor="alice", actor_role="user")
        assert rule["status"] == "active"
        # Rule persisted normally.
        stored = scheduled_tasks.get_rule(rid)
        assert stored["status"] == "active"
        _reset_db()


def test_memory_failure_does_not_break_scheduler_tick(monkeypatch):
    """Routine tick must remain unaffected even if memory is broken."""
    with isolated_env():
        _init_db()
        from eduflow.memory import capsules as mem_capsules

        def _boom(*a, **kw):
            raise RuntimeError("memory offline")
        monkeypatch.setattr(mem_capsules, "write_d_scheduler_summary", _boom)

        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        # No memory summary is expected for tick anyway, but a
        # broken memory module must not raise here either.
        result = engine.tick(_ms(2026, 7, 12, 8, 0))
        assert result["occurrences_created"] == [f"{rid}:2026-07-12T08:00:00Z"]
        _reset_db()


def test_memory_bridge_record_returns_false_on_failure(monkeypatch):
    """memory_bridge.record_* must swallow exceptions and return False."""
    with isolated_env():
        from eduflow.scheduling import memory_bridge
        from eduflow.memory import capsules as mem_capsules

        def _boom(*a, **kw):
            raise RuntimeError("memory offline")
        monkeypatch.setattr(mem_capsules, "write_d_scheduler_summary", _boom)

        assert memory_bridge.record_rule_summary("D-1", "x") is False
        assert memory_bridge.record_workflow_start("D-1", "k", "x") is False
        assert memory_bridge.record_workflow_stop("D-1", "k", "x") is False
        assert memory_bridge.record_major_failure("D-1", "k", "x") is False
        assert memory_bridge.record_user_preference("D-1", "x") is False


# ── packet rendering ────────────────────────────────────────────────


def test_render_d_scheduler_block_returns_empty_when_no_summaries():
    with isolated_env():
        _init_db()
        from eduflow.memory.packet import render_d_scheduler_block
        assert render_d_scheduler_block(rule_id="D-999") == ""
        _reset_db()


def test_render_d_scheduler_block_lists_decision_grade_summaries():
    with isolated_env():
        _init_db()
        from eduflow.memory.capsules import write_d_scheduler_summary
        from eduflow.memory.packet import render_d_scheduler_block

        write_d_scheduler_summary(
            rule_id="D-3", summary_kind="rule_summary",
            content="weekly report at 10am",
        )
        write_d_scheduler_summary(
            rule_id="D-3", summary_kind="workflow_start",
            content="dispatched D-3:2026-07-13T10:00:00Z",
        )
        block = render_d_scheduler_block(rule_id="D-3")
        assert "D Scheduler" in block
        assert "rule_summary" in block
        assert "workflow_start" in block
        assert "weekly report at 10am" in block
        assert "dispatched" in block
        _reset_db()


def test_render_d_scheduler_block_does_not_show_routine_records():
    with isolated_env():
        _init_db()
        # Even if a non-decision-grade memory somehow ended up under the
        # scheduler scope, render must filter it out.
        from eduflow.memory.capsules import write_d_scheduler_summary
        from eduflow.memory.items import add_memory
        from eduflow.memory.packet import render_d_scheduler_block

        write_d_scheduler_summary(
            rule_id="D-9", summary_kind="rule_summary", content="real summary",
        )
        # Inject a non-summary memory under the same scope.
        add_memory(
            scope="scheduler:rule:D-9", kind="note",
            content="noise", status="confirmed",
        )
        block = render_d_scheduler_block(rule_id="D-9")
        assert "real summary" in block
        assert "noise" not in block
        _reset_db()


# ── T memory capsule behaviour unchanged ─────────────────────────────


def test_t_capsule_upsert_still_works_alongside_d_summaries():
    """Adding D summary helpers must not regress T capsule CRUD."""
    with isolated_env():
        _init_db()
        from eduflow.memory.capsules import (
            upsert_capsule,
            get_capsule,
            write_d_scheduler_summary,
        )
        upsert_capsule("T-1", goal="refactor auth", current_status="in_progress",
                       decisions=["use JWT"])
        write_d_scheduler_summary(
            rule_id="D-1", summary_kind="rule_summary", content="x",
        )
        cap = get_capsule("T-1")
        assert cap["goal"] == "refactor auth"
        assert json.loads(cap["decisions"]) == ["use JWT"]
        _reset_db()