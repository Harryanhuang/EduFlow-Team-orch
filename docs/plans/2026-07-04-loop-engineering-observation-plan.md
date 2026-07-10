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

## Long-Range Direction

The long-range goal is to upgrade EduFlow from a task loop system into an
experience loop system.

The current loop already answers:

- did the deterministic checker run?
- did it pass, fail, need repair, or stop?
- where is the evidence?
- who owns the next move?

The next layer should answer:

- what reusable failure pattern did this run expose?
- should the lesson update a loop spec, handoff, workflow rule, memory candidate, or nothing?
- did the update reduce future repair cycles without weakening review or closeout authority?

### Stage 0: Preserve Authority Boundaries

Keep the current boundaries while the loop layer matures:

- `loop passed` remains checker evidence only, not delivery, REVIEW, or CLOSEOUT.
- `worker_review` owns formal REVIEW verdicts for company-wide review/check work.
- `manager` remains the only CLOSEOUT owner.
- workflow documents stay protocol references, not an automatic execution engine.

### Stage 1: Add Experience Packet Read Model

Before adding more automation, add a read-only experience compiler over existing
loop evidence:

```text
loop cycle evidence
-> failure pattern
-> likely root cause
-> attempted repair
-> reusable lesson
-> suggested update surface
```

Use this small update-surface vocabulary:

```text
loop_spec
handoff
workflow_rule
memory_candidate
no_reuse
```

This should read from existing `loop_runs/<loop_id>/meta.json`, checker output,
failed commands, fingerprints, preflight data, and task state. It must not write
memory, skills, workflow docs, or task status.

### Stage 2: Strengthen Evolution Packet

Extend `task evolution-packet` so `loop_cycle_count >= 2` produces useful
repair-cycle candidates, not only a thin "cycle count increased" note.

For repeated loop failures, the packet should include:

- recent failed commands;
- latest failure fingerprint;
- stop reason;
- evidence ref;
- suggested update surface;
- whether the failure looks reusable or case-specific.

Keep it read-only. Candidate review still happens outside the loop.

### Stage 3: Human-Gated Experience Promotion

Do not auto-promote experience into memory, skills, or workflow rules. Use this
gate:

```text
candidate -> manager / reviewer audit -> promote / reject / archive
```

Promotion targets:

- `memory_candidate`: cross-task reminder or recurring operational lesson;
- `workflow_rule`: protocol gate, forbidden move, or review boundary;
- `loop_spec`: deterministic checker coverage gap;
- `handoff`: clearer repair packet wording or required fields;
- `no_reuse`: preserve as case evidence only.

### Stage 4: Add Business Loop Specs Only From Observed Need

Keep `code-repair` as the default until observation shows a repeated business
gap. Add the smallest deterministic spec that closes the observed gap:

- `workflow-candidate-check`
- `syllabus-coverage-check`
- `qbank-manifest-check`
- `review-handoff-check`
- `closeout-evidence-check`

Do not add LLM-based subjective quality checks until deterministic checks prove
insufficient and reviewer authority remains explicit.

### Stage 5: Manager Loop Report

Build `task loop-report` only when manager repeatedly needs cross-task visibility.
It should summarize:

- repair-needed tasks;
- stopped tasks grouped by stop reason;
- same-failure repeated cases;
- closeout-ready tasks;
- pending evolution candidates;
- tasks needing business-specific loop specs.

### Stage 6: Semi-Automatic Handoff, Not Auto-Repair

If handoff copying becomes a real bottleneck, add:

```bash
./scripts/eduflowteam task loop-handoff <task_id>
```

It may generate or send the repair handoff. It must not fix code, auto-dispatch
repair work, approve REVIEW, or close the task.

### Stage 7: Experience Quality Review

Before any stronger automation, review whether promoted experience actually
helps:

- Did later repair cycles decrease?
- Did old tasks regress?
- Did manager / reviewer authority become less clear?
- Was the candidate reused without benefit?
- Should the candidate be pruned, edited, or archived?

## Flow Memory Improvement Track

The memory layer should remain a governed experience system, not an autonomous
rule-writing system. Loop evidence may propose lessons, but only reviewed
memories, constraints, workflow docs, or loop specs should affect future
execution.

### Current Memory Findings

As of 2026-07-07 local inspection:

- `memory packet --agent manager` is empty without a `task_id`; manager does not
  see a standing governance snapshot.
- `memory packet --agent manager --task T-2` and similar task-scoped packets do
  work, because task capsules and task constraints are present.
- active constraints are mostly task-scoped repair gates, with repeated stale
  `task:T-2` entries; query dedup hides duplicates at injection time, but the
  database still carries noise.
- the candidate queue contains real signals (`review_reject`,
  `task_failure_pattern`, `task_failure`) mixed with placeholder/manual test
  candidates such as `proposed candidate`, `test`, and `valid`.
- `eduflow_memory.db` is the code path used by `memory_db_file()`, while
  `flow_memory.db` also exists locally with near-empty data. The MCP server
  documents `EDUFLOW_MEMORY_DB`, but the override is not actually wired through
  the runtime path layer.
- current Evolution Packet support detects `loop_cycle_count >= 2`, but the
  candidate content is still too thin to decide whether the lesson belongs in a
  loop spec, handoff, workflow rule, memory candidate, or no-reuse archive.

### Memory Principle

Use this contract:

```text
runtime trace -> experience packet -> memory candidate -> human review -> confirmed memory / rejected candidate
```

Never use this contract:

```text
runtime trace -> automatic permanent rule
```

Confirmed memory should be small, evidence-backed, scoped, and reversible. If a
lesson is not reusable across future tasks, keep it as task evidence rather than
promoting it.

### Optimized Sequence

Do not build "smarter memory" until the memory substrate is trustworthy. Execute
the packages in this gate order:

```text
Gate A: one memory store, visible diagnostics
Gate B: candidate queue hygiene
Gate C: task constraint lifecycle cleanup
Gate D: manager governance snapshot
Gate E: stronger read-only evolution packet
Gate F: loop_repair_cycle candidate source
Gate G: weekly memory quality review
```

The numbered package labels below are work areas, not execution order. The gate
list above is the execution order.

The important change is that Loop learning moves behind hygiene. If the review
queue already contains placeholder candidates and stale task gates, adding
`loop_repair_cycle` first would amplify noise instead of creating experience.

### Hold Conditions

Pause Loop-to-memory expansion when any of these are true:

- CLI and MCP do not point to the same memory DB.
- `memory packet --agent manager` has no governance signal and no task context.
- proposed candidates include obvious placeholders.
- active task constraints outlive the task state that created them.
- no one owns a recurring promote/reject rhythm.

When a hold condition is active, only fix diagnostics, hygiene, or lifecycle.
Do not add new candidate sources.

### Memory Package 1: Align Memory Stores And Diagnostics

Add a cheap diagnostic surface before changing learning behavior:

```bash
./scripts/eduflowteam memory doctor
```

It should print:

- active DB path;
- whether `EDUFLOW_MEMORY_DB` is honored;
- row counts for constraints, items, candidates, capsules;
- top proposed candidate source types;
- active stale task constraints;
- whether `flow_memory.db` and `eduflow_memory.db` disagree.

Implementation notes:

- make `memory_db_file()` honor `EDUFLOW_MEMORY_DB`, or remove the documented
  override from the MCP server and standardize on `eduflow_memory.db`;
- keep the default DB unchanged unless an explicit override is set;
- add a regression test proving CLI and MCP resolve the same DB path.

### Memory Package 2: Clean Candidate Admission

Tighten the admission gate so placeholder text does not enter the review queue.

Reject or mark low-value before persistence when content is:

- `proposed candidate`;
- `test`;
- `valid`;
- one-character or near-empty notes;
- manual candidates without evidence and without a meaningful reason.

Do not delete existing rows automatically. Add a review command instead:

```bash
./scripts/eduflowteam memory candidates hygiene --dry-run
./scripts/eduflowteam memory candidates hygiene --reject-placeholders --yes
```

Expected effect: manager/Hermes review effort focuses on real operational
lessons instead of test artifacts.

### Memory Package 3: Make Loop Experience A First-Class Candidate Source

Add a new event source for loop experience, separate from generic task failure:

```text
source_type = loop_repair_cycle
source_ref = loop:<loop_id>
```

The bridge should be explicit and idempotent:

```text
task loop-check
-> task loop evidence
-> read loop_runs/<loop_id>/meta.json
-> if cycle_count >= 2 or stop_reason is structural
-> propose loop_repair_cycle candidate
```

Candidate content should include:

- task id and workflow id;
- loop id and evidence ref;
- cycle count;
- stop reason;
- latest failure fingerprint;
- recent failed commands;
- suggested update surface: `loop_spec`, `handoff`, `workflow_rule`,
  `memory_candidate`, or `no_reuse`;
- why it is reusable or why it should stay case-specific.

Mapping guidance:

- workspace/preflight blocked repeatedly -> `handoff` or `workflow_rule`;
- same failure fingerprint repeats -> `loop_spec` or `handoff`;
- checker unavailable -> `loop_spec`;
- review boundary confusion -> `workflow_rule`;
- one-off local failure -> `no_reuse`.

### Memory Package 4: Strengthen Evolution Packet Before Writing Candidates

Keep `task evolution-packet` read-only, but make the packet strong enough for
manager review.

For `repair_cycle_ge2`, read the loop run meta file instead of relying only on
the compact task fields. Include failed commands and fingerprints from the last
one or two cycles. If the loop run file is missing, keep the existing thin
candidate but lower confidence to `low`.

Acceptance checks:

- no trigger still returns `{"candidates": []}`;
- missing loop run file does not crash;
- `loop_cycle_count >= 2` with loop meta returns a candidate with
  `suggested_update_surface`;
- no memory rows are written by `task evolution-packet`.

### Memory Package 5: Improve Packet Scoping Without Flooding Workers

Keep proposed candidates out of worker packets. Workers should see only active
constraints, the current task capsule, and confirmed memories.

For manager only, add a compact governance snapshot either to `memory daily` or
to a manager-specific packet section:

```text
Pending memory review:
- high-impact candidates
- loop_repair_cycle candidates
- stale candidates expiring soon
```

Do not inject the full candidate body as instruction. Candidate text is
unreviewed evidence, not a rule.

Also expand confirmed memory recall carefully:

- include pinned `team` memories for every agent;
- include `agent:<name>` memories for that agent;
- include workflow memories only when a task capsule provides `workflow_id`;
- do not include arbitrary team notes unless pinned or high-importance
  role/workflow rules.

### Memory Package 6: Constraint Lifecycle Hygiene

Task-scoped constraints should expire when the task leaves the state that made
the constraint true.

Add or tighten:

- uniqueness for active `scope + constraint_type + content`;
- query-time `valid_until` filtering;
- cleanup for duplicate active task constraints;
- deactivation when the related task is no longer blocked by the same revision,
  loop, or closeout gate.

This keeps Memory Packet useful instead of letting old task gates accumulate.

### Memory Package 7: Memory Quality Review

Once real loop candidates exist for several days, review memory quality weekly:

- promoted vs rejected ratio;
- how many promoted memories were actually recalled later;
- whether a promoted memory reduced repeated repair cycles;
- stale high-impact memories older than 30 days;
- conflicts between active constraints and confirmed memories.

Good memory is not "more memory"; good memory is lower future coordination cost
without weakening REVIEW or CLOSEOUT authority.

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
