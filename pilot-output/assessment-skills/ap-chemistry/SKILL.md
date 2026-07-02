---
name: ap-chemistry
description: AP Chemistry course framework + exam structure (College Board CED).
---

# ap-chemistry

## Overview

Assessment skill for the AP Chemistry course and exam, based on
the College Board Course and Exam Description (CED).

- System: AP (College Board)
- Subject: Chemistry
- Level: AP (high school / college intro)
- Assessment code: AP Chemistry
- Source: AP Chemistry Course and Exam Description
- Valid: 2025 → (ongoing)

## Course Units

  - Unit 1: Atomic Structure and Properties (7–9%)
  - Unit 2: Compound Structure and Properties (7–9%)
  - Unit 3: Properties of Substances and Mixtures (18–22%)
  - Unit 4: Chemical Reactions (7–9%)
  - Unit 5: Kinetics (7–9%)
  - Unit 6: Thermochemistry (7–9%)
  - Unit 7: Equilibrium (7–9%)
  - Unit 8: Acids and Bases (11–15%)
  - Unit 9: Thermodynamics and Electrochemistry (7–9%)

## Supported use modes

- Classification / routing of content to AP Chemistry units (default).
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

- `skill_id`: `ap-chemistry`
- `topic_id`: the most specific unit id (e.g. `ap-chemistry-unitNN`)
- `confidence`: 0.0–1.0
- `exam_scope`: `section_i` / `section_ii` / `multiple` / `n/a`
- `reason`: one sentence with page reference if possible
- If out of scope: `verdict: out_of_scope`, `action: extension|archive`, `reason`

## Low-confidence and edge cases

- Confidence below 0.75 triggers review.
- Items covering multiple units: report primary + secondary.
