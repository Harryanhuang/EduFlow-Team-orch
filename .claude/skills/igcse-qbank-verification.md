---
name: igcse-qbank-verification
description: IGCSE three-layer QBank verification flow — scan qa/, qa-question-level/, items/ independently then cross-reference. Covers schema validation, legacy fragment detection, orphan quarantine, artifact consistency drift, and lifecycle state derivation. Use when verifying any IGCSE subject's QBank output.
metadata:
  type: workflow
  generated_by: worker_qbank
  date: 2026-06-24
---

# IGCSE QBank Three-Layer Verification

## Architecture

IGCSE QBank stores questions in up to 3 layers per topic:

```
igcse-{subject}-{code}/
├── qa/                    # human-authored questions (canonical)
│   └── N.M-*.md
├── qa-question-level/     # generated question-level files
│   └── N.M-*.md
├── items/                 # structured item files
│   └── N.M-items.md
└── qa-manifest.csv        # manifest listing expected files + counts
```

**Priority**: `qa/` (topic original) > `qa-question-level/` > `items/` (supplement).

## Verification Steps

### Step 1: Auto-Discovery

```python
import re
SUBJECT_RE = re.compile(r'^igcse-[a-z]+(?:-[a-z]+)*-\d{4}$')
# Scan content/ for matching directories
# Extract subject code (digits) and human-readable name
```

### Step 2: Per-Layer Parse

For each layer (qa/, qa-question-level/, items/), scan all `.md` files for Question entities.

**Parser must handle 4 QQL heading formats**:
- `### Question Q-x.y-zz`
- `# Question: Q-x.y-zz`
- `# Question: Question ...`
- `# QQL: Q-x.y-zz`

**Difficulty suffix** (Chemistry): some questions have ` (C)` or ` (S)` after difficulty — parser must handle `(?:\s+\([^)]+\))?`.

**Validate parser coverage** before running full verification: parse a sample file and confirm entity count matches manual count.

### Step 3: Schema Validation (per Question entity)

| Field | Required | Validation |
|-------|----------|------------|
| Difficulty | yes | Must be `Foundation`, `Standard`, or `Challenge` |
| Q-ID | yes | Format `^Q-[A-Z]?\d+(?:\.\d+)?-\d+$` |
| Question text | yes | Non-empty |
| Answer | yes | Non-empty |
| Explanation | no | Warning if missing |
| Tags | no | Warning if missing |

### Step 4: Legacy Fragment Detection

Flag files matching these patterns as legacy fragments:

| Pattern | Meaning |
|---------|---------|
| `-s2.md`, `-s3.md` | Supplement batches |
| `-round2-items.md` | Round 2 expansion |
| `-final-push-items.md` | Final push batch |
| `-round2/` directory | Round 2 directory |

Legacy fragments produce WARNING status. They block subject closeout until resolved (merge into canonical file or quarantine).

### Step 5: Artifact Consistency Drift

Compare counts across all layers:

```
qa_count  vs  qql_count  vs  items_count  vs  manifest_count
```

**Any mismatch is a BLOCKING failure.** Possible causes:
- Items were added to one layer but not others
- Manifest was not regenerated after expansion
- File was deleted without manifest update

**Fix**: regenerate manifest AFTER all expansion is complete, BEFORE review.

### Step 6: Orphan File Detection

For each Q-ID, check if it exists in multiple layers:
- **Shared Q-ID** (present in 2+ layers): normal
- **Orphan Q-ID** (unique to 1 layer): flagged as `recommendation: quarantine_review`, `auto_delete: false`

**Never auto-delete orphan files.** They may represent questions that were intentionally placed in a specific layer.

### Step 7: Duplicate Detection

See [[qbank-dedup-content-hash]] for the full dedup flow. Summary:
- Within-layer duplicate Q-ID: ERROR
- Cross-layer duplicate Q-ID: INFO (expected, dedup candidate)
- Must use SHA-256 content hash to distinguish true duplicates from ID collisions

### Step 8: Lifecycle State Derivation

Map verification results to machine-readable state:

| Condition | State | Next Action |
|-----------|-------|-------------|
| 0 questions, 0 scanned | `scan` | Run verification |
| FAIL or errors > 0 | `issue_fix` | Fix errors, re-verify |
| Warnings or manifest issues | `reverify` | Address warnings, re-verify |
| PASS, no issues | `ready_for_import` | Request user authorization |

### Step 9: Dedup/Import Gate

Import requires **two keys**:
1. `review_course_pass` = True (reviewer approved)
2. `user_authorized` OR `manager_authorized` = True

Dry-run is always permitted but never counts as authorization.

## Manager Panel Summary

For dashboard consumption, aggregate across all subjects:

```
most_urgent_action = highest priority state across subjects
Priority: issue_fix (0) > scan (1) > reverify (2) > needs_review (3) > ready_for_import (5)
```

## Common Failure Patterns

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| Foundationoundation | Regex captured wrong text | Fix difficulty parser regex |
| items_count != qql_count | Expansion not propagated | Regenerate all layers |
| 39 "duplicates" that aren't | v1 Q-ID-only matching | Use SHA-256 content hash (see dedup skill) |
| Manifest stale after expansion | Generated before expansion | Regenerate manifest AFTER expansion |
| Legacy fragment blocks closeout | Old supplement files not merged | Merge into canonical or quarantine |
