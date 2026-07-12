from __future__ import annotations

import re
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


def test_done_claims_are_evidenced_or_explicitly_unverified() -> None:
    rows = {row["plan"]: row for row in _rows()}
    for plan in _plan_files():
        text = (PLANS / plan).read_text(encoding="utf-8")
        if re.search(r"\bDONE\b", text):
            evidence = rows[plan]["done_evidence"]
            complete_evidence = all(
                marker in evidence for marker in ("code:", "commit:", "test:")
            )
            explicit_non_claim = evidence in {"unverified", "incomplete"}
            assert complete_evidence or explicit_non_claim, (
                f"{plan}: DONE claims need code+commit+test evidence, or must be "
                "labelled unverified/incomplete"
            )


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
