---
name: item-prototype-check
description: "review_course skill: run the item-level prototype review checklist when reviewing worker_qbank item artifacts. Covers solvability, answer correctness, explanation usefulness, topic mapping, and metadata validation."
metadata:
  type: workflow
  generated_by: worker_builder
  date: 2026-06-24
---

# Item-Level Prototype Review Checklist

## When to Use

When review_course receives item-level prototype artifacts from worker_qbank (workflow: `igcse-item-level-prototype`). This is the mechanical checklist that ensures consistent, bounded review of item prototypes.

## Review Dimensions

### 1. Solvability

For each item in the prototype:
- Is the question self-contained and unambiguous?
- Can a student answer it without external context not provided?
- Are all necessary values/units given?

### 2. Answer Correctness

- Is the answer factually correct?
- Does it match the question scope (Foundation/Standard/Challenge)?
- Are numerical answers within reasonable range?
- Are multiple-choice options plausible?

### 3. Explanation Usefulness

- Does the explanation clarify WHY the answer is correct?
- Is it at the right difficulty level for the target student?
- Does it reference relevant concepts or formulas?
- Is it concise enough to be useful (not a textbook excerpt)?

### 4. Topic Mapping

- Does the item's Q-ID map to the correct topic?
- Is the topic consistent with the item's content?
- Are prerequisite topics correctly identified?

### 5. Difficulty/Type Metadata

- Is difficulty set to `Foundation`, `Standard`, or `Challenge`?
- Is the item type correct (MCQ, structured, etc.)?
- Does the difficulty match the actual question complexity?

## Running the Check

```bash
# Read the item files
ls content/<subject>/items/
ls content/<subject>/qa-question-level/

# For each item file, check:
# 1. File exists in expected location
# 2. Q-ID format: Q-<topic>-<number>
# 3. Required fields present: difficulty, question, answer
# 4. Difficulty value is F/S/C
# 5. Topic mapping is consistent
```

## Issuing the Verdict

After completing the checklist, send verdict using the `review-verdict` skill template:

```
igcse-item-level-prototype verdict for <subject>:
Verdict: <pass / minor_required / reject>
Scope reviewed: <item files / topic ids>
Evidence: <solvability check, answer verification, explanation review>
Blocking issues: <none / list>
Reusable pattern: <what should become a template>
```

## Common Item-Level Issues

| Issue | Verdict Impact | Fix |
|-------|---------------|-----|
| Wrong answer | reject | Worker must correct |
| Missing explanation | minor_required | Worker must add |
| Difficulty mismatch | minor_required | Worker must adjust |
| Q-ID topic mismatch | minor_required | Worker must remap |
| Non-functional question | reject | Worker must rewrite |

## Bounded Scope

This review covers ONLY the 1-2 topics or files in scope. Do NOT:
- Expand review to other topics
- Issue a full-subject verdict
- Make recommendations about subject closeout

The `worker_builder` handles template extraction after your verdict.

## Related Skills

- `submit-to-review` — what worker_qbank sent you
- `review-verdict` — the general verdict protocol
- `check-closeout` — what manager runs after your verdict
