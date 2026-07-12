"""Tests for EduFlow Memory Obsidian Export.

Covers:
- export_all creates correct directory structure
- export_all produces correct markdown files with frontmatter
- export_status returns correct metadata
- export handles empty DB gracefully
- export handles deprecated items (moves to archive/)
- export cleans up stale files
- --scope and --task filters work
- export failure does not crash core memory operations
"""
from __future__ import annotations

import os
import sys
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


# ── Empty DB export ────────────────────────────────────────────────

def test_export_empty_db_creates_structure(tmp_path):
    """export_all on empty DB should create all directories and empty index files."""
    with isolated_env() as env:
        os.environ["EDUFLOW_OBSIDIAN_ROOT"] = str(tmp_path)
        _init_db()

        from eduflow.memory.obsidian_export import export_all, export_root
        counts = export_all()

        assert counts["constraints"] == 0
        assert counts["capsules"] == 0
        assert counts["items"] == 0

        root = export_root()
        assert (root / "index.md").exists()
        assert (root / "active-constraints.md").exists()
        assert (root / "task-capsules.md").exists()
        assert (root / "core-blocks.md").exists()
        assert (root / "decisions").is_dir()
        assert (root / "mistakes").is_dir()
        assert (root / "handoffs").is_dir()
        assert (root / "archive").is_dir()
        _reset_db()


# ── Export with data ──────────────────────────────────────────────

def test_export_active_constraints(tmp_path):
    """Active constraints should appear in active-constraints.md."""
    with isolated_env() as env:
        os.environ["EDUFLOW_OBSIDIAN_ROOT"] = str(tmp_path)
        _init_db()

        from eduflow.memory.constraints import add_constraint
        from eduflow.memory.obsidian_export import export_all

        cid = add_constraint(
            scope="team", level="L0", constraint_type="must_follow",
            content="manager is the only dispatch point",
            source_ref="team-rule:2026",
            enforcement="gate_required",
        )

        counts = export_all()
        assert counts["constraints"] == 1

        ac_text = (tmp_path / "_memory-exports" / "active-constraints.md").read_text()
        assert "manager is the only dispatch point" in ac_text
        assert "L0" in ac_text
        assert "gate_required" in ac_text
        _reset_db()


def test_export_confirmed_memory_items(tmp_path):
    """Confirmed memory items should appear in decisions/ as individual files."""
    with isolated_env() as env:
        os.environ["EDUFLOW_OBSIDIAN_ROOT"] = str(tmp_path)
        _init_db()

        from eduflow.memory.items import add_memory
        from eduflow.memory.obsidian_export import export_all

        mid = add_memory(
            scope="workflow:igcse-subject-launch",
            kind="workflow_rule",
            content="closeout requires items/QQL/manifest consistency",
            layer="decision",
            status="confirmed",
            importance=9,
            source_ref="task:T-29",
        )

        counts = export_all()
        assert counts["items"] == 1

        item_file = tmp_path / "_memory-exports" / "decisions" / f"{mid}.md"
        assert item_file.exists()
        text = item_file.read_text()
        assert f"memory_id: '{mid}'" in text
        assert "workflow_rule" in text
        assert "closeout requires items/QQL/manifest consistency" in text
        assert "task:T-29" in text
        _reset_db()


def test_export_mistake_kind(tmp_path):
    """Mistake-type memories should go to mistakes/ directory."""
    with isolated_env() as env:
        os.environ["EDUFLOW_OBSIDIAN_ROOT"] = str(tmp_path)
        _init_db()

        from eduflow.memory.items import add_memory
        from eduflow.memory.obsidian_export import export_all

        mid = add_memory(
            scope="team",
            kind="mistake",
            content="manager once confused durable memory with workflow state",
            layer="decision",
            status="confirmed",
            importance=7,
        )

        counts = export_all()
        assert counts["items"] == 1

        item_file = tmp_path / "_memory-exports" / "mistakes" / f"{mid}.md"
        assert item_file.exists()
        _reset_db()


def test_export_handoff_kind(tmp_path):
    """Handoff-type memories should go to handoffs/ directory."""
    with isolated_env() as env:
        os.environ["EDUFLOW_OBSIDIAN_ROOT"] = str(tmp_path)
        _init_db()

        from eduflow.memory.items import add_memory
        from eduflow.memory.obsidian_export import export_all

        mid = add_memory(
            scope="lane:course_caie",
            kind="handoff",
            content="course_caie hands off to review_caie after production",
            layer="decision",
            status="confirmed",
        )

        counts = export_all()
        assert counts["items"] == 1

        item_file = tmp_path / "_memory-exports" / "handoffs" / f"{mid}.md"
        assert item_file.exists()
        _reset_db()


def test_export_deprecated_to_archive(tmp_path):
    """Deprecated memories should go to archive/ directory."""
    with isolated_env() as env:
        os.environ["EDUFLOW_OBSIDIAN_ROOT"] = str(tmp_path)
        _init_db()

        from eduflow.memory.items import add_memory
        from eduflow.memory.obsidian_export import export_all

        mid = add_memory(
            scope="team",
            kind="workflow_rule",
            content="old rule that is no longer valid",
            layer="decision",
            status="deprecated",
        )

        counts = export_all()
        assert counts["archive"] == 1
        assert counts["items"] == 0  # not in active items

        archive_file = tmp_path / "_memory-exports" / "archive" / f"{mid}.md"
        assert archive_file.exists()
        # Should NOT be in decisions/
        assert not (tmp_path / "_memory-exports" / "decisions" / f"{mid}.md").exists()
        _reset_db()


def test_export_cleans_stale_files(tmp_path):
    """Re-exporting should remove files that no longer exist in DB."""
    with isolated_env() as env:
        os.environ["EDUFLOW_OBSIDIAN_ROOT"] = str(tmp_path)
        _init_db()

        from eduflow.memory.items import add_memory
        from eduflow.memory.obsidian_export import export_all

        mid = add_memory(
            scope="team", kind="workflow_rule",
            content="temporary rule", layer="decision", status="confirmed",
        )

        counts1 = export_all()
        assert counts1["items"] == 1
        item_file = tmp_path / "_memory-exports" / "decisions" / f"{mid}.md"
        assert item_file.exists()

        # Deprecate it
        from eduflow.memory.items import deprecate_memory
        deprecate_memory(mid)

        # Re-export
        counts2 = export_all()
        assert counts2["items"] == 0
        assert counts2["archive"] == 1
        # File should no longer be in decisions/
        assert not item_file.exists()
        # But should be in archive/
        assert (tmp_path / "_memory-exports" / "archive" / f"{mid}.md").exists()
        _reset_db()


def test_export_task_capsules(tmp_path):
    """Task capsules should appear in task-capsules.md."""
    with isolated_env() as env:
        os.environ["EDUFLOW_OBSIDIAN_ROOT"] = str(tmp_path)
        _init_db()

        from eduflow.memory.capsules import upsert_capsule
        from eduflow.memory.obsidian_export import export_all

        upsert_capsule(
            "T-99",
            workflow_id="igcse-subject-launch",
            owner="worker_course",
            gate="review_pending",
            goal="Produce 0606 Biology items",
            next_action="awaiting_review",
        )

        counts = export_all()
        assert counts["capsules"] == 1

        tc_text = (tmp_path / "_memory-exports" / "task-capsules.md").read_text()
        assert "T-99" in tc_text
        assert "worker_course" in tc_text
        assert "review_pending" in tc_text
        _reset_db()


def test_export_status(tmp_path):
    """export_status should return last export time and file counts."""
    with isolated_env() as env:
        os.environ["EDUFLOW_OBSIDIAN_ROOT"] = str(tmp_path)
        _init_db()

        from eduflow.memory.obsidian_export import export_all, export_status

        # Before export
        status = export_status()
        assert status["last_export"] == ""

        # After export
        export_all()
        status = export_status()
        assert status["last_export"] != ""
        assert "root" in status["file_counts"]
        _reset_db()


def test_export_scope_filter(tmp_path):
    """export_all with scope filter should only export matching items."""
    with isolated_env() as env:
        os.environ["EDUFLOW_OBSIDIAN_ROOT"] = str(tmp_path)
        _init_db()

        from eduflow.memory.items import add_memory
        from eduflow.memory.obsidian_export import export_all

        add_memory(
            scope="team", kind="workflow_rule",
            content="team rule", layer="decision", status="confirmed",
        )
        add_memory(
            scope="lane:course_caie", kind="workflow_rule",
            content="lane rule", layer="decision", status="confirmed",
        )

        # Export only team scope
        counts = export_all(scope="team")
        assert counts["items"] == 1
        _reset_db()


def test_export_does_not_crash_on_db_error(tmp_path, monkeypatch):
    """Export failure should not crash core memory operations."""
    with isolated_env() as env:
        os.environ["EDUFLOW_OBSIDIAN_ROOT"] = str(tmp_path)
        _init_db()

        from eduflow.memory.items import add_memory
        from eduflow.memory import obsidian_export

        # Add a memory first — should work
        mid = add_memory(
            scope="team", kind="workflow_rule",
            content="test rule", layer="decision", status="confirmed",
        )
        assert mid.startswith("MI-")

        # Make export_root raise — export should fail but memory should still work
        original_root = obsidian_export.export_root
        def bad_root():
            raise RuntimeError("simulated failure")
        obsidian_export.export_root = bad_root

        with pytest.raises(RuntimeError):
            obsidian_export.export_all()

        # Restore and verify memory still works
        obsidian_export.export_root = original_root
        mid2 = add_memory(
            scope="team", kind="mistake",
            content="another rule", layer="decision", status="confirmed",
        )
        assert mid2.startswith("MI-")
        _reset_db()


# ── CLI tests ─────────────────────────────────────────────────────

def test_cli_export_all(tmp_path):
    """CLI export command should produce files and print summary."""
    with isolated_env() as env:
        os.environ["EDUFLOW_OBSIDIAN_ROOT"] = str(tmp_path)
        _init_db()

        from eduflow.commands.memory_cli import _cmd_export

        # Capture stdout
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = _cmd_export([])

        assert rc == 0
        output = buf.getvalue()
        assert "Export complete" in output
        _reset_db()


def test_cli_export_status(tmp_path):
    """CLI export status should print status."""
    with isolated_env() as env:
        os.environ["EDUFLOW_OBSIDIAN_ROOT"] = str(tmp_path)
        _init_db()

        from eduflow.memory.obsidian_export import export_all
        from eduflow.commands.memory_cli import _cmd_export

        export_all()  # create initial export

        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = _cmd_export(["status"])

        assert rc == 0
        output = buf.getvalue()
        assert "Last export:" in output
        _reset_db()
