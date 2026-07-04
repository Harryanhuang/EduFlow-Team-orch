# Loop Engineering Observation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans only if this plan is later converted into implementation work. For the next few days, this is an operations observation plan, not a coding plan.

**Goal:** Run the newly merged loop engineering layer for a few real tasks before deciding the next implementation phase.

**Architecture:** Keep `flow task` as the source of truth. Use the existing `task loop-check`, `task loop-status`, and `task loop-list` surfaces to collect evidence. Do not add automation until the observed bottleneck is clear.

**Tech Stack:** EduFlow CLI, task store, loop run archive, workflow candidate docs, pytest/compileall checker specs.

---

## Decision

Do not build the next phase immediately.

Run the current loop layer for 3-5 working days, then decide whether the next change should be:

1. `task loop-report`
2. business-specific loop specs
3. semi-automatic Builder repair handoff
4. background pid/status/cancel support

## Operating Rules

- Use loop only on tasks that already have a real `task_id`.
- Prefer `task loop-check <task_id> --background` for manager-run checks.
- Treat `loop passed` as checker evidence only, not delivery, review approval, or manager closeout.
- If `repair_needed`, forward the generated Builder handoff manually.
- Do not auto-dispatch repair work yet.
- Do not promote the workflow candidate during this observation window.

## Daily Routine

### Step 1: Pick observed tasks

Choose 2-5 active tasks where loop evidence is useful:

- builder/code repair tasks;
- workflow candidate edits;
- tasks with prior repeated repair;
- tasks where manager needs confidence before closeout.

Skip routine chat/status tasks.

### Step 2: Run loop check

Run:

```bash
./scripts/eduflowteam task loop-check <task_id> --background
```

Expected:

- loop run is created or appended;
- task row receives loop summary;
- background log is attached under `loop_runs/<loop_id>/background.log`.

### Step 3: Inspect status

Run:

```bash
./scripts/eduflowteam task loop-status <task_id>
```

Record:

- `agent_loop.status`
- `agent_loop.stop_reason`
- `agent_loop.recommended_action`
- `team_loop.phase`
- `team_loop.next_owner`
- `team_loop.loop_health`
- evidence ref

### Step 4: Handle repair manually

If status is `repair_needed`, `stopped`, or `failed`:

1. Copy the generated Builder handoff.
2. Send it to the responsible builder.
3. After the builder reports a fix, rerun:

```bash
./scripts/eduflowteam task loop-check <task_id> --background
```

### Step 5: Daily snapshot

At the end of each day, run:

```bash
./scripts/eduflowteam task loop-list
```

Record a short note:

```markdown
## YYYY-MM-DD Loop Observation

- Tasks checked:
- Passed:
- Repair needed:
- Repeated failures:
- Most confusing status output:
- Most useful handoff:
- Missing command/report:
- Decision pressure:
```

## What To Watch

### Signal A: Manager visibility

Question:

Can manager tell which tasks are blocked, repair-needed, review-ready, or closeout-ready without opening raw files?

If no, build `task loop-report` first.

### Signal B: Checker fit

Question:

Does `code-repair` cover the tasks we actually care about?

If no, add the smallest deterministic business specs:

- `workflow-candidate-check`
- `syllabus-review-check`
- `qbank-manifest-check`

### Signal C: Handoff friction

Question:

Is copying the Builder handoff still a bottleneck after 3-5 days?

If yes, add a semi-automatic handoff command. Do not auto-close tasks.

### Signal D: Background observability

Question:

Does manager need pid/status/cancel for background checks?

If yes, extend background run metadata. Skip this if background logs are enough.

### Signal E: Authority confusion

Question:

Did anyone treat loop pass as delivery, review approval, or manager closeout?

If yes, fix wording and identity prompts before adding automation.

## Exit Criteria

After 3-5 working days, continue to implementation only if at least one of these is true:

- manager repeatedly asks "which loop tasks need attention?";
- more than 30% of checked tasks need non-code deterministic specs;
- Builder handoff copying happens often enough to slow operations;
- background checks are hard to monitor or cancel;
- loop wording causes authority confusion.

If none are true, keep using the current layer and do not build the next phase.

## Recommended Next Implementation Order

1. `task loop-report`
2. one or two business-specific loop specs
3. semi-automatic Builder handoff command
4. background pid/status/cancel

## Non-Goals

- No auto-dispatch.
- No automatic manager closeout.
- No second workflow engine.
- No dashboard UI.
- No new dependency.
- No LLM-based subjective checker until deterministic checks prove insufficient.

## Final Review Prompt

After the observation window, answer:

1. Which command did manager wish existed more than once?
2. Which task type failed because `code-repair` was the wrong checker?
3. Which loop status caused the most confusion?
4. Which manual step was repeated enough to automate?
5. What should still not be automated?
