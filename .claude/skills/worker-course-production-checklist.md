---
name: worker-course-production-checklist
description: Per-item and per-batch quality gate for worker_course. Use after every production batch to verify correctness before submitting to review. Covers math re-derivation, Answer/Explanation consistency, MCQ NOT-question validation, difficulty distribution, and batch size limits.
metadata:
  type: workflow
  generated_by: Luke_recorder
  date: 2026-06-24
  source: ap-content-production-pitfalls + igcse-9subject-sprint-lessons + review_course rejection patterns
---

# Worker Course Production Checklist

## Why This Exists

Items that skip this checklist fail review_course at 2-5x the rate of
items that pass through it. Running this per batch saves a full review
cycle.

## Per-Item Checks (Every Item, Every Batch)

### 1. Math Re-Derivation (STEM subjects)

After writing each Answer field, **independently re-derive the answer**
without looking at what you wrote. If the two results disagree → flag
the item, don't ship it.

**Highest risk items**: limits, L'Hôpital, optimization (max/min),
integration, FRQ-style multi-step.

### 2. Answer / Explanation Consistency

The final numerical or symbolic answer in the `Answer:` field MUST
match the conclusion of the `Explanation:` field.

**Common failure mode**: Explanation is correct, but the Answer field
still has an old or wrong value from an earlier draft.

### 3. MCQ NOT-Question Validation

For "Which of the following is NOT X" style questions:
- Verify at least one option IS genuinely NOT X
- If all options ARE X → broken question (no valid answer)
- If all options are NOT X → broken question (multiple valid answers)

### 4. Difficulty Tag Accuracy

Each item's `Difficulty:` field must match its actual cognitive demand:

| Tag | Expected demand |
|-----|----------------|
| Foundation | Single-step recall or direct application |
| Standard | 2-3 step problem, standard technique |
| Challenge | Multi-step, novel context, or common trap |

## Per-Batch Checks (After Each Batch of ≤5 Topics)

### 5. Difficulty Distribution Count

Count actual F/S/C items per topic. Expected:

| Syllabus | F | S | C | Total per topic |
|----------|---|---|---|----------------|
| IGCSE | 4 | 8 | 6 | 18 |
| AP | 5 | 7 | 6 | 18 |

Tolerance: ±1 per category. Don't trust manifest claims — count actual
item difficulty tags in the files.

### 6. File Naming Convention

Verify all files follow the expected pattern:
- IGCSE items: `topic_{X}.md` in `items/`, `Q-{X}-{NN}.md` in `qa-question-level/`
- AP items: `U{x}.{y}.{z}-{F|S|C}.md`

### 7. Topic Outline Coverage

Cross-reference created items against `topic-outline.md`:
- Every subtopic listed in the outline has corresponding items
- No orphan items (items without a matching outline subtopic)

## Batch Size Rule

**Hard limit**: 5 topics per batch.

Rationale: context window overflow at >5 topics causes worker_course
crashes that lose in-context state (files survive, work state doesn't).

## Pre-Submit Gate

Before sending to review_course, ALL of the following must be true:

```
□ Math re-derived for every STEM item (no disagreements)
□ Answer == Explanation conclusion for every item
□ MCQ NOT-questions validated (at least one valid answer)
□ Difficulty distribution within ±1 tolerance per topic
□ Files named correctly per syllabus convention
□ Tone scan passed (see: tone-scan-pre-review)
□ Topic outline coverage ≥ 95%
```

If any check fails → fix first, then submit.

## Quality Metric

Items that complete this checklist pass review on first attempt ~90%
of the time. Items that skip it fail review ~40% of the time
(data from igcse-9subject-sprint and AP Calculus T-32).

## Related

- `{{name:tone-scan-pre-review}}` — tone scan step (run after this)
- `{{name:ap-content-production-pitfalls}}` — AP-specific failure examples
- `{{name:review-criteria}}` — what review_course checks
- `{{name:c-class-expansion-workflow}}` — batch production phases
