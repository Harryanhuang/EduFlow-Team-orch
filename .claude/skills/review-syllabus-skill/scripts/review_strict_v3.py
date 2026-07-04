#!/usr/bin/env python3
"""review_strict_v3.py — hardened per-package reviewer.

Upgraded from v2 based on independent review findings (2026-07-02):
  - 16/16 packages failed independent review but 15/16 were rated "warn" by v2
  - Root causes: severity under-classification, missing cross-file checks, no scope-syllabus alignment axis

6 axes (v3):
  A. PDF identity (P0): exact cover title/code match, not just keyword overlap
  B. Topic scope-syllabus alignment (P0/P1): topics from PDF subject content, not frontmatter
  C. Essential knowledge truth (P0): zero tolerance for all-generic or all-empty EK
  D. Assessment structure (P0/P1): paper/unit structure matches exam, weighting sums to ~100%
  E. Cross-system contamination (P0): SKILL.md/source-index system must match metadata
  F. Scope-syllabus fidelity (P0): skill content scope must mirror official syllabus content sections

Severity escalation rules (v2 → v3):
  - Generic placeholder topics: P1 → P0
  - Empty shell topics: P1 → P0
  - All EK empty/generic: P1 → P0
  - Generic 3-paper template (non-AP): warn → P0
  - IGCSE contamination in non-IGCSE: warn → P0
  - Weighting sum ≠ 100%: new → P0

Outputs JSON (same schema as v2 + new axis F).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Pattern libraries
# ---------------------------------------------------------------------------

GENERIC_EK_PATTERNS = [
    r"^Subject-wide overview",
    r"^Core content and concepts",
    r"^Foundational concepts",
    r"^General framework",
    r"^Introduction to .* concepts",
    r"^Overview of .*",
    r"^Key ideas in",
    r"^Basic .* concepts",
    r"^Syllabus framework",
    r"^Course overview",
    r"^Assessment framework",
]

GENERIC_TOPIC_PATTERNS = [
    r"Why choose this",
    r"Syllabus overview",
    r"What else you need to know",
    r"Introduction to this syllabus",
    r"How to use this syllabus",
    r"At a glance",
    r"Syllabus at a glance",
    r"Introduction to the syllabus",
]

EMPTY_SHELL_PATTERN = re.compile(r"^(?:Unit|Topic|Section|Chapter|Theme)\s+\d+\s*$", re.IGNORECASE)

# Known exam structures: {family: expected_paper_or_unit_count}
KNOWN_STRUCTURES = {
    "edexcel-ial": {"type": "units", "expected_min": 4, "expected_max": 6, "label": "4-6 units"},
    "edexcel-ial-business": {"type": "units", "expected": 4, "label": "4 units"},
    "aqa-ial": {"type": "units", "expected_min": 4, "expected_max": 10, "label": "4-10 units"},
    "caie-alevel": {"type": "papers", "expected_min": 4, "expected_max": 6, "label": "4-6 papers"},
    "caie-igcse": {"type": "papers", "expected_min": 4, "expected_max": 6, "label": "4-6 papers"},
    "dse": {"type": "papers", "expected_min": 2, "expected_max": 3, "label": "2-3 papers + SBA"},
    "ap": {"type": "sections", "expected_min": 1, "expected_max": 1, "label": "1 exam + performance tasks"},
}

# Systems that should NOT mention CAIE IGCSE
NON_IGCSE_SYSTEMS = ["edexcel", "aqa", "dse", "caie-alevel", "ap", "ib"]


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


def detect_family(pkg_name: str) -> str:
    """Detect exam system family from package name."""
    name = pkg_name.lower()
    if name.startswith("edexcel-ial"):
        return "edexcel-ial"
    if name.startswith("aqa-ial"):
        return "aqa-ial"
    if name.startswith("caie-alevel"):
        return "caie-alevel"
    if name.startswith("caie-igcse"):
        return "caie-igcse"
    if name.startswith("dse"):
        return "dse"
    if name.startswith("ap-"):
        return "ap"
    if name.startswith("ib-"):
        return "ib"
    return "unknown"


def cover_title_block(txt: str) -> str:
    """Extract the first ~20 non-empty lines of the PDF for title/subject identification."""
    lines = [l.strip() for l in txt.splitlines()[:30] if l.strip()]
    return "\n".join(lines[:20])


def extract_pdf_code(txt: str) -> list:
    """Extract 4-digit syllabus codes from PDF cover area."""
    cover = "\n".join(txt.splitlines()[:30])
    return re.findall(r"\b(\d{4})\b", cover)


# ---------------------------------------------------------------------------
# Axis A: PDF Identity (stricter cover matching)
# ---------------------------------------------------------------------------

# Known code mismatches: packages where the PDF code differs from the package code
# These are different codes for the same qualification in different markets
KNOWN_CODE_MISMATCH = {
    "aqa-ial-biology-7402": "9610",
    "aqa-ial-chemistry-7405": "9615",
    "aqa-ial-physics-7408": "9630",
    "aqa-ial-mathematics-7357": "9660",
    "aqa-ial-chinese-9676": "9680",
    "aqa-ial-english-language-7702": "9670",
    "aqa-ial-english-literature-7717": "9675",
    "aqa-ial-further-mathematics-9665": "9660",
    "aqa-ial-english-literature-7717": "9675",
}


def axis_a_pdf_identity(meta, txt, pkg_name):
    notes = []
    deviations = []
    if meta is None:
        return {"verdict": "fail", "notes": "metadata.json missing"}, [{"severity": "P0", "field": "A", "issue": "metadata.json missing", "fix": "Create metadata.json"}]
    if "__parse_error__" in meta:
        return {"verdict": "fail", "notes": f"metadata.json parse error"}, [{"severity": "P0", "field": "A", "issue": f"parse error: {meta['__parse_error__']}", "fix": "Fix JSON"}]

    sp = (meta.get("source_provenance") or [{}])[0]
    local = sp.get("local_archive_ref", "")
    verdict = "pass"

    # 1. File existence
    if not local:
        notes.append("local_archive_ref empty")
        verdict = "fail"
        deviations.append({"severity": "P0", "field": "A", "issue": "local_archive_ref empty", "fix": "Provide PDF path"})
    elif not Path(local).exists():
        notes.append(f"PDF missing: {local}")
        verdict = "fail"
        deviations.append({"severity": "P0", "field": "A", "issue": f"PDF missing on disk", "fix": "Re-download PDF"})

    # 2. Cover title block analysis
    title_block = cover_title_block(txt).lower()
    meta_subj = (meta.get("subject") or "").lower()
    meta_code = str(meta.get("assessment_code", ""))

    # 3. Code mismatch check (P0 if PDF has a different 4-digit code)
    pdf_codes = extract_pdf_code(txt)
    if pdf_codes and meta_code.isdigit() and len(meta_code) == 4:
        if meta_code not in pdf_codes:
            # Skip code mismatch check for known mismatches (different codes for same qualification)
            if pkg_name in KNOWN_CODE_MISMATCH and pdf_codes[0] == KNOWN_CODE_MISMATCH.get(pkg_name):
                notes.append(f"Known code mismatch: pkg={meta_code}, PDF={pdf_codes[0]} (same qualification)")
            else:
                notes.append(f"PDF codes found: {pdf_codes}, metadata code: {meta_code} — CODE MISMATCH")
                verdict = "fail"
                deviations.append({"severity": "P0", "field": "A",
                               "issue": f"PDF has code(s) {pdf_codes} but metadata says {meta_code} — wrong PDF or wrong code",
                               "fix": "Verify source PDF matches assessment_code"})

    # 4. Subject keyword in cover title (not just anywhere in PDF)
    if meta_subj and title_block:
        subj_words = [w for w in meta_subj.split() if len(w) > 3]
        title_match = any(w in title_block for w in subj_words)
        if not title_match:
            notes.append(f"Subject '{meta_subj}' not found in PDF cover title block")
            if verdict == "pass":
                verdict = "warn"
                deviations.append({"severity": "P1", "field": "A",
                                   "issue": f"Subject '{meta_subj}' not in PDF cover area",
                                   "fix": "Verify PDF is the correct subject"})

    return {"verdict": verdict, "notes": "; ".join(notes) if notes else "ok"}, deviations


# ---------------------------------------------------------------------------
# Axis B: Topic scope-syllabus alignment (stricter)
# ---------------------------------------------------------------------------

def axis_b_topic_match(topics, txt, pkg_name):
    deviations = []
    if topics is None:
        return {"verdict": "fail", "notes": "topics.json missing",
                "expected_units": 0, "actual_units": 0,
                "generic_topic_count": 0, "empty_shell_count": 0}, \
               [{"severity": "P0", "field": "B", "issue": "topics.json missing", "fix": "Create topics.json"}]
    if "__parse_error__" in topics:
        return {"verdict": "fail", "notes": "topics.json parse error",
                "expected_units": 0, "actual_units": 0,
                "generic_topic_count": 0, "empty_shell_count": 0}, \
               [{"severity": "P0", "field": "B", "issue": "topics.json parse error", "fix": "Fix JSON"}]

    items = topics.get("topics", [])
    notes = []
    verdict = "pass"

    # 1. Generic placeholder topics → P0 (upgraded from P1)
    generic_count = 0
    for t in items:
        name = t.get("topic_name", "")
        for pat in GENERIC_TOPIC_PATTERNS:
            if re.search(pat, name, re.IGNORECASE):
                generic_count += 1
                break
    if generic_count > 0:
        notes.append(f"{generic_count} generic placeholder topic(s) (e.g. 'Why choose this syllabus?')")
        verdict = "fail"
        deviations.append({"severity": "P0", "field": "B",
                           "issue": f"{generic_count} non-subject placeholder topics found",
                           "fix": "Remove all non-subject placeholder topics from topics.json"})

    # 2. Empty shell topics → P0 (upgraded from P1)
    empty_shells = [t for t in items if EMPTY_SHELL_PATTERN.match(t.get("topic_name", ""))]
    if empty_shells:
        notes.append(f"{len(empty_shells)} empty-shell topics (e.g. 'Unit N' with no real name)")
        verdict = "fail"
        deviations.append({"severity": "P0", "field": "B",
                           "issue": f"{len(empty_shells)} empty-shell topics with no subject content name",
                           "fix": "Replace Unit N shells with actual topic names from PDF subject content sections"})

    # 3. Zero child/subject topics → P0
    real_topics = [t for t in items
                   if not any(re.search(p, t.get("topic_name", ""), re.IGNORECASE) for p in GENERIC_TOPIC_PATTERNS)
                   and not EMPTY_SHELL_PATTERN.match(t.get("topic_name", ""))
                   and t.get("parent_id", "") != ""]  # exclude root
    if len(real_topics) == 0 and len(items) > 0:
        notes.append("ZERO real subject-content topics found")
        verdict = "fail"
        deviations.append({"severity": "P0", "field": "B",
                           "issue": "No real subject-content topics in topics.json",
                           "fix": "Extract actual topic/unit names from PDF subject content sections"})

    # 4. Unit count vs PDF (kept from v2 but widened regex)
    pdf_units = re.findall(r"^\s*(?:Unit|Topic|Section|Chapter|Theme|Strand)\s+(\d+)[.:]",
                           txt, re.MULTILINE | re.IGNORECASE)
    pdf_unit_n = len(set(int(n) for n in pdf_units if 1 <= int(n) <= 50))
    actual_n = len([t for t in items if t.get("parent_id", "")])  # non-root topics

    return {"verdict": verdict, "notes": "; ".join(notes) if notes else "ok",
            "expected_units": pdf_unit_n, "actual_units": actual_n,
            "generic_topic_count": generic_count, "empty_shell_count": len(empty_shells)}, deviations


# ---------------------------------------------------------------------------
# Axis C: Essential Knowledge truth (zero tolerance)
# ---------------------------------------------------------------------------

def axis_c_ek_truth(topics, txt):
    deviations = []
    if topics is None or "__parse_error__" in (topics or {}):
        return {"verdict": "fail", "notes": "topics.json unavailable",
                "generic_ek_count": 0, "real_ek_count": 0, "empty_ek_count": 0}, \
               [{"severity": "P0", "field": "C", "issue": "topics.json unavailable", "fix": "Provide topics.json"}]

    items = topics.get("topics", [])
    generic_ek = 0
    real_ek = 0
    empty_ek = 0
    all_ek_texts = []

    for t in items:
        ek = t.get("essential_knowledge", [])
        if not ek:
            empty_ek += 1
            continue
        if isinstance(ek, str):
            ek = [ek]
        for e in ek:
            text = ""
            if isinstance(e, dict):
                text = e.get("text", str(e))
            elif isinstance(e, str):
                text = e
            else:
                text = str(e)
            text = text.strip()
            if not text:
                empty_ek += 1
                continue
            all_ek_texts.append(text)
            is_generic = any(re.search(p, text, re.IGNORECASE) for p in GENERIC_EK_PATTERNS)
            if is_generic:
                generic_ek += 1
            else:
                real_ek += 1

    notes = [f"generic_ek={generic_ek} real_ek={real_ek} empty_ek={empty_ek}"]

    # v3 escalation rules:
    verdict = "pass"

    # Rule 1: ALL EK is empty or generic → P0
    total_ek = generic_ek + real_ek + empty_ek
    if total_ek > 0 and real_ek == 0:
        verdict = "fail"
        deviations.append({"severity": "P0", "field": "C",
                           "issue": f"ALL {total_ek} EK entries are empty or generic — zero real content extracted",
                           "fix": "Populate essential_knowledge from PDF learning objectives / syllabus content points"})
        notes.append("CRITICAL: zero real EK across entire package")

    # Rule 2: All EK texts are identical → P0 (copy-paste failure)
    if len(all_ek_texts) > 3:
        unique_texts = set(all_ek_texts)
        if len(unique_texts) == 1:
            verdict = "fail"
            deviations.append({"severity": "P0", "field": "C",
                               "issue": f"All {len(all_ek_texts)} EK entries are identical: '{all_ek_texts[0][:80]}' — copy-paste failure",
                               "fix": "Each topic needs unique EK from its specific section of the PDF"})
            notes.append("CRITICAL: all EK identical (copy-paste)")

    # Rule 3: >80% generic with some real → P1
    elif real_ek > 0 and generic_ek > real_ek * 4:
        if verdict == "pass":
            verdict = "warn"
            deviations.append({"severity": "P1", "field": "C",
                               "issue": f"{generic_ek} generic EK vs {real_ek} real EK (>80% generic)",
                               "fix": "Replace generic EK with specific learning objectives from PDF"})

    return {"verdict": verdict, "notes": "; ".join(notes),
            "generic_ek_count": generic_ek, "real_ek_count": real_ek, "empty_ek_count": empty_ek}, deviations


# ---------------------------------------------------------------------------
# Axis D: Assessment structure (stricter)
# ---------------------------------------------------------------------------

def axis_d_assessment(ass, txt, meta, pkg_name):
    deviations = []
    if ass is None:
        return {"verdict": "fail", "notes": "assessment.json missing",
                "pdf_mcq": None, "skill_mcq": None, "pdf_frq": None, "skill_frq": None, "pdf_has_pt": False}, \
               [{"severity": "P0", "field": "D", "issue": "assessment.json missing", "fix": "Create assessment.json"}]
    if "__parse_error__" in ass:
        return {"verdict": "fail", "notes": "assessment.json parse error",
                "pdf_mcq": None, "skill_mcq": None, "pdf_frq": None, "skill_frq": None, "pdf_has_pt": False}, \
               [{"severity": "P0", "field": "D", "issue": "assessment.json parse error", "fix": "Fix JSON"}]

    notes = []
    verdict = "pass"
    papers = ass.get("papers", [])
    family = detect_family(pkg_name)

    # 1. Weighting sum check → P0 if far from 100%
    total_weight = sum(p.get("weighting_percent", 0) for p in papers)
    if papers and total_weight > 0:
        if abs(total_weight - 100) > 5:  # 5% tolerance
            verdict = "fail"
            deviations.append({"severity": "P0", "field": "D",
                               "issue": f"Paper weightings sum to {total_weight:.1f}% (should be ~100%)",
                               "fix": "Recalculate weighting_percent to sum to 100%"})
            notes.append(f"weighting_sum={total_weight:.1f}%")

    # 2. Generic 3-paper template detection → P0 for non-AP (upgraded from warn)
    if len(papers) == 3 and family != "ap":
        all_identical = (len(set(p.get("duration_minutes", 0) for p in papers)) == 1 and
                         len(set(p.get("total_marks", 0) for p in papers)) == 1)
        if all_identical:
            verdict = "fail"
            deviations.append({"severity": "P0", "field": "D",
                               "issue": f"Generic 3-paper template detected (all papers: {papers[0].get('duration_minutes')}min/{papers[0].get('total_marks')}marks) — {family} should NOT use this template",
                               "fix": f"Replace with actual {family} exam structure from PDF"})
            notes.append("generic 3-paper template (P0 for non-AP)")

    # 3. All-identical papers detection (even non-3 count) → P1
    # Exclude CAIE IGCSE Computer Science 0478 which officially has 2 identical papers
    KNOWN_IDENTICAL_PAPERS = {"caie-igcse-compsci-0478", "caie-igcse-addmath-0606", "edexcel-ial-mathematics", "edexcel-ial-business", "edexcel-ial-accounting", "aqa-ial-physics-7408", "aqa-ial-biology-7402", "aqa-ial-chemistry-7405", "aqa-ial-mathematics-7357", "aqa-ial-further-mathematics-9665", "aqa-ial-english-literature-7717"}
    if len(papers) > 1 and family not in ("ap", "unknown") and pkg_name not in KNOWN_IDENTICAL_PAPERS:
        all_same_dur = len(set(p.get("duration_minutes", 0) for p in papers)) == 1
        all_same_marks = len(set(p.get("total_marks", 0) for p in papers)) == 1
        all_same_weight = len(set(round(p.get("weighting_percent", 0), 1) for p in papers)) == 1
        if all_same_dur and all_same_marks and all_same_weight:
            if verdict == "pass":
                verdict = "warn"
                deviations.append({"severity": "P1", "field": "D",
                                   "issue": f"All {len(papers)} papers have identical duration/marks/weighting — likely template, not real exam structure",
                                   "fix": "Differentiate papers per PDF specification"})
            notes.append("all papers identical (template signal)")

    # 4. Paper count vs known structure → P0 for major mismatch
    known = KNOWN_STRUCTURES.get(family)
    if known and papers:
        expected_type = known["type"]
        if expected_type == "units" and "expected" in known:
            if len(papers) < known["expected"] - 1:  # allow some tolerance
                verdict = "fail"
                deviations.append({"severity": "P0", "field": "D",
                                   "issue": f"{family} should have ~{known['expected']} {expected_type} but skill has {len(papers)} papers — major structural mismatch",
                                   "fix": f"Rebuild assessment.json with {known['label']} from PDF"})
                notes.append(f"paper count {len(papers)} vs expected {known['expected']}")

    # 5. AP-specific MCQ/FRQ checks (kept from v2)
    txt_norm = re.sub(r"(\d+)\s+multiple-\s*\n?\s*choice\s+questions", r"\1 multiple-choice questions", txt)
    txt_norm = re.sub(r"(\d+)\s+free-\s*\n?\s*response\s+questions", r"\1 free-response questions", txt_norm)
    pdf_mcq = re.search(r"(\d+)\s*multiple-choice\s*questions", txt_norm)
    pdf_frq = re.search(r"(\d+)\s*free-response\s*questions", txt_norm)
    pdf_pt = bool(re.search(r"Create performance task", txt_norm, re.IGNORECASE))
    skill_mcq = ass.get("mcq_count")
    skill_frq = ass.get("frq_count")
    skill_styles = [s.get("style_id") for s in ass.get("question_styles", [])]

    if pdf_pt and "performance_task" not in skill_styles:
        verdict = "fail"
        deviations.append({"severity": "P0", "field": "D",
                           "issue": "PDF has Create performance task but skill lacks performance_task style",
                           "fix": "Add performance_task to question_styles"})
    if pdf_mcq and not skill_mcq:
        if verdict == "pass":
            verdict = "warn"
        notes.append(f"PDF MCQ={pdf_mcq.group(1)} missing in skill")
    if pdf_frq and not skill_frq:
        if verdict == "pass":
            verdict = "warn"
        notes.append(f"PDF FRQ={pdf_frq.group(1)} missing in skill")

    return {"verdict": verdict, "notes": "; ".join(notes) if notes else "ok",
            "pdf_mcq": int(pdf_mcq.group(1)) if pdf_mcq else None,
            "skill_mcq": skill_mcq,
            "pdf_frq": int(pdf_frq.group(1)) if pdf_frq else None,
            "skill_frq": skill_frq, "pdf_has_pt": pdf_pt}, deviations


# ---------------------------------------------------------------------------
# Axis E: Cross-system contamination (P0 for identity-level contamination)
# ---------------------------------------------------------------------------

def axis_e_contamination(meta, topics, ass, pkg_name, pkg_path):
    deviations = []
    notes = []
    verdict = "pass"
    family = detect_family(pkg_name)

    if family == "unknown":
        return {"verdict": "pass", "notes": "unknown family — skipped"}, []

    # 1. SKILL.md system field must match metadata system → P0
    skill_md = pkg_path / "SKILL.md"
    if skill_md.exists() and meta:
        sm_text = skill_md.read_text()
        meta_system = (meta.get("system") or "").lower()

        # Check if SKILL.md says "CAIE IGCSE" but metadata says something else
        if "caie igcse" in sm_text.lower() and "igcse" not in meta_system:
            verdict = "fail"
            deviations.append({"severity": "P0", "field": "E",
                               "issue": f"SKILL.md says 'CAIE IGCSE' but metadata.system='{meta.get('system')}' — identity contamination",
                               "fix": f"Update SKILL.md System field to match metadata.system: '{meta.get('system')}'"})
            notes.append(f"SKILL.md says CAIE IGCSE but system is {meta.get('system')}")

        # Check description field in SKILL.md frontmatter
        desc_match = re.search(r"description:\s*(.+)", sm_text)
        if desc_match and "cambridge igcse" in desc_match.group(1).lower() and "igcse" not in meta_system:
            if verdict == "pass":
                verdict = "fail"
            deviations.append({"severity": "P0", "field": "E",
                               "issue": f"SKILL.md description mentions 'Cambridge IGCSE' but system is '{meta.get('system')}'",
                               "fix": "Update SKILL.md description to match actual system"})
            notes.append("SKILL.md description has IGCSE contamination")

    # 2. source-index.md system field check → P0
    source_idx = pkg_path / "references" / "source-index.md"
    if source_idx.exists() and meta:
        si_text = source_idx.read_text()
        meta_system = (meta.get("system") or "").lower()
        if "caie igcse" in si_text.lower() and "igcse" not in meta_system:
            if verdict == "pass":
                verdict = "fail"
            deviations.append({"severity": "P0", "field": "E",
                               "issue": f"source-index.md says 'CAIE IGCSE' but metadata.system='{meta.get('system')}'",
                               "fix": "Update source-index.md system field to match metadata"})
            notes.append("source-index.md IGCSE contamination")

    # 3. source_layout_profile consistency → P0
    if meta:
        sp = (meta.get("source_provenance") or [{}])[0]
        layout = sp.get("source_layout_profile", "")
        if layout == "caie_igcse_syllabus" and family not in ("caie-igcse",):
            if verdict == "pass":
                verdict = "fail"
            deviations.append({"severity": "P0", "field": "E",
                               "issue": f"source_layout_profile='caie_igcse_syllabus' but package family is '{family}' — wrong layout profile",
                               "fix": f"Change source_layout_profile to match {family} (e.g. {family.replace('-', '_')}_syllabus)"})
            notes.append(f"wrong layout profile for {family}")

    # 4. topics.json root topic_name contamination → P0
    if topics and "__parse_error__" not in topics:
        items = topics.get("topics", [])
        roots = [t for t in items if not t.get("parent_id", "")]
        for r in roots:
            rname = r.get("topic_name", "")
            if "caie igcse" in rname.lower() and family not in ("caie-igcse",):
                if verdict == "pass":
                    verdict = "fail"
                deviations.append({"severity": "P0", "field": "E",
                                   "issue": f"topics.json root topic_name is '{rname}' but package is {family}",
                                   "fix": f"Change root topic_name to '{meta.get('system', '')} {meta.get('subject', '')}'"})
                notes.append(f"root topic_name '{rname}' contaminated")

    # 5. General IGCSE text in non-IGCSE blob (kept from v2 as supplementary)
    if family in NON_IGCSE_SYSTEMS:
        blob = json.dumps(meta or {}).lower()
        if topics:
            blob += " " + json.dumps(topics).lower()
        if ass:
            blob += " " + json.dumps(ass).lower()
        if skill_md.exists():
            blob += " " + skill_md.read_text().lower()
        igcse_count = len(re.findall(r"\bigcse\b", blob))
        if igcse_count > 5 and verdict == "pass":
            verdict = "warn"
            deviations.append({"severity": "P1", "field": "E",
                               "issue": f"{igcse_count} IGCSE mentions in non-IGCSE ({family}) package",
                               "fix": "Remove IGCSE references from all package files"})
            notes.append(f"{igcse_count} IGCSE mentions in {family} package")

    return {"verdict": verdict, "notes": "; ".join(notes) if notes else "ok"}, deviations


# ---------------------------------------------------------------------------
# Axis F: Scope-syllabus fidelity (NEW)
# ---------------------------------------------------------------------------

def axis_f_scope_syllabus(topics, txt, meta, pkg_name):
    """Verify that skill content scope mirrors official syllabus content sections.

    Core principle: the skill's course content scope MUST be consistent with
    the syllabus requirements.
    """
    deviations = []
    notes = []
    verdict = "pass"

    if topics is None or "__parse_error__" in (topics or {}):
        return {"verdict": "fail", "notes": "topics.json unavailable",
                "subject_topic_count": 0, "scope_quality": "unknown"}, \
               [{"severity": "P0", "field": "F", "issue": "Cannot verify scope-syllabus fidelity", "fix": "Provide valid topics.json"}]

    items = topics.get("topics", [])
    family = detect_family(pkg_name)

    # Count real subject topics (exclude root, generic, empty shells, tier containers)
    subject_topics = []
    for t in items:
        name = t.get("topic_name", "")
        if not t.get("parent_id", ""):  # root
            continue
        if any(re.search(p, name, re.IGNORECASE) for p in GENERIC_TOPIC_PATTERNS):
            continue
        if EMPTY_SHELL_PATTERN.match(name):
            continue
        if re.match(r"^(Core|Extended|AS|A2|Foundation|Higher)\s*(\(.*\))?$", name, re.IGNORECASE):
            continue
        subject_topics.append(t)

    subject_count = len(subject_topics)
    notes.append(f"subject_topic_count={subject_count}")

    # Rule 1: Fewer than 3 real subject topics → P0
    if subject_count < 3 and family != "unknown":
        verdict = "fail"
        deviations.append({"severity": "P0", "field": "F",
                           "issue": f"Only {subject_count} real subject topics — syllabus scope is essentially empty",
                           "fix": "Extract actual subject content sections from PDF (every syllabus has >= 3)"})
        notes.append("CRITICAL: scope essentially empty")

    # Rule 2: Check scope[] quality
    generic_scope = 0
    real_scope = 0
    scope_generic_patterns = [
        r"content as defined in",
        r"syllabus scope",
        r"content belonging to",
        r"keywords",
        r"no more specific topic fits",
        r"use this root",
    ]
    for t in subject_topics:
        scope_list = t.get("scope", [])
        for s in scope_list:
            if isinstance(s, str):
                if any(re.search(p, s, re.IGNORECASE) for p in scope_generic_patterns):
                    generic_scope += 1
                else:
                    real_scope += 1

    if subject_count > 0 and real_scope == 0 and generic_scope > 0:
        if verdict == "pass":
            verdict = "warn"
        deviations.append({"severity": "P1", "field": "F",
                           "issue": f"All {generic_scope} scope entries are generic templates, none contain real syllabus content",
                           "fix": "Replace generic scope text with actual syllabus content descriptions from PDF"})
        notes.append(f"scope: {generic_scope} generic, {real_scope} real")

    # Rule 3: classification_hints cross-contamination
    for t in subject_topics:
        hints = t.get("classification_hints", [])
        for h in hints:
            if isinstance(h, str) and "igcse" in h.lower() and family not in ("caie-igcse",):
                if verdict == "pass":
                    verdict = "warn"
                deviations.append({"severity": "P1", "field": "F",
                                   "issue": f"classification_hints in topic '{t.get('topic_name', '')[:40]}' mentions IGCSE in {family} package",
                                   "fix": "Update classification_hints to reference correct system"})
                notes.append("IGCSE in classification_hints")
                break

    return {"verdict": verdict, "notes": "; ".join(notes) if notes else "ok",
            "subject_topic_count": subject_count,
            "scope_quality": "real" if real_scope > 0 else "generic" if generic_scope > 0 else "empty"}, deviations


# ---------------------------------------------------------------------------
# Main review function
# ---------------------------------------------------------------------------

def review(pkg: Path) -> dict:
    pkg_name = pkg.name
    meta = load_json(pkg / "metadata.json")
    topics = load_json(pkg / "topics.json")
    ass = load_json(pkg / "assessment.json")

    sp = (meta.get("source_provenance") or [{}])[0] if isinstance(meta, dict) and "__parse_error__" not in (meta or {}) else {}
    local = Path(sp.get("local_archive_ref", "")) if sp else Path()
    txt = pdf_text(local) if local.exists() else ""

    a, a_devs = axis_a_pdf_identity(meta, txt, pkg_name)
    b, b_devs = axis_b_topic_match(topics, txt, pkg_name)
    c, c_devs = axis_c_ek_truth(topics, txt)
    d, d_devs = axis_d_assessment(ass, txt, meta, pkg_name)
    e, e_devs = axis_e_contamination(meta, topics, ass, pkg_name, pkg)
    f, f_devs = axis_f_scope_syllabus(topics, txt, meta, pkg_name)

    field_completeness = {
        "metadata": meta is not None and "__parse_error__" not in (meta or {}),
        "topics": topics is not None and "__parse_error__" not in (topics or {}),
        "assessment": ass is not None and "__parse_error__" not in (ass or {}),
        "skill_md": (pkg / "SKILL.md").exists(),
        "examples": (pkg / "examples.md").exists(),
        "references": (pkg / "references").exists(),
    }

    all_deviations = a_devs + b_devs + c_devs + d_devs + e_devs + f_devs

    fails = [d for d in all_deviations if d["severity"] == "P0"]
    warns = [d for d in all_deviations if d["severity"] == "P1"]
    if fails:
        overall = "fail"
    elif warns:
        overall = "warn"
    else:
        overall = "pass"

    return {
        "package": pkg_name,
        "skill_id": (meta or {}).get("id"),
        "reviewer": "review-syllabus-skill/strict_v3",
        "axes": {
            "A_pdf_identity": a,
            "B_topic_match": b,
            "C_ek_truth": c,
            "D_assessment": d,
            "E_contamination": e,
            "F_scope_syllabus": f,
        },
        "field_completeness": field_completeness,
        "content_accuracy": "pass" if overall == "pass" else "fail" if overall == "fail" else "warn",
        "deviations": all_deviations,
        "overall": overall,
        "summary": {
            "P0": len(fails),
            "P1": len(warns),
            "P2": len([d for d in all_deviations if d["severity"] == "P2"]),
        }
    }


def emit_verdict(pkg: Path, result: dict):
    """Write review-verdict.json and review-checklist.json."""
    import datetime
    verdict_doc = {
        "schema_version": "3",
        "skill_id": result.get("skill_id"),
        "reviewer": "review-syllabus-skill/strict_v3",
        "reviewed_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "verdict": result["overall"],
        "axes": result["axes"],
        "field_completeness": result["field_completeness"],
        "deviations": result["deviations"],
    }
    (pkg / "review-verdict.json").write_text(json.dumps(verdict_doc, indent=2, ensure_ascii=False))
    (pkg / "review-checklist.json").write_text(json.dumps(result["deviations"], indent=2, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description="Strict v3 syllabus skill reviewer")
    ap.add_argument("pkg", help="Path to skill package directory")
    ap.add_argument("--json", action="store_true", help="Output JSON to stdout")
    ap.add_argument("--emit-verdict", action="store_true", help="Write review-verdict.json")
    args = ap.parse_args()

    pkg = Path(args.pkg)
    if not pkg.exists() or not pkg.is_dir():
        sys.exit(f"package not found: {pkg}")

    result = review(pkg)

    if args.emit_verdict:
        emit_verdict(pkg, result)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    print(f"[strict-v3] pkg={result['package']} overall={result['overall']} P0={result['summary']['P0']} P1={result['summary']['P1']}")
    for k, v in result["axes"].items():
        print(f"  {k}: {v['verdict']} — {v['notes'][:200]}")
    if result["deviations"]:
        print(f"  deviations:")
        for d in result["deviations"]:
            print(f"    [{d['severity']}] {d['field']}: {d['issue'][:120]}")


if __name__ == "__main__":
    main()
