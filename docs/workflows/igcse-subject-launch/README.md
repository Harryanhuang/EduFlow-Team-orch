# workflow: igcse-subject-launch

## Purpose

Use this workflow when an IGCSE course moves from candidate status into formal launch or pre-QA gate.

It prevents the common failure where `worker_course` submits a plan directly to `manager`, or `manager` announces launch before `review_course` has passed the plan.

## Primary Chain

```text
manager -> worker_course -> review_course -> manager
```

## Required Result

The course is either formally launched, formally rejected, or returned for bounded minor repair. The decision must be based on `review_course` verdict, not worker self-report.

Manager closeout remains the only formal user-facing decision point. `worker_course`
may provide low-frequency reassurance for acceptance/start/handoff, but it must
not抢 manager verdict, launch, rejection, or closeout language.

## Core Gates

- `dispatch_acceptance_gate`
- `review_handoff_gate`
- `file_evidence_gate`
- `quality_gate`
- `artifact_standard_gate`
- `repair_acceptance_contract`
- `stale_state_reconciliation`

## Forbidden Moves

- `worker_course` cannot close the course directly to `manager`.
- `manager` cannot announce launch while `review_course` verdict is missing or minor repair is still open.
- Worker reassurance cannot be treated as review evidence or manager closeout.

## Mounted Gate Contract

- IGCSE course tasks must carry `workflow_id=igcse-subject-launch`.
- CLI accepts `--stage course` and stores it as the canonical flow stage `curriculum` for backward compatibility.
- `task submit-review` must auto-assign `review_course` when this workflow is mounted and no reviewer is set.
- `task batch-closeout` is only for batch/package PASS and must not be used as subject closeout.
- `task manager-closeout` remains subject-only and still requires subject inventory and evidence gates.

## Use These Files

- `trigger.md`: manager call examples.
- `roles.md`: each agent's fixed responsibilities.
- `checklist.md`: gate checklist before closeout.
- `handoff-template.md`: copy-ready dispatch/handoff text.
