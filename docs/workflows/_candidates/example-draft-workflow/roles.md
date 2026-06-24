# roles: example-draft-workflow

## manager

- Requests candidate drafting.
- Decides whether the candidate can become active.
- Owns formal closeout and promotion decision.

## worker_builder

- Maintains candidate files.
- Checks the candidate against `_template`.
- Recommends promotion, backlog, stale, split, reject, or case-note-only status.

## worker_course / review_course / worker_qbank

- Provide scoped evidence only when manager asks.
- Do not treat the candidate as active workflow.

## auto_ops

- Watches candidate-related anomalies.
- Does not own candidate promotion.
