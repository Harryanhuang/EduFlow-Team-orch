# Skill: AP Topic Outline Framework

## When To Use

When starting a new AP subject — generate the topic outline before any item production. This is the first step of the ap-knowledge-base-optimization workflow.

## Source

College Board Course and Exam Description (CED) PDF — the authoritative source for:
- Unit structure and numbering
- Topic names and IDs
- Exam weighting percentages
- Learning objectives

## Output File

```
content/ap-{subject}/topic-outline.md
```

## Template Structure

```markdown
# AP {Subject Name}: {Full Title} — Topic Outline

> Source: College Board AP {Subject} CED ({year})
> Generated: {date}
> Units: {range}
> Total Exam Weight: 100%

---

## Unit {N}: {Unit Name} ({weight}%)

| Topic | Name | Subtopics |
|-------|------|-----------|
| {N}.1 | {Topic Name} | {N}.1.1, {N}.1.2 |
| {N}.2 | {Topic Name} | {N}.2.1, {N}.2.2, {N}.2.3 |

---

## Summary

| Unit | Name | Exam Weight | Topics | Subtopics |
|------|------|-------------|--------|-----------|
| {N} | {Name} | {weight}% | {count} | {count} |
| **Total** | | **100%** | **{sum}** | **{sum}** |

## Production Plan

- **Items per subtopic**: 3 (F:1 | S:1 | C:1)
- **Total items**: {subtopics} × 3 = {total}
- **Batch plan**: {N} batches, one per unit
  - Batch 1: Unit {X} — {N} subtopics × 3 = {N} items
  ...
```

## Extraction Process

1. **Locate CED PDF**: Search College Board website for "[Subject] Course and Exam Description"
2. **Identify Units**: Note unit numbers, names, and exam weighting
3. **List Topics**: For each unit, list topic numbers and names
4. **Count Subtopics**: Each topic contains 2-5 subtopics
5. **Calculate Totals**: Sum subtopics, compute total items = subtopics × 3
6. **Plan Batches**: One batch per unit; note which units are large (>15 subtopics)

## Key Formulas

```
Total items = Total subtopics × 3
Batch items = Unit subtopics × 3
Exam weight range = typically 11%-17% per unit
```

## Validation Checklist

- [ ] All units from CED are represented
- [ ] Exam weights sum to 100%
- [ ] Topic numbering matches CED exactly
- [ ] Subtopic count is accurate
- [ ] Production plan covers all units

## AP Physics 2 Reference (Completed 2026-06-24)

| Unit | Name | Exam Weight | Topics | Subtopics | Items |
|------|------|-------------|--------|-----------|-------|
| 9 | Fluids | 11-14% | 3 | 6 | 18 |
| 10 | Thermodynamics | 12-15% | 5 | 9 | 27 |
| 11 | Electric Force, Field, Potential | 14-17% | 6 | 17 | 51 |
| 12 | Electric Circuits | 14-17% | 5 | 13 | 39 |
| 13 | Magnetism & EM Induction | 11-14% | 5 | 11 | 33 |
| 14 | Geometric & Physical Optics | 12-15% | 6 | 22 | 66 |
| 15 | Quantum, Atomic, Nuclear | 12-15% | 5 | 14 | 42 |
| **Total** | | **100%** | **35** | **92** | **276** |
