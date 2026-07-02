#!/usr/bin/env python3
"""review-syllabus-skill: per-package reviewer.

Usage:
  python3 review_one.py <pkg_path>
  python3 review_one.py <pkg_path> --json
  python3 review_one.py <pkg_path> --emit-verdict   # writes review-verdict.json next to package

Emits:
- human-readable findings (stdout)
- review-checklist.json (machine-readable)
- review-verdict.json (overall verdict; only with --emit-verdict)
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# ---------- helpers ----------

def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def load_json(path: Path):
    if not path.exists():
        return {"__missing__": True, "__path__": str(path)}
    try:
        return json.load(open(path))
    except json.JSONDecodeError as e:
        return {"__parse_error__": str(e), "__path__": str(path)}

def pdf_extract(pdf: Path) -> str:
    if not pdf.exists():
        return ""
    try:
        out = subprocess.run(
            ["pdftotext", "-layout", str(pdf), "-"],
            capture_output=True, text=True, timeout=60
        )
        return out.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""

# ---------- axis checks ----------

def axis1_source(meta: dict, pdf: Path, txt: str) -> list:
    findings = []
    sp = (meta.get("source_provenance") or [{}])[0]
    local = sp.get("local_archive_ref", "")
    doc_ver = sp.get("document_version", "")

    if local and not Path(local).exists():
        findings.append({
            "axis": "source",
            "severity": "P0",
            "issue": f"local_archive_ref does not exist on disk: {local}",
            "fix": f"Re-download or re-archive the PDF to: {local}"
        })
    elif not local:
        findings.append({
            "axis": "source",
            "severity": "P0",
            "issue": "source_provenance[0].local_archive_ref is empty",
            "fix": "Provide local archive path or official URL."
        })

    # version cross-check
    pdf_falls = re.findall(r"Fall\s+\d{4}", txt)
    pdf_falls = list(set(pdf_falls))[:3]
    if pdf_falls and doc_ver:
        if not any(f in doc_ver for f in pdf_falls):
            findings.append({
                "axis": "source",
                "severity": "P1",
                "issue": f"document_version '{doc_ver}' does not match any Fall YYYY in PDF ({pdf_falls})",
                "fix": f"Set document_version to '{('Effective ' + pdf_falls[0]) if 'Effective' not in pdf_falls[0] else pdf_falls[0]}'"
            })
    return findings

def axis2_topics(topics_doc: dict, txt: str) -> list:
    findings = []
    if topics_doc.get("__missing__"):
        return [{
            "axis": "topics",
            "severity": "P0",
            "issue": "topics.json file missing",
            "fix": "Create topics.json from PDF extraction."
        }]
    if "__parse_error__" in topics_doc:
        return [{
            "axis": "topics",
            "severity": "P0",
            "issue": f"topics.json parse error: {topics_doc['__parse_error__']}",
            "fix": "Fix JSON syntax in topics.json."
        }]
    topics = topics_doc.get("topics", [])
    ids = [t.get("topic_id") for t in topics]
    dups = [i for i in set(ids) if ids.count(i) > 1]
    for d in dups:
        findings.append({
            "axis": "topics",
            "severity": "P0",
            "issue": f"duplicate topic_id: {d}",
            "fix": f"Rename or merge duplicate {d}."
        })
    units = [t for t in topics if re.search(r"-unit\d{1,2}$", t.get("topic_id", ""))]
    # TOC artifact detection
    for u in units:
        name = u.get("topic_name", "")
        # Pattern: "Unit N: Unit 2 Unit 3 Unit 4..." (2+ adjacent Unit labels)
        if re.search(r"Unit\s+\d+(\s+Unit\s+\d+){2,}", name):
            findings.append({
                "axis": "topics",
                "severity": "P0",
                "issue": f"topic_name '{name[:60]}' contains TOC concatenation artifact",
                "fix": "Re-extract unit headers from PDF; do not include TOC lines."
            })
        if "Return to Table of Contents" in name or "Not Assessed on the AP Exam" in name:
            findings.append({
                "axis": "topics",
                "severity": "P0",
                "issue": f"topic_name '{name[:60]}' is a PDF layout artifact, not a unit title",
                "fix": "Filter TOC/auxiliary lines from unit extraction."
            })
    # Unit count vs PDF
    pdf_units = re.findall(r"^\s*Unit\s+(\d+):", txt, re.MULTILINE)
    pdf_unit_n = len(set(int(n) for n in pdf_units if 1 <= int(n) <= 25))
    if pdf_unit_n > 0 and pdf_unit_n != len(units):
        findings.append({
            "axis": "topics",
            "severity": "P1",
            "issue": f"unit count mismatch: PDF has {pdf_unit_n} units, skill has {len(units)}",
            "fix": "Re-extract topic tree from PDF Course-at-a-Glance."
        })
    # Padding check
    for u in units:
        name = u.get("topic_name", "")
        if "%" in name or "   " in name or name != normalize(name):
            findings.append({
                "axis": "topics",
                "severity": "P2",
                "issue": f"unit_name contains padding or weighting: '{name[:60]}...'",
                "fix": "Move weighting to scope field; strip padding spaces."
            })
            break
    return findings

def axis3_assessment(ass: dict, txt: str) -> list:
    findings = []
    if ass.get("__missing__"):
        return [{
            "axis": "assessment",
            "severity": "P0",
            "issue": "assessment.json file missing",
            "fix": "Create assessment.json with paper structure."
        }]
    if "__parse_error__" in ass:
        return [{
            "axis": "assessment",
            "severity": "P0",
            "issue": f"assessment.json parse error: {ass['__parse_error__']}",
            "fix": "Fix JSON syntax in assessment.json."
        }]
    txt_norm = re.sub(r"(\d+)\s+multiple-\s*\n?\s*choice\s+questions", r"\1 multiple-choice questions", txt)
    txt_norm = re.sub(r"(\d+)\s+free-\s*\n?\s*response\s+questions", r"\1 free-response questions", txt_norm)
    mcq_m = re.search(r"(\d+)\s*multiple-choice\s*questions", txt_norm)
    frq_m = re.search(r"(\d+)\s*free-response\s*questions", txt_norm)
    pt_present = bool(re.search(r"Create performance task", txt_norm, re.IGNORECASE))
    time_m = re.search(r"(\d+)[\s-]+hour", txt_norm)

    styles = [s.get("style_id") for s in ass.get("question_styles", [])]
    if pt_present and "performance_task" not in styles:
        findings.append({
            "axis": "assessment",
            "severity": "P0",
            "issue": "PDF describes Create performance task but assessment.json question_styles lacks 'performance_task'",
            "fix": "Add performance_task to question_styles + define performance_tasks[] block."
        })
    if mcq_m and not ass.get("mcq_count"):
        findings.append({
            "axis": "assessment",
            "severity": "P1",
            "issue": f"PDF has {mcq_m.group(1)} MCQ but assessment.json missing mcq_count",
            "fix": f"Add \"mcq_count\": {mcq_m.group(1)} to assessment.json"
        })
    if frq_m and not ass.get("frq_count"):
        findings.append({
            "axis": "assessment",
            "severity": "P1",
            "issue": f"PDF has {frq_m.group(1)} FRQ but assessment.json missing frq_count",
            "fix": f"Add \"frq_count\": {frq_m.group(1)} to assessment.json"
        })
    if time_m and not ass.get("duration_hours"):
        findings.append({
            "axis": "assessment",
            "severity": "P1",
            "issue": f"PDF states exam is {time_m.group(1)} hours but assessment.json missing duration_hours",
            "fix": f"Add \"duration_hours\": {time_m.group(1)} to assessment.json"
        })
    return findings

def axis4_lo(topics_doc: dict, txt: str) -> list:
    findings = []
    if topics_doc.get("__missing__") or "__parse_error__" in topics_doc:
        return []
    topics = topics_doc.get("topics", [])
    ek_count = 0
    for t in topics:
        if t.get("essential_knowledge"):
            ek_count += 1
    pdf_ek_mentions = len(re.findall(r"(learning objective|Essential Knowledge|EK [0-9]|LO [0-9])", txt, re.IGNORECASE))
    if pdf_ek_mentions > 50 and ek_count == 0:
        findings.append({
            "axis": "lo",
            "severity": "P1",
            "issue": f"PDF has {pdf_ek_mentions} LO/EK mentions but topics.json has no essential_knowledge arrays",
            "fix": "For each unit topic, populate essential_knowledge: [...] from PDF EK tables."
        })
    return findings

# ---------- main ----------

def review(pkg: Path) -> dict:
    meta = load_json(pkg / "metadata.json")
    topics = load_json(pkg / "topics.json")
    ass = load_json(pkg / "assessment.json")

    if "__parse_error__" in meta:
        return {
            "package": str(pkg),
            "verdict": "fail",
            "findings": [{
                "axis": "metadata",
                "severity": "P0",
                "issue": f"metadata.json parse error: {meta['__parse_error__']}",
                "fix": "Fix metadata.json JSON syntax."
            }],
            "axes": {"source":[], "topics":[], "assessment":[], "lo":[]},
        }

    sp = (meta.get("source_provenance") or [{}])[0]
    local_pdf = Path(sp.get("local_archive_ref", ""))
    txt = pdf_extract(local_pdf) if local_pdf.exists() else ""

    findings = []
    findings += axis1_source(meta, local_pdf, txt)
    findings += axis2_topics(topics, txt)
    findings += axis3_assessment(ass, txt)
    findings += axis4_lo(topics, txt)

    has_p0 = any(f["severity"] == "P0" for f in findings)
    has_p1 = any(f["severity"] == "P1" for f in findings)
    if has_p0 or has_p1:
        verdict = "fail"
    elif findings:
        verdict = "pass_with_risks"
    else:
        verdict = "pass"

    return {
        "package": str(pkg),
        "skill_id": meta.get("id"),
        "verdict": verdict,
        "findings": findings,
        "summary": {
            "P0": sum(1 for f in findings if f["severity"] == "P0"),
            "P1": sum(1 for f in findings if f["severity"] == "P1"),
            "P2": sum(1 for f in findings if f["severity"] == "P2"),
        }
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pkg_path")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--emit-verdict", action="store_true")
    args = ap.parse_args()
    pkg = Path(args.pkg_path)
    if not pkg.exists() or not pkg.is_dir():
        sys.exit(f"package not found: {pkg}")

    result = review(pkg)

    if args.emit_verdict:
        verdict_doc = {
            "schema_version": "1",
            "skill_id": result.get("skill_id"),
            "reviewer": "review-syllabus-skill",
            "reviewed_at": __import__("datetime").date.today().isoformat(),
            "verdict": result["verdict"],
            "findings": result["findings"],
            "summary": result["summary"],
        }
        (pkg / "review-verdict.json").write_text(json.dumps(verdict_doc, indent=2, ensure_ascii=False))
        (pkg / "review-checklist.json").write_text(json.dumps(result["findings"], indent=2, ensure_ascii=False))

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    print(f"[review-syllabus-skill] package={result['package']} skill_id={result.get('skill_id')}")
    print(f"[verdict] {result['verdict']}  P0={result['summary']['P0']}  P1={result['summary']['P1']}  P2={result['summary']['P2']}")
    for f in result["findings"]:
        print(f"  [{f['severity']}] {f['axis']}: {f['issue']}")
        print(f"      fix: {f['fix']}")

if __name__ == "__main__":
    main()