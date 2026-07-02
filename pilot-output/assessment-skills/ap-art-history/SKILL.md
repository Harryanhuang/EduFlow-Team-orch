---
name: ap-art-history
description: AP Art History course framework + exam structure (College Board CED).
---

# ap-art-history

## Overview

Assessment skill for the AP Art History course and exam, based on
the College Board Course and Exam Description (CED).

- System: AP (College Board)
- Subject: Art History
- Level: AP (high school / college intro)
- Assessment code: AP Art History
- Source: AP Art History Course and Exam Description
- Valid: 2025 → (ongoing)

## Course Units

  - Unit 1: Global Prehistory, 30,000–500 bce                                                     ~4% (weighting n/a)
  - Unit 2: Ancient Mediterranean, 3500 bce–300 ce                                               ~15% (weighting n/a)
  - Unit 3: Early Europe and Colonial Americas, 200–1750 ce                                      ~21% (weighting n/a)
  - Unit 4: Later Europe and Americas, 1750–1980 ce                                              ~21% (weighting n/a)
  - Unit 5: Indigenous Americas, 1000 bce–1980 ce                                                 ~6% (weighting n/a)
  - Unit 6: Africa, 1100–1980 ce                                                                  ~6% (weighting n/a)
  - Unit 7: West and Central Asia, 500 bce–1980 ce                                                ~4% (weighting n/a)
  - Unit 8: South, East, and Southeast Asia, 300 bce–1980 ce                                      ~8% (weighting n/a)
  - Unit 9: The Pacific, 700–1980 ce                                                              ~4% (weighting n/a)
  - Unit 10: Global Contemporary, 1980 ce to Present                                             ~11% (weighting n/a)

## Supported use modes

- Classification / routing of content to AP Art History units (default).
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

- `skill_id`: `ap-art-history`
- `topic_id`: the most specific unit id (e.g. `ap-art-history-unitNN`)
- `confidence`: 0.0–1.0
- `exam_scope`: `section_i` / `section_ii` / `multiple` / `n/a`
- `reason`: one sentence with page reference if possible
- If out of scope: `verdict: out_of_scope`, `action: extension|archive`, `reason`

## Low-confidence and edge cases

- Confidence below 0.75 triggers review.
- Items covering multiple units: report primary + secondary.
