---
name: ap-music-theory
description: AP Music Theory course framework + exam structure (College Board CED).
---

# ap-music-theory

## Overview

Assessment skill for the AP Music Theory course and exam, based on
the College Board Course and Exam Description (CED).

- System: AP (College Board)
- Subject: Music Theory
- Level: AP (high school / college intro)
- Assessment code: AP Music Theory
- Source: AP Music Theory Course and Exam Description
- Valid: 2025 → (ongoing)

## Course Units

  - Unit 1: Music Fundamentals I: Pitch, Major Scales and Key (weighting n/a)
  - Unit 2: Music Fundamentals II: Minor Scales and Key (weighting n/a)
  - Unit 3: Music Fundamentals III: Triads and Seventh Chords (weighting n/a)
  - Unit 4: Harmony and Voice Leading I: Chord Function, (weighting n/a)
  - Unit 5: Harmony and Voice Leading II: Chord Progressions and (weighting n/a)
  - Unit 6: Harmony and Voice Leading III: Embellishments, (weighting n/a)
  - Unit 7: Harmony and Voice Leading IV: Secondary Function (weighting n/a)
  - Unit 8: Modes and Form (weighting n/a)

## Supported use modes

- Classification / routing of content to AP Music Theory units (default).
- Scope checking and out-of-scope flagging.

`lesson_use.supported` is `false` in this version.

## Files to read

1. `metadata.json` — identity and source provenance.
2. `topics.json` — unit tree and classification hints (8 units).
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

- `skill_id`: `ap-music-theory`
- `topic_id`: the most specific unit id (e.g. `ap-music-theory-unitNN`)
- `confidence`: 0.0–1.0
- `exam_scope`: `section_i` / `section_ii` / `multiple` / `n/a`
- `reason`: one sentence with page reference if possible
- If out of scope: `verdict: out_of_scope`, `action: extension|archive`, `reason`

## Low-confidence and edge cases

- Confidence below 0.75 triggers review.
- Items covering multiple units: report primary + secondary.
