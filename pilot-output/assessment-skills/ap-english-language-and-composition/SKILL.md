---
name: ap-english-language-and-composition
description: AP English Language and Composition course framework + exam structure (College Board CED).
---

# ap-english-language-and-composition

## Overview

Assessment skill for the AP English Language and Composition course and exam, based on
the College Board Course and Exam Description (CED).

- System: AP (College Board)
- Subject: English Language and Composition
- Level: AP (high school / college intro)
- Assessment code: AP English Language and Composition
- Source: AP English Language and Composition Course and Exam Description
- Valid: 2025 → (ongoing)

## Course Units

  - Unit 1: Unit 2           Unit 3    Unit 4   Unit 5   Unit 6   Unit 7   Unit 8   Unit 9 (weighting n/a)
  - Unit 7: Return to Table of Contents (weighting n/a)
  - Unit 9: Skills define what a student should learn, practice, and develop (weighting n/a)
  - Unit 2: UNIT OVERVIEW (weighting n/a)
  - Unit 3: UNIT OVERVIEW (weighting n/a)
  - Unit 4: UNIT OVERVIEW (weighting n/a)
  - Unit 5: UNIT OVERVIEW (weighting n/a)
  - Unit 6: UNIT OVERVIEW (weighting n/a)
  - Unit 8: UNIT OVERVIEW (weighting n/a)

## Supported use modes

- Classification / routing of content to AP English Language and Composition units (default).
- Scope checking and out-of-scope flagging.

`lesson_use.supported` is `false` in this version.

## Files to read

1. `metadata.json` — identity and source provenance.
2. `topics.json` — unit tree and classification hints (9 units).
3. `assessment.json` — exam structure (Section I MCQ + Section II FRQ).
4. `examples.md` — golden classification examples.
5. `references/source-index.md` and `references/page-map.json` — source traceability.

## Classification rules

- Prefer the most specific unit node (Unit N over root).
- Cross-unit items should report a primary unit and a secondary unit id.
- Items outside the AP framework should be marked `out_of_scope` and flagged as
  `extension` (if they belong to a related field) or `archive` (if unrelated).

## Output format

Return a concise routing verdict:

- `skill_id`: `ap-english-language-and-composition`
- `topic_id`: the most specific unit id (e.g. `ap-english-language-and-composition-unitNN`)
- `confidence`: 0.0–1.0
- `exam_scope`: `section_i` / `section_ii` / `multiple` / `n/a`
- `reason`: one sentence with page reference if possible
- If out of scope: `verdict: out_of_scope`, `action: extension|archive`, `reason`

## Low-confidence and edge cases

- Confidence below 0.75 triggers review.
- Items covering multiple units: report primary + secondary.
