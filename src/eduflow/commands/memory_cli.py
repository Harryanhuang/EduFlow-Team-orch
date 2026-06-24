"""`eduflow memory` subcommands for active constraints, task capsules,
memory items, search, scope aliases, and candidates.

Usage:
    eduflow memory constraints --agent <agent> [--task <task_id>]
    eduflow memory constraints refresh --agent <agent> [--task <task_id>]
    eduflow memory constraints add <scope> <level> <type> "<content>" [options]
    eduflow memory constraints deactivate <constraint_id> [--reason "<reason>"]
    eduflow memory capsule <task_id>
    eduflow memory capsule refresh <task_id>
    eduflow memory packet --agent <agent> [--task <task_id>]
    eduflow memory items list [--scope <scope>] [--kind <kind>] [--status <status>]
    eduflow memory items get <memory_id>
    eduflow memory items add <scope> <kind> "<content>" [options]
    eduflow memory items deprecate <memory_id> [--reason "<reason>"]
    eduflow memory items supersede <old_id> <new_id>
    eduflow memory search "<query>" [--scope <scope>] [--kind <kind>]
    eduflow memory alias add <alias> <target_scope> [--kind-filter <kind>]
    eduflow memory alias list
    eduflow memory alias deactivate <alias>
    eduflow memory candidate add <scope> <kind> "<content>" [options]
    eduflow memory candidates [--scope <scope>] [--status <status>] [--source <type>] [--expire]
    eduflow memory promote <candidate_id> [--reviewer <name>] [--yes]
    eduflow memory reject <candidate_id> [--reason "<reason>"] [--yes]
    eduflow memory budget [check|enforce <table>]
    eduflow memory expire
    eduflow memory audit [scope|retention [--days <N>]]
    eduflow memory cleanup
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from eduflow.util import pop_flag, pop_bool_flag, usage_error

USAGE = (
    "usage: eduflow memory <subcommand> [args...]\n"
    "\n"
    "Phase 1A (existing):\n"
    "  constraints --agent <agent> [--task <task_id>]\n"
    "  constraints refresh --agent <agent> [--task <task_id>]\n"
    "  constraints add <scope> <level> <type> \"<content>\" [--enforcement <level>] [--ref <source>]\n"
    "  constraints deactivate <constraint_id> [--reason \"<reason>\"]\n"
    "  capsule <task_id>\n"
    "  capsule refresh <task_id>\n"
    "  packet --agent <agent> [--task <task_id>]\n"
    "\n"
    "Phase 1 (memory core):\n"
    "  items list [--scope <scope>] [--kind <kind>] [--status <status>] [--layer <layer>]\n"
    "  items get <memory_id>\n"
    "  items add <scope> <kind> \"<content>\" [--layer <layer>] [--summary \"<text>\"] [--importance <1-10>]\n"
    "  items deprecate <memory_id> [--reason \"<reason>\"]\n"
    "  items supersede <old_id> <new_id>\n"
    "  search \"<query>\" [--scope <scope>] [--kind <kind>] [--min-importance <1-10>] [--limit <N>] [--fts]\n"
    "  semantic \"<query>\"  (alias for search)\n"
    "  reindex  (rebuild semantic vector index)\n"
    "  index-status  (show semantic vector index status)\n"
    "  test-embedding [\"text\"]  (test SiliconFlow API and show dimension)\n"
    "  alias add <alias> <target_scope> [--kind-filter <kind>]\n"
    "  alias list\n"
    "  alias deactivate <alias>\n"
    "\n"
    "Phase 3 (candidate/promote):\n"
    "  candidate add <scope> <kind> \"<content>\" [--source <type>] [--reason \"<reason>\"] [--layer <layer>]\n"
    "  candidates [--scope <scope>] [--status <status>] [--source <type>] [--limit <N>] [--expire]\n"
    "  promote <candidate_id> [--reviewer <name>] [--yes]\n"
    "  reject <candidate_id> [--reason \"<reason>\"] [--yes]\n"
    "\n"
    "Obsidian export:\n"
    "  export [--all] [--scope <scope>] [--task <task_id>]\n"
    "  export status\n"
    "\n"
    "Management:\n"
    "  budget                    (full budget report: all tables + DB size)\n"
    "  budget check <table>      (single table row count vs limit)\n"
    "  budget enforce <table>    (evict oldest rows to bring table under budget)\n"
    "  expire                    (run all automatic expiry scans)\n"
    "  audit                     (full audit: row counts by status)\n"
    "  audit scope               (scope coverage report for confirmed memories)\n"
    "  audit retention [--days N] (lifecycle stats in time window)\n"
    "  cleanup                   (expire + budget enforce combined)\n"
    "\n"
    "Debug (injection preview):\n"
    "  packet --agent <agent> [--task <task_id>]\n"
    "  inject-check <agent> --message \"...\" [--task <task_id>]\n"
    "  gate-check <agent> --task <task_id> --gate <gate_name>"
)


def _cmd_constraints(argv: list[str]) -> int:
    rest = list(argv)

    # Check for sub-subcommands
    if rest and rest[0] == "refresh":
        return _cmd_constraints_refresh(rest[1:])
    if rest and rest[0] == "add":
        return _cmd_constraints_add(rest[1:])
    if rest and rest[0] == "deactivate":
        return _cmd_constraints_deactivate(rest[1:])

    # Default: list constraints
    agent = pop_flag(rest, "--agent")
    task = pop_flag(rest, "--task")
    if not agent:
        return usage_error("usage: eduflow memory constraints --agent <agent> [--task <task_id>]")

    from eduflow.memory.constraints import query_for_agent
    constraints = query_for_agent(agent, task_id=task)

    if not constraints:
        print(f"No active constraints for agent={agent}" + (f" task={task}" if task else ""))
        return 0

    print(f"Active constraints for agent={agent}" + (f" task={task}" if task else "") + ":")
    for c in constraints:
        level = c.get("constraint_level", "")
        enforcement = c.get("enforcement", "")
        ctype = c.get("constraint_type", "")
        scope = c.get("scope", "")
        content = c.get("content", "")
        cid = c.get("id", "")
        print(f"  [{cid}] [{level}/{enforcement}] [{ctype}] scope={scope}")
        print(f"    {content}")
    return 0


def _cmd_constraints_refresh(argv: list[str]) -> int:
    rest = list(argv)
    agent = pop_flag(rest, "--agent")
    task = pop_flag(rest, "--task")
    if not agent:
        return usage_error("usage: eduflow memory constraints refresh --agent <agent> [--task <task_id>]")

    if task:
        from eduflow.memory.capsules import refresh_from_task_store
        capsule = refresh_from_task_store(task)
        if capsule:
            print(f"Refreshed capsule for {task}")
        else:
            print(f"No flow task found for {task}")

    # Re-derive constraints from current task state
    if task:
        from eduflow.memory.constraints import list_constraints
        existing = list_constraints(scope=f"task:{task}", status="active")
        print(f"Active constraints for task {task}: {len(existing)}")
    else:
        print(f"Refreshed for agent={agent}")

    return 0


def _cmd_constraints_add(argv: list[str]) -> int:
    rest = list(argv)
    if len(rest) < 3:
        return usage_error(
            "usage: eduflow memory constraints add <scope> <level> <type> \"<content>\" "
            "[--enforcement <level>] [--ref <source>]"
        )
    scope = rest.pop(0)
    level = rest.pop(0)
    constraint_type = rest.pop(0)
    content = rest.pop(0) if rest else ""

    enforcement = pop_flag(rest, "--enforcement") or "prompt_only"
    ref = pop_flag(rest, "--ref") or ""

    if not content:
        return usage_error("content cannot be empty")

    from eduflow.memory.constraints import add_constraint
    cid = add_constraint(
        scope=scope,
        level=level,
        constraint_type=constraint_type,
        content=content,
        source_ref=ref,
        enforcement=enforcement,
    )
    print(f"Created constraint: {cid}")
    return 0


def _cmd_constraints_deactivate(argv: list[str]) -> int:
    rest = list(argv)
    if not rest:
        return usage_error("usage: eduflow memory constraints deactivate <constraint_id> [--reason \"<reason>\"]")
    cid = rest.pop(0)
    reason = pop_flag(rest, "--reason") or ""

    from eduflow.memory.constraints import deactivate_constraint
    ok = deactivate_constraint(cid, reason=reason)
    if ok:
        print(f"Deactivated constraint: {cid}")
    else:
        print(f"Constraint not found or already inactive: {cid}")
    return 0


def _cmd_capsule(argv: list[str]) -> int:
    rest = list(argv)
    if not rest:
        return usage_error("usage: eduflow memory capsule <task_id>")
    if rest[0] == "refresh":
        return _cmd_capsule_refresh(rest[1:])

    task_id = rest[0]
    from eduflow.memory.capsules import get_capsule
    capsule = get_capsule(task_id)
    if not capsule:
        print(f"No capsule for {task_id}")
        return 0

    print(f"Capsule for {task_id}:")
    for key in ("workflow_id", "owner", "gate", "goal", "acceptance",
                 "current_status", "next_action", "blockers", "decisions",
                 "last_evidence_ref", "updated_at"):
        val = capsule.get(key, "")
        if val and val != "[]":
            print(f"  {key}: {val}")
    return 0


def _cmd_capsule_refresh(argv: list[str]) -> int:
    rest = list(argv)
    if not rest:
        return usage_error("usage: eduflow memory capsule refresh <task_id>")
    task_id = rest[0]

    from eduflow.memory.capsules import refresh_from_task_store
    capsule = refresh_from_task_store(task_id)
    if capsule:
        print(f"Refreshed capsule for {task_id}")
        for key in ("workflow_id", "owner", "gate", "goal", "next_action", "blockers"):
            val = capsule.get(key, "")
            if val and val != "[]":
                print(f"  {key}: {val}")
    else:
        print(f"No flow task found for {task_id}")
    return 0


def _cmd_packet(argv: list[str]) -> int:
    rest = list(argv)
    agent = pop_flag(rest, "--agent")
    task = pop_flag(rest, "--task")
    if not agent:
        return usage_error("usage: eduflow memory packet --agent <agent> [--task <task_id>]")

    from eduflow.memory.packet import assemble_memory_packet
    packet = assemble_memory_packet(agent, task_id=task)
    if packet:
        print(packet)
    else:
        print(f"No memory packet for agent={agent}" + (f" task={task}" if task else ""))
    return 0


# ── Phase 1: Memory Items ──────────────────────────────────────────────

def _cmd_items(argv: list[str]) -> int:
    rest = list(argv)
    if not rest:
        return usage_error("usage: eduflow memory items <list|get|add|deprecate|supersede> ...")
    sub = rest[0]
    if sub == "list":
        return _cmd_items_list(rest[1:])
    if sub == "get":
        return _cmd_items_get(rest[1:])
    if sub == "add":
        return _cmd_items_add(rest[1:])
    if sub == "deprecate":
        return _cmd_items_deprecate(rest[1:])
    if sub == "supersede":
        return _cmd_items_supersede(rest[1:])
    return usage_error(f"unknown items subcommand: {sub}")


def _cmd_items_list(argv: list[str]) -> int:
    rest = list(argv)
    scope = pop_flag(rest, "--scope")
    kind = pop_flag(rest, "--kind")
    status = pop_flag(rest, "--status") or "confirmed"
    layer = pop_flag(rest, "--layer")
    limit = int(pop_flag(rest, "--limit") or "50")

    from eduflow.memory.items import list_memories
    memories = list_memories(
        scope=scope or None, kind=kind or None, status=status or None,
        layer=layer or None, limit=limit,
    )
    if not memories:
        print("No memory items found.")
        return 0
    for m in memories:
        mid = m.get("id", "")
        kind_v = m.get("kind", "")
        scope_v = m.get("scope", "")
        layer_v = m.get("layer", "")
        importance = m.get("importance", 5)
        summary = m.get("summary", "") or m.get("content", "")[:80]
        print(f"  [{mid}] [{kind_v}] [{layer_v}] scope={scope_v} importance={importance}")
        print(f"    {summary}")
    return 0


def _cmd_items_get(argv: list[str]) -> int:
    rest = list(argv)
    if not rest:
        return usage_error("usage: eduflow memory items get <memory_id>")
    mid = rest[0]
    from eduflow.memory.items import get_memory
    m = get_memory(mid)
    if not m:
        print(f"Memory item not found: {mid}")
        return 0
    for key in ("id", "layer", "scope", "kind", "status", "content", "summary",
                "source_ref", "evidence_refs", "confidence", "importance",
                "valid_from", "valid_until", "created_by", "created_at",
                "supersedes", "revision_of"):
        val = m.get(key, "")
        if val and val != "[]" and val != "{}":
            print(f"  {key}: {val}")
    return 0


def _cmd_items_add(argv: list[str]) -> int:
    rest = list(argv)
    if len(rest) < 3:
        return usage_error(
            "usage: eduflow memory items add <scope> <kind> \"<content>\" "
            "[--layer <layer>] [--summary \"<text>\"] [--importance <1-10>] "
            "[--confidence <0-1>] [--supersedes <id>] [--revision-of <id>] "
            "[--status <status>] [--created-by <agent>]"
        )
    scope = rest.pop(0)
    kind = rest.pop(0)
    content = rest.pop(0)

    layer = pop_flag(rest, "--layer") or "episode"
    summary = pop_flag(rest, "--summary") or ""
    importance = int(pop_flag(rest, "--importance") or "5")
    confidence = float(pop_flag(rest, "--confidence") or "1.0")
    supersedes = pop_flag(rest, "--supersedes") or ""
    revision_of = pop_flag(rest, "--revision-of") or ""
    status = pop_flag(rest, "--status") or "candidate"
    created_by = pop_flag(rest, "--created-by") or ""
    source_ref = pop_flag(rest, "--source") or ""

    from eduflow.memory.items import add_memory
    mid = add_memory(
        scope=scope, kind=kind, content=content,
        layer=layer, summary=summary, source_ref=source_ref,
        confidence=confidence, importance=importance,
        created_by=created_by, supersedes=supersedes,
        revision_of=revision_of, status=status,
    )
    print(f"Created memory item: {mid}")
    return 0


def _cmd_items_deprecate(argv: list[str]) -> int:
    rest = list(argv)
    if not rest:
        return usage_error("usage: eduflow memory items deprecate <memory_id> [--reason \"<reason>\"]")
    mid = rest.pop(0)
    reason = pop_flag(rest, "--reason") or ""
    from eduflow.memory.items import deprecate_memory
    ok = deprecate_memory(mid, reason=reason)
    if ok:
        print(f"Deprecated memory item: {mid}")
    else:
        print(f"Memory item not found or already deprecated: {mid}")
    return 0


def _cmd_items_supersede(argv: list[str]) -> int:
    rest = list(argv)
    if len(rest) < 2:
        return usage_error("usage: eduflow memory items supersede <old_id> <new_id>")
    old_id = rest[0]
    new_id = rest[1]
    from eduflow.memory.items import supersede_memory
    ok = supersede_memory(old_id, new_id)
    if ok:
        print(f"Superseded: {old_id} → {new_id}")
    else:
        print(f"Failed to supersede (check IDs exist): {old_id} → {new_id}")
    return 0


# ── Phase 1: Search ────────────────────────────────────────────────────

def _cmd_search(argv: list[str]) -> int:
    rest = list(argv)
    if not rest:
        return usage_error(
            "usage: eduflow memory search \"<query>\" [--scope <scope>] [--kind <kind>] "
            "[--min-importance <1-10>] [--limit <N>] [--fts]"
        )
    query = rest.pop(0)
    scope = pop_flag(rest, "--scope")
    kind = pop_flag(rest, "--kind")
    status = pop_flag(rest, "--status") or "confirmed"
    limit = int(pop_flag(rest, "--limit") or "5")
    min_importance = int(pop_flag(rest, "--min-importance") or "0")
    fts_mode = "--fts" in rest
    if fts_mode:
        rest = [a for a in rest if a != "--fts"]

    if fts_mode:
        from eduflow.memory.search import search_memories
        results = search_memories(
            query, scope=scope or None, kind=kind or None,
            status=status or None, limit=limit,
        )
        if not results:
            print(f"No memories found matching: {query}")
            return 0
        print(f"FTS search results for \"{query}\":")
        for m in results:
            mid = m.get("id", "")
            kind_v = m.get("kind", "")
            scope_v = m.get("scope", "")
            summary = m.get("summary", "") or m.get("content", "")[:80]
            print(f"  [{mid}] [{kind_v}] scope={scope_v}")
            print(f"    {summary}")
        return 0

    # Semantic search via vector store; fall back to FTS if vector index unavailable.
    from eduflow.memory.vector_store import search_similar, index_status
    status_info = index_status()
    if not status_info.get("available"):
        from eduflow.memory.search import search_memories
        results = search_memories(
            query, scope=scope or None, kind=kind or None,
            status=status or None, limit=limit,
        )
        if not results:
            print(f"No memories found matching: {query}")
            return 0
        print("(vector index unavailable; falling back to FTS search)")
        print(f"Search results for \"{query}\":")
        for m in results:
            mid = m.get("id", "")
            kind_v = m.get("kind", "")
            scope_v = m.get("scope", "")
            summary = m.get("summary", "") or m.get("content", "")[:80]
            print(f"  [{mid}] [{kind_v}] scope={scope_v}")
            print(f"    {summary}")
        return 0

    results = search_similar(
        query, top_k=limit,
        scope_filter=scope or None,
        min_importance=min_importance,
    )
    if not results:
        print(f"No semantic matches for: {query}")
        return 0
    print(f"Semantic search results for \"{query}\":")
    for r in results:
        mid = r.get("memory_id", "")
        kind_v = r.get("kind", "")
        scope_v = r.get("scope", "")
        score = r.get("score", 0.0)
        summary = r.get("content", "")[:80]
        print(f"  [{mid}] [{kind_v}] scope={scope_v} score={score}")
        print(f"    {summary}")
    return 0


def _cmd_reindex(argv: list[str]) -> int:
    """Rebuild the semantic vector index from all confirmed memories."""
    from eduflow.memory.vector_store import index_all_confirmed, index_status
    status_info = index_status()
    if not status_info.get("available"):
        print("向量索引不可用。请先安装 lancedb：")
        print("  pip install 'eduflow[vector]'")
        return 1
    count = index_all_confirmed()
    print(f"Reindexed {count} confirmed memories into LanceDB.")
    return 0


def _cmd_index_status(argv: list[str]) -> int:
    """Show semantic vector index status."""
    from eduflow.memory.vector_store import index_status
    status = index_status()
    if not status.get("available"):
        print("向量索引不可用。请先安装 lancedb：")
        print("  pip install 'eduflow[vector]'")
        return 1
    print("Semantic index status:")
    print(f"  backend: {status.get('backend', 'none')}")
    print(f"  dimension: {status.get('dimension', 0)}")
    print(f"  row_count: {status.get('row_count', 0)}")
    print(f"  lancedb_dir: {status.get('lancedb_dir', '')}")
    return 0


def _cmd_test_embedding(argv: list[str]) -> int:
    """Test SiliconFlow embedding API availability and dimension."""
    text = argv[0] if argv else "这是一个测试文本，用于验证 embedding API"
    from eduflow.memory.embeddings import get_embedding_provider
    provider = get_embedding_provider()
    print(f"Backend: {provider.backend}")
    print(f"Dimension: {provider.dimension}")
    if provider.backend == "dummy":
        print("未配置 SILICONFLOW_API_KEY，使用 DummyProvider")
        return 1
    print(f"Encoding: {text[:80]}")
    vec = provider.encode(text)
    print(f"Result dim: {len(vec)}")
    norm = sum(x * x for x in vec) ** 0.5
    print(f"L2 norm: {norm:.6f}")
    if len(vec) > 5:
        print(f"First 5: {[round(x, 6) for x in vec[:5]]}")
    print("✅ Embedding API 正常")
    return 0


# ── Phase 1: Scope Aliases ─────────────────────────────────────────────

def _cmd_alias(argv: list[str]) -> int:
    rest = list(argv)
    if not rest:
        return usage_error("usage: eduflow memory alias <add|list|deactivate> ...")
    sub = rest[0]
    if sub == "add":
        return _cmd_alias_add(rest[1:])
    if sub == "list":
        return _cmd_alias_list(rest[1:])
    if sub == "deactivate":
        return _cmd_alias_deactivate(rest[1:])
    return usage_error(f"unknown alias subcommand: {sub}")


def _cmd_alias_add(argv: list[str]) -> int:
    rest = list(argv)
    if len(rest) < 2:
        return usage_error("usage: eduflow memory alias add <alias> <target_scope> [--kind-filter <kind>]")
    alias = rest.pop(0)
    target_scope = rest.pop(0)
    kind_filter = pop_flag(rest, "--kind-filter") or ""

    from eduflow.memory.scope_aliases import add_alias
    add_alias(alias, target_scope, kind_filter=kind_filter)
    print(f"Alias added: {alias} → {target_scope}")
    return 0


def _cmd_alias_list(argv: list[str]) -> int:
    from eduflow.memory.scope_aliases import list_aliases
    aliases = list_aliases(active_only=True)
    if not aliases:
        print("No active aliases.")
        return 0
    for a in aliases:
        alias_v = a.get("alias", "")
        target = a.get("target_scope", "")
        kf = a.get("kind_filter", "")
        kf_str = f" (kind={kf})" if kf else ""
        print(f"  {alias_v} → {target}{kf_str}")
    return 0


def _cmd_alias_deactivate(argv: list[str]) -> int:
    rest = list(argv)
    if not rest:
        return usage_error("usage: eduflow memory alias deactivate <alias>")
    alias = rest[0]
    from eduflow.memory.scope_aliases import deactivate_alias
    ok = deactivate_alias(alias)
    if ok:
        print(f"Deactivated alias: {alias}")
    else:
        print(f"Alias not found or already inactive: {alias}")
    return 0


# ── Phase 3: Candidates ────────────────────────────────────────────────

def _cmd_candidate(argv: list[str]) -> int:
    rest = list(argv)
    if not rest or rest[0] != "add":
        return usage_error("usage: eduflow memory candidate add <scope> <kind> \"<content>\" [options]")
    return _cmd_candidate_add(rest[1:])


def _cmd_candidate_add(argv: list[str]) -> int:
    rest = list(argv)
    if len(rest) < 3:
        return usage_error(
            "usage: eduflow memory candidate add <scope> <kind> \"<content>\" "
            "[--source <type>] [--reason \"<reason>\"] [--layer <layer>]"
        )
    scope = rest.pop(0)
    kind = rest.pop(0)
    content = rest.pop(0)

    source = pop_flag(rest, "--source") or "manual"
    reason = pop_flag(rest, "--reason") or ""
    layer = pop_flag(rest, "--layer") or "episode"

    from eduflow.memory.candidates import add_candidate
    cid = add_candidate(
        scope=scope, kind=kind, content=content,
        source_type=source, reason=reason, layer=layer,
    )
    print(f"Created candidate: {cid}")
    return 0


def _cmd_candidates(argv: list[str]) -> int:
    rest = list(argv)
    scope = pop_flag(rest, "--scope")
    status = pop_flag(rest, "--status") or "proposed"
    source = pop_flag(rest, "--source")
    limit = int(pop_flag(rest, "--limit") or "50")
    # --expire is a side-effecting housekeeping action: mark any
    # proposed candidates past their expires_at as rejected, then
    # continue with the normal list. We surface the count so the
    # operator sees what changed.
    expire_mode = "--expire" in rest
    if expire_mode:
        rest = [a for a in rest if a != "--expire"]
        from eduflow.memory.candidates import expire_stale_candidates
        expired_count = expire_stale_candidates()
        print(f"Expired {expired_count} stale candidate(s).")

    from eduflow.memory.candidates import list_candidates
    candidates = list_candidates(
        scope=scope or None, status=status or None,
        source_type=source or None, limit=limit,
    )
    if not candidates:
        print("No candidates found.")
        return 0
    for c in candidates:
        cid = c.get("candidate_id", "")
        kind_v = c.get("proposed_kind", "")
        scope_v = c.get("proposed_scope", "")
        cstatus = c.get("review_status", "")
        src_type = c.get("source_type", "")
        content_v = c.get("content", "")[:80]
        print(f"  [{cid}] [{kind_v}] scope={scope_v} status={cstatus} source={src_type}")
        print(f"    {content_v}")
    return 0


def _cmd_promote(argv: list[str]) -> int:
    rest = list(argv)
    if not rest:
        return usage_error("usage: eduflow memory promote <candidate_id> [--reviewer <name>] [--yes]")
    cid = rest.pop(0)
    reviewer = pop_flag(rest, "--reviewer") or ""
    auto_yes = pop_bool_flag(rest, "--yes")

    from eduflow.memory.candidates import get_candidate, promote_candidate
    candidate = get_candidate(cid)
    if candidate is None:
        print(f"Candidate not found: {cid}", file=sys.stderr)
        return 1

    # Preview
    scope = candidate.get("proposed_scope", "")
    kind = candidate.get("proposed_kind", "")
    layer = candidate.get("proposed_layer", "")
    content = candidate.get("content", "")[:120]
    print(f"Promote candidate {cid}:")
    print(f"  scope={scope}  kind={kind}  layer={layer}")
    print(f"  content: {content}")

    if not auto_yes:
        try:
            answer = input("Proceed? [y/N] ").strip().lower()
        except (EOFError, OSError):
            # Non-interactive (tests, piped stdin) — proceed without prompt
            answer = "y"
        if answer != "y":
            print("Aborted.")
            return 0

    try:
        mid = promote_candidate(cid, reviewer=reviewer)
        print(f"Promoted candidate {cid} → memory item {mid}")
        _audit_log("promote", {"candidate_id": cid, "memory_id": mid, "reviewer": reviewer})
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


def _cmd_reject(argv: list[str]) -> int:
    rest = list(argv)
    if not rest:
        return usage_error("usage: eduflow memory reject <candidate_id> [--reason \"<reason>\"] [--yes]")
    cid = rest.pop(0)
    reason = pop_flag(rest, "--reason") or ""
    auto_yes = pop_bool_flag(rest, "--yes")

    from eduflow.memory.candidates import get_candidate, reject_candidate
    candidate = get_candidate(cid)
    if candidate is None:
        print(f"Candidate not found: {cid}", file=sys.stderr)
        return 1

    # Preview
    scope = candidate.get("proposed_scope", "")
    kind = candidate.get("proposed_kind", "")
    content = candidate.get("content", "")[:120]
    print(f"Reject candidate {cid}:")
    print(f"  scope={scope}  kind={kind}")
    print(f"  content: {content}")
    if reason:
        print(f"  reason: {reason}")

    if not auto_yes:
        try:
            answer = input("Proceed? [y/N] ").strip().lower()
        except (EOFError, OSError):
            answer = "y"
        if answer != "y":
            print("Aborted.")
            return 0

    ok = reject_candidate(cid, reason=reason)
    if ok:
        print(f"Rejected candidate: {cid}")
        _audit_log("reject", {"candidate_id": cid, "reason": reason})
    else:
        print(f"Candidate not found or not in 'proposed' status: {cid}")
    return 0


# ── Obsidian Export ────────────────────────────────────────────────────

def _cmd_export(argv: list[str]) -> int:
    rest = list(argv)
    if not rest or rest[0] == "--all":
        scope = pop_flag(rest, "--scope") if rest else None
        task = pop_flag(rest, "--task") if rest else None
        from eduflow.memory.obsidian_export import export_all
        try:
            counts = export_all(scope=scope or None, task_id=task or None)
            print("Export complete:")
            print(f"  constraints: {counts.get('constraints', 0)}")
            print(f"  capsules:    {counts.get('capsules', 0)}")
            print(f"  items:       {counts.get('items', 0)}")
            print(f"  archive:     {counts.get('archive', 0)}")
            print(f"  candidates:  {counts.get('candidates', 0)}")
            from eduflow.memory.obsidian_export import export_root
            print(f"  → {export_root()}")
        except Exception as e:
            print(f"Export failed: {e}", file=sys.stderr)
            return 1
        return 0
    if rest[0] == "status":
        from eduflow.memory.obsidian_export import export_status
        status = export_status()
        print(f"Last export: {status.get('last_export', 'never')}")
        print("File counts:")
        for k, v in status.get("file_counts", {}).items():
            print(f"  {k}: {v}")
        log_tail = status.get("log_tail", [])
        if log_tail:
            print("Recent log:")
            for line in log_tail:
                print(f"  {line}")
        return 0
    if rest[0] == "--scope":
        scope = pop_flag(rest, "--scope")
        task = pop_flag(rest, "--task")
        from eduflow.memory.obsidian_export import export_all
        try:
            counts = export_all(scope=scope or None, task_id=task or None)
            print(f"Exported (scope={scope}): {counts}")
        except Exception as e:
            print(f"Export failed: {e}", file=sys.stderr)
            return 1
        return 0
    if rest[0] == "--task":
        task = pop_flag(rest, "--task")
        from eduflow.memory.obsidian_export import export_all
        try:
            counts = export_all(task_id=task or None)
            print(f"Exported (task={task}): {counts}")
        except Exception as e:
            print(f"Export failed: {e}", file=sys.stderr)
            return 1
        return 0
    return usage_error("usage: eduflow memory export [--all] [--scope <scope>] [--task <task_id>] | export status")


# ── Debug / Injection Check ──────────────────────────────────────

def _cmd_inject_check(argv: list[str]) -> int:
    """Simulate Memory Packet injection for a given agent + message.

    Usage: eduflow memory inject-check <agent> --message "..." [--task <task_id>]

    Shows what the message would look like after inject_to_send runs.
    Useful for verifying injection format without actually sending.
    """
    rest = list(argv)
    if not rest:
        return usage_error(
            "usage: eduflow memory inject-check <agent> --message \"...\" "
            "[--task <task_id>]"
        )
    agent = rest.pop(0)
    message = pop_flag(rest, "--message") or ""
    task = pop_flag(rest, "--task")

    if not message:
        return usage_error("--message is required")

    from eduflow.memory.inject import inject_to_send
    result = inject_to_send(agent, message)
    print(result)
    return 0


def _cmd_gatecheck(argv: list[str]) -> int:
    """Simulate gate check for a given agent/task/gate.

    Usage: eduflow memory gate-check <agent> --task <task_id> --gate <gate_name>

    Shows whether the gate would be allowed and which constraints
    would block it.
    """
    rest = list(argv)
    if not rest:
        return usage_error(
            "usage: eduflow memory gate-check <agent> --task <task_id> "
            "--gate <gate_name>"
        )
    agent = rest.pop(0)
    task = pop_flag(rest, "--task") or ""
    gate = pop_flag(rest, "--gate") or ""
    if not task or not gate:
        return usage_error("--task and --gate are required")

    from eduflow.memory.inject import build_gate_check
    result = build_gate_check(agent, task, gate)
    print(f"allowed: {result['allowed']}")
    blocking = result.get("blocking_constraints", [])
    if blocking:
        print(f"blocking_constraints ({len(blocking)}):")
        for b in blocking:
            bid = b.get("id", "")
            level = b.get("level", "")
            content = b.get("content", "")
            print(f"  [{bid}] [{level}] {content}")
    else:
        print("blocking_constraints: (none)")
    packet = result.get("packet", "")
    if packet:
        print(f"\npacket ({len(packet)} chars):")
        print(packet)
    return 0


def _audit_log(action: str, details: dict | None = None) -> None:
    """Append an audit record to ~/.eduflow/audit.log as JSONL.

    Fire-and-forget: never crashes the caller.
    """
    import datetime as _dt
    record = {
        "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "action": action,
        **(details or {}),
    }
    try:
        log_path = Path.home() / ".eduflow" / "audit.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ── Management commands ────────────────────────────────────────────

def _cmd_budget(argv: list[str]) -> int:
    """Budget report or per-table check/enforce."""
    rest = list(argv)
    if not rest:
        from eduflow.memory.storage_budget import budget_report
        report = budget_report()
        print(f"DB: {report['db_file']}  ({report['db_size_bytes']} bytes)")
        for name, info in report["tables"].items():
            status_line = (
                f"  {name}: {info['current']}/{info['limit']} "
                f"(headroom={info['headroom']})"
            )
            if info["over"] > 0:
                status_line += f"  *** OVER by {info['over']} ***"
            print(status_line)
        return 0

    sub = rest.pop(0)
    if sub == "check":
        if not rest:
            return usage_error("usage: eduflow memory budget check <table>")
        table = rest.pop(0)
        from eduflow.memory.storage_budget import check_budget
        info = check_budget(table)
        print(f"{info['table']}: {info['current']}/{info['limit']}  (over={info['over']}, headroom={info['headroom']})")
        return 0
    if sub == "enforce":
        if not rest:
            return usage_error("usage: eduflow memory budget enforce <table>")
        table = rest.pop(0)
        from eduflow.memory.storage_budget import enforce_budget
        result = enforce_budget(table)
        print(f"Evicted: {result['evicted']}  Remaining: {result['remaining']}  Strategy: {result['strategy']}")
        return 0

    return usage_error("usage: eduflow memory budget [check|enforce <table>]")


def _cmd_expire(argv: list[str]) -> int:
    """Run all automatic expiry scans."""
    from eduflow.memory.expiration import run_all_expirations
    result = run_all_expirations()
    print(f"Expired: {result['constraints_expired']} constraints, "
          f"{result['memories_expired']} memories, "
          f"{result['candidates_expired']} candidates "
          f"(total={result['total']})")
    return 0


def _cmd_audit(argv: list[str]) -> int:
    """Audit reports: full, scope, or retention."""
    rest = list(argv)
    if not rest:
        from eduflow.memory.audit import full_audit
        data = full_audit()
        for table, statuses in data.items():
            print(f"{table}:")
            for status, count in statuses.items():
                print(f"  {status}: {count}")
        return 0

    sub = rest.pop(0)
    if sub == "scope":
        from eduflow.memory.audit import scope_coverage_report
        report = scope_coverage_report()
        if not report:
            print("No confirmed memories found.")
            return 0
        for entry in report:
            print(f"{entry['scope']}: {entry['total']} item(s)")
            for kind, cnt in entry["kinds"].items():
                print(f"  {kind}: {cnt}")
        return 0
    if sub == "retention":
        days = int(pop_flag(rest, "--days") or "90")
        from eduflow.memory.audit import retention_report
        report = retention_report(days=days)
        print(f"Retention report ({report['period_days']}d, from {report['window_start'][:10]}):")
        print(f"  Items:      created={report['items']['created']}, "
              f"confirmed={report['items']['confirmed']}, "
              f"deprecated={report['items']['deprecated']}")
        print(f"  Candidates: proposed={report['candidates']['proposed']}, "
              f"promoted={report['candidates']['promoted']}, "
              f"rejected={report['candidates']['rejected']}")
        print(f"  Constraints: created={report['constraints']['created']}, "
              f"inactivated={report['constraints']['inactivated']}")
        return 0

    return usage_error("usage: eduflow memory audit [scope|retention [--days <N>]]")


def _cmd_cleanup(argv: list[str]) -> int:
    """Combined expire + budget enforce."""
    from eduflow.memory.expiration import run_all_expirations
    from eduflow.memory.storage_budget import enforce_budget, LIMITS
    result = run_all_expirations()
    print(f"Expired: {result['total']} total")
    for table in LIMITS:
        eresult = enforce_budget(table)
        if eresult["evicted"] > 0:
            print(f"Budget enforce {table}: evicted {eresult['evicted']}")
    print("Cleanup complete.")
    return 0


_SUBCOMMANDS = {
    "constraints": _cmd_constraints,
    "capsule": _cmd_capsule,
    "packet": _cmd_packet,
    "items": _cmd_items,
    "search": _cmd_search,
    "semantic": _cmd_search,
    "reindex": _cmd_reindex,
    "index-status": _cmd_index_status,
    "test-embedding": _cmd_test_embedding,
    "alias": _cmd_alias,
    "candidate": _cmd_candidate,
    "candidates": _cmd_candidates,
    "promote": _cmd_promote,
    "reject": _cmd_reject,
    "export": _cmd_export,
    "inject-check": _cmd_inject_check,
    "gate-check": _cmd_gatecheck,
    "budget": _cmd_budget,
    "expire": _cmd_expire,
    "audit": _cmd_audit,
    "cleanup": _cmd_cleanup,
}


def main(argv: list[str]) -> int:
    if not argv:
        return usage_error(USAGE)
    sub = argv[0]
    handler = _SUBCOMMANDS.get(sub)
    if handler is None:
        return usage_error(f"unknown memory subcommand: {sub}\n\n{USAGE}")
    return handler(argv[1:])
