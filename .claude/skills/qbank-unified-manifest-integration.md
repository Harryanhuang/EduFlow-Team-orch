---
name: qbank-unified-manifest-integration
description: End-to-end QBank integration workflow for worker_qbank — from reading unified_manifest.csv through merge, dedup, verify, to handoff. Use when integrating a new subject's content into the unified question bank.
metadata:
  type: workflow
  generated_by: Luke_recorder
  date: 2026-06-24
  source: igcse-9subject-sprint-lessons Pattern 6 + qbank-validation-patterns + worker_qbank identity
---

# QBank Unified Manifest Integration

## When to Use

After review_course issues `pass` or `conditional_pass` (with fixes
complete), worker_qbank receives task to integrate the new subject's
content into the unified question bank.

## Pre-Integration Checklist

Before starting integration, verify:

```
□ review_course verdict: pass (or conditional_pass with all fixes done)
□ Subject manifest (qa-manifest.csv) regenerated from actual files
□ Item count matches manifest row count
□ No tone blocking tokens in content
```

If any check fails → report to manager, don't start integration.

## Integration Steps

### Step 1: Read Existing Unified Manifest

```python
import csv
with open('unified_manifest.csv') as f:
    existing = list(csv.DictReader(f))
print(f"Existing: {len(existing)} rows")
```

### Step 2: Parse New Subject Manifest

```python
with open('content/{subject}/qa-manifest.csv') as f:
    new_subject = list(csv.DictReader(f))
print(f"New subject: {len(new_subject)} rows")
```

### Step 3: Merge with Deduplication

```python
existing_ids = {row['id'] for row in existing}
new_rows = []
dupes = 0
for row in new_subject:
    if row['id'] in existing_ids:
        dupes += 1
    else:
        new_rows.append(row)
        existing_ids.add(row['id'])

merged = existing + new_rows
print(f"New added: {len(new_rows)}, Duplicates skipped: {dupes}")
```

### Step 4: Write Updated Unified Manifest

```python
if new_rows:
    fieldnames = list(existing[0].keys())
    with open('unified_manifest.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged)
    print(f"Updated: {len(merged)} rows")
```

### Step 5: Run Verification Script

```bash
# IGCSE subjects
python3 scripts/qbank_verify.py

# AP subjects
python3 scripts/ap_qbank_verify.py
```

Expected output:
- IGCSE: 0 errors after cleanup (367→56 is normal during cleanup; 0 = ready)
- AP: 0 missing frontmatter, 0 answer mismatches

### Step 6: Verify Row Count

```python
# Final sanity check
with open('unified_manifest.csv') as f:
    final = list(csv.DictReader(f))
print(f"Final unified_manifest: {len(final)} rows")

# Cross-check: subject items should all appear
subject_ids = {row['id'] for row in new_subject}
final_ids = {row['id'] for row in final}
missing = subject_ids - final_ids
if missing:
    print(f"ERROR: {len(missing)} items missing from unified manifest")
else:
    print("All subject items present in unified manifest ✅")
```

## Known Parser Bugs

### Biology "Foundationoundation" duplication

**Symptom**: difficulty field shows "Foundationoundation" instead of "Foundation"

**Fix**: regex in parser
```python
import re
def fix_difficulty(s):
    return re.sub(r'Foundationoundation', 'Foundation', s)
```

### Duplicate Q-ID across subjects

**Symptom**: same Q-ID appears in two different subject manifests

**Resolution**: Q-ID includes subject prefix; if collision occurs, verify
that the two entries are truly different questions. If same question,
keep the newer version.

## Handoff to review_course

After integration, if review_course verification is needed:

```
eduflow send review_course worker_qbank "QBank integration complete:
- unified_manifest: {N} rows (was {old_N})
- New subject items: {M} added
- Duplicates: {D} skipped
- Verification: PASS
Ready for final review."
```

Or directly to manager:

```
eduflow send manager worker_qbank "QBank integration for {subject} complete:
unified_manifest: {N} rows, errors=0. Ready for closeout."
```

## Related

- `{{name:qbank-lifecycle-gates}}` — state machine for qbank lifecycle
- `{{name:qbank-validation-patterns}}` — validation checks and error patterns
- `{{name:qbank-dedup-content-hash}}` — content-hash based deduplication
- `{{name:igcse-qbank-verification}}` — IGCSE-specific verification
- `{{name:ap-qbank-verification}}` — AP-specific verification
