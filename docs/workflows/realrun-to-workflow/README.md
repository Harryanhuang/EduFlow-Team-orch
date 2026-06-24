# workflow: realrun-to-workflow

## Purpose

Use this workflow when a real EduFlow Team run has produced a stable collaboration pattern or repeated failure mode that should become a reusable workflow asset.

This is the main path for turning gap notes into operating assets.

## Primary Chain

```text
manager -> worker_builder -> manager
```

## Required Result

Manager receives a workflow asset or registry update recommendation: active, backlog, stale, variation, or case-note only.

Manager closeout is the only point where a workflow becomes active or changes
status. `worker_builder` owns the maintenance draft and may provide reassurance
that an asset update has started or been handed off, but it must not抢 manager
approval or closeout.

## Core Gates

- `dispatch_acceptance_gate`
- `file_evidence_gate`
- `quality_gate`
- `runtime_reality`
- `stale_state_reconciliation`

## Forbidden Moves

- `worker_builder` cannot mark a workflow active without manager closeout.
- A case note cannot be promoted without evidence from a real run or gap note.
- A stale workflow cannot stay active after repeated failures without a maintenance action.

## Use These Files

- `trigger.md`: manager call examples.
- `roles.md`: fixed responsibilities.
- `checklist.md`: criteria for promoting a real run into workflow.
- `handoff-template.md`: manager/builder handoff text.
