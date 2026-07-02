#!/usr/bin/env python3
"""review_strict_v2.py — strict per-package reviewer (no reuse of prior verdict).

5 axes (boss-specified):
  A. PDF identity (P0): pkg name/metadata subject/code/system matches PDF cover
  B. topic/unit match (P0/P1): topics.json count/name/hierarchy from PDF subject content
  C. essential_knowledge truth (P0/P1): no empty/null/generic placeholders
  D. assessment.json match (P0/P1): paper/unit/duration/weighting/structure match PDF
  E. template contamination (P1/P2): AQA/Edexcel/DSE/CAIE A-Level wrongly modeled as CAIE IGCSE; SKILL.md/metadata/topics contradictions

Outputs JSON:
  {
    "package": "...",
    "skill_id": "...",
    "axes": {
      "A_pdf_identity": {"verdict": "pass|warn|fail", "notes": "..."},
      "B_topic_match": {"verdict": "pass|warn|fail", "notes": "...", "expected_units": N, "actual_units": N},
      "C_ek_truth": {"verdict": "pass|warn|fail", "notes": "...", "generic_ek_count": N, "real_ek_count": N},
      "D_assessment": {"verdict": "pass|warn|fail", "notes": "...", "pdf_mcq": N, "skill_mcq": N},
      "E_template_contamination": {"verdict": "pass|warn|fail", "notes": "..."}
    },
    "field_completeness": {"metadata": bool, "topics": bool, "assessment": bool, "skill_md": bool, "examples": bool},
    "content_accuracy": "pass|warn|fail",
    "deviations": [{"severity": "P0|P1|P2", "field": "...", "issue": "...", "fix": "..."}],
    "overall": "pass|warn|fail"
  }
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Generic phrases that look like placeholders, not real EK
GENERIC_EK_PATTERNS = [
    r"^Subject-wide overview",
    r"^Core content and concepts",
    r"^Foundational concepts",
    r"^General framework",
    r"^Introduction to .* concepts",
    r"^Overview of .*",
    r"^Key ideas in",
    r"^Basic .* concepts",
]
GENERIC_TOPIC_PATTERNS = [
    r"Why choose this",
    r"Syllabus overview",
    r"What else you need to know",
    r"Introduction to this syllabus",
    r"How to use this syllabus",
    r"At a glance",
]

CONTAMINATION_PATTERNS = {
    "edexcel": [r"\bIGCSE\b"],   # Edexcel packages shouldn't claim IGCSE
    "aqa": [r"\bIGCSE\b"],
    "dse": [r"\bIGCSE\b"],
    "alevel": [r"\bIGCSE\b"],
    "igcse": [r"\bA-Level only\b", r"\bA2 only\b"],
}

def normalize(s):
    return re.sub(r"\s+", " ", s).strip()

def load_json(path):
    if not path.exists():
        return None
    try:
        return json.load(open(path))
    except json.JSONDecodeError as e:
        return {"__parse_error__": str(e)}

def pdf_text(pdf: Path) -> str:
    if not pdf.exists():
        return ""
    try:
        out = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                             capture_output=True, text=True, timeout=60)
        return out.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""

def cover_subject(txt: str) -> str:
    """Extract subject from PDF cover (first 50 lines)."""
    head = "\n".join(txt.splitlines()[:50]).lower()
    # Heuristic subject keywords
    subjects = ["biology", "physics", "chemistry", "mathematics", "further mathematics",
                "economics", "business", "accounting", "computer science", "psychology",
                "geography", "history", "english", "literature", "french", "german",
                "spanish", "chinese", "japanese", "italian", "latin", "african american",
                "art history", "studio art", "drawing", "music theory", "calculus",
                "statistics", "precalculus", "cybersecurity", "seminar", "research",
                "environmental science", "human geography", "macroeconomics", "microeconomics",
                "comparative government", "us government", "us history", "world history",
                "european history", "philosophy", "law", "engineering"]
    found = []
    for s in subjects:
        if s in head:
            found.append(s)
    return ",".join(found[:3])

def axis_a_pdf_identity(meta, txt, pkg_name):
    notes = []
    verdict = "pass"
    if meta is None:
        return {"verdict": "fail", "notes": "metadata.json missing"}
    if "__parse_error__" in meta:
        return {"verdict": "fail", "notes": f"metadata.json parse error: {meta['__parse_error__']}"}
    sp = (meta.get("source_provenance") or [{}])[0]
    local = sp.get("local_archive_ref", "")
    if not local:
        notes.append("local_archive_ref empty")
        verdict = "fail"
    elif not Path(local).exists():
        notes.append(f"local_archive_ref missing on disk: {local}")
        verdict = "fail"
    pdf_subj = cover_subject(txt)
    meta_subj = (meta.get("subject") or "").lower()
    if pdf_subj and meta_subj:
        # Check at least one keyword overlap
        pdf_tokens = set(pdf_subj.split(","))
        meta_tokens = set(re.findall(r"[a-z]+", meta_subj))
        if not (pdf_tokens & meta_tokens):
            notes.append(f"PDF cover mentions '{pdf_subj}' but metadata.subject='{meta_subj}' — SOURCE PDF MIS-ATTRIBUTED")
            verdict = "fail"  # upgraded: this is a P0 source mis-attribution
    # Cross-check pkg_name with skill_id
    sid = meta.get("id", "")
    if pkg_name and sid and pkg_name != sid:
        notes.append(f"pkg_name={pkg_name} but metadata.id={sid}")
        verdict = "warn" if verdict == "pass" else verdict
    return {"verdict": verdict, "notes": "; ".join(notes) if notes else "ok"}

def axis_b_topic_match(topics, txt):
    if topics is None:
        return {"verdict": "fail", "notes": "topics.json missing"}
    if "__parse_error__" in topics:
        return {"verdict": "fail", "notes": f"topics.json parse error: {topics['__parse_error__']}"}
    items = topics.get("topics", [])
    unit_like = [t for t in items if re.search(r"unit|topic|section|strand|theme|chapter", t.get("topic_id","").lower() + t.get("topic_name","").lower())]
    notes = []
    # Filter out generic placeholder topic names
    generic_count = 0
    for t in items:
        name = t.get("topic_name","")
        for pat in GENERIC_TOPIC_PATTERNS:
            if re.search(pat, name, re.IGNORECASE):
                notes.append(f"generic placeholder topic: '{name[:60]}'")
                generic_count += 1
                break
    # Empty shell topics
    empty_shell = [t for t in items if re.fullmatch(r"Unit \d+\s*", t.get("topic_name",""))]
    if empty_shell:
        notes.append(f"{len(empty_shell)} empty-shell topics (e.g. 'Unit N' only)")
    # Extract unit count from PDF (best-effort)
    pdf_units = re.findall(r"^\s*(?:Unit|Topic|Section|Chapter|Theme|Strand)\s+(\d+)[.:]", txt, re.MULTILINE | re.IGNORECASE)
    pdf_unit_n = len(set(int(n) for n in pdf_units if 1 <= int(n) <= 50))
    actual_n = len(unit_like)
    if pdf_unit_n and abs(pdf_unit_n - actual_n) > max(2, pdf_unit_n * 0.2):
        notes.append(f"unit count mismatch: PDF has ~{pdf_unit_n}, skill has {actual_n}")
        verdict = "warn"
    else:
        verdict = "pass"
    if generic_count > 0 or empty_shell:
        verdict = "warn" if verdict == "pass" else verdict
    return {"verdict": verdict, "notes": "; ".join(notes) if notes else "ok",
            "expected_units": pdf_unit_n, "actual_units": actual_n,
            "generic_topic_count": generic_count, "empty_shell_count": len(empty_shell)}

def axis_c_ek_truth(topics, txt):
    if topics is None or "__parse_error__" in topics:
        return {"verdict": "fail", "notes": "topics.json unavailable"}
    items = topics.get("topics", [])
    notes = []
    generic_ek = 0
    real_ek = 0
    empty_ek = 0
    for t in items:
        ek = t.get("essential_knowledge", [])
        if not ek:
            empty_ek += 1
            continue
        if isinstance(ek, str):
            ek = [ek]
        for e in ek:
            if not isinstance(e, str) or not e.strip():
                empty_ek += 1
                continue
            is_generic = any(re.search(p, e, re.IGNORECASE) for p in GENERIC_EK_PATTERNS)
            if is_generic:
                generic_ek += 1
            else:
                real_ek += 1
    # PDF mention count for sanity
    pdf_ek_mentions = len(re.findall(r"(learning objective|Essential Knowledge|EK [0-9]|LO [0-9]|syllabus content|students should)", txt, re.IGNORECASE))
    notes.append(f"generic_ek={generic_ek} real_ek={real_ek} empty_ek={empty_ek} pdf_mentions={pdf_ek_mentions}")
    if pdf_ek_mentions > 50 and real_ek == 0:
        verdict = "fail"
        notes.append(f"PDF has {pdf_ek_mentions} LO/EK mentions but skill has 0 real EK")
    elif generic_ek > real_ek and generic_ek > 0:
        verdict = "warn"
    elif empty_ek > 0 and real_ek == 0:
        verdict = "warn"
    else:
        verdict = "pass"
    return {"verdict": verdict, "notes": "; ".join(notes),
            "generic_ek_count": generic_ek, "real_ek_count": real_ek, "empty_ek_count": empty_ek}

def axis_d_assessment(ass, txt, meta):
    if ass is None:
        return {"verdict": "fail", "notes": "assessment.json missing"}
    if "__parse_error__" in ass:
        return {"verdict": "fail", "notes": f"assessment.json parse error: {ass['__parse_error__']}"}
    notes = []
    verdict = "pass"
    txt_norm = re.sub(r"(\d+)\s+multiple-\s*\n?\s*choice\s+questions", r"\1 multiple-choice questions", txt)
    txt_norm = re.sub(r"(\d+)\s+free-\s*\n?\s*response\s+questions", r"\1 free-response questions", txt_norm)
    pdf_mcq = re.search(r"(\d+)\s*multiple-choice\s*questions", txt_norm)
    pdf_frq = re.search(r"(\d+)\s*free-response\s*questions", txt_norm)
    pdf_pt = bool(re.search(r"Create performance task|performance task.*?(\d+)\s*(?:written response|questions)", txt_norm, re.IGNORECASE))
    pdf_time = re.search(r"(\d+)\s*(?:hour|hr)", txt_norm)
    skill_mcq = ass.get("mcq_count")
    skill_frq = ass.get("frq_count")
    skill_time = ass.get("duration_hours")
    skill_styles = [s.get("style_id") for s in ass.get("question_styles", [])]
    if pdf_pt and "performance_task" not in skill_styles:
        notes.append(f"PDF has Create performance task but skill styles={skill_styles}")
        verdict = "fail"
    if pdf_mcq and not skill_mcq:
        notes.append(f"PDF MCQ={pdf_mcq.group(1)} missing in skill")
        verdict = "warn"
    if pdf_frq and not skill_frq:
        notes.append(f"PDF FRQ={pdf_frq.group(1)} missing in skill")
        verdict = "warn"
    if pdf_time and not skill_time:
        notes.append(f"PDF duration={pdf_time.group(1)}h missing in skill")
        verdict = "warn"
    # Generic 3-paper template detection
    papers = ass.get("papers", [])
    if len(papers) == 3 and all(p.get("paper_id","").startswith(("P","Paper")) for p in papers):
        notes.append("generic 3-paper template detected")
        verdict = "warn"
    return {"verdict": verdict, "notes": "; ".join(notes) if notes else "ok",
            "pdf_mcq": int(pdf_mcq.group(1)) if pdf_mcq else None,
            "skill_mcq": skill_mcq, "pdf_frq": int(pdf_frq.group(1)) if pdf_frq else None,
            "skill_frq": skill_frq, "pdf_has_pt": pdf_pt}

def axis_e_contamination(meta, topics, ass, pkg_name):
    notes = []
    verdict = "pass"
    if meta is None or "__parse_error__" in meta:
        return {"verdict": "warn", "notes": "metadata unavailable for cross-check"}
    pkg_lower = pkg_name.lower()
    # Determine intended family from pkg_name
    family = None
    for k in ["edexcel", "aqa", "dse", "caie-alevel", "caie-igcse", "ap-", "ib-"]:
        if k in pkg_lower:
            family = k.rstrip("-")
            break
    if not family:
        return {"verdict": "pass", "notes": "unknown family — skipped"}
    # Concatenate all text content
    blob = json.dumps(meta).lower()
    if topics:
        blob += " " + json.dumps(topics).lower()
    if ass:
        blob += " " + json.dumps(ass).lower()
    skill_md = Path(pkg_name) / "SKILL.md"
    if skill_md.exists():
        blob += " " + skill_md.read_text().lower()
    # Apply family rules
    expected_blockers = CONTAMINATION_PATTERNS.get(family, [])
    for pat in expected_blockers:
        m = re.search(pat, blob, re.IGNORECASE)
        if m:
            notes.append(f"family={family} but text mentions '{m.group(0)}'")
            verdict = "warn"
    # Internal contradictions: skill_md says different level than metadata
    if meta.get("level","") and skill_md.exists():
        sm = skill_md.read_text().lower()
        meta_level = meta["level"].lower()
        if meta_level not in sm:
            notes.append(f"metadata.level={meta['level']} but SKILL.md doesn't mention it")
            verdict = "warn"
    return {"verdict": verdict, "notes": "; ".join(notes) if notes else "ok"}

def review(pkg: Path) -> dict:
    pkg_name = pkg.name
    meta = load_json(pkg / "metadata.json")
    topics = load_json(pkg / "topics.json")
    ass = load_json(pkg / "assessment.json")

    sp = (meta.get("source_provenance") or [{}])[0] if isinstance(meta, dict) and "__parse_error__" not in (meta or {}) else {}
    local = Path(sp.get("local_archive_ref", "")) if sp else Path()
    txt = pdf_text(local) if local.exists() else ""

    a = axis_a_pdf_identity(meta, txt, pkg_name)
    b = axis_b_topic_match(topics, txt)
    c = axis_c_ek_truth(topics, txt)
    d = axis_d_assessment(ass, txt, meta)
    e = axis_e_contamination(meta, topics, ass, pkg_name)

    field_completeness = {
        "metadata": meta is not None and "__parse_error__" not in meta,
        "topics": topics is not None and "__parse_error__" not in topics,
        "assessment": ass is not None and "__parse_error__" not in ass,
        "skill_md": (pkg / "SKILL.md").exists(),
        "examples": (pkg / "examples.md").exists(),
    }

    deviations = []
    for ax_name, ax in [("A", a), ("B", b), ("C", c), ("D", d), ("E", e)]:
        sev = {"pass": None, "warn": "P1", "fail": "P0"}.get(ax["verdict"])
        if sev:
            deviations.append({"severity": sev, "field": ax_name, "issue": ax["notes"], "fix": "(see notes)"})

    fails = [d for d in deviations if d["severity"] == "P0"]
    warns = [d for d in deviations if d["severity"] == "P1"]
    if fails:
        overall = "fail"
    elif warns:
        overall = "warn"
    else:
        overall = "pass"

    return {
        "package": pkg_name,
        "skill_id": (meta or {}).get("id"),
        "axes": {"A_pdf_identity": a, "B_topic_match": b, "C_ek_truth": c, "D_assessment": d, "E_contamination": e},
        "field_completeness": field_completeness,
        "content_accuracy": "pass" if overall == "pass" else "fail" if overall == "fail" else "warn",
        "deviations": deviations,
        "overall": overall,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pkg")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    pkg = Path(args.pkg)
    if not pkg.exists() or not pkg.is_dir():
        sys.exit(f"package not found: {pkg}")
    result = review(pkg)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    print(f"[strict-review] pkg={result['package']} overall={result['overall']}")
    for k, v in result["axes"].items():
        print(f"  {k}: {v['verdict']} — {v['notes'][:200]}")
    print(f"  field_completeness: {result['field_completeness']}")

if __name__ == "__main__":
    main()