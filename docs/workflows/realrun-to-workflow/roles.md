# roles: realrun-to-workflow

## manager

- Identifies the real-run sample or gap.
- Calls the workflow.
- Decides whether the result becomes active, backlog, stale, variation, or case-note only.

## worker_builder

- Reads the real-run evidence.
- Produces workflow asset updates.
- Updates registry recommendations.
- Captures trigger examples, gates, forbidden moves, done definition, and common failure modes.

## review_course / worker_qbank / worker_course

- Provide evidence if the real run depends on their artifacts or verdicts.

## auto_ops

- Provides anomaly evidence if the workflow came from stalled, stale, or noisy runtime behavior.
- Does not own the workflow.

