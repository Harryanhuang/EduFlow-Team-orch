---
name: check-closeout
description: "Manager skill: run the pre-closeout gate checklist before announcing subject launch or batch closeout. Covers artifact consistency, review verdict authority, revision-first blockers, and worker context guards."
metadata:
  type: workflow
  generated_by: worker_builder
  date: 2026-06-24
---

# Pre-Closeout Gate Checklist

## When to Use

Before announcing `manager-closeout` or `batch-closeout` for any IGCSE subject. This is the mechanical checklist that prevents premature or invalid closeouts.

## Steps

### 1. Verify review verdict is authoritative

The latest `review_course` verdict must be:
- `verdict == "approved"` (PASS)
- `verdict_scope == "full_subject"` (for subject closeout)

Run:

```bash
eduflow task supervisor-check
```

Look for:
- `latest_authoritative_verdict` is PASS
- No `review_truth_conflict` finding (chat PASS contradicting structured FAIL)

### 2. Run artifact consistency verifier

```bash
eduflow task supervisor-check [--json]
```

`supervisor-check` runs the subject verifier internally; parse the output
for `subject_verifier` blocks. Each must return `status == "pass"`. Check:
- `qql_count == manifest_claimed_total`
- `items_count <= qql_count`
- No format errors
- Difficulty values are F/S/C only
- Manifest is not a substitute for empty content

(There is no standalone `task verify-subject` subcommand; verification is
embedded in `supervisor-check` and `manager-closeout`.)

### 3. Check revision-first blockers

```bash
eduflow task list
```

For each active task in the workflow, verify:
- `revision_priority` is empty (no open revision)
- No `stale_execution_context` finding is active
- Worker has not self-reported "已修好" without a fresh reviewer PASS

### 4. Check worker context guards

```bash
eduflow health
```

Block closeout if any worker shows:
- `context_exhausted`
- `ready_unproven`
- `CLI not ready`
- `inbox_recovery_needed`

### 5. Verify evidence packet

If a batch closeout, verify the evidence packet includes:
- `workflow_id`
- `task_id`
- `batch_range`
- `items_count`
- `qql_count`
- `manifest_evidence`

### 6. Check scope match

| Closeout Type | Required Verdict Scope |
|---------------|----------------------|
| `manager-closeout` (full subject) | `full_subject` |
| `batch-closeout` | `package` or `batch` |

A `qql_only` PASS does NOT authorize subject closeout.
An `items_only` PASS does NOT authorize subject closeout.

### 7. Announce closeout (only if all gates pass)

```bash
eduflow task manager-closeout <task-id> --actor manager
eduflow say manager "学科 <subject> 已正式 closeout：<verdict summary>" --to user
```

## Block Closeout If Any of These Hold

- worker_course tried to bypass review_course
- Manager directly produced or repaired content
- Manager treated Python/file verification as verdict instead of dispatching review_course
- PASS is summary-level while file-level evidence is required
- Minor repair has not returned to review
- Manager has unread high-priority quality instruction
- Artifact truth and status summary disagree
- Batch/package PASS pushed through `manager-closeout` instead of `batch-closeout`

## Related Skills

- `igcse-subject-dispatch` — how the workflow started
- `review-verdict` — what the review verdict looks like
