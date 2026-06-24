# roles: igcse-item-level-prototype

## manager

- Calls the workflow.
- Limits the first prototype to 1-2 topics or files.
- Owns formal decision on whether to expand.

## worker_qbank

- Acknowledges and starts visibly at low frequency.
- Produces item-level prototype artifacts.
- States gaps without making formal user-facing conclusions.
- Hands prototype to `review_course`.

## review_course

- Reviews item solvability, answer quality, explanation quality, topic mapping, and metadata.
- Gives bounded verdict on item-level readiness.

## worker_builder

- Turns the accepted prototype into reusable template assets.
- Maintains item handoff, checklist, and forbidden moves.

## auto_ops

- Watches stale handoff, low visibility, and quality gate anomalies.

