---
name: ap-statistics
description: AP Statistics course framework + exam structure (College Board CED).
---

# ap-statistics

## Overview

Assessment skill for the AP Statistics course and exam, based on
the College Board Course and Exam Description (CED).

- System: AP (College Board)
- Subject: Statistics
- Level: AP (high school / college intro)
- Assessment code: AP Statistics
- Source: AP Statistics Course and Exam Description
- Valid: 2025 → (ongoing)

## Course Units

  - Unit 1: Exploring One-Variable Data (15–23%)
  - Unit 2: Exploring Two-Variable Data (5–7%)
  - Unit 3: Collecting Data (12–15%)
  - Unit 4: Probability, Random Variables, and (10–20%)
  - Unit 5: Sampling Distributions (7–12%)
  - Unit 6: Inference for Categorical Data: Proportions (12–15%)
  - Unit 7: Inference for Quantitative Data: Means (10–18%)
  - Unit 8: Inference for Categorical Data: Chi-Square (2–5%)
  - Unit 9: Inference for Quantitative Data: Slopes (2–5%)

## Supported use modes

- Classification / routing of content to AP Statistics units (default).
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

- `skill_id`: `ap-statistics`
- `topic_id`: the most specific unit id (e.g. `ap-statistics-unitNN`)
- `confidence`: 0.0–1.0
- `exam_scope`: `section_i` / `section_ii` / `multiple` / `n/a`
- `reason`: one sentence with page reference if possible
- If out of scope: `verdict: out_of_scope`, `action: extension|archive`, `reason`

## Low-confidence and edge cases

- Confidence below 0.75 triggers review.
- Items covering multiple units: report primary + secondary.
