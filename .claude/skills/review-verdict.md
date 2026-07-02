---
name: review-verdict
description: "review_course skill: issue a structured verdict after reviewing worker artifacts. Covers verdict formatting, evidence packet requirements, scope declaration, and the handoff back to manager."
metadata:
  type: workflow
  generated_by: worker_builder
  date: 2026-06-24
---

# review_course Verdict Protocol

## When to Use

After receiving artifacts from worker_course or worker_qbank, issue a structured verdict with evidence.

For article-like content, marketing copy, WeChat/Xiaohongshu drafts, school/course
introductions, or prose-heavy artifacts, run `content-review-orchestration` before
issuing the final verdict. The content verdict must include gates for source/claim
audit, structure/logic, voice/AI residue, and platform fit.

## Verdict Types

| Verdict | Meaning | Manager Action |
|---------|---------|---------------|
| `pass` / `approved` | All quality gates met | Proceed to closeout |
| `minor_required` | Fixable issues found | Send worker repair, re-review |
| `reject` | Fundamental problems | Major rework or scope change |
| `conditional_pass` | Pass with specific conditions | Fix conditions, then closeout |

## Issuing a Verdict

### 1. ACK the review request

```bash
eduflow read <local_id> --ack started_task
eduflow status review_course 进行中 "复核中：<subject/scope>"
```

### 2. Run the review checks

Use the review checklist from `docs/workflows/<workflow>/checklist.md`:

- Format check: file structure, naming, JSON schema
- Content check: topic coverage, difficulty gradient
- Quality check: error rate, duplication, completeness
- Teaching usability: actual pedagogical value

### 3. Send the structured verdict

Use the template from `docs/workflows/igcse-subject-launch/handoff-template.md`:

```
igcse-subject-launch verdict for <subject + code>:
Verdict: <pass / minor_required / reject / conditional_pass>
Scope reviewed: <files / artifacts>
Evidence: <sampled files, mapping count, spot checks, path convention check>
Blocking issues: <none / list>
Manager action needed: <launch / reject / send minor repair>
```

```bash
eduflow send manager review_course "igcse-subject-launch verdict for <subject> (<code>):
Verdict: <verdict>
Scope reviewed: <list of files>
Evidence: <evidence summary>
Blocking issues: <none or list>
Manager action needed: <action>"
```

### 4. For item-level reviews, also send to worker_builder

```
item prototype review result:
Verdict: <pass / minor_required / reject>
Reusable pattern: <what can become template>
Issues: <blocking / minor>
请 worker_builder 沉淀 item template、handoff template、review checklist。
```

```bash
eduflow send worker_builder review_course "item prototype review result:
Verdict: <verdict>
Reusable pattern: <template description>
Issues: <issue list>
请 worker_builder 沉淀 item template、handoff template、review checklist。"
```

### 5. Declare verdict scope (critical for closeout authority)

Always declare `verdict_target` / scope:

| Scope | What It Covers | Closeout Authority |
|-------|---------------|-------------------|
| `full_subject` | QQL + items + manifest | Authorizes `manager-closeout` |
| `qql_items` | QQL + items only | Does NOT authorize subject closeout |
| `qql_only` | Only qa-question-level files | Does NOT authorize subject closeout |
| `items_only` | Only items layer | Does NOT authorize subject closeout |
| `manifest` | Only manifest consistency | Does NOT authorize subject closeout |

### 6. Notify chat

```bash
eduflow say review_course "复核完成：<subject> verdict=<verdict>" --to user
```

## Common Review Failure Patterns

| Issue | Fix |
|-------|-----|
| Knowledge point coverage < 90% | Worker must add missing topics |
| Difficulty mismatch (AS-level difficulty in A-Level stage) | Worker adjusts difficulty |
| Error rate > 5% | Worker corrects errors one by one |
| Duplication rate > 10% | Worker deduplicates or adapts |
| Missing required JSON fields | Worker补全 fields |

## Revision Flow (when verdict = minor_required)

1. Worker creates `accepted_revision` entry
2. Worker fixes the specific issues listed in verdict
3. Worker resubmits to review_course
4. review_course re-reviews and issues new verdict
5. Only after PASS can manager close out

## Related Skills

- `submit-to-review` — what workers run before sending to you
- `content-review-orchestration` — content/article review routing and evidence packet
- `check-closeout` — what manager runs after your verdict is PASS
