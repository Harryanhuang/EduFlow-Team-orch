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
    eduflow memory daily [--limit <N>] [--scope <scope>] [--json]
"""
from __future__ import annotations

import base64
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from eduflow.util import pop_flag, pop_bool_flag, reject_extra_args, usage_error

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
    "  search \"<query>\" [--scope <scope>] [--kind <kind>] [--min-importance <1-10>] [--limit <N>] [--fts|--hybrid]\n"
    "  semantic \"<query>\"  (alias for search)\n"
    "  decay run|dry-run|status  (confidence decay over time)\n"
    "  consolidate --report [--threshold 0.85]\n"
    "  consolidate --merge <keep_id> <drop_id> [--reason \"...\"]\n"
    "  pin <memory_id>     (pin a memory; protected from budget eviction)\n"
    "  unpin <memory_id>   (remove pin)\n"
    "  pin list [--scope S] [--limit N]  (list pinned memories)\n"
    "  recall --subject <subj>  (V3 P0-3: subject hierarchy recall)\n"
    "  daily-summary write <agent> \"<summary>\" [--decision \"...\"] [--question \"...\"]\n"
    "  daily-summary show <date> <agent>\n"
    "  daily-summary list [--agent <agent>] [--limit <N>]\n"
    "  daily-summary archive [--days 30]  (delete summaries older than N days)\n"
    "  dashboard [--days 7]  (V3 P2-4: visualization dashboard)\n"
    "  agents-md --scope <scope> [--write <path>] [--overwrite] (V3 P3-2)\n"
    "  skill-evolve report [--scope S] [--min-importance 7] [--cooldown-hours 168]\n"
    "  skill-evolve accept <rule_id>\n"
    "  skill-evolve reject <rule_id> [--reason \"...\"] [--cooldown-hours N]\n"
    "  skill-evolve cooldowns\n"
    "  skill-evolve clear --yes\n"
    "  reflect <agent> \"<learning>\" [--kind <kind>] [--scope <scope>] (V3 P3-1)\n"
    "  reflect-stats [--days 30]  (reflection candidate statistics)\n"
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
    "  daily [--limit N] [--scope S] [--json]  (daily manager/Hermes review summary; read-only; --json for programmatic output)\n"
    "\n"
    "Sensitive data (encrypted):\n"
    "  sensitive setup            (set password + 3 security questions)\n"
    "  sensitive unlock <password> (unlock for 60 min)\n"
    "  sensitive lock             (immediate lock)\n"
    "  sensitive status           (check lock state)\n"
    "  sensitive change-password  (change password)\n"
    "  sensitive recover          (reset password via security questions)\n"
    "  sensitive add <scope> <kind> \"<content>\" [--by <agent>]\n"
    "  sensitive get <memory_id>\n"
    "  sensitive list [--scope <scope>] [--kind <kind>] [--limit <N>]\n"
    "  sensitive search \"<query>\" [--limit <N>]\n"
    "  sensitive delete <memory_id>\n"
    "  sensitive export           (encrypted export to Obsidian)\n"
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
            "[--min-importance <1-10>] [--limit <N>] [--fts] [--hybrid]"
        )
    query = rest.pop(0)
    scope = pop_flag(rest, "--scope")
    kind = pop_flag(rest, "--kind")
    status = pop_flag(rest, "--status") or "confirmed"
    limit = int(pop_flag(rest, "--limit") or "5")
    min_importance = int(pop_flag(rest, "--min-importance") or "0")
    fts_mode = "--fts" in rest
    hybrid_mode = "--hybrid" in rest
    if fts_mode:
        rest = [a for a in rest if a != "--fts"]
    if hybrid_mode:
        rest = [a for a in rest if a != "--hybrid"]

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

    if hybrid_mode:
        from eduflow.memory.search import hybrid_search
        results = hybrid_search(
            query, scope=scope or None, kind=kind or None,
            status=status or None, limit=limit,
        )
        if not results:
            print(f"No memories found matching: {query}")
            return 0
        print(f"Hybrid (FTS+Vector) search results for \"{query}\":")
        for m in results:
            mid = m.get("id", "")
            kind_v = m.get("kind", "")
            scope_v = m.get("scope", "")
            sources = m.get("_sources", "?")
            summary = m.get("summary", "") or m.get("content", "")[:80]
            print(f"  [{sources}] [{mid}] [{kind_v}] scope={scope_v}")
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
        return usage_error(
            "usage: eduflow memory promote <candidate_id> "
            "[--reviewer <name>] [--hermes-can-promote] [--yes]"
        )
    cid = rest.pop(0)
    reviewer = pop_flag(rest, "--reviewer") or ""
    auto_yes = pop_bool_flag(rest, "--yes")
    hermes_can_promote = pop_bool_flag(rest, "--hermes-can-promote")

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
    if hermes_can_promote:
        print("  hermes_can_promote: True (manager explicitly authorized)")

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
        mid = promote_candidate(
            cid, reviewer=reviewer, hermes_can_promote=hermes_can_promote,
        )
        print(f"Promoted candidate {cid} → memory item {mid}")
        _audit_log("promote", {
            "candidate_id": cid, "memory_id": mid,
            "reviewer": reviewer, "hermes_can_promote": hermes_can_promote,
        })
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
    usage = (
        "usage: eduflow memory inject-check <agent> --message \"...\" "
        "[--task <task_id>]"
    )
    rest = list(argv)
    if not rest:
        return usage_error(usage)
    agent = rest.pop(0)
    message = pop_flag(rest, "--message") or ""
    task_requested = "--task" in rest
    task = pop_flag(rest, "--task")
    if task_requested and (task is None or not task.strip()):
        return usage_error("--task requires a non-empty value\n" + usage)
    if task is not None:
        task = task.strip()
    if (rc := reject_extra_args(rest, usage)) is not None:
        return rc

    if not message:
        return usage_error("--message is required")

    from eduflow.memory.inject import inject_to_send
    result = inject_to_send(agent, message, task_id=task)
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


def _cmd_daily(argv: list[str]) -> int:
    """Daily memory review summary for manager + Hermes handoff.

    Read-only. Outputs:
      - proposed candidate backlog (by source_type)
      - stale candidates count
      - high-priority manager corrections
      - workflow-level failure patterns
      - suggested review order
      - Hermes handoff section

    Usage:
      eduflow memory daily [--limit N] [--scope S] [--json]

    --json  emit a single JSON object on stdout for programmatic
            consumption (Hermes handoff pipelines, monitoring, etc.).
            Default is human-readable text.
    """
    import datetime as _dt
    rest = list(argv)
    limit = int(pop_flag(rest, "--limit") or "50")
    scope_filter = pop_flag(rest, "--scope") or ""
    json_mode = pop_bool_flag(rest, "--json")

    from eduflow.memory.candidates import list_candidates
    proposed = list_candidates(status="proposed", limit=limit)
    if scope_filter:
        proposed = [c for c in proposed if c.get("proposed_scope") == scope_filter]

    today = _dt.date.today().isoformat()

    # Compute derived sections first (so --json and human-readable share logic).
    by_source: dict[str, int] = {}
    for c in proposed:
        src = c.get("source_type") or "unknown"
        by_source[src] = by_source.get(src, 0) + 1
    total = sum(by_source.values())

    now = _dt.datetime.now(_dt.timezone.utc).isoformat()
    soon = (_dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(days=7)).isoformat()
    stale = [c for c in proposed if c.get("expires_at", "") < soon]

    high_mgr = [
        c for c in proposed
        if c.get("source_type") == "manager_correction"
        and (
            "high" in (c.get("risk_flags") or [])
            or c.get("proposed_kind") == "role_rule"
        )
    ]

    wf_patterns = [
        c for c in proposed
        if c.get("source_type") in ("task_failure_pattern", "closeout_anomaly")
    ]

    high_impact_kinds = {"workflow_rule", "role_rule", "runtime_rule", "decision", "preference", "handoff"}
    def _priority(c: dict) -> tuple:
        is_high_impact = c.get("proposed_kind") in high_impact_kinds
        is_high_severity = "high" in (c.get("risk_flags") or [])
        is_pattern = c.get("source_type") in ("task_failure_pattern", "closeout_anomaly", "manager_correction")
        return (0 if is_pattern else 1, 0 if is_high_severity else 1, 0 if is_high_impact else 1)
    sorted_cands = sorted(proposed, key=_priority)

    obsidian_ready = [
        c for c in proposed
        if c.get("source_type") in ("manager_correction", "task_failure_pattern")
    ]
    conflict_candidates = [
        c for c in proposed
        if "conflict" in (c.get("content", "") or "").lower()
        or c.get("source_type") == "closeout_anomaly"
    ]

    # ── JSON output mode ────────────────────────────────────────
    if json_mode:
        def _candidate_summary(c: dict) -> dict:
            return {
                "candidate_id": c.get("candidate_id", ""),
                "source_type": c.get("source_type", ""),
                "proposed_scope": c.get("proposed_scope", ""),
                "proposed_kind": c.get("proposed_kind", ""),
                "proposed_layer": c.get("proposed_layer", ""),
                "content_preview": (c.get("content", "") or "")[:120],
                "expires_at": c.get("expires_at", ""),
                "risk_flags": c.get("risk_flags") or [],
            }
        payload = {
            "date": today,
            "generated_at": now,
            "scope_filter": scope_filter or None,
            "limits": {"candidate_limit": limit},
            "totals": {
                "proposed": total,
                "by_source_type": by_source,
                "stale_within_7d": len(stale),
                "high_priority_manager_corrections": len(high_mgr),
                "workflow_patterns": len(wf_patterns),
            },
            "stale": [_candidate_summary(c) for c in stale],
            "high_priority_manager_corrections": [_candidate_summary(c) for c in high_mgr],
            "workflow_patterns": [_candidate_summary(c) for c in wf_patterns],
            "suggested_review_order": [_candidate_summary(c) for c in sorted_cands[:10]],
            "hermes_handoff": {
                "obsidian_backlog_candidates": len(obsidian_ready),
                "conflict_or_anomaly_candidates": len(conflict_candidates),
                "next_actions": [
                    "eduflow memory export",
                    'eduflow task dispatch Hermes "<knowledge task>"',
                ],
            },
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    # ── Human-readable output mode (default) ─────────────────────
    print(f"📅 Daily Memory Review ({today})")
    print()

    print(f"📊 Proposed candidate backlog: {total}")
    for src, cnt in sorted(by_source.items(), key=lambda x: -x[1]):
        print(f"   - {src}: {cnt}")
    print()

    if stale:
        print(f"⏰ Stale/expiring (≤7d): {len(stale)}")
        for c in stale[:5]:
            cid = c.get("candidate_id", "")
            exp = c.get("expires_at", "")[:10]
            content = (c.get("content", "") or "")[:60]
            print(f"   - {cid}  expires={exp}  {content}")
        print()

    if high_mgr:
        print(f"🔥 High-priority manager corrections: {len(high_mgr)}")
        for c in high_mgr[:5]:
            cid = c.get("candidate_id", "")
            scope_v = c.get("proposed_scope", "")
            content = (c.get("content", "") or "")[:60]
            print(f"   - {cid}  scope={scope_v}  {content}")
        print()

    if wf_patterns:
        print(f"🔁 Workflow-level patterns/anomalies: {len(wf_patterns)}")
        for c in wf_patterns[:5]:
            cid = c.get("candidate_id", "")
            scope_v = c.get("proposed_scope", "")
            src = c.get("source_type", "")
            content = (c.get("content", "") or "")[:60]
            print(f"   - {cid}  scope={scope_v}  source={src}  {content}")
        print()

    print("📋 Suggested review order (top 5):")
    for i, c in enumerate(sorted_cands[:5], 1):
        cid = c.get("candidate_id", "")
        src = c.get("source_type", "")
        kind = c.get("proposed_kind", "")
        content = (c.get("content", "") or "")[:60]
        print(f"   {i}. {cid}  {src}  kind={kind}")
        print(f"      {content}")
    print()

    print("🤝 Hermes handoff section:")
    print(f"   - {len(obsidian_ready)} candidate(s) ready for Obsidian _memory-candidate-backlog/ export")
    print(f"   - {len(conflict_candidates)} conflict/anomaly candidate(s) for _待复核冲突/")
    print("   - Hermes action: run `eduflow memory export` after review,")
    print("     then dispatch Hermes with `eduflow task dispatch Hermes \"<task>\"`")
    print("     using the export root as the brief attachment.")
    return 0


# ── Sensitive data commands ─────────────────────────────────────────

def _cmd_sensitive(argv: list[str]) -> int:
    """Manage encrypted sensitive memories."""
    if not argv:
        return usage_error(
            "usage: eduflow memory sensitive <setup|unlock|lock|status|change-password|recover|add|get|list|search|delete|export> ..."
        )
    sub = argv[0]
    handlers = {
        "setup": _cmd_sensitive_setup,
        "unlock": _cmd_sensitive_unlock,
        "lock": _cmd_sensitive_lock,
        "status": _cmd_sensitive_status,
        "change-password": _cmd_sensitive_change_password,
        "recover": _cmd_sensitive_recover,
        "add": _cmd_sensitive_add,
        "get": _cmd_sensitive_get,
        "list": _cmd_sensitive_list,
        "search": _cmd_sensitive_search,
        "delete": _cmd_sensitive_delete,
        "export": _cmd_sensitive_export,
    }
    handler = handlers.get(sub)
    if handler is None:
        return usage_error(f"unknown sensitive subcommand: {sub}")
    return handler(argv[1:])


def _cmd_sensitive_setup(argv: list[str]) -> int:
    """Set up password + 3 security questions."""
    import getpass
    from eduflow.memory.sensitive import is_configured, setup_password

    if is_configured():
        print("⚠️  Sensitive storage already configured. Use 'change-password' to update.")
        return 1

    print("🔒 Setting up sensitive storage")
    print()

    pw = getpass.getpass("Enter new password (min 6 chars): ")
    if len(pw) < 6:
        print("❌ Password must be at least 6 characters")
        return 1
    pw2 = getpass.getpass("Confirm password: ")
    if pw != pw2:
        print("❌ Passwords do not match")
        return 1

    print()
    print("Set up 3 security questions for password recovery:")
    print("(You'll need to answer 2 of 3 correctly to reset a forgotten password)")
    print()

    questions = []
    for i in range(1, 4):
        q = input(f"Question {i}: ").strip()
        a = getpass.getpass(f"Answer {i}: ").strip()
        questions.append({"question": q, "answer": a})

    setup_password(pw, questions)
    print()
    print("✅ Sensitive storage configured!")
    print("⚠️  Remember your password. Security questions are for emergency recovery only.")
    return 0


def _cmd_sensitive_unlock(argv: list[str]) -> int:
    """Unlock sensitive data for 60 minutes."""
    import getpass
    from eduflow.memory.sensitive import unlock

    pw = argv[0] if argv else getpass.getpass("Enter password: ")
    try:
        result = unlock(pw)
        print(f"🔓 Unlocked (expires in {result['expires_in'] // 60} min)")
        return 0
    except ValueError:
        print("❌ Invalid password")
        return 1
    except RuntimeError as e:
        print(f"❌ {e}")
        return 1


def _cmd_sensitive_lock(argv: list[str]) -> int:
    """Immediately lock sensitive data."""
    from eduflow.memory.sensitive import lock
    lock()
    print("🔒 Locked")
    return 0


def _cmd_sensitive_status(argv: list[str]) -> int:
    """Check lock status."""
    from eduflow.memory.sensitive import status
    s = status()
    if not s["configured"]:
        print("⚪ Not configured. Run: eduflow memory sensitive setup")
    elif s["unlocked"]:
        mins = s["expires_in"] // 60
        print(f"🔓 Unlocked ({mins} min remaining)")
    else:
        print("🔒 Locked")
    return 0


def _cmd_sensitive_change_password(argv: list[str]) -> int:
    """Change password."""
    import getpass
    from eduflow.memory.sensitive import change_password

    old_pw = getpass.getpass("Enter current password: ")
    new_pw = getpass.getpass("Enter new password (min 6 chars): ")
    if len(new_pw) < 6:
        print("❌ Password must be at least 6 characters")
        return 1
    new_pw2 = getpass.getpass("Confirm new password: ")
    if new_pw != new_pw2:
        print("❌ Passwords do not match")
        return 1

    try:
        change_password(old_pw, new_pw)
        print("✅ Password changed. All sensitive data re-encrypted.")
        return 0
    except ValueError as e:
        print(f"❌ {e}")
        return 1


def _cmd_sensitive_recover(argv: list[str]) -> int:
    """Reset password via security questions."""
    import getpass
    from eduflow.memory.sensitive import get_security_questions, recover

    questions = get_security_questions()
    if not questions:
        print("❌ No security questions configured")
        return 1

    print("Answer the following questions (2 of 3 required):")
    print()
    answers = {}
    for i, q in enumerate(questions):
        a = getpass.getpass(f"Q{i+1}: {q}\nA{i+1}: ").strip()
        answers[f"q{i}"] = a

    new_pw = getpass.getpass("\nEnter new password (min 6 chars): ")
    if len(new_pw) < 6:
        print("❌ Password must be at least 6 characters")
        return 1
    new_pw2 = getpass.getpass("Confirm new password: ")
    if new_pw != new_pw2:
        print("❌ Passwords do not match")
        return 1

    try:
        recover(answers, new_pw)
        print("✅ Password reset. All sensitive data re-encrypted.")
        return 0
    except ValueError as e:
        print(f"❌ {e}")
        return 1


def _cmd_sensitive_add(argv: list[str]) -> int:
    """Add a sensitive memory item."""
    if len(argv) < 3:
        return usage_error(
            'usage: eduflow memory sensitive add <scope> <kind> "<content>" [--by <agent>]'
        )
    scope = argv[0]
    kind = argv[1]
    content = argv[2]
    created_by = pop_flag(argv[3:], "--by") or ""

    from eduflow.memory.sensitive import add_sensitive
    try:
        mid = add_sensitive(scope, kind, content, created_by=created_by)
        print(f"🔐 Encrypted sensitive memory: {mid}")
        return 0
    except PermissionError as e:
        print(f"🔒 {e}")
        return 1


def _cmd_sensitive_get(argv: list[str]) -> int:
    """Get a sensitive memory item."""
    if not argv:
        return usage_error("usage: eduflow memory sensitive get <memory_id>")
    mid = argv[0]

    from eduflow.memory.sensitive import get_sensitive
    try:
        m = get_sensitive(mid)
        if not m:
            print(f"Not found: {mid}")
            return 0
        for key in ("id", "scope", "kind", "content", "status", "created_by", "created_at"):
            val = m.get(key, "")
            if val:
                print(f"  {key}: {val}")
        return 0
    except PermissionError as e:
        print(f"🔒 {e}")
        return 1


def _cmd_sensitive_list(argv: list[str]) -> int:
    """List sensitive memory items."""
    rest = list(argv)
    scope = pop_flag(rest, "--scope")
    kind = pop_flag(rest, "--kind")
    limit = int(pop_flag(rest, "--limit") or "50")

    from eduflow.memory.sensitive import list_sensitive
    try:
        items = list_sensitive(scope=scope, kind=kind, limit=limit)
        if not items:
            print("No sensitive memories found.")
            return 0
        print(f"Sensitive memories ({len(items)}):")
        for m in items:
            print(f"  [{m['id']}] [{m['kind']}] scope={m['scope']} ({m['created_at'][:10]})")
        return 0
    except PermissionError as e:
        print(f"🔒 {e}")
        return 1


def _cmd_sensitive_search(argv: list[str]) -> int:
    """Search sensitive memories by content."""
    if not argv:
        return usage_error('usage: eduflow memory sensitive search "<query>" [--limit <N>]')
    rest = list(argv)
    query = rest[0]
    limit = int(pop_flag(rest[1:], "--limit") or "20")

    from eduflow.memory.sensitive import search_sensitive
    try:
        results = search_sensitive(query, limit=limit)
        if not results:
            print("No matches found.")
            return 0
        print(f"Search results ({len(results)}):")
        for m in results:
            content = m.get("content", "")[:80]
            print(f"  [{m['id']}] [{m['kind']}] scope={m['scope']}")
            print(f"    {content}")
        return 0
    except PermissionError as e:
        print(f"🔒 {e}")
        return 1


def _cmd_sensitive_delete(argv: list[str]) -> int:
    """Delete a sensitive memory item."""
    if not argv:
        return usage_error("usage: eduflow memory sensitive delete <memory_id>")
    mid = argv[0]

    from eduflow.memory.sensitive import delete_sensitive
    try:
        ok = delete_sensitive(mid)
        if ok:
            print(f"🗑️  Deleted: {mid}")
        else:
            print(f"Not found: {mid}")
        return 0
    except PermissionError as e:
        print(f"🔒 {e}")
        return 1


def _cmd_sensitive_export(argv: list[str]) -> int:
    """Export sensitive memories to encrypted files in Obsidian."""
    from eduflow.memory.sensitive import export_sensitive_json, is_unlocked
    from eduflow.memory.obsidian_export import export_root

    if not is_unlocked():
        print("🔒 Sensitive storage is locked. Unlock first: eduflow memory sensitive unlock")
        return 1

    try:
        import hashlib
        from cryptography.fernet import Fernet

        items = export_sensitive_json()
        if not items:
            print("No sensitive memories to export.")
            return 0

        root = export_root()
        sensitive_dir = root / "sensitive"
        sensitive_dir.mkdir(exist_ok=True)

        # Derive export key from same password session
        from eduflow.memory.sensitive import _derived_key
        export_key = base64.urlsafe_b64encode(hashlib.sha256(_derived_key + b"export").digest())
        f = Fernet(export_key)

        # Encrypt and write
        data = json.dumps(items, ensure_ascii=False, indent=2).encode("utf-8")
        encrypted = f.encrypt(data)
        (sensitive_dir / "sensitive-items.enc").write_bytes(encrypted)

        # Write README
        (sensitive_dir / "README.md").write_text(
            "# 敏感数据导出\n\n"
            "此文件夹包含加密的敏感记忆。\n\n"
            "## 解密方法\n\n"
            "```bash\n"
            "eduflow memory sensitive unlock\n"
            "# 然后使用 Python Fernet 解密\n"
            "```\n\n"
            f"导出时间: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
            f"条目数: {len(items)}\n",
            encoding="utf-8",
        )

        print(f"🔐 Exported {len(items)} sensitive items to {sensitive_dir}")
        print("   - sensitive-items.enc (encrypted)")
        print("   - README.md")
        return 0

    except PermissionError as e:
        print(f"🔒 {e}")
        return 1
    except ImportError:
        print("❌ cryptography package required: pip install cryptography")
        return 1


# ── Decay commands ──────────────────────────────────────────────────

def _cmd_decay(argv: list[str]) -> int:
    """Run confidence decay on memory items."""
    if not argv:
        return usage_error(
            "usage: eduflow memory decay <run|dry-run|status>"
        )
    sub = argv[0]
    if sub == "run":
        return _cmd_decay_run(argv[1:])
    if sub == "dry-run":
        return _cmd_decay_run(argv[1:] + ["--dry-run"])
    if sub == "status":
        return _cmd_decay_status(argv[1:])
    return usage_error(f"unknown decay subcommand: {sub}")


def _cmd_decay_run(argv: list[str]) -> int:
    """Apply decay to all confirmed memories."""
    from eduflow.memory.decay import decay_batch
    dry_run = "--dry-run" in argv
    result = decay_batch(dry_run=dry_run)
    label = "[dry-run] " if dry_run else ""
    print(f"{label}decay: {result['updated']} updated, {result['skipped']} skipped, {result['total']} total")
    return 0


def _cmd_decay_status(argv: list[str]) -> int:
    """Show decay summary statistics."""
    from eduflow.memory.db import get_conn, init_schema
    init_schema()
    conn = get_conn()
    row = conn.execute(
        "SELECT COUNT(*) AS total, AVG(confidence) AS avg_conf, "
        "MIN(confidence) AS min_conf, MAX(confidence) AS max_conf "
        "FROM memory_items WHERE status='confirmed'"
    ).fetchone()
    total = row["total"] or 0
    avg = row["avg_conf"] or 0.0
    print(f"Confirmed memories: {total}")
    print(f"Average confidence: {avg:.3f}")
    print(f"Min/Max: {row['min_conf']:.3f} / {row['max_conf']:.3f}")
    return 0


# ── Consolidate commands ────────────────────────────────────────────

def _cmd_consolidate(argv: list[str]) -> int:
    """Detect and merge similar memories."""
    if not argv:
        return usage_error(
            'usage: eduflow memory consolidate --report [--threshold <0.0-1.0>]\n'
            '       eduflow memory consolidate --merge <keep_id> <drop_id> [--reason "..."]'
        )

    if "--report" in argv:
        threshold = 0.85
        if "--threshold" in argv:
            i = argv.index("--threshold")
            if i + 1 < len(argv):
                threshold = float(argv[i + 1])
        return _cmd_consolidate_report(threshold)

    if "--merge" in argv:
        i = argv.index("--merge")
        if i + 2 >= len(argv):
            return usage_error(
                "usage: eduflow memory consolidate --merge <keep_id> <drop_id>"
            )
        keep_id = argv[i + 1]
        drop_id = argv[i + 2]
        reason = ""
        if "--reason" in argv:
            j = argv.index("--reason")
            if j + 1 < len(argv):
                reason = argv[j + 1]
        return _cmd_consolidate_merge(keep_id, drop_id, reason)

    return usage_error("usage: eduflow memory consolidate --report | --merge ...")


def _cmd_consolidate_report(threshold: float) -> int:
    """Generate consolidation report."""
    from eduflow.memory.consolidate import find_similar_pairs
    pairs = find_similar_pairs(threshold=threshold, limit_pairs=20)
    if not pairs:
        print(f"No similar pairs found (threshold={threshold}).")
        print("(vector store may be unavailable or no memories indexed)")
        return 0
    print(f"Found {len(pairs)} similar pair(s) (threshold={threshold}):")
    for p in pairs[:10]:
        print(f"\n  Score: {p['score']:.3f}")
        print(f"    [{p['id_a']}] {p['content_a'][:80]}")
        print(f"    [{p['id_b']}] {p['content_b'][:80]}")
        print(f"  Merge: eduflow memory consolidate --merge {p['id_a']} {p['id_b']}")
    return 0


def _cmd_consolidate_merge(keep_id: str, drop_id: str, reason: str) -> int:
    """Merge two memories."""
    from eduflow.memory.consolidate import merge_memories
    try:
        result = merge_memories(keep_id, drop_id, reason=reason)
        print(f"✅ Merged: keep={result['keep_id']}, drop={result['drop_id']}")
        return 0
    except ValueError as e:
        print(f"❌ {e}")
        return 1


# ── Pin commands ─────────────────────────────────────────────────────

def _cmd_pin(argv: list[str]) -> int:
    """Pin/unpin/list pinned memories."""
    if not argv:
        return usage_error(
            "usage: eduflow memory pin <memory_id>\n"
            "       eduflow memory unpin <memory_id>\n"
            "       eduflow memory pin list [--scope <scope>] [--limit <N>]"
        )
    if argv[0] == "list":
        return _cmd_pin_list(argv[1:])
    if argv[0] == "unpin":
        return _cmd_pin_unpin(argv[1:])
    # Default: pin the given memory_id
    return _cmd_pin_do(argv)


def _cmd_pin_do(memory_ids: list[str]) -> int:
    """Pin one or more memories."""
    from eduflow.memory.items import pin_memory
    if not memory_ids:
        return usage_error("usage: eduflow memory pin <memory_id> [<memory_id> ...]")
    pinned_count = 0
    for mid in memory_ids:
        if pin_memory(mid):
            pinned_count += 1
            print(f"📌 Pinned: {mid}")
        else:
            print(f"  Already pinned or not found: {mid}")
    print(f"\nTotal pinned this call: {pinned_count}")
    return 0


def _cmd_pin_unpin(argv: list[str]) -> int:
    """Unpin a memory."""
    from eduflow.memory.items import unpin_memory
    if not argv:
        return usage_error("usage: eduflow memory unpin <memory_id>")
    mid = argv[0]
    if unpin_memory(mid):
        print(f"✅ Unpinned: {mid}")
        return 0
    print(f"  Not pinned or not found: {mid}")
    return 1


def _cmd_pin_list(argv: list[str]) -> int:
    """List pinned memories."""
    from eduflow.memory.items import list_pinned_memories
    scope = pop_flag(argv, "--scope")
    limit = int(pop_flag(argv, "--limit") or "50")
    items = list_pinned_memories(scope=scope or None, limit=limit)
    if not items:
        print("No pinned memories.")
        return 0
    print(f"Pinned memories ({len(items)}):")
    for m in items:
        kind = m.get("kind", "")
        scope = m.get("scope", "")
        summary = m.get("summary", "") or m.get("content", "")[:60]
        print(f"  📌 [{m['id']}] [{kind}] scope={scope}")
        print(f"     {summary}")
    return 0


# ── Recall (V3 P0-3 subject) ────────────────────────────────────────

def _cmd_recall(argv: list[str]) -> int:
    """Recall memories by subject (with parent inheritance)."""
    subject = pop_flag(argv, "--subject")
    if not subject:
        return usage_error("usage: eduflow memory recall --subject <subj> [--limit <N>]")
    limit = int(pop_flag(argv, "--limit") or "20")

    from eduflow.memory.scope_aliases import resolve_subject_scopes, get_subject_hierarchy
    from eduflow.memory.items import list_memories

    scopes = resolve_subject_scopes(subject)
    hierarchy = get_subject_hierarchy(subject)
    print(f"Subject hierarchy: {' > '.join(hierarchy)}")
    print(f"Searching scopes: {scopes}")

    # Fetch memories matching any scope in the hierarchy
    all_items: list[dict] = []
    seen: set[str] = set()
    for scope in scopes:
        items = list_memories(scope=scope, status="confirmed", limit=limit)
        for m in items:
            mid = m.get("id", "")
            if mid not in seen:
                all_items.append(m)
                seen.add(mid)

    if not all_items:
        print(f"No memories found for subject '{subject}'.")
        return 0

    print(f"\nFound {len(all_items)} memory items:")
    for m in all_items[:limit]:
        kind = m.get("kind", "")
        scope_v = m.get("scope", "")
        summary = m.get("summary", "") or m.get("content", "")[:80]
        print(f"  [{m['id']}] [{kind}] scope={scope_v}")
        print(f"    {summary}")
    return 0


# ── Daily summary (V3 P1-5) ──────────────────────────────────────────

def _cmd_daily_summary(argv: list[str]) -> int:
    """Manage daily summaries (short-term memory)."""
    if not argv:
        return usage_error(
            "usage: eduflow memory daily-summary <write|show|list|archive> ..."
        )
    sub = argv[0]
    if sub == "write":
        return _cmd_daily_summary_write(argv[1:])
    if sub == "show":
        return _cmd_daily_summary_show(argv[1:])
    if sub == "list":
        return _cmd_daily_summary_list(argv[1:])
    if sub == "archive":
        return _cmd_daily_summary_archive(argv[1:])
    return usage_error(f"unknown daily-summary subcommand: {sub}")


def _cmd_daily_summary_write(argv: list[str]) -> int:
    """Write a daily summary."""
    from datetime import date as _date

    if len(argv) < 2:
        return usage_error(
            'usage: eduflow memory daily-summary write <agent> "<summary>" '
            '[--decision "..."] [--question "..."] [--date YYYY-MM-DD]'
        )
    agent = argv[0]
    summary = argv[1]
    decisions = []
    questions = []

    # Parse --decision / --question flags (can appear multiple times)
    i = 2
    target_date = _date.today().isoformat()
    while i < len(argv):
        if argv[i] == "--decision" and i + 1 < len(argv):
            decisions.append(argv[i + 1])
            i += 2
        elif argv[i] == "--question" and i + 1 < len(argv):
            questions.append(argv[i + 1])
            i += 2
        elif argv[i] == "--date" and i + 1 < len(argv):
            target_date = argv[i + 1]
            i += 2
        else:
            i += 1

    from eduflow.memory.daily_summary import upsert_summary
    key = upsert_summary(
        target_date, agent, summary,
        key_decisions=decisions, open_questions=questions,
    )
    print(f"📅 Saved summary: {key}")
    if decisions:
        print(f"  Decisions: {len(decisions)}")
    if questions:
        print(f"  Open questions: {len(questions)}")
    return 0


def _cmd_daily_summary_show(argv: list[str]) -> int:
    """Show a single daily summary."""
    if len(argv) < 2:
        return usage_error("usage: eduflow memory daily-summary show <date> <agent>")
    date_arg = argv[0]
    agent = argv[1]
    from eduflow.memory.daily_summary import get_summary
    s = get_summary(date_arg, agent)
    if not s:
        print(f"No summary found for {date_arg} :: {agent}")
        return 0
    print(f"📅 {s['date']} :: {s['agent']}")
    print(f"  Summary: {s['summary']}")
    if s.get("key_decisions"):
        print(f"  Decisions ({len(s['key_decisions'])}):")
        for d in s["key_decisions"]:
            print(f"    - {d}")
    if s.get("open_questions"):
        print(f"  Open questions ({len(s['open_questions'])}):")
        for q in s["open_questions"]:
            print(f"    - {q}")
    print(f"  Updated: {s['updated_at']}")
    return 0


def _cmd_daily_summary_list(argv: list[str]) -> int:
    """List daily summaries."""
    from eduflow.memory.daily_summary import list_summaries
    agent = pop_flag(argv, "--agent")
    limit = int(pop_flag(argv, "--limit") or "30")
    summaries = list_summaries(agent=agent, limit=limit)
    if not summaries:
        print("No daily summaries found.")
        return 0
    print(f"Daily summaries ({len(summaries)}):")
    for s in summaries:
        date = s["date"]
        agent = s["agent"]
        summary_preview = s["summary"][:60].replace("\n", " ")
        print(f"  📅 {date} :: {agent}")
        print(f"     {summary_preview}")
    return 0


def _cmd_daily_summary_archive(argv: list[str]) -> int:
    """Archive old summaries."""
    days = int(pop_flag(argv, "--days") or "30")
    from eduflow.memory.daily_summary import archive_old_summaries
    count = archive_old_summaries(retention_days=days)
    print(f"🗑️  Archived {count} summaries older than {days} days")
    return 0


# ── Dashboard (V3 P2-4) ─────────────────────────────────────────────

def _cmd_dashboard(argv: list[str]) -> int:
    """Render the memory dashboard."""
    days = int(pop_flag(argv, "--days") or "7")
    from eduflow.memory.dashboard import render_dashboard
    print(render_dashboard(days=days))
    return 0


# ── AGENTS.md generator (V3 P3-2) ────────────────────────────────────

def _cmd_agents_md(argv: list[str]) -> int:
    """Generate AGENTS.md draft for a scope."""
    scope = pop_flag(argv, "--scope")
    if not scope:
        return usage_error(
            "usage: eduflow memory agents-md --scope <scope> [--write <path>] [--overwrite] "
            "[--min-importance 5] [--limit 50]"
        )

    write_path = pop_flag(argv, "--write")
    overwrite = pop_bool_flag(argv, "--overwrite")
    min_importance = int(pop_flag(argv, "--min-importance") or "5")
    limit = int(pop_flag(argv, "--limit") or "50")

    if write_path:
        from eduflow.memory.agents_md_gen import write_agents_md
        result = write_agents_md(
            scope, write_path,
            min_importance=min_importance, limit=limit, overwrite=overwrite,
        )
        if result["written"]:
            print(f"✅ Wrote AGENTS.md to {result['path']}")
            return 0
        elif result.get("skipped"):
            print(f"⏭️  Skipped: {result.get('reason', 'unknown')}")
            print(f"   Use --overwrite to replace: {result['path']}")
            # Still print preview
            print("\n--- Draft preview ---")
            print(result["content"][:1500])
            return 1
    else:
        from eduflow.memory.agents_md_gen import generate_agents_md
        draft = generate_agents_md(
            scope, min_importance=min_importance, limit=limit,
        )
        print(draft)
        return 0


# ── Reflect (V3 P3-1 lightweight) ────────────────────────────────────

def _cmd_reflect(argv: list[str]) -> int:
    """Submit an agent's reflection as candidate memories."""
    if len(argv) < 2:
        return usage_error(
            "usage: eduflow memory reflect <agent> \"<learning>\" "
            "[--kind <kind>] [--scope <scope>] [--reason \"...\"]\n"
            "       Multi-learning JSON: eduflow memory reflect <agent> --json '[{...}, ...]'"
        )

    agent = argv[0]
    source_ref = pop_flag(argv, "--source")

    # Parse learnings: either single from argv[1] or multi via --json
    json_mode = "--json" in argv
    if json_mode:
        try:
            json_idx = argv.index("--json")
            learnings = json.loads(argv[json_idx + 1])
        except (IndexError, json.JSONDecodeError) as e:
            print(f"❌ Invalid JSON: {e}")
            return 1
    else:
        if len(argv) < 2:
            return usage_error("missing learning content")
        learning = {
            "kind": pop_flag(argv[2:], "--kind") or "note",
            "content": argv[1],
            "proposed_scope": pop_flag(argv[2:], "--scope") or f"agent:{agent}",
            "reason": pop_flag(argv[2:], "--reason") or "",
        }
        learnings = [learning]

    from eduflow.memory.reflect import submit_reflection
    try:
        ids = submit_reflection(
            agent, learnings,
            source_ref=source_ref or "",
        )
        print(f"🤔 Reflected {len(ids)} learning(s) from agent '{agent}':")
        for cid in ids:
            print(f"  📝 {cid}")
        return 0
    except Exception as e:
        print(f"❌ {e}")
        return 1


def _cmd_reflect_stats(argv: list[str]) -> int:
    """Show reflection candidate statistics."""
    days = int(pop_flag(argv, "--days") or "30")
    from eduflow.memory.reflect import reflection_stats, list_recent_reflection_candidates

    stats = reflection_stats(days=days)
    print(f"Reflection stats (last {stats['window_days']} days):")
    print(f"  Total: {stats['total']}")
    print(f"  Promote rate: {stats['promote_rate']:.1%}")
    print("  By status:")
    for status, cnt in stats["by_status"].items():
        print(f"    {status}: {cnt}")

    # Show recent unpromoted
    recent = list_recent_reflection_candidates(days=days, limit=10)
    if recent:
        unpromoted = [c for c in recent if c["review_status"] == "proposed"]
        if unpromoted:
            print(f"\n  Pending review ({len(unpromoted)}):")
            for c in unpromoted[:5]:
                print(f"    {c['candidate_id']} [{c['proposed_kind']}] {c['content'][:50]}")
    return 0


# ── Skill evolution (V3 P3-3 skeleton) ──────────────────────────────

def _cmd_skill_evolve(argv: list[str]) -> int:
    """Skill evolution: detect frequent rules, propose AGENTS.md updates, manage cooldowns."""
    if not argv:
        return usage_error(
            "usage: eduflow memory skill-evolve <report|accept|reject|cooldowns|clear> ..."
        )

    sub = argv[0]
    if sub == "report":
        return _cmd_skill_evolve_report(argv[1:])
    if sub == "accept":
        return _cmd_skill_evolve_accept(argv[1:])
    if sub == "reject":
        return _cmd_skill_evolve_reject(argv[1:])
    if sub == "cooldowns":
        return _cmd_skill_evolve_cooldowns(argv[1:])
    if sub == "clear":
        return _cmd_skill_evolve_clear(argv[1:])
    return usage_error(f"unknown skill-evolve subcommand: {sub}")


def _cmd_skill_evolve_report(argv: list[str]) -> int:
    """Generate skill evolution suggestion report."""
    scope = pop_flag(argv, "--scope")
    min_importance = int(pop_flag(argv, "--min-importance") or "7")
    cooldown_hours = int(pop_flag(argv, "--cooldown-hours") or "168")

    from flow_memory.skill_evolution import render_suggestion_report
    print(render_suggestion_report(
        scope=scope or None,
        min_importance=min_importance,
        cooldown_hours=cooldown_hours,
    ))
    return 0


def _cmd_skill_evolve_accept(argv: list[str]) -> int:
    """Accept a suggestion (clear cooldown)."""
    if not argv:
        return usage_error("usage: eduflow memory skill-evolve accept <rule_id>")
    rule_id = argv[0]
    from flow_memory.skill_evolution import accept_suggestion
    cleared = accept_suggestion(rule_id)
    if cleared:
        print(f"✅ Cleared cooldown for {rule_id}")
    else:
        print(f"  No cooldown was active for {rule_id}")
    return 0


def _cmd_skill_evolve_reject(argv: list[str]) -> int:
    """Reject a suggestion (enter cooldown)."""
    if not argv:
        return usage_error(
            'usage: eduflow memory skill-evolve reject <rule_id> [--reason "..."] [--cooldown-hours N]'
        )
    rule_id = argv[0]
    reason = pop_flag(argv, "--reason") or ""
    cooldown_hours = int(pop_flag(argv, "--cooldown-hours") or "168")

    from flow_memory.skill_evolution import reject_suggestion
    reject_suggestion(rule_id, reason=reason, cooldown_hours=cooldown_hours)
    print(f"🗑️  Rejected {rule_id} (cooldown: {cooldown_hours}h)")
    return 0


def _cmd_skill_evolve_cooldowns(argv: list[str]) -> int:
    """List active cooldowns."""
    from flow_memory.skill_evolution import list_active_cooldowns
    cooldowns = list_active_cooldowns()
    if not cooldowns:
        print("No active cooldowns.")
        return 0
    print(f"Active cooldowns ({len(cooldowns)}):")
    for c in cooldowns:
        until = c["cooldown_until"][:19]
        reject_count = c["reject_count"]
        reason = c.get("reason", "")
        print(f"  {c['rule_id']} — until {until} (rejected {reject_count}x) {reason}")
    return 0


def _cmd_skill_evolve_clear(argv: list[str]) -> int:
    """Clear all cooldowns (admin operation)."""
    confirm = pop_bool_flag(argv, "--yes")
    if not confirm:
        print("⚠️  This will clear ALL skill evolution cooldowns.")
        print("   Use --yes to confirm.")
        return 1
    from flow_memory.skill_evolution import clear_all_cooldowns
    count = clear_all_cooldowns()
    print(f"✅ Cleared {count} cooldown(s)")
    return 0


_SUBCOMMANDS = {
    "constraints": _cmd_constraints,
    "capsule": _cmd_capsule,
    "packet": _cmd_packet,
    "items": _cmd_items,
    "pin": _cmd_pin,
    "recall": _cmd_recall,
    "daily-summary": _cmd_daily_summary,
    "dashboard": _cmd_dashboard,
    "agents-md": _cmd_agents_md,
    "skill-evolve": _cmd_skill_evolve,
    "reflect": _cmd_reflect,
    "reflect-stats": _cmd_reflect_stats,
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
    "sensitive": _cmd_sensitive,
    "decay": _cmd_decay,
    "consolidate": _cmd_consolidate,
    "export": _cmd_export,
    "inject-check": _cmd_inject_check,
    "gate-check": _cmd_gatecheck,
    "budget": _cmd_budget,
    "expire": _cmd_expire,
    "audit": _cmd_audit,
    "cleanup": _cmd_cleanup,
    "daily": _cmd_daily,
}


def main(argv: list[str]) -> int:
    if not argv:
        return usage_error(USAGE)
    sub = argv[0]
    handler = _SUBCOMMANDS.get(sub)
    if handler is None:
        return usage_error(f"unknown memory subcommand: {sub}\n\n{USAGE}")
    return handler(argv[1:])
