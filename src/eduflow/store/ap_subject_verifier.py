"""AP subject artifact verifier.

Scans an AP subject directory (e.g. /.../AP Computer Science A/) and validates
that the produced item files, qa-manifest.csv, and QA-自检.md meet the
AP qbank-agent schema.

Directory layout expected:
    <subject_dir>/02-题库/items/Unit 1/U1.1.1-F.md
    <subject_dir>/02-题库/items/Unit 1/qa-manifest.csv
    <subject_dir>/02-题库/items/Unit 1/QA-自检.md
    ...
"""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any


_REQUIRED_FRONTMATTER_KEYS = (
    "id",
    "difficulty",
    "type",
    "calculator",
    "subject",
    "unit",
    "topic",
    "subtopic",
    "learning_objective",
    "knowledge_point",
    "core_concept",
    "exam_pattern",
    "question_type",
    "common_mistake",
    "explanation_context",
)

_VALID_DIFFICULTIES = {"F", "S", "C"}

_ITEM_FILENAME_RE = re.compile(r"^U\d+\.\d+\.\d+-(?:F|S|C)\.md$")

_QA_STATUS_COMPLETE_RE = re.compile(r"本\s*Unit\s*状态\s*[:：]\s*\*\*完成\*\*|状态\s*[:：]\s*\*\*完成\*\*")


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Extract a simple key: value YAML frontmatter block."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    result: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip()
    return result


def _has_heading(text: str, heading: str) -> bool:
    """Check for a markdown heading line (e.g. ## Options)."""
    return bool(re.search(rf"^##\s+{re.escape(heading)}\s*$", text, re.MULTILINE))


def _empty_result(subject_name: str = "") -> dict[str, Any]:
    return {
        "subject_name": subject_name,
        "scope": "subject",
        "status": "fail",
        "unit_count": 0,
        "item_count": 0,
        "manifest_item_rows": 0,
        "qa_passed": False,
        "difficulty_distribution": {},
        "blocking_reasons": [],
        "unit_details": [],
    }


def _validate_item_file(path: Path) -> list[str]:
    """Return list of blocking reasons for a single item file."""
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        return [f"cannot_read:{path.name}:{exc}"]

    fm = _parse_frontmatter(text)
    missing = [k for k in _REQUIRED_FRONTMATTER_KEYS if not fm.get(k)]
    if missing:
        errors.append(f"missing_frontmatter:{path.name}:{','.join(missing)}")

    if fm.get("difficulty") not in _VALID_DIFFICULTIES:
        errors.append(f"invalid_difficulty:{path.name}:{fm.get('difficulty')}")

    for heading in ("Options", "Answer", "Explanation"):
        if not _has_heading(text, heading):
            errors.append(f"missing_heading:{path.name}:{heading}")

    return errors


def _read_manifest_item_rows(manifest_path: Path) -> tuple[list[dict[str, str]], list[str]]:
    """Return item rows (non-SUMMARY) and any parse errors."""
    errors: list[str] = []
    rows: list[dict[str, str]] = []
    try:
        with open(manifest_path, encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for idx, row in enumerate(reader, start=2):
                subtopic = str(row.get("subtopic") or "").strip()
                item_id = str(row.get("item_id") or "").strip()
                if subtopic.upper() == "SUMMARY" or item_id.upper().endswith("SUMMARY"):
                    continue
                if not item_id:
                    errors.append(f"manifest_missing_item_id:{manifest_path.name}:row{idx}")
                    continue
                rows.append(row)
    except Exception as exc:
        errors.append(f"manifest_read_error:{manifest_path.name}:{exc}")
    return rows, errors


def _qa_self_check_passes(qa_path: Path) -> bool:
    """Return True if QA-自检.md declares this Unit 完成."""
    try:
        text = qa_path.read_text(encoding="utf-8")
    except Exception:
        return False
    return bool(_QA_STATUS_COMPLETE_RE.search(text))


def verify_ap_subject(subject_dir: str | Path) -> dict[str, Any]:
    """Run full AP artifact verification for a single subject directory.

    Returns structured result with status, counts, difficulty distribution,
    and blocking reasons.
    """
    subject_dir = Path(subject_dir)
    result = _empty_result(subject_dir.name)
    blocking: list[str] = []

    items_root = subject_dir / "02-题库" / "items"
    if not items_root.exists():
        blocking.append("items_directory_not_found")
        result["blocking_reasons"] = blocking
        return result

    unit_dirs = sorted(
        p for p in items_root.iterdir()
        if p.is_dir() and p.name.lower().startswith("unit ")
    )
    if not unit_dirs:
        blocking.append("no_unit_directories_found")
        result["blocking_reasons"] = blocking
        return result

    unit_details: list[dict[str, Any]] = []
    total_items = 0
    total_manifest_rows = 0
    qa_passed_count = 0
    all_difficulties: list[str] = []

    for unit_dir in unit_dirs:
        unit_name = unit_dir.name
        item_files = sorted(
            p for p in unit_dir.iterdir()
            if p.is_file() and _ITEM_FILENAME_RE.match(p.name)
        )

        unit_errors: list[str] = []
        for item_file in item_files:
            unit_errors.extend(_validate_item_file(item_file))
            fm = _parse_frontmatter(item_file.read_text(encoding="utf-8"))
            diff = fm.get("difficulty")
            if diff in _VALID_DIFFICULTIES:
                all_difficulties.append(diff)

        manifest_path = unit_dir / "qa-manifest.csv"
        manifest_rows: list[dict[str, str]] = []
        if not manifest_path.exists():
            unit_errors.append(f"missing_manifest:{unit_name}")
        else:
            manifest_rows, manifest_errors = _read_manifest_item_rows(manifest_path)
            unit_errors.extend(manifest_errors)
            total_manifest_rows += len(manifest_rows)
            if len(manifest_rows) != len(item_files):
                unit_errors.append(
                    f"manifest_item_count_mismatch:{unit_name}:files={len(item_files)}:manifest={len(manifest_rows)}"
                )

        qa_path = unit_dir / "QA-自检.md"
        qa_ok = _qa_self_check_passes(qa_path)
        if not qa_path.exists():
            unit_errors.append(f"missing_qa_self_check:{unit_name}")
        elif not qa_ok:
            unit_errors.append(f"qa_self_check_not_complete:{unit_name}")
        else:
            qa_passed_count += 1

        total_items += len(item_files)
        unit_details.append({
            "unit": unit_name,
            "item_count": len(item_files),
            "manifest_item_rows": len(manifest_rows),
            "qa_passed": qa_ok,
            "errors": unit_errors,
        })
        blocking.extend(unit_errors)

    result["unit_count"] = len(unit_dirs)
    result["item_count"] = total_items
    result["manifest_item_rows"] = total_manifest_rows
    result["qa_passed"] = qa_passed_count == len(unit_dirs) and len(unit_dirs) > 0
    result["unit_details"] = unit_details
    result["difficulty_distribution"] = dict(sorted(
        __import__("collections").Counter(all_difficulties).items()
    ))

    if not result["qa_passed"]:
        blocking.append("qa_self_check_not_all_passed")

    result["blocking_reasons"] = list(dict.fromkeys(blocking))
    result["status"] = "pass" if not result["blocking_reasons"] else "fail"
    return result


def compact_summary(result: dict[str, Any]) -> dict[str, Any]:
    """Return a manager-panel friendly summary."""
    return {
        "status": result.get("status", "fail"),
        "subject_name": result.get("subject_name", ""),
        "unit_count": result.get("unit_count", 0),
        "item_count": result.get("item_count", 0),
        "manifest_item_rows": result.get("manifest_item_rows", 0),
        "qa_passed": result.get("qa_passed", False),
        "difficulty_distribution": result.get("difficulty_distribution", {}),
        "blocking_reasons": result.get("blocking_reasons", []),
    }
