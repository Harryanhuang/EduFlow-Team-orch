---
name: submit-to-review
description: "Worker skill: format and send a review handoff to review_course from production artifacts. Covers the worker_course->review_course and worker_qbank->review_course handoff templates."
metadata:
  type: workflow
  generated_by: worker_builder
  date: 2026-06-24
---

# Submit Artifacts to review_course

## When to Use

After producing or repairing course/QA artifacts, hand them to `review_course` for formal review. Never send directly to manager — review_course is the mandatory intermediary.

## worker_course -> review_course (Subject Launch)

Use this template (from `docs/workflows/igcse-subject-launch/handoff-template.md`):

```
请按 igcse-subject-launch 复核 <subject + code>。
范围:
- <files / outline / seed / manifest>
需要 verdict:
- pass / minor_required / reject / conditional_pass
如为 pass，请给 file-level evidence packet。
如为 minor_required，请列出 issue id、文件、必须修复项。
```

```bash
eduflow send review_course worker_course "请按 igcse-subject-launch 复核 <subject> (<code>)。
范围:
- <list of artifact files/paths>
需要 verdict:
- pass / minor_required / reject / conditional_pass
如为 pass，请给 file-level evidence packet。
如为 minor_required，请列出 issue id、文件、必须修复项。"
```

## worker_qbank -> review_course (Item Prototype)

Use this template (from `docs/workflows/igcse-item-level-prototype/handoff-template.md`):

```
请按 igcse-item-level-prototype 复核 item prototype。
范围: <item files / topic ids>
请检查:
- solvability
- answer correctness
- explanation usefulness
- topic mapping
- difficulty/type metadata
请给 bounded verdict，不做完整题库结论。
```

```bash
eduflow send review_course worker_qbank "请按 igcse-item-level-prototype 复核 item prototype。
范围: <item files / topic ids>
请检查:
- solvability
- answer correctness
- explanation usefulness
- topic mapping
- difficulty/type metadata
请给 bounded verdict，不做完整题库结论。"
```

## After Sending

1. Update your status to reflect the handoff:
   ```bash
   eduflow status <your-name> 待复核 "已提交 review_course，等待 verdict"
   ```

2. Notify the chat:
   ```bash
   eduflow say <your-name> "已提交 review_course 复核：<subject/scope>" --to user
   ```

3. Monitor your inbox for the review verdict. If review_course sends `minor_required`, follow the revision flow.

## Common Review Outcomes

| Verdict | Worker Next Step |
|---------|-----------------|
| `pass` / `approved` | Proceed to closeout or next batch |
| `minor_required` | Fix issues, create `accepted_revision`, resubmit |
| `reject` | Major rework needed; escalate to manager if unclear |
| `conditional_pass` | Fix specific items, then re-review scope |

## Related Skills

- `review-verdict` — what review_course runs when issuing a verdict
- `check-closeout` — what manager runs after verdict is PASS
