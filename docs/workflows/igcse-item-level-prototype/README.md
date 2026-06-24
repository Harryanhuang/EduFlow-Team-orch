# workflow: igcse-item-level-prototype

## Purpose

Use this workflow when topic-level QA exists, but EduFlow Team must verify whether it can become item-level question-bank assets.

The first run should stay small: 1-2 topics or files only.

## Primary Chain

```text
manager -> worker_qbank -> review_course -> worker_builder -> manager
```

## Required Result

Manager receives a formal judgment on whether the item-level prototype is ready to expand, needs repair, or should stop.

Manager closeout is required before prototype expansion. `worker_qbank` may send
brief reassurance that the prototype work was accepted or started, but it must
not抢 manager conclusion, review verdict, or expansion decision.

## Core Gates

- `dispatch_acceptance_gate`
- `review_handoff_gate`
- `file_evidence_gate`
- `quality_gate`
- `artifact_standard_gate`
- `runtime_reality`
- `stale_state_reconciliation`

## Forbidden Moves

- `worker_qbank` cannot turn a prototype into full production without manager closeout.
- `review_course` cannot pass item-level work without file-level evidence.
- `worker_builder` cannot publish a template as active before manager confirms the prototype verdict.

## Use These Files

- `trigger.md`: manager call examples.
- `roles.md`: fixed responsibilities.
- `checklist.md`: item prototype readiness checks.
- `handoff-template.md`: qbank/review/builder handoff text.
