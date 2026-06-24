# Skill: AP Manifest CSV Sync

## When To Use

After generating items for a Unit, update the qa-manifest.csv in the subject's root directory. The manifest tracks all subtopics, their item counts, and status.

## Output File

```
content/ap-{subject}/qa-manifest.csv
```

## CSV Format

```csv
topic_id,topic_name,unit,items_count,question_count,difficulty_mix,calculator_marked,status,notes
U9.1.1,Pascal's Law,U9,3,3,F:1|S:1|C:1,yes,submitted_for_review,Unit 9 subtopic items
```

## Field Definitions

| Field | Description | Example |
|-------|-------------|---------|
| `topic_id` | Subtopic ID matching file naming | `U9.1.1` |
| `topic_name` | Human-readable topic name | `Pascal's Law` |
| `unit` | Unit number | `U9` |
| `items_count` | Number of item files | `3` |
| `question_count` | Number of questions (usually = items_count) | `3` |
| `difficulty_mix` | Distribution of difficulties | `F:1\|S:1\|C:1` |
| `calculator_marked` | Whether calculator is used in any item | `yes` or `no` |
| `status` | Current status | `submitted_for_review` |
| `notes` | Optional notes | `Batch 1 gap-fill CED 2.1.1` |

## Rules

1. **One row per subtopic** — no SUMMARY rows (removed in R42)
2. **items_count = 3** for standard production (F+S+C)
3. **difficulty_mix always F:1|S:1|C:1** for standard production
4. **calculator_marked = yes** if ANY of the 3 items uses `calc`
5. **status = submitted_for_review** when items are complete and QA is done
6. **No duplicate topic_id** — each subtopic appears exactly once

## Append Workflow

For each new Unit's subtopics:

```bash
# After producing items for Unit N, append rows:
# (Write each row to the CSV file)
```

## Verification

```bash
# Count total rows (excluding header)
tail -n +2 content/ap-{subject}/qa-manifest.csv | wc -l

# Verify no SUMMARY rows
grep "SUMMARY" content/ap-{subject}/qa-manifest.csv

# Check total items match
tail -n +2 content/ap-{subject}/qa-manifest.csv | awk -F',' '{sum += $4} END {print "Total items:", sum}'
```

## Manifest Parity Check

Before submitting for review, verify:
- [ ] CSV row count = number of subtopics produced
- [ ] No SUMMARY rows present
- [ ] Total items in CSV = total .md files in subtopics directory
- [ ] Each topic_id matches an existing file
- [ ] No duplicate topic_ids

## AP Physics 2 Manifest Example

```csv
topic_id,topic_name,unit,items_count,question_count,difficulty_mix,calculator_marked,status,notes
U9.1.1,Pascal's Law,U9,3,3,F:1|S:1|C:1,yes,submitted_for_review,Unit 9 subtopic items
U9.1.2,Pressure in a Fluid at Rest,U9,3,3,F:1|S:1|C:1,yes,submitted_for_review,Unit 9 subtopic items
U9.2.1,Buoyancy and Archimedes' Principle,U9,3,3,F:1|S:1|C:1,yes,submitted_for_review,Unit 9 subtopic items
...
```
