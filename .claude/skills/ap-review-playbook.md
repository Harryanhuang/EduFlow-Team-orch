---
name: ap-review-playbook
description: Standard review playbook for AP-level content produced by worker_course. Use when review_course receives an AP/STEM submit-review task (Physics, Calculus, Statistics, Psychology, Biology, Chemistry, CSA). Covers the full review path from file discovery to verdict delivery.
metadata:
  type: experience
  generated_by: review_course
  date: 2026-06-24
  source: T-44 AP Statistics, T-45 AP Psychology, T-40~T-46 AP Calculus AB, T-43/AP Physics 1 B1~B6 review cycles
---

# AP Review Playbook

## Use When

- `eduflow inbox review_course` delivers an AP subject submit-review trigger
- Workflow: ap-knowledge-base-optimization
- Subjects covered: AP Calculus AB/BC, AP Physics 1/2/C, AP Statistics, AP Psychology, AP Biology, AP Chemistry, AP CSA

## Review Path (in order)

### Step 1: Discover Output Location

AP content lands under Obsidian knowledge base:
```
/Volumes/Halobster/Obsidian Edu/留学公司知识库/01-留学课程通用知识/03-AP知识库/03-学科知识/<Subject>/02-题库/items/<Unit>/
```
Each unit contains:
- `qa-manifest.csv` — one row per subtopic, columns: `topic_id, topic_name, unit, items_count, question_count, difficulty_mix, calculator_marked, status, notes`
- `QA-自检.md` — worker's self-check summary
- `<subtopic>/<item>.md` — individual item files (naming: `U{X}.{Y}.{Z}-{F|S|C}.md`)

### Step 2: Manifest Parity Check

**MUST DO FIRST — catches the most common gate-blocking error.**

1. Read `qa-manifest.csv`: count data rows (exclude HEADER and any SUMMARY/total rows)
2. Count actual `.md` item files under `items/` (excluding manifest and self-check)
3. **Rule:** data_rows × 3 = item_file_count (each subtopic = 3 items: F/S/C)
4. If mismatch → REVISION REQUIRED with specific counts

Known pitfall: manifests sometimes include SUMMARY rows (row count = data_rows + N_summary), making count ≠ expected. Worker must delete SUMMARY rows before review.

### Step 3: Schema Spot-Check (5 subtopics × 3 items = 15 items)

Select 5 subtopics (stratified: mix of early/mid/late units):
- For each: read all 3 files (F.md, S.md, C.md)
- Check the 12-field YAML frontmatter is complete:
  `id, unit, topic, subtopic, knowledge_point, core_concept, exam_pattern, question_type, difficulty, calculator, common_mistake, explanation_context`
- Check the 4 body sections are present: `Question`, `## Options`, `## Answer`, `## Explanation`
- Verify `id` matches filename (e.g., file `U1.2.2-F.md` must have `id: U1.2.2-F`)
- Flag any missing or malformed fields

**Source of truth**: the production schema is defined in `ap-item-production.md`. This step verifies items match that template, not a different/older schema.

### Step 4: Content/Math Verification

For each spot-checked item:
- **Re-derive math independently** — don't trust the answer field
- **Answer ↔ Explanation consistency** — final answer in Answer field must match Explanation conclusion
- **g-value consistency** — if stem says g=10, options and explanation must use g=10 (not 9.8)
- **Stopping conditions** — for energy/work problems: check |W_friction| > E_initial → answer should be 0 m/s (not continuing motion)
- **NOT-questions** — for "which is NOT X" MCQs, verify exactly one option is NOT X
- **Physics conceptual** — check units, signs, vector directions, reference frame consistency

### Step 5: Tone Artifact Scan

Run across ALL items in the unit (not just spot-checked):
```python
import re, glob
PATTERNS = r'Wait|Hmm|Actually|Let me (redo|recalculate|recompute|be more careful)|I need to|Let us reconsider'
for f in glob.glob('**/*.md', recursive=True):
    text = open(f).read()
    hits = re.findall(PATTERNS, text, re.IGNORECASE)
    if hits: print(f, hits)
```
- 0 artifacts → PASS
- Any artifacts → REVISION REQUIRED (list file + artifact text)

### Step 6: Difficulty Distribution Check

Count actual F/S/C across all items:
- Per subtopic: expect 1F + 1S + 1C = 3 items
- Per unit: F_total = S_total = C_total = number_of_subtopics
- Tolerance: exact (since 3-item-per-subtopic is hard constraint)

### Step 7: Deliver Verdict

| Gate | Pass | Fail |
|------|------|------|
| Manifest parity | data_rows × 3 = file_count | REVISION REQUIRED |
| Schema (15 items) | All 12 YAML fields + 4 body sections present | REVISION REQUIRED |
| Content/math | All re-derived answers match | REVISION REQUIRED (list errors) |
| Tone scan | 0 artifacts across all files | REVISION REQUIRED (list files) |
| Difficulty distribution | F=S=C = subtopic_count | REVISION REQUIRED |

**Verdict delivery:**
```bash
eduflow task review T-XX --approve  # or --reject
eduflow say review_course "T-XX <Subject> <Unit> PASS/REVISION: <one-line summary>" --to user
```

## Known Error Patterns by Subject

### AP Calculus AB/BC
- L'Hôpital application errors (0/0 form misidentified)
- Options with same value duplicated (broken MCQ)
- Integral sign errors in multi-step evaluation

### AP Physics 1/2/C
- **g-value inconsistency**: stem says g=10, explanation uses g=9.8
- **Energy stopping condition**: |W_fric| > E_initial → block stops, but answer says it continues
- **Direction/sign errors**: velocity vs speed, work sign conventions
- Tone leaks: "Wait, let me reconsider" in C-class multi-step items

### AP Statistics
- Manifest SUMMARY-row pollution (data row ≠ expected count)
- Probability calculation errors in binomial/normal problems
- Mislabelled distribution type

### AP Psychology
- Lower error rate (less math-heavy)
- Focus: definition accuracy, theory attribution, example-concept alignment

### AP Biology / Chemistry
- Expected: formula balancing, unit conversions, reaction pathway errors
- Bio: metabolic pathway direction errors; Chem: equilibrium constant expressions

## Related Skills

- [[ap-content-production-pitfalls]] — production-side prevention (worker_course reference)
- [[workflow-recovery-patterns]] — worker crash / stale evidence recovery
- [[brainstorming]] — production preflight (worker_course reference)
