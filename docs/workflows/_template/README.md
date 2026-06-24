# workflow: <workflow_id>

## Metadata

- workflow_id: `<workflow_id>`
- workflow_name: `<workflow_name>`
- status: `draft`
- owner: `worker_builder`

## When To Use

Describe the repeated real-run pattern, gap note, or manager need that justifies this workflow.

Use this workflow only when the scenario is repeatable enough for manager to call it by name.

## Trigger Examples

- `<example manager request>`
- `<example real-run gap>`

## Initiator

- manager

## Participants

- manager
- worker_builder
- `<worker_role>`
- `<review_role>`
- auto_ops

## Primary Chain

```text
manager -> <worker_role> -> <review_role> -> manager
```

## Handoff Chain

```text
manager -> <first_assignee>
<first_assignee> -> <review_or_next_assignee>
<review_or_next_assignee> -> manager
```

## In Scope

- `<what this workflow owns>`

## Out Of Scope

- Automatic workflow execution.
- Automatic task dispatch.
- Feishu sending.
- Flow-task state-machine changes.
- `<what this workflow must not own>`

## Required Inputs

- `<input one>`
- `<input two>`

## Expected Outputs

- `<output one>`
- `<output two>`

## Core Gates

- `dispatch_acceptance_gate`
- `review_handoff_gate`
- `file_evidence_gate`
- `quality_gate`
- `artifact_standard_gate`
- `runtime_reality`
- `repair_acceptance_contract`
- `stale_state_reconciliation`

## Acceptance Gates

- `<gate that proves dispatch was accepted>`
- `<gate that proves review or handoff actually started>`
- `<gate that proves artifacts are real and named correctly>`
- `<gate that proves manager can close out>`

## Forbidden Moves

- Worker roles cannot bypass required review or manager closeout.
- `manager` cannot announce formal completion before required gates pass.
- `worker_builder` cannot mark this workflow active without manager confirmation.
- `auto_ops` cannot become the workflow owner; it only watches anomalies.

## Reassurance Policy

Workers may send low-frequency reassurance for accepted / started / handed-off states.

Worker reassurance must not抢 manager formal verdict, user-facing result, problem explanation, or manager closeout.

## Builder Followup

`worker_builder` maintains this workflow after real runs by choosing one maintenance action:

- `update_trigger_examples`
- `update_forbidden_moves`
- `update_acceptance_gates`
- `mark_stale_candidate`
- `split_new_workflow_candidate`

## Done Definition

- The workflow has real-run evidence or a clear gap-note source.
- The standard files exist.
- `eduflowteam workflow validate` passes.
- `eduflowteam workflow validate --strict` passes after promotion to active.
- manager confirms active status.

## Common Failure Modes

- The workflow is actually only a one-off case note.
- The workflow is a variant of an existing active workflow.
- The workflow lacks file-level evidence gates.
- The workflow lets worker status updates抢 manager formal closeout.
- Runtime reality is inferred from status text instead of live action.

## Manager Closeout

manager is the workflow caller and formal decision owner. A workflow can enter active registry only after manager confirms the closeout and status.

## Lifecycle Notes

- Start as `draft`.
- Move to backlog if useful but not yet validated.
- Move to active only after manager closeout and strict validation.
- Mark stale when repeated real runs show the gates no longer match reality.

## Boundary

This workflow is a reusable coordination asset. It is not an automatic execution engine, scheduler, Feishu sender, or task writer.
