---
name: igcse-subject-dispatch
description: "Manager skill: dispatch a new IGCSE subject to worker_course via igcse-subject-launch workflow. Constructs handoff message from subject name + syllabus code, mounts workflow, and sends formal dispatch."
metadata:
  type: workflow
  generated_by: worker_builder
  date: 2026-06-24
---

# IGCSE Subject Launch Dispatch

## When to Use

- A previous subject has been closed out and the next subject is ready to launch.
- `worker_course` has proposed a candidate subject with a minimum plan.
- You need to formally dispatch work to `worker_course` for a new IGCSE subject.

## Do Not Use When

- The task is item-level qbank prototype (use `igcse-item-dispatch`).
- The subject still has open revision-first or quality-gate blockers.

## Dispatch Steps

### 1. Confirm readiness

Run the pre-dispatch gate check:

```bash
eduflow task list
```

Verify no active task belongs to the same subject. If one exists, close it out first.

### 2. Mount the workflow

```bash
eduflow task dispatch worker_course "<subject name> (<syllabus code>) launch" \
  --stage curriculum \
  --owner worker_course \
  --by manager \
  --workflow igcse-subject-launch \
  --desc "subject=<subject name> code=<syllabus code> scope=candidate -> outline -> QA seed -> manifest"
```

(`--subject` and `--code` are NOT separate flags; pass them via `--desc`.)

### 3. Send the formal handoff message to worker_course

Use this template (from `docs/workflows/igcse-subject-launch/handoff-template.md`):

```
调用 workflow: igcse-subject-launch
对象: <subject name + syllabus code>
范围: candidate -> outline -> QA seed -> manifest
边界:
- 先交 review_course，不直接向 manager 收口
- 如 review_course 给 minor_required，先做 accepted_revision，再修复
- 未通过 review 前不得说成正式开线
请先低频外显接单与开工，然后提交 artifacts 给 review_course。
```

```bash
eduflow send worker_course manager "调用 workflow: igcse-subject-launch
对象: <subject name> (<code>)
范围: candidate -> outline -> QA seed -> manifest
边界:
- 先交 review_course，不直接向 manager 收口
- 如 review_course 给 minor_required，先做 accepted_revision，再修复
- 未通过 review 前不得说成正式开线
请先低频外显接单与开工，然后提交 artifacts 给 review_course。"
```

### 4. Post a chat notification

```bash
eduflow say manager "新学科已派工：<subject name> (<code>) → worker_course，workflow=igcse-subject-launch" --to user
```

### 5. Wait for worker ACK

```bash
eduflow inbox manager
```

The worker should ACK with `accepted_task` then `started_task`. If no ACK within 5 minutes, nudge.

## Post-Dispatch Checklist

- [ ] Task row exists with `workflow_id=igcse-subject-launch`
- [ ] worker_course inbox received the handoff
- [ ] worker_course ACKed (accepted_task at minimum)
- [ ] No revision-first blockers from prior subject are still active

## Related Skills

- `submit-to-review` — what worker_course runs after producing artifacts
- `check-closeout` — what manager runs before announcing launch
