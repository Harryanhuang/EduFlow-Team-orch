# checklist: loop-engineering-execution-layer

## Before Loop Check

- [ ] Formal flow task id exists.
- [ ] Builder work used `task dispatch` before `send`.
- [ ] Workspace metadata is present, or unscoped risk is explicitly allowed.
- [ ] Acceptance spec is deterministic.

## Repair Gate

- [ ] Loop evidence ref exists.
- [ ] Builder handoff includes task id and loop id.
- [ ] Builder handoff names failing command and failure summary.
- [ ] Red lines say not to weaken, delete, or skip tests.
- [ ] Rerun command is present.

## Closeout Boundary

- [ ] Loop pass is treated as supporting evidence only.
- [ ] Review verdict remains separate from self-check.
- [ ] Manager closeout remains separate from review-check.

## Block Promotion If

- [ ] Candidate implies workflow auto-execution.
- [ ] Candidate lets loop pass become formal delivery.
- [ ] Candidate lacks memory/workflow crystallization guidance after repeated failures.
