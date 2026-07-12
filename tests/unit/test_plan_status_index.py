from __future__ import annotations

import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PLANS = ROOT / "docs" / "plans"
INDEX = PLANS / "PLAN_STATUS_INDEX.md"
ALLOWED_STATUSES = {"historical", "active", "superseded", "observation-only"}


def _plan_files() -> set[str]:
    return {path.name for path in PLANS.glob("*.md") if path != INDEX}


def _rows() -> list[dict[str, str]]:
    assert INDEX.is_file(), f"historical-plan ledger is missing: {INDEX}"
    rows: list[dict[str, str]] = []
    for line in INDEX.read_text(encoding="utf-8").splitlines():
        if line.startswith("| `CLM-"):
            continue
        if not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        assert len(cells) == 5, f"index row must contain five columns: {line}"
        rows.append(
            dict(
                plan=cells[0].strip("`"),
                status=cells[1],
                gate_task=cells[2],
                disposition=cells[3],
                done_evidence=cells[4],
            )
        )
    return rows


def _claim_rows() -> list[dict[str, str]]:
    assert INDEX.is_file(), f"historical-plan ledger is missing: {INDEX}"
    claims: list[dict[str, str]] = []
    for line in INDEX.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| `CLM-"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        assert len(cells) == 8, f"claim row must contain eight columns: {line}"
        claims.append(
            dict(
                claim_id=cells[0].strip("`"),
                source=cells[1],
                assertion=cells[2],
                status=cells[3],
                code=cells[4],
                commit=cells[5],
                test=cells[6],
                notes=cells[7],
            )
        )
    return claims


def _master_done_state_rows() -> list[tuple[int, str, str]]:
    master = PLANS / "2026-07-12-eduflow-governed-team-operating-system-master-plan.md"
    rows: list[tuple[int, str, str]] = []
    for number, line in enumerate(master.read_text(encoding="utf-8").splitlines(), 1):
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if len(cells) == 4 and re.fullmatch(r"DONE(?:/PARTIAL)?", cells[1]):
            rows.append((number, cells[0], cells[1]))
    return rows


def test_index_has_exactly_one_row_for_every_top_level_plan() -> None:
    rows = _rows()
    indexed = [row["plan"] for row in rows]
    assert set(indexed) == _plan_files()
    assert len(indexed) == len(set(indexed)), "each plan must occur exactly once"


def test_statuses_and_active_gate_links_are_explicit() -> None:
    rows = _rows()
    for row in rows:
        assert row["status"] in ALLOWED_STATUSES
        if row["status"] == "active":
            assert re.search(r"\bG(?:-1|[0-7])\b", row["gate_task"])
            assert re.search(r"\bTask\s+\d+\b", row["gate_task"])
        else:
            assert row["gate_task"] == "—"


def test_done_tokens_are_classified_as_claims_or_normative() -> None:
    rows = {row["plan"]: row for row in _rows()}
    master = "2026-07-12-eduflow-governed-team-operating-system-master-plan.md"
    acceptance = "2026-07-12-eduflow-upgrade-acceptance-standard.md"
    g_minus_1 = "2026-07-12-g-minus-1-production-governance-implementation-plan.md"
    assert rows[master]["done_evidence"] == "claim ledger (5 claims)"
    assert rows[acceptance]["done_evidence"] == "not_applicable (normative)"
    assert rows[g_minus_1]["done_evidence"] == "not_applicable (normative)"


def test_each_master_done_assertion_has_its_own_claim_evidence() -> None:
    state_rows = _master_done_state_rows()
    assert [(title, status) for _, title, status in state_rows] == [
        ("Residency warm/active/sleep/wake", "DONE"),
        ("Feishu Cards v2", "DONE"),
        ("Flow task 与 REVIEW/CLOSEOUT 边界", "DONE/PARTIAL"),
        ("Workflow Registry", "DONE"),
    ]

    claims = _claim_rows()
    assert len(claims) == 5
    assert len({claim["claim_id"] for claim in claims}) == 5
    source_counts = Counter(claim["source"] for claim in claims)
    for line, _, status in state_rows:
        source = f"master-plan:L{line}"
        assert source_counts[source] == (2 if status == "DONE/PARTIAL" else 1)

    for claim in claims:
        assert claim["status"] in {"verified", "unverified", "incomplete"}
        assert re.search(r"`src/[^`]+`", claim["code"])
        assert re.search(r"`[0-9a-f]{8,40}`", claim["commit"])
        assert "pytest" in claim["test"] and "tests/" in claim["test"]


def test_document_level_unverified_cannot_cover_multiple_done_claims() -> None:
    rows = {row["plan"]: row for row in _rows()}
    master = rows["2026-07-12-eduflow-governed-team-operating-system-master-plan.md"]
    assert master["done_evidence"] not in {"unverified", "incomplete"}
    assert {claim["source"] for claim in _claim_rows()}


def test_scheduled_plans_record_preexisting_engine_without_claiming_g6() -> None:
    rows = {row["plan"]: row for row in _rows()}
    for name in (
        "2026-07-11-scheduled-tasks-design.md",
        "2026-07-11-scheduled-tasks.md",
    ):
        disposition = rows[name]["disposition"]
        assert "bde14c5c" in disposition and "a64d611c" in disposition
        assert "src/eduflow/scheduling/" in disposition
        assert "src/eduflow/store/scheduled_tasks.py" in disposition
        assert "tests/unit/test_scheduled_engine.py" in disposition
        assert "tests/integration/test_scheduled_tasks_e2e.py" in disposition
        assert "out-of-order preexisting implementation" in disposition
        assert "G6 remains unaccepted" in disposition


def test_duplicate_copy_is_explicitly_superseded() -> None:
    rows = {row["plan"]: row for row in _rows()}
    duplicate = "2026-06-21 EduFlow Team overnight gap repair packages_副本.md"
    canonical = "2026-06-21 EduFlow Team overnight gap repair packages.md"
    assert rows[duplicate]["status"] == "superseded"
    assert f"`{canonical}`" in rows[duplicate]["disposition"]


def test_every_superseded_plan_names_its_replacement() -> None:
    plans = _plan_files()
    for row in _rows():
        if row["status"] != "superseded":
            continue
        match = re.fullmatch(r"Superseded by `(.+\.md)`", row["disposition"])
        assert match, f"{row['plan']}: supersession target must be explicit"
        assert match.group(1) in plans
