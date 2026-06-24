"""Export SQLite memory data to Obsidian-readable Markdown files.

Design principles:
- SQLite is source of truth; Obsidian is a read-only export view.
- Exports are triggered automatically on mutations or manually via CLI.
- Each memory item becomes one markdown file with YAML frontmatter.
- Aggregate views (active-constraints.md, task-capsules.md, index.md)
  list summaries of all items of that type.

Export layout:
    <obsidian_root>/_memory-exports/
        index.md
        active-constraints.md
        task-capsules.md
        core-blocks.md
        decisions/<id>.md ...
        mistakes/<id>.md ...
        handoffs/<id>.md ...
        archive/<id>.md ...
"""
from __future__ import annotations

import json
import os
import shutil
import traceback
from datetime import datetime, timezone
from pathlib import Path


# Default Obsidian vault root. Override via EDUFLOW_OBSIDIAN_ROOT env var.
_DEFAULT_OBSIDIAN_ROOT = Path("/Volumes/Halobster/Obsidian Edu")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _obsidian_root() -> Path:
    env = os.environ.get("EDUFLOW_OBSIDIAN_ROOT", "")
    return Path(env) if env else _DEFAULT_OBSIDIAN_ROOT


def export_root() -> Path:
    """Return the export directory, creating it if needed."""
    root = _obsidian_root() / "_memory-exports"
    root.mkdir(parents=True, exist_ok=True)
    for sub in ("decisions", "mistakes", "handoffs", "archive", "candidates"):
        (root / sub).mkdir(exist_ok=True)
    return root


def _log_path() -> Path:
    """Log file for export operations."""
    from eduflow.runtime.paths import state_dir
    log_dir = state_dir() / "memory"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "export.log"


def _log(msg: str) -> None:
    """Append a timestamped line to the export log. Best-effort."""
    try:
        with open(_log_path(), "a") as f:
            f.write(f"{_now_iso()} {msg}\n")
    except Exception:
        pass


def _yaml_frontmatter(data: dict) -> str:
    """Render a dict as YAML frontmatter (simple key: value, no nested YAML lib)."""
    lines = ["---"]
    for k, v in data.items():
        if isinstance(v, bool):
            lines.append(f"{k}: {'true' if v else 'false'}")
        elif isinstance(v, (list, dict)):
            lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
        elif isinstance(v, (int, float)):
            lines.append(f"{k}: {v}")
        elif v is None or v == "":
            lines.append(f"{k}: ''")
        else:
            # Escape single quotes in strings
            sv = str(v).replace("'", "''")
            lines.append(f"{k}: '{sv}'")
    lines.append("---")
    return "\n".join(lines)


def _memory_item_md(m: dict) -> str:
    """Render a single memory item as a Markdown file."""
    now = _now_iso()
    evidence = m.get("evidence_refs", "[]")
    if isinstance(evidence, str):
        try:
            evidence = json.loads(evidence)
        except (json.JSONDecodeError, TypeError):
            evidence = [evidence] if evidence else []

    fm = _yaml_frontmatter({
        "memory_id": m.get("id", ""),
        "layer": m.get("layer", ""),
        "scope": m.get("scope", ""),
        "kind": m.get("kind", ""),
        "status": m.get("status", ""),
        "confidence": m.get("confidence", 1.0),
        "importance": m.get("importance", 5),
        "valid_from": m.get("valid_from", ""),
        "valid_until": m.get("valid_until", ""),
        "source_ref": m.get("source_ref", ""),
        "evidence_refs": evidence,
        "supersedes": m.get("supersedes", ""),
        "revision_of": m.get("revision_of", ""),
        "export_at": now,
    })

    title = m.get("summary", "") or m.get("content", "")[:80]
    content = m.get("content", "")
    source_ref = m.get("source_ref", "")

    body_lines = [
        fm,
        "",
        f"# {title}",
        "",
        content,
        "",
    ]

    if source_ref:
        body_lines.append(f"## 来源\n\n- {source_ref}")
        body_lines.append("")

    if evidence:
        body_lines.append("## 证据\n")
        for e in evidence:
            body_lines.append(f"- {e}")
        body_lines.append("")

    return "\n".join(body_lines) + "\n"


def _constraint_md(c: dict) -> str:
    """Render a single active constraint as Markdown."""
    now = _now_iso()
    evidence = c.get("evidence_refs", "[]")
    if isinstance(evidence, str):
        try:
            evidence = json.loads(evidence)
        except (json.JSONDecodeError, TypeError):
            evidence = [evidence] if evidence else []

    fm = _yaml_frontmatter({
        "constraint_id": c.get("id", ""),
        "scope": c.get("scope", ""),
        "constraint_level": c.get("constraint_level", ""),
        "constraint_type": c.get("constraint_type", ""),
        "enforcement": c.get("enforcement", ""),
        "status": c.get("status", ""),
        "valid_from": c.get("valid_from", ""),
        "valid_until": c.get("valid_until", ""),
        "source_ref": c.get("source_ref", ""),
        "injection_point": c.get("injection_point", ""),
        "export_at": now,
    })

    content = c.get("content", "")
    source_ref = c.get("source_ref", "")
    body_lines = [fm, "", f"# {content}", ""]
    if source_ref:
        body_lines.append(f"## 来源\n\n- {source_ref}")
        body_lines.append("")
    return "\n".join(body_lines) + "\n"


def _capsule_md(cap: dict) -> str:
    """Render a task capsule as Markdown."""
    now = _now_iso()
    blockers = cap.get("blockers", "[]")
    if isinstance(blockers, str):
        try:
            blockers = json.loads(blockers)
        except (json.JSONDecodeError, TypeError):
            blockers = []
    decisions = cap.get("decisions", "[]")
    if isinstance(decisions, str):
        try:
            decisions = json.loads(decisions)
        except (json.JSONDecodeError, TypeError):
            decisions = []

    fm = _yaml_frontmatter({
        "task_id": cap.get("task_id", ""),
        "workflow_id": cap.get("workflow_id", ""),
        "owner": cap.get("owner", ""),
        "gate": cap.get("gate", ""),
        "current_status": cap.get("current_status", ""),
        "next_action": cap.get("next_action", ""),
        "blockers": blockers,
        "decisions": decisions,
        "export_at": now,
    })

    task_id = cap.get("task_id", "")
    goal = cap.get("goal", "")
    acceptance = cap.get("acceptance", "")
    next_action = cap.get("next_action", "")

    body_lines = [fm, "", f"# {task_id}", ""]
    if goal:
        body_lines.append(f"**目标**: {goal}")
        body_lines.append("")
    if acceptance:
        body_lines.append(f"**验收标准**: {acceptance}")
        body_lines.append("")
    if next_action:
        body_lines.append(f"**下一步**: {next_action}")
        body_lines.append("")
    if blockers:
        body_lines.append("## 阻塞\n")
        for b in blockers:
            body_lines.append(f"- {b}")
        body_lines.append("")

    return "\n".join(body_lines) + "\n"


def _candidate_md(c: dict) -> str:
    """Render a single memory candidate as Markdown.

    Follows the same frontmatter/body convention as ``_memory_item_md``
    so reviewers can flip between confirmed items and candidates without
    re-learning the layout.
    """
    now = _now_iso()
    evidence = c.get("evidence_refs", "[]")
    if isinstance(evidence, str):
        try:
            evidence = json.loads(evidence)
        except (json.JSONDecodeError, TypeError):
            evidence = [evidence] if evidence else []
    risk_flags = c.get("risk_flags", "[]")
    if isinstance(risk_flags, str):
        try:
            risk_flags = json.loads(risk_flags)
        except (json.JSONDecodeError, TypeError):
            risk_flags = [risk_flags] if risk_flags else []

    fm = _yaml_frontmatter({
        "candidate_id": c.get("candidate_id", ""),
        "source_type": c.get("source_type", ""),
        "proposed_layer": c.get("proposed_layer", ""),
        "proposed_scope": c.get("proposed_scope", ""),
        "proposed_kind": c.get("proposed_kind", ""),
        "review_status": c.get("review_status", ""),
        "expires_at": c.get("expires_at", ""),
        "source_ref": c.get("source_ref", ""),
        "evidence_refs": evidence,
        "risk_flags": risk_flags,
        "export_at": now,
    })

    content = c.get("content", "")
    reason = c.get("reason", "")
    source_ref = c.get("source_ref", "")

    body_lines = [
        fm,
        "",
        f"# {content[:80]}",
        "",
        content,
        "",
    ]
    if reason:
        body_lines.append(f"## 生成原因\n\n{reason}")
        body_lines.append("")
    if source_ref:
        body_lines.append(f"## 来源\n\n- {source_ref}")
        body_lines.append("")
    if evidence:
        body_lines.append("## 证据\n")
        for e in evidence:
            body_lines.append(f"- {e}")
        body_lines.append("")
    if risk_flags:
        body_lines.append("## 风险标记\n")
        for f in risk_flags:
            body_lines.append(f"- {f}")
        body_lines.append("")

    return "\n".join(body_lines) + "\n"


def _semantic_index_status_lines() -> list[str]:
    """Return markdown status lines for the semantic vector index."""
    try:
        from eduflow.memory.vector_store import index_status
        status = index_status()
        if not status.get("available"):
            return []
        return [
            f"backend={status.get('backend', 'none')}",
            f"dim={status.get('dimension', 0)}",
            f"rows={status.get('row_count', 0)}",
        ]
    except Exception:
        return []


# ── Public API ─────────────────────────────────────────────────────────

def _kind_subdir(kind: str) -> str:
    """Map memory kind to export subdirectory."""
    mapping = {
        "decision": "decisions",
        "mistake": "mistakes",
        "handoff": "handoffs",
        "role_rule": "decisions",
        "workflow_rule": "decisions",
        "preference": "decisions",
        "domain_fact": "decisions",
        "runtime_rule": "decisions",
        "note": "decisions",
    }
    return mapping.get(kind, "decisions")


def export_all(
    *,
    scope: str | None = None,
    task_id: str | None = None,
) -> dict:
    """Export all memory data to Obsidian markdown files.

    Returns a summary dict with counts of exported items.
    """
    from eduflow.memory.constraints import list_constraints
    from eduflow.memory.items import list_memories
    from eduflow.memory.db import get_conn, init_schema

    init_schema()
    root = export_root()
    counts: dict[str, int] = {
        "constraints": 0,
        "capsules": 0,
        "items": 0,
        "archive": 0,
        "candidates": 0,
    }

    # 1. Export active constraints
    ac_path = root / "active-constraints.md"
    constraints = list_constraints(status="active")
    if scope:
        constraints = [c for c in constraints if c.get("scope") == scope]
    if task_id:
        constraints = [c for c in constraints
                       if c.get("scope") in ("team", f"task:{task_id}")
                       or c.get("scope", "").startswith("lane:")
                       or c.get("scope", "").startswith("workflow:")]

    ac_lines = [
        "---",
        f"export_at: '{_now_iso()}'",
        f"total: {len(constraints)}",
        "---",
        "",
        "# Active Constraints",
        "",
    ]
    if not constraints:
        ac_lines.append("_No active constraints._\n")
    else:
        for c in constraints:
            cid = c.get("id", "")
            level = c.get("constraint_level", "")
            enforcement = c.get("enforcement", "")
            ctype = c.get("constraint_type", "")
            content = c.get("content", "")
            ac_scope = c.get("scope", "")
            ac_lines.append(f"- **[{level}/{enforcement}]** [{ctype}] scope=`{ac_scope}` — {content}")
            counts["constraints"] += 1
    ac_path.write_text("\n".join(ac_lines) + "\n", encoding="utf-8")

    # 2. Export task capsules
    conn = get_conn()
    capsules_rows = conn.execute(
        "SELECT * FROM task_capsules ORDER BY updated_at DESC"
    ).fetchall()
    capsules = [dict(r) for r in capsules_rows]
    if task_id:
        capsules = [c for c in capsules if c.get("task_id") == task_id]

    tc_path = root / "task-capsules.md"
    tc_lines = [
        "---",
        f"export_at: '{_now_iso()}'",
        f"total: {len(capsules)}",
        "---",
        "",
        "# Task Capsules",
        "",
    ]
    if not capsules:
        tc_lines.append("_No task capsules._\n")
    else:
        for cap in capsules:
            tid = cap.get("task_id", "")
            owner = cap.get("owner", "")
            gate = cap.get("gate", "")
            status = cap.get("current_status", "")
            next_act = cap.get("next_action", "")
            tc_lines.append(f"## {tid}")
            tc_lines.append(f"- **owner**: {owner}")
            tc_lines.append(f"- **gate**: {gate}")
            tc_lines.append(f"- **status**: {status}")
            tc_lines.append(f"- **next_action**: {next_act}")
            tc_lines.append("")
            counts["capsules"] += 1
    tc_path.write_text("\n".join(tc_lines) + "\n", encoding="utf-8")

    # 3. Export memory items — one file per item + aggregate core-blocks.md
    confirmed = list_memories(status="confirmed", limit=1000)
    deprecated = list_memories(status="deprecated", limit=500)

    if scope:
        confirmed = [m for m in confirmed if m.get("scope") == scope]
        deprecated = [m for m in deprecated if m.get("scope") == scope]

    # Write individual item files
    for m in confirmed:
        mid = m.get("id", "")
        kind = m.get("kind", "")
        subdir = _kind_subdir(kind)
        fpath = root / subdir / f"{mid}.md"
        fpath.write_text(_memory_item_md(m), encoding="utf-8")
        counts["items"] += 1

    # Archive deprecated items
    for m in deprecated:
        mid = m.get("id", "")
        fpath = root / "archive" / f"{mid}.md"
        fpath.write_text(_memory_item_md(m), encoding="utf-8")
        counts["archive"] += 1

    # Clean up stale files in decisions/mistakes/handoffs that no longer exist
    for subdir in ("decisions", "mistakes", "handoffs"):
        existing_ids = {m.get("id") for m in confirmed if _kind_subdir(m.get("kind", "")) == subdir}
        sub_path = root / subdir
        if sub_path.exists():
            for f in sub_path.iterdir():
                if f.suffix == ".md" and f.stem not in existing_ids:
                    f.unlink()

    # Write core-blocks.md (summary of confirmed core/decision items)
    cb_path = root / "core-blocks.md"
    core_items = [m for m in confirmed if m.get("layer") in ("core", "decision") or m.get("importance", 5) >= 8]

    # Semantic index status for core-blocks footer
    semantic_status = _semantic_index_status_lines()

    cb_lines = [
        "---",
        f"export_at: '{_now_iso()}'",
        f"total: {len(core_items)}",
        "---",
        "",
        "# Core Blocks",
        "",
        "高重要性确认记忆（core/decision 层或 importance >= 8）",
        "",
    ]
    if not core_items:
        cb_lines.append("_No core blocks found._\n")
    else:
        for m in sorted(core_items, key=lambda x: -x.get("importance", 5)):
            mid = m.get("id", "")
            kind = m.get("kind", "")
            content = m.get("content", "")[:120]
            imp = m.get("importance", 5)
            cb_lines.append(f"- **[{mid}]** [{kind}] (imp={imp}) {content}")
    if semantic_status:
        cb_lines.append("")
        cb_lines.append("## 语义索引状态")
        cb_lines.extend(semantic_status)
    cb_path.write_text("\n".join(cb_lines) + "\n", encoding="utf-8")

    # 4. Export candidates — pending review queue
    # One file per candidate under candidates/; stale files (for
    # candidates no longer in proposed state) are cleaned up so the
    # directory reflects the current queue exactly.
    try:
        from eduflow.memory.candidates import list_candidates as _list_cands
        proposed_cands = _list_cands(status="proposed", limit=1000)
        rejected_cands = _list_cands(status="rejected", limit=200)
        promoted_cands = _list_cands(status="promoted", limit=200)
        all_cands = proposed_cands + rejected_cands + promoted_cands
        if scope:
            all_cands = [c for c in all_cands if c.get("proposed_scope") == scope]
        cands_dir = root / "candidates"
        written_ids: set[str] = set()
        for c in all_cands:
            cid = c.get("candidate_id", "")
            fpath = cands_dir / f"{cid}.md"
            fpath.write_text(_candidate_md(c), encoding="utf-8")
            written_ids.add(cid)
            counts["candidates"] += 1
        # Cleanup stale files
        if cands_dir.exists():
            for f in cands_dir.iterdir():
                if f.suffix == ".md" and f.stem not in written_ids:
                    try:
                        f.unlink()
                    except Exception:
                        pass
    except Exception:
        # Export is best-effort; never block the rest of the export
        # on a candidates query failure.
        pass

    # 5. Write index.md
    idx_path = root / "index.md"

    semantic_status = _semantic_index_status_lines()
    idx_lines = [
        "---",
        f"export_at: '{_now_iso()}'",
        "---",
        "",
        "# EduFlow Memory Exports",
        "",
        f"**导出时间**: {_now_iso()[:19]}",
        "",
        "## 当前状态",
        "",
        f"- **活跃约束**: {counts['constraints']} 条",
        f"- **任务胶囊**: {counts['capsules']} 个",
        f"- **确认记忆**: {counts['items']} 条",
        f"- **归档记忆**: {counts['archive']} 条",
        f"- **待审核候选**: {counts['candidates']} 条",
    ]
    if semantic_status:
        idx_lines.append("- **语义索引**: " + " | ".join(semantic_status))
    else:
        idx_lines.append("- **语义索引**: 未启用（缺少 lancedb）")
    idx_lines.extend([
        "",
        "## 文件索引",
        "",
        "- [[active-constraints]] — 当前活跃约束",
        "- [[task-capsules]] — 当前任务胶囊",
        "- [[core-blocks]] — 核心规则和高重要性记忆",
        "- `decisions/` — 已确认决策",
        "- `mistakes/` — 错误模式",
        "- `handoffs/` — 交接规则",
        "- `candidates/` — 待审核候选（事件驱动自动生成）",
        "- `archive/` — 历史/废弃记忆",
        "",
    ])
    idx_path.write_text("\n".join(idx_lines) + "\n", encoding="utf-8")

    _log(f"export_all complete: {counts}")
    return counts


def export_status() -> dict:
    """Return export status: last export time, file counts, log tail."""
    root = export_root()
    idx = root / "index.md"
    last_export = ""
    if idx.exists():
        # Parse export_at from frontmatter
        text = idx.read_text(encoding="utf-8")
        for line in text.split("\n"):
            if line.startswith("export_at:"):
                last_export = line.split(":", 1)[1].strip().strip("'\"")
                break

    # Count files
    file_counts: dict[str, int] = {}
    for sub in ("", "decisions", "mistakes", "handoffs", "archive", "candidates"):
        sub_path = root / sub if sub else root
        if sub_path.exists():
            md_files = list(sub_path.glob("*.md"))
            key = sub or "root"
            file_counts[key] = len(md_files)

    # Log tail
    log_tail: list[str] = []
    log_path = _log_path()
    if log_path.exists():
        lines = log_path.read_text(encoding="utf-8").strip().split("\n")
        log_tail = lines[-5:] if lines else []

    return {
        "last_export": last_export,
        "file_counts": file_counts,
        "log_tail": log_tail,
    }
