---
name: brainstorming
description: Use before substantial course-production work to clarify intent, compare possible structures, and split broad requests into ordered production tasks.
---

# Brainstorming Ideas Into Production Plans

## Overview

Turn a broad request into a clear production route before drafting content.
For `worker_course`, this skill is a course-production preflight: it helps
clarify scope, choose a structure, and split the work into small verifiable
tasks.

For `worker_course`, this is mandatory for every accepted production or repair
task. Even when the task is clear, run the lightweight version before execution.

## Use When

- A manager task asks for a broad subject, course, batch, or curriculum output.
- The output needs topic structure, syllabus alignment, QA coverage, or staged
  production.
- There are multiple plausible production routes.
- The task should be split before execution.

Skip only the full version for tiny, already-clear fixes. The lightweight
version is still required.

## Lightweight Worker Flow

When the task is assigned or clear enough, do not block on formal approval. Do
this quickly before producing:

1. Restate the production goal, target audience, exam board/course scope, output
   format, and success criteria.
2. Identify constraints: source requirements, difficulty balance, topic count,
   review gate, file location, and non-goals.
3. Propose the smallest useful structure.
4. Split into ordered subtasks with verification checks.
5. Choose the most efficient Claude Code execution mode for the task.
6. Start the first safe subtask and report progress through normal
   `eduflow` channels.

This preflight may be short, but it must be explicit enough that a reviewer can
see what will be produced and how it will be checked.

## Claude Code Advantage Rule

After decomposition, deliberately use Claude Code's strengths instead of doing
everything as one linear main-thread draft.

Prefer Claude Code-native capabilities when they fit the task:

- **Agent team / subagents**: use for independent research, production,
  consistency checks, item generation, review preparation, or file inventory.
- **Workflow / task tracking**: use for multi-step work that needs clear stages,
  visible progress, and resumability.
- **Todo / checklist UI**: use to keep the live execution state explicit.
- **Parallel fan-out**: use when subtasks are independent and can be checked or
  produced separately.
- **Fresh review pass**: use a separate reviewer-style pass when quality,
  syllabus alignment, math correctness, or tone cleanup matters.

The preflight must decide which mode is appropriate:

```markdown
Claude Code execution choice:
- Mode: main-thread | subagents | agent team | workflow
- Why this mode fits:
- Parallel-safe subtasks:
- Sequential blockers:
- Review/check pass:
```

Use the lightest mode that preserves quality. For a small repair, main-thread +
checklist may be enough. For broad course production, prefer agent team or
subagents so research, drafting, QA checks, and cleanup do not all compete in
one context.

## Repeat-Work Skill Distillation Rule

During the preflight, check whether this task belongs to a repeated work type.
Do not judge this by vague feeling. Use a repeat-work key and durable logs.

If the same repeat-work key has been observed **5 or more times**, automatically
create a skill-distillation follow-up instead of letting the experience stay
implicit.

### Repeat-Work Key

For every accepted task, create a stable key before execution:

```text
repeat_work_key = <domain>/<exam-board-or-course>/<output-type>/<workflow-shape>
```

Examples:

```text
curriculum/igcse-0450/qa-batch/topic-to-items-qql-review
curriculum/ap-calculus-ab/review-repair/math-error-tone-cleanup
curriculum/igcse-0653/subject-expansion/outline-to-300-items-closeout
qbank/igcse/manifest-repair/items-to-unified-manifest
```

Use these fields:

- `domain`: curriculum, qbank, review, closeout, source-audit, etc.
- `exam-board-or-course`: `igcse-0450`, `ap-calculus-ab`, `caie-a-level-physics`,
  etc.
- `output-type`: topic-outline, qa-batch, review-repair, manifest, closeout,
  tone-cleanup, etc.
- `workflow-shape`: the shortest useful description of the repeated chain.

Count a task as the same kind only when the repeat-work key matches, or when a
manager explicitly says two keys should be merged.

### How To Record Each Observation

After the preflight, log the key before or during the first progress report:

```bash
eduflow log worker_course repeat_work_observed "<repeat_work_key> | <task-id-or-source> | <one-line task summary>"
```

If the task produced a durable lesson, also remember it:

```bash
eduflow remember worker_course learning "repeat_work::<repeat_work_key>::<short reusable lesson>"
```

This gives future runs something countable. The log is the task counter; memory
is the distilled lesson.

### How To Detect The Count

During brainstorming preflight:

1. Generate `repeat_work_key`.
2. Check recent logs and memory for that key:

```bash
eduflow workspace worker_course
eduflow recall worker_course
```

3. If exact counting is needed, inspect the local facts log for
   `repeat_work_observed` rows containing the key.
4. Use these buckets:
   - `0-2`: no distillation, just execute.
   - `3-4`: mention "pattern emerging" to manager if useful.
   - `>=5`: create `Skill distillation candidate`.

Do not trigger on "feels similar" alone. If evidence is not countable, treat it
as `3-4 / pattern emerging`, not as `>=5`.

### What Counts As Similar

- same subject family or exam board pattern
- same output type: topic outline, QA item batch, review repair, manifest,
  closeout, tone cleanup, source audit, etc.
- same file surfaces and handoff chain
- same repeated pitfalls or review failures
- same verification commands or acceptance checks

When the threshold is met, do all of the following:

1. Continue the current production task; do not block delivery.
2. Add a short `Skill distillation candidate` section to the manager-facing
   breakdown.
3. Capture the reusable pattern:
   - trigger
   - production move
   - required inputs
   - output format
   - acceptance checks
   - known pitfalls
   - when not to use it
4. Recommend whether to create a new skill or update an existing skill.
5. Send the candidate to manager for review, or use the project `dot-skill`
   workflow if manager explicitly asks to generate the skill file.

Suggested candidate shape:

```markdown
Skill distillation candidate:
- Repeat work key:
- Repeated work type:
- Evidence this has happened >=5 times:
  - log/memory reference 1:
  - log/memory reference 2:
  - log/memory reference 3:
  - log/memory reference 4:
  - log/memory reference 5:
- Candidate skill name:
- Trigger:
- Core workflow:
- Acceptance checks:
- Known pitfalls:
- Suggested owner/reviewer:
```

Do not silently rewrite canonical skills during normal production. A worker may
draft the candidate, but manager/review owner should approve the durable skill
before it becomes a standing rule.

## Full Brainstorming Flow

Use the full flow when the request is unclear or has a real tradeoff.

### 1. Explore Context

Read the relevant project files, content folder, prior manifests, review notes,
and existing skills before deciding the route.

For course work, prefer these evidence surfaces:

- Existing `content/<subject>/topic-outline.md`
- Existing `content/<subject>/manifest.md`
- Existing `items/` and `qa-question-level/` files
- Relevant `.claude/skills/*.md` workflow notes
- Manager or review_course task messages

### 2. Ask One Focused Question If Needed

Ask only when the missing answer changes the production route. Keep it to one
question at a time.

Good questions:

- Which exam board and syllabus code is in scope?
- Is the target output topic outline, QA items, review repair, or final closeout?
- Should this optimize for breadth, depth, or review readiness?

If the manager task already answers this, proceed.

### 3. Propose 2-3 Routes

When there is a meaningful choice, present options with tradeoffs and a
recommendation.

Example:

- Route A: topic-outline first, then QA expansion. Best when structure is shaky.
- Route B: batch QA production from an accepted outline. Best when structure is
  already stable.
- Route C: repair-first from review verdict. Best when review_course has already
  identified blockers.

### 4. Convert Into Ordered Tasks

Each task should include:

- Goal
- Inputs to read
- Output file or handoff target
- Acceptance check
- Review or reporting step

Prefer batch sizes that protect context quality. For `worker_course`, keep
course-production batches small enough to review and recover.

## Output Shape

For manager-facing task breakdowns, use this shape:

```markdown
生产目标：
- ...

推荐路线：
- ...

任务拆解：
1. ...
2. ...
3. ...

验收点：
- ...

当前先做：
- ...
```

For user-visible group updates, keep it short and operational:

```text
阶段进度：已完成任务拆解，当前先处理 <第一步>，预计交给 review_course 的产物是 <产物>。
```

## Priority Rules

- Existing `worker_course` identity, reporting, and handoff rules are higher
  priority than this generic workflow.
- Do not use this skill to delay a clear manager task; use the lightweight
  version and continue.
- Do not turn every task into a long design document.
- The goal is better production, not more ceremony.
- Claude Code capability selection is part of the decomposition. Do not default
  to single-thread execution when the task naturally benefits from Claude Code
  agent team, workflow, or subagent features.
- If the same task pattern has appeared 5+ times, create a skill-distillation
  candidate while continuing the current task. Repeated work should become a
  reusable skill instead of staying as tacit memory.
