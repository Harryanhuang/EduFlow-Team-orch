#!/usr/bin/env python3
"""Regression verification: EduFlow Memory real production cases.

Two real production incidents validate that the memory system prevents
recurrence:

Case 1 — "Anna Fire": Departed worker agent:anna's personal memories
must NOT leak into other workers' Memory Packets. Scope isolation,
alias resolution, deprecation, and Obsidian archive export are verified.

Case 2 — "0606 Inconsistency": Active Constraint + Gate + Re-injection.
Constraints recorded after the T-29 items/QQL/manifest mismatch must
survive reidentify cycles and remain enforceable even when verdict is
FAIL (Package 3 review-verdict authority).

Dual-mode:
    pytest scripts/verify_memory_cases.py          # pytest integration
    python3 scripts/verify_memory_cases.py          # standalone report
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Path bootstrap — safe under both pytest (conftest.py handles it) and
# standalone execution.
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parents[1]
_SRC = _PROJECT_ROOT / "src"
_TESTS = _PROJECT_ROOT / "tests"
for _p in (_SRC, _TESTS):
    _sp = str(_p)
    if _sp not in sys.path:
        sys.path.insert(0, _sp)

import pytest  # noqa: E402  (must follow path bootstrap)

from helpers import isolated_env  # noqa: E402


# ---------------------------------------------------------------------------
# DB helpers — follow the pattern from tests/unit/test_memory_*.py
# ---------------------------------------------------------------------------

def _init_db():
    """Reset the thread-local SQLite connection and (re-)create schema."""
    from eduflow.memory.db import close, init_schema
    close()  # clear any stale connection from a prior test
    init_schema()


def _reset_db():
    from eduflow.memory.db import close
    close()


# ===================================================================
# Case 1 — Anna Fire: Departed agent memory isolation
# ===================================================================

def _run_case1(tmp_dir: Path) -> list[tuple[str, bool, str]]:
    """Execute all Case 1 verification points.

    Returns a list of (point_id, passed, detail) triples.
    Each point is wrapped in its own try/except so a single failure
    does not prevent later points from running.
    """
    results: list[tuple[str, bool, str]] = []
    os.environ["EDUFLOW_OBSIDIAN_ROOT"] = str(tmp_dir)

    with isolated_env():
        _init_db()

        from eduflow.memory.items import (
            add_memory,
            deprecate_memory,
            list_memories,
        )
        from eduflow.memory.constraints import add_constraint
        from eduflow.memory.scope_aliases import add_alias, resolve_alias
        from eduflow.memory.packet import assemble_memory_packet
        from eduflow.memory.obsidian_export import export_all

        # ── 1.1 — agent:anna confirmed memory visible in her scope ──
        try:
            anna_mid = add_memory(
                scope="agent:anna",
                kind="note",
                content="Anna's confidential project observation",
                layer="episode",
                status="confirmed",
                importance=7,
            )
            anna_mems = list_memories(scope="agent:anna", status="confirmed")
            assert len(anna_mems) >= 1, f"expected >=1, got {len(anna_mems)}"
            assert any(
                m["id"] == anna_mid for m in anna_mems
            ), f"anna_mid={anna_mid} not in results"
            results.append(("1.1", True, "anna memories scoped correctly"))
        except Exception as exc:
            results.append(("1.1", False, str(exc)))

        # ── 1.2 — worker_ben packet does NOT contain anna's memory ──
        try:
            ben_packet = assemble_memory_packet("worker_ben")
            assert "Anna's confidential project observation" not in ben_packet, (
                "LEAK: anna's memory found in worker_ben's packet!"
            )
            results.append(("1.2", True, "no memory leak to worker_ben"))
        except Exception as exc:
            results.append(("1.2", False, str(exc)))

        # ── 1.3 — team-level constraint visible in worker_ben packet ──
        try:
            add_constraint(
                scope="team",
                level="L0",
                constraint_type="must_follow",
                content="All workers must submit daily status",
                enforcement="prompt_only",
            )
            ben_packet2 = assemble_memory_packet("worker_ben")
            assert "All workers must submit daily status" in ben_packet2, (
                "team constraint missing from worker_ben packet"
            )
            results.append(("1.3", True, "team constraint visible to worker_ben"))
        except Exception as exc:
            results.append(("1.3", False, str(exc)))

        # ── 1.4 — scope alias resolves correctly ──
        try:
            add_alias("anna_legacy", "agent:anna")
            resolved = resolve_alias("anna_legacy")
            assert resolved == "agent:anna", f"expected agent:anna, got {resolved}"
            assert resolve_alias("nonexistent_alias") is None, (
                "nonexistent alias should return None"
            )
            results.append(("1.4", True, "scope alias resolved correctly"))
        except Exception as exc:
            results.append(("1.4", False, str(exc)))

        # ── 1.5 — deprecated anna memory → archive/ not decisions/ ──
        try:
            deprecate_memory(anna_mid)
            mem = list_memories(scope="agent:anna", status="deprecated")
            assert len(mem) >= 1, "deprecated memory not found"
            export_all()
            archive_f = tmp_dir / "_memory-exports" / "archive" / f"{anna_mid}.md"
            decisions_f = tmp_dir / "_memory-exports" / "decisions" / f"{anna_mid}.md"
            assert archive_f.exists(), (
                f"deprecated memory NOT in archive/ ({archive_f})"
            )
            assert not decisions_f.exists(), (
                f"deprecated memory still in decisions/ ({decisions_f})"
            )
            results.append(("1.5", True, "deprecated → archive, not decisions"))
        except Exception as exc:
            results.append(("1.5", False, str(exc)))

        # ── 1.6 — archive dir contains anna's deprecated memory file ──
        try:
            archive_dir = tmp_dir / "_memory-exports" / "archive"
            assert archive_dir.is_dir(), "archive/ dir missing"
            archive_files = list(archive_dir.glob("*.md"))
            anna_archive = [f for f in archive_files if anna_mid in f.name]
            assert len(anna_archive) >= 1, (
                f"anna's deprecated file not in archive/ "
                f"(files: {[f.name for f in archive_files]})"
            )
            results.append(("1.6", True, "anna's file present in archive/"))
        except Exception as exc:
            results.append(("1.6", False, str(exc)))

        _reset_db()

    return results


# ===================================================================
# Case 2 — 0606 Inconsistency: Active Constraint + Gate + Re-injection
# ===================================================================

def _run_case2(tmp_dir: Path) -> list[tuple[str, bool, str]]:
    """Execute all Case 2 verification points."""
    results: list[tuple[str, bool, str]] = []
    os.environ["EDUFLOW_OBSIDIAN_ROOT"] = str(tmp_dir)

    with isolated_env():
        _init_db()

        from eduflow.memory.items import add_memory, list_memories
        from eduflow.memory.constraints import (
            add_constraint,
            get_constraint,
            query_for_agent,
        )
        from eduflow.memory.capsules import upsert_capsule, get_capsule
        from eduflow.memory.packet import assemble_memory_packet
        from eduflow.memory.obsidian_export import export_all

        # ── 2.1 — add workflow constraint (L1 / gate_required) ──
        try:
            cid = add_constraint(
                scope="workflow:igcse-subject-launch",
                level="L1",
                constraint_type="gate_check",
                content="items/QQL/manifest must be consistent before closeout",
                enforcement="gate_required",
                source_ref="task:T-29",
            )
            assert cid.startswith("AC-"), f"bad constraint id: {cid}"
            c = get_constraint(cid)
            assert c is not None, "constraint not found after insert"
            assert c["enforcement"] == "gate_required"
            assert c["scope"] == "workflow:igcse-subject-launch"
            assert c["constraint_level"] == "L1"
            results.append(("2.1", True, f"constraint {cid} added"))
        except Exception as exc:
            results.append(("2.1", False, str(exc)))

        # ── 2.2 — query_for_agent finds workflow-scope constraint ──
        try:
            qr = query_for_agent("worker_course", task_id="T-29")
            matching = [
                c for c in qr
                if c["scope"] == "workflow:igcse-subject-launch"
            ]
            assert len(matching) >= 1, (
                f"workflow constraint not found (got {len(qr)} total)"
            )
            results.append(("2.2", True, "workflow constraint visible"))
        except Exception as exc:
            results.append(("2.2", False, str(exc)))

        # ── 2.3 — task scope: different task_id → not found ──
        try:
            add_constraint(
                scope="task:T-29",
                level="L2",
                constraint_type="evidence_rule",
                content="T-29 requires items/QQL/manifest triple check",
                enforcement="gate_required",
            )
            wrong = query_for_agent("worker_course", task_id="T-99")
            t29_wrong = [c for c in wrong if c["scope"] == "task:T-29"]
            assert len(t29_wrong) == 0, (
                f"task scope LEAK: T-29 constraint visible for T-99"
            )
            right = query_for_agent("worker_course", task_id="T-29")
            t29_right = [c for c in right if c["scope"] == "task:T-29"]
            assert len(t29_right) >= 1, (
                "task constraint missing for correct task_id"
            )
            results.append(("2.3", True, "task scope isolation verified"))
        except Exception as exc:
            results.append(("2.3", False, str(exc)))

        # ── 2.4 — confirmed memory at workflow scope ──
        try:
            mid = add_memory(
                scope="workflow:igcse-subject-launch",
                kind="decision",
                content="0606 closeout requires triple consistency check",
                layer="decision",
                status="confirmed",
                importance=9,
                source_ref="task:T-29",
            )
            assert mid.startswith("MI-"), f"bad memory id: {mid}"
            wmem = list_memories(
                scope="workflow:igcse-subject-launch", status="confirmed",
            )
            assert len(wmem) >= 1
            results.append(("2.4", True, f"memory {mid} added"))
        except Exception as exc:
            results.append(("2.4", False, str(exc)))

        # ── 2.5 — packet contains constraint + agent-scope memory ──
        # Note: _render_memories only pulls memories at the agent's
        # resolved scope (agent:worker_course). Workflow-scope memories
        # are stored but not rendered into other agents' packets —
        # this IS the scope isolation we want to verify.
        try:
            # Add an agent-scope memory so it shows up in worker_course's packet
            worker_mid = add_memory(
                scope="agent:worker_course",
                kind="note",
                content="worker_course: always verify items/QQL/manifest triple",
                layer="episode",
                status="confirmed",
                importance=8,
            )
            pkt = assemble_memory_packet(
                "worker_course", task_id="T-29",
            )
            assert "items/QQL/manifest" in pkt, (
                "constraint content missing from packet"
            )
            assert "gate_required" in pkt, (
                "gate_required enforcement label missing"
            )
            assert "verify items/QQL/manifest triple" in pkt, (
                "agent-scope memory content missing from packet"
            )
            # Confirm workflow-scope memory is NOT leaked into the packet
            assert "triple consistency check" not in pkt, (
                "workflow-scope memory leaked into agent packet (scope bypass)"
            )
            results.append(("2.5", True, "packet has constraint + agent memory"))
        except Exception as exc:
            results.append(("2.5", False, str(exc)))

        # ── 2.6 — capsule in packet ──
        try:
            upsert_capsule(
                "T-29",
                workflow_id="igcse-subject-launch",
                owner="worker_course",
                gate="review_pending",
                goal="Produce 0606 Biology items with consistency",
                next_action="awaiting_review",
                acceptance="items/QQL/manifest triple match",
            )
            cap = get_capsule("T-29")
            assert cap is not None, "capsule not found"
            assert cap["workflow_id"] == "igcse-subject-launch"
            pkt2 = assemble_memory_packet(
                "worker_course", task_id="T-29",
            )
            assert "T-29" in pkt2, "capsule task_id missing from packet"
            assert "worker_course" in pkt2, "capsule owner missing from packet"
            results.append(("2.6", True, "capsule present in packet"))
        except Exception as exc:
            results.append(("2.6", False, str(exc)))

        # ── 2.7 — Obsidian export: active-constraints.md ──
        try:
            export_all()
            ac_file = tmp_dir / "_memory-exports" / "active-constraints.md"
            assert ac_file.exists(), "active-constraints.md not created"
            ac_text = ac_file.read_text()
            assert (
                "items/QQL/manifest must be consistent before closeout"
                in ac_text
            ), "constraint content missing from active-constraints.md"
            assert "gate_required" in ac_text
            results.append(("2.7", True, "active-constraints.md has content"))
        except Exception as exc:
            results.append(("2.7", False, str(exc)))

        # ── 2.8 — Obsidian export: memory item .md file ──
        try:
            item_file = tmp_dir / "_memory-exports" / "decisions" / f"{mid}.md"
            assert item_file.exists(), (
                f"memory item file not found at {item_file}"
            )
            item_text = item_file.read_text()
            assert "triple consistency check" in item_text
            results.append(("2.8", True, "memory item .md exported"))
        except Exception as exc:
            results.append(("2.8", False, str(exc)))

        # ── 2.9 — reidentify: re-assembled packet still has constraint ──
        try:
            pkt3 = assemble_memory_packet(
                "worker_course", task_id="T-29",
            )
            assert "items/QQL/manifest" in pkt3, (
                "constraint not re-injected after reidentify"
            )
            assert "gate_required" in pkt3
            results.append(("2.9", True, "constraint re-injected on reidentify"))
        except Exception as exc:
            results.append(("2.9", False, str(exc)))

        # ── 2.10 — Package 3: FAIL verdict, gate_required persists ──
        try:
            upsert_capsule(
                "T-29",
                workflow_id="igcse-subject-launch",
                owner="worker_course",
                gate="verdict:fail",
                current_status="FAIL — items/QQL/manifest inconsistent",
                blockers=["Resolve consistency before closeout"],
            )
            cap2 = get_capsule("T-29")
            assert cap2 is not None
            assert "FAIL" in (cap2.get("current_status") or "")
            pkt4 = assemble_memory_packet(
                "worker_course", task_id="T-29",
            )
            assert "gate_required" in pkt4, (
                "gate_required lost after FAIL verdict (Package 3 regression)"
            )
            assert "items/QQL/manifest" in pkt4, (
                "constraint content lost after FAIL verdict"
            )
            results.append((
                "2.10", True,
                "gate_required persists despite FAIL verdict",
            ))
        except Exception as exc:
            results.append(("2.10", False, str(exc)))

        _reset_db()

    return results


# ===================================================================
# Standalone runner
# ===================================================================

def _print_report(
    case_name: str,
    results: list[tuple[str, bool, str]],
) -> int:
    """Print per-point PASS/FAIL and return the failure count."""
    failures = 0
    print(f"\n{'=' * 64}")
    print(f"  {case_name}")
    print(f"{'=' * 64}")
    for point_id, passed, detail in results:
        tag = "PASS" if passed else "FAIL"
        if not passed:
            failures += 1
        print(f"  [{tag}]  {point_id}  {detail}")
    return failures


def main() -> int:
    """Run both cases and print a standalone PASS/FAIL report."""
    total_failures = 0
    total_points = 0

    # ── Case 1 ──
    with tempfile.TemporaryDirectory(prefix="verify_case1_") as td:
        try:
            case1 = _run_case1(Path(td))
        except Exception as exc:
            print(f"\nCase 1 FATAL: {exc}")
            case1 = [
                (f"1.{i}", False, "case crashed") for i in range(1, 7)
            ]
        total_failures += _print_report(
            "Case 1: Anna Fire — Agent Memory Isolation (6 checks)",
            case1,
        )
        total_points += len(case1)

    # ── Case 2 ──
    with tempfile.TemporaryDirectory(prefix="verify_case2_") as td:
        try:
            case2 = _run_case2(Path(td))
        except Exception as exc:
            print(f"\nCase 2 FATAL: {exc}")
            case2 = [
                (f"2.{i}", False, "case crashed") for i in range(1, 11)
            ]
        total_failures += _print_report(
            "Case 2: 0606 Inconsistency — Constraint + Gate + Re-injection"
            " (10 checks)",
            case2,
        )
        total_points += len(case2)

    # ── Summary ──
    passed = total_points - total_failures
    print(f"\n{'=' * 64}")
    verdict = "ALL PASS" if total_failures == 0 else f"{total_failures} FAIL"
    print(f"  Result: {verdict}  ({passed}/{total_points} passed)")
    print(f"{'=' * 64}\n")
    return 1 if total_failures else 0


# ===================================================================
# pytest interface
# ===================================================================

class TestCase1AnnaFire:
    """Case 1 — Anna Fire: departed agent memory isolation."""

    def test_full_case(self, tmp_path):
        results = _run_case1(tmp_path)
        failures = [
            f"  {pid}: {detail}"
            for pid, ok, detail in results if not ok
        ]
        assert not failures, (
            f"{len(failures)} check(s) failed:\n" + "\n".join(failures)
        )


class TestCase20606Inconsistency:
    """Case 2 — 0606: Active Constraint + Gate + Re-injection."""

    def test_full_case(self, tmp_path):
        results = _run_case2(tmp_path)
        failures = [
            f"  {pid}: {detail}"
            for pid, ok, detail in results if not ok
        ]
        assert not failures, (
            f"{len(failures)} check(s) failed:\n" + "\n".join(failures)
        )


# ===================================================================
# Entry point — `python3 scripts/verify_memory_cases.py`
# ===================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--pytest":
        sys.exit(pytest.main([__file__, "-v"]))
    sys.exit(main())
