---
name: tone-scan-pre-review
description: Mandatory tone pollution scan before submitting content to review_course. Covers Wait/Actually/Hmm/Let me redo blocking tokens, self-negation detection, answer-length heuristic, and Python regex scripts. Use at end of every worker_course production batch.
metadata:
  type: workflow
  generated_by: Luke_recorder
  date: 2026-06-24
  source: igcse-9subject-sprint-lessons + ap-content-production-pitfalls + review_course rejection logs
---

# Tone Scan Before Review (Mandatory Gate)

## Why This Exists

Tone pollution is the **#1 review rejection cause** across IGCSE and AP
production runs. Items with LLM thinking-out-loud tokens get
`quality_not_met` verdicts and require a full re-scan — wasting a
review cycle.

## Blocking Tokens (Hard Fail)

These tokens in **any item's Answer or Explanation field** = automatic rejection:

```
Wait|Actually|Hmm|Let me (redo|recalculate|recompute|be more careful)|
Need to redo|ERROR|Let me check|I need to
```

## Soft Warning Tokens (Flag, Don't Block)

These appear in less severe forms but still reduce quality:

```
Hmm|I think|Maybe|Perhaps|It seems like|I'm not sure
```

## Self-Negation Detection

**Symptom**: answer text >50 lines = likely contains LLM "thinking
out loud" or contradicting itself.

**Check**: count lines in each Answer field. If >50, flag for manual review.

**Example (AP Calculus T-32)**: one item had 108 lines of self-negation
in its explanation — the LLM wrote multiple approaches then chose one
mid-text.

## Python Scan Script

```python
import re, sys, pathlib

BLOCKERS = re.compile(
    r'\b(Wait|Actually|Hmm|Let me redo|Let me recalculate|'
    r'Let me recompute|Let me be more careful|Need to redo|'
    r'ERROR|Let me check|I need to)\b',
    re.IGNORECASE
)

SOFT = re.compile(
    r'\b(Hmm|I think|Maybe|Perhaps|It seems like|I\'m not sure)\b',
    re.IGNORECASE
)

def scan_file(path):
    text = path.read_text()
    blockers = BLOCKERS.findall(text)
    soft = SOFT.findall(text)
    lines = len(text.splitlines())
    long = lines > 50
    return {
        'file': str(path),
        'blocking': blockers,
        'warning': soft,
        'line_count': lines,
        'over_50_lines': long,
    }

def scan_dir(root):
    results = []
    for f in pathlib.Path(root).rglob('*.md'):
        if f.name in ('topic-outline.md', 'qa-manifest.csv'):
            continue
        r = scan_file(f)
        if r['blocking'] or r['over_50_lines'] or r['warning']:
            results.append(r)
    return results

if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    issues = scan_dir(root)
    if not issues:
        print('CLEAN — no tone issues found')
    else:
        for r in issues:
            print(f"\n{'BLOCK' if r['blocking'] else 'WARN'}: {r['file']}")
            if r['blocking']:
                print(f"  BLOCKING tokens: {r['blocking']}")
            if r['over_50_lines']:
                print(f"  SELF-NEGATION: {r['line_count']} lines (>50)")
            if r['warning']:
                print(f"  Warning tokens: {r['warning']}")
        sys.exit(1)
```

## Run Before Submit

```bash
python3 .claude/skills/_scripts/tone_scan.py content/igcse-{subject}-{code}/items/
# Exit code 0 = clean, 1 = issues found
```

## When to Run

1. **After every batch** (before sending to review_course)
2. **Before final submit** (after last expansion batch)
3. **On rework** (after fixing flagged items, re-scan before re-submit)

## Allowed Tokens (NOT Blocking)

These are legitimate math teaching steps — do NOT flag them:

```
Verify:|Check:|Substitute:|Solve:|Try:|Calculate:|Evaluate:|
Derive:|Simplify:|Factor:|Expand:
```

## Related

- `{{name:review-criteria}}` — what happens if tone scan is skipped
- `{{name:ap-content-production-pitfalls}}` — AP-specific tone examples
- `{{name:igcse-9subject-sprint-lessons}}` — Pattern 3: tone cleanup mandatory
