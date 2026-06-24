---
name: ap-content-production-pitfalls
description: Pitfalls discovered during AP Calculus AB T-32 production (FAILED first review). Use when producing AP-level (high-difficulty) STEM content, especially with parallel sub-agents. AP content fails differently from IGCSE.
metadata:
  type: experience
  generated_by: manager
  date: 2026-06-22
  source: AP Calculus AB T-32 FAIL verdict
---

# AP Content Production Pitfalls

## Context

AP Calculus AB T-32: 24 topics × 18 items = 432 items produced by parallel sub-agents.
**First review verdict: FAIL ❌** — multiple math errors + heavy tone pollution.

## Why AP Fails Differently from IGCSE

IGCSE content rarely had math-design errors. AP content failed on:
1. **Question design errors** (not just answer errors)
2. **Self-contradicting explanations** (108-line LLM self-negation in one item)
3. **Answer/Explanation mismatch** (376.99 vs 585.9 in same item)
4. **Mass tone pollution** (76 heavy + 27 light tone items)

## Root Causes

### 1. Parallel sub-agents amplify errors
- Each sub-agent produces a topic independently
- No cross-agent consistency check
- Math errors compound: harder content + no self-verification

### 2. High difficulty = higher error rate
- L'Hôpital, ε-δ, FRQ-level items
- AP C-class items require multi-step derivations
- More steps = more places to make sign/arithmetic errors

### 3. Tone leaks under cognitive load
- When the math is hard, LLM "thinks out loud": Wait/Hmm/Let me recalculate
- 108-line self-negation = LLM trying multiple approaches in the answer text
- This is WORSE in AP than IGCSE (harder problems → more thinking-out-loud)

## Prevention Patterns

### MUST: Self-verification gate per item
- Each item: after writing answer, RE-DERIVE independently
- If two derivations disagree → flag, don't ship
- Especially for limits, L'Hôpital, optimization (max/min)

### MUST: Answer/Explanation consistency check
- Final answer in Answer field MUST match Explanation conclusion
- Common failure: Explanation correct, Answer field has old/wrong value

### MUST: Question design validation for MCQ
- For "which is NOT X" questions: verify at least one option IS NOT X
- L'Hôpital trap: all options 0/0 → no valid answer → broken question

### MUST: Tone scan BEFORE submit (not after review)
- Python regex scan: Wait|Hmm|Actually|Let me (redo|recalculate|recompute|be more careful)
- Self-negation pattern: answer text >50 lines = likely contains thinking-out-loud
- Clean BEFORE sending to review, not as post-review fix

### SHOULD: Difficulty distribution post-check
- After batch, count F/S/C per topic
- Target tolerance ±1 per category
- Don't trust manifest claims; count actual item difficulty tags

## Quality Gate Recommendation for AP

```
Per-topic production:
1. Generate 18 items
2. Self-verify math (re-derive each answer)
3. Check Answer == Explanation conclusion
4. Validate MCQ design (NOT-questions have valid answer)
5. Python tone scan + clean
6. Count F:S:C distribution
7. ONLY THEN submit to review
```

## Related

- See: `{{name:c-class-expansion-workflow}}` for IGCSE baseline
- See: `{{name:workflow-recovery-patterns}}` for worker crash handling
- AP target: F:5|S:7|C:6 per topic (±1), NOT IGCSE's F:6|S:6|C:6
