#!/usr/bin/env python3
"""
Validate assessment skill packages after remediation.

Checks:
1. Cross-system contamination (SKILL.md/source-index system vs metadata system)
2. EK quality gate (no empty/placeholder essential_knowledge)
3. Assessment structure validation (paper/unit count, weighting sanity)
4. Profile routing consistency (metadata system vs source_layout_profile)

Usage:
    python3 validate_packages.py [--pkg-dir PATH] [--pkg NAME] [--json]
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Profile routing table
PROFILE_ROUTING = {
    "CAIE IGCSE": "caie_igcse_syllabus",
    "CAIE A-Level": "caie_alevel_syllabus",
    "CAIE AS & A Level": "caie_alevel_syllabus",
    "Edexcel International A-Level": "edexcel_ial_specification",
    "AQA International A-Level": "oxfordaqa_ial_specification",
    "DSE": "dse_syllabus",
}

EK_PLACEHOLDERS = [
    "Subject-wide overview and framework.",
    "subject-wide overview and framework",
    "Overview and framework",
    "General syllabus framework",
    "AS & A Level .* syllabus framework.",
]

SEVERITY_ORDER = {"P0": 0, "P1": 1, "P2": 2}


def check_contamination(pkg_path: Path, meta: dict) -> list[dict]:
    """Axis 0: Cross-system contamination check."""
    findings = []
    system = meta.get("system", "")

    # Check SKILL.md
    skill_md = pkg_path / "SKILL.md"
    if skill_md.exists():
        content = skill_md.read_text(encoding="utf-8")

        # Check System: line
        sys_match = re.search(r"^- System:\s*(.+)$", content, re.MULTILINE)
        if sys_match:
            skill_system = sys_match.group(1).strip()
            if skill_system != system:
                findings.append(
                    {
                        "severity": "P0",
                        "axis": "contamination",
                        "file": "SKILL.md",
                        "message": f"System mismatch: SKILL.md says '{skill_system}', metadata says '{system}'",
                    }
                )

        # Check for hardcoded "CAIE IGCSE" in non-IGCSE packages
        if "igcse" not in system.lower():
            if "CAIE IGCSE" in content or "Cambridge IGCSE" in content:
                findings.append(
                    {
                        "severity": "P0",
                        "axis": "contamination",
                        "file": "SKILL.md",
                        "message": f"CAIE IGCSE contamination found in non-IGCSE package (system={system})",
                    }
                )

    # Check source-index.md
    si = pkg_path / "references" / "source-index.md"
    if si.exists():
        si_content = si.read_text(encoding="utf-8")
        si_sys = re.search(r"- system:\s*`?([^`\n]+)`?", si_content)
        if si_sys:
            si_system = si_sys.group(1).strip()
            if si_system != system:
                findings.append(
                    {
                        "severity": "P0",
                        "axis": "contamination",
                        "file": "references/source-index.md",
                        "message": f"System mismatch: source-index says '{si_system}', metadata says '{system}'",
                    }
                )

    return findings


def check_profile_routing(meta: dict) -> list[dict]:
    """Axis 1: Profile routing consistency."""
    findings = []
    system = meta.get("system", "")
    sp = meta.get("source_provenance", [{}])[0] if meta.get("source_provenance") else {}
    profile = sp.get("source_layout_profile", "")

    expected = PROFILE_ROUTING.get(system)
    if expected and profile != expected:
        # Special case: DSE-CA packages use dse_curriculum_assessment_guide
        if system == "DSE" and profile == "dse_curriculum_assessment_guide":
            pass  # This is valid for C&A Guide packages
        else:
            findings.append(
                {
                    "severity": "P0",
                    "axis": "profile_routing",
                    "file": "metadata.json",
                    "message": f"Profile mismatch: system='{system}' requires '{expected}', got '{profile}'",
                }
            )

    return findings


def check_ek_quality(pkg_path: Path, meta: dict) -> list[dict]:
    """Axis 2: Essential Knowledge quality gate."""
    findings = []
    tj = pkg_path / "topics.json"
    if not tj.exists():
        return [
            {
                "severity": "P0",
                "axis": "ek_quality",
                "file": "topics.json",
                "message": "topics.json not found",
            }
        ]

    try:
        data = json.loads(tj.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [
            {
                "severity": "P0",
                "axis": "ek_quality",
                "file": "topics.json",
                "message": "topics.json parse error",
            }
        ]

    topics = data.get("topics", [])
    if not topics:
        return [
            {
                "severity": "P0",
                "axis": "ek_quality",
                "file": "topics.json",
                "message": "topics array is empty",
            }
        ]

    empty_ek_count = 0
    placeholder_ek_count = 0
    total_discipline_topics = 0

    for topic in topics:
        name = topic.get("topic_name", "")
        # Skip root node and non-discipline placeholders
        if topic.get("parent_id", "") == "":
            continue  # root node
        if name.startswith(("Why choose", "Syllabus overview", "What else")):
            continue  # non-discipline placeholder

        total_discipline_topics += 1
        ek = topic.get("essential_knowledge", [])

        if not ek or ek == []:
            empty_ek_count += 1
        elif len(ek) == 1:
            text = ek[0].get("text", "") if isinstance(ek[0], dict) else str(ek[0])
            is_placeholder = False
            for ph in EK_PLACEHOLDERS:
                if re.match(ph, text, re.IGNORECASE):
                    is_placeholder = True
                    break
            if is_placeholder:
                placeholder_ek_count += 1

    if total_discipline_topics > 0:
        if empty_ek_count == total_discipline_topics:
            findings.append(
                {
                    "severity": "P1",
                    "axis": "ek_quality",
                    "file": "topics.json",
                    "message": f"All {total_discipline_topics} discipline topics have empty EK arrays",
                }
            )
        elif empty_ek_count > 0:
            findings.append(
                {
                    "severity": "P1",
                    "axis": "ek_quality",
                    "file": "topics.json",
                    "message": f"{empty_ek_count}/{total_discipline_topics} discipline topics have empty EK",
                }
            )

        if placeholder_ek_count > 0:
            findings.append(
                {
                    "severity": "P1",
                    "axis": "ek_quality",
                    "file": "topics.json",
                    "message": f"{placeholder_ek_count}/{total_discipline_topics} topics have placeholder EK "
                    f"(e.g. 'Subject-wide overview and framework.')",
                }
            )

    # Check for non-discipline placeholder topics that should be removed
    placeholder_names = []
    for topic in topics:
        name = topic.get("topic_name", "")
        if name.startswith(
            ("Why choose", "Syllabus overview", "What else you need to know")
        ):
            placeholder_names.append(name)
    if placeholder_names:
        findings.append(
            {
                "severity": "P2",
                "axis": "ek_quality",
                "file": "topics.json",
                "message": f"Non-discipline placeholder topics present: {placeholder_names}",
            }
        )

    return findings


def check_assessment_structure(pkg_path: Path, meta: dict) -> list[dict]:
    """Axis 3: Assessment structure validation."""
    findings = []
    system = meta.get("system", "")

    aj = pkg_path / "assessment.json"
    if not aj.exists():
        return [
            {
                "severity": "P1",
                "axis": "assessment",
                "file": "assessment.json",
                "message": "assessment.json not found",
            }
        ]

    try:
        data = json.loads(aj.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [
            {
                "severity": "P0",
                "axis": "assessment",
                "file": "assessment.json",
                "message": "assessment.json parse error",
            }
        ]

    papers = data.get("papers", [])
    if not papers:
        findings.append(
            {
                "severity": "P1",
                "axis": "assessment",
                "file": "assessment.json",
                "message": "No papers defined",
            }
        )
        return findings

    # Check for 3-paper template contamination (120min/100marks/33.33%)
    template_count = sum(
        1
        for p in papers
        if p.get("duration_minutes") == 120
        and p.get("total_marks") == 100
        and abs(p.get("weighting_percent", 0) - 33.33) < 0.5
    )
    if template_count >= 3 and system not in ["CAIE IGCSE", "CAIE A-Level"]:
        findings.append(
            {
                "severity": "P0",
                "axis": "assessment",
                "file": "assessment.json",
                "message": f"Suspicious 3-paper template detected: {template_count} papers "
                f"with identical 120min/100marks/33.33% structure (system={system})",
            }
        )

    # Check weighting sanity
    total_weight = sum(p.get("weighting_percent", 0) for p in papers)
    if total_weight > 0 and abs(total_weight - 100) > 5:
        findings.append(
            {
                "severity": "P0",
                "axis": "assessment",
                "file": "assessment.json",
                "message": f"Weighting total is {total_weight:.1f}%, expected ~100%",
            }
        )

    # Check for duplicate paper structures
    paper_sigs = []
    for p in papers:
        sig = (
            p.get("duration_minutes"),
            p.get("total_marks"),
            p.get("weighting_percent"),
        )
        paper_sigs.append(sig)
    if len(set(paper_sigs)) == 1 and len(papers) > 2:
        findings.append(
            {
                "severity": "P1",
                "axis": "assessment",
                "file": "assessment.json",
                "message": f"All {len(papers)} papers have identical structure "
                f"({paper_sigs[0][0]}min/{paper_sigs[0][1]}marks/{paper_sigs[0][2]}%)",
            }
        )

    return findings


def check_topic_completeness(pkg_path: Path, meta: dict) -> list[dict]:
    """Axis 4: Topic tree completeness (basic sanity check)."""
    findings = []
    tj = pkg_path / "topics.json"
    if not tj.exists():
        return []

    try:
        data = json.loads(tj.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    topics = data.get("topics", [])
    # Count discipline topics (excluding root and placeholders)
    discipline = [
        t
        for t in topics
        if t.get("parent_id", "") != ""
        and not t.get("topic_name", "").startswith(
            ("Why choose", "Syllabus overview", "What else")
        )
    ]

    if len(discipline) < 3:
        findings.append(
            {
                "severity": "P1",
                "axis": "topic_completeness",
                "file": "topics.json",
                "message": f"Only {len(discipline)} discipline topics found (expected 5+ for most syllabi)",
            }
        )

    # Check for empty-shell unit names
    shell_names = [
        t["topic_name"]
        for t in discipline
        if re.match(r"^Unit\s+\d+$", t.get("topic_name", ""))
        or re.match(r"^Topic\s+\d+$", t.get("topic_name", ""))
    ]
    if shell_names:
        findings.append(
            {
                "severity": "P1",
                "axis": "topic_completeness",
                "file": "topics.json",
                "message": f"Empty-shell topic names without descriptive titles: {shell_names[:5]}",
            }
        )

    # Check for duplicate topic names
    names = [t.get("topic_name", "") for t in discipline]
    dupes = [n for n in names if names.count(n) > 1]
    if dupes:
        findings.append(
            {
                "severity": "P1",
                "axis": "topic_completeness",
                "file": "topics.json",
                "message": f"Duplicate topic names: {list(set(dupes))[:5]}",
            }
        )

    return findings


def validate_package(pkg_path: Path) -> dict:
    """Run all validation axes on a single package."""
    mj = pkg_path / "metadata.json"
    if not mj.exists():
        return {"package": pkg_path.name, "status": "skip", "findings": []}

    try:
        meta = json.loads(mj.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "package": pkg_path.name,
            "status": "error",
            "findings": [
                {
                    "severity": "P0",
                    "axis": "metadata",
                    "message": "metadata.json parse error",
                }
            ],
        }

    all_findings = []
    all_findings.extend(check_contamination(pkg_path, meta))
    all_findings.extend(check_profile_routing(meta))
    all_findings.extend(check_ek_quality(pkg_path, meta))
    all_findings.extend(check_assessment_structure(pkg_path, meta))
    all_findings.extend(check_topic_completeness(pkg_path, meta))

    # Sort by severity
    all_findings.sort(key=lambda f: SEVERITY_ORDER.get(f["severity"], 99))

    # Determine overall status
    has_p0 = any(f["severity"] == "P0" for f in all_findings)
    has_p1 = any(f["severity"] == "P1" for f in all_findings)

    if has_p0:
        status = "fail"
    elif has_p1:
        status = "warn"
    elif all_findings:
        status = "warn"  # P2 only
    else:
        status = "pass"

    return {
        "package": pkg_path.name,
        "system": meta.get("system", ""),
        "subject": meta.get("subject", ""),
        "status": status,
        "p0_count": sum(1 for f in all_findings if f["severity"] == "P0"),
        "p1_count": sum(1 for f in all_findings if f["severity"] == "P1"),
        "p2_count": sum(1 for f in all_findings if f["severity"] == "P2"),
        "findings": all_findings,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate assessment skill packages")
    parser.add_argument("--pkg-dir", type=str, default=None)
    parser.add_argument(
        "--pkg", type=str, default=None, help="Validate a single package by name"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.pkg_dir:
        pkg_dir = Path(args.pkg_dir)
    else:
        script_dir = Path(__file__).resolve().parent
        pkg_dir = script_dir.parent / "pilot-output" / "assessment-skills"

    if args.pkg:
        pkg_path = pkg_dir / args.pkg
        if not pkg_path.exists():
            print(f"ERROR: package not found: {pkg_path}", file=sys.stderr)
            sys.exit(1)
        result = validate_package(pkg_path)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print_report([result])
        return

    results = []
    for pkg_path in sorted(pkg_dir.iterdir()):
        if not pkg_path.is_dir() or pkg_path.name.startswith("."):
            continue
        if pkg_path.name.startswith("ap-"):
            continue
        results.append(validate_package(pkg_path))

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print_report(results)


def print_report(results: list[dict]):
    """Print human-readable report."""
    print("=" * 100)
    print("ASSESSMENT SKILL PACKAGE VALIDATION REPORT")
    print("=" * 100)
    print()

    pass_count = sum(1 for r in results if r["status"] == "pass")
    warn_count = sum(1 for r in results if r["status"] == "warn")
    fail_count = sum(1 for r in results if r["status"] == "fail")
    skip_count = sum(1 for r in results if r["status"] == "skip")

    print(
        f"Total: {len(results)} | Pass: {pass_count} | Warn: {warn_count} | Fail: {fail_count} | Skip: {skip_count}"
    )
    print()

    for r in results:
        if r["status"] == "skip":
            continue

        status_icon = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}.get(
            r["status"], "?"
        )
        print(
            f"[{status_icon}] {r['package']} ({r.get('system', '?')} {r.get('subject', '?')})"
        )

        for f in r.get("findings", []):
            print(f"  [{f['severity']}] {f['axis']}: {f['message']}")

        if not r.get("findings"):
            print("  No issues found")
        print()


if __name__ == "__main__":
    main()
