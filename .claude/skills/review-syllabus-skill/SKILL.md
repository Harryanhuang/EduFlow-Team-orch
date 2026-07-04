---
name: review-syllabus-skill
description: "Review an assessment skill package (metadata.json / topics.json / assessment.json / SKILL.md / examples.md) against the official source PDF with strict v3 rules. Detect P0/P1/P2 deviations including cross-system template contamination and scope-syllabus misalignment. Use after worker_syllabus produces a skill package, or for batch QA across all skills in pilot-output/assessment-skills/. Companion to T-86 / T-87 review findings."
---

# review-syllabus-skill (v3)

Validate one **assessment skill package** against its official source PDF and emit a structured deviation report with strict severity classification.

Designed for the v1 syllabus skill pipeline (A-Level / IGCSE / AP / IB / DSE). Refers to the master standard at:

`Assessment Skill Registry与Builder执行标准.md` (Assessment Skill Factory)

and the empirical baseline from T-86 (100% deviation across 8 sampled AP skills), T-87 (#1-7 of the remaining 30 AP loop), and the 2026-07-02 independent audit of 16 cross-system packages (CAIE A-Level, CAIE IGCSE, Edexcel IAL, AQA IAL, DSE) where 16/16 failed.

## When to use this skill

- After `worker_syllabus` finishes a skill package and before promoting to `validated`.
- During batch QA sweeps over `pilot-output/assessment-skills/*`.
- When a reviewer wants a deterministic baseline before adding semantic judgement.

Do **not** use this skill for:

- Generating a new skill (use `assessment-skill-builder`).
- Extracting PDF source bundles (use `assessment-source-pdf-extractor`).
- Items that are not syllabus / CED / spec / C&A Guide (e.g. SAT/ACT/MAT) — those are v2/v3 reserved.

## Inputs

The skill accepts one positional argument:

```text
<pkg_path>   path to a skill package folder, e.g. pilot-output/assessment-skills/ap-biology
```

The reviewer must ensure `pdftotext` (poppler) is installed. The skill itself reads JSON and the local CED PDF; it does not need network access.

## Outputs

Two artefacts are produced next to the package:

1. `review-checklist.json` — machine-readable findings, one entry per deviation.
2. `review-verdict.json` — overall verdict (`pass` / `warn` / `fail`) with per-axis breakdown.

If invoked in batch mode over a directory of packages, an extra `review-batch-summary.json` is written.

## Review dimensions (6 axes)

| # | Axis | What it checks | Severity |
|---|------|----------------|----------|
| A | PDF identity | `metadata.json.source_provenance[0].local_archive_ref` exists; PDF cover subject and code match metadata `subject` and `assessment_code`; no wrong-PDF substitution (e.g. Marine Science 9693 in a Biology 9700 package) | P0 if file missing, code mismatch, or wrong subject |
| B | Topic match | `topics.json` topics correspond to PDF subject content sections; no generic placeholder topics ("Why choose this syllabus?", "Syllabus overview"); no empty shell topics ("Unit N" with no name); topic count matches PDF structure | P0 for generic/shell topics or zero real topics; P1 for count mismatch |
| C | Essential knowledge truth | `essential_knowledge` arrays contain real learning objectives from PDF, not empty/null or generic placeholders like "Subject-wide overview and framework" | P0 if all EK empty/generic/identical; P1 if >80% generic |
| D | Assessment structure | `assessment.json` paper/unit count, duration, marks, weighting match PDF exam structure; weighting sums to ~100%; no generic 3-paper template for non-AP systems | P0 for generic template, weighting >105% or <95%, or major structural mismatch; P1 for minor missing numbers |
| E | Cross-system contamination | SKILL.md `system` field matches `metadata.json.system`; `source-index.md` system matches; `source_layout_profile` is appropriate for exam system; root `topic_name` uses correct system name | P0 for any cross-system contamination (e.g. "CAIE IGCSE" in Edexcel/AQA/DSE/A-Level packages) |
| F | Scope-syllabus fidelity | Skill topic scope mirrors official syllabus content sections; at least 3 real subject topics; scope text contains actual syllabus content not generic template text; classification_hints reference correct system | P0 if <3 real subject topics; P1 for generic scope text or wrong-system hints |

## P0/P1/P2 classification rules (v3 — upgraded from v2)

- **P0** — block register / active. Findings: missing/wrong source PDF, PDF code mismatch, generic placeholder topics, empty-shell topics, zero real subject topics, all-generic/identical EK, generic assessment template, weighting sum ≠ 100%, cross-system contamination in SKILL.md/source-index/topics, wrong source_layout_profile.
- **P1** — block validated / reviewed. Findings: partial EK gaps (>80% generic), minor topic count mismatch, minor assessment field gaps, generic scope text, wrong-system hints in classification_hints.
- **P2** — suggestion only. Findings: unit_name padding, classification hints too sparse, page-map under-detailed, naming ambiguity.

## Procedure

1. **Resolve paths.** Read `<pkg_path>/metadata.json`. Capture `source_provenance[0].local_archive_ref`.
2. **Extract PDF text.** Run `pdftotext -layout <local_archive_ref> <tmp.txt>`. Skip if file missing (→ P0).
3. **Load skill files.** Read `metadata.json`, `topics.json`, `assessment.json`, `SKILL.md`, `references/source-index.md`. Catch `json.JSONDecodeError` (→ P0).
4. **Run axis A (PDF identity).** Verify file exists. Extract cover title block (first 20 lines). Cross-check assessment_code against 4-digit codes in PDF cover. Verify subject keyword appears in cover area. Code mismatch → P0.
5. **Run axis B (topic match).**
   - Parse `topics.json.topics`. Check `topic_id` uniqueness → P0 if duplicate.
   - Detect generic placeholder topics (Why choose, Syllabus overview, etc.) → P0.
   - Detect empty shell topics matching `Unit \d+` with no descriptive name → P0.
   - Count real subject-content topics; if zero → P0.
   - Compare unit count against PDF structure → P1 if mismatch.
6. **Run axis C (EK truth).**
   - Check each topic's `essential_knowledge` array.
   - Classify each EK entry as generic (matches placeholder patterns) or real.
   - ALL entries empty/generic → P0. All identical text → P0 (copy-paste failure).
   - >80% generic with some real → P1.
7. **Run axis D (assessment).**
   - Check weighting sum: if |sum - 100| > 5% → P0.
   - Detect generic 3-paper template (3 papers, identical duration/marks/weighting) for non-AP → P0.
   - Detect all-identical papers for any non-AP system → P1.
   - Compare paper count against known exam structure → P0 if major mismatch.
   - AP-specific: check MCQ/FRQ counts and performance_task style.
8. **Run axis E (contamination).**
   - Check SKILL.md text for "CAIE IGCSE" when system is non-IGCSE → P0.
   - Check source-index.md for same → P0.
   - Check source_layout_profile appropriateness → P0 if wrong.
   - Check topics.json root topic_name for wrong system name → P0.
9. **Run axis F (scope-syllabus fidelity).**
   - Count real subject topics (excluding root, generic, shell, tier containers).
   - If <3 real topics → P0.
   - Check scope[] text quality: generic template vs actual syllabus content.
   - Check classification_hints for cross-system references.
10. **Compute verdict.**
    - `pass` if zero findings.
    - `warn` if only P1/P2 findings.
    - `fail` if any P0 finding present.
11. **Emit auto-fix suggestions.** For each finding, write a concrete patch hint.

## Reference scripts

The bundled `scripts/review_strict_v3.py` performs the full v3 review:

```bash
python3 .claude/skills/review-syllabus-skill/scripts/review_strict_v3.py pilot-output/assessment-skills/caie-alevel-biology-9700
```

For batch sweeps (legacy v1 reviewer):

```bash
python3 .claude/skills/review-syllabus-skill/scripts/review_one.py pilot-output/assessment-skills/ap-biology
python3 .claude/skills/review-syllabus-skill/scripts/review_batch.py pilot-output/assessment-skills/ > review-batch-summary.json
```

## Empirical baseline (calibration data)

### AP skills (T-86, 8/8 subjects had ≥1 deviation):

| Subject | Verdict | Findings |
|---------|---------|----------|
| AP Biology | P1 | assessment.json missing numbers; LO granularity |
| AP Chemistry | P1 | assessment.json missing numbers |
| AP Statistics | P1 | version Fall 2020 vs 2025; missing numbers |
| AP US History | P1 | version Fall 2023 vs 2025; missing numbers |
| AP Art History | P1 | version Fall 2020 vs 2025; missing numbers |
| AP CSP | P0 | missing `performance_task` style; version Fall 2023 vs 2025 |
| AP Physics 2 | P0 | unit numbering 9-15 vs canonical 1-8; version Fall 2024 vs 2025 |
| AP English Lang | P0 | TOC artifact in unit_name; version Fall 2024 vs 2025 |

### Cross-system audit (2026-07-02, 16/16 packages failed):

| Package | v2 Verdict | v3 Verdict | Key Issues |
|---------|-----------|-----------|------------|
| caie-alevel-biology-9700 | fail | fail | P0: PDF is Marine Science 9693, not Biology 9700 |
| caie-alevel-physics-9702 | warn | fail | P0: IGCSE contamination, missing topics, EK empty |
| caie-alevel-mathematics-9709 | warn | fail | P0: 150% weighting, zero subject topics |
| caie-igcse-biology-0610 | warn | fail | P0: all EK generic placeholders |
| caie-igcse-physics-0625 | warn | fail | P0: 80% topics missing, EK all placeholders |
| edexcel-ial-biology | warn | fail | P0: IGCSE contamination, 3-paper template vs 6 units |
| edexcel-ial-physics | warn | fail | P0: IGCSE contamination, 3-paper template vs 6 units |
| edexcel-ial-mathematics | warn | fail | P0: IGCSE contamination, duplicate topics |
| aqa-ial-biology-7402 | warn | fail | P0: wrong code (7402 vs 9610), IGCSE contamination |
| aqa-ial-physics-7408 | warn | fail | P0: wrong code (7408 vs 9630), IGCSE contamination |
| dse-biology | warn | fail | P0: IGCSE contamination, empty shell topics |
| dse-physics | warn | fail | P0: IGCSE contamination, empty shell topics |
| dse-mathematics | warn | fail | P0: IGCSE contamination, zero child topics |
| dse-chemistry | warn | fail | P0: IGCSE contamination, empty shell topics |
| dse-biology-ca | warn | fail | P0: all EK generic placeholders |
| dse-physics-ca | warn | fail | P0: wrong hierarchy (elective under compulsory) |

**Root causes identified:**
1. All packages use `source_layout_profile: "caie_igcse_syllabus"` regardless of actual system
2. SKILL.md generator hardcodes "CAIE IGCSE" in system/description fields
3. EK extraction completely fails across all PDF types (zero real content extracted)
4. Non-CAIE assessment structures forced into generic 3-paper template

## Out of scope

- Semantic judgement of LO content accuracy — that's a manual reviewer call after this skill passes.
- Page-map completeness review (deferred to source extractor).

## Sample invocation

```text
$ python3 scripts/review_strict_v3.py pilot-output/assessment-skills/caie-alevel-physics-9702
[strict-v3] pkg=caie-alevel-physics-9702 overall=fail P0=7 P1=0
  A_pdf_identity: pass — ok
  B_topic_match: fail — 2 generic placeholder topics; 10 topics missing from PDF's 25 sections
  C_ek_truth: fail — ALL 13 EK entries are empty — zero real content extracted
  D_assessment: pass — ok
  E_contamination: fail — SKILL.md says 'CAIE IGCSE' but system is 'CAIE A-Level'
  F_scope_syllabus: fail — only 10 real subject topics vs 25 in PDF syllabus content
  deviations:
    [P0] B: 2 non-subject placeholder topics found
    [P0] C: ALL 13 EK entries are empty or generic
    [P0] E: SKILL.md says 'CAIE IGCSE' but metadata.system='CAIE A-Level'
    ...
```
