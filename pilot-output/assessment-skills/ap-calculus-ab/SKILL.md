---
name: ap-calculus-ab
description: AP Calculus AB course framework + exam structure (College Board CED).
---

# ap-calculus-ab

## Overview

Assessment skill for the AP Calculus AB course and exam, based on
the College Board Course and Exam Description (CED).

- System: AP (College Board)
- Subject: Calculus AB
- Level: AP (high school / college intro)
- Assessment code: AP Calculus AB
- Source: AP Calculus AB Course and Exam Description
- Valid: 2025 → (ongoing)

## Course Units

  - Unit 1: Limits and Continuity                       10–12% (4–7%)
  - Unit 2: Differentiation: Definition (weighting n/a)
  - Unit 3: Differentiation: Composite, (weighting n/a)
  - Unit 4: Contextual Applications of (weighting n/a)
  - Unit 5: Analytical Applications of (weighting n/a)
  - Unit 6: Integration and (weighting n/a)
  - Unit 7: Differential Equations                      6–12% (6–9%)
  - Unit 8: Applications of Integration                 10–15% (6–9%)
  - Unit 9: Parametric Equations, Polar (weighting n/a)
  - Unit 10: Infinite Sequences and (weighting n/a)

## Supported use modes

- Classification / routing of content to AP Calculus AB units (default).
- Scope checking and out-of-scope flagging.

`lesson_use.supported` is `false` in this version.

## Files to read

1. `metadata.json` — identity and source provenance.
2. `topics.json` — unit tree and classification hints (10 units).
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

- `skill_id`: `ap-calculus-ab`
- `topic_id`: the most specific unit id (e.g. `ap-calculus-ab-unitNN`)
- `confidence`: 0.0–1.0
- `exam_scope`: `section_i` / `section_ii` / `multiple` / `n/a`
- `reason`: one sentence with page reference if possible
- If out of scope: `verdict: out_of_scope`, `action: extension|archive`, `reason`

## Low-confidence and edge cases

- Confidence below 0.75 triggers review.
- Items covering multiple units: report primary + secondary.
