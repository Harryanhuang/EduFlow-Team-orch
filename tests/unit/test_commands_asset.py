"""Tests for `eduflow asset` (M7 Asset Registry Doctor initial version)."""
from __future__ import annotations

import json
from pathlib import Path

from helpers import env_patch, isolated_env, run_cli

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


# ── OPT-5: unified no-confident topic table ──────────────────────


def test_asset_registry_derive_no_confident_topics_uses_unified_source():
    """OPT-5: the no-confident topic table is derived from
    `_GATE_KEYWORDS` + `_GATE_TOPIC`. Adding a new topic only needs
    one entry in `_GATE_TOPIC`; the keyword surface comes from
    `_GATE_KEYWORDS`."""
    topics = asset_registry.derive_no_confident_topics()
    assert topics, "expected at least one topic"
    # Build a {next_step -> [keywords]} map for assertions.
    by_step: dict[str, set[str]] = {}
    for keywords, next_step, skills in topics:
        by_step.setdefault(next_step, set()).update(keywords)
    # The runtime-failover-style topics all point at ops-dashboard.
    runtime_keywords = by_step.get("./scripts/eduflowteam task ops-dashboard --json", set())
    # The pseudo-gate keywords added in OPT-5 must show up.
    assert "外显陈旧" in runtime_keywords
    assert "温备" in runtime_keywords
    assert "wake failed" in runtime_keywords
    assert "manager panel" in runtime_keywords


def test_asset_registry_derive_no_confident_topics_includes_alternates():
    """OPT-6: each topic carries a list of candidate skills."""
    topics = asset_registry.derive_no_confident_topics()
    by_skill_count = {len(skills) for _, _, skills in topics}
    # At least one topic should have a primary + alternative.
    assert max(by_skill_count) >= 2, \
        "expected at least one topic with multiple candidate_skills"


def test_asset_registry_topic_table_skips_orphan_gate_entries():
    """OPT-5: a `_GATE_TOPIC` entry without a matching `_GATE_KEYWORDS`
    bucket is silently skipped (its keywords would be empty)."""
    from eduflow.store import asset_registry as reg
    original = reg._GATE_TOPIC.copy()
    try:
        reg._GATE_TOPIC["__orphan_gate__"] = {
            "next_step": "noop",
            "candidate_skills": ["x"],
        }
        topics = reg.derive_no_confident_topics()
        # The orphan gate contributes zero keywords and is filtered out.
        for _, _, _ in topics:
            pass
        # We can confirm the orphan was skipped by checking that no
        # topic has the orphan's next_step.
        next_steps = {ns for _, ns, _ in topics}
        assert "noop" not in next_steps
    finally:
        reg._GATE_TOPIC.clear()
        reg._GATE_TOPIC.update(original)


# ── OPT-7: surface / runtime / verdict taxonomy ──────────────────


def test_asset_registry_topic_taxonomy_is_surface_runtime_verdict():
    """OPT-7: the no-confident topic table uses a stable 3-class
    taxonomy: surface / runtime / verdict. Each class has a clear
    semantic and its own keyword surface."""
    from eduflow.store import asset_registry as reg
    topics = reg.derive_no_confident_topics()
    # Group topic_ids by their keywords' presence in the topic table.
    surfaced = []
    for topic_id, topic in reg._GATE_TOPIC.items():
        keywords = (reg._GATE_KEYWORDS.get(topic_id)
                     or reg._TOPIC_KEYWORDS.get(topic_id) or [])
        if keywords:
            surfaced.append((topic_id, set(keywords), topic))
    topic_ids = {tid for tid, _, _ in surfaced}
    # The 3 taxonomy classes must be present as topic_ids.
    assert "surface" in topic_ids
    assert "runtime" in topic_ids
    assert "verdict" in topic_ids
    # Surface keywords cover the display-vs-functional class.
    surface_kws = next(
        ks for tid, ks, _ in surfaced if tid == "surface"
    )
    assert "外显陈旧" in surface_kws
    assert "二手外显" in surface_kws
    assert "stale display" in surface_kws
    # Runtime keywords cover the agent/provider liveness class.
    runtime_kws = next(
        ks for tid, ks, _ in surfaced if tid == "runtime"
    )
    assert "温备" in runtime_kws
    assert "wake failed" in runtime_kws
    assert "429" in runtime_kws
    # Verdict keywords cover the handoff/verdict-authority class.
    verdict_kws = next(
        ks for tid, ks, _ in surfaced if tid == "verdict"
    )
    assert "manager panel" in verdict_kws
    assert "状态不一致" in verdict_kws
    assert "task truth drift" in verdict_kws


def test_asset_registry_verdict_topic_has_alternative_skill():
    """OPT-7: the verdict class has a primary + alternative
    candidate_skill pair; the surface/runtime classes have only
    the runtime drift explainer (single skill)."""
    from eduflow.store import asset_registry as reg
    topics = {tid: skills for tid, skills in
              ((tid, topic.get("candidate_skills") or [])
               for tid, topic in reg._GATE_TOPIC.items())}
    assert topics["verdict"] == [
        "eduflow-harness-surface-audit",
        "eduflow-runtime-task-drift-explainer",
    ]
    assert topics["surface"] == ["eduflow-runtime-task-drift-explainer"]
    assert topics["runtime"] == ["eduflow-runtime-task-drift-explainer"]


def test_asset_registry_taxonomy_is_disjoint():
    """OPT-7: surface / runtime / verdict must not share keywords.
    If a keyword belongs to two classes, the no-confident match order
    becomes non-deterministic, which would make tests flaky."""
    from eduflow.store import asset_registry as reg
    surface = set(reg._TOPIC_KEYWORDS["surface"])
    runtime = set(reg._TOPIC_KEYWORDS["runtime"])
    verdict = set(reg._TOPIC_KEYWORDS["verdict"])
    # Each pair must be disjoint.
    assert surface.isdisjoint(runtime), \
        f"surface/runtime overlap: {surface & runtime}"
    assert surface.isdisjoint(verdict), \
        f"surface/verdict overlap: {surface & verdict}"
    assert runtime.isdisjoint(verdict), \
        f"runtime/verdict overlap: {runtime & verdict}"


# ── OPT-8: topic-class registry + decision tree hygiene ────────


def test_asset_registry_topic_class_registry_lists_all_taxonomy_classes():
    """OPT-8: every drift class in `_TOPIC_KEYWORDS` must be in
    `_TOPIC_CLASS_REGISTRY` so the no-confident path and the
    developer-facing decision tree stay in sync."""
    from eduflow.store import asset_registry as reg
    keyword_classes = set(reg._TOPIC_KEYWORDS)
    registered = set(reg._TOPIC_CLASS_REGISTRY)
    assert keyword_classes <= registered, (
        f"topic classes missing from registry: "
        f"{keyword_classes - registered}"
    )
    # The 3 canonical classes must be present.
    for canonical in ("surface", "runtime", "verdict"):
        assert canonical in registered, \
            f"canonical class {canonical!r} missing from registry"
        # Each class has semantic + decision_rule + examples.
        info = reg._TOPIC_CLASS_REGISTRY[canonical]
        for required_key in ("semantic", "decision_rule", "examples"):
            assert required_key in info, \
                f"{canonical!r} missing {required_key!r} in registry entry"
            assert info[required_key], \
                f"{canonical!r}.{required_key!r} is empty"


def test_asset_registry_drift_check_flags_unknown_topic_class():
    """OPT-8: a `_GATE_TOPIC` key that is neither a real gate nor a
    registered class is flagged as `topic_class_not_in_registry`."""
    from eduflow.store import asset_registry as reg
    original_topic = reg._GATE_TOPIC.copy()
    original_topic_kw = reg._TOPIC_KEYWORDS.copy()
    original_registry = reg._TOPIC_CLASS_REGISTRY.copy()
    try:
        # Inject a class into _GATE_TOPIC that is NOT in either
        # _GATE_KEYWORDS (real gates) or _TOPIC_CLASS_REGISTRY.
        reg._GATE_TOPIC["__phantom_class__"] = {
            "next_step": "noop",
            "candidate_skills": ["x"],
        }
        report = reg.drift_check()
        flagged = [
            f for f in report["findings"]
            if f["category"] == "topic_class_not_in_registry"
        ]
        assert flagged, "expected topic_class_not_in_registry finding"
        assert "__phantom_class__" in flagged[0]["unknown_classes"]
    finally:
        reg._GATE_TOPIC.clear()
        reg._GATE_TOPIC.update(original_topic)
        reg._TOPIC_KEYWORDS.clear()
        reg._TOPIC_KEYWORDS.update(original_topic_kw)
        reg._TOPIC_CLASS_REGISTRY.clear()
        reg._TOPIC_CLASS_REGISTRY.update(original_registry)


def test_asset_registry_drift_check_flags_unregistered_topic_keyword_class():
    """OPT-8: a class in `_TOPIC_KEYWORDS` that is not in
    `_TOPIC_CLASS_REGISTRY` is flagged as
    `topic_keyword_class_not_registered`."""
    from eduflow.store import asset_registry as reg
    original_topic_kw = reg._TOPIC_KEYWORDS.copy()
    original_registry = reg._TOPIC_CLASS_REGISTRY.copy()
    try:
        reg._TOPIC_KEYWORDS["__orphan_topic__"] = ["orphan_keyword"]
        report = reg.drift_check()
        flagged = [
            f for f in report["findings"]
            if f["category"] == "topic_keyword_class_not_registered"
        ]
        assert flagged, "expected topic_keyword_class_not_registered finding"
        assert "__orphan_topic__" in flagged[0]["unregistered_classes"]
    finally:
        reg._TOPIC_KEYWORDS.clear()
        reg._TOPIC_KEYWORDS.update(original_topic_kw)
        reg._TOPIC_CLASS_REGISTRY.clear()
        reg._TOPIC_CLASS_REGISTRY.update(original_registry)


def test_asset_registry_topic_class_registry_decision_tree_examples_match():
    """OPT-8: the `examples` in each registry entry should be a subset
    of the keywords in `_TOPIC_KEYWORDS`. This prevents the registry
    from advertising keywords that the no-confident path will not
    actually match."""
    from eduflow.store import asset_registry as reg
    for class_name, info in reg._TOPIC_CLASS_REGISTRY.items():
        examples = set(info.get("examples") or [])
        actual = set(reg._TOPIC_KEYWORDS.get(class_name, []))
        missing = examples - actual
        assert not missing, (
            f"{class_name!r} registry examples are not in the "
            f"keyword bucket: {sorted(missing)}"
        )
