---
name: item-format-spec
description: Canonical item format for IGCSE multi-question and AP single-question files. Use when worker_course creates new items or when review_course validates item structure. Covers field requirements, difficulty codes, MCQ vs free-response, and common format errors.
metadata:
  type: reference
  generated_by: Luke_recorder
  date: 2026-06-24
  source: c-class-expansion-workflow + ap-qbank-verification + review_course rejection logs
---

# Item Format Specification

## IGCSE Item Format

File: `items/topic_{N}.md` — contains up to 18 items per topic.

### Structure

```markdown
**Item 1 [F]**

Question:
<question text — may include sub-questions a/b/c>

Answer:
<correct answer — for MCQ: the letter; for free-response: full solution>

Difficulty:
Foundation

Topic:
1.1 Algebra Basics

Explanation:
<step-by-step explanation — must end with the same answer as Answer field>

Tags:
algebra, linear-equations
```

### Required Fields

| Field | Required | Notes |
|-------|----------|-------|
| `**Item N [F/S/C]**` | Yes | Header with difficulty tag |
| `Question:` | Yes | May include sub-questions |
| `Answer:` | Yes | Must match Explanation conclusion |
| `Difficulty:` | Yes | Foundation / Standard / Challenge |
| `Topic:` | Yes | Must match topic-outline.md entry |
| `Explanation:` | Yes | Step-by-step, no thinking-out-loud |
| `Tags:` | Yes | Comma-separated, lowercase |

### Difficulty Distribution Per Topic

| Syllabus | Foundation | Standard | Challenge | Total |
|----------|-----------|----------|-----------|-------|
| IGCSE | 4 | 8 | 6 | 18 |
| AP | 5 | 7 | 6 | 18 |

### Question Level Files

File: `qa-question-level/Q-{N}-{NN}.md` — one per item.

These mirror the item content in a different format for qbank import.
Must have matching count: if `topic_1.md` has 18 items, there must be
18 `Q-1-XX.md` files.

## AP Item Format

File: `items/Unit N/U{x}.{y}.{z}-{F|S|C}.md` — one file per question.

### Structure (YAML Frontmatter)

```markdown
---
id: U4.2.1-S
difficulty: S
type: MCQ
calculator: false
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

<question text>

A. <option>
B. <option>
C. <option>
D. <option>

**Answer: B**

**Explanation:**
<step-by-step reasoning>
```

### AP 15 Required Frontmatter Keys

All 15 keys MUST be present. Missing any key = `missing_frontmatter` blocker.

```
id, difficulty, type, calculator, subject, unit, topic, subtopic,
learning_objective, knowledge_point, core_concept, exam_pattern,
question_type, common_mistake, explanation_context
```

### AP File Naming Pattern

```
U{unit}.{topic}.{subtopic}-{F|S|C}.md
```

Example: `U4.2.1-S.md` = Unit 4, Topic 2, Subtopic 1, Standard difficulty.

## Common Format Errors

| Error | How to spot | Fix |
|-------|-------------|-----|
| Missing `Tags:` field | grep -v "Tags:" items/*.md | Add tags |
| Difficulty mismatch | Item header says [F] but Difficulty: says Standard | Align both |
| Answer ≠ Explanation | Numerical answer in Answer field doesn't match Explanation conclusion | Reconcile |
| Thinking-out-loud in Explanation | Wait/Actually/Hmm in Explanation text | Run tone scan |
| Missing topic-level files | items/ has files but qa-question-level/ doesn't | Create matching Q files |
| AP missing frontmatter key | YAML parser error on any key | Add missing key |

## Validation Command

```bash
# IGCSE: check all items have required fields
for f in items/topic_*.md; do
  for field in "Question:" "Answer:" "Difficulty:" "Topic:" "Explanation:" "Tags:"; do
    grep -q "$field" "$f" || echo "MISSING $field in $f"
  done
done

# AP: check frontmatter keys
for f in items/Unit*/*.md; do
  python3 -c "
import yaml, sys
text = open('$f').read()
start = text.index('---') + 3
end = text.index('---', start)
data = yaml.safe_load(text[start:end])
required = ['id','difficulty','type','calculator','subject','unit','topic',
            'subtopic','learning_objective','knowledge_point','core_concept',
            'exam_pattern','question_type','common_mistake','explanation_context']
missing = [k for k in required if k not in data]
if missing: print(f'MISSING KEYS in $f: {missing}')
"
done
```

## Related

- `{{name:worker-course-production-checklist}}` — per-item quality gate
- `{{name:tone-scan-pre-review}}` — tone scan for Explanation fields
- `{{name:igcse-qbank-verification}}` — validation against this spec
- `{{name:ap-qbank-verification}}` — AP-specific 15-key validation
- `{{name:ap-review-playbook}}` — Step 2 manifest parity check
