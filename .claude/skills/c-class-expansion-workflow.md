---
name: c-class-expansion-workflow
description: Workflow for expanding C-class (Combined/Computer/AddMath) IGCSE subjects from 3-topic seed (27 items) to 300+ items with proper review gates. Use when boss demands "扩到300-400 items" or "单科完成制" for C-class subjects.
metadata:
  type: workflow
  generated_by: manager
  date: 2026-06-22
---

# C-class Subject Expansion Workflow

## Use When

- Boss demands扩量 to 300-400 items
- Subject has seed (3 topics × 9 items = 27)
- workflow_id: `igcse-9subject-sprint`
- Subject code pattern: `igcse-addmath-0606` / `igcse-combined-0653` / `igcse-computer-0478`

## Phases

### Phase 1: Gap Scan

1. worker_course reads `content/igcse-{code}/topic-outline.md`
2. Extract subtopics (e.g., 34 for 0653, 8 for 0478)
3. List completed vs pending
4. Report to manager with batch plan

### Phase 2: Batch Expansion (每 batch 3-5 topics)

For each topic:
- Create `items/topic_{X}.md` with 18 items (F:4|S:8|C:6)
- Create corresponding `qa-question-level/Q-{X}-{NN}.md` × 18 files
- Each item format: `**Item N [F/S/C]**` + `Question:` + `Answer:` + `Difficulty:` + `Topic:` + `Explanation:` + `Tags:`

After each batch:
- worker_course send manager: "Batch X 完工"
- manager: send review_course spot-check (1 random topic × 3 items)

### Phase 3: Final Review

When total items ≥300:
- Send review_course: workflow_id, task ID, gate
- review_course: 5×3 spot-check + tone scan
- If CONDITIONAL PASS: fix all flagged items, then ask for re-verdict

### Phase 4: Closeout

- T-XX verdict PASS
- remember manager task_completed with ref
- Say group: confirm milestone

## Critical Rules

- Tone tokens BLOCK review: Wait/Actually/Let me redo/Let me recalculate/Need to redo
- Quality > speed: boss rule
- Quality verification: NOT just numerical count, must verify Answer 数学正确性
- Batch ≤5 topics per worker_course cycle to avoid context overflow

## Red Flags

- worker_course context 100% → pause, send compression hint
- worker_course self-proclaimed "完成" without file evidence → verify with peek
- Review verdict skipping gate → enforce 5×3 spot-check
