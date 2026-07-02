---
name: ap-physics-2
description: AP Physics 2: Algebra-Based course framework + exam structure (College Board CED).
---

# ap-physics-2

## Overview

Assessment skill for the AP Physics 2: Algebra-Based course and exam, based on
the College Board Course and Exam Description (CED).

- System: AP (College Board)
- Subject: Physics 2: Algebra-Based
- Level: AP (high school / college intro)
- Assessment code: AP Physics 2: Algebra-Based
- Source: AP Physics 2: Algebra-Based Course and Exam Description
- Valid: 2025 → (ongoing)

## Course Units

  - Unit 9: Thermodynamics (15–18%)
  - Unit 10: Electric Force, Field, and Potential (15–18%)
  - Unit 11: Electric Circuits (15–18%)
  - Unit 12: Magnetism and Electromagnetism (12–15%)
  - Unit 13: Geometric Optics (12–15%)
  - Unit 14: Waves, Sound, and Physical Optics (12–15%)
  - Unit 15: Modern Physics (12–15%)

## Supported use modes

- Classification / routing of content to AP Physics 2: Algebra-Based units (default).
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

- `skill_id`: `ap-physics-2`
- `topic_id`: the most specific unit id (e.g. `ap-physics-2-unitNN`)
- `confidence`: 0.0–1.0
- `exam_scope`: `section_i` / `section_ii` / `multiple` / `n/a`
- `reason`: one sentence with page reference if possible
- If out of scope: `verdict: out_of_scope`, `action: extension|archive`, `reason`

## Low-confidence and edge cases

- Confidence below 0.75 triggers review.
- Items covering multiple units: report primary + secondary.
