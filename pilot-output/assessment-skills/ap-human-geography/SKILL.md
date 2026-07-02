---
name: ap-human-geography
description: AP Human Geography course framework + exam structure (College Board CED).
---

# ap-human-geography

## Overview

Assessment skill for the AP Human Geography course and exam, based on
the College Board Course and Exam Description (CED).

- System: AP (College Board)
- Subject: Human Geography
- Level: AP (high school / college intro)
- Assessment code: AP Human Geography
- Source: AP Human Geography Course and Exam Description
- Valid: 2025 → (ongoing)

## Course Units

  - Unit 1: Thinking Geographically (8–10%)
  - Unit 2: Population and Migration Patterns and Processes (12–17%)
  - Unit 3: Cultural Patterns and Processes (12–17%)
  - Unit 4: Political Patterns and Processes (12–17%)
  - Unit 5: Agriculture and Rural Land-Use Patterns and Processes (12–17%)
  - Unit 6: Cities and Urban Land-Use Patterns and Processes (12–17%)
  - Unit 7: Industrial and Economic Development Patterns and Processes (12–17%)

## Supported use modes

- Classification / routing of content to AP Human Geography units (default).
- Scope checking and out-of-scope flagging.

`lesson_use.supported` is `false` in this version.

## Files to read

1. `metadata.json` — identity and source provenance.
2. `topics.json` — unit tree and classification hints (7 units).
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

- `skill_id`: `ap-human-geography`
- `topic_id`: the most specific unit id (e.g. `ap-human-geography-unitNN`)
- `confidence`: 0.0–1.0
- `exam_scope`: `section_i` / `section_ii` / `multiple` / `n/a`
- `reason`: one sentence with page reference if possible
- If out of scope: `verdict: out_of_scope`, `action: extension|archive`, `reason`

## Low-confidence and edge cases

- Confidence below 0.75 triggers review.
- Items covering multiple units: report primary + secondary.
