"""Subject artifact verifier — package 2 artifact consistency + closeout gate.

Replaces worker self-audit with deterministic, repeatable artifact checks.
Outputs structured results that the subject-closeout gate MUST consume.

Key invariants:
  - Package PASS never becomes subject PASS.
  - Orphan candidates go to quarantine recommendation only (no auto-delete).
  - Legacy fragments (-s2/-s3 and other variants) are flagged, not merged into pass stats.
  - Subject closeout gate reads verifier result; fail → blocked.
"""
from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

# ── Constants ───────────────────────────────────────────────────────

# Legacy fragment patterns: -s2/s3 items, round2, final variants, uppercase
_LEGACY_FRAGMENT_RES = [
    re.compile(r"-(s[2-9]\d*)-items\.md$", re.IGNORECASE),
    re.compile(r"-round\d+-items\.md$", re.IGNORECASE),
    re.compile(r"-final.*-items\.md$", re.IGNORECASE),
]

_VALID_DIFFICULTIES = {"Foundation", "Standard", "Challenge"}

# Support both `### Question` (qa/items convention) and `# Question` (qql convention)
_QUESTION_ENTITY_RE = re.compile(
    r"#{1,3}\s+Question\s+(Q-\S+)\s*\n"
    r"(.*?)(?=\n#{1,3}\s+Question\s+Q-|\Z)",
    re.DOTALL,
)

_DIFFICULTY_RE = re.compile(r"\*\*Difficulty\*\*:\s*(.+)")

_TOPIC_OUTLINE_ROW_RE = re.compile(
    r"\|\s*(\S+)\s*\|\s*(.+?)\s*\|\s*(Core|Extended|Core\+E).*?\|",
    re.MULTILINE,
)

_KNOWN_CONTENT_LAYERS = ("qa", "qa-question-level", "items")

# ── Default result builder ──────────────────────────────────────────


def _empty_result(subject_slug: str, *, scope: str = "subject") -> dict:
    """Shared baseline for results, so the two early-return sites don't drift."""
    return {
        "subject_slug": subject_slug,
        "scope": scope,
        "status": "fail",
        "topic_count": 0,
        "qa_count": 0,
        "qql_count": 0,
        "items_count": 0,
        "total_questions": 0,
        "difficulty_distribution": {},
        "has_manifest": False,
        "manifest_path": "",
        "manifest_rows": 0,
        "id_mapping": {},
        "orphan_candidates": [],
        "legacy_fragment_present": False,
        "legacy_fragments": [],
        "consistency": {
            "drifts": [],
            "format_errors": [],
            "invalid_difficulty_files": [],
            "scoped_total": 0,
            "has_qa": False,
            "has_qql": False,
            "has_items": False,
            "has_manifest": False,
            "drift_count": 0,
            "format_error_count": 0,
            "invalid_difficulty_count": 0,
            "missing_layers": [],
        },
        "blocking_reasons": [],
        "next_action": "",
        "evidence": {},
    }


# ── Helpers ─────────────────────────────────────────────────────────


def _parse_question_ids(text: str) -> list[str]:
    """Extract Question IDs from markdown text."""
    return [m.group(1).rstrip("`") for m in _QUESTION_ENTITY_RE.finditer(text)]


def _parse_difficulties(text: str) -> list[str]:
    """Extract difficulty values from markdown text."""
    return [m.group(1).strip().rstrip("`") for m in _DIFFICULTY_RE.finditer(text)]


def _parse_topic_outline(path: Path) -> dict[str, str]:
    """Parse topic-outline.md → {topic_id: topic_name}."""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    topics = {}
    for m in _TOPIC_OUTLINE_ROW_RE.finditer(text):
        tid = m.group(1).strip()
        tname = m.group(2).strip()
        topics[tid] = tname
    return topics


def _read_layer_files(layer_dir: Path) -> list[dict]:
    """Read all .md files in a content layer directory. Returns list of file stats."""
    if not layer_dir.exists():
        return []
    results = []
    for f in sorted(layer_dir.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        ids = _parse_question_ids(text)
        diffs = _parse_difficulties(text)
        results.append({
            "file": str(f.name),
            "path": str(f),
            "question_ids": ids,
            "question_count": len(ids),
            "difficulties": diffs,
        })
    return results


def _read_manifest(path: Path) -> list[dict]:
    """Read qa-manifest.csv → list of row dicts."""
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _detect_orphans(subject_dir: Path, *, topic_ids: set[str],
                    manifest_files: set[str],
                    qid_file_counts: dict[str, int]) -> list[dict]:
    """Identify files not referenced by manifest, topic outline, or Q-ID mapping.

    A file is orphaned if ALL of these are true:
      - Not listed in manifest (by relative path or basename).
      - Filename prefix does not match a known topic ID.
      - Contains zero Question IDs that appear in >=2 distinct files
        (cross-file Q-ID sharing).
      - Contains at least one Question entity.

    Returns quarantine recommendations only — never modifies files.
    """
    orphans = []
    for layer in _KNOWN_CONTENT_LAYERS:
        layer_dir = subject_dir / layer
        if not layer_dir.exists():
            continue
        for f in sorted(layer_dir.glob("*.md")):
            rel = str(f.relative_to(subject_dir))
            # Check if file is referenced in manifest
            if rel in manifest_files or f.name in manifest_files:
                continue
            # Check topic association via filename convention
            topic_match = re.match(r"(\d+(?:\.\d+)?)", f.name)
            if topic_match:
                tid = topic_match.group(1)
                if tid in topic_ids:
                    continue  # associated with known topic by filename

            # Check cross-file Q-ID association:
            # If any Q-ID in this file appears in >=2 files total,
            # this file is connected to the rest of the subject.
            try:
                text = f.read_text(encoding="utf-8")
                file_qids = set(_parse_question_ids(text))
            except Exception:
                file_qids = set()

            if not file_qids:
                continue  # empty file — not worth flagging

            if any(qid_file_counts.get(qid, 0) >= 2 for qid in file_qids):
                continue  # shares Q-IDs with at least one other file

            orphans.append({
                "file": rel,
                "layer": layer,
                "reason": "not_referenced_in_manifest_topic_or_cross_layer",
                "recommendation": "quarantine_review",
                "auto_delete": False,
                "evidence": _orphan_evidence_from_ids(file_qids, f),
            })
    return orphans


def _orphan_evidence_from_ids(qids: set[str], file_path: Path) -> dict:
    """Collect lightweight evidence about an orphan file."""
    try:
        return {
            "question_ids_sample": sorted(qids)[:10],
            "question_count": len(qids),
            "file_size_bytes": file_path.stat().st_size,
        }
    except Exception:
        return {"error": "could_not_read_file"}


def _detect_legacy_fragments(subject_dir: Path) -> list[dict]:
    """Find legacy fragment files (-s2, -s3, round2, final-*, etc.) across all content layers."""
    fragments = []
    for layer in _KNOWN_CONTENT_LAYERS:
        layer_dir = subject_dir / layer
        if not layer_dir.exists():
            continue
        for f in sorted(layer_dir.glob("*.md")):
            for pat in _LEGACY_FRAGMENT_RES:
                m = pat.search(f.name)
                if m:
                    fragments.append({
                        "file": str(f.relative_to(subject_dir)),
                        "layer": layer,
                        "pattern": pat.pattern,
                        "recommendation": "review_legacy_fragment",
                    })
                    break  # report once per file
    return fragments


def _build_id_mapping(layer_stats: dict) -> dict:
    """Build bidirectional question-ID mapping summary."""
    all_ids: dict[str, set[str]] = defaultdict(set)
    for layer_name, files in layer_stats.items():
        for fstat in files:
            for qid in fstat.get("question_ids", []):
                all_ids[qid].add(layer_name)

    by_layer: dict[str, int] = {}
    for layer_name, files in layer_stats.items():
        count = sum(f.get("question_count", 0) for f in files)
        by_layer[layer_name] = count

    cross_layer = {qid: layers for qid, layers in all_ids.items() if len(layers) > 1}

    return {
        "total_unique_ids": len(all_ids),
        "by_layer": by_layer,
        "cross_layer_count": len(cross_layer),
        "cross_layer_ids": sorted(cross_layer.keys())[:20],
    }


def _collect_all_qids(layer_stats: dict) -> set[str]:
    """Collect all unique Q-IDs across all layers."""
    all_qids: set[str] = set()
    for files in layer_stats.values():
        for fstat in files:
            all_qids.update(fstat.get("question_ids", []))
    return all_qids


def _qid_file_count(layer_stats: dict) -> dict[str, int]:
    """Count how many distinct files each Q-ID appears in (across all layers)."""
    counts: dict[str, set[str]] = defaultdict(set)
    for files in layer_stats.values():
        for fstat in files:
            fname = fstat.get("file", "")
            for qid in fstat.get("question_ids", []):
                counts[qid].add(fname)
    return {qid: len(files) for qid, files in counts.items()}


# ── Package 2: Artifact Consistency Verifier ────────────────────────
#
# Detects yesterday's real IGCSE 8h drift problems:
#   - items vs QQL vs manifest row counts disagree (e.g. items=378, QQL=324)
#   - markdown blocks are unclosed / malformed (e.g. `**Item 10 [F]`)
#   - difficulty fields use non-F/S/C values (e.g. `Difficulty: 1`)
#   - manifest exists but QQL layer is empty (manifest-only completion)
#
# Each finding becomes a blocking_reason so closeout gate sees it,
# and is surfaced via compact_summary() so manager-panel can render it.

# Numeric / non-canonical difficulty markers seen in yesterday's drafts.
# We do NOT auto-correct; we flag so the worker / manager can repair.
_NON_FSC_DIFFICULTY_RES = [
    (re.compile(r"^\s*[123]\s*$"), "numeric_difficulty"),
    (re.compile(r"^\s*[Ff]\s*/?\s*[1-3]\s*$"), "compact_F1_F2_F3"),
    (re.compile(r"^\s*[Ee]asy\s*/?\s*[1-3]\s*$"), "easy_label"),
    (re.compile(r"^\s*(?:low|med|high|medium)\s*$", re.IGNORECASE), "loose_label"),
]

# Pattern for an orphan/malformed marker: a paragraph that LOOKS like a
# question line but is missing the `### Question` header that `_QUESTION_ENTITY_RE`
# requires. Yesterday: `**Item 10 [F]` was emitted with no closing `### Question`.
# Codex Q3: include lowercase [f/s/c] variants and the compact [F/S] notation.
_ORPHAN_MARKER_RE = re.compile(
    r"^\*\*Item\s+\d+\s*\[[FfSsCc](?:/[SsCcCc])?[^\]]*\]",
    re.MULTILINE,
)


def _scan_format_errors(layer_stats: dict) -> list[dict]:
    """Scan each parsed layer file for malformed / unclosed question blocks.

    Two kinds:
      - `unclosed_question_block`: text starts a question but has no
        `### Question` header (e.g. `**Item 10 [F]` with no preceding heading)
      - `orphan_marker`: a line that looks like an item marker but is
        not part of any valid `### Question` block

    The parser-based file stats already drop these, so the only signal
    we have is to re-scan the raw text for orphan markers and compare
    against the parsed question_ids.
    """
    errors: list[dict] = []
    for layer_name, files in layer_stats.items():
        for fstat in files:
            fpath = fstat.get("path", "")
            if not fpath:
                continue
            try:
                raw = Path(fpath).read_text(encoding="utf-8")
            except Exception:
                continue
            for m in _ORPHAN_MARKER_RE.finditer(raw):
                # Find the line number for evidence
                line_no = raw[: m.start()].count("\n") + 1
                errors.append({
                    "kind": "unclosed_question_block",
                    "file": fstat.get("file", ""),
                    "layer": layer_name,
                    "marker": m.group(0).strip(),
                    "line": line_no,
                    "recommendation": "repair_unclosed_question_block",
                })
    return errors


# Short forms documented in workflow checklists (docs/workflows/igcse-subject-launch).
# Normalize F/S/C to long forms so the verifier accepts documented shorthand
# without treating them as invalid. Codex Q4 alignment.
_DIFFICULTY_SHORT_FORM = {"F": "Foundation", "S": "Standard", "C": "Challenge"}


def _normalize_difficulty(value: str) -> str:
    """Map documented short forms F/S/C to canonical long names.

    Returns the input unchanged when it's not a recognized short form.
    """
    v = value.strip()
    if v in _DIFFICULTY_SHORT_FORM:
        return _DIFFICULTY_SHORT_FORM[v]
    return v


def _scan_invalid_difficulties(layer_stats: dict) -> list[dict]:
    """Find difficulty values that are NOT one of Foundation/Standard/Challenge.

    Accepts documented short forms F/S/C and normalizes them.
    Yesterday: `**Difficulty**: 1` was emitted instead of `Foundation`.
    Returned as {file, samples: [{value, line}], invalid_count} per file.
    """
    invalid_by_file: dict[str, list[dict]] = defaultdict(list)
    for layer_name, files in layer_stats.items():
        for fstat in files:
            fname = fstat.get("file", "")
            fpath = fstat.get("path", "")
            if not fpath:
                continue
            try:
                raw = Path(fpath).read_text(encoding="utf-8")
            except Exception:
                continue
            # Walk every line that starts with `**Difficulty**:` (not just the
            # parsed ones, since the regex only fires on F/S/C line in the
            # parser's distribution path)
            for ln, line in enumerate(raw.splitlines(), start=1):
                m = _DIFFICULTY_RE.match(line)
                if not m:
                    continue
                value = m.group(1).strip().rstrip("`")
                if value in _VALID_DIFFICULTIES:
                    continue
                if _normalize_difficulty(value) in _VALID_DIFFICULTIES:
                    continue
                invalid_by_file[f"{layer_name}/{fname}"].append({
                    "value": value,
                    "line": ln,
                })
    out = []
    for fkey, samples in invalid_by_file.items():
        out.append({
            "file": fkey,
            "invalid_count": len(samples),
            "samples": samples[:5],
            "recommendation": "rewrite_difficulty_to_Foundation_Standard_Challenge",
        })
    return out


def _compute_drift_entries(*, qa_count: int, qql_count: int,
                            items_count: int, manifest_rows: int) -> list[dict]:
    """Compute drift entries between items / QQL / manifest counts.

    Drift is reported (not auto-resolved). Each drift kind has:
      {kind, items, qql, manifest, delta, recommendation}

    Canonical invariants (from IGCSE 8h monitor gap analysis 2026-06-22):
      - `qql_count == manifest_claimed_total`: manifest enumerates the
        QQL set; a mismatch means manifest is stale or doesn't claim all
        QQL files. This was the 0606 324/324 case where manifest matched
        QQL but items did not. Blocking.
      - `items_count > qql_count`: items must be a subset/superset of
        the canonical QQL set, not a parallel source. Yesterday's 378/324
        case — items had grown beyond the canonical set. Blocking.
      - `items_count < qql_count`: items are a subset; not blocking,
        just informational so the manager knows coverage is partial.
    """
    entries: list[dict] = []
    if qql_count != manifest_rows and qql_count > 0:
        entries.append({
            "kind": "qql_vs_manifest_drift",
            "qql": qql_count,
            "manifest": manifest_rows,
            "delta": qql_count - manifest_rows,
            "severity": "blocking",
            "recommendation": "rebuild_manifest_from_qql",
        })
    if items_count > qql_count and qql_count > 0:
        # items have grown beyond the canonical set → blocking
        entries.append({
            "kind": "items_vs_qql_drift",
            "items": items_count,
            "qql": qql_count,
            "delta": items_count - qql_count,
            "severity": "blocking",
            "recommendation": "trim_items_to_canonical_qql_set",
        })
    elif items_count < qql_count and items_count > 0 and qql_count > 0:
        # items are a subset → informational only
        entries.append({
            "kind": "items_subset_of_qql",
            "items": items_count,
            "qql": qql_count,
            "delta": qql_count - items_count,
            "severity": "info",
            "recommendation": "consider_expanding_items_to_full_qql_set",
        })
    return entries


def _compute_consistency(*, qa_count: int, qql_count: int,
                          items_count: int, manifest_rows: int,
                          layer_stats: dict,
                          missing_layers: list[str]) -> dict:
    """Build the consistency summary embedded in the verifier result.

    Returns a dict with:
      drifts: list[dict]                — count disagreements
      format_errors: list[dict]         — unclosed/malformed blocks
      invalid_difficulty_files: list[dict] — non-F/S/C difficulties
      scoped_total: int                 — min(items, qql, manifest) used as
                                          current scoped canonical count
      has_qa: bool, has_qql: bool,
      has_items: bool, has_manifest: bool
      drift_count: int, format_error_count: int
    """
    drifts = _compute_drift_entries(
        qa_count=qa_count, qql_count=qql_count,
        items_count=items_count, manifest_rows=manifest_rows,
    )
    format_errors = _scan_format_errors(layer_stats)
    invalid_diffs = _scan_invalid_difficulties(layer_stats)

    # The "scoped total" is what all three layers currently agree on
    # (or the smallest agreeing subset). Useful for the manager to see
    # "we are at 189, not the original 300-400 target".
    counts = [items_count, qql_count, manifest_rows]
    present_counts = [c for c in counts if c > 0]
    scoped_total = min(present_counts) if present_counts else 0

    has_qa = qa_count > 0
    has_qql = qql_count > 0
    has_items = items_count > 0
    has_manifest = manifest_rows > 0

    return {
        "drifts": drifts,
        "format_errors": format_errors,
        "invalid_difficulty_files": invalid_diffs,
        "scoped_total": scoped_total,
        "has_qa": has_qa,
        "has_qql": has_qql,
        "has_items": has_items,
        "has_manifest": has_manifest,
        "drift_count": len(drifts),
        "blocking_drift_count": sum(
            1 for d in drifts if d.get("severity") == "blocking"
        ),
        "format_error_count": len(format_errors),
        "invalid_difficulty_count": len(invalid_diffs),
        "missing_layers": list(missing_layers),
    }


def _consistency_to_blocking_reasons(consistency: dict) -> list[str]:
    """Translate consistency findings into blocking_reasons entries.

    Drift entries with severity=blocking become hard blockers.
    Format errors and invalid-difficulty clusters are always blocking
    (they reflect real data corruption, not coverage choice).
    items_vs_manifest_drift is severity=warning — surface in consistency
    but don't promote to blocking_reasons.
    """
    reasons: list[str] = []
    for d in consistency.get("drifts", []):
        if d.get("severity") != "blocking":
            continue
        kind = d.get("kind", "")
        if kind == "items_vs_qql_drift":
            reasons.append(
                f"consistency_drift: items={d['items']} qql={d['qql']} "
                f"delta={d['delta']}"
            )
        elif kind == "qql_vs_manifest_drift":
            reasons.append(
                f"consistency_drift: qql={d['qql']} manifest={d['manifest']} "
                f"delta={d['delta']}"
            )
    for fe in consistency.get("format_errors", []):
        reasons.append(
            f"consistency_format_error: {fe['kind']} in {fe['file']} "
            f"(marker={fe.get('marker', '?')!r})"
        )
    for ide in consistency.get("invalid_difficulty_files", []):
        reasons.append(
            f"consistency_invalid_difficulty: {ide['file']} "
            f"({ide['invalid_count']} non-F/S/C value(s))"
        )
    return reasons


def _derive_status(*, has_topics: bool, has_manifest: bool,
                   total_questions: int, legacy_count: int,
                   orphan_count: int, blocking_reasons: list[str],
                   missing_layers: list[str],
                   warn_drift_count: int = 0) -> str:
    """Derive pass/warn/fail status from evidence.

    Orphans always cause at least warn, even with manifest.
    Missing content layers are a hard fail.
    Items/QQL subset drift (info severity) is at least a warn — the
    manager must see the delta before signing off on closeout
    (Codex Q1 — items < qql was silently passing before).
    """
    if blocking_reasons:
        return "fail"
    if missing_layers:
        return "fail"
    if legacy_count > 0:
        return "warn"
    if orphan_count > 10:
        return "warn"
    if warn_drift_count > 0:
        return "warn"
    if total_questions == 0:
        return "warn"
    return "pass"


def _derive_next_action(status: str, blocking_reasons: list[str],
                        missing_layers: list[str]) -> str:
    """Suggest next action based on verification status."""
    if status == "pass":
        return "ready_for_subject_closeout"
    if status == "warn":
        return "review_warnings_before_closeout"
    # fail
    if missing_layers:
        return f"create_missing_content_layers: {','.join(missing_layers)}"
    if any("manifest" in r.lower() for r in blocking_reasons):
        return "create_or_fix_qa_manifest"
    if any("topic" in r.lower() for r in blocking_reasons):
        return "create_or_fix_topic_outline"
    if any("question" in r.lower() or "content" in r.lower() for r in blocking_reasons):
        return "add_question_content"
    if any("directory" in r.lower() for r in blocking_reasons):
        return "create_subject_content_directory"
    return "review_blocking_reasons"


# ── Public API ──────────────────────────────────────────────────────


def verify_subject(content_dir: str | Path,
                   subject_slug: str) -> dict:
    """Run full artifact verification for a single subject.

    Returns a structured result dict with at minimum:
      subject_slug, scope, status, topic_count, qa_count, qql_count,
      items_count, total_questions, difficulty_distribution, has_manifest,
      manifest_path, id_mapping, orphan_candidates, legacy_fragment_present,
      legacy_fragments, blocking_reasons, next_action, evidence.
    """
    content_dir = Path(content_dir)
    subject_dir = content_dir / subject_slug
    blocking_reasons: list[str] = []
    missing_layers: list[str] = []

    if not subject_dir.exists():
        result = _empty_result(subject_slug, scope="subject")
        result["blocking_reasons"] = ["subject_directory_not_found"]
        result["next_action"] = "create_subject_content_directory"
        result["evidence"] = {
            "content_dir": str(content_dir),
            "root_cause": "subject_directory_not_found",
        }
        return result

    # ── Topic outline ─────────────────────────────────────────────
    outline_path = subject_dir / "topic-outline.md"
    topics = _parse_topic_outline(outline_path)
    topic_count = len(topics)
    if topic_count == 0:
        blocking_reasons.append("missing_topic_outline_or_empty")
    topic_ids = set(topics.keys())

    # ── Content layers ────────────────────────────────────────────
    layer_stats: dict[str, list[dict]] = {}
    for layer in _KNOWN_CONTENT_LAYERS:
        layer_stats[layer] = _read_layer_files(subject_dir / layer)

    qa_count = sum(f["question_count"] for f in layer_stats.get("qa", []))
    qql_count = sum(f["question_count"] for f in layer_stats.get("qa-question-level", []))
    items_count = sum(f["question_count"] for f in layer_stats.get("items", []))
    total_questions = qa_count + qql_count + items_count

    # ── Layer presence enforcement ────────────────────────────────
    for layer in _KNOWN_CONTENT_LAYERS:
        layer_dir = subject_dir / layer
        if not layer_dir.exists() or not list(layer_dir.glob("*.md")):
            missing_layers.append(layer)

    # ── Difficulty distribution ───────────────────────────────────
    all_diffs: list[str] = []
    for layer_files in layer_stats.values():
        for fstat in layer_files:
            all_diffs.extend(fstat.get("difficulties", []))
    difficulty_distribution = dict(sorted(Counter(
        d for d in all_diffs if d in _VALID_DIFFICULTIES
    ).items()))

    # ── Manifest ──────────────────────────────────────────────────
    manifest_path = subject_dir / "qa-manifest.csv"
    has_manifest = manifest_path.exists()
    manifest_rows_data = _read_manifest(manifest_path) if has_manifest else []
    manifest_file_set: set[str] = set()
    # manifest_claimed_total = sum of question_count values in manifest rows.
    # Used for drift comparison against qql_count / items_count, which
    # represent parsed question totals (not file counts).
    manifest_claimed_total = 0
    if has_manifest:
        for row in manifest_rows_data:
            qa_file = row.get("qa_file", "")
            if qa_file:
                manifest_file_set.add(qa_file)
                manifest_file_set.add(Path(qa_file).name)
            try:
                manifest_claimed_total += int(row.get("question_count") or 0)
            except (TypeError, ValueError):
                pass

    if not has_manifest:
        blocking_reasons.append("missing_qa_manifest")
    if total_questions == 0:
        blocking_reasons.append("no_questions_found_in_any_layer")

    # ── ID mapping + cross-layer Q-ID set for orphan detection ───
    id_mapping = _build_id_mapping(layer_stats)
    qid_file_counts = _qid_file_count(layer_stats)

    # ── Orphan detection ──────────────────────────────────────────
    orphan_candidates = _detect_orphans(
        subject_dir, topic_ids=topic_ids,
        manifest_files=manifest_file_set,
        qid_file_counts=qid_file_counts,
    )

    # ── Legacy fragments ──────────────────────────────────────────
    legacy_fragments = _detect_legacy_fragments(subject_dir)

    # ── Package 2: artifact consistency (drifts / format / difficulty) ──
    consistency = _compute_consistency(
        qa_count=qa_count, qql_count=qql_count,
        items_count=items_count, manifest_rows=manifest_claimed_total,
        layer_stats=layer_stats, missing_layers=missing_layers,
    )
    # Surface consistency findings as blocking_reasons so the closeout
    # gate cannot miss them. Each drift/format/difficulty becomes one.
    blocking_reasons.extend(_consistency_to_blocking_reasons(consistency))

    # Items<QQL drift is informational severity but must still surface
    # as at least a warn (Codex Q1). Count these so _derive_status
    # can downgrade pass → warn and let the closeout gate block
    # (warn already blocks per Codex Q9 fix).
    warn_drift_count = sum(
        1 for d in consistency.get("drifts", [])
        if d.get("severity") not in ("blocking",)
        and d.get("severity")  # only count actual drifts, not empty severity
    )

    # ── Status derivation ─────────────────────────────────────────
    status = _derive_status(
        has_topics=(topic_count > 0),
        has_manifest=has_manifest,
        total_questions=total_questions,
        legacy_count=len(legacy_fragments),
        orphan_count=len(orphan_candidates),
        blocking_reasons=blocking_reasons,
        missing_layers=missing_layers,
        warn_drift_count=warn_drift_count,
    )

    return {
        "subject_slug": subject_slug,
        "scope": "subject",
        "status": status,
        "topic_count": topic_count,
        "qa_count": qa_count,
        "qql_count": qql_count,
        "items_count": items_count,
        "total_questions": total_questions,
        "missing_layers": missing_layers,
        "difficulty_distribution": difficulty_distribution,
        "has_manifest": has_manifest,
        "manifest_path": str(manifest_path) if has_manifest else "",
        "manifest_rows": len(manifest_rows_data),
        "id_mapping": id_mapping,
        "orphan_candidates": orphan_candidates,
        "legacy_fragment_present": len(legacy_fragments) > 0,
        "legacy_fragments": legacy_fragments,
        "consistency": consistency,
        "blocking_reasons": blocking_reasons,
        "next_action": _derive_next_action(status, blocking_reasons, missing_layers),
        "evidence": {
            "content_dir": str(content_dir),
            "source_paths": {
                "qa_dir": str(subject_dir / "qa") if (subject_dir / "qa").exists() else "",
                "qql_dir": str(subject_dir / "qa-question-level") if (subject_dir / "qa-question-level").exists() else "",
                "items_dir": str(subject_dir / "items") if (subject_dir / "items").exists() else "",
                "topic_outline": str(outline_path) if outline_path.exists() else "",
                "manifest": str(manifest_path) if has_manifest else "",
            },
            "consistency_summary": {
                "drift_count": consistency["drift_count"],
                "format_error_count": consistency["format_error_count"],
                "invalid_difficulty_count": consistency["invalid_difficulty_count"],
                "scoped_total": consistency["scoped_total"],
            },
        },
    }


def verify_package(content_dir: str | Path,
                   package_slug: str) -> dict:
    """Verify a package/batch directory (narrower scope than verify_subject).

    Package verification is lighter-weight: checks that the directory exists
    and has at least minimal content. Does NOT attempt subject-level closeout.
    """
    content_dir = Path(content_dir)
    pkg_dir = content_dir / package_slug
    blocking_reasons: list[str] = []
    total_questions = 0
    topic_count = 0

    if not pkg_dir.exists():
        blocking_reasons.append("package_directory_not_found")

    if pkg_dir.exists():
        outline_path = pkg_dir / "topic-outline.md"
        if outline_path.exists():
            topics = _parse_topic_outline(outline_path)
            topic_count = len(topics)

        for layer in _KNOWN_CONTENT_LAYERS:
            layer_dir = pkg_dir / layer
            if layer_dir.exists():
                for f in layer_dir.glob("*.md"):
                    text = f.read_text(encoding="utf-8")
                    total_questions += len(_parse_question_ids(text))

    if topic_count == 0 and not blocking_reasons:
        blocking_reasons.append("package_missing_topic_outline")

    status = "pass" if not blocking_reasons else "fail"

    return {
        "subject_slug": package_slug,
        "scope": "package",
        "status": status,
        "topic_count": topic_count,
        "total_questions": total_questions,
        "has_manifest": False,
        "manifest_path": "",
        "blocking_reasons": blocking_reasons,
        "next_action": "review_package_verification" if status == "fail" else "ready_for_batch_closeout",
        "evidence": {
            "content_dir": str(content_dir),
            "note": "package_scope_only_not_subject_closeout",
        },
    }


def subject_closeout_gate(*, task: dict | None,
                          verifier_result: dict,
                          content_dir: str = "") -> dict:
    """Subject closeout gate: integrates task state with verifier result.

    Returns:
      closeout_allowed: bool
      blocking_reasons: list[str]
      recommended_action: str
      verifier_status: str
      combined_evidence: dict

    Hard blocks:
      - verifier scope is not 'subject' (package results can never close out a subject)
      - verifier status is 'fail'
      - task verdict is not 'approved'
      - task status is not 'delivered'
    """
    task = task or {}
    blocking: list[str] = []

    # HARD BLOCK: non-subject scope verifier results cannot close out subjects
    vscope = verifier_result.get("scope", "")
    if vscope != "subject":
        blocking.append(f"verifier_scope_is_{vscope}_not_subject")
        return {
            "closeout_allowed": False,
            "blocking_reasons": blocking,
            "recommended_action": "use_subject_verifier_not_package_verifier",
            "verifier_status": verifier_result.get("status", "fail"),
            "verifier_scope": vscope,
            "verifier_next_action": verifier_result.get("next_action", ""),
            "combined_evidence": {
                "task_verdict": str(task.get("verdict") or ""),
                "task_status": str(task.get("status") or ""),
                "verifier_status": verifier_result.get("status", ""),
                "verifier_blocking_reasons": verifier_result.get("blocking_reasons", []),
                "content_dir": content_dir,
            },
        }

    vstatus = verifier_result.get("status", "fail")
    task_verdict = str(task.get("verdict") or "")
    task_status = str(task.get("status") or "")
    consistency_summary = verifier_result.get("consistency", {}) or {}

    # Defense-in-depth: a forged or stub verifier_result that omits the
    # `consistency` payload must NOT silently pass closeout. If consistency
    # evidence is missing entirely, treat it as a fail (cannot prove internal
    # agreement). This blocks the attack pattern of forging
    # {"scope": "subject", "status": "pass", "blocking_reasons": []}.
    if not consistency_summary:
        blocking.append("verifier_consistency_payload_missing")

    # Defense-in-depth: even if status="pass", any drift flagged as severity=blocking
    # inside the consistency summary must still block. This catches the case
    # where vstatus is "pass" but blocking_reasons was emptied by a buggy caller.
    for d in consistency_summary.get("drifts", []):
        if d.get("severity") == "blocking":
            kind = d.get("kind", "unknown")
            blocking.append(f"verifier_consistency_blocking_drift:{kind}")
            break

    # Core rule: verifier must return status="pass" for closeout.
    # warn and fail both block. (Codex Q9: workflow doc at
    # docs/workflows/igcse-subject-launch/checklist.md states
    # "verify_subject returns status != pass blocks closeout".)
    if vstatus == "warn":
        blocking.append("subject_verifier_warn_blocks_closeout")
    if vstatus == "fail":
        blocking.append("subject_verifier_failed")
        for reason in verifier_result.get("blocking_reasons", []):
            blocking.append(f"verifier: {reason}")

    # Task must be approved
    if task_verdict != "approved":
        blocking.append("task_verdict_not_approved")

    # Task must be delivered
    if task_status != "delivered":
        blocking.append("task_not_delivered")

    closeout_allowed = len(blocking) == 0

    return {
        "closeout_allowed": closeout_allowed,
        "blocking_reasons": blocking,
        "recommended_action": (
            "proceed_with_manager_closeout"
            if closeout_allowed
            else "resolve_blocking_reasons_before_closeout"
        ),
        "verifier_status": vstatus,
        "verifier_scope": vscope,
        "verifier_next_action": verifier_result.get("next_action", ""),
        "combined_evidence": {
            "task_verdict": task_verdict,
            "task_status": task_status,
            "verifier_status": vstatus,
            "verifier_blocking_reasons": verifier_result.get("blocking_reasons", []),
            "orphan_candidates": len(verifier_result.get("orphan_candidates", [])),
            "legacy_fragments": len(verifier_result.get("legacy_fragments", [])),
            "consistency": {
                "drift_count": consistency_summary.get("drift_count", 0),
                "format_error_count": consistency_summary.get("format_error_count", 0),
                "invalid_difficulty_count": consistency_summary.get("invalid_difficulty_count", 0),
                "scoped_total": consistency_summary.get("scoped_total", 0),
            },
            "content_dir": content_dir,
        },
    }


def compact_summary(verifier_result: dict) -> dict:
    """Produce a compact summary suitable for subject-inventory display.

    Excludes full evidence payloads to avoid polluting manager-panel output.
    Includes a `consistency` summary so manager-panel can render
    drift / format-error / invalid-difficulty evidence without loading the
    full verifier result.
    """
    consistency = verifier_result.get("consistency") or {}
    return {
        "subject_slug": verifier_result.get("subject_slug", ""),
        "scope": verifier_result.get("scope", "subject"),
        "status": verifier_result.get("status", "fail"),
        "topic_count": verifier_result.get("topic_count", 0),
        "total_questions": verifier_result.get("total_questions", 0),
        "qa_count": verifier_result.get("qa_count", 0),
        "qql_count": verifier_result.get("qql_count", 0),
        "items_count": verifier_result.get("items_count", 0),
        "missing_layers": verifier_result.get("missing_layers", []),
        "has_manifest": verifier_result.get("has_manifest", False),
        "legacy_fragment_present": verifier_result.get("legacy_fragment_present", False),
        "orphan_candidate_count": len(verifier_result.get("orphan_candidates", [])),
        "consistency": {
            "drifts": consistency.get("drifts", []),
            "format_errors": consistency.get("format_errors", []),
            "invalid_difficulty_files": consistency.get("invalid_difficulty_files", []),
            "scoped_total": consistency.get("scoped_total", 0),
            "drift_count": consistency.get("drift_count", 0),
            "format_error_count": consistency.get("format_error_count", 0),
            "invalid_difficulty_count": consistency.get("invalid_difficulty_count", 0),
        },
        "blocking_reasons": verifier_result.get("blocking_reasons", []),
        "next_action": verifier_result.get("next_action", ""),
    }
