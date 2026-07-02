---
name: review-syllabus-skill
description: Review an assessment skill package (metadata.json / topics.json / assessment.json / SKILL.md / examples.md) against the official source PDF. Detect P0/P1/P2 deviations and emit auto-fix suggestions. Use after worker_syllabus produces a skill package, or for batch QA across all skills in pilot-output/assessment-skills/. Companion to T-86 / T-87 review findings.
---

# review-syllabus-skill

Validate one **assessment skill package** against its official source PDF and emit a structured deviation report.

Designed for the v1 syllabus skill pipeline (A-Level / IGCSE / AP / IB / DSE). Refers to the master standard at:

`Assessment Skill Registry与Builder执行标准.md` (Assessment Skill Factory)

and the empirical baseline from T-86 (100% deviation across 8 sampled AP skills) and T-87 (#1-7 of the remaining 30 AP loop).

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

1. `review-checklist.json` — machine-readable findings, one entry per dimension.
2. `review-verdict.json` — overall verdict (`pass` / `pass_with_risks` / `fail`) following the standard's reviewer rubric.

If invoked in batch mode over a directory of packages, an extra `review-batch-summary.json` is written.

## Review dimensions (5 axes)

| # | Axis | What it checks | Severity |
|---|------|----------------|----------|
| 1 | Source provenance | `metadata.json.source_provenance[0].local_archive_ref` exists on disk; `document_version` matches `Fall YYYY` text actually present in PDF | P0 if file missing; P1 if version mismatch |
| 2 | Topic tree integrity | `topics.json` JSON-valid; no duplicate `topic_id`; `unit_name` free of TOC artifacts, padding, weighting strings; unit count matches PDF `Unit N:` enumeration | P0 on duplicate ID or TOC artifact; P1 on count mismatch; P2 on padding |
| 3 | Assessment model | `assessment.json` includes numeric fields when PDF gives them: `mcq_count`, `frq_count`, `duration_hours`; `question_styles` includes `performance_task` when PDF mentions Create performance task (CSP-family) | P0 missing required style; P1 missing numbers |
| 4 | Learning objective granularity | `topics.json` records `essential_knowledge` array per topic (or top-level scope list) sourced from PDF EK/LO text | P1 |
| 5 | Version year accuracy | `metadata.json.document_version` reflects the **actual** `Fall YYYY` in the local PDF, not the latest 2025 stamp | P1 (P0 if also wrong system/version claim) |

## P0/P1/P2 classification rules (from Builder Standard §7)

- **P0** — block register / active. Findings: missing source file, duplicate topic_id, JSON parse error, TOC artifact in topic_name, missing required question_style, hardcoded platform dependency, registry/metadata mismatch.
- **P1** — block validated / reviewed. Findings: missing scope, missing mcq/frq numbers, missing essential_knowledge, examples insufficient, version year mismatch.
- **P2** — suggestion only. Findings: unit_name padding, classification hints too sparse, page-map under-detailed, naming ambiguity.

## Procedure

1. **Resolve paths.** Read `<pkg_path>/metadata.json`. Capture `source_provenance[0].local_archive_ref`.
2. **Extract PDF text.** Run `pdftotext -layout <local_archive_ref> <tmp.txt>`. Skip if file missing (→ P0).
3. **Load skill files.** Read `metadata.json`, `topics.json`, `assessment.json`. Catch `json.JSONDecodeError` (→ P0).
4. **Run axis 1 (source).** Verify the file exists at the recorded path. Cross-check `document_version` regex `Fall \d{4}` against text in the PDF. Mismatch → P1.
5. **Run axis 2 (topic tree).**
   - Parse `topics.json.topics`. Check `topic_id` uniqueness → P0 if duplicate.
   - For each unit-like topic (`*-unitNN`), check `topic_name` does not contain 2+ adjacent digits followed by space (TOC concatenation pattern), `Return to Table of Contents`, or `Not Assessed` markers → P0 if any.
   - Compare unit count against PDF `^\s*Unit\s+(\d+):` regex → P1 if mismatch > 0.
   - Compare `unit_name` against PDF unit list (substring 25 chars); flag mismatches → P1.
   - Check for trailing padding (`%` inside name, `   ` runs, trailing weighting like `10–12%`) → P2.
6. **Run axis 3 (assessment model).**
   - Scan PDF for `\d+\s*multiple-choice\s*questions` (handle split-line `40 multiple-\nchoice questions`).
   - Scan for `\d+\s*free-response\s*questions`.
   - Scan for `Create performance task` (CSP-family signal).
   - If PDF gives a number and skill lacks `mcq_count`/`frq_count`/`duration_hours` → P1.
   - If PDF has Create performance task and skill `question_styles` lacks `performance_task` → P0.
7. **Run axis 4 (LO granularity).** Check if any topic has `essential_knowledge` non-empty array; if all empty and PDF has LO/EK mentions (>50) → P1.
8. **Run axis 5 (version).** Combine with axis 1. If `document_version` does not match any `Fall \d{4}` in PDF → P1.
9. **Compute verdict.**
   - `pass` if zero findings.
   - `pass_with_risks` if only P2 findings.
   - `fail` if any P0 or P1 finding present.
10. **Emit auto-fix suggestions.** For each finding, write a concrete patch hint (e.g. "set `metadata.source_provenance[0].document_version` to `Effective Fall 2024`"). The reviewer can apply these to drive worker_syllabus retries.

## Reference scripts

The bundled `scripts/review_one.py` performs steps 1-9 deterministically and prints findings in the order they appear. Use it directly:

```bash
python3 .claude/skills/review-syllabus-skill/scripts/review_one.py pilot-output/assessment-skills/ap-biology
```

For batch sweeps across all skills:

```bash
python3 .claude/skills/review-syllabus-skill/scripts/review_batch.py pilot-output/assessment-skills/ > review-batch-summary.json
```

## Empirical baseline (calibration data)

From T-86 (8/8 subjects had ≥1 deviation):

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

From T-87 first 7 of the remaining 30:

| Subject | Verdict |
|---------|---------|
| AP Calculus AB | P1 |
| AP Physics 1 | P1 |
| AP Physics C: Mechanics | P1 |
| AP Physics C: E&M | P1 |
| AP Precalculus | P1 |
| AP African American Studies | P1 |
| AP Comparative Gov & Politics | P1 |

Common failure mode: `document_version` was stamped `Effective Fall 2025` across all 38 AP skills regardless of actual PDF source year.

## Out of scope

- Semantic judgement of LO content (e.g. is the explanation text accurate) — that's a manual reviewer call after this skill passes.
- Out-of-scope classification of cross-system contamination (A-Level topics leaking into AP).
- Page-map completeness review (deferred to source extractor).

## Sample invocation

```text
$ python3 scripts/review_one.py pilot-output/assessment-skills/ap-biology
[review-syllabus-skill] reading ap-biology/metadata.json ...
[review-syllabus-skill] pdftotext ... ok
[axis 1] source provenance ok (document_version=Eff/Fall 2025, pdf=Fall 2025 match)
[axis 2] topic tree: 9 topics, 8 units, no duplicates, no TOC artifact
[axis 3] assessment model: PDF has MCQ=60 FRQ=6, skill missing mcq_count/frq_count (P1)
[axis 4] LO granularity: no essential_knowledge found (P1)
[axis 5] version: match
verdict: fail (P1×2)
suggested fixes:
  - P1: add assessment.json fields mcq_count=60, frq_count=6, duration_hours=3
  - P1: for each unit topic, populate essential_knowledge from PDF pp.20-200
```