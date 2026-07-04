# roles: loop-engineering-execution-layer

## manager

- Creates formal tasks before loop-verified builder work.
- Runs or schedules `task loop-check`.
- Forwards Builder handoff manually when repair is needed.
- Owns final closeout.

## worker_builder

- Fixes root cause inside the declared workspace.
- Preserves tests and avoids unrelated edits.
- Reports back with the task id and asks manager to rerun loop-check.

## review_course / deterministic reviewer

- Owns official review-check evidence when the task requires formal review.
- Does not treat worker self-check as final review verdict.

## memory / workflow maintainer

- After repeated failures, captures reusable lessons or workflow updates.
- Keeps candidate promotion separate from active workflow execution.
