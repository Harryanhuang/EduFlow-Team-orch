---
name: ap-united-states-history
description: AP United States History course framework + exam structure (College Board CED).
---

# ap-united-states-history

## Overview

Assessment skill for the AP United States History course and exam, based on
the College Board Course and Exam Description (CED).

- System: AP (College Board)
- Subject: United States History
- Level: AP (high school / college intro)
- Assessment code: AP United States History
- Source: AP United States History Course and Exam Description
- Valid: 2025 → (ongoing)

## Course Units

  - Unit 1: Period 1: 1491–1607 (4–6%)
  - Unit 2: Period 2: 1607–1754 (6–8%)
  - Unit 3: Period 3: 1754–1800 (10–17%)
  - Unit 4: Period 4: 1800–1848 (10–17%)
  - Unit 5: Period 5: 1844–1877 (10–17%)
  - Unit 6: Period 6: 1865–1898 (10–17%)
  - Unit 7: Period 7: 1890–1945 (10–17%)
  - Unit 8: Period 8: 1945–1980 (10–17%)
  - Unit 9: Period 9: 1980–Present (4–6%)

## Supported use modes

- Classification / routing of content to AP United States History units (default).
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

- `skill_id`: `ap-united-states-history`
- `topic_id`: the most specific unit id (e.g. `ap-united-states-history-unitNN`)
- `confidence`: 0.0–1.0
- `exam_scope`: `section_i` / `section_ii` / `multiple` / `n/a`
- `reason`: one sentence with page reference if possible
- If out of scope: `verdict: out_of_scope`, `action: extension|archive`, `reason`

## Low-confidence and edge cases

- Confidence below 0.75 triggers review.
- Items covering multiple units: report primary + secondary.
