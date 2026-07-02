# SKILL: DSE Physics Syllabus Classification

## Purpose

Classify physics items (questions, prompts, learning materials) against the Hong Kong DSE Physics curriculum.

## When to use

Use when the user provides physics content and asks which DSE Physics topic it belongs to, whether it is in scope, or how it should be routed.

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
skill_id: dse-physics-ca
topic_id: <topic_id> or <multiple> or out_of_scope
confidence: 0.0–1.0
threshold_source: assessment.confidence_thresholds.classification_minimum (0.75)
reason: short evidence with page reference
```

## Special rules

- Compulsory topics I-V are always in scope for Paper 1.
- Elective topics VI-IX are in scope only if the item explicitly matches one of the four electives; students choose two, so the classifier should still route to the matched elective topic.
- Curriculum planning, STSE discussion prompts and general pedagogy are not public-exam content topics; mark as `out_of_scope` unless the request is explicitly about SBA skills.
- Cross-topic items should list a primary topic and secondary topics.
- If confidence is below 0.75, flag for human review.
- Do not copy official text; cite page references only.
