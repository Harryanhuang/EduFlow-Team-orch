---
name: review-course-file-evidence-playbook
description: Standardized file-level evidence protocol for review_course verdicts. Every PASS/conditional_pass MUST include sampled file evidence. Use when review_course issues any verdict to prevent summary-only rejections from manager.
metadata:
  type: workflow
  generated_by: Luke_recorder
  date: 2026-06-24
  source: manager-role-red-lines Violation 2 + igcse-9subject-sprint-lessons Pattern 5 + review_course workflow
---

# Review Course File-Evidence Playbook

## Why This Exists

A review verdict WITHOUT file-level evidence is not accepted by manager.
This happened on 2026-06-22: review_course gave a verdict without reading
actual files; manager had to re-trigger the review.

**Rule**: Every verdict must be backed by concrete file reads, not
summary restatements of what the worker claims.

## Evidence Packet (Required for Every Verdict)

```
## Evidence Packet

### Files Sampled
- [file path] — [what was checked]
- [file path] — [what was checked]
(minimum 5 files for PASS; 10+ for conditional_pass/reject)

### Spot-Check Results
- Topic 1.1 Item 3: [pass/fail + one-line reason]
- Topic 2.1 Item 1: [pass/fail + one-line reason]
(minimum 15 items checked: 5 topics × 3 items)

### Counts
- Topics in outline: N
- Items in items/ directory: N
- QQL files in qa-question-level/: N
- Manifest rows: N
- Items-Outline match: [yes/no, details]
- Items-QQL match: [yes/no, details]

### Tone Scan
- Files scanned: N
- Blocking tokens found: [list or "none"]
- Self-negation detected: [list or "none"]

### Difficulty Distribution
| Topic | F | S | C | Total | Within tolerance |
|-------|---|---|---|-------|-----------------|
| 1.1   | 4 | 8 | 6 | 18    | ✅              |
(minimum 5 topics shown)

### Path Convention Check
- All items follow correct naming: [yes/no]
- No orphan files: [yes/no]
- No legacy fragments: [yes/no]
```

## Spot-Check Sampling Strategy

### For IGCSE (multi-question files)
- Pick 5 topics (mix of early/late/middle)
- For each topic, read 3 items: 1 Foundation, 1 Standard, 1 Challenge
- Verify: Answer correctness (re-derive for STEM), Answer==Explanation, no tone tokens

### For AP (single-question files)
- Pick 5 subtopics across different units
- For each subtopic, read all 3 difficulty files (F/S/C)
- Verify: all 15 frontmatter keys present, answer correctness, no tone tokens

## Verdict Types

| Verdict | Evidence requirement | Next step |
|---------|---------------------|-----------|
| pass | Full evidence packet | Deliver to manager |
| conditional_pass | Full evidence packet + specific fix list | Worker fixes, re-submit |
| reject | Full evidence packet + blocking issues | Full rework |

## What is NOT Evidence

- "I checked the files and they look good" ← no file paths
- "worker_course said 18 items per topic" ← not file-level
- "manifest shows 3356 items" ← not file-level
- Counting without reading content ← not a spot-check

## Example: Good Evidence for PASS

```markdown
## Evidence Packet

### Files Sampled
- content/igcse-math-0606/items/topic_1.md — 18 items, F:4 S:8 C:6 ✅
- content/igcse-math-0606/items/topic_5.md — 18 items, F:3 S:9 C:6 (F-1, S+1 within tolerance)
- content/igcse-math-0606/items/topic_12.md — 18 items, F:4 S:8 C:6 ✅
- content/igcse-math-0606/items/topic_20.md — 18 items, F:4 S:7 C:7 (C+1 within tolerance)
- content/igcse-math-0606/items/topic_30.md — 18 items, F:5 S:7 C:6 (F+1 within tolerance)

### Spot-Check Results (15 items)
- Topic 1.1 Item 3 [F]: Answer correct, tone clean ✅
- Topic 1.1 Item 8 [S]: Answer correct, tone clean ✅
- Topic 1.1 Item 15 [C]: Answer correct, tone clean ✅
- Topic 5.1 Item 2 [F]: Answer correct, tone clean ✅
- Topic 5.1 Item 9 [S]: Answer re-derived — correct ✅
...
(all 15 listed)

### Counts
- Topics in outline: 34
- Items in items/: 612
- QQL files: 612
- Manifest rows: 34
- Items-Outline match: ✅
- Items-QQL match: ✅

### Tone Scan
- Files scanned: 34
- Blocking tokens found: none
- Self-negation detected: none

### Difficulty Distribution
| Topic | F | S | C | Total | Within tolerance |
|-------|---|---|---|-------|-----------------|
| 1.1   | 4 | 8 | 6 | 18    | ✅              |
| 5.1   | 3 | 9 | 6 | 18    | ✅ (F-1, S+1)  |
| 12.1  | 4 | 8 | 6 | 18    | ✅              |
| 20.1  | 4 | 7 | 7 | 18    | ✅ (C+1)        |
| 30.1  | 5 | 7 | 6 | 18    | ✅ (F+1)        |

### Path Convention Check
- All items follow `topic_{N}.md` pattern: ✅
- No orphan files: ✅
- No legacy fragments: ✅

## Verdict: pass
```

## Related

- `{{name:review-criteria}}` — what the checks evaluate
- `{{name:manager-role-red-lines}}` — why evidence is non-negotiable
- `{{name:ap-review-playbook}}` — AP-specific review path
- `{{name:worker-course-production-checklist}}` — what worker should have verified before submit
