---
name: ap-world-history-modern
description: AP World History: Modern course framework + exam structure (College Board CED).
---

# ap-world-history-modern

## Overview

Assessment skill for the AP World History: Modern course and exam, based on
the College Board Course and Exam Description (CED).

- System: AP (College Board)
- Subject: World History: Modern
- Level: AP (high school / college intro)
- Assessment code: AP World History: Modern
- Source: AP World History: Modern Course and Exam Description
- Valid: 2025 → (ongoing)

## Course Units

  - Unit 1: The Global Tapestry (8–10%)
  - Unit 2: Networks of Exchange (8–10%)
  - Unit 3: Land-Based Empires (12–15%)
  - Unit 4: Transoceanic Interconnections (12–15%)
  - Unit 5: Revolutions (12–15%)
  - Unit 6: Consequences of Industrialization (12–15%)
  - Unit 7: Global Conflict (8–10%)
  - Unit 8: Cold War and Decolonization (weighting n/a)
  - Unit 9: Globalization (8–10%)

## Supported use modes

- Classification / routing of content to AP World History: Modern units (default).
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

- `skill_id`: `ap-world-history-modern`
- `topic_id`: the most specific unit id (e.g. `ap-world-history-modern-unitNN`)
- `confidence`: 0.0–1.0
- `exam_scope`: `section_i` / `section_ii` / `multiple` / `n/a`
- `reason`: one sentence with page reference if possible
- If out of scope: `verdict: out_of_scope`, `action: extension|archive`, `reason`

## Low-confidence and edge cases

- Confidence below 0.75 triggers review.
- Items covering multiple units: report primary + secondary.
