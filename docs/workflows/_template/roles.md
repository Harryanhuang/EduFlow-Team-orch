# roles: <workflow_id>

## manager

- Calls the workflow.
- Defines object, scope, constraints, and expected outputs.
- Owns formal dispatch, formal closeout, and user-facing result language.

## worker_builder

- Maintains workflow assets.
- Converts real-run evidence and gap notes into template updates.
- Chooses maintenance actions: `update_trigger_examples`, `update_forbidden_moves`, `update_acceptance_gates`, `mark_stale_candidate`, or `split_new_workflow_candidate`.
- Does not mark the workflow active without manager confirmation.

## <worker_role>

- Accepts the task.
- Sends low-frequency reassurance for accepted / started / handed-off states.
- Produces scoped artifacts.
- Does not bypass required review or manager closeout.

## <review_role>

- Reviews the assigned scope.
- Gives an explicit verdict.
- Provides file-level evidence when the workflow activates `file_evidence_gate`.

## auto_ops

- Watches stale handoffs, unread backlog, runtime anomalies, and gap signals.
- Does not own the workflow.
- Does not drive the main process when workflow gates and role procedures can carry it.

## Boundary

Worker/review/qbank roles operate inside their lane. manager remains the caller and formal decision owner. This workflow is not an automatic execution engine.
