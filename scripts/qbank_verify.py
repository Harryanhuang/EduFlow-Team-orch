#!/usr/bin/env python3
"""QBank verification toolkit.

Scans all closed-loop IGCSE subject directories under content/,
parses Question entities from the three content layers (qa/,
qa-question-level/, items/), validates schema compliance,
detects duplicates, checks consistency, and produces a unified
manifest + verification report.

Usage:
    python scripts/qbank_verify.py [--content-dir content] [--json]
"""

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path

VALID_DIFFICULTIES = {"Foundation", "Standard", "Challenge"}

QUESTION_ENTITY_RE = re.compile(
    r"(?:###\s+Question\s+|#\s+(?:QQL:|[Qq]uestion)[:\s]+(?:QQL:?\s*)?(?:Question\s*)?)(Q-\S+)(?:\s+\([^)]+\))?\s*\n"
    r"(.*?)(?=\n(?:###\s+Question\s+|#\s+(?:QQL:|[Qq]uestion)[:\s]+(?:QQL:?\s*)?(?:Question\s*)?)Q-|\Z)",
    re.DOTALL,
)

FIELD_RE = {
    "difficulty": re.compile(r"\*\*Difficulty\*\*:\s*(.+)"),
    "question": re.compile(r"\*\*Question\*\*:\s*(.+)"),
    "answer": re.compile(r"\*\*Answer\*\*:\s*(.+)"),
    "explanation": re.compile(r"\*\*Explanation\*\*:\s*(.+)"),
    "tags": re.compile(r"\*\*Tags\*\*:\s*(.+)"),
}

TOPIC_OUTLINE_TABLE_RE = re.compile(
    r"\|\s*(\S+)\s*\|\s*(.+?)\s*\|\s*(Core|Extended|Core\+E).*?\|",
    re.MULTILINE,
)

_IGCSE_DIR_RE = re.compile(r"^igcse-[a-z]+(?:-[a-z]+)*-\d{4}$")


@dataclass
class Question:
    question_id: str
    difficulty: str
    question: str
    answer: str
    explanation: str
    tags: str
    source_file: str
    source_layer: str  # "qa", "qa-question-level", "items"
    subject_slug: str


@dataclass
class Issue:
    severity: str  # "error", "warning", "info"
    category: str
    subject: str
    file: str
    message: str


@dataclass
class SubjectReport:
    slug: str
    name: str
    code: str
    topic_count: int = 0
    qa_topic_files: int = 0
    qa_question_level_files: int = 0
    items_files: int = 0
    total_questions: int = 0
    difficulty_dist: dict = field(default_factory=dict)
    has_manifest: bool = False
    manifest_rows: int = 0
    issues: list = field(default_factory=list)


def discover_igcse_subjects(content_dir: Path) -> dict[str, dict]:
    """Auto-discover igcse-* directories under content_dir.

    Returns a dict of {slug: {"code": "NNNN", "name": "SubjectName"}}.
    """
    subjects: dict[str, dict] = {}
    if not content_dir.exists():
        return subjects
    for entry in sorted(content_dir.iterdir()):
        if not entry.is_dir():
            continue
        if not _IGCSE_DIR_RE.match(entry.name):
            continue
        slug = entry.name
        # Extract the 4-digit code from the directory name
        code_match = re.search(r"-(\d{4})$", slug)
        code = code_match.group(1) if code_match else ""
        # Extract a human-readable name
        name_part = slug[len("igcse-"):].rsplit("-", 1)[0]
        name = " ".join(word.capitalize() for word in name_part.replace("-", " ").split())
        subjects[slug] = {"code": code, "name": name}
    return subjects


def parse_question_entities(text: str, source_file: str, layer: str, subject_slug: str) -> list:
    questions = []
    for m in QUESTION_ENTITY_RE.finditer(text):
        qid = m.group(1).rstrip("`")
        body = m.group(2)
        fields = {}
        for fname, pat in FIELD_RE.items():
            fm = pat.search(body)
            fields[fname] = fm.group(1).strip().rstrip("`") if fm else ""
        questions.append(Question(
            question_id=qid,
            difficulty=fields.get("difficulty", ""),
            question=fields.get("question", ""),
            answer=fields.get("answer", ""),
            explanation=fields.get("explanation", ""),
            tags=fields.get("tags", ""),
            source_file=source_file,
            source_layer=layer,
            subject_slug=subject_slug,
        ))
    return questions


def parse_topic_outline(path: Path) -> dict:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    topics = {}
    for m in TOPIC_OUTLINE_TABLE_RE.finditer(text):
        tid = m.group(1).strip()
        tname = m.group(2).strip()
        topics[tid] = tname
    return topics


def validate_question(q: Question) -> list:
    issues = []
    if q.difficulty not in VALID_DIFFICULTIES:
        issues.append(Issue(
            "error", "schema", q.subject_slug, q.source_file,
            f"Invalid difficulty '{q.difficulty}' for {q.question_id} "
            f"(expected one of {VALID_DIFFICULTIES})",
        ))
    if not q.question:
        issues.append(Issue(
            "error", "schema", q.subject_slug, q.source_file,
            f"Missing Question field for {q.question_id}",
        ))
    if not q.answer:
        issues.append(Issue(
            "error", "schema", q.subject_slug, q.source_file,
            f"Missing Answer field for {q.question_id}",
        ))
    if not q.explanation:
        issues.append(Issue(
            "warning", "schema", q.subject_slug, q.source_file,
            f"Missing Explanation field for {q.question_id}",
        ))
    if not q.tags:
        issues.append(Issue(
            "warning", "schema", q.subject_slug, q.source_file,
            f"Missing Tags field for {q.question_id}",
        ))
    qid_pat = re.compile(r"^Q-[A-Z]?\d+(?:\.\d+)?-\d+$")
    if not qid_pat.match(q.question_id):
        issues.append(Issue(
            "warning", "schema", q.subject_slug, q.source_file,
            f"Non-standard Question ID format: '{q.question_id}'",
        ))
    return issues


def check_duplicates(all_questions: list) -> list:
    issues = []
    by_subject_id = defaultdict(list)
    for q in all_questions:
        by_subject_id[(q.subject_slug, q.question_id)].append(q)
    for (slug, qid), qs in by_subject_id.items():
        if len(qs) < 2:
            continue
        layers = set(q.source_layer for q in qs)
        within_layer = [
            (layer, [q for q in qs if q.source_layer == layer])
            for layer in layers
        ]
        has_within_dup = any(len(qs_in_layer) > 1 for _, qs_in_layer in within_layer)
        if has_within_dup:
            for layer, qs_in_layer in within_layer:
                if len(qs_in_layer) > 1:
                    files = [f"{q.subject_slug}/{q.source_file}" for q in qs_in_layer]
                    issues.append(Issue(
                        "error", "duplicate", slug, "",
                        f"Within-layer duplicate '{qid}' in layer '{layer}': {', '.join(files)}",
                    ))
        elif len(layers) > 1:
            files = [f"{q.subject_slug}/{q.source_file}({q.source_layer})" for q in qs]
            issues.append(Issue(
                "info", "cross-layer", slug, "",
                f"Cross-layer overlap '{qid}' across {', '.join(sorted(layers))}: {', '.join(files)}",
            ))
    return issues


def scan_subject(content_dir: Path, slug: str, meta: dict) -> tuple:
    subject_dir = content_dir / slug
    if not subject_dir.exists():
        return None, [], [Issue("error", "missing", slug, "", f"Subject directory not found: {subject_dir}")]

    report = SubjectReport(slug=slug, name=meta["name"], code=meta["code"])
    all_questions = []
    issues = []

    qa_dir = subject_dir / "qa"
    if qa_dir.exists():
        qa_files = list(qa_dir.glob("*.md"))
        report.qa_topic_files = len(qa_files)
        for f in qa_files:
            text = f.read_text(encoding="utf-8")
            qs = parse_question_entities(text, str(f.relative_to(subject_dir)), "qa", slug)
            all_questions.extend(qs)

    qql_dir = subject_dir / "qa-question-level"
    if qql_dir.exists():
        qql_files = list(qql_dir.glob("*.md"))
        report.qa_question_level_files = len(qql_files)
        for f in qql_files:
            text = f.read_text(encoding="utf-8")
            qs = parse_question_entities(text, str(f.relative_to(subject_dir)), "qa-question-level", slug)
            all_questions.extend(qs)

    items_dir = subject_dir / "items"
    if items_dir.exists():
        items_files = list(items_dir.glob("*.md"))
        report.items_files = len(items_files)
        for f in items_files:
            text = f.read_text(encoding="utf-8")
            qs = parse_question_entities(text, str(f.relative_to(subject_dir)), "items", slug)
            all_questions.extend(qs)

    outline_path = subject_dir / "topic-outline.md"
    topics = parse_topic_outline(outline_path)
    report.topic_count = len(topics)

    manifest_path = subject_dir / "qa-manifest.csv"
    if manifest_path.exists():
        report.has_manifest = True
        with open(manifest_path, encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
            report.manifest_rows = len(rows)

    report.total_questions = len(all_questions)
    diff_counter = Counter(q.difficulty for q in all_questions)
    report.difficulty_dist = dict(sorted(diff_counter.items()))

    for q in all_questions:
        issues.extend(validate_question(q))

    return report, all_questions, issues


def check_manifest_consistency(content_dir: Path, slug: str, subject_dir_name: str) -> list:
    issues = []
    subject_dir = content_dir / subject_dir_name
    manifest_path = subject_dir / "qa-manifest.csv"
    if not manifest_path.exists():
        issues.append(Issue(
            "warning", "manifest", slug, "",
            "No qa-manifest.csv found — cannot verify manifest consistency",
        ))
        return issues

    with open(manifest_path, encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            qa_file = row.get("qa_file", "")
            if qa_file:
                full_path = subject_dir / qa_file
                if not full_path.exists():
                    issues.append(Issue(
                        "error", "manifest", slug, qa_file,
                        f"Manifest references missing file: {qa_file}",
                    ))
            claimed_count = row.get("question_count", "")
            if claimed_count and qa_file:
                full_path = subject_dir / qa_file
                if full_path.exists():
                    text = full_path.read_text(encoding="utf-8")
                    actual = len(QUESTION_ENTITY_RE.findall(text))
                    if actual > 0 and actual != int(claimed_count):
                        issues.append(Issue(
                            "warning", "manifest", slug, qa_file,
                            f"Manifest claims {claimed_count} questions but file has {actual} Question entities",
                        ))
    return issues


def generate_unified_manifest(all_questions: list, content_dir: Path) -> list:
    rows = []
    by_subject_topic = defaultdict(list)
    for q in all_questions:
        topic_match = re.match(r"Q-([A-Z]?\d+(?:\.\d+)?)-\d+", q.question_id)
        topic_id = topic_match.group(1) if topic_match else "unknown"
        by_subject_topic[(q.subject_slug, topic_id)].append(q)

    for (slug, topic_id), qs in sorted(by_subject_topic.items()):
        diff_dist = Counter(q.difficulty for q in qs)
        diff_mix = "|".join(
            f"{k[0]}:{v}" for k, v in sorted(diff_dist.items())
            if k in VALID_DIFFICULTIES
        )
        source_files = sorted(set(q.source_file for q in qs))
        rows.append({
            "subject_slug": slug,
            "topic_id": topic_id,
            "question_count": len(qs),
            "difficulty_mix": diff_mix,
            "source_layers": ",".join(sorted(set(q.source_layer for q in qs))),
            "source_files": ";".join(source_files),
        })
    return rows


def derive_status(report: SubjectReport, subject_issues: list) -> str:
    """Derive compact status from report and issues for this subject."""
    errors = [i for i in subject_issues if i.severity == "error"]
    warnings = [i for i in subject_issues if i.severity == "warning"]
    if not report.total_questions and not report.has_manifest:
        return "empty"
    if errors:
        return "issue_fix"
    if warnings:
        return "reverify"
    if not report.has_manifest:
        return "needs_review"
    return "ready_for_import"


def derive_next_action(status: str, has_dedup_report: bool = False) -> str:
    """Suggest next action based on QBank status."""
    actions = {
        "empty": "no_qa_found_check_content",
        "issue_fix": "fix_schema_or_manifest_errors",
        "reverify": "reverify_warnings_then_review",
        "needs_review": "review_course_review_required",
        "ready_for_import": "needs_user_authorization",
    }
    return actions.get(status, "unknown_status")


def build_compact_summary(reports: list, all_issues: list, all_questions: list) -> dict:
    """Build a compact JSON summary suitable for CLI / manager-panel consumption."""
    subject_summaries = []
    for r in reports:
        subject_issues = [i for i in all_issues if i.subject == r.slug]
        status = derive_status(r, subject_issues)
        error_count = len([i for i in subject_issues if i.severity == "error"])
        warning_count = len([i for i in subject_issues if i.severity == "warning"])
        info_count = len([i for i in subject_issues if i.severity == "info"])
        report_path = f"content/{r.slug}/qbank-verification-report.json"
        subject_summaries.append({
            "subject": r.slug,
            "name": r.name,
            "code": r.code,
            "status": status,
            "total_questions": r.total_questions,
            "topic_count": r.topic_count,
            "error_count": error_count,
            "warning_count": warning_count,
            "issue_count": error_count + warning_count + info_count,
            "has_manifest": r.has_manifest,
            "manifest_rows": r.manifest_rows,
            "difficulty_distribution": r.difficulty_dist,
            "report_path": report_path,
            "next_action": derive_next_action(status),
        })

    total_errors = len([i for i in all_issues if i.severity == "error"])
    overall_status = "PASS" if total_errors == 0 else "FAIL"

    return {
        "overall_status": overall_status,
        "total_questions": len(all_questions),
        "subjects_scanned": len(reports),
        "total_errors": total_errors,
        "total_warnings": len([i for i in all_issues if i.severity == "warning"]),
        "total_infos": len([i for i in all_issues if i.severity == "info"]),
        "within_layer_duplicates": len([i for i in all_issues if i.category == "duplicate"]),
        "cross_layer_overlaps": len([i for i in all_issues if i.category == "cross-layer"]),
        "schema_violations": len([i for i in all_issues if i.category == "schema"]),
        "manifest_issues": len([i for i in all_issues if i.category == "manifest"]),
        "subjects": subject_summaries,
    }


def get_detail_items(all_issues: list) -> list:
    """Return compact issue detail list (kept minimal for JSON output)."""
    return [
        {
            "severity": i.severity,
            "category": i.category,
            "subject": i.subject,
            "file": i.file,
            "message": i.message,
        }
        for i in all_issues
    ]


def print_report(reports: list, all_issues: list, all_questions: list):
    print("=" * 72)
    print("  QBank Verification Report")
    print("=" * 72)
    print()

    print("--- Subject Inventory ---")
    print(f"{'Subject':<30} {'Topics':>7} {'QA(q)':>7} {'QA(qql)':>8} {'Items':>7} {'Total Q':>8}")
    print("-" * 72)
    total_q = 0
    for r in reports:
        print(f"{r.slug:<30} {r.topic_count:>7} {r.qa_topic_files:>7} "
              f"{r.qa_question_level_files:>8} {r.items_files:>7} {r.total_questions:>8}")
        total_q += r.total_questions
    print("-" * 72)
    print(f"{'TOTAL':<30} {'':>7} {'':>7} {'':>8} {'':>7} {total_q:>8}")
    print()

    print("--- Difficulty Distribution ---")
    for r in reports:
        if r.difficulty_dist:
            dist_str = ", ".join(f"{k}: {v}" for k, v in r.difficulty_dist.items())
            print(f"  {r.slug}: {dist_str}")
        else:
            print(f"  {r.slug}: (no questions parsed)")
    print()

    print("--- Manifest Status ---")
    for r in reports:
        status = f"yes ({r.manifest_rows} rows)" if r.has_manifest else "MISSING"
        print(f"  {r.slug}: {status}")
    print()

    errors = [i for i in all_issues if i.severity == "error"]
    warnings = [i for i in all_issues if i.severity == "warning"]
    infos = [i for i in all_issues if i.severity == "info"]

    print(f"--- Issues: {len(errors)} errors, {len(warnings)} warnings, {len(infos)} info ---")
    for issue in all_issues:
        marker = {"error": "ERR", "warning": "WRN", "info": "INF"}[issue.severity]
        loc = f" [{issue.file}]" if issue.file else ""
        print(f"  [{marker}] {issue.category}/{issue.subject}{loc}: {issue.message}")
    print()

    print("--- Verification Summary ---")
    if errors:
        print(f"  FAIL: {len(errors)} error(s) must be resolved before import.")
    else:
        print("  PASS: No blocking errors found.")
    print(f"  Total questions parsed: {total_q}")
    print(f"  Subjects scanned: {len(reports)}")
    dup_count = len([i for i in all_issues if i.category == "duplicate"])
    cross_count = len([i for i in all_issues if i.category == "cross-layer"])
    print(f"  Within-layer duplicates: {dup_count}")
    print(f"  Cross-layer overlaps: {cross_count}")
    schema_errs = len([i for i in errors if i.category == "schema"])
    print(f"  Schema violations: {schema_errs}")
    manifest_issues = len([i for i in all_issues if i.category == "manifest"])
    print(f"  Manifest issues: {manifest_issues}")


def main():
    parser = argparse.ArgumentParser(description="QBank verification toolkit")
    parser.add_argument("--content-dir", default="content", help="Path to content directory")
    parser.add_argument("--json", action="store_true", help="Output compact JSON summary instead of text")
    parser.add_argument("--json-full", action="store_true", help="Output full JSON with all issue details")
    parser.add_argument("--manifest-out", default=None, help="Write unified manifest CSV to this path")
    args = parser.parse_args()

    content_dir = Path(args.content_dir)
    if not content_dir.exists():
        print(f"Error: content directory '{content_dir}' not found", file=sys.stderr)
        sys.exit(1)

    subjects = discover_igcse_subjects(content_dir)

    all_questions = []
    all_issues = []
    reports = []

    for slug, meta in subjects.items():
        report, questions, issues = scan_subject(content_dir, slug, meta)
        if report:
            reports.append(report)
        all_questions.extend(questions)
        all_issues.extend(issues)
        all_issues.extend(check_manifest_consistency(content_dir, slug, slug))

    all_issues.extend(check_duplicates(all_questions))

    manifest_rows = generate_unified_manifest(all_questions, content_dir)

    if args.manifest_out:
        out_path = Path(args.manifest_out)
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=[
                "subject_slug", "topic_id", "question_count",
                "difficulty_mix", "source_layers", "source_files",
            ])
            writer.writeheader()
            writer.writerows(manifest_rows)

    if args.json or args.json_full:
        summary = build_compact_summary(reports, all_issues, all_questions)
        if args.json_full:
            summary["detail_items"] = get_detail_items(all_issues)
            summary["manifest"] = manifest_rows
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print_report(reports, all_issues, all_questions)

    error_count = len([i for i in all_issues if i.severity == "error"])
    return 1 if error_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
