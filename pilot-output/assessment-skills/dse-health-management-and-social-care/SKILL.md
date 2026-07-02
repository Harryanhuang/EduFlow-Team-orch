---
name: dse-health-management-and-social-care
description: Scope and assessment model for Cambridge IGCSE Health Management and Social Care (DSE Health Management and Social Care).
---

# dse-health-management-and-social-care

## Overview

Assessment skill for the Cambridge IGCSE Health Management and Social Care syllabus.
Use this skill to classify, route, or scope health management and social care content
against the CAIE IGCSE syllabus.

- System: CAIE IGCSE
- Board/owner: HKEAA / Curriculum Development Council
- Subject: Health Management and Social Care
- Level: DSE Senior Secondary (S4-S6)
- Assessment code: DSE Health Management and Social Care
- Source: DSE Health Management and Social Care Syllabus
- Valid: 2024 → (ongoing)

## Supported use modes

- Classification / routing of health management and social care items to CAIE IGCSE topics (default).
- Scope checking and out-of-scope flagging.

`lesson_use.supported` is `false` in this version; teacher/student/parent-facing
modes are not enabled.

## Files to read

When this skill is invoked, read these structured files in order:

1. `metadata.json` — identity and source provenance.
2. `topics.json` — topic tree and classification hints (1 nodes).
3. `assessment.json` — papers, assessment objectives, question styles, constraints.
4. `examples.md` — golden classification examples.
5. `references/source-index.md` and `references/page-map.json` — source traceability.

## Classification rules

- Prefer the most specific topic node (subtopic over topic over root).
- Items purely about curriculum emphasis (e.g. scientific inquiry, STSE) without
  specific content should route to the most relevant content topic with emphasis
  noted as context.
- Mark out-of-scope items as `out_of_scope` and flag as `extension` if they
  belong to a related higher-level field, or `archive` if unrelated.

## Output format

Return a concise routing verdict:

- `skill_id`: `dse-health-management-and-social-care`
- `topic_id`: the most specific topic id (e.g. `dse-health-management-and-social-care-tNN`)
- `confidence`: 0.0–1.0
- `paper_scope`: `paper1` / `paper2` / `paper3` / `paper4` / `paper5` / `paper6` / `multiple`
- `tier`: `core` / `extended` / `na`
- `reason`: one sentence with page reference if possible
- If out of scope: `verdict: out_of_scope`, `action: extension|archive`, `reason`

## Low-confidence and edge cases

- Confidence below 0.75 triggers review.
- Cross-topic items: report a primary topic and secondary topic ids.
- Items spanning Core and Extended content should note both tiers.
