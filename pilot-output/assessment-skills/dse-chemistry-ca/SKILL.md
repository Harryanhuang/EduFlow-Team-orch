# SKILL: DSE Chemistry Syllabus Classification

## Purpose

Classify chemistry items (questions, prompts, learning materials) against the Hong Kong DSE Chemistry curriculum.

## When to use

Use when the user provides chemistry content and asks which DSE Chemistry topic it belongs to, whether it is in scope, or how it should be routed.

## Required structured files

- `metadata.json` — assessment identity and source provenance.
- `topics.json` — compulsory and elective topic tree.
- `assessment.json` — paper structure, assessment objectives, question styles, difficulty/confidence rules.
- `examples.md` — golden classification examples.
- `references/source-index.md` and `references/page-map.json` — source evidence.

## Supported modes

- Classification only. `lesson_use.supported=false` in v1.

## Output format

Return a routing verdict:

```
skill_id: dse-chemistry-ca
topic_id: <topic_id> or <multiple> or out_of_scope
confidence: 0.0–1.0
threshold_source: assessment.confidence_thresholds.classification_minimum (0.75)
reason: short evidence with page reference
```

## Special rules

- Compulsory topics 1-12 are always in scope for Paper 1.
- Elective topics 13-15 are in scope only if the item explicitly matches one of the three electives; students choose two, so the classifier should still route to the matched elective topic.
- Topic 16 (Investigative Study) and STSE discussion prompts are not public-exam content topics; mark as `out_of_scope` unless the request is explicitly about SBA skills.
- Cross-topic items should list a primary topic and secondary topics.
- If confidence is below 0.75, flag for human review.
- Do not copy official text; cite page references only.
