# Skill: AP Item Production (F/S/C Three-Piece Set)

## When To Use

When producing AP physics/math/science qbank items for any subtopic. Each subtopic gets exactly 3 items:
- **F (Foundation)**: Concept identification, definition recall, basic calculation
- **S (Standard)**: Multi-step calculation, concept application, standard exam patterns
- **C (Challenge)**: FRQ-level, cross-topic integration, analysis and synthesis

## Template

### File Naming

```
U{unit}.{topic}.{subtopic}-{F|S|C}.md
```

Example: `U9.1.1-F.md`, `U9.1.1-S.md`, `U9.1.1-C.md`

### YAML Frontmatter (Required for All Items — 12 fields)

```yaml
---
id: U{unit}.{topic}.{subtopic}-{F|S|C}
unit: U{unit}
topic: {unit}.{topic}
subtopic: {unit}.{topic}.{subtopic}
knowledge_point: {Chinese or English topic name}
core_concept: {One sentence describing the key physics concept}
exam_pattern: {How this appears on the AP exam}
question_type: mcq
difficulty: F|S|C
calculator: no-calc|calc
common_mistake: {2-3 common errors students make}
explanation_context: {Theoretical framework for the explanation}
---
```

> **Schema ownership note (2026-06-24 audit)**: This is the **single source of truth** for the item schema. `ap-qa-selfcheck.md` (worker self-check) and `ap-review-playbook.md` (reviewer check) MUST verify the same 12 fields. If you add/rename a field here, update both downstream skills in the same commit.

### Body Structure

```markdown
{Question text — clear, specific, self-contained}

## Options
A) {option}
B) {option}
C) {option}
D) {option}

## Answer
{Letter}

## Explanation
{2-4 sentences: correct reasoning, why other options are wrong, common mistake warning}
```

## Difficulty Definitions

### F (Foundation) — ~30% of items
- Concept identification or definition
- Single-step calculation with given values
- Direct formula application
- **Calculator**: usually `no-calc`
- **Common mistakes**: confusion of basic definitions

### S (Standard) — ~40% of items
- Multi-step calculation
- Concept application in standard scenarios
- Comparison or ranking tasks
- **Calculator**: usually `calc`
- **Common mistakes**: sign errors, unit conversion, wrong formula selection

### C (Challenge) — ~30% of items
- FRQ-level analysis
- Cross-topic integration
- "Which statement is correct" format
- Design or evaluation questions
- **Calculator**: varies
- **Common mistakes**: conceptual traps, exception handling

## Quality Rules

1. **No tone tokens**: Never use "Wait", "Hmm", "let me", "重新检查"
2. **Unique correct answer**: Only one option is correct; no equivalent options
3. **Self-consistent explanation**: Answer must match explanation; explanation must match question
4. **Physical correctness**: All numbers, formulas, and reasoning must be physically accurate
5. **No information leaks**: Explanation must not reveal the answer before the reasoning

## Batch Production Workflow

For a unit with N subtopics:

1. Write all N × F items first (same difficulty, faster batch)
2. Write all N × S items
3. Write all N × C items
4. Count: verify total = N × 3
5. Generate QA-自检.md
6. Update qa-manifest.csv
7. Submit for review

## Example (AP Physics — Foundation)

```yaml
---
id: U9.1.1-F
unit: U9
topic: 9.1
subtopic: 9.1.1
knowledge_point: Pascal's Law
core_concept: A change in pressure applied to an enclosed fluid is transmitted undiminished to every point of the fluid.
exam_pattern: Given a hydraulic system, calculate force or pressure using Pascal's law.
question_type: mcq
difficulty: F
calculator: no-calc
common_mistake: Confusing Pascal's law with atmospheric pressure; forgetting that force depends on area.
explanation_context: Hydraulic press, Pascal's principle.
---
A hydraulic press has two pistons. The smaller piston has area $2 \text{ cm}^2$ and the larger has $100 \text{ cm}^2$. A force of $10 \text{ N}$ is applied to the smaller piston. What is the force on the larger piston?

## Options
A) $10 \text{ N}$
B) $200 \text{ N}$
C) $500 \text{ N}$
D) $1000 \text{ N}$

## Answer
C

## Explanation
By Pascal's law, $F_2 = F_1 \times (A_2/A_1) = 10 \times (100/2) = 500 \text{ N}$.
```
