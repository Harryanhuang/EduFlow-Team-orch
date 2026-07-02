---
name: ap-psychology
description: AP Psychology course framework + exam structure (College Board CED).
---

# ap-psychology

## Overview

Assessment skill for the AP Psychology course and exam, based on
the College Board Course and Exam Description (CED).

- System: AP (College Board)
- Subject: Psychology
- Level: AP (high school / college intro)
- Assessment code: AP Psychology
- Source: AP Psychology Course and Exam Description
- Valid: 2025 → (ongoing)

## Course Units

  - Unit 1: Biological Bases of Behavior (15–25%)
  - Unit 2: Cognition (15–25%)
  - Unit 3: Development and Learning (15–25%)
  - Unit 4: Social Psychology and Personality (15–25%)
  - Unit 5: Mental and Physical Health (15–25%)

## Supported use modes

- Classification / routing of content to AP Psychology units (default).
- Scope checking and out-of-scope flagging.

`lesson_use.supported` is `false` in this version.

## Files to read

1. `metadata.json` — identity and source provenance.
2. `topics.json` — unit tree and classification hints (5 units).
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

- `skill_id`: `ap-psychology`
- `topic_id`: the most specific unit id (e.g. `ap-psychology-unitNN`)
- `confidence`: 0.0–1.0
- `exam_scope`: `section_i` / `section_ii` / `multiple` / `n/a`
- `reason`: one sentence with page reference if possible
- If out of scope: `verdict: out_of_scope`, `action: extension|archive`, `reason`

## Low-confidence and edge cases

- Confidence below 0.75 triggers review.
- Items covering multiple units: report primary + secondary.
