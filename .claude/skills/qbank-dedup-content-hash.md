---
name: qbank-dedup-content-hash
description: QBank deduplication using SHA-256 normalized content hashing. Prevents false-positive deletion when same Q-ID contains different content (ID collision). Covers normalize → hash → classify → renumber flow. Use when deduplicating any QBank subject.
metadata:
  type: workflow
  generated_by: worker_qbank
  date: 2026-06-24
---

# QBank Dedup with Content Hashing

## Why Q-ID-Only Matching Fails

Initial approach (v1) matched duplicates by Q-ID alone. Result: flagged 39 "duplicates" across Physics/Chemistry/Biology/Accounting — but **review found 35 of those were ID collisions** (same Q-ID, different question content). Deleting them would have lost unique questions.

**Root cause**: different production batches independently assigned the same Q-ID to different questions.

## The Pattern: Normalize → Hash → Classify

### Step 1: Normalize Content

For each Question entity, extract the Q and A fields and normalize:

```python
import re, hashlib

def normalize(text: str) -> str:
    """Collapse whitespace, strip, lowercase for comparison."""
    return re.sub(r'\s+', ' ', text.strip().lower())

def content_hash(q_text: str, a_text: str) -> str:
    """SHA-256 of normalized Q+A."""
    normalized = f"Q:{normalize(q_text)}||A:{normalize(a_text)}"
    return hashlib.sha256(normalized.encode()).hexdigest()
```

**Critical**: use normalized Q+A fields, NOT raw body. Raw body length differences (e.g., 248 vs 253 chars) can mask identical normalized content.

### Step 2: Classify Each Duplicate Candidate

For each Q-ID appearing in 2+ layers:

| Condition | Classification | Action |
|-----------|---------------|--------|
| Same Q-ID + same hash | `true_duplicate` | Safe to delete one copy |
| Same Q-ID + different hash | `id_collision` | Must renumber, NOT delete |

### Step 3: Canonical File Priority (for true duplicates)

When deciding which copy to KEEP:

```
N.M-items.md (topic original) > qa-question-level/ > round2/s2/final-push/
```

**Do NOT use file alphabetical sorting** — `round2` sorts before `canonical` and would be误选 as keep. Use business rules: the original topic file (items/) is always the canonical keeper.

### Step 4: Renumber ID Collisions

For `id_collision` entries, the conflicting Q-ID must be renumbered:

```python
def next_available_qid(base_prefix: str, existing_ids: set) -> str:
    """Find next numeric suffix after the base prefix."""
    # e.g., base_prefix="Q-1.1" → try Q-1.1-01, Q-1.1-02, ...
    # Skip any ID already in existing_ids
    suffix = 1
    while True:
        candidate = f"{base_prefix}-{suffix:02d}"
        if candidate not in existing_ids:
            return candidate
        suffix += 1
```

**Important**: renumbering must produce schema-valid Q-IDs: `^Q-[A-Z]?\d+(?:\.\d+)?-\d+$`. Pure numeric suffix only — no `r2`, `-s2` etc.

### Step 5: Generate Machine-Readable Maps

Produce two JSON files for downstream consumption:

**true_duplicates.json**:
```json
[{
  "qid": "Q-5.5-01",
  "layer": "qa",
  "files": ["qa/5.5-xxx.md", "items/5.5-items.md"],
  "hash": "abc123...",
  "subject": "accounting",
  "preview": "First 80 chars of question..."
}]
```

**renumber_map.json**:
```json
[{
  "subject": "physics",
  "old_qid": "Q-3.2-05",
  "new_qid": "Q-3.2-12",
  "file": "qa-question-level/3.2-xxx.md"
}]
```

### Step 6: Apply with Gate

Dedup apply requires authorization (see [[igcse-qbank-verification]] Step 9). Dry-run is always permitted.

## Real-World Results (v3, 7 subjects, 3154 questions)

| Category | Count |
|----------|-------|
| Total Q-IDs examined | 3154 |
| True duplicates | 7 |
| ID collisions requiring renumber | 32 |
| Renumber mappings generated | 37 |
| Data loss | **0** |

## Verification After Apply

After applying dedup:
1. Re-run full verification (`qbank_verify.py`)
2. Confirm 0 within-layer duplicate Q-IDs
3. Confirm all renumbered Q-IDs pass schema validation
4. Regenerate manifest to reflect removed/renumbered entries

## Related

- [[igcse-qbank-verification]] — full verification flow including lifecycle states
