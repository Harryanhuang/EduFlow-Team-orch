"""Tests for EduFlow Memory Phase 3: Manual Candidate/Promote.

Covers: candidate CRUD, promote (with high-impact guard), reject,
CLI integration.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tests.helpers import isolated_env


# ── helpers ───────────────────────────────────────────────────────

def _init_db():
    from eduflow.memory.db import init_schema, close
    close()
    init_schema()


def _reset_db():
    from eduflow.memory.db import close
    close()


# ── Candidate CRUD ───────────────────────────────────────────────

class TestCandidateCRUD:
    def test_add_candidate(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import add_candidate, get_candidate
            cid = add_candidate(
                scope="team", kind="note",
                content="candidate note content",
                source_type="manual", reason="test reason",
            )
            assert cid.startswith("CAND-")
            c = get_candidate(cid)
            assert c is not None
            assert c["content"] == "candidate note content"
            assert c["review_status"] == "proposed"
            assert c["source_type"] == "manual"
            # Default expiry: 90 days
            assert c["expires_at"] > c["created_at"]
            _reset_db()

    def test_add_candidate_high_impact_shorter_expiry(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import add_candidate, get_candidate
            cid = add_candidate(
                scope="team", kind="workflow_rule",
                content="high impact rule",
            )
            c = get_candidate(cid)
            # High-impact: 30 days expiry
            from datetime import datetime
            created = datetime.fromisoformat(c["created_at"])
            expires = datetime.fromisoformat(c["expires_at"])
            delta_days = (expires - created).days
            assert delta_days == 30
            _reset_db()

    def test_list_candidates_default_proposed(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import add_candidate, list_candidates
            add_candidate(scope="team", kind="note", content="proposed one")
            add_candidate(scope="team", kind="note", content="proposed two")
            candidates = list_candidates(status="proposed")
            assert len(candidates) == 2
            _reset_db()

    def test_list_candidates_by_scope(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import add_candidate, list_candidates
            add_candidate(scope="team", kind="note", content="team candidate")
            add_candidate(scope="agent:worker", kind="note", content="worker candidate")
            team_cands = list_candidates(scope="team", status="proposed")
            assert len(team_cands) == 1
            assert team_cands[0]["proposed_scope"] == "team"
            _reset_db()


# ── Promote ───────────────────────────────────────────────────────

class TestPromote:
    def test_promote_creates_confirmed_memory(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import add_candidate, promote_candidate
            from eduflow.memory.items import get_memory
            cid = add_candidate(
                scope="team", kind="note",
                content="promote me",
            )
            mid = promote_candidate(cid, reviewer="test")
            assert mid.startswith("MI-")
            m = get_memory(mid)
            assert m is not None
            assert m["status"] == "confirmed"
            assert m["content"] == "promote me"
            _reset_db()

    def test_promote_low_impact_no_reviewer_needed(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import add_candidate, promote_candidate
            cid = add_candidate(scope="team", kind="note", content="low impact")
            # note is NOT high-impact, so no reviewer required
            mid = promote_candidate(cid)
            assert mid.startswith("MI-")
            _reset_db()

    def test_promote_high_impact_requires_reviewer(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import add_candidate, promote_candidate
            cid = add_candidate(scope="team", kind="workflow_rule", content="high impact")
            with pytest.raises(ValueError, match="designated reviewer"):
                promote_candidate(cid)  # no reviewer
            _reset_db()

    def test_promote_high_impact_with_authorized_reviewer(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import add_candidate, promote_candidate
            cid = add_candidate(scope="team", kind="workflow_rule", content="high impact")
            mid = promote_candidate(cid, reviewer="manager")
            assert mid.startswith("MI-")
            _reset_db()

    def test_promote_high_impact_unauthorized_reviewer_rejected(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import add_candidate, promote_candidate
            cid = add_candidate(scope="team", kind="decision", content="high impact")
            with pytest.raises(ValueError, match="designated reviewer"):
                promote_candidate(cid, reviewer="worker_course")
            _reset_db()

    def test_promote_nonexistent_candidate(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import promote_candidate
            with pytest.raises(ValueError, match="not found"):
                promote_candidate("CAND-99999999-999")
            _reset_db()


# ── Reject ────────────────────────────────────────────────────────

class TestReject:
    def test_reject_sets_status(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import add_candidate, reject_candidate, get_candidate
            cid = add_candidate(scope="team", kind="note", content="reject me")
            ok = reject_candidate(cid)
            assert ok is True
            c = get_candidate(cid)
            assert c["review_status"] == "rejected"
            _reset_db()

    def test_reject_with_reason(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import add_candidate, reject_candidate, get_candidate
            cid = add_candidate(scope="team", kind="note", content="reject with reason")
            reject_candidate(cid, reviewer="manager", reason="duplicate")
            c = get_candidate(cid)
            assert c["reviewed_by"] == "manager"
            _reset_db()

    def test_reject_nonexistent(self):
        with isolated_env():
            _init_db()
            from eduflow.memory.candidates import reject_candidate
            ok = reject_candidate("CAND-99999999-999")
            assert ok is False
            _reset_db()


# ── CLI Integration ───────────────────────────────────────────────

class TestCLIIntegration:
    def test_cli_items_add_and_get(self):
        with isolated_env():
            _init_db()
            from tests.helpers import run_cli
            rc, out, err = run_cli(["memory", "items", "add", "team", "domain_fact",
                           "CLI test content", "--status", "confirmed"])
            assert rc == 0
            assert "Created memory item" in out
            # Extract the ID from output
            mid = out.strip().split(": ")[-1]
            rc2, out2, err2 = run_cli(["memory", "items", "get", mid])
            assert rc2 == 0
            assert "CLI test content" in out2
            _reset_db()

    def test_cli_search(self):
        with isolated_env():
            _init_db()
            from tests.helpers import run_cli
            from eduflow.memory.items import add_memory
            add_memory(scope="team", kind="note",
                      content="searchable CLI test content", status="confirmed")
            rc, out, err = run_cli(["memory", "search", "searchable"])
            assert rc == 0
            assert "Search results" in out
            assert "searchable" in out
            _reset_db()

    def test_cli_candidate_add_and_promote(self):
        with isolated_env():
            _init_db()
            from tests.helpers import run_cli
            rc, out, err = run_cli(["memory", "candidate", "add", "team", "note",
                           "CLI candidate content"])
            assert rc == 0
            assert "Created candidate" in out
            cid = out.strip().split(": ")[-1]
            rc2, out2, err2 = run_cli(["memory", "promote", cid])
            assert rc2 == 0
            assert "Promoted" in out2
            _reset_db()

    def test_cli_candidate_reject(self):
        with isolated_env():
            _init_db()
            from tests.helpers import run_cli
            rc, out, err = run_cli(["memory", "candidate", "add", "team", "note",
                           "CLI reject candidate"])
            assert rc == 0
            assert "Created candidate" in out
            cid = out.strip().split(": ")[-1]
            rc2, out2, err2 = run_cli(["memory", "reject", cid, "--reason", "not useful"])
            assert rc2 == 0
            assert "Rejected" in out2
            _reset_db()
