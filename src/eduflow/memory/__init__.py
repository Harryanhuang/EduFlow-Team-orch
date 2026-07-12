"""Backwards-compat shim: EduFlow's old eduflow.memory import path now aliases flow_memory.

All EduFlow code should migrate to `from flow_memory import ...` directly.
This shim ensures zero behavior change during the transition window.

Migration path:
  1. Install flow-memory: pip install flow-memory
  2. Replace `from eduflow.memory.X import Y` with `from flow_memory.X import Y`
  3. (optional) Remove this shim once all callers migrated
"""
from __future__ import annotations

import warnings

try:
    from flow_memory import *  # noqa: F401, F403
    from flow_memory.storage import (
        DefaultPathProvider as DefaultPathProvider,
        LanceDBBackend as LanceDBBackend,
        MarkdownBackend as MarkdownBackend,
        PathProvider as PathProvider,
        PostgresBackend as PostgresBackend,
        SqliteBackend as SqliteBackend,
        StorageBackend as StorageBackend,
        VectorBackend as VectorBackend,
        get_backend as get_backend,
        get_path_provider as get_path_provider,
        get_vector_backend as get_vector_backend,
        set_backend as set_backend,
        set_path_provider as set_path_provider,
        use_backend as use_backend,
        use_vector_backend as use_vector_backend,
    )
    from flow_memory.packet import (
        MAX_CAPSULE_CHARS as MAX_CAPSULE_CHARS,
        MAX_CONSTRAINTS as MAX_CONSTRAINTS,
        MAX_MEMORIES as MAX_MEMORIES,
        MAX_MEMORY_CHARS as MAX_MEMORY_CHARS,
        MAX_TOTAL_CHARS as MAX_TOTAL_CHARS,
        assemble_memory_packet as assemble_memory_packet,
        extract_task_id_from_message as extract_task_id_from_message,
    )
    from flow_memory.items import (
        add_memory as add_memory,
        deprecate_memory as deprecate_memory,
        get_memory as get_memory,
        list_memories as list_memories,
        list_pinned_memories as list_pinned_memories,
        pin_memory as pin_memory,
        supersede_memory as supersede_memory,
        unpin_memory as unpin_memory,
    )
    from flow_memory.search import (
        hybrid_search as hybrid_search,
        search_memories as search_memories,
        sync_fts as sync_fts,
    )
    from flow_memory.vector_store import (
        get_embedding_provider as get_embedding_provider,
        index_all_confirmed as index_all_confirmed,
        index_memory as index_memory,
        index_status as index_status,
        remove_from_index as remove_from_index,
        search_similar as search_similar,
        set_embedding_provider as set_embedding_provider,
    )
    from flow_memory.user_profile import (
        delete_profile as delete_profile,
        get_profile as get_profile,
        list_profile as list_profile,
        set_profile as set_profile,
    )
    from flow_memory.candidates import (
        add_candidate as add_candidate,
        expire_stale_candidates as expire_stale_candidates,
        get_candidate as get_candidate,
        list_candidates as list_candidates,
        promote_candidate as promote_candidate,
        reject_candidate as reject_candidate,
    )
    from flow_memory.candidate_gen import (
        generate_from_event as generate_from_event,
        infer_scope_kind_layer as infer_scope_kind_layer,
    )
    from flow_memory.constraints import (
        add_constraint as add_constraint,
        deactivate_constraint as deactivate_constraint,
        list_constraints as list_constraints,
        query_for_agent as query_for_agent,
    )
    from flow_memory.capsules import (
        get_capsule as get_capsule,
        refresh_from_task_store as refresh_from_task_store,
    )
    from flow_memory.scope_aliases import (
        add_alias as add_alias,
        deactivate_alias as deactivate_alias,
        get_subject_hierarchy as get_subject_hierarchy,
        get_subject_parents as get_subject_parents,
        list_aliases as list_aliases,
        resolve_alias as resolve_alias,
        resolve_subject_scopes as resolve_subject_scopes,
    )
    from flow_memory.links import (
        add_link as add_link,
        get_contradictions as get_contradictions,
        get_links_from as get_links_from,
        get_links_to as get_links_to,
        get_support_chain as get_support_chain,
        remove_link as remove_link,
    )
    from flow_memory.storage_budget import (
        LIMITS as LIMITS,
        budget_report as budget_report,
        check_budget as check_budget,
        enforce_budget as enforce_budget,
    )
    from flow_memory.expiration import run_all_expirations as run_all_expirations
    from flow_memory.audit import (
        full_audit as full_audit,
        retention_report as retention_report,
        scope_coverage_report as scope_coverage_report,
    )
    from flow_memory.decay import (
        decay_batch as decay_batch,
        effective_confidence as effective_confidence,
    )
    from flow_memory.dual_query import dual_query_memories as dual_query_memories
    from flow_memory.daily_summary import (
        archive_old_summaries as archive_old_summaries,
        get_summary as get_summary,
        list_summaries as list_summaries,
        upsert_summary as upsert_summary,
    )
    from flow_memory.dashboard import render_dashboard as render_dashboard
    from flow_memory.agents_md_gen import (
        generate_agents_md as generate_agents_md,
        write_agents_md as write_agents_md,
    )
    from flow_memory.reflect import (
        list_recent_reflection_candidates as list_recent_reflection_candidates,
        reflection_stats as reflection_stats,
        submit_reflection as submit_reflection,
    )
    from flow_memory.sensitive import (
        add_sensitive as add_sensitive,
        change_password as change_password,
        delete_sensitive as delete_sensitive,
        get_sensitive as get_sensitive,
        is_configured as is_configured,
        is_unlocked as is_unlocked,
        list_sensitive as list_sensitive,
        lock as lock,
        recover as recover,
        search_sensitive as search_sensitive,
        setup_password as setup_password,
        status as status,
        unlock as unlock,
    )
    from flow_memory.inject import build_gate_check as build_gate_check, inject_to_send as inject_to_send
    from flow_memory.event_bridge import (
        bridge_closeout_check as bridge_closeout_check,
        bridge_manager_correction as bridge_manager_correction,
        bridge_review_event as bridge_review_event,
        bridge_task_lifecycle as bridge_task_lifecycle,
    )
    from flow_memory.event_hooks import (
        on_closeout_anomaly as on_closeout_anomaly,
        on_manager_correction as on_manager_correction,
        on_review_rejected as on_review_rejected,
        on_task_failure_pattern as on_task_failure_pattern,
    )
    from flow_memory.derivation import (
        on_authoritative_verdict_fail as on_authoritative_verdict_fail,
        on_closeout_completed as on_closeout_completed,
        on_revision_priority_set as on_revision_priority_set,
    )
    from flow_memory.jit_recall import (
        get_facts_by_kind as get_facts_by_kind,
        get_handoffs as get_handoffs,
        get_mistakes_for_agent as get_mistakes_for_agent,
        get_recent_decisions as get_recent_decisions,
    )
    from flow_memory.admission import (
        ADMISSION_THRESHOLD as ADMISSION_THRESHOLD,
        score_candidate as score_candidate,
    )
    from flow_memory.consolidate import (
        consolidation_report as consolidation_report,
        find_similar_pairs as find_similar_pairs,
        merge_memories as merge_memories,
    )
    from flow_memory.skill_evolution import (
        accept_suggestion as accept_suggestion,
        aggregate_frequent_rules as aggregate_frequent_rules,
        clear_all_cooldowns as clear_all_cooldowns,
        generate_suggestions as generate_suggestions,
        list_active_cooldowns as list_active_cooldowns,
        reject_suggestion as reject_suggestion,
        render_suggestion_report as render_suggestion_report,
    )
except ImportError as e:
    warnings.warn(
        f"flow-memory package not installed; eduflow.memory shim may not work: {e}",
        ImportWarning,
        stacklevel=2,
    )
    raise


def get_conn():
    """Backwards-compat: legacy eduflow.memory.db.get_conn() returns a connection."""
    return get_backend().connect()


def init_schema():
    """Backwards-compat: legacy eduflow.memory.db.init_schema() creates tables."""
    return get_backend().init_schema()


# ── EduFlow-specific extension: register task store provider ─────
# This bridges flow_memory's generic capsule module to EduFlow's
# tasks.json store. Without this, refresh_from_task_store() returns None.

try:
    from eduflow.store import tasks as _eduflow_tasks
    from flow_memory.capsules import register_task_provider as register_task_provider

    register_task_provider(_eduflow_tasks.get)
except ImportError:
    pass  # EduFlow store not available; capsules work in pure-CRUD mode