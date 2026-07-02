---
name: ap-environmental-science
description: AP Environmental Science course framework + exam structure (College Board CED).
---

# ap-environmental-science

## Overview

Assessment skill for the AP Environmental Science course and exam, based on
the College Board Course and Exam Description (CED).

- System: AP (College Board)
- Subject: Environmental Science
- Level: AP (high school / college intro)
- Assessment code: AP Environmental Science
- Source: AP Environmental Science Course and Exam Description
- Valid: 2025 → (ongoing)

## Course Units

  - Unit 1: The Living World: Ecosystems (6–8%)
  - Unit 2: The Living World: Biodiversity (6–8%)
  - Unit 3: Populations (10–15%)
  - Unit 4: Earth Systems and Resources (10–15%)
  - Unit 5: Land and Water Use (10–15%)
  - Unit 6: Energy Resources and Consumption (10–15%)
  - Unit 7: Atmospheric Pollution (7–10%)
  - Unit 8: Aquatic and Terrestrial Pollution (7–10%)
  - Unit 9: Global Change (15–20%)

## Supported use modes

- Classification / routing of content to AP Environmental Science units (default).
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

- `skill_id`: `ap-environmental-science`
- `topic_id`: the most specific unit id (e.g. `ap-environmental-science-unitNN`)
- `confidence`: 0.0–1.0
- `exam_scope`: `section_i` / `section_ii` / `multiple` / `n/a`
- `reason`: one sentence with page reference if possible
- If out of scope: `verdict: out_of_scope`, `action: extension|archive`, `reason`

## Low-confidence and edge cases

- Confidence below 0.75 triggers review.
- Items covering multiple units: report primary + secondary.
