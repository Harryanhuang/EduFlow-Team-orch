---
name: ap-european-history
description: AP European History course framework + exam structure (College Board CED).
---

# ap-european-history

## Overview

Assessment skill for the AP European History course and exam, based on
the College Board Course and Exam Description (CED).

- System: AP (College Board)
- Subject: European History
- Level: AP (high school / college intro)
- Assessment code: AP European History
- Source: AP European History Course and Exam Description
- Valid: 2025 → (ongoing)

## Course Units

  - Unit 1: Renaissance and Exploration (10–15%)
  - Unit 2: Age of Reformation (10–15%)
  - Unit 3: Absolutism and Constitutionalism (10–15%)
  - Unit 4: Scientific, Philosophical, and (10–15%)
  - Unit 5: Conflict, Crisis, and Reaction in the (10–15%)
  - Unit 6: Industrialization and Its Effects (10–15%)
  - Unit 9: Cold War and Contemporary Europe (10–15%)
  - Unit 7: Learning Objective A         KC-3.4 (weighting n/a)
  - Unit 8: Learning Objective A          KC-4.1 (weighting n/a)

## Supported use modes

- Classification / routing of content to AP European History units (default).
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

- `skill_id`: `ap-european-history`
- `topic_id`: the most specific unit id (e.g. `ap-european-history-unitNN`)
- `confidence`: 0.0–1.0
- `exam_scope`: `section_i` / `section_ii` / `multiple` / `n/a`
- `reason`: one sentence with page reference if possible
- If out of scope: `verdict: out_of_scope`, `action: extension|archive`, `reason`

## Low-confidence and edge cases

- Confidence below 0.75 triggers review.
- Items covering multiple units: report primary + secondary.
