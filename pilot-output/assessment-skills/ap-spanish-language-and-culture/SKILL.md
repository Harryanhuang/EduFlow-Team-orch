---
name: ap-spanish-language-and-culture
description: AP Spanish Language and Culture course framework + exam structure (College Board CED).
---

# ap-spanish-language-and-culture

## Overview

Assessment skill for the AP Spanish Language and Culture course and exam, based on
the College Board Course and Exam Description (CED).

- System: AP (College Board)
- Subject: Spanish Language and Culture
- Level: AP (high school / college intro)
- Assessment code: AP Spanish Language and Culture
- Source: AP Spanish Language and Culture Course and Exam Description
- Valid: 2025 → (ongoing)

## Course Units

(units not auto-extracted; see topics.json for full list)

## Supported use modes

- Classification / routing of content to AP Spanish Language and Culture units (default).
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

- `skill_id`: `ap-spanish-language-and-culture`
- `topic_id`: the most specific unit id (e.g. `ap-spanish-language-and-culture-unitNN`)
- `confidence`: 0.0–1.0
- `exam_scope`: `section_i` / `section_ii` / `multiple` / `n/a`
- `reason`: one sentence with page reference if possible
- If out of scope: `verdict: out_of_scope`, `action: extension|archive`, `reason`

## Low-confidence and edge cases

- Confidence below 0.75 triggers review.
- Items covering multiple units: report primary + secondary.
