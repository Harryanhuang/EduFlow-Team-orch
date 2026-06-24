---
name: ap-qbank-verification
description: AP subject QBank verification — directory layout, 15-key frontmatter validation, difficulty codes, QA self-check, manifest count check. Use when verifying any AP subject's QBank output.
metadata:
  type: workflow
  generated_by: worker_qbank
  date: 2026-06-24
---

# AP QBank Verification

## AP Directory Layout (differs from IGCSE)

```
AP {Subject Name}/
├── 02-题库/
│   ├── items/
│   │   └── Unit N/
│   │       └── Ux.y.z-{F|S|C}.md    # per-question file
│   ├── qa-manifest.csv
│   └── QA-自检.md                     # self-check document
```

**Key difference from IGCSE**: AP stores one question per `.md` file with YAML frontmatter. IGCSE uses multi-question markdown files with heading-based delimiters.

## File Naming Convention

Pattern: `^U\d+\.\d+\.\d+-(?:F|S|C)\.md$`

| Suffix | Difficulty |
|--------|-----------|
| `F` | Foundation |
| `S` | Standard |
| `C` | Challenge |

## Frontmatter Schema (15 Required Keys)

Every item `.md` file MUST have all 15 keys in YAML frontmatter:

```yaml
---
id: U4.2.1-S
difficulty: S          # F | S | C
type: MCQ              # question type
calculator: false      # calculator allowed
subject: "AP Physics C: Mechanics"
unit: 4
topic: 2
subtopic: 1
learning_objective: "..."
knowledge_point: "..."
core_concept: "..."
exam_pattern: "..."
question_type: "..."
common_mistake: "..."
explanation_context: "..."
---
```

**Validation**: any missing key = `missing_frontmatter` blocker.

## Validation Checks

### 1. Frontmatter Completeness
- All 15 keys present
- `difficulty` in `{F, S, C}`
- `id` matches filename pattern

### 2. Content Structure (per .md file)
Each file must contain these markdown headings:
- `## Options` (for MCQ) or answer area
- `## Answer`
- `## Explanation`

Missing heading = `missing_heading` blocker.

### 3. QA Self-Check

File `QA-自检.md` must contain the exact string:
```
本 Unit 状态：**完成**
```

Not present = `qa_self_check_not_complete` blocker.

### 4. Manifest Consistency

`qa-manifest.csv`:
- Skip SUMMARY rows
- Compare manifest item count to actual file count in `items/Unit N/`
- Mismatch = `manifest_item_count_mismatch` blocker

### 5. Difficulty Distribution Check

Verify the difficulty mix in each unit is reasonable:
- No unit should be 100% Foundation or 100% Challenge
- Flag extreme distributions as warnings

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All checks passed |
| 1 | One or more blocking failures |

## CLI Usage

```bash
python3 scripts/ap_qbank_verify.py --subject-dir "/path/to/AP Subject Name" [--json]
```

JSON output includes `blocking_reasons` array for programmatic consumption.

## Blocking Reasons Taxonomy

| Reason | Severity | Fix |
|--------|----------|-----|
| `missing_frontmatter` | BLOCK | Add all 15 required YAML keys |
| `invalid_difficulty` | BLOCK | Use F/S/C only |
| `missing_heading` | BLOCK | Add ## Options/Answer/Explanation |
| `manifest_item_count_mismatch` | BLOCK | Regenerate manifest |
| `qa_self_check_not_complete` | BLOCK | Mark QA-自检.md as 完成 |
| `missing_items_directory` | BLOCK | Create items/Unit N/ structure |

## Common Pitfalls

1. **Manifest generated before expansion**: always regenerate AFTER all items are created
2. **QA-自检.md not updated**: must be explicitly marked complete after all items pass self-check
3. **Filename typo**: file must match `Ux.y.z-{F|S|C}.md` exactly — underscores or extra digits break regex

## Related

- [[igcse-qbank-verification]] — IGCSE-specific 3-layer verification (different architecture)
- [[qbank-dedup-content-hash]] — dedup patterns (AP typically doesn't need cross-layer dedup)
