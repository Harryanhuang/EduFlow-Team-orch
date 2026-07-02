"""Focused tests for eduflow.memory.candidates — promotion guards and lifecycle.

Covers:
- promote_candidate: low-impact no reviewer, high-impact requires reviewer,
  hermes_can_promote flag, hermes high-impact always blocked, scope guard
- reject_candidate: status transition, idempotent, missing returns false
- expire_stale_candidates: only proposed+expired are rejected, count returned
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
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


def _add_note_candidate(scope="team", content="test note", **kw):
    """Helper: add a low-impact candidate (note kind)."""
    from eduflow.memory.candidates import add_candidate
    return add_candidate(
        scope=scope, kind="note", content=content, **kw,
    )


def _add_high_impact_candidate(kind="workflow_rule", scope="team", **kw):
    """Helper: add a high-impact candidate."""
    from eduflow.memory.candidates import add_candidate
    return add_candidate(
        scope=scope, kind=kind, content=f"high impact {kind}", **kw,
    )


# ── promote_candidate: basic ──────────────────────────────────────

class TestPromoteBasic:
    def test_low_impact_no_reviewer_needed(self):
        """note/mistake/domain_fact can promote without a reviewer."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import promote_candidate, get_candidate
            cid = _add_note_candidate()
            mid = promote_candidate(cid)
            assert mid.startswith("MI-")
            cand = get_candidate(cid)
            assert cand["review_status"] == "promoted"
            _reset_db()

    def test_promote_creates_confirmed_memory_item(self):
        """Promoted candidate becomes a confirmed memory_item."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import promote_candidate
            from eduflow.memory.items import get_memory
            cid = _add_note_candidate(
                scope="agent:alice", content="important note",
            )
            mid = promote_candidate(cid, reviewer="manager")
            item = get_memory(mid)
            assert item is not None
            assert item["status"] == "confirmed"
            assert item["scope"] == "agent:alice"
            assert item["content"] == "important note"
            _reset_db()

    def test_promote_not_found_raises(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import promote_candidate
            with pytest.raises(ValueError, match="candidate not found"):
                promote_candidate("CAND-00000000-999")
            _reset_db()

    def test_promote_non_proposed_raises(self):
        """Cannot promote a candidate that was already promoted or rejected."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import (
                promote_candidate, reject_candidate, get_candidate,
            )
            cid = _add_note_candidate()
            reject_candidate(cid, reviewer="test")
            cand = get_candidate(cid)
            assert cand["review_status"] == "rejected"
            with pytest.raises(ValueError, match="not in 'proposed' status"):
                promote_candidate(cid)
            _reset_db()

    def test_promote_already_promoted_raises(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import promote_candidate
            cid = _add_note_candidate()
            promote_candidate(cid)
            with pytest.raises(ValueError, match="not in 'proposed' status"):
                promote_candidate(cid)
            _reset_db()


# ── promote_candidate: high-impact guard ───────────────────────────

class TestPromoteHighImpact:
    def test_high_impact_without_reviewer_raises(self):
        """High-impact kinds require a designated reviewer."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import promote_candidate
            cid = _add_high_impact_candidate(kind="workflow_rule")
            with pytest.raises(ValueError, match="high-impact kind.*requires designated reviewer"):
                promote_candidate(cid)
            _reset_db()

    def test_high_impact_with_manager_reviewer_succeeds(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import promote_candidate
            cid = _add_high_impact_candidate(kind="decision")
            mid = promote_candidate(cid, reviewer="manager")
            assert mid.startswith("MI-")
            _reset_db()

    def test_high_impact_with_hermes_reviewer_raises(self):
        """Hermes can NEVER promote high-impact kinds, even with flag."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import promote_candidate
            cid = _add_high_impact_candidate(kind="role_rule")
            with pytest.raises(ValueError, match="Hermes cannot promote high-impact"):
                promote_candidate(
                    cid, reviewer="hermes", hermes_can_promote=True,
                )
            _reset_db()

    @pytest.mark.parametrize("kind", [
        "workflow_rule", "role_rule", "runtime_rule",
        "decision", "preference", "handoff",
    ])
    def test_all_high_impact_kinds_require_reviewer(self, kind):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import promote_candidate
            cid = _add_high_impact_candidate(kind=kind)
            with pytest.raises(ValueError, match="high-impact"):
                promote_candidate(cid)
            _reset_db()

    @pytest.mark.parametrize("kind", ["note", "domain_fact", "mistake"])
    def test_low_impact_kinds_dont_require_reviewer(self, kind):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import add_candidate, promote_candidate
            cid = add_candidate(
                scope="team", kind=kind, content=f"low impact {kind}",
            )
            mid = promote_candidate(cid)
            assert mid.startswith("MI-")
            _reset_db()


# ── promote_candidate: hermes_can_promote flag ─────────────────────

class TestPromoteHermesFlag:
    def test_hermes_without_flag_raises(self):
        """Hermes cannot promote without hermes_can_promote flag."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import promote_candidate
            cid = _add_note_candidate()
            with pytest.raises(ValueError, match="requires the hermes_can_promote flag"):
                promote_candidate(cid, reviewer="hermes")
            _reset_db()

    def test_hermes_with_flag_on_hermes_scope_succeeds(self):
        """Hermes CAN promote low-impact on hermes-owned scope."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import promote_candidate
            cid = _add_note_candidate(scope="agent:Hermes")
            mid = promote_candidate(
                cid, reviewer="hermes", hermes_can_promote=True,
            )
            assert mid.startswith("MI-")
            _reset_db()

    def test_hermes_with_flag_on_team_scope_succeeds(self):
        """Hermes can promote on team scope (team-level housekeeping)."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import promote_candidate
            cid = _add_note_candidate(scope="team")
            mid = promote_candidate(
                cid, reviewer="hermes", hermes_can_promote=True,
            )
            assert mid.startswith("MI-")
            _reset_db()

    def test_hermes_with_flag_on_foreign_scope_raises(self):
        """Hermes cannot promote candidates outside hermes-owned scope."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import promote_candidate
            cid = _add_note_candidate(scope="agent:worker_qbank")
            with pytest.raises(ValueError, match="hermes_can_promote requires.*Hermes context"):
                promote_candidate(
                    cid, reviewer="hermes", hermes_can_promote=True,
                )
            _reset_db()

    def test_hermes_with_flag_on_hermes_prefix_scope_succeeds(self):
        """Scope 'hermes:*' prefix is recognized as hermes-owned."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import promote_candidate
            cid = _add_note_candidate(scope="hermes:housekeeping")
            mid = promote_candidate(
                cid, reviewer="hermes", hermes_can_promote=True,
            )
            assert mid.startswith("MI-")
            _reset_db()

    def test_hermes_with_flag_on_hermes_source_type_succeeds(self):
        """source_type starting with 'hermes_' is recognized."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import promote_candidate
            cid = _add_note_candidate(
                scope="agent:worker_course",
                source_type="hermes_manual",
            )
            mid = promote_candidate(
                cid, reviewer="hermes", hermes_can_promote=True,
            )
            assert mid.startswith("MI-")
            _reset_db()


# ── reject_candidate ───────────────────────────────────────────────

class TestRejectCandidate:
    def test_reject_changes_status(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import (
                reject_candidate, get_candidate,
            )
            cid = _add_note_candidate()
            ok = reject_candidate(cid, reviewer="alice", reason="not useful")
            assert ok is True
            cand = get_candidate(cid)
            assert cand["review_status"] == "rejected"
            assert cand["reviewed_by"] == "alice"
            _reset_db()

    def test_reject_not_found_returns_false(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import reject_candidate
            ok = reject_candidate("CAND-00000000-999")
            assert ok is False
            _reset_db()

    def test_reject_already_rejected_returns_false(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import reject_candidate
            cid = _add_note_candidate()
            reject_candidate(cid)
            ok = reject_candidate(cid)
            assert ok is False
            _reset_db()

    def test_reject_already_promoted_returns_false(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import (
                promote_candidate, reject_candidate,
            )
            cid = _add_note_candidate()
            promote_candidate(cid)
            ok = reject_candidate(cid)
            assert ok is False
            _reset_db()


# ── expire_stale_candidates ────────────────────────────────────────

class TestExpireStaleCandidates:
    def _add_expired_candidate(self, scope="team"):
        """Insert a candidate whose expires_at is in the past."""
        from eduflow.memory.db import get_conn
        from eduflow.memory.candidates import _now_iso, _next_candidate_id
        now = _now_iso()
        past = (datetime.fromisoformat(now) - timedelta(days=1)).isoformat()
        cid = _next_candidate_id(now)
        conn = get_conn()
        conn.execute(
            """INSERT INTO memory_candidates
               (candidate_id, source_type, source_ref, proposed_layer,
                proposed_scope, proposed_kind, content, reason,
                evidence_refs, risk_flags, created_at, review_status,
                reviewed_by, reviewed_at, expires_at)
               VALUES (?, 'manual', '', 'episode', ?, 'note', 'expired', '',
                       '[]', '[]', ?, 'proposed', '', '', ?)""",
            (cid, scope, now, past),
        )
        conn.commit()
        return cid

    def test_expires_proposed_past_due(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import (
                expire_stale_candidates, get_candidate,
            )
            cid = self._add_expired_candidate()
            count = expire_stale_candidates()
            assert count == 1
            cand = get_candidate(cid)
            assert cand["review_status"] == "rejected"
            assert cand["reviewed_by"] == "system"
            _reset_db()

    def test_does_not_expire_future_candidates(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import expire_stale_candidates
            _add_note_candidate()  # expires in 90 days
            count = expire_stale_candidates()
            assert count == 0
            _reset_db()

    def test_does_not_expire_already_rejected(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import (
                expire_stale_candidates, reject_candidate,
            )
            cid = self._add_expired_candidate()
            reject_candidate(cid, reviewer="alice")
            count = expire_stale_candidates()
            assert count == 0
            _reset_db()

    def test_does_not_expire_already_promoted(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import (
                promote_candidate, expire_stale_candidates,
            )
            cid = self._add_expired_candidate()
            promote_candidate(cid)
            count = expire_stale_candidates()
            assert count == 0
            _reset_db()

    def test_batch_expiration(self):
        """Multiple expired candidates are all expired in one call."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import expire_stale_candidates
            for _ in range(5):
                self._add_expired_candidate()
            count = expire_stale_candidates()
            assert count == 5
            _reset_db()

    def test_idempotent_double_call(self):
        """Running expire twice only processes once."""
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import expire_stale_candidates
            self._add_expired_candidate()
            expire_stale_candidates()
            count = expire_stale_candidates()
            assert count == 0
            _reset_db()
