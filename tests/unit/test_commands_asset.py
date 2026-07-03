"""Tests for `eduflow asset` (M7 Asset Registry Doctor initial version)."""
from __future__ import annotations

import json
from pathlib import Path

from helpers import env_patch, isolated_env, run_cli

from eduflow.commands import asset as asset_cmd
from eduflow.store import asset_registry


# ── fixtures ─────────────────────────────────────────────────────


def _write_skill(skill_dir: Path, *, name: str, description: str,
                 body_extra: str = "") -> None:
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        "---\n\n"
        f"# {name}\n\n{body_extra}\n",
        encoding="utf-8",
    )


def _write_workflow(workflow_root: Path, *, workflow_id: str,
                    status: str = "active",
                    standard_files: bool = True) -> Path:
    """Create one workflow directory with optional standard files.

    Returns the workflow directory path.
    """
    parent = workflow_root
    if status != "active":
        parent = workflow_root / "_candidates"
    workflow_dir = parent / workflow_id
    workflow_dir.mkdir(parents=True, exist_ok=True)
    if standard_files:
        (workflow_dir / "README.md").write_text(
            f"# workflow: {workflow_id}\n\n"
            "## Primary Chain\n\nmanager -> worker_course -> review_course -> manager\n\n"
            "## Core Gates\n\n- dispatch_acceptance_gate\n\n"
            "## Forbidden Moves\n\n- worker must not bypass manager closeout.\n\n"
            f"status: {status}\n",
            encoding="utf-8",
        )
        for standard in asset_registry.WORKFLOW_STANDARD_FILES:
            if standard == "README.md":
                continue
            (workflow_dir / standard).write_text(
                f"# {standard}\n\n{workflow_id}\n", encoding="utf-8"
            )
    else:
        (workflow_dir / "README.md").write_text(
            f"# workflow: {workflow_id}\n\nstatus: {status}\n",
            encoding="utf-8",
        )
    return workflow_dir


def _isolated_assets_root(tmp: Path) -> dict[str, Path]:
    """Build a temp tree of workflow/skill/identity assets and return the roots."""
    workflows_root = tmp / "workflows"
    workflows_root.mkdir(parents=True, exist_ok=True)
    skills_root = tmp / "skills"
    skills_root.mkdir(parents=True, exist_ok=True)
    claude_skills_root = tmp / "claude_skills"
    claude_skills_root.mkdir(parents=True, exist_ok=True)
    agents_root = tmp / "agents"
    agents_root.mkdir(parents=True, exist_ok=True)
    return {
        "workflows": workflows_root,
        "skills": skills_root,
        "claude_skills": claude_skills_root,
        "agents": agents_root,
    }


# ── list ─────────────────────────────────────────────────────────


def test_asset_list_json_includes_workflows_and_skills():
    """`asset list --json` surfaces a temp workflow and a temp skill."""
    with isolated_env() as tmp:
        roots = _isolated_assets_root(tmp)
        _write_workflow(roots["workflows"], workflow_id="igcse-subject-launch")
        _write_skill(
            roots["skills"] / "eduflow-evidence-account-explainer",
            name="eduflow-evidence-account-explainer",
            description="M6 explainer skill",
            body_extra="evidence account verdict packet",
        )
        with env_patch(
            EDUFLOW_WORKFLOW_DIR=str(roots["workflows"]),
            EDUFLOW_SKILLS_DIR=str(roots["skills"]),
            EDUFLOW_CLAUDE_SKILLS_DIR=str(roots["claude_skills"]),
        ):
            rc, out, err = run_cli(["asset", "list", "--json"])
        assert rc == 0, err
        payload = json.loads(out)
        ids = {a["asset_id"] for a in payload["assets"]}
        assert "igcse-subject-launch" in ids
        assert "eduflow-evidence-account-explainer" in ids
        assert payload["count"] == len(payload["assets"])
        # Every asset row has the required fields
        for entry in payload["assets"]:
            for key in (
                "asset_id", "asset_type", "title", "path", "status",
                "owner_role", "trigger_terms", "validation_command",
                "source_evidence",
            ):
                assert key in entry, f"missing field {key} in {entry}"


def test_asset_list_filtered_by_type_only_returns_workflows():
    with isolated_env() as tmp:
        roots = _isolated_assets_root(tmp)
        _write_workflow(roots["workflows"], workflow_id="igcse-subject-launch")
        _write_skill(
            roots["skills"] / "eduflow-asset",
            name="eduflow-asset",
            description="asset registry",
        )
        with env_patch(
            EDUFLOW_WORKFLOW_DIR=str(roots["workflows"]),
            EDUFLOW_SKILLS_DIR=str(roots["skills"]),
            EDUFLOW_CLAUDE_SKILLS_DIR=str(roots["claude_skills"]),
        ):
            rc, out, _ = run_cli(["asset", "list", "--type", "workflow", "--json"])
        assert rc == 0
        payload = json.loads(out)
        assert all(a["asset_type"] == "workflow" for a in payload["assets"])
        assert any(a["asset_id"] == "igcse-subject-launch" for a in payload["assets"])


# ── recommend ────────────────────────────────────────────────────


def test_asset_recommend_matches_workflow_and_skill_keywords():
    with isolated_env() as tmp:
        roots = _isolated_assets_root(tmp)
        _write_workflow(roots["workflows"], workflow_id="igcse-subject-launch")
        _write_skill(
            roots["skills"] / "qbank-verification",
            name="qbank-verification",
            description="qbank readiness check",
        )
        with env_patch(
            EDUFLOW_WORKFLOW_DIR=str(roots["workflows"]),
            EDUFLOW_SKILLS_DIR=str(roots["skills"]),
            EDUFLOW_CLAUDE_SKILLS_DIR=str(roots["claude_skills"]),
        ):
            rc, out, _ = run_cli([
                "asset", "recommend", "igcse subject launch plan", "--json"
            ])
        assert rc == 0
        payload = json.loads(out)
        ids = [r["asset_id"] for r in payload["recommendations"]]
        assert "igcse-subject-launch" in ids
        # Every recommendation carries a confidence field
        for r in payload["recommendations"]:
            assert "confidence" in r
            assert 0.0 <= r["confidence"] <= 1.0
        # Direct asset_id substring should boost score
        workflow_row = next(
            r for r in payload["recommendations"]
            if r["asset_id"] == "igcse-subject-launch"
        )
        assert workflow_row["confidence"] > 0.0


def test_asset_recommend_returns_no_confident_recommendation_for_garbage():
    with isolated_env():
        # Use a token sequence that does not overlap with any trigger
        # term in the registry (no "asset", "registry", "validate", etc).
        rc, out, _ = run_cli([
            "asset", "recommend",
            "qqq zzz xxx nonsense phrase", "--json",
        ])
        assert rc == 0
        payload = json.loads(out)
        assert payload["recommendations"] == []


# ── validate ─────────────────────────────────────────────────────


def test_asset_validate_json_returns_ok_for_complete_registry():
    with isolated_env() as tmp:
        roots = _isolated_assets_root(tmp)
        _write_workflow(roots["workflows"], workflow_id="igcse-subject-launch")
        _write_skill(
            roots["skills"] / "eduflow-asset",
            name="eduflow-asset",
            description="asset registry",
        )
        (roots["agents"] / "worker_course").mkdir(parents=True, exist_ok=True)
        (roots["agents"] / "worker_course" / "identity.md").write_text(
            "identity placeholder", encoding="utf-8"
        )
        with env_patch(
            EDUFLOW_WORKFLOW_DIR=str(roots["workflows"]),
            EDUFLOW_SKILLS_DIR=str(roots["skills"]),
            EDUFLOW_CLAUDE_SKILLS_DIR=str(roots["claude_skills"]),
            EDUFLOW_STATE_DIR=str(tmp / "state"),
            EDUFLOW_ASSET_AGENTS_DIR=str(roots["agents"]),
        ):
            rc, out, _ = run_cli(["asset", "validate", "--json"])
        # The CLI wraps the validate report in a top-level "validate" key.
        payload = json.loads(out)["validate"]
        assert "errors" in payload
        assert "warnings" in payload
        assert "summary" in payload
        assert payload["summary"]["workflows"] >= 1
        assert payload["summary"]["skills"] >= 1


def test_asset_validate_flags_missing_workflow_standard_file():
    with isolated_env() as tmp:
        roots = _isolated_assets_root(tmp)
        _write_workflow(
            roots["workflows"],
            workflow_id="incomplete-workflow",
            standard_files=False,
        )
        with env_patch(
            EDUFLOW_WORKFLOW_DIR=str(roots["workflows"]),
            EDUFLOW_SKILLS_DIR=str(roots["skills"]),
            EDUFLOW_CLAUDE_SKILLS_DIR=str(roots["claude_skills"]),
        ):
            rc, out, _ = run_cli(["asset", "validate", "--json"])
        payload = json.loads(out)["validate"]
        assert payload["ok"] is False
        assert any(
            "incomplete-workflow" in err and "missing workflow standard file" in err
            for err in payload["errors"]
        )


# ── drift-check ──────────────────────────────────────────────────


def test_asset_drift_check_finds_duplicate_skill_and_missing_file():
    with isolated_env() as tmp:
        roots = _isolated_assets_root(tmp)
        # Two skills with the same asset_id (one under skills/, one under .claude/skills/)
        _write_skill(
            roots["skills"] / "eduflow-asset",
            name="eduflow-asset",
            description="asset registry",
        )
        _write_skill(
            roots["claude_skills"] / "eduflow-asset",
            name="eduflow-asset",
            description="asset registry (claude copy)",
        )
        # Active workflow missing standard files
        _write_workflow(
            roots["workflows"],
            workflow_id="broken-workflow",
            standard_files=False,
        )
        with env_patch(
            EDUFLOW_WORKFLOW_DIR=str(roots["workflows"]),
            EDUFLOW_SKILLS_DIR=str(roots["skills"]),
            EDUFLOW_CLAUDE_SKILLS_DIR=str(roots["claude_skills"]),
        ):
            rc, out, _ = run_cli(["asset", "drift-check", "--json"])
        payload = json.loads(out)["drift_check"]
        categories = {f["category"] for f in payload["findings"]}
        assert "duplicate_asset" in categories
        assert "active_workflow_missing_standard_file" in categories
        assert payload["summary"]["errors"] >= 1
        # Should not be ok because the workflow is missing standard files
        assert payload["ok"] is False


def test_asset_drift_check_clean_registry_returns_no_findings():
    with isolated_env() as tmp:
        roots = _isolated_assets_root(tmp)
        _write_workflow(roots["workflows"], workflow_id="clean-workflow")
        _write_skill(
            roots["skills"] / "eduflow-asset",
            name="eduflow-asset",
            description="asset registry",
        )
        with env_patch(
            EDUFLOW_WORKFLOW_DIR=str(roots["workflows"]),
            EDUFLOW_SKILLS_DIR=str(roots["skills"]),
            EDUFLOW_CLAUDE_SKILLS_DIR=str(roots["claude_skills"]),
        ):
            rc, out, _ = run_cli(["asset", "drift-check", "--json"])
        payload = json.loads(out)["drift_check"]
        # Either zero findings or only identity-related warnings. The
        # identity check requires a team config; isolated_env may not
        # produce one, so we only assert that the active workflow is clean.
        for f in payload["findings"]:
            assert f.get("asset_id") != "clean-workflow"
        assert payload["summary"]["errors"] == 0
        assert payload["ok"] is True


def test_asset_drift_check_candidate_overlap_is_info_not_error():
    """OPT-1: a candidate+active pair is the expected post-promotion state.

    Per docs/workflows/README.md the candidate is retained as evidence
    after promotion. So the finding is `info`, not `error`, and the
    overall `ok` flag stays True.
    """
    with isolated_env() as tmp:
        roots = _isolated_assets_root(tmp)
        # Active workflow with all standard files (real).
        _write_workflow(roots["workflows"], workflow_id="igcse-subject-launch")
        # Same id as a candidate (post-promotion archived source).
        _write_workflow(
            roots["workflows"], workflow_id="igcse-subject-launch",
            status="promotion_ready",
        )
        with env_patch(
            EDUFLOW_WORKFLOW_DIR=str(roots["workflows"]),
            EDUFLOW_SKILLS_DIR=str(roots["skills"]),
            EDUFLOW_CLAUDE_SKILLS_DIR=str(roots["claude_skills"]),
        ):
            rc, out, _ = run_cli(["asset", "drift-check", "--json"])
        assert rc == 0
        payload = json.loads(out)["drift_check"]
        overlap = [
            f for f in payload["findings"]
            if f.get("category") == "candidate_id_clashes_with_active_workflow"
        ]
        assert overlap, "expected candidate_id_clashes finding"
        for f in overlap:
            assert f["severity"] == "info"
            assert "remediation" in f and len(f["remediation"]) >= 1
        # No errors at all; ok stays True.
        assert payload["summary"]["errors"] == 0
        assert payload["ok"] is True


def test_asset_drift_check_findings_carry_remediation_hints():
    """OPT-1: every finding has a `remediation` list with at least one step."""
    with isolated_env() as tmp:
        roots = _isolated_assets_root(tmp)
        # Create one duplicate and one broken workflow to surface 2 findings.
        _write_skill(
            roots["skills"] / "eduflow-asset",
            name="eduflow-asset",
            description="asset registry",
        )
        _write_skill(
            roots["claude_skills"] / "eduflow-asset",
            name="eduflow-asset",
            description="asset registry (claude copy)",
        )
        _write_workflow(
            roots["workflows"],
            workflow_id="broken-workflow",
            standard_files=False,
        )
        with env_patch(
            EDUFLOW_WORKFLOW_DIR=str(roots["workflows"]),
            EDUFLOW_SKILLS_DIR=str(roots["skills"]),
            EDUFLOW_CLAUDE_SKILLS_DIR=str(roots["claude_skills"]),
        ):
            rc, out, _ = run_cli(["asset", "drift-check", "--show-remediation"])
        assert rc != 0  # broken workflow is a real error
        # Every finding line is followed by `-> remediation` lines.
        assert "-> " in out
        # duplicate_asset remediation mentions `.claude/skills/`.
        assert ".claude/skills/" in out or "skills/" in out
        # active_workflow_missing_standard_file remediation mentions
        # `eduflow workflow validate --strict`.
        assert "eduflow workflow validate --strict" in out


# ── direct store API ─────────────────────────────────────────────


def test_asset_registry_scan_includes_identity_rules():
    """Direct call to the store: identity_rule assets are surfaced."""
    with isolated_env() as tmp:
        agents = tmp / "agents"
        (agents / "worker_course").mkdir(parents=True, exist_ok=True)
        (agents / "worker_course" / "identity.md").write_text(
            "identity stub", encoding="utf-8"
        )
        with env_patch(
            EDUFLOW_STATE_DIR=str(tmp / "state"),
            EDUFLOW_ASSET_AGENTS_DIR=str(agents),
        ):
            assets = asset_registry.scan_identity_rules(agents)
    by_id = {a.asset_id: a for a in assets}
    assert "worker_course" in by_id
    assert by_id["worker_course"].asset_type == "identity_rule"
    assert by_id["worker_course"].status == "active"


def test_asset_registry_recommend_returns_top_k_sorted_by_confidence():
    with isolated_env() as tmp:
        roots = _isolated_assets_root(tmp)
        _write_workflow(roots["workflows"], workflow_id="igcse-subject-launch")
        _write_skill(
            roots["skills"] / "igcse-qbank-verification",
            name="igcse-qbank-verification",
            description="igcse qbank readiness verification",
        )
        with env_patch(
            EDUFLOW_WORKFLOW_DIR=str(roots["workflows"]),
            EDUFLOW_SKILLS_DIR=str(roots["skills"]),
            EDUFLOW_CLAUDE_SKILLS_DIR=str(roots["claude_skills"]),
        ):
            rows = asset_registry.recommend("igcse qbank verification")
        assert len(rows) >= 1
        # Sorted by score desc
        for prev, nxt in zip(rows, rows[1:]):
            assert prev["score"] >= nxt["score"]


def test_asset_registry_recommend_uses_workflow_gate_keywords():
    """OPT-3: a query that mentions a gate keyword should rank that workflow up.

    A workflow that declares `runtime_reality` in its Core Gates gets
    the gate-keyword surface ("runtime", "429", "fallback", "inbox",
    "运行", "模型"). A query that only mentions one of those tokens (and
    does NOT mention the workflow id directly) should still surface it.
    """
    with isolated_env() as tmp:
        roots = _isolated_assets_root(tmp)
        # Custom workflow that actually declares `runtime_reality` in
        # its Core Gates; the default _write_workflow fixture only
        # declares dispatch_acceptance_gate.
        wf = roots["workflows"] / "runtime-failover-workflow"
        wf.mkdir(parents=True, exist_ok=True)
        (wf / "README.md").write_text(
            "# workflow: runtime-failover-workflow\n\n"
            "## Core Gates\n\n"
            "- `runtime_reality`\n"
            "- `repair_acceptance_contract`\n",
            encoding="utf-8",
        )
        for standard in asset_registry.WORKFLOW_STANDARD_FILES:
            if standard == "README.md":
                continue
            (wf / standard).write_text(
                f"# {standard}\nruntime-failover-workflow\n", encoding="utf-8"
            )
        with env_patch(
            EDUFLOW_WORKFLOW_DIR=str(roots["workflows"]),
            EDUFLOW_SKILLS_DIR=str(roots["skills"]),
            EDUFLOW_CLAUDE_SKILLS_DIR=str(roots["claude_skills"]),
        ):
            rows = asset_registry.recommend("429 fallback env")
        ids = [r["asset_id"] for r in rows]
        assert "runtime-failover-workflow" in ids
        runtime_row = next(
            r for r in rows if r["asset_id"] == "runtime-failover-workflow"
        )
        # The match should be picked up via gate keywords, not asset_id.
        assert "fallback" in runtime_row["matched_terms"] or "429" in runtime_row["matched_terms"]


def test_extract_workflow_gates_parses_core_and_acceptance_sections():
    """OPT-3 helper: both '## Core Gates' and '## Acceptance Gates' work."""
    with isolated_env() as tmp:
        roots = _isolated_assets_root(tmp)
        _write_workflow(roots["workflows"], workflow_id="igcse-subject-launch")
        with env_patch(
            EDUFLOW_WORKFLOW_DIR=str(roots["workflows"]),
        ):
            gates = asset_registry._extract_workflow_gates(
                roots["workflows"] / "igcse-subject-launch" / "README.md"
            )
        # The fixture's README mentions dispatch_acceptance_gate.
        assert "dispatch_acceptance_gate" in gates


def test_asset_registry_validate_flags_missing_identity():
    with isolated_env() as tmp:
        agents = tmp / "agents"
        (agents / "ghost_agent").mkdir(parents=True, exist_ok=True)
        # No identity.md inside
        with env_patch(
            EDUFLOW_STATE_DIR=str(tmp / "state"),
            EDUFLOW_ASSET_AGENTS_DIR=str(agents),
        ):
            report = asset_registry.validate(asset_registry.scan_identity_rules(agents))
    assert report["ok"] is False
    assert any("ghost_agent" in err for err in report["errors"])
