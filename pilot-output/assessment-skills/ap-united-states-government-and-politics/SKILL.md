---
name: ap-united-states-government-and-politics
description: AP United States Government and Politics course framework + exam structure (College Board CED).
---

# ap-united-states-government-and-politics

## Overview

Assessment skill for the AP United States Government and Politics course and exam, based on
the College Board Course and Exam Description (CED).

- System: AP (College Board)
- Subject: United States Government and Politics
- Level: AP (high school / college intro)
- Assessment code: AP United States Government and Politics
- Source: AP United States Government and Politics Course and Exam Description
- Valid: 2025 → (ongoing)

## Course Units

  - Unit 1: Foundations of American Democracy (15–22%)
  - Unit 2: Interactions Among Branches of Government (25–36%)
  - Unit 3: Civil Liberties and Civil Rights (13–18%)
  - Unit 4: American Political Ideologies and Beliefs (10–15%)
  - Unit 5: Political Participation (20–27%)

## Supported use modes

- Classification / routing of content to AP United States Government and Politics units (default).
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

- `skill_id`: `ap-united-states-government-and-politics`
- `topic_id`: the most specific unit id (e.g. `ap-united-states-government-and-politics-unitNN`)
- `confidence`: 0.0–1.0
- `exam_scope`: `section_i` / `section_ii` / `multiple` / `n/a`
- `reason`: one sentence with page reference if possible
- If out of scope: `verdict: out_of_scope`, `action: extension|archive`, `reason`

## Low-confidence and edge cases

- Confidence below 0.75 triggers review.
- Items covering multiple units: report primary + secondary.
