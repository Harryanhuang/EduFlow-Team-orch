# workflow: example-draft-workflow

## Metadata

- workflow_id: `example-draft-workflow`
- workflow_name: `Example Draft Workflow`
- status: `draft`
- owner: `worker_builder`

## When To Use

Use this candidate as a shape example for a draft workflow produced from real-run evidence or a gap note.

## Trigger Examples

- manager asks worker_builder to turn a repeated gap into a reusable workflow.

## Initiator

- manager

## Participants

- manager
- worker_builder
- worker_course
- review_course
- auto_ops

## Primary Chain

```text
manager -> worker_builder -> manager
```

## Handoff Chain

```text
manager -> worker_builder -> manager
```

## In Scope

- Drafting a candidate workflow from real-run evidence.
- Keeping candidate status separate from active workflow status.

## Out Of Scope

- Automatic workflow execution.
- Automatic task dispatch.
- Feishu sending.
- Flow-task state-machine changes.

## Required Inputs

- Real-run evidence or gap note.
- Candidate workflow scope.

## Expected Outputs

- Draft candidate workflow files.
- Builder recommendation for promotion, backlog, stale, or case-note-only status.

## Core Gates

- `dispatch_acceptance_gate`
- `review_handoff_gate`
- `file_evidence_gate`
- `artifact_standard_gate`
- `runtime_reality`

## Acceptance Gates

- Candidate source evidence is explicit.
- manager closeout point is explicit.
- Standard files exist.
- Candidate does not duplicate an active workflow.

## Forbidden Moves

- Candidate cannot be treated as active workflow.
- Candidate cannot be used for `task dispatch --workflow`.
- `worker_builder` cannot promote it without manager closeout.
- Worker reassurance cannot抢 manager formal decision.

## Reassurance Policy

Workers may provide low-frequency accepted / started / handed-off reassurance. Reassurance must not抢 manager final result, user-facing decision, or manager closeout.

## Builder Followup

`worker_builder` maintains this candidate and chooses one action:

- `update_trigger_examples`
- `update_forbidden_moves`
- `update_acceptance_gates`
- `mark_stale_candidate`
- `split_new_workflow_candidate`

## Done Definition

- Candidate files are complete.
- `eduflowteam workflow candidate-validate` passes.
- `eduflowteam workflow candidate-validate --strict` passes.
- manager decides whether to promote, backlog, reject, or keep as case note.

## Common Failure Modes

- Candidate duplicates an active workflow.
- Candidate lacks manager closeout.
- Candidate lacks builder followup.
- Candidate lets worker status updates抢 formal manager language.

## Manager Closeout

manager is the only role that can approve promotion from candidate to active.

## Lifecycle Notes

Start as `draft`. Move to `promotion_ready` only after candidate strict validation passes and manager agrees it is callable.
