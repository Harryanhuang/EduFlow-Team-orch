"""EduFlow Asset Registry — read-only asset discovery and drift-check.

M7 initial version. This module scans the existing workflow, skill, and
identity assets on disk and exposes a uniform list for the
`eduflow asset` CLI. It does NOT install, copy, or delete any assets.

Asset types in v1:

  - workflow          -> docs/workflows/<id>/README.md
  - skill             -> skills/<id>/SKILL.md or .claude/skills/<id>/SKILL.md
                         (also .claude/skills/<name>.md as a top-level skill)
  - identity_rule     -> .eduflow-team-state/agents/<agent>/identity.md
  - patrol_reference  -> .claude/skills/<name>.md (top-level reference)
  - memory_candidate  -> flow-memory candidate placeholders
  - cli_check         -> built-in `eduflow asset ...` self-check surface
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


VALID_ASSET_TYPES = (
    "workflow",
    "skill",
    "identity_rule",
    "patrol_reference",
    "memory_candidate",
    "cli_check",
)

WORKFLOW_STANDARD_FILES = (
    "README.md",
    "trigger.md",
    "roles.md",
    "checklist.md",
    "handoff-template.md",
)


@dataclass
class Asset:
    """A single read-only asset entry.

    The fields are stable; downstream parsers and tests grep on them.
    Do not silently rename them.
    """

    asset_id: str
    asset_type: str
    title: str
    path: str
    status: str  # active | candidate | draft | stale | unknown
    owner_role: str = ""
    trigger_terms: list[str] = field(default_factory=list)
    validation_command: str = ""
    source_evidence: str = ""
    warnings: list[str] = field(default_factory=list)
    exists: bool = True

    def to_dict(self) -> dict:
        return {
            "asset_id": self.asset_id,
            "asset_type": self.asset_type,
            "title": self.title,
            "path": self.path,
            "status": self.status,
            "owner_role": self.owner_role,
            "trigger_terms": list(self.trigger_terms),
            "validation_command": self.validation_command,
            "source_evidence": self.source_evidence,
            "warnings": list(self.warnings),
            "exists": self.exists,
        }


# ── Path resolvers (overridable via env for tests) ───────────────


def _workflows_root() -> Path:
    override = os.environ.get("EDUFLOW_WORKFLOW_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[3] / "docs" / "workflows"


def _skills_root() -> Path:
    override = os.environ.get("EDUFLOW_SKILLS_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[3] / "skills"


def _claude_skills_root() -> Path:
    override = os.environ.get("EDUFLOW_CLAUDE_SKILLS_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[3] / ".claude" / "skills"


def _agents_root() -> Path:
    override = os.environ.get("EDUFLOW_ASSET_AGENTS_DIR")
    if override:
        return Path(override)
    state_dir = os.environ.get("EDUFLOW_STATE_DIR")
    if state_dir:
        return Path(state_dir) / "agents"
    return Path(__file__).resolve().parents[3] / ".eduflow-team-state" / "agents"


def _memory_candidates_root() -> Path:
    return Path(__file__).resolve().parents[3] / ".omc" / "state" / "candidates"


def _readme_title(readme: Path) -> str:
    try:
        for line in readme.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
    except Exception:
        return ""
    return ""


def _has_skill_name_description(text: str) -> tuple[bool, str, str]:
    """Return (ok, name, description) for a SKILL.md frontmatter.

    Tolerates the simple `name:` / `description:` lines that we use
    everywhere in this repo. Falls back to the first H1 + first
    paragraph when the frontmatter is missing.
    """
    if not text:
        return False, "", ""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        # No frontmatter; try to extract from the H1 + first non-empty paragraph.
        h1 = ""
        paragraph = ""
        for line in lines:
            if not h1 and line.strip().startswith("# "):
                h1 = line.strip()[2:].strip()
                continue
            if h1 and line.strip() and not line.strip().startswith("#"):
                paragraph = line.strip()
                break
        return bool(h1), h1, paragraph[:160]
    name = ""
    description = ""
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if key == "name" and not name:
            name = value
        elif key == "description" and not description:
            description = value
    return bool(name or description), name, description


_TRIGGER_TERM_SPLIT = re.compile(r"[\s,，;；、]+")


# Mirror of `_GATE_KEYWORDS` in `eduflow.commands.workflow`. Kept in
# sync manually because importing from `eduflow.commands` would create
# a circular import surface for future tool builders. Each gate maps
# to the keyword surface that `recommend` should match against free-
# form task text. The list is intentionally small and stable; the
# source of truth is the workflow README `## Core Gates` section.
_GATE_KEYWORDS: dict[str, list[str]] = {
    "dispatch_acceptance_gate": ["dispatch", "accept", "accepted", "接单", "派工"],
    "review_handoff_gate": ["review", "handoff", "reviewer", "复核", "交 review"],
    "file_evidence_gate": ["file", "evidence", "sample", "文件", "证据"],
    "quality_gate": ["quality", "qa_count", "item_count", "质量", "数量"],
    "artifact_standard_gate": [
        "artifact", "manifest", "path", "naming", "产物", "命名",
    ],
    "runtime_reality": [
        "runtime", "429", "fallback", "model", "inbox", "运行", "模型",
    ],
    "repair_acceptance_contract": ["repair", "minor", "revision", "返工", "修复"],
    "stale_state_reconciliation": [
        "stale", "old", "unread", "lag", "滞后", "旧状态",
    ],
    "subject_sample_first_gate": [
        "subject sample", "学科样板", "first subject", "golden path",
    ],
    "ap_qbank_schema_gate": [
        "ap qbank schema", "frontmatter", "qbank-agent",
        "item schema", "schema check",
    ],
    "content_quality_gate": [
        "content quality", "内容质量", "content pass", "quality pass",
    ],
    "role_boundary_gate": [
        "role boundary", "角色边界", "worker_builder", "boundary",
    ],
    "review_verdict_authority_gate": [
        "review verdict", "verdict authority", "正式 verdict", "manager verdict",
    ],
    "retro_before_next_subject_gate": [
        "retro", "复盘", "lesson learned", "next subject",
    ],
    "manager_closeout_gate": [
        "manager closeout", "正式收口", "closeout", "closeout_completed",
    ],
    "ap_item_schema_gate": [
        "ap item schema", "schema gate", "item validation", "frontmatter check",
    ],
    "tier_promotion_gate": [
        "tier promotion", "promotion gate", "tier advance", "晋级", "升级",
    ],
}


def _extract_workflow_gates(readme_path: Path) -> list[str]:
    """Parse `## Core Gates` from a workflow README and return gate names.

    The section is delimited by `## Core Gates` (or `## Acceptance Gates`)
    and the next `##` heading. Returned names are lowercased and stripped
    of backticks. Unknown / empty results yield an empty list.

    Accepts either the README path or the workflow directory; in the
    latter case, it looks for `README.md` inside.
    """
    if readme_path.is_dir():
        readme_path = readme_path / "README.md"
    try:
        text = readme_path.read_text(encoding="utf-8")
    except Exception:
        return []
    gates: list[str] = []
    in_section = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            heading = stripped[3:].strip().lower()
            in_section = heading in {"core gates", "acceptance gates"}
            continue
        if not in_section:
            continue
        # Stop at the next non-bullet, non-empty line so we don't pull
        # body text past the bullets.
        if not stripped:
            continue
        if not (stripped.startswith("-") or stripped.startswith("*")):
            # A paragraph under "## Core Gates" still describes gates; keep
            # reading until the next `##`.
            continue
        # Strip bullet + leading/trailing backticks/quotes, then take the
        # first word (the gate id).
        cleaned = re.sub(r"^[\-\*]\s*", "", stripped)
        cleaned = cleaned.strip().strip("`").strip("'").strip('"')
        # The first whitespace-delimited token is the gate id.
        token = cleaned.split()[0] if cleaned else ""
        token = token.strip("`").strip("'").strip('"').strip(",")
        if token:
            gates.append(token)
    return gates


# Cache: workflow_id -> list of gate names. Built lazily by
# `recommend()` so we don't re-parse every README on every call.
_workflow_gate_cache: dict[str, list[str]] = {}


def _workflow_gate_keywords(workflow_id: str, readme_path: str) -> set[str]:
    """Return the union of gate-keyword tokens for a workflow.

    Combines the gates declared in the workflow's README with the
    static `_GATE_KEYWORDS` lookup. Cached per workflow_id+path.
    """
    cache_key = f"{workflow_id}::{readme_path}"
    if cache_key in _workflow_gate_cache:
        gate_names = _workflow_gate_cache[cache_key]
    else:
        gate_names = _extract_workflow_gates(Path(readme_path))
        _workflow_gate_cache[cache_key] = gate_names
    out: set[str] = set()
    for gate in gate_names:
        out.update(_GATE_KEYWORDS.get(gate, []))
    return out



def _collect_trigger_terms(text: str, *, limit: int = 6) -> list[str]:
    """Heuristic trigger-term harvest from a SKILL.md body.

    Used only to make `asset recommend` return a non-empty
    `trigger_terms` list for keyword scoring. Not a semantic model.
    """
    if not text:
        return []
    terms: list[str] = []
    seen: set[str] = set()
    for raw in _TRIGGER_TERM_SPLIT.split(text):
        token = raw.strip().strip("`").strip('"').strip("'")
        if not token or len(token) < 2 or len(token) > 24:
            continue
        lowered = token.lower()
        if not re.search(r"[a-z0-9一-鿿]", lowered):
            continue
        if lowered in seen:
            continue
        seen.add(lowered)
        terms.append(token)
        if len(terms) >= limit:
            break
    return terms


# ── Scanners ─────────────────────────────────────────────────────


def scan_workflows(root: Path | None = None) -> list[Asset]:
    """Return workflow assets under docs/workflows (active + candidate)."""
    root = root or _workflows_root()
    rows: list[Asset] = []
    if not root.exists():
        return rows
    for entry in sorted(root.iterdir()):
        if not entry.is_dir() or entry.name.startswith("_"):
            continue
        if not (entry / "README.md").exists():
            continue
        asset_id = entry.name
        title = _readme_title(entry / "README.md")
        status = _workflow_status_from_readme(entry / "README.md")
        rows.append(Asset(
            asset_id=asset_id,
            asset_type="workflow",
            title=title or asset_id,
            path=str(entry),
            status=status,
            owner_role="manager",
            trigger_terms=[],
            validation_command=(
                f"eduflow workflow validate --strict"
            ),
            source_evidence="docs/workflows/.../README.md",
        ))
    candidate_root = root / "_candidates"
    if candidate_root.exists():
        for entry in sorted(candidate_root.iterdir()):
            if not entry.is_dir() or entry.name.startswith("_"):
                continue
            if not (entry / "README.md").exists():
                continue
            asset_id = entry.name
            title = _readme_title(entry / "README.md")
            status = _workflow_status_from_readme(entry / "README.md")
            rows.append(Asset(
                asset_id=asset_id,
                asset_type="workflow",
                title=title or asset_id,
                path=str(entry),
                status=status,
                owner_role="worker_builder",
                trigger_terms=[],
                validation_command=(
                    "eduflow workflow candidate-validate --strict"
                ),
                source_evidence="docs/workflows/_candidates/.../README.md",
            ))
    return rows


def _workflow_status_from_readme(readme: Path) -> str:
    """Best-effort status extraction; defaults to active when not declared."""
    try:
        text = readme.read_text(encoding="utf-8").lower()
    except Exception:
        return "unknown"
    for marker, status in (
        ("status: draft", "draft"),
        ("status: backlog", "backlog"),
        ("status: promotion_ready", "promotion_ready"),
        ("status: stale_candidate", "stale"),
        ("status: rejected", "stale"),
        ("status: case_note_only", "stale"),
        ("status: active", "active"),
    ):
        if marker in text:
            return status
    # No declared status; under _candidates the parent dir is the signal.
    if "_candidates" in str(readme):
        return "draft"
    return "active"


def scan_skills(skills_root: Path | None = None,
                claude_skills_root: Path | None = None) -> list[Asset]:
    """Return skill assets under skills/ and .claude/skills/.

    Layout:

    - skills/<id>/SKILL.md             (treat as folder skill)
    - .claude/skills/<id>/SKILL.md     (treat as folder skill)
    - .claude/skills/<name>.md         (treat as top-level reference)
    """
    skills_root = skills_root or _skills_root()
    claude_root = claude_skills_root or _claude_skills_root()
    rows: list[Asset] = []

    for base, owner in (
        (skills_root, "worker_builder"),
        (claude_root, "worker_builder"),
    ):
        if not base.exists():
            continue
        for entry in sorted(base.iterdir()):
            if entry.is_dir():
                skill_md = entry / "SKILL.md"
                if not skill_md.exists():
                    continue
                rows.append(_skill_from_file(
                    asset_id=entry.name, path=skill_md,
                    asset_type="skill", owner_role=owner,
                    source_evidence=f"{base.name}/{entry.name}/SKILL.md",
                ))
                continue
            if entry.is_file() and entry.suffix == ".md":
                rows.append(_skill_from_file(
                    asset_id=entry.stem, path=entry,
                    asset_type="patrol_reference", owner_role=owner,
                    source_evidence=f"{base.name}/{entry.name}",
                ))

    # Do NOT silently deduplicate here. `drift_check` needs to see
    # duplicates so it can surface them; `recommend` ignores duplicates
    # by collapsing on (asset_type, asset_id) and taking the highest
    # score, so duplicates never inflate the user-facing top-k.
    return rows


def _skill_from_file(*, asset_id: str, path: Path, asset_type: str,
                     owner_role: str, source_evidence: str) -> Asset:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        text = ""
    ok, name, description = _has_skill_name_description(text)
    status = "active" if ok else "draft"
    title = name or description.split(".")[0] if description else asset_id
    return Asset(
        asset_id=asset_id,
        asset_type=asset_type,
        title=title or asset_id,
        path=str(path),
        status=status,
        owner_role=owner_role,
        trigger_terms=_collect_trigger_terms(text),
        validation_command="",
        source_evidence=source_evidence,
        warnings=[] if ok else [f"{path.name} missing name/description"],
    )


def scan_identity_rules(agents_root: Path | None = None) -> list[Asset]:
    """Return identity_rule assets for every agent directory.

    Read-only: only checks existence and non-emptiness. Does NOT parse
    the actual identity content (which may carry secret material).
    """
    agents_root = agents_root or _agents_root()
    rows: list[Asset] = []
    if not agents_root.exists():
        return rows
    for entry in sorted(agents_root.iterdir()):
        if not entry.is_dir():
            continue
        identity = entry / "identity.md"
        if not identity.exists():
            rows.append(Asset(
                asset_id=entry.name,
                asset_type="identity_rule",
                title=entry.name,
                path=str(identity),
                status="missing",
                owner_role="manager",
                trigger_terms=[],
                validation_command="",
                source_evidence=f".eduflow-team-state/agents/{entry.name}/identity.md",
                exists=False,
                warnings=["identity.md missing"],
            ))
            continue
        try:
            size = identity.stat().st_size
        except Exception:
            size = 0
        if size <= 0:
            rows.append(Asset(
                asset_id=entry.name,
                asset_type="identity_rule",
                title=entry.name,
                path=str(identity),
                status="stale",
                owner_role="manager",
                trigger_terms=[],
                validation_command="",
                source_evidence=f".eduflow-team-state/agents/{entry.name}/identity.md",
                warnings=["identity.md empty"],
            ))
            continue
        rows.append(Asset(
            asset_id=entry.name,
            asset_type="identity_rule",
            title=entry.name,
            path=str(identity),
            status="active",
            owner_role="manager",
            trigger_terms=[],
            validation_command="",
            source_evidence=f".eduflow-team-state/agents/{entry.name}/identity.md",
        ))
    return rows


def scan_memory_candidates(root: Path | None = None) -> list[Asset]:
    """Return memory_candidate assets discovered under .omc/state/candidates.

    v1 only surfaces directory placeholders; it never reads candidate
    content. This keeps the registry safe to expose to read-only tooling.
    """
    root = root or _memory_candidates_root()
    rows: list[Asset] = []
    if not root.exists():
        return rows
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        rows.append(Asset(
            asset_id=entry.name,
            asset_type="memory_candidate",
            title=entry.name,
            path=str(entry),
            status="draft",
            owner_role="hermes",
            trigger_terms=[],
            validation_command="",
            source_evidence=f".omc/state/candidates/{entry.name}/",
        ))
    return rows


def scan_cli_check() -> list[Asset]:
    """Return the cli_check asset that represents this surface itself."""
    return [Asset(
        asset_id="eduflow-asset",
        asset_type="cli_check",
        title="eduflow asset",
        path="eduflow.commands.asset",
        status="active",
        owner_role="worker_builder",
        trigger_terms=["asset", "registry", "drift-check", "validate"],
        validation_command="eduflow asset validate --json",
        source_evidence="src/eduflow/commands/asset.py",
    )]


# ── Aggregator ──────────────────────────────────────────────────


def scan_all() -> list[Asset]:
    """Return the full read-only asset list across all types."""
    rows: list[Asset] = []
    rows.extend(scan_workflows())
    rows.extend(scan_skills())
    rows.extend(scan_identity_rules())
    rows.extend(scan_memory_candidates())
    rows.extend(scan_cli_check())
    return rows


# ── Recommend (keyword scoring) ─────────────────────────────────


def recommend(task_text: str, *, top_k: int = 5) -> list[dict]:
    """Return ranked asset recommendations for a free-form task text.

    Uses simple keyword overlap scoring. Every returned entry carries
    a `confidence` in [0, 1] so callers can render a stable
    "no confident recommendation" line when nothing scores well.
    """
    text = (task_text or "").lower()
    if not text.strip():
        return []
    text_tokens = {tok for tok in re.split(r"[\s,，;；、]+", text) if len(tok) >= 2}
    rows: list[dict] = []
    for asset in scan_all():
        haystack_tokens: set[str] = set()
        haystack_tokens.update(
            tok.lower() for tok in asset.trigger_terms if tok
        )
        haystack_tokens.update(
            tok.lower() for tok in re.split(r"[\s_/-]+", asset.asset_id) if len(tok) >= 2
        )
        if asset.title:
            haystack_tokens.update(
                tok.lower() for tok in re.split(r"[\s_/-]+", asset.title) if len(tok) >= 2
            )
        haystack_tokens.update(asset.asset_type.split())
        # Workflow-gate keyword matrix (OPT-3). When the task text
        # mentions a gate concept (e.g. "429 fallback", "stale inbox",
        # "manifest naming"), the workflow that owns that gate ranks
        # higher. Only active workflows gate-keywords are indexed;
        # candidates and skill assets keep their existing tokens.
        if asset.asset_type == "workflow":
            haystack_tokens.update(
                _workflow_gate_keywords(asset.asset_id, asset.path)
            )
        if not haystack_tokens:
            continue
        hits = text_tokens & haystack_tokens
        if not hits:
            continue
        score = len(hits) / max(len(haystack_tokens), 1)
        # boost when asset_id substring matches task text
        if asset.asset_id.lower() in text:
            score += 0.25
        score = min(score, 1.0)
        rows.append({
            "asset_id": asset.asset_id,
            "asset_type": asset.asset_type,
            "title": asset.title,
            "path": asset.path,
            "status": asset.status,
            "matched_terms": sorted(hits),
            "score": round(score, 3),
            "confidence": round(score, 3),
        })
    # Collapse duplicates so the same (asset_type, asset_id) does not
    # appear twice in the top-k. Keep the highest-scoring entry.
    seen_keys: set[tuple[str, str]] = set()
    collapsed: list[dict] = []
    for row in sorted(
        rows, key=lambda r: (-r["score"], r["asset_type"], r["asset_id"])
    ):
        key = (row["asset_type"], row["asset_id"])
        if key in seen_keys:
            continue
        seen_keys.add(key)
        collapsed.append(row)
        if len(collapsed) >= top_k:
            break
    return collapsed


# ── Validate ────────────────────────────────────────────────────


def validate(assets: Iterable[Asset] | None = None) -> dict:
    """Return ok / warnings / errors for the full registry.

    Errors are blocking (asset is not safe to consume); warnings are
    informational. The shape is stable: callers / tests rely on the
    top-level keys.
    """
    assets = list(assets) if assets is not None else scan_all()
    warnings: list[str] = []
    errors: list[str] = []
    workflows = [a for a in assets if a.asset_type == "workflow"]
    skills = [a for a in assets if a.asset_type in {"skill", "patrol_reference"}]
    identities = [a for a in assets if a.asset_type == "identity_rule"]

    # Workflow standard files
    for asset in workflows:
        if not asset.exists:
            errors.append(f"{asset.asset_id}: workflow directory missing")
            continue
        workflow_dir = Path(asset.path)
        for standard in WORKFLOW_STANDARD_FILES:
            if not (workflow_dir / standard).exists():
                msg = f"{asset.asset_id}: missing workflow standard file {standard}"
                # Candidates only need a subset; the strict check is
                # `eduflow workflow candidate-validate --strict`. Here
                # we only error when the active workflow is missing files.
                if "candidates" not in str(workflow_dir):
                    errors.append(msg)
                else:
                    warnings.append(msg)

    # Skill name/description
    for asset in skills:
        if not asset.path:
            warnings.append(f"{asset.asset_id}: skill path empty")
            continue
        path = Path(asset.path)
        if not path.exists():
            errors.append(f"{asset.asset_id}: skill path missing on disk")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception as exc:
            errors.append(f"{asset.asset_id}: cannot read skill ({exc})")
            continue
        ok, name, description = _has_skill_name_description(text)
        if not ok:
            warnings.append(
                f"{asset.asset_id}: SKILL.md missing name/description"
            )
        elif not name:
            warnings.append(
                f"{asset.asset_id}: SKILL.md missing frontmatter name"
            )
        elif not description:
            warnings.append(
                f"{asset.asset_id}: SKILL.md missing frontmatter description"
            )

    # Identity non-empty
    for asset in identities:
        if asset.status in {"missing", "stale"}:
            errors.append(
                f"{asset.asset_id}: identity rule {asset.status} "
                f"({asset.path or '-'})"
            )

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "total": len(assets),
            "workflows": len(workflows),
            "skills": len(skills),
            "identities": len(identities),
        },
    }


# ── Drift check ────────────────────────────────────────────────


def drift_check(assets: Iterable[Asset] | None = None) -> dict:
    """Return registry-level drift findings.

    Current drift dimensions:

    1. Same `asset_id` registered twice (different types ignored).
    2. Active workflow with the same id as a candidate workflow.
    3. Active workflow missing one of the standard files.
    4. Identity rule exists for an agent not present in the team
       config (best-effort: we only flag when the team config does
       not list the agent at all; we never modify it).
    5. Skill with no frontmatter name and no H1.
    """
    assets = list(assets) if assets is not None else scan_all()
    findings: list[dict] = []

    # 1. Duplicate asset_id (within the same asset_type).
    by_id: dict[tuple[str, str], list[Asset]] = {}
    for asset in assets:
        by_id.setdefault((asset.asset_type, asset.asset_id), []).append(asset)
    for (asset_type, asset_id), group in by_id.items():
        if len(group) > 1:
            paths = [a.path for a in group]
            findings.append({
                "category": "duplicate_asset",
                "asset_type": asset_type,
                "asset_id": asset_id,
                "paths": paths,
                "severity": "warn",
                "remediation": [
                    "Identify the canonical copy (the one the team actually loads).",
                    "For skills: the canonical home is `skills/<id>/SKILL.md`; "
                    "remove the duplicate under `.claude/skills/<id>/`.",
                    "For workflows: the canonical home is `docs/workflows/<id>/`; "
                    "delete the duplicate under `docs/workflows/_candidates/<id>/` "
                    "ONLY after confirming the candidate is the source archive "
                    "and no in-flight draft lives there.",
                ],
            })

    # 2. Active workflow with the same id as a candidate workflow.
    # Per docs/workflows/README.md the candidate source is "retained
    # unchanged as evidence/source archive" after promotion. So an
    # active+candidate pair is the EXPECTED post-promotion state, not
    # a bug. Severity is `info`; the finding stays visible for
    # operator review but does not fail `ok`.
    workflow_by_id_status: dict[str, list[Asset]] = {}
    for asset in assets:
        if asset.asset_type != "workflow":
            continue
        workflow_by_id_status.setdefault(asset.asset_id, []).append(asset)
    for asset_id, group in workflow_by_id_status.items():
        active = [a for a in group if a.status == "active"]
        candidates = [a for a in group if a.status != "active"]
        if active and candidates:
            # All candidates paired with the same id are expected.
            # The severity stays `info` regardless of candidate status;
            # the docs make it clear candidates are kept as evidence.
            findings.append({
                "category": "candidate_id_clashes_with_active_workflow",
                "asset_type": "workflow",
                "asset_id": asset_id,
                "active_path": active[0].path,
                "candidate_paths": [c.path for c in candidates],
                "candidate_statuses": sorted({c.status for c in candidates}),
                "severity": "info",
                "remediation": [
                    "Expected post-promotion state: docs/workflows/README.md "
                    "keeps the candidate as evidence/source archive.",
                    "If the candidate is no longer useful as evidence, "
                    "mark it as `case_note_only` in the candidate README "
                    "or remove the directory.",
                ],
            })

    # 3. Active workflow missing standard files.
    for asset in assets:
        if asset.asset_type != "workflow" or asset.status != "active":
            continue
        if not asset.path:
            continue
        workflow_dir = Path(asset.path)
        missing = [
            standard for standard in WORKFLOW_STANDARD_FILES
            if not (workflow_dir / standard).exists()
        ]
        if missing:
            findings.append({
                "category": "active_workflow_missing_standard_file",
                "asset_type": "workflow",
                "asset_id": asset.asset_id,
                "missing": missing,
                "severity": "error",
                "remediation": [
                    f"Add the missing file(s) under the workflow directory: {', '.join(missing)}",
                    "Or run `eduflow workflow validate --strict` to see exact "
                    "structural requirements.",
                ],
            })

    # 4. Identity rule but no team config listing.
    team_agents = _team_agent_names()
    for asset in assets:
        if asset.asset_type != "identity_rule":
            continue
        if team_agents is None:
            # No team config; cannot evaluate. Skip rather than false positive.
            continue
        if asset.asset_id not in team_agents:
            findings.append({
                "category": "identity_rule_for_unknown_agent",
                "asset_type": "identity_rule",
                "asset_id": asset.asset_id,
                "severity": "warn",
                "remediation": [
                    "Either add the agent to the team config "
                    "(`eduflow.toml` or `team.json`) or remove the orphan "
                    "identity directory under `.eduflow-team-state/agents/`.",
                ],
            })

    # 5. Skill with no frontmatter name and no H1.
    for asset in assets:
        if asset.asset_type not in {"skill", "patrol_reference"}:
            continue
        if not asset.path:
            continue
        path = Path(asset.path)
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        ok, name, _ = _has_skill_name_description(text)
        if not ok and not any(line.strip().startswith("# ") for line in text.splitlines()):
            findings.append({
                "category": "skill_missing_name_and_h1",
                "asset_type": asset.asset_type,
                "asset_id": asset.asset_id,
                "path": asset.path,
                "severity": "warn",
                "remediation": [
                    "Add a YAML frontmatter `name:` and `description:` block, "
                    "or a top-level `# Title` H1 heading.",
                ],
            })

    # 6. Mismatched gate-keyword mirror vs workflow.py (OPT-3 hygiene).
    # Read the source of truth from workflow.py and compare against the
    # local _GATE_KEYWORDS. If the two diverge, surface an info so the
    # asset registry never silently drifts from the workflow command.
    try:
        from eduflow.commands.workflow import _GATE_KEYWORDS as _WF_GATE_KEYWORDS
    except Exception:
        _WF_GATE_KEYWORDS = None
    if _WF_GATE_KEYWORDS is not None:
        local_keys = set(_GATE_KEYWORDS)
        wf_keys = set(_WF_GATE_KEYWORDS)
        missing = sorted(local_keys - wf_keys)
        extra = sorted(wf_keys - local_keys)
        if missing or extra:
            findings.append({
                "category": "gate_keyword_mirror_drift",
                "missing_in_workflow_py": missing,
                "extra_in_workflow_py": extra,
                "severity": "info",
                "remediation": [
                    "Re-sync asset_registry._GATE_KEYWORDS with "
                    "eduflow.commands.workflow._GATE_KEYWORDS so the "
                    "recommend scoring does not silently drop gate concepts.",
                ],
            })

    return {
        "ok": not any(f.get("severity") == "error" for f in findings),
        "findings": findings,
        "summary": {
            "total_findings": len(findings),
            "errors": sum(1 for f in findings if f.get("severity") == "error"),
            "warnings": sum(1 for f in findings if f.get("severity") == "warn"),
            "info": sum(1 for f in findings if f.get("severity") == "info"),
        },
    }


def _team_agent_names() -> set[str] | None:
    """Best-effort load of the team agent set. None when no config exists.

    Reads EDUFLOW_STATE_DIR/team.json (isolated_env default) and
    `claudeteam.toml` from the repo root. Never writes back.
    """
    candidates: list[Path] = []
    state_dir = os.environ.get("EDUFLOW_STATE_DIR")
    if state_dir:
        candidates.append(Path(state_dir) / "team.json")
    candidates.append(
        Path(__file__).resolve().parents[3] / ".eduflow-team-state" / "team.json"
    )
    for path in candidates:
        if not path.exists():
            continue
        try:
            import json as _json
            payload = _json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        agents = payload.get("agents") if isinstance(payload, dict) else None
        if isinstance(agents, dict):
            return {str(name) for name in agents}
        if isinstance(agents, list):
            return {str(name) for name in agents}
    return None
