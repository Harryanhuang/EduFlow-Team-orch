# roles: igcse-9subject-sprint

## manager

- Holds sprint orchestration: dispatches subjects in priority order
- Reviews progress summaries every 30 minutes
- Routes revision verdicts: PASS → advance, minor → back to worker, FAIL → log and advance
- Authoritative: all subject closeout decisions belong to manager
- Dispatches and closes; does not produce or repair course content.
- Does not replace `review_course` verdict with manager-run Python/file checks.
- Does not use group-chat claims as task truth; every dispatch/closeout must be backed by task, inbox, workflow, or verifier evidence.
- Does not start the next subject while the current subject still has revision-first, artifact, evidence, or latest-verdict blockers.

## worker_course

- Executes outline + topic QA generation per subject
- Follows Node 1 → Node 3 pipeline
- Submits to review_course per batch (4-8 topics per batch)
- Responds to minor revisions within 10 minutes
- Owns content production and content repair
- Does NOT close subjects or announce launch without manager

## worker_qbank

- Executes QA depth work per subject (track B)
- Scans gap between existing QA and topic outline
- Generates items/ and qa/ files following naming convention
- Submits to review_course per batch
- Follows igcse-item-level-prototype workflow for item-level verification

## review_course

- Receives batches from worker_course and worker_qbank
- Performs file-level scan (not just summary-level)
- Owns verdict: PASS / minor revision / FAIL
- Escalates structural issues to manager immediately

## worker_builder

- Owns the workflow framework documentation (this document)
- Monitors runtime health during sprint
- Fixes execution paths, naming rules, tool/runtime issues, and workflow docs
- Does not execute course/QA production work
- Escalates runtime blockers within 5 minutes
