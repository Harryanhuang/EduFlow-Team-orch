---
name: manifest-generation
description: When and how to generate/regenerate qa-manifest.csv for any subject. Covers IGCSE multi-question and AP single-question formats, row count validation, and the "always regenerate before final review" rule. Use when producing new content or expanding existing subjects.
metadata:
  type: workflow
  generated_by: Luke_recorder
  date: 2026-06-24
  source: igcse-9subject-sprint-lessons Pattern 4 + c-class-expansion-workflow Phase 3
---

# Manifest Generation & Regeneration

## Why This Exists

The manifest is the single source of truth for review_course and
worker_qbank. An outdated manifest causes:
- review_course counts mismatch → `quality_not_met` verdict
- worker_qbank unified_manifest merge fails → errors spike
- Subject closeout gate fails (items count ≠ manifest rows)

**Rule**: ALWAYS regenerate the manifest after content expansion,
BEFORE final review. Never trust a pre-expansion manifest.

## When to Generate

| Situation | Action |
|-----------|--------|
| New subject (first production) | Generate after first batch |
| Expansion (adding topics) | Regenerate after expansion completes |
| After rework (fixing flagged items) | Regenerate if files changed |
| Before final review submit | Regenerate (mandatory) |
| Before qbank integration | Regenerate (mandatory) |

## IGCSE Manifest Format

File: `content/igcse-{subject}-{code}/qa-manifest.csv`

```csv
topic_id,topic_name,items_file,items_count,question_files,questions_count
1.1,"Algebra Basics",topic_1.md,18,"Q-1-01.md..Q-1-18.md",18
1.2,"Quadratic Equations",topic_2.md,18,"Q-2-01.md..Q-2-18.md",18
```

**Generation script** (run from subject directory):

```python
import csv, pathlib, re

subject_dir = pathlib.Path('.')
items_dir = subject_dir / 'items'
qql_dir = subject_dir / 'qa-question-level'
outline = subject_dir / 'topic-outline.md'

# Parse outline for topic names
topic_names = {}
for line in outline.read_text().splitlines():
    m = re.match(r'^\s*(\d+\.\d+)\s+(.+)', line)
    if m:
        topic_names[m.group(1)] = m.group(2).strip()

rows = []
for items_file in sorted(items_dir.glob('topic_*.md')):
    # Filename convention: topic_N_M.md → topic_id "N.M".
    # (e.g. topic_1_2.md → "1.2"; topic_1_2_3.md → "1.2.3")
    parts = items_file.stem.replace('topic_', '').split('_')
    topic_id = '.'.join(parts)
    items_count = len(re.findall(r'\*\*Item \d+', items_file.read_text()))
    qql_files = list(qql_dir.glob(f'Q-{topic_id.replace(".", "-")}-*.md'))
    rows.append({
        'topic_id': topic_id,
        'topic_name': topic_names.get(topic_id, ''),
        'items_file': items_file.name,
        'items_count': items_count,
        'question_files': f'Q-{topic_id.replace(".", "-")}-01.md..Q-{topic_id.replace(".", "-")}-{items_count:02d}.md',
        'questions_count': len(qql_files),
    })

with open('qa-manifest.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['topic_id','topic_name','items_file','items_count','question_files','questions_count'])
    w.writeheader()
    w.writerows(rows)

print(f'Manifest written: {len(rows)} topics, {sum(r["items_count"] for r in rows)} items')
```

## AP Manifest Format

File: `02-题库/qa-manifest.csv`

```csv
subtopic_id,items_count,files_list
U4.2.1,3,"U4.2.1-F.md,U4.2.1-S.md,U4.2.1-C.md"
U4.2.2,3,"U4.2.2-F.md,U4.2.2-S.md,U4.2.2-C.md"
```

**AP rule**: each subtopic = exactly 3 items (F/S/C).
`data_rows × 3 = total_item_file_count`. Any mismatch = blocker.

## Validation After Generation

```python
# After generating, validate:
import csv
with open('qa-manifest.csv') as f:
    rows = list(csv.DictReader(f))

total_items = sum(int(r['items_count']) for r in rows)
actual_files = len(list(items_dir.glob('topic_*.md')))

assert total_items == actual_files, f"MISMATCH: manifest={total_items}, files={actual_files}"
print(f"VALID: {total_items} items, {len(rows)} topics")
```

## Common Mistakes

1. **Not regenerating after expansion** — the #1 cause of manifest drift
2. **Forgetting to update item counts** after adding/removing items
3. **Trusting old manifest** — always regenerate from actual files
4. **Wrong separator** — IGCSE uses `N.M`, files use `N-M`; don't confuse

## Related

- `{{name:c-class-expansion-workflow}}` — Phase 4 closeout requires fresh manifest
- `{{name:igcse-qbank-verification}}` — Step 2 uses manifest for validation
- `{{name:ap-review-playbook}}` — Step 2 Manifest Parity Check
- `{{name:qbank-lifecycle-gates}}` — manifest drift = reverify state
