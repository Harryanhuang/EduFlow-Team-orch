from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import flow_memory.items
import flow_memory.storage

from eduflow import memory


ROOT = Path(__file__).resolve().parents[2]
SHIM = ROOT / "src" / "eduflow" / "memory" / "__init__.py"
EXPECTED_EXPLICIT_EXPORT_COUNT = 135
EXPECTED_EXPLICIT_EXPORT_SHA256 = "97d56d0757e7684712f2f77651aea0b111203bce12dba3b1f4496066a329c4c6"


def _explicit_flow_memory_exports() -> list[str]:
    tree = ast.parse(SHIM.read_text(encoding="utf-8"))
    return sorted(
        f"{node.module}:{alias.name}:{alias.asname}"
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module
        and node.module.startswith("flow_memory")
        for alias in node.names
        if alias.name != "*"
    )


def test_memory_shim_explicit_export_surface_is_unchanged() -> None:
    # Runtime namespace enumeration is deliberately avoided: legacy tests add
    # compatibility doubles to this module.  The source-level export contract
    # is deterministic, while representative identities cover runtime wiring.
    names = _explicit_flow_memory_exports()
    digest = hashlib.sha256("\n".join(names).encode()).hexdigest()

    assert len(names) == EXPECTED_EXPLICIT_EXPORT_COUNT
    assert digest == EXPECTED_EXPLICIT_EXPORT_SHA256
    assert memory.StorageBackend is flow_memory.storage.StorageBackend
    assert memory.add_memory is flow_memory.items.add_memory


def test_memory_shim_marks_every_flow_memory_import_as_an_explicit_reexport() -> None:
    tree = ast.parse(SHIM.read_text(encoding="utf-8"))
    implicit: list[str] = []
    wildcard_modules: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if not node.module or not node.module.startswith("flow_memory"):
            continue
        for alias in node.names:
            if alias.name == "*":
                wildcard_modules.append(node.module)
                continue
            if alias.asname != alias.name:
                implicit.append(f"{node.module}.{alias.name}")

    assert wildcard_modules == ["flow_memory"]
    assert not implicit, f"implicit compatibility exports: {implicit}"
