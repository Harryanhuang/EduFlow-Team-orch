---
name: ap-biology
description: AP Biology course framework + exam structure (College Board CED).
---

# ap-biology

## Overview

Assessment skill for the AP Biology course and exam, based on
the College Board Course and Exam Description (CED).

- System: AP (College Board)
- Subject: Biology
- Level: AP (high school / college intro)
- Assessment code: AP Biology
- Source: AP Biology Course and Exam Description
- Valid: 2025 → (ongoing)

## Course Units

  - Unit 1: Chemistry of Life (8–11%)
  - Unit 2: Cells (10–13%)
  - Unit 3: Cellular Energetics (12–16%)
  - Unit 4: Cell Communication and Cell Cycle (10–15%)
  - Unit 5: Heredity (8–11%)
  - Unit 6: Gene Expression and Regulation (12–16%)
  - Unit 7: Natural Selection (13–20%)
  - Unit 8: Ecology (10–15%)

## Supported use modes

- Classification / routing of content to AP Biology units (default).
- Scope checking and out-of-scope flagging.

`lesson_use.supported` is `false` in this version.

## Files to read

1. `metadata.json` — identity and source provenance.
2. `topics.json` — unit tree and classification hints (8 units).
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

- `skill_id`: `ap-biology`
- `topic_id`: the most specific unit id (e.g. `ap-biology-unitNN`)
- `confidence`: 0.0–1.0
- `exam_scope`: `section_i` / `section_ii` / `multiple` / `n/a`
- `reason`: one sentence with page reference if possible
- If out of scope: `verdict: out_of_scope`, `action: extension|archive`, `reason`

## Low-confidence and edge cases

- Confidence below 0.75 triggers review.
- Items covering multiple units: report primary + secondary.
