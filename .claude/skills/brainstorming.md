---
name: brainstorming
description: Course-production preflight for worker_course. Use before broad curriculum, topic, syllabus, QA, or research production to clarify scope, compare structures, and split work into ordered subtasks.
metadata:
  type: workflow
  source: adapted-from-codex-brainstorming
---

# Brainstorming for Course Production

`worker_course` must use this after every accepted production or repair task and
before execution. Clear tasks still require the lightweight version; unclear
tasks use the full version.

## Lightweight Default

If manager/review_course already gave a clear task, do not stop for approval.
Instead, do this preflight quickly before producing:

1. Restate goal, scope, output format, and success criteria.
2. Identify constraints: exam board, syllabus code, difficulty balance, target
   files, review gate, and non-goals.
3. Pick the smallest useful production route.
4. Split into ordered subtasks with acceptance checks.
5. Choose the best Claude Code execution mode.
6. Start the first safe subtask and report progress through `claudeteam`.

The output can be brief, but must be visible in the worker's reasoning/report:
goal, constraints, subtasks, and acceptance checks.

## Claude Code Advantage Rule

After task decomposition, explicitly decide how to use Claude Code efficiently:

- Use agent team / subagents for independent research, drafting, verification,
  file inventory, tone cleanup, or review-prep lanes.
- Use workflow/task tracking for multi-step work that needs stage control.
- Use Todo/checklists for live execution state.
- Use a fresh review-style pass when correctness, syllabus alignment, or tone
  risk matters.

Include this in the breakdown:

```text
Claude Code execution choice:
- Mode: main-thread | subagents | agent team | workflow
- Parallel-safe subtasks:
- Sequential blockers:
- Review/check pass:
```

Do not default to one long main-thread execution when the task naturally
benefits from Claude Code's agent team, workflow, or subagent capabilities.

## Repeat-Work Skill Distillation Rule

During every preflight, check whether this is the same type of work the team has
already done 5 or more times. Do not judge this by vague feeling; use a stable
repeat-work key and logs.

For every accepted task, create:

```text
repeat_work_key = <domain>/<exam-board-or-course>/<output-type>/<workflow-shape>
```

Examples:

```text
curriculum/igcse-0450/qa-batch/topic-to-items-qql-review
curriculum/ap-calculus-ab/review-repair/math-error-tone-cleanup
qbank/igcse/manifest-repair/items-to-unified-manifest
```

Record it with:

```bash
claudeteam log worker_course repeat_work_observed "<repeat_work_key> | <task-id-or-source> | <one-line task summary>"
```

If there is a reusable lesson:

```bash
claudeteam remember worker_course learning "repeat_work::<repeat_work_key>::<short reusable lesson>"
```

To detect the count, check `claudeteam workspace worker_course`,
`claudeteam recall worker_course`, or local facts logs for matching
`repeat_work_observed` entries.

Use buckets:

- `0-2`: execute normally.
- `3-4`: pattern emerging; mention to manager if useful.
- `>=5`: create a `Skill distillation candidate`.

Treat work as repeated when the repeat-work key matches. If it merely feels
similar but is not countable, do not mark it as `>=5`.

If repeated >=5 times:

1. Continue the current task; do not block delivery.
2. Add a `Skill distillation candidate` section to the manager-facing breakdown.
3. Capture trigger, workflow, inputs, output format, acceptance checks, known
   pitfalls, and when not to use it.
4. Recommend creating a new skill or updating an existing one.
5. Send the candidate to manager for review, or use `dot-skill` only when
   manager explicitly asks to generate the skill file.

Do not silently rewrite standing skills during normal production. Draft the
candidate first, then let manager/review owner approve durable rules.

## Full Version

Use the full version only when there is real ambiguity or a branching choice:

- Read the relevant content files and prior workflow notes.
- Ask one focused question if missing information changes the route.
- Propose 2-3 production routes with tradeoffs.
- Recommend one route.
- Convert it into ordered, verifiable tasks.

## Reporting Shape

Manager-facing:

```text
生产目标：...
repeat_work_key：...
推荐路线：...
任务拆解：1... 2... 3...
验收点：...
Skill distillation candidate：如同类任务已 >=5 次，写触发条件 / 核心流程 / 验收点 / 坑点 / 建议 skill 名
当前先做：...
```

User-facing status stays short:

```text
阶段进度：已完成任务拆解，当前先处理 <第一步>，预计交给 review_course 的产物是 <产物>。
```

Existing `worker_course` identity, ACK, progress, and handoff rules always stay
higher priority.
