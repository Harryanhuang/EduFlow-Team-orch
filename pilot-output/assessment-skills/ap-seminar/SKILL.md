---
name: ap-seminar
description: AP Seminar course framework + exam structure (College Board CED).
---

# ap-seminar

## Overview

Assessment skill for the AP Seminar course and exam, based on
the College Board Course and Exam Description (CED).

- System: AP (College Board)
- Subject: Seminar
- Level: AP (high school / college intro)
- Assessment code: AP Seminar
- Source: AP Seminar Course and Exam Description
- Valid: 2025 → (ongoing)

## Course Units

(units not auto-extracted; see topics.json for full list)

## Supported use modes

- Classification / routing of content to AP Seminar units (default).
- Scope checking and out-of-scope flagging.

`lesson_use.supported` is `false` in this version.

## Files to read

1. `metadata.json` — identity and source provenance.
2. `topics.json` — unit tree and classification hints (0 units).
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

- `skill_id`: `ap-seminar`
- `topic_id`: the most specific unit id (e.g. `ap-seminar-unitNN`)
- `confidence`: 0.0–1.0
- `exam_scope`: `section_i` / `section_ii` / `multiple` / `n/a`
- `reason`: one sentence with page reference if possible
- If out of scope: `verdict: out_of_scope`, `action: extension|archive`, `reason`

## Low-confidence and edge cases

- Confidence below 0.75 triggers review.
- Items covering multiple units: report primary + secondary.
