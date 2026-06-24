# roles: igcse-subject-launch

## manager

- Calls the workflow.
- Sends formal dispatch.
- Waits for `review_course` verdict before launch or closeout.
- Owns final result and user-facing decision language.
- Does not produce or repair course content directly.
- Does not run Python/file verification as the verdict source.
- Does not treat group-chat claims as task truth; dispatch, closeout, and decisions must be backed by task / inbox / workflow evidence.

## worker_course

- Acknowledges acceptance and start.
- Produces and repairs candidate plan, outline, QA seed, content files, and manifest.
- Hands artifacts to `review_course`.
- Performs minor repair only after review issues are explicit.
- Does not directly close with manager.

## review_course

- Acknowledges review start.
- Reviews exact scope assigned by manager.
- Gives the latest authoritative verdict with file-level evidence when quality gate is active.
- Sends verdict back for manager closeout.

## auto_ops

- Watches for stale handoff, unread backlog, quality gate, or runtime anomaly.
- Watches only; does not own the workflow or decide course closeout.

## worker_builder

- Fixes workflow assets, execution paths, naming rules, and tool/runtime issues.
- Does not execute course/QA production work.

## worker_qbank

- Owns qbank readiness checks and qbank-specific verification.
- Reports qbank readiness back to manager; does not authorize subject closeout.
