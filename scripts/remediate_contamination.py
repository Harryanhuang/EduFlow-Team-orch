#!/usr/bin/env python3
"""
Remediate CAIE IGCSE template contamination across all non-IGCSE assessment skill packages.

Root cause: Builder agent hardcoded "CAIE IGCSE" in SKILL.md, source-index.md, topics.json root,
and metadata.json source_layout_profile, regardless of actual exam system.

This script reads each package's metadata.json (which has the CORRECT system/subject),
then fixes the contaminated strings in all affected files.

Usage:
    python3 remediate_contamination.py [--dry-run] [--pkg-dir PATH]
"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

# ── Profile routing: system → correct source_layout_profile ──
PROFILE_ROUTING = {
    # CAIE IGCSE
    "CAIE IGCSE": "caie_igcse_syllabus",
    # CAIE A-Level / AS & A Level
    "CAIE A-Level": "caie_alevel_syllabus",
    "CAIE AS & A Level": "caie_alevel_syllabus",
    "CAIE International A-Level": "caie_alevel_syllabus",
    # Edexcel International A-Level
    "Edexcel International A-Level": "edexcel_ial_specification",
    "Pearson Edexcel International A-Level": "edexcel_ial_specification",
    "Edexcel IAL": "edexcel_ial_specification",
    # AQA / OxfordAQA International A-Level
    "AQA International A-Level": "oxfordaqa_ial_specification",
    "OxfordAQA International A-Level": "oxfordaqa_ial_specification",
    "AQA IAL": "oxfordaqa_ial_specification",
    # DSE
    "DSE": "dse_syllabus",
    "HKDSE": "dse_syllabus",
}

# ── Contamination patterns to detect ──
WRONG_SYSTEMS = ["CAIE IGCSE", "Cambridge IGCSE"]
WRONG_PROFILES = ["caie_igcse_syllabus"]  # wrong when used by non-IGCSE packages


def get_correct_profile(system: str) -> str | None:
    """Look up the correct profile for a given system name."""
    if system in PROFILE_ROUTING:
        return PROFILE_ROUTING[system]
    # Try partial match
    for key, profile in PROFILE_ROUTING.items():
        if key.lower() in system.lower() or system.lower() in key.lower():
            return profile
    return None


def is_igcse_package(system: str) -> bool:
    """Check if the system is actually CAIE IGCSE (no fix needed)."""
    return "igcse" in system.lower() and ("caie" in system.lower() or "cambridge" in system.lower())


def fix_skill_md(pkg_path: Path, system: str, subject: str, board: str, level: str,
                 assessment_code: str, dry_run: bool) -> list[str]:
    """Fix contaminated SKILL.md."""
    skill_md = pkg_path / "SKILL.md"
    if not skill_md.exists():
        return ["SKIP: SKILL.md not found"]

    content = skill_md.read_text(encoding="utf-8")
    original = content
    changes = []

    # Fix frontmatter description
    # Pattern: "Scope and assessment model for Cambridge IGCSE {Subject} ({code})."
    old_desc_pattern = re.compile(
        r'(description:\s*)Scope and assessment model for (?:Cambridge |CAIE )IGCSE (\w[\w\s]*?)(\s*\()',
        re.MULTILINE
    )
    m = old_desc_pattern.search(content)
    if m:
        new_desc = f"{m.group(1)}Scope and assessment model for {system} {subject} ("
        content = content[:m.start()] + new_desc + content[m.end():]
        changes.append(f"frontmatter description: 'Cambridge IGCSE {m.group(2)}' -> '{system} {subject}'")

    # Fix body: "Assessment skill for the Cambridge IGCSE {Subject} syllabus."
    body_fix = re.sub(
        r'Assessment skill for the (?:Cambridge |CAIE )IGCSE (\w+) syllabus\.',
        f'Assessment skill for the {system} {subject} specification.',
        content,
        count=1,
    )
    if body_fix != content:
        content = body_fix
        changes.append(f"body overview: 'Cambridge IGCSE syllabus' -> '{system} specification'")

    # Fix body: "classify, route, or scope {subject} content against the CAIE IGCSE syllabus"
    route_fix = re.sub(
        r'against the (?:CAIE IGCSE|Cambridge IGCSE) syllabus',
        f'against the {system} specification',
        content,
    )
    if route_fix != content:
        content = route_fix
        changes.append(f"body route: 'against CAIE IGCSE syllabus' -> 'against {system} specification'")

    # Fix "- System: CAIE IGCSE"
    old_system_line = re.search(r'^- System:\s*(?:CAIE IGCSE|Cambridge IGCSE)\s*$', content, re.MULTILINE)
    if old_system_line:
        new_system_line = f"- System: {system}"
        content = content[:old_system_line.start()] + new_system_line + content[old_system_line.end():]
        changes.append(f"System field: 'CAIE IGCSE' -> '{system}'")

    # Fix "route {subject} items to CAIE IGCSE topics"
    topic_fix = re.sub(
        r'to (?:CAIE IGCSE|Cambridge IGCSE) topics',
        f'to {system} topics',
        content,
    )
    if topic_fix != content:
        content = topic_fix

    # Fix inline source-index section if present
    # "- system: `CAIE IGCSE`"
    content = re.sub(
        r'(- system:\s*`)(?:CAIE IGCSE|Cambridge IGCSE)(`)',
        f'\\g<1>{system}\\g<2>',
        content,
    )
    # "- source_layout_profile: `caie_igcse_syllabus`"
    correct_profile = get_correct_profile(system)
    if correct_profile:
        content = re.sub(
            r'(- source_layout_profile:\s*`)caie_igcse_syllabus(`)',
            f'\\g<1>{correct_profile}\\g<2>',
            content,
        )

    # Fix "Source evidence bundle for the CAIE IGCSE {Subject} syllabus"
    content = re.sub(
        r'Source evidence bundle for the (?:CAIE IGCSE|Cambridge IGCSE) (\w+) syllabus',
        f'Source evidence bundle for the {system} \\1 specification',
        content,
    )

    if content != original:
        if not dry_run:
            # Backup
            bak = skill_md.with_suffix('.md.bak')
            if not bak.exists():
                shutil.copy2(skill_md, bak)
            skill_md.write_text(content, encoding="utf-8")
        return changes if changes else ["SKILL.md: contamination strings replaced"]
    return []


def fix_source_index(pkg_path: Path, system: str, subject: str, dry_run: bool) -> list[str]:
    """Fix contaminated references/source-index.md."""
    si = pkg_path / "references" / "source-index.md"
    if not si.exists():
        return ["SKIP: references/source-index.md not found"]

    content = si.read_text(encoding="utf-8")
    original = content
    changes = []

    correct_profile = get_correct_profile(system)

    # Fix "Source evidence bundle for the CAIE IGCSE {Subject} syllabus"
    new_content = re.sub(
        r'Source evidence bundle for the (?:CAIE IGCSE|Cambridge IGCSE) (\w+) syllabus',
        f'Source evidence bundle for the {system} \\1 specification',
        content,
    )

    # Fix "- system: `CAIE IGCSE`" or "- system: CAIE IGCSE"
    new_content = re.sub(
        r'(- system:\s*`?)(?:CAIE IGCSE|Cambridge IGCSE)(`?)',
        f'\\g<1>{system}\\g<2>',
        new_content,
    )

    # Fix "- source_layout_profile: `caie_igcse_syllabus`"
    if correct_profile:
        new_content = re.sub(
            r'(- source_layout_profile:\s*`?)caie_igcse_syllabus(`?)',
            f'\\g<1>{correct_profile}\\g<2>',
            new_content,
        )

    if new_content != original:
        if not dry_run:
            bak = si.with_suffix('.md.bak')
            if not bak.exists():
                shutil.copy2(si, bak)
            si.write_text(new_content, encoding="utf-8")
        changes.append("source-index.md: system/layout_profile corrected")
    return changes


def fix_topics_json(pkg_path: Path, system: str, subject: str, dry_run: bool) -> list[str]:
    """Fix contaminated topics.json root node."""
    tj = pkg_path / "topics.json"
    if not tj.exists():
        return ["SKIP: topics.json not found"]

    try:
        data = json.loads(tj.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ["SKIP: topics.json parse error"]

    changes = []
    correct_root = f"{system} {subject}"
    topics = data.get("topics", [])

    if topics:
        root = topics[0]
        old_name = root.get("topic_name", "")
        # Fix root node if it says "CAIE IGCSE ..."
        if any(wrong in old_name for wrong in WRONG_SYSTEMS):
            root["topic_name"] = correct_root
            changes.append(f"topics.json root: '{old_name}' -> '{correct_root}'")

    if changes and not dry_run:
        bak = tj.with_suffix('.json.bak')
        if not bak.exists():
            shutil.copy2(tj, bak)
        tj.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return changes


def fix_metadata_json(pkg_path: Path, system: str, dry_run: bool) -> list[str]:
    """Fix metadata.json source_layout_profile."""
    mj = pkg_path / "metadata.json"
    if not mj.exists():
        return ["SKIP: metadata.json not found"]

    try:
        data = json.loads(mj.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ["SKIP: metadata.json parse error"]

    changes = []
    correct_profile = get_correct_profile(system)
    if not correct_profile:
        return [f"SKIP: no profile mapping for system='{system}'"]

    sp_list = data.get("source_provenance", [])
    for i, sp in enumerate(sp_list):
        old_profile = sp.get("source_layout_profile", "")
        if old_profile == "caie_igcse_syllabus" and correct_profile != "caie_igcse_syllabus":
            sp["source_layout_profile"] = correct_profile
            changes.append(f"metadata.json source_provenance[{i}].source_layout_profile: "
                          f"'{old_profile}' -> '{correct_profile}'")

    if changes and not dry_run:
        bak = mj.with_suffix('.json.bak')
        if not bak.exists():
            shutil.copy2(mj, bak)
        mj.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return changes


def remediate_package(pkg_path: Path, dry_run: bool) -> dict:
    """Remediate a single package. Returns a report dict."""
    mj = pkg_path / "metadata.json"
    if not mj.exists():
        return {"status": "skip", "reason": "no metadata.json"}

    try:
        meta = json.loads(mj.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"status": "skip", "reason": "metadata.json parse error"}

    system = meta.get("system", "")
    subject = meta.get("subject", "")
    board = meta.get("board_or_owner", "")
    level = meta.get("level", "")
    assessment_code = meta.get("assessment_code", "")

    # Skip actual IGCSE packages (no contamination)
    if is_igcse_package(system):
        sp = meta.get("source_provenance", [{}])[0]
        profile = sp.get("source_layout_profile", "")
        if profile == "caie_igcse_syllabus":
            return {"status": "ok", "reason": "IGCSE package, profile correct"}
        # IGCSE but wrong profile — still needs profile fix
        changes = fix_metadata_json(pkg_path, system, dry_run)
        return {"status": "partial", "system": system, "changes": changes}

    # Check if contamination exists
    current_profile = meta.get("source_provenance", [{}])[0].get("source_layout_profile", "")
    correct_profile = get_correct_profile(system)

    if not correct_profile:
        return {"status": "skip", "reason": f"no profile mapping for system='{system}'"}

    all_changes = []

    # Fix SKILL.md
    all_changes.extend(fix_skill_md(pkg_path, system, subject, board, level, assessment_code, dry_run))

    # Fix source-index.md
    all_changes.extend(fix_source_index(pkg_path, system, subject, dry_run))

    # Fix topics.json root
    all_changes.extend(fix_topics_json(pkg_path, system, subject, dry_run))

    # Fix metadata.json layout profile
    all_changes.extend(fix_metadata_json(pkg_path, system, dry_run))

    if all_changes:
        return {
            "status": "fixed" if not dry_run else "would_fix",
            "system": system,
            "subject": subject,
            "correct_profile": correct_profile,
            "changes": all_changes,
        }
    else:
        return {"status": "ok", "reason": "no contamination detected"}


def main():
    parser = argparse.ArgumentParser(description="Remediate CAIE IGCSE template contamination")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be fixed without changing files")
    parser.add_argument("--pkg-dir", type=str, default=None,
                        help="Path to assessment-skills directory")
    args = parser.parse_args()

    if args.pkg_dir:
        pkg_dir = Path(args.pkg_dir)
    else:
        # Default: look for pilot-output/assessment-skills relative to this script
        script_dir = Path(__file__).resolve().parent
        pkg_dir = script_dir.parent / "pilot-output" / "assessment-skills"

    if not pkg_dir.exists():
        print(f"ERROR: package directory not found: {pkg_dir}", file=sys.stderr)
        sys.exit(1)

    mode = "DRY RUN" if args.dry_run else "LIVE"
    print(f"[remediate] mode={mode} pkg_dir={pkg_dir}")
    print(f"[remediate] timestamp={datetime.now().isoformat()}")
    print()

    report = {"mode": mode, "packages": {}}
    fixed_count = 0
    ok_count = 0
    skip_count = 0

    for pkg_path in sorted(pkg_dir.iterdir()):
        if not pkg_path.is_dir() or pkg_path.name.startswith('.'):
            continue
        if pkg_path.name.startswith('ap-'):
            continue  # Skip AP packages (different pipeline)

        result = remediate_package(pkg_path, args.dry_run)
        report["packages"][pkg_path.name] = result

        status = result["status"]
        if status in ("fixed", "would_fix"):
            fixed_count += 1
            print(f"  [{status.upper()}] {pkg_path.name}")
            for c in result.get("changes", []):
                print(f"    -> {c}")
        elif status == "ok":
            ok_count += 1
        else:
            skip_count += 1
            reason = result.get("reason", "")
            if reason and "no profile mapping" in reason:
                print(f"  [SKIP] {pkg_path.name}: {reason}")

    print()
    print(f"[remediate] summary: fixed={fixed_count} ok={ok_count} skip={skip_count}")

    # Write report
    report_path = pkg_dir.parent / "remediation-report.json"
    if not args.dry_run:
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[remediate] report written to {report_path}")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
