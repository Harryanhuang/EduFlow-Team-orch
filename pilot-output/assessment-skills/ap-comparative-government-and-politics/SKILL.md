---
name: ap-comparative-government-and-politics
description: AP Comparative Government and Politics course framework + exam structure (College Board CED).
---

# ap-comparative-government-and-politics

## Overview

Assessment skill for the AP Comparative Government and Politics course and exam, based on
the College Board Course and Exam Description (CED).

- System: AP (College Board)
- Subject: Comparative Government and Politics
- Level: AP (high school / college intro)
- Assessment code: AP Comparative Government and Politics
- Source: AP Comparative Government and Politics Course and Exam Description
- Valid: 2025 → (ongoing)

## Course Units

  - Unit 1: Political Systems, Regimes, and Governments (18–27%)
  - Unit 2: Political Institutions (22–33%)
  - Unit 3: Political Culture and Participation (11–18%)
  - Unit 4: Party and Electoral Systems and Citizen Organizations (13–18%)
  - Unit 5: Political and Economic Changes and Development (16–24%)

## Supported use modes

- Classification / routing of content to AP Comparative Government and Politics units (default).
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

- `skill_id`: `ap-comparative-government-and-politics`
- `topic_id`: the most specific unit id (e.g. `ap-comparative-government-and-politics-unitNN`)
- `confidence`: 0.0–1.0
- `exam_scope`: `section_i` / `section_ii` / `multiple` / `n/a`
- `reason`: one sentence with page reference if possible
- If out of scope: `verdict: out_of_scope`, `action: extension|archive`, `reason`

## Low-confidence and edge cases

- Confidence below 0.75 triggers review.
- Items covering multiple units: report primary + secondary.
