"""P7: D scheduler retention policy and archival queries.

The scheduler store is the single source of truth.  After a configured
retention window (default 90 days), the full per-occurrence / lane /
notification audit is summarised and the raw rows are deleted.  Active
or unfinished references (awaiting_manager / running / confirmed /
blocked) MUST stay in the active store regardless of age.

Retention is configurable and supports a dry-run mode that returns the
list of candidates without mutating state.
"""
from __future__ import annotations

import pytest

from helpers import isolated_env
from eduflow.store import scheduled_tasks


def _ms(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> int:
    from datetime import datetime, timezone
    dt = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _utc(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> str:
    return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:00Z"


def _day_ms(year: int, month: int, day: int) -> int:
    return _ms(year, month, day)


# ── helpers exist + constants ────────────────────────────────────────


def test_retention_default_is_90_days():
    from eduflow.store.scheduled_tasks import DEFAULT_RETENTION_DAYS
    assert DEFAULT_RETENTION_DAYS == 90


def test_active_statuses_set_includes_unfinished_only():
    from eduflow.store.scheduled_tasks import ACTIVE_STATUSES
    assert ACTIVE_STATUSES == frozenset({
        "awaiting_manager",
        "confirmed",
        "running",
        "blocked",
    })


# ── find_archival_candidates ────────────────────────────────────────


def test_find_archival_candidates_returns_empty_when_nothing_old():
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 7, 12, 8, 0),
        )
        scheduled_tasks.create_occurrence(rid, scheduled_at_utc=_utc(2026, 7, 12, 8, 0))
        # Cutoff well before the occurrence age — nothing old enough.
        candidates = scheduled_tasks.find_archival_candidates(
            cutoff_ms=_ms(2026, 7, 11, 0, 0),
        )
        assert candidates["occurrences"] == []
        assert candidates["lanes"] == []
        assert candidates["notifications"] == []


def test_find_archival_candidates_finds_old_completed_occurrence():
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 1, 1, 8, 0),
        )
        key = scheduled_tasks.create_occurrence(
            rid, scheduled_at_utc=_utc(2026, 1, 1, 8, 0),
            status="done",
        )
        # Backdate the occurrence by writing created_at directly.
        from eduflow.runtime import paths
        data = {
            "occurrences": [{
                "id": key, "rule_id": rid,
                "scheduled_at_utc": _utc(2026, 1, 1, 8, 0),
                "status": "done", "context": {}, "version": 1,
                "created_at": _ms(2026, 1, 1, 8, 0),
                "updated_at": _ms(2026, 1, 1, 8, 0),
            }],
            "_meta": {"version_counter": 1},
        }
        from eduflow.util import write_json
        write_json(paths.scheduler_occurrences_file(), data)

        # Cutoff 100 days after creation -> eligible for archival.
        cutoff = _ms(2026, 1, 1, 8, 0) + 100 * 24 * 60 * 60 * 1000
        candidates = scheduled_tasks.find_archival_candidates(cutoff_ms=cutoff)
        assert any(c["id"] == key for c in candidates["occurrences"])


def test_find_archival_candidates_skips_active_unfinished_occurrences():
    """Active/unfinished occurrences (awaiting_manager / running /
    confirmed / blocked) must NEVER appear in candidates regardless
    of age — they must remain in the active store."""
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2025, 1, 1, 8, 0),
        )
        # Backdate so they're ancient — yet they're awaiting_manager.
        from eduflow.runtime import paths
        from eduflow.util import write_json
        ancient = _ms(2025, 1, 1, 8, 0)
        write_json(paths.scheduler_occurrences_file(), {
            "occurrences": [
                {
                    "id": f"{rid}:2025-01-01T08:00:00Z", "rule_id": rid,
                    "scheduled_at_utc": _utc(2025, 1, 1, 8, 0),
                    "status": "awaiting_manager", "context": {}, "version": 1,
                    "created_at": ancient, "updated_at": ancient,
                },
                {
                    "id": f"{rid}:2025-01-02T08:00:00Z", "rule_id": rid,
                    "scheduled_at_utc": _utc(2025, 1, 2, 8, 0),
                    "status": "running", "context": {}, "version": 1,
                    "created_at": ancient, "updated_at": ancient,
                },
                {
                    "id": f"{rid}:2025-01-03T08:00:00Z", "rule_id": rid,
                    "scheduled_at_utc": _utc(2025, 1, 3, 8, 0),
                    "status": "confirmed", "context": {}, "version": 1,
                    "created_at": ancient, "updated_at": ancient,
                },
                {
                    "id": f"{rid}:2025-01-04T08:00:00Z", "rule_id": rid,
                    "scheduled_at_utc": _utc(2025, 1, 4, 8, 0),
                    "status": "blocked", "context": {}, "version": 1,
                    "created_at": ancient, "updated_at": ancient,
                },
                # done is the only status that's archivable.
                {
                    "id": f"{rid}:2025-01-05T08:00:00Z", "rule_id": rid,
                    "scheduled_at_utc": _utc(2025, 1, 5, 8, 0),
                    "status": "done", "context": {}, "version": 1,
                    "created_at": ancient, "updated_at": ancient,
                },
            ],
            "_meta": {"version_counter": 5},
        })

        cutoff = ancient + 100 * 24 * 60 * 60 * 1000
        candidates = scheduled_tasks.find_archival_candidates(cutoff_ms=cutoff)
        candidate_ids = [c["id"] for c in candidates["occurrences"]]
        # The 4 active ones MUST be absent.
        assert f"{rid}:2025-01-01T08:00:00Z" not in candidate_ids
        assert f"{rid}:2025-01-02T08:00:00Z" not in candidate_ids
        assert f"{rid}:2025-01-03T08:00:00Z" not in candidate_ids
        assert f"{rid}:2025-01-04T08:00:00Z" not in candidate_ids
        # The done one IS eligible.
        assert f"{rid}:2025-01-05T08:00:00Z" in candidate_ids


def test_find_archival_candidates_includes_lanes_for_done_occurrences():
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2025, 1, 1, 8, 0),
        )
        key = scheduled_tasks.create_occurrence(
            rid, scheduled_at_utc=_utc(2025, 1, 1, 8, 0), status="done",
        )
        lane_id = scheduled_tasks.create_lane(
            occurrence_key=key, agent="worker_course",
        )

        from eduflow.runtime import paths
        from eduflow.util import write_json
        ancient = _ms(2025, 1, 1, 8, 0)
        write_json(paths.scheduler_occurrences_file(), {
            "occurrences": [{
                "id": key, "rule_id": rid,
                "scheduled_at_utc": _utc(2025, 1, 1, 8, 0),
                "status": "done", "context": {}, "version": 1,
                "created_at": ancient, "updated_at": ancient,
            }],
            "_meta": {"version_counter": 1},
        })
        write_json(paths.scheduler_lanes_file(), {
            "lanes": [{
                "id": lane_id, "occurrence_key": key,
                "agent": "worker_course", "dependencies": [],
                "inputs": {}, "artifacts": [], "evidence": {},
                "status": "done",
                "created_at": ancient, "updated_at": ancient,
            }],
            "_meta": {"version_counter": 1},
        })

        cutoff = ancient + 100 * 24 * 60 * 60 * 1000
        candidates = scheduled_tasks.find_archival_candidates(cutoff_ms=cutoff)
        assert any(c["id"] == key for c in candidates["occurrences"])
        assert any(c["id"] == lane_id for c in candidates["lanes"])


def test_find_archival_candidates_includes_notifications_for_old_occurrences():
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2025, 1, 1, 8, 0),
        )
        scheduled_tasks.append_notification(
            rid, "manager", "occurrence_due",
            occurrence_key=f"{rid}:2025-01-01T08:00:00Z",
            payload={"scheduled_at_utc": "2025-01-01T08:00:00Z"},
        )

        from eduflow.runtime import paths
        from eduflow.util import write_json, read_jsonl
        ancient = _ms(2025, 1, 1, 8, 0)
        # Backdate the notification row.
        rows = read_jsonl(paths.scheduler_notifications_file())
        for row in rows:
            row["created_at"] = ancient
        write_json(
            paths.scheduler_notifications_file().with_suffix(".rewritten.jsonl"),
            rows,
        )
        # Rewrite the JSONL with the backdated timestamp.
        import json as _json
        with paths.scheduler_notifications_file().open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(_json.dumps(row, ensure_ascii=False) + "\n")

        cutoff = ancient + 100 * 24 * 60 * 60 * 1000
        candidates = scheduled_tasks.find_archival_candidates(cutoff_ms=cutoff)
        assert len(candidates["notifications"]) >= 1


# ── archive_old_records (dry-run) ───────────────────────────────────


def test_archive_old_records_dry_run_does_not_mutate():
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2025, 1, 1, 8, 0),
        )
        key = scheduled_tasks.create_occurrence(
            rid, scheduled_at_utc=_utc(2025, 1, 1, 8, 0), status="done",
        )
        from eduflow.runtime import paths
        from eduflow.util import write_json
        ancient = _ms(2025, 1, 1, 8, 0)
        write_json(paths.scheduler_occurrences_file(), {
            "occurrences": [{
                "id": key, "rule_id": rid,
                "scheduled_at_utc": _utc(2025, 1, 1, 8, 0),
                "status": "done", "context": {}, "version": 1,
                "created_at": ancient, "updated_at": ancient,
            }],
            "_meta": {"version_counter": 1},
        })

        cutoff = ancient + 100 * 24 * 60 * 60 * 1000
        result = scheduled_tasks.archive_old_records(
            cutoff_ms=cutoff, dry_run=True,
        )
        assert result["dry_run"] is True
        assert any(c["id"] == key for c in result["candidates"]["occurrences"])
        # State unchanged.
        occs = scheduled_tasks.list_occurrences(rule_id=rid)
        assert len(occs) == 1
        assert occs[0]["id"] == key


# ── archive_old_records (commit) ────────────────────────────────────


def test_archive_old_records_summarizes_and_removes_done_occurrences():
    """After archive, the detailed occurrence row is replaced with a
    summary row (same id) and the summary carries evidence references
    that allow reconstruction from active store."""
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2025, 1, 1, 8, 0),
        )
        key = scheduled_tasks.create_occurrence(
            rid, scheduled_at_utc=_utc(2025, 1, 1, 8, 0),
            status="done",
            context={"notes": "completed by worker_course"},
        )
        scheduled_tasks.append_notification(
            rid, "manager", "occurrence_due",
            occurrence_key=key, payload={"scheduled_at_utc": _utc(2025, 1, 1, 8, 0)},
        )

        from eduflow.runtime import paths
        from eduflow.util import write_json
        ancient = _ms(2025, 1, 1, 8, 0)
        write_json(paths.scheduler_occurrences_file(), {
            "occurrences": [{
                "id": key, "rule_id": rid,
                "scheduled_at_utc": _utc(2025, 1, 1, 8, 0),
                "status": "done", "context": {"notes": "completed"},
                "version": 1, "created_at": ancient, "updated_at": ancient,
            }],
            "_meta": {"version_counter": 1},
        })

        cutoff = ancient + 100 * 24 * 60 * 60 * 1000
        result = scheduled_tasks.archive_old_records(
            cutoff_ms=cutoff, dry_run=False,
        )
        assert result["dry_run"] is False
        assert any(c["id"] == key for c in result["candidates"]["occurrences"])

        # Occurrence still present, but summarised.
        occs = scheduled_tasks.list_occurrences(rule_id=rid)
        assert len(occs) == 1
        archived = occs[0]
        assert archived["id"] == key
        assert archived.get("archived") is True
        assert archived.get("status") == "done"
        # Original audit detail replaced by summary fields.
        assert "summary" in archived
        assert "evidence_refs" in archived
        assert isinstance(archived["evidence_refs"], list)
        # Original noisy context stripped (notes removed).
        ctx = archived.get("context", {})
        if isinstance(ctx, dict):
            assert "notes" not in ctx


def test_archive_old_records_keeps_active_unfinished_occurrences_intact():
    """Active/unfinished occurrences MUST stay in the active store with
    their full detail — even if their age exceeds the retention window."""
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2025, 1, 1, 8, 0),
        )
        from eduflow.runtime import paths
        from eduflow.util import write_json
        ancient = _ms(2025, 1, 1, 8, 0)
        write_json(paths.scheduler_occurrences_file(), {
            "occurrences": [
                {
                    "id": f"{rid}:2025-01-01T08:00:00Z", "rule_id": rid,
                    "scheduled_at_utc": _utc(2025, 1, 1, 8, 0),
                    "status": "awaiting_manager", "context": {"x": 1},
                    "version": 1, "created_at": ancient, "updated_at": ancient,
                },
                {
                    "id": f"{rid}:2025-01-02T08:00:00Z", "rule_id": rid,
                    "scheduled_at_utc": _utc(2025, 1, 2, 8, 0),
                    "status": "running", "context": {"x": 2},
                    "version": 1, "created_at": ancient, "updated_at": ancient,
                },
            ],
            "_meta": {"version_counter": 2},
        })

        cutoff = ancient + 365 * 24 * 60 * 60 * 1000  # 1 year later
        result = scheduled_tasks.archive_old_records(cutoff_ms=cutoff, dry_run=False)
        # Neither was archived.
        candidate_ids = [c["id"] for c in result["candidates"]["occurrences"]]
        assert candidate_ids == []

        # Both still intact with original context.
        occs = scheduled_tasks.list_occurrences(rule_id=rid)
        assert len(occs) == 2
        for occ in occs:
            assert occ.get("archived") is None
            assert occ.get("context", {}).get("x") in (1, 2)


# ── retention window helpers ────────────────────────────────────────


def test_retention_cutoff_ms_uses_default_when_unspecified():
    from eduflow.store.scheduled_tasks import retention_cutoff_ms
    now = _ms(2026, 7, 12, 12, 0)
    cutoff = retention_cutoff_ms(now, retention_days=None)
    expected = now - 90 * 24 * 60 * 60 * 1000
    assert cutoff == expected


def test_retention_cutoff_ms_honours_retention_days_override():
    from eduflow.store.scheduled_tasks import retention_cutoff_ms
    now = _ms(2026, 7, 12, 12, 0)
    cutoff = retention_cutoff_ms(now, retention_days=30)
    expected = now - 30 * 24 * 60 * 60 * 1000
    assert cutoff == expected


def test_archive_old_records_accepts_retention_days_override():
    """A 50-day-old occurrence is NOT eligible with a 30-day cutoff
    but IS eligible with a 60-day retention override."""
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2026, 5, 23, 8, 0),
        )
        key = scheduled_tasks.create_occurrence(
            rid, scheduled_at_utc=_utc(2026, 5, 23, 8, 0), status="done",
        )
        from eduflow.runtime import paths
        from eduflow.util import write_json
        old = _ms(2026, 5, 23, 8, 0)
        write_json(paths.scheduler_occurrences_file(), {
            "occurrences": [{
                "id": key, "rule_id": rid,
                "scheduled_at_utc": _utc(2026, 5, 23, 8, 0),
                "status": "done", "context": {}, "version": 1,
                "created_at": old, "updated_at": old,
            }],
            "_meta": {"version_counter": 1},
        })

        # 50 days after creation.
        now = _ms(2026, 5, 23, 8, 0) + 50 * 24 * 60 * 60 * 1000
        # 30-day window: cutoff = now - 30d → occurrence older than 30d → eligible.
        cands_30 = scheduled_tasks.find_archival_candidates(
            cutoff_ms=scheduled_tasks.retention_cutoff_ms(now, retention_days=30),
        )
        assert any(c["id"] == key for c in cands_30["occurrences"])
        # 60-day window: cutoff = now - 60d → occurrence (50d old) is NEWER than cutoff → NOT eligible.
        cands_60 = scheduled_tasks.find_archival_candidates(
            cutoff_ms=scheduled_tasks.retention_cutoff_ms(now, retention_days=60),
        )
        assert not any(c["id"] == key for c in cands_60["occurrences"])


# ── evidence references preserved ───────────────────────────────────


def test_archived_occurrence_keeps_rule_id_and_occurrence_key_as_evidence():
    """Summary record must keep enough information to reconstruct what
    was archived (rule_id, occurrence_key, original scheduled_at_utc)."""
    with isolated_env():
        rid = scheduled_tasks.create_rule(
            target="x", artifact="x.md", frequency="daily",
            timezone="UTC", next_due_utc=_utc(2025, 1, 1, 8, 0),
        )
        key = scheduled_tasks.create_occurrence(
            rid, scheduled_at_utc=_utc(2025, 1, 1, 8, 0), status="done",
        )
        from eduflow.runtime import paths
        from eduflow.util import write_json
        ancient = _ms(2025, 1, 1, 8, 0)
        write_json(paths.scheduler_occurrences_file(), {
            "occurrences": [{
                "id": key, "rule_id": rid,
                "scheduled_at_utc": _utc(2025, 1, 1, 8, 0),
                "status": "done", "context": {}, "version": 1,
                "created_at": ancient, "updated_at": ancient,
            }],
            "_meta": {"version_counter": 1},
        })

        cutoff = ancient + 100 * 24 * 60 * 60 * 1000
        scheduled_tasks.archive_old_records(cutoff_ms=cutoff, dry_run=False)

        occ = scheduled_tasks.get_occurrence(key)
        assert occ["rule_id"] == rid
        assert occ["id"] == key
        assert occ["scheduled_at_utc"] == _utc(2025, 1, 1, 8, 0)
        # Evidence references present.
        assert occ["evidence_refs"]
        assert any(rid in ref for ref in occ["evidence_refs"])
        # archived_at recorded.
        assert occ["archived_at"] > 0