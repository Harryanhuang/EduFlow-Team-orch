"""Tests for V3 P2 items: admission gate, JIT recall, dashboard."""
from __future__ import annotations

import pytest

from eduflow.memory import db, items, admission, jit_recall, dashboard


@pytest.fixture(autouse=True)
def _clean_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test_memory.db"
    conn = db.sqlite3.connect(str(db_path), timeout=5.0)
    conn.row_factory = db.sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")

    db._local.conn = conn
    db.init_schema()
    db.migrate_pinned_column()
    yield
    conn.close()
    db._local.conn = None


# ── Admission gate (P2-1) ───────────────────────────────────────────

def test_score_high_quality_passes():
    """High-quality candidate with evidence + team scope + stable source should pass."""
    result = admission.score_candidate(
        content="Always verify closeout items",
        source_type="review_reject",
        source_ref="T-29",
        evidence_refs=["audit-log-1", "audit-log-2"],
        proposed_scope="team",
        proposed_kind="workflow_rule",
        risk_flags=[],
    )
    assert result["passed"] is True
    assert result["score"] >= 0.5
    assert len(result["reasons"]) == 0


def test_score_low_quality_blocked():
    """No evidence + task scope + unstable source + note kind should be blocked."""
    result = admission.score_candidate(
        content="x",
        source_type="unknown_source",
        source_ref="",
        evidence_refs=[],
        proposed_scope="task:T-1",
        proposed_kind="note",
        risk_flags=[],
    )
    assert result["passed"] is False
    assert result["score"] < 0.5
    assert len(result["reasons"]) > 0


def test_score_conflict_penalty():
    """Candidates similar to existing memory should be penalized."""
    base = admission.score_candidate(
        content="closeout rule",
        source_type="manual",
        source_ref="",
        evidence_refs=["ev1"],
        proposed_scope="team",
        proposed_kind="workflow_rule",
    )
    penalized = admission.score_candidate(
        content="closeout rule",
        source_type="manual",
        source_ref="",
        evidence_refs=["ev1"],
        proposed_scope="team",
        proposed_kind="workflow_rule",
        similar_to_existing=True,
    )
    assert penalized["score"] < base["score"]
    assert any("similar" in r for r in penalized["reasons"])


def test_score_risk_flags_recorded():
    result = admission.score_candidate(
        content="risky",
        source_type="manual",
        source_ref="",
        evidence_refs=["ev1"],
        proposed_scope="team",
        proposed_kind="note",
        risk_flags=["unsafe", "unverified"],
    )
    assert any("risk flags" in r for r in result["reasons"])


def test_score_breakdown_keys():
    result = admission.score_candidate(
        content="x",
        source_type="manual",
        source_ref="",
        evidence_refs=[],
        proposed_scope="team",
        proposed_kind="note",
    )
    assert set(result["breakdown"].keys()) == {
        "evidence_quality",
        "reusability",
        "stability",
        "kind_weight",
        "conflict_penalty",
    }


def test_score_scope_team_high_reusability():
    """team and lane scopes should give high reusability."""
    team = admission.score_candidate("x", "manual", "", ["ev1"], "team", "note")
    lane = admission.score_candidate("x", "manual", "", ["ev1"], "lane:course", "note")
    workflow = admission.score_candidate("x", "manual", "", ["ev1"], "workflow:igcse", "note")
    task = admission.score_candidate("x", "manual", "", ["ev1"], "task:T-1", "note")
    assert team["breakdown"]["reusability"] >= 0.7
    assert lane["breakdown"]["reusability"] >= 0.7
    assert workflow["breakdown"]["reusability"] == 0.7
    assert task["breakdown"]["reusability"] < 0.5


# ── JIT recall (P2-2) ──────────────────────────────────────────────

def test_get_recent_decisions():
    items.add_memory(scope="team", kind="decision", content="decided x",
                     status="confirmed")
    items.add_memory(scope="team", kind="note", content="note",
                     status="confirmed")

    decisions = jit_recall.get_recent_decisions()
    assert all(d["kind"] == "decision" for d in decisions)
    assert len(decisions) >= 1


def test_get_mistakes_for_agent():
    items.add_memory(scope="agent:worker_course", kind="mistake",
                     content="tried X", status="confirmed")
    items.add_memory(scope="agent:worker_course", kind="note",
                     content="not a mistake", status="confirmed")

    mistakes = jit_recall.get_mistakes_for_agent(agent="worker_course")
    assert all(m["kind"] == "mistake" for m in mistakes)


def test_get_mistakes_for_lane():
    items.add_memory(scope="lane:course", kind="mistake",
                     content="lane mistake", status="confirmed")

    mistakes = jit_recall.get_mistakes_for_agent(lane="course")
    assert len(mistakes) >= 1


def test_get_handoffs():
    items.add_memory(scope="workflow:abc", kind="handoff",
                     content="passed from manager", status="confirmed")

    handoffs = jit_recall.get_handoffs(workflow_id="abc")
    assert len(handoffs) >= 1


def test_get_facts_by_kind():
    items.add_memory(scope="team", kind="domain_fact",
                     content="domain fact 1", status="confirmed")

    facts = jit_recall.get_facts_by_kind("domain_fact")
    assert all(f["kind"] == "domain_fact" for f in facts)


def test_jit_recall_empty_results():
    """Empty DB should return empty lists, not error."""
    assert jit_recall.get_recent_decisions() == []
    assert jit_recall.get_mistakes_for_agent(agent="nonexistent") == []
    assert jit_recall.get_handoffs() == []
    assert jit_recall.get_facts_by_kind("nonexistent_kind") == []


# ── Dashboard (P2-4) ────────────────────────────────────────────────

def test_dashboard_trends_empty():
    trends = dashboard.get_memory_trends(days=7)
    assert len(trends) == 7
    for t in trends:
        assert "date" in t
        assert t["items_added"] == 0


def test_dashboard_trends_with_data():
    items.add_memory(scope="team", kind="note", content="recent", status="confirmed")
    trends = dashboard.get_memory_trends(days=7)
    today = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).date().isoformat()
    today_bucket = next(t for t in trends if t["date"] == today)
    assert today_bucket["items_added"] >= 1


def test_dashboard_top_injected():
    items.add_memory(scope="team", kind="note", content="touched", status="confirmed")
    items.add_memory(scope="team", kind="note", content="untouched", status="confirmed")

    top = dashboard.get_top_injected_memories(days=7, limit=5)
    assert len(top) >= 1
    assert all("id" in m for m in top)


def test_dashboard_candidate_quality():
    from eduflow.memory.candidates import add_candidate, reject_candidate
    add_candidate(scope="team", kind="note", content="proposed candidate")
    cid2 = add_candidate(scope="team", kind="note", content="to be rejected")
    reject_candidate(cid2)

    quality = dashboard.get_candidate_quality_distribution()
    assert quality["total"] >= 2
    assert "proposed" in quality["by_status"]
    assert "rejected" in quality["by_status"]


def test_dashboard_pinned_summary():
    mid = items.add_memory(scope="team", kind="workflow_rule", content="x", status="confirmed")
    items.pin_memory(mid)

    summary = dashboard.get_pinned_summary()
    assert summary["total"] >= 1
    assert "workflow_rule" in summary["by_kind"]


def test_dashboard_render_includes_sections():
    rendered = dashboard.render_dashboard(days=7)
    assert "# 📊 EduFlow Memory Dashboard" in rendered
    assert "Trends" in rendered
    assert "Recently Touched" in rendered
    assert "Candidate Quality" in rendered
    assert "Consolidation" in rendered
    assert "Pinned Memories" in rendered


def test_dashboard_similar_pair_count_graceful():
    """Should return int even when vector store unavailable."""
    count = dashboard.get_similar_pair_count(threshold=0.5)
    assert isinstance(count, int)