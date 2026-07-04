# workflow: loop-engineering-execution-layer

## Metadata

- workflow_id: `loop-engineering-execution-layer`
- workflow_name: `Loop Engineering Execution Layer`
- status: `draft`
- owner: `worker_builder`

## When To Use

Use this candidate when a builder or workflow-backed task needs explicit loop evidence: deterministic check, repair handoff, review verdict, manager closeout, and later memory/workflow crystallization.

## Primary Chain

```text
manager -> worker_builder -> manager
manager -> worker_course -> review_course -> manager
```

## In Scope

- Agent Loop: `task loop-check <task_id> --background` records deterministic self-check or review-check evidence.
- Team Loop: `task loop-status <task_id>` shows workflow phase, next owner, repair cycles, and loop health.
- Builder code-repair handoff when loop status is `repair_needed`, `stopped`, or `failed`.
- Repeated failure review after closeout to decide whether memory or workflow docs need updating.

## Out Of Scope

- Automatic workflow execution.
- Automatic Feishu send to workers.
- Treating loop pass as delivery, review approval, or manager closeout.
- Subjective content quality checks without reviewer authority.

## Required Inputs

- A formal `flow task` id.
- Workspace metadata for builder work.
- A deterministic loop spec, initially `code-repair`.

## Expected Outputs

- Loop evidence under `$EDUFLOW_STATE_DIR/loop_runs/<loop_id>/`.
- Task row loop summary fields.
- Optional Builder handoff packet.
- Team loop read model from task events and review verdicts.

## Acceptance Gates

- `loop passed` remains supporting evidence only.
- `review_course` or deterministic reviewer authority remains the formal review gate.
- `manager` remains the only final closeout owner.
- `workflow_id` stays a protocol reference, not an execution engine.

## Core Gates

- `dispatch_acceptance_gate`
- `review_handoff_gate`
- `file_evidence_gate`
- `artifact_standard_gate`
- `repair_acceptance_contract`
- `runtime_reality`

## Forbidden Moves

- Do not use loop pass as `delivered`, `approved`, or `closeout_completed`.
- Do not weaken, delete, or skip tests to make a loop pass.
- Do not edit unrelated files during builder repair.
- Do not promote this candidate without manager closeout.
- Candidate cannot be treated as active workflow.
- Candidate cannot be used for `task dispatch --workflow`.
- Worker reassurance cannot be treated as review evidence or manager closeout.

## Reassurance Policy

Workers may provide low-frequency accepted / started / handed-off reassurance. Reassurance must not抢 manager final result, user-facing decision, review verdict, or manager closeout.

## Builder Followup

After repeated same-failure or repair cycles, `worker_builder` should propose one of:

- update loop spec or handoff wording;
- update active workflow forbidden moves;
- add memory candidate for recurring failure;
- keep as case note if not reusable.

## Done Definition

- The operator can run `task loop-status <task_id>` and see both `agent_loop` and `team_loop`.
- Repair handoff contains task id, loop id, failing command, evidence ref, red lines, and rerun command.
- Evidence explain and memory capsules mention loop evidence without granting formal PASS.
