"""`eduflowteam workflow` — inspect manager-callable workflow assets.

This command is mostly read-only. v1.9 adds one guarded write path for
candidate promotion so manager-approved workflow assets can be copied into the
active registry without turning the docs into an execution engine.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from eduflow.util import error_exit, maybe_print_help, usage_error


USAGE = (
    "usage:\n"
    "  eduflowteam workflow list\n"
    "  eduflowteam workflow show <workflow_id>\n"
    "  eduflowteam workflow trigger <workflow_id>\n"
    "  eduflowteam workflow roles <workflow_id>\n"
    "  eduflowteam workflow checklist <workflow_id>\n"
    "  eduflowteam workflow handoff <workflow_id>\n"
    "  eduflowteam workflow files <workflow_id>\n"
    "  eduflowteam workflow use <workflow_id>\n"
    "  eduflowteam workflow maintainer <workflow_id>\n"
    "  eduflowteam workflow template [README|trigger|roles|checklist|handoff]\n"
    "  eduflowteam workflow candidates\n"
    "  eduflowteam workflow candidate-show <workflow_id>\n"
    "  eduflowteam workflow candidate-files <workflow_id>\n"
    "  eduflowteam workflow candidate-validate [--strict]\n"
    "  eduflowteam workflow promotion-map [--summary] [--manager] [--actionable] [--ready] [--state <candidate_only|promoted|active_only>]\n"
    "  eduflowteam workflow promote-plan <candidate_id>\n"
    "  eduflowteam workflow promote <candidate_id> --approved-by-manager --write\n"
    "  eduflowteam workflow recommend <free_text>\n"
    "  eduflowteam workflow gates <workflow_id>\n"
    "  eduflowteam workflow closeout <workflow_id>\n"
    "  eduflowteam workflow gap-map\n"
    "  eduflowteam workflow validate [--strict]\n"
    "\n"
    "legacy alias: eduflow workflow ..."
)

_STANDARD_FILES = {
    "show": "README.md",
    "trigger": "trigger.md",
    "roles": "roles.md",
    "checklist": "checklist.md",
    "handoff": "handoff-template.md",
}

_TEMPLATE_FILES = {
    "README": "README.md",
    "readme": "README.md",
    "trigger": "trigger.md",
    "roles": "roles.md",
    "checklist": "checklist.md",
    "handoff": "handoff-template.md",
}

_REQUIRED_FILES = [
    "README.md",
    "trigger.md",
    "roles.md",
    "checklist.md",
    "handoff-template.md",
]

_KNOWN_GATES = [
    "dispatch_acceptance_gate",
    "review_handoff_gate",
    "file_evidence_gate",
    "quality_gate",
    "artifact_standard_gate",
    "runtime_reality",
    "repair_acceptance_contract",
    "stale_state_reconciliation",
    "ap_item_schema_gate",
    "manifest_qa_script_gate",
    "tier_promotion_gate",
    "subject_sample_first_gate",
    "ap_qbank_schema_gate",
    "content_quality_gate",
    "role_boundary_gate",
    "review_verdict_authority_gate",
    "retro_before_next_subject_gate",
    "manager_closeout_gate",
]

_RECOMMEND_KEYWORDS = {
    "igcse-subject-launch": [
        "launch", "subject", "candidate", "physics", "accounting", "curriculum",
        "pre-qa", "outline", "manifest", "closeout", "rollover", "new subject",
        "开线", "学科", "下一学科", "收口",
    ],
    "igcse-item-level-prototype": [
        "item", "qbank", "question", "prototype", "topic-level", "qa seed",
        "题库", "原型", "题目", "入库", "item-level",
    ],
    "realrun-to-workflow": [
        "realrun", "real run", "workflow", "builder", "gap", "asset",
        "maintenance", "maintainer", "case note", "沉淀", "复盘", "流程资产",
        # M8: task-truth drift operators describe a real run that
        # exposed a status / handoff / supervisor-check disagreement.
        # These keywords are the manager-side entry points for turning
        # the gap into a workflow asset, not a runtime-failover line.
        "task truth drift", "supervisor-check", "supervisor check",
        "manager panel", "manager-panel", "状态不一致", "状态漂移",
        "truth drift", "状态对不上",
    ],
    "ap-knowledge-base-optimization": [
        "ap", "calculus", "computer science", "csa", "physics", "psychology", "statistics",
        "biology", "chemistry", "knowledge base", "qbank", "题库", "知识库",
        "unit", "subject", "subject sample", "advanced placement", "ap exam",
    ],
    # M8: ops / status-drift class problems previously fell through to
    # `no confident workflow recommendation`. This bucket routes them
    # to `runtime-failover-hardening` (env / 429 / fallback / heart-
    # beat / warm-residency / status_truth_lag class) before the no-
    # confident path hands off to `task ops-dashboard` + the drift
    # explainer skill.
    "runtime-failover-hardening": [
        "429", "fallback", "runtime", "runtime_reality",
        "env drift", "env-drift", "runtime drift",
        "respawn", "cross-pool", "cross pool", "pool",
        "stale display", "stale_display", "stale status", "stale_status",
        "status_lag", "status lag", "status drift", "status-drift",
        "heartbeat", "heartbeat fresh", "heartbeat stale",
        "inbox not consumed", "pane ready but inbox",
        "pane not ready", "pane_ready", "pane_not_ready",
        "warm idle", "warm_idle", "温备", "温备 agent",
        "wake failed", "wake_failed", "wake failure",
        "外显陈旧", "外显滞后", "实际功能正常", "功能正常但显示陈旧",
        "二手外显", "二手状态",
    ],
}

# M8 + OPT-5: the no-confident topic table is derived from the
# unified `_GATE_KEYWORDS` + `_GATE_TOPIC` pair in
# `eduflow.store.asset_registry`. Adding a new drift concept is now a
# one-place change: extend `_GATE_KEYWORDS` for the keyword surface
# and add a topic entry in `_GATE_TOPIC` for the action mapping.
_NO_CONFIDENT_NEXT_STEPS_CACHE: list[tuple[frozenset, str, list[str]]] | None = None


def _no_confident_topics() -> list[tuple[frozenset, str, list[str]]]:
    """Lazy-resolved no-confident topic list. Cached after first call.

    Imports the asset_registry module on first call to avoid a
    circular import surface (workflow is imported by some asset
    registration paths during bootstrap).
    """
    global _NO_CONFIDENT_NEXT_STEPS_CACHE
    if _NO_CONFIDENT_NEXT_STEPS_CACHE is None:
        try:
            from eduflow.store import asset_registry
            _NO_CONFIDENT_NEXT_STEPS_CACHE = asset_registry.derive_no_confident_topics()
        except Exception:
            _NO_CONFIDENT_NEXT_STEPS_CACHE = []
    return _NO_CONFIDENT_NEXT_STEPS_CACHE


def _suggest_no_confident_packet(query: str) -> tuple[str, list[str]]:
    """Pick suggested_next_step + ordered candidate_skills for an unmatched query.

    Returns (next_step, candidate_skills_list). The list is ordered:
    the first entry is the primary skill, the rest are alternatives.
    Falls back to the generic list handoff with no skill when no
    topic matches.
    """
    lowered = (query or "").lower()
    for keywords, next_step, skills in _no_confident_topics():
        for token in keywords:
            if token and token in lowered:
                return next_step, list(skills)
    return "eduflowteam workflow list", []

_GATE_KEYWORDS = {
    "dispatch_acceptance_gate": ["dispatch", "accept", "accepted", "接单", "派工"],
    "review_handoff_gate": ["review", "handoff", "reviewer", "复核", "交 review"],
    "file_evidence_gate": ["file", "evidence", "sample", "文件", "证据"],
    "quality_gate": ["quality", "qa_count", "item_count", "质量", "数量"],
    "artifact_standard_gate": ["artifact", "manifest", "path", "naming", "产物", "命名"],
    "runtime_reality": ["runtime", "429", "fallback", "model", "inbox", "运行", "模型"],
    "repair_acceptance_contract": ["repair", "minor", "revision", "返工", "修复"],
    "stale_state_reconciliation": ["stale", "old", "unread", "lag", "滞后", "旧状态"],
    "subject_sample_first_gate": ["subject sample", "学科样板", "first subject", "golden path"],
    "ap_qbank_schema_gate": ["ap qbank schema", "frontmatter", "qbank-agent", "item schema", "schema check"],
    "content_quality_gate": ["content quality", "内容质量", "content pass", "quality pass"],
    "role_boundary_gate": ["role boundary", "角色边界", "worker_builder", "boundary"],
    "review_verdict_authority_gate": ["review verdict", "verdict authority", "正式 verdict", "manager verdict"],
    "retro_before_next_subject_gate": ["retro", "复盘", "lesson learned", "next subject"],
    "manager_closeout_gate": ["manager closeout", "正式收口", "closeout", "closeout_completed"],
    "ap_item_schema_gate": ["ap item schema", "schema gate", "item validation", "frontmatter check"],
    "tier_promotion_gate": ["tier promotion", "promotion gate", "tier advance", "晋级", "升级"],
}

_MAINTENANCE_ACTIONS = [
    "update_trigger_examples",
    "update_forbidden_moves",
    "update_acceptance_gates",
    "mark_stale_candidate",
    "split_new_workflow_candidate",
]

_CANDIDATE_STATUSES = {
    "draft",
    "backlog",
    "stale_candidate",
    "promotion_ready",
    "rejected",
    "case_note_only",
}

_PROMOTION_LINK_STATES = {
    "candidate_only",
    "promoted",
    "active_only",
}


def _workflow_root() -> Path:
    override = os.environ.get("EDUFLOW_WORKFLOW_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[3] / "docs" / "workflows"


def _workflow_dirs(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        p for p in root.iterdir()
        if p.is_dir() and not p.name.startswith("_") and (p / "README.md").exists()
    )


def _candidate_root(root: Path) -> Path:
    return root / "_candidates"


def _candidate_dirs(root: Path) -> list[Path]:
    candidate_root = _candidate_root(root)
    if not candidate_root.exists():
        return []
    return sorted(
        p for p in candidate_root.iterdir()
        if p.is_dir() and not p.name.startswith("_") and (p / "README.md").exists()
    )


def _title_from_readme(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return path.parent.name


def _cmd_list(root: Path) -> int:
    dirs = _workflow_dirs(root)
    if not dirs:
        return error_exit(f"❌ no workflows found under {root}")
    print("workflow_id\tname")
    for d in dirs:
        print(f"{d.name}\t{_title_from_readme(d / 'README.md')}")
    return 0


def _cmd_read(root: Path, workflow_id: str, kind: str) -> int:
    if "/" in workflow_id or workflow_id in ("", ".", ".."):
        return error_exit(f"❌ invalid workflow_id: {workflow_id!r}")
    filename = _STANDARD_FILES[kind]
    path = root / workflow_id / filename
    if not path.exists():
        return error_exit(f"❌ no such workflow {workflow_id!r} ({path})")
    print(path.read_text(encoding="utf-8").rstrip())
    return 0


def _workflow_dir(root: Path, workflow_id: str) -> Path | None:
    if "/" in workflow_id or workflow_id in ("", ".", ".."):
        return None
    path = root / workflow_id
    if not path.is_dir():
        return None
    return path


def is_active_workflow(workflow_id: str, *, root: Path | None = None) -> bool:
    """Return True when workflow_id points at a repo-side active workflow."""
    if workflow_id.startswith("_"):
        return False
    d = _workflow_dir(root or _workflow_root(), workflow_id)
    if d is None or any(part.startswith("_") for part in d.relative_to(root or _workflow_root()).parts):
        return False
    return all((d / name).exists() for name in _REQUIRED_FILES)


def _cmd_files(root: Path, workflow_id: str) -> int:
    d = _workflow_dir(root, workflow_id)
    if d is None:
        return error_exit(f"❌ no such workflow {workflow_id!r} ({root / workflow_id})")
    for name in _REQUIRED_FILES:
        print(d / name)
    return 0


def _cmd_template(root: Path, args: list[str]) -> int:
    if len(args) > 1:
        return usage_error(USAGE)
    part = args[0] if args else "README"
    filename = _TEMPLATE_FILES.get(part)
    if filename is None:
        allowed = "README, trigger, roles, checklist, handoff"
        return error_exit(f"❌ unknown template part: {part} (allowed: {allowed})")
    path = root / "_template" / filename
    if not path.exists():
        return error_exit(f"❌ workflow template file missing: {path}")
    print(path.read_text(encoding="utf-8").rstrip())
    return 0


def _candidate_dir(root: Path, workflow_id: str) -> Path | None:
    if "/" in workflow_id or workflow_id in ("", ".", "..") or workflow_id.startswith("_"):
        return None
    path = _candidate_root(root) / workflow_id
    if not path.is_dir():
        return None
    return path


def _candidate_status(d: Path) -> str:
    text = _read_required(d, "README.md")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- status:"):
            return stripped.split(":", 1)[1].strip().strip("`")
    return "-"


def _cmd_candidates(root: Path) -> int:
    dirs = _candidate_dirs(root)
    print("candidate_workflow_id\tstatus\tname")
    if not dirs:
        print("none")
        return 0
    for d in dirs:
        print(f"{d.name}\t{_candidate_status(d)}\t{_title_from_readme(d / 'README.md')}")
    return 0


def _cmd_candidate_show(root: Path, workflow_id: str) -> int:
    d = _candidate_dir(root, workflow_id)
    if d is None:
        return error_exit(f"❌ no such candidate workflow {workflow_id!r} ({_candidate_root(root) / workflow_id})")
    print((d / "README.md").read_text(encoding="utf-8").rstrip())
    return 0


def _cmd_candidate_files(root: Path, workflow_id: str) -> int:
    d = _candidate_dir(root, workflow_id)
    if d is None:
        return error_exit(f"❌ no such candidate workflow {workflow_id!r} ({_candidate_root(root) / workflow_id})")
    for name in _REQUIRED_FILES:
        print(d / name)
    return 0


def _validate_candidate(d: Path, *, strict: bool = False) -> list[str]:
    errors: list[str] = []
    workflow_id = d.name
    files: dict[str, str] = {}
    for name in _REQUIRED_FILES:
        path = d / name
        if not path.exists():
            errors.append(f"{workflow_id}: missing {name}")
            continue
        files[name] = path.read_text(encoding="utf-8")

    readme = files.get("README.md", "")
    if readme:
        if not _contains_any(readme, [workflow_id, "workflow:"]):
            errors.append(f"{workflow_id}: README.md missing workflow id/title")
        if "Primary Chain" not in readme:
            errors.append(f"{workflow_id}: README.md missing Primary Chain")
        if "Core Gates" not in readme:
            errors.append(f"{workflow_id}: README.md missing Core Gates")
        if not _contains_any(readme, _KNOWN_GATES):
            errors.append(f"{workflow_id}: README.md missing known gate names")

    trigger = files.get("trigger.md", "")
    if trigger:
        expected = f"调用 candidate workflow: {workflow_id}"
        active_call = f"调用 workflow: {workflow_id}"
        if expected not in trigger:
            errors.append(f"{workflow_id}: trigger.md missing {expected}")
        if active_call in trigger:
            errors.append(f"{workflow_id}: trigger.md must not use active call syntax")

    checklist = files.get("checklist.md", "")
    if checklist and "- [ ]" not in checklist:
        errors.append(f"{workflow_id}: checklist.md missing checkbox items")

    roles = files.get("roles.md", "")
    if roles and "manager" not in roles:
        errors.append(f"{workflow_id}: roles.md missing manager role")

    handoff = files.get("handoff-template.md", "")
    if handoff and not _contains_any(handoff, ["Manager ->", "manager", "handoff"]):
        errors.append(f"{workflow_id}: handoff-template.md missing manager/handoff template")

    if strict:
        for name, text in files.items():
            if workflow_id not in text and f"workflow: {workflow_id}" not in text:
                errors.append(f"{workflow_id}: {name} missing workflow_id reference")
        combined = "\n".join(files.values())
        combined_lower = combined.lower()
        readme = _read_required(d, "README.md")
        status = _candidate_status(d)
        if "- status:" not in readme or status not in _CANDIDATE_STATUSES:
            errors.append(f"{workflow_id}: strict missing status")
        if "- owner:" not in readme:
            errors.append(f"{workflow_id}: strict missing owner")
        if "manager" not in combined_lower or "closeout" not in combined_lower:
            errors.append(f"{workflow_id}: strict missing manager closeout")
        if "worker_builder" not in combined_lower and "builder" not in combined_lower:
            errors.append(f"{workflow_id}: strict missing builder followup")
        if "forbidden" not in combined_lower and "block promotion if" not in combined_lower:
            errors.append(f"{workflow_id}: strict missing forbidden moves")
        if "reassurance" not in combined_lower and "不抢 manager" not in combined_lower:
            errors.append(f"{workflow_id}: strict missing reassurance boundary")
        if "active workflow" not in combined_lower or "task dispatch --workflow" not in combined_lower:
            errors.append(f"{workflow_id}: strict missing active/task-dispatch boundary")
        if "promotion" not in combined_lower or "manager closeout" not in combined_lower:
            errors.append(f"{workflow_id}: strict missing promotion closeout boundary")
    return errors


def _cmd_candidate_validate(root: Path, *, strict: bool = False) -> int:
    dirs = _candidate_dirs(root)
    if not dirs:
        print("✅ candidate workflow registry valid (0 candidates)")
        return 0
    errors: list[str] = []
    for d in dirs:
        errors.extend(_validate_candidate(d, strict=strict))
    if errors:
        print("❌ candidate workflow validation failed")
        for err in errors:
            print(f"- {err}")
        return 1
    suffix = " strict" if strict else ""
    print(f"✅ candidate workflow registry{suffix} valid ({len(dirs)} candidates)")
    for d in dirs:
        print(f"- {d.name} status={_candidate_status(d)}")
    return 0


def _promotion_link_state(root: Path, workflow_id: str) -> str:
    candidate = _candidate_dir(root, workflow_id)
    active = _workflow_dir(root, workflow_id)
    if candidate is not None and active is not None:
        return "promoted"
    if candidate is not None:
        return "candidate_only"
    if active is not None:
        return "active_only"
    return "missing"


def _promotion_rows(root: Path) -> list[dict[str, str]]:
    candidate_dirs = _candidate_dirs(root)
    active_dirs = _workflow_dirs(root)
    ids = sorted({d.name for d in candidate_dirs} | {d.name for d in active_dirs})
    rows: list[dict[str, str]] = []
    for workflow_id in ids:
        candidate = _candidate_dir(root, workflow_id)
        rows.append({
            "workflow_id": workflow_id,
            "candidate_status": _candidate_status(candidate) if candidate is not None else "-",
            "active_present": "yes" if is_active_workflow(workflow_id, root=root) else "no",
            "candidate_present": "yes" if candidate is not None else "no",
            "link_state": _promotion_link_state(root, workflow_id),
        })
    return rows


def _manager_priority(row: dict[str, str]) -> int:
    if row["link_state"] == "candidate_only" and row["candidate_status"] == "promotion_ready":
        return 0
    if row["link_state"] == "candidate_only":
        return 1
    if row["link_state"] == "promoted":
        return 2
    return 3


def _manager_next_step(row: dict[str, str]) -> str:
    status = row["candidate_status"]
    if row["link_state"] == "candidate_only" and status == "promotion_ready":
        return f"run promote-plan {row['workflow_id']} then manager closeout"
    if row["link_state"] == "candidate_only":
        if status == "draft":
            return "finish candidate drafting and rerun candidate-validate --strict"
        if status == "backlog":
            return "keep in backlog until a real run or gap note justifies promotion review"
        if status == "stale_candidate":
            return "reconfirm runtime fit or retire the candidate from active consideration"
        if status == "rejected":
            return "retain as rejected evidence; do not reopen without new real-run evidence"
        if status == "case_note_only":
            return "keep as case-note evidence, not a reusable workflow candidate"
        return f"keep candidate review for status={status}"
    if row["link_state"] == "promoted":
        return f"verify active workflow {row['workflow_id']} and retain candidate source"
    return "active-only audit; candidate source not present"


def _cmd_promotion_map(root: Path, args: list[str]) -> int:
    summary = False
    manager_view = False
    actionable_only = False
    ready_only = False
    state_filter: str | None = None
    idx = 0
    while idx < len(args):
        arg = args[idx]
        if arg == "--summary":
            summary = True
            idx += 1
            continue
        if arg == "--manager":
            manager_view = True
            idx += 1
            continue
        if arg == "--actionable":
            actionable_only = True
            idx += 1
            continue
        if arg == "--ready":
            ready_only = True
            idx += 1
            continue
        if arg == "--state":
            if idx + 1 >= len(args):
                return usage_error(USAGE)
            state_filter = args[idx + 1]
            if state_filter not in _PROMOTION_LINK_STATES:
                allowed = ", ".join(sorted(_PROMOTION_LINK_STATES))
                return error_exit(f"❌ unknown promotion-map state: {state_filter} (allowed: {allowed})")
            idx += 2
            continue
        return usage_error(USAGE)

    rows = _promotion_rows(root)
    if ready_only:
        manager_view = True
        rows = [
            row for row in rows
            if row["link_state"] == "candidate_only" and row["candidate_status"] == "promotion_ready"
        ]
        actionable_only = True
        if state_filter is None:
            state_filter = "candidate_only"
    if actionable_only:
        rows = [row for row in rows if row["link_state"] == "candidate_only"]
        if state_filter is None:
            state_filter = "candidate_only"
    if state_filter is not None:
        rows = [row for row in rows if row["link_state"] == state_filter]

    if summary and manager_view:
        ready_for_closeout = [
            row for row in rows
            if row["link_state"] == "candidate_only" and row["candidate_status"] == "promotion_ready"
        ]
        candidate_review = [
            row for row in rows
            if row["link_state"] == "candidate_only" and row["candidate_status"] != "promotion_ready"
        ]
        promoted_audit = [row for row in rows if row["link_state"] == "promoted"]
        active_only_audit = [row for row in rows if row["link_state"] == "active_only"]
        print("promotion_map_manager_summary")
        print(f"ready_for_closeout\t{len(ready_for_closeout)}")
        print(f"candidate_review\t{len(candidate_review)}")
        print(f"promoted_audit\t{len(promoted_audit)}")
        print(f"active_only_audit\t{len(active_only_audit)}")
        if ready_for_closeout:
            first_ready = sorted(ready_for_closeout, key=lambda row: row["workflow_id"])[0]
            print(f"top_priority_workflow\t{first_ready['workflow_id']}")
            print(f"top_priority_next_step\t{_manager_next_step(first_ready)}")
        else:
            print("top_priority_workflow\t-")
            print("top_priority_next_step\t-")
        if ready_only:
            print("ready_only\tyes")
        if actionable_only:
            print("actionable_only\tyes")
        if state_filter is not None:
            print(f"filtered_state\t{state_filter}")
        print("read_only\tyes")
        print("suggested_next_step\teduflowteam workflow promotion-map --manager")
        return 0

    if summary:
        counts = {state: 0 for state in sorted(_PROMOTION_LINK_STATES)}
        for row in rows:
            counts[row["link_state"]] += 1
        print("promotion_map_summary")
        for state in ("candidate_only", "promoted", "active_only"):
            print(f"{state}\t{counts[state]}")
        if ready_only:
            print("ready_only\tyes")
        if actionable_only:
            print("actionable_only\tyes")
        if state_filter is not None:
            print(f"filtered_state\t{state_filter}")
        print("read_only\tyes")
        print("suggested_next_step\teduflowteam workflow promotion-map")
        return 0

    if manager_view:
        rows = sorted(rows, key=lambda row: (_manager_priority(row), row["workflow_id"]))
        print("workflow_id\tcandidate_status\tlink_state\tmanager_priority\tnext_step")
        if not rows:
            print("none")
            return 0
        for row in rows:
            print(
                f"{row['workflow_id']}\t{row['candidate_status']}\t{row['link_state']}\t"
                f"{_manager_priority(row)}\t{_manager_next_step(row)}"
            )
        print()
        print("legend:")
        print("- priority 0: promotion_ready candidates that can move toward manager closeout")
        print("- priority 1: candidate-only workflows still under review/backlog")
        print("- priority 2: already promoted workflows for audit/verification")
        print("- priority 3: active-only workflows without candidate source")
        if ready_only:
            print("- ready_only: candidate-only rows already marked promotion_ready")
        if actionable_only:
            print("- actionable_only: candidate-only manager decision queue")
        if state_filter is not None:
            print(f"- filtered_state: {state_filter}")
        print("- manager view is read-only; it does not modify candidate status or workflow files")
        return 0

    print("workflow_id\tcandidate_status\tactive_present\tcandidate_present\tlink_state")
    if not rows:
        print("none")
        return 0
    for row in rows:
        print(
            f"{row['workflow_id']}\t{row['candidate_status']}\t{row['active_present']}\t"
            f"{row['candidate_present']}\t{row['link_state']}"
        )
    print()
    print("legend:")
    print("- promoted: candidate source exists and active workflow exists")
    print("- candidate_only: candidate exists but no active workflow exists yet")
    print("- active_only: active workflow exists without candidate source in _candidates")
    if ready_only:
        print("- ready_only: promotion_ready candidate-only slice for manager closeout review")
    if actionable_only:
        print("- actionable_only: candidate-only slice for manager review")
    if state_filter is not None:
        print(f"- filtered_state: {state_filter}")
    print("- promotion-map is read-only; it does not modify candidate status or workflow files")
    return 0


def _cmd_promote_plan(root: Path, candidate_id: str) -> int:
    checked = _check_promotion_ready(root, candidate_id)
    if checked is None:
        return 1
    d, target, status = checked

    print(f"# candidate promotion plan: {candidate_id}")
    print()
    print(f"candidate workflow id: {candidate_id}")
    print(f"current status: {status}")
    print(f"source path: {d}")
    print(f"target path: {target}")
    print()
    print("## Required Approval")
    print("- manager closeout must explicitly approve promotion before any future write command.")
    print()
    print("## File Mapping")
    for name in _REQUIRED_FILES:
        print(f"- {d / name} -> {target / name}")
    print()
    print("## Read-only Boundary")
    print("- 本命令不会写文件、不会移动文件、不会派单、不会发飞书。")
    print("- It does not create an active workflow and does not execute workflows automatically.")
    print()
    print("## Suggested Next Commands")
    print(f"- eduflowteam workflow candidate-validate --strict")
    print(f"- future: eduflowteam workflow promote {candidate_id} --approved-by-manager --write")
    return 0


def _check_promotion_ready(root: Path, candidate_id: str) -> tuple[Path, Path, str] | None:
    d = _candidate_dir(root, candidate_id)
    if d is None:
        error_exit(
            f"❌ no such candidate workflow {candidate_id!r} "
            f"({_candidate_root(root) / candidate_id})"
        )
        return None

    target = root / candidate_id
    if target.exists():
        print("❌ promotion target conflict")
        print(f"- active workflow already exists: {target}")
        print("- resolve the conflict before promotion.")
        return None

    basic_errors = _validate_candidate(d, strict=False)
    if basic_errors:
        print("❌ candidate validation failed")
        for err in basic_errors:
            print(f"- {err}")
        return None

    strict_errors = _validate_candidate(d, strict=True)
    if strict_errors:
        print("❌ strict validation failed")
        for err in strict_errors:
            print(f"- {err}")
        return None

    status = _candidate_status(d)
    if status != "promotion_ready":
        print("❌ candidate is not promotion_ready")
        print(f"- candidate workflow id: {candidate_id}")
        print(f"- current status: {status}")
        print("- recommended next step: keep it in candidate review until manager closeout marks promotion_ready.")
        print("- no files were written or moved.")
        return None

    return d, target, status


def _promoted_trigger_text(candidate_id: str, text: str) -> str:
    return text.replace(
        f"调用 candidate workflow: {candidate_id}",
        f"调用 workflow: {candidate_id}",
    )


def _cmd_promote(root: Path, candidate_id: str, flags: list[str]) -> int:
    approved = "--approved-by-manager" in flags
    write = "--write" in flags
    unknown = [flag for flag in flags if flag not in {"--approved-by-manager", "--write"}]
    if unknown:
        return usage_error(USAGE)
    if not approved and not write:
        print("❌ promotion requires explicit authorization")
        print("- required flags: --approved-by-manager --write")
        print("- no files were written.")
        return 1
    if not approved:
        print("❌ missing manager approval")
        print("- required flag: --approved-by-manager")
        print("- no files were written.")
        return 1
    if not write:
        print("❌ missing write confirmation")
        print("- required flag: --write")
        print("- no files were written.")
        return 1

    checked = _check_promotion_ready(root, candidate_id)
    if checked is None:
        return 1
    source, target, _status = checked
    staging = root / f".{candidate_id}.promote.tmp"
    if staging.exists():
        shutil.rmtree(staging)

    copied: list[str] = []
    try:
        staging.mkdir(parents=False)
        for name in _REQUIRED_FILES:
            source_path = source / name
            target_path = staging / name
            text = source_path.read_text(encoding="utf-8")
            if name == "trigger.md":
                text = _promoted_trigger_text(candidate_id, text)
            target_path.write_text(text, encoding="utf-8")
            copied.append(name)
        staging.rename(target)
    except Exception as exc:
        if staging.exists():
            shutil.rmtree(staging)
        print("❌ promotion write failed")
        print(f"- candidate workflow id: {candidate_id}")
        print(f"- target path: {target}")
        print(f"- partial failure handled: temporary target cleaned")
        print(f"- error: {exc}")
        return 1

    print(f"✅ promoted workflow: {candidate_id}")
    print(f"source path: {source}")
    print(f"target path: {target}")
    print("copied files:")
    for name in copied:
        print(f"- {name}")
    print("trigger conversion:")
    print(f"- trigger.md converted `调用 candidate workflow: {candidate_id}` -> `调用 workflow: {candidate_id}`")
    print("next verification commands:")
    print("- eduflowteam workflow validate --strict")
    print("- eduflowteam workflow list")
    print("boundary:")
    print("- 未派单")
    print("- 未写 task")
    print("- 未发飞书")
    print("- 未自动执行 workflow")
    print("- candidate source retained")
    return 0


def _read_required(d: Path, name: str) -> str:
    path = d / name
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _first_section(text: str, heading: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    in_section = False
    for line in lines:
        if line.strip() == heading:
            in_section = True
            out.append(line)
            continue
        if in_section and line.startswith("## ") and line.strip() != heading:
            break
        if in_section:
            out.append(line)
    return "\n".join(out).strip()


def _section_after_heading(text: str, heading: str) -> str:
    wanted = heading.strip().lower()
    lines = text.splitlines()
    out: list[str] = []
    in_section = False
    for line in lines:
        stripped = line.strip()
        if stripped.lower() == wanted:
            in_section = True
            out.append(line)
            continue
        if in_section and stripped.startswith("## ") and stripped.lower() != wanted:
            break
        if in_section:
            out.append(line)
    return "\n".join(out).strip()


def _workflow_text(d: Path) -> str:
    return "\n".join(_read_required(d, name) for name in _REQUIRED_FILES)


def _tokenize(text: str) -> set[str]:
    normalized = []
    for ch in text.lower():
        if ch.isalnum() or ch in {"-", "_"}:
            normalized.append(ch)
        else:
            normalized.append(" ")
    return {part for part in "".join(normalized).split() if len(part) >= 3}


def _workflow_recommendations(root: Path, query: str) -> list[dict]:
    query_lower = query.lower()
    query_tokens = _tokenize(query)
    rows = []
    for d in _workflow_dirs(root):
        workflow_id = d.name
        text = _workflow_text(d).lower()
        keyword_hits = [
            kw for kw in _RECOMMEND_KEYWORDS.get(workflow_id, [])
            if kw.lower() in query_lower
        ]
        doc_hits = sorted(query_tokens & _tokenize(text))[:8]
        # M8: keyword hits still weight 3x and doc overlap up to 5, but
        # a single keyword hit is now enough to surface the workflow as
        # a candidate. The confidence tier labels the row but no longer
        # gates whether it appears in the output.
        score = len(keyword_hits) * 3 + min(len(doc_hits), 5)
        if score >= 8:
            confidence = "high"
        elif score >= 4:
            confidence = "medium"
        elif score >= 2:
            confidence = "low"
        else:
            confidence = "none"
        if score > 0:
            reason_bits = []
            if keyword_hits:
                reason_bits.append("keywords=" + ",".join(keyword_hits[:5]))
            if doc_hits:
                reason_bits.append("doc_overlap=" + ",".join(doc_hits[:5]))
            rows.append({
                "workflow_id": workflow_id,
                "score": score,
                "confidence": confidence,
                "reason": "; ".join(reason_bits) or "local text overlap",
            })
    rows.sort(key=lambda row: (-row["score"], row["workflow_id"]))
    return rows[:3]


def _cmd_recommend(root: Path, args: list[str]) -> int:
    query = " ".join(args).strip()
    if not query:
        return usage_error(USAGE)
    rows = _workflow_recommendations(root, query)
    # M8: a row with at least one keyword hit is a candidate
    # recommendation, even if its overall score is "low". We only
    # suppress rows whose only signal is one or two doc-overlap tokens
    # (the previous "low confidence" tier that hid keyword hits).
    confident = [row for row in rows
                 if row["confidence"] in {"high", "medium", "low"}
                 and row["score"] >= 2]
    if not confident:
        next_step, candidate_skills = _suggest_no_confident_packet(query)
        print("no confident workflow recommendation")
        print(f"suggested_next_step: {next_step}")
        if candidate_skills:
            print(f"candidate_skill: {candidate_skills[0]}")
            for alt in candidate_skills[1:]:
                print(f"also_consider_skill: {alt}")
        return 0
    print("workflow recommendations")
    for row in confident[:3]:
        marker = " (low confidence candidate)" if row["confidence"] == "low" else ""
        print(
            f"- {row['workflow_id']} confidence={row['confidence']} "
            f"score={row['score']} reason={row['reason']}{marker}"
        )
    # Always also print a next_step hint. When we have any confident
    # row (including low-confidence candidates), point at the top
    # match's `workflow use` page. The candidate_skills are shown when
    # the query is on a topic the operator skill set covers
    # (status-drift, runtime, task-truth-drift) so they can pair the
    # workflow with the read-only skill.
    top = confident[0]
    print(
        f"suggested_next_step: ./scripts/eduflowteam workflow use "
        f"{top['workflow_id']}"
    )
    topic_next_step, topic_skills = _suggest_no_confident_packet(query)
    if topic_skills:
        # Only attach the skill when the topic matched. A truly
        # unrelated query keeps the workflow-only output.
        print(f"candidate_skill: {topic_skills[0]}")
        for alt in topic_skills[1:]:
            print(f"also_consider_skill: {alt}")
    return 0


def _cmd_gates(root: Path, workflow_id: str) -> int:
    d = _workflow_dir(root, workflow_id)
    if d is None:
        return error_exit(f"❌ no such workflow {workflow_id!r} ({root / workflow_id})")
    readme = _read_required(d, "README.md")
    checklist = _read_required(d, "checklist.md")
    print(f"# workflow gates: {workflow_id}")
    print()
    print("## Core Gates")
    core = _section_after_heading(readme, "## Core Gates")
    print(core.replace("## Core Gates", "", 1).strip() or "(missing Core Gates)")
    print()
    print("## Forbidden Moves")
    forbidden = _section_after_heading(readme, "## Forbidden Moves")
    print(forbidden.replace("## Forbidden Moves", "", 1).strip() or "(missing Forbidden Moves)")
    print()
    print("## Block Closeout If")
    block = _section_after_heading(checklist, "## Block Closeout If")
    print(block.replace("## Block Closeout If", "", 1).strip() or "(missing Block Closeout If)")
    return 0


def _cmd_closeout(root: Path, workflow_id: str) -> int:
    d = _workflow_dir(root, workflow_id)
    if d is None:
        return error_exit(f"❌ no such workflow {workflow_id!r} ({root / workflow_id})")
    checklist = _read_required(d, "checklist.md")
    print(f"# manager closeout checklist: {workflow_id}")
    before = _section_after_heading(checklist, "## Before Manager Announces Launch")
    if not before:
        before = _section_after_heading(checklist, "## Before Manager Expands Prototype")
    if not before:
        before = _section_after_heading(checklist, "## Before Manager Marks Workflow Active")
    if not before:
        before = "\n".join(
            line for line in checklist.splitlines()
            if line.strip().startswith("- [ ]")
        )
    print(before.strip() or "(missing closeout checklist)")
    block = _section_after_heading(checklist, "## Block Closeout If")
    if block:
        print()
        print(block)
    return 0


def _docs_root(root: Path) -> Path:
    return root.parent if root.name == "workflows" else root


def _cmd_gap_map(root: Path) -> int:
    docs_root = _docs_root(root)
    candidates = []
    for pattern in ("*GAP*", "*REALRUN*", "*Workflow*", "workflows/*.md", "workflows/*/*.md"):
        candidates.extend(docs_root.glob(pattern))
    files = sorted({
        p for p in candidates
        if p.is_file() and "_template" not in p.parts and "_candidates" not in p.parts
    })
    workflow_texts = {
        d.name: _workflow_text(d).lower()
        for d in _workflow_dirs(root)
    }
    candidate_texts = {
        d.name: _workflow_text(d).lower()
        for d in _candidate_dirs(root)
    }
    print("workflow gap-map")
    emitted = 0
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        lower = text.lower()
        matched_gates = []
        for gate, keywords in _GATE_KEYWORDS.items():
            if gate in text or any(kw.lower() in lower for kw in keywords):
                matched_gates.append(gate)
        if not matched_gates:
            continue
        matched_workflows = []
        for workflow_id, wf_text in workflow_texts.items():
            if any(gate in wf_text for gate in matched_gates):
                matched_workflows.append(workflow_id)
        matched_candidates = []
        for workflow_id, wf_text in candidate_texts.items():
            if any(gate in wf_text for gate in matched_gates):
                matched_candidates.append(workflow_id)
        print(f"- {path.relative_to(docs_root)}")
        print(f"  gates: {', '.join(matched_gates)}")
        print(
            "  active_workflows: "
            f"{', '.join(matched_workflows) if matched_workflows else 'backlog_or_new_workflow'}"
        )
        if matched_candidates:
            print(f"  candidate_workflows: {', '.join(matched_candidates)}")
        emitted += 1
    if emitted == 0:
        print("no gap-to-gate mapping candidates found")
    return 0


def _cmd_use(root: Path, workflow_id: str) -> int:
    d = _workflow_dir(root, workflow_id)
    if d is None:
        return error_exit(f"❌ no such workflow {workflow_id!r} ({root / workflow_id})")
    readme = _read_required(d, "README.md")
    trigger = _read_required(d, "trigger.md")
    roles = _read_required(d, "roles.md")
    checklist = _read_required(d, "checklist.md")
    handoff = _read_required(d, "handoff-template.md")
    print(f"# manager workflow package: {workflow_id}")
    print()
    print("## Trigger")
    print(trigger.strip())
    print()
    print("## Primary Chain")
    chain = _first_section(readme, "## Primary Chain")
    print(chain or "(missing Primary Chain)")
    print()
    print("## Roles Summary")
    print(roles.strip())
    print()
    print("## Closeout Checklist")
    print(checklist.strip())
    print()
    print("## Handoff Template")
    print(handoff.strip())
    print()
    print("## Forbidden Moves")
    forbidden = _first_section(readme, "## Forbidden Moves")
    print(forbidden or "See checklist / workflow spec for forbidden moves.")
    return 0


def _cmd_maintainer(root: Path, workflow_id: str) -> int:
    d = _workflow_dir(root, workflow_id)
    if d is None:
        return error_exit(f"❌ no such workflow {workflow_id!r} ({root / workflow_id})")
    errors = _validate_workflow(d, strict=True)
    print(f"# worker_builder maintenance package: {workflow_id}")
    print()
    print("## Standard Files")
    for name in _REQUIRED_FILES:
        path = d / name
        state = "ok" if path.exists() else "missing"
        print(f"- {state}: {path}")
    print()
    print("## Validate Result")
    if errors:
        print("failed")
        for err in errors:
            print(f"- {err}")
    else:
        print("passed")
    print()
    print("## Next Maintenance Checklist")
    print("- [ ] Review latest real-run / gap-note evidence.")
    print("- [ ] Update trigger examples if manager used a new call pattern.")
    print("- [ ] Add forbidden moves when a repeated failure appears.")
    print("- [ ] Update checklist before changing manager or worker behavior.")
    print("- [ ] Run `eduflowteam workflow validate --strict` after edits.")
    print()
    print("## Maintenance Action Taxonomy")
    for action in _MAINTENANCE_ACTIONS:
        print(f"- {action}")
    print()
    print("## Lifecycle / Intake Reminder")
    print("- Keep active workflows backed by real runs.")
    print("- Treat one-off ideas as backlog or case notes until validated.")
    print("- worker_builder maintains assets; manager confirms active status.")
    return 0


def _contains_any(text: str, needles: list[str]) -> bool:
    return any(needle in text for needle in needles)


def _validate_workflow(d: Path, *, strict: bool = False) -> list[str]:
    errors: list[str] = []
    workflow_id = d.name
    files: dict[str, str] = {}
    for name in _REQUIRED_FILES:
        path = d / name
        if not path.exists():
            errors.append(f"{workflow_id}: missing {name}")
            continue
        files[name] = path.read_text(encoding="utf-8")

    readme = files.get("README.md", "")
    if readme:
        if not _contains_any(readme, [workflow_id, "workflow:"]):
            errors.append(f"{workflow_id}: README.md missing workflow id/title")
        if "Primary Chain" not in readme:
            errors.append(f"{workflow_id}: README.md missing Primary Chain")
        if "Core Gates" not in readme:
            errors.append(f"{workflow_id}: README.md missing Core Gates")
        if not _contains_any(readme, _KNOWN_GATES):
            errors.append(f"{workflow_id}: README.md missing known gate names")

    trigger = files.get("trigger.md", "")
    if trigger and f"调用 workflow: {workflow_id}" not in trigger:
        errors.append(f"{workflow_id}: trigger.md missing 调用 workflow: {workflow_id}")

    checklist = files.get("checklist.md", "")
    if checklist and "- [ ]" not in checklist:
        errors.append(f"{workflow_id}: checklist.md missing checkbox items")

    roles = files.get("roles.md", "")
    if roles and "manager" not in roles:
        errors.append(f"{workflow_id}: roles.md missing manager role")

    handoff = files.get("handoff-template.md", "")
    if handoff and not _contains_any(handoff, ["Manager ->", "manager", "handoff"]):
        errors.append(f"{workflow_id}: handoff-template.md missing manager/handoff template")
    if strict:
        for name, text in files.items():
            if workflow_id not in text and f"workflow: {workflow_id}" not in text:
                errors.append(f"{workflow_id}: {name} missing workflow_id reference")
        combined = "\n".join(files.values())
        combined_lower = combined.lower()
        if "manager" not in combined_lower or "closeout" not in combined_lower:
            errors.append(f"{workflow_id}: strict missing manager closeout language")
        if "worker_builder" not in combined_lower and "builder" not in combined_lower:
            errors.append(f"{workflow_id}: strict missing builder followup language")
        if "forbidden" not in combined_lower and "block closeout if" not in combined_lower:
            errors.append(f"{workflow_id}: strict missing forbidden move language")
        if "reassurance" not in combined_lower and "不抢 manager" not in combined_lower:
            errors.append(f"{workflow_id}: strict missing reassurance / manager-boundary language")
    return errors


def _cmd_validate(root: Path, *, strict: bool = False) -> int:
    dirs = _workflow_dirs(root)
    if not dirs:
        return error_exit(f"❌ no workflows found under {root}")
    errors: list[str] = []
    for d in dirs:
        errors.extend(_validate_workflow(d, strict=strict))
    if errors:
        print("❌ workflow registry validation failed")
        for err in errors:
            print(f"- {err}")
        return 1
    suffix = " strict" if strict else ""
    print(f"✅ workflow registry{suffix} valid ({len(dirs)} active workflows)")
    for d in dirs:
        print(f"- {d.name}")
    return 0


def main(argv: list[str]) -> int:
    rest = list(argv)
    if maybe_print_help(rest, USAGE):
        return 0
    if not rest:
        return usage_error(USAGE)

    root = _workflow_root()
    cmd = rest[0]
    args = rest[1:]
    if cmd == "list" and not args:
        return _cmd_list(root)
    if cmd == "validate":
        strict = False
        if args == ["--strict"]:
            strict = True
            args = []
        if not args:
            return _cmd_validate(root, strict=strict)
    if cmd == "files" and len(args) == 1:
        return _cmd_files(root, args[0])
    if cmd == "use" and len(args) == 1:
        return _cmd_use(root, args[0])
    if cmd == "maintainer" and len(args) == 1:
        return _cmd_maintainer(root, args[0])
    if cmd == "template":
        return _cmd_template(root, args)
    if cmd == "candidates" and not args:
        return _cmd_candidates(root)
    if cmd == "candidate-show" and len(args) == 1:
        return _cmd_candidate_show(root, args[0])
    if cmd == "candidate-files" and len(args) == 1:
        return _cmd_candidate_files(root, args[0])
    if cmd == "candidate-validate":
        strict = False
        if args == ["--strict"]:
            strict = True
            args = []
        if not args:
            return _cmd_candidate_validate(root, strict=strict)
    if cmd == "promotion-map":
        return _cmd_promotion_map(root, args)
    if cmd == "promote-plan" and len(args) == 1:
        return _cmd_promote_plan(root, args[0])
    if cmd == "promote" and len(args) >= 1:
        return _cmd_promote(root, args[0], args[1:])
    if cmd == "recommend":
        return _cmd_recommend(root, args)
    if cmd == "gates" and len(args) == 1:
        return _cmd_gates(root, args[0])
    if cmd == "closeout" and len(args) == 1:
        return _cmd_closeout(root, args[0])
    if cmd == "gap-map" and not args:
        return _cmd_gap_map(root)
    if cmd in _STANDARD_FILES and len(args) == 1:
        return _cmd_read(root, args[0], cmd)
    return usage_error(USAGE)
