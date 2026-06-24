"""EduFlow Memory — Active Constraint Rehydration (Phase 1A) + Memory Core (Phase 1) + Candidates (Phase 3).

Public API for the memory subsystem. This package introduces SQLite-backed
active constraints, task capsules, memory items, scope aliases, FTS search,
and candidate/promote workflows so critical rules survive /compact,
reidentify, and gate changes.

Usage:
    from eduflow.memory import assemble_memory_packet

    packet = assemble_memory_packet("worker_course", task_id="T-29")
"""
from __future__ import annotations

from eduflow.memory.packet import (
    assemble_memory_packet,
    extract_task_id_from_message,
    MAX_TOTAL_CHARS,
    MAX_CONSTRAINTS,
    MAX_CAPSULE_CHARS,
    MAX_MEMORIES,
    MAX_MEMORY_CHARS,
)

__all__ = [
    # Packet assembly
    "assemble_memory_packet",
    "extract_task_id_from_message",
    # Packet budget constants
    "MAX_TOTAL_CHARS",
    "MAX_CONSTRAINTS",
    "MAX_CAPSULE_CHARS",
    "MAX_MEMORIES",
    "MAX_MEMORY_CHARS",
]
