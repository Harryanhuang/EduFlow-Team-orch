# checklist: igcse-subject-launch

## Before Manager Announces Launch

- [ ] The IGCSE course task is mounted with `workflow_id=igcse-subject-launch`.
- [ ] If the operator used `--stage course`, the stored canonical stage is still `curriculum`.

- [ ] `worker_course` accepted the task; dispatch is not only delivered.
- [ ] Candidate subject and syllabus code are explicit.
- [ ] Minimum plan is present.
- [ ] Artifacts are present or explicitly scoped: outline, QA seed, manifest.
- [ ] Artifacts use the current path/naming convention.
- [ ] `review_course` acknowledged the review handoff.
- [ ] Latest review verdict is bound to the subject and artifact scope.
- [ ] `review_course` declared `verdict_target` (Package 3 — scope must match closeout target: `full_subject` for subject closeout; partial scopes like `qql_only` / `items_only` / `manifest` / `package` block subject closeout).
- [ ] If verdict is PASS, evidence is file-level when quality gate is active.
- [ ] If verdict is minor, worker produced accepted_revision before repair.
- [ ] No active quality gate blocks rollover.
- [ ] Old unread handoff/task state has been reconciled.

## Block Closeout If

- `worker_course` tries to bypass `review_course`.
- Manager directly produces or repairs course content instead of dispatching `worker_course`.
- Manager directly runs Python/file verification and treats it as the verdict instead of dispatching `review_course` or `worker_builder`.
- Manager claims dispatch / execution / closeout in group chat without matching task, inbox, workflow, or verifier evidence.
- Manager starts the next subject while the current subject still has revision-first, artifact, evidence, or latest-verdict blockers.
- PASS is summary-level while file-level evidence is required.
- Minor repair has not returned to review.
- Manager has unread high-priority quality instruction.
- Artifact truth and status summary disagree.
- A batch/package PASS is being pushed through `manager-closeout` instead of `batch-closeout`.
- **`verify_subject` returns `status != "pass"`** (Package 2 — see Artifact Consistency Gate below).
- [ ] Revision-First Gate is active for this workflow (revision_priority != "" or stale_execution_context detected).
- [ ] **Latest review verdict is not authoritative for closeout** (Package 3): `verdict=rejected` / `manager_action` / `pending`, or `verdict_scope` ∈ {`qql_only`, `items_only`, `manifest`, `package`} when closeout target is `full_subject`. See Review Verdict Authority Gate below.
- [ ] **Worker self-reported "已修好" without a fresh reviewer PASS** (Package 3). Manager must wait for review_course re-review, not act on the worker's word.

## Manager Boundary Gate (Package 5)

Manager is allowed to decide, dispatch, request clarification, and close out
only after gates pass. Manager is not a production or verdict role.

### Forbidden Manager Moves

- [ ] Direct content production or repair (`manager_direct_content_execution`): dispatch `worker_course` for content work.
- [ ] Direct Python/file verification used as verdict (`manager_direct_verification_execution`): dispatch `review_course` for content verdict, or `worker_builder` for path/tool verification.
- [ ] Oral dispatch without task/inbox/workflow truth (`manager_claim_without_task_truth`): create a task-backed dispatch and require worker ACK.
- [ ] Next subject started before current subject gate passes (`premature_next_subject`): finish the current closeout gate first.
- [ ] Non-production role state (for example Anna / Luke / old template roles) used as live production truth (`inactive_role_runtime_drift`): ignore for workflow progress unless it maps to the current production role.

### Required Evidence Before Advancing

- [ ] Dispatch claim has a task row or worker inbox message for the same scope.
- [ ] Closeout claim has latest authoritative `review_course` PASS plus artifact/evidence gates.
- [ ] Review PASS claim matches `latest_authoritative_verdict`, not a group-chat summary.
- [ ] Next-subject launch waits until current subject closeout blockers are clear.
- [ ] `manager-panel` / `manager-actions` show an owner and next action for every boundary blocker.

## Review Verdict Authority Gate (Package 3)

The latest structured `review_course` verdict is the single source of truth
for whether a subject may be closed out. Group chat claims, older PASSes,
and worker self-reports cannot bypass a newer FAIL or a scope mismatch.

### Verdict Scope Contract

Before `review_course` issues a PASS, the review command must declare the
scope via `--verdict-target`. Allowed scopes:

- `full_subject` — QQL + items + manifest all reviewed; only this scope
  authorizes `manager-closeout` for the subject.
- `qql_items` — QQL + items reviewed but manifest layer still pending;
  recognized scope (not empty string), but NOT authoritative for
  subject closeout. Reviewer must add a follow-up `full_subject`
  review that covers the manifest before manager-closeout.
- `qql_only` — only `qa-question-level/` files were validated.
- `items_only` — only the items layer was validated.
- `manifest` — only the manifest consistency was validated.
- `package` / `batch` / `topic` / `unit` — a small scoped unit was reviewed.

### Closeout Authority Rules

- [ ] `manager-closeout` is allowed only when `latest_authoritative_verdict.verdict == "approved"` AND `latest_authoritative_verdict.verdict_scope == "full_subject"`.
- [ ] A `qql_only` PASS does NOT authorize full-subject closeout (items layer may still be missing).
- [ ] An `items_only` PASS does NOT authorize full-subject closeout (QQL layer may still be missing).
- [ ] A `manifest` or `package` PASS does NOT promote to subject PASS.
- [ ] A newer `rejected` or `manager_action` verdict overrides any older `approved` verdict.
- [ ] Worker logs saying "已修好" / "fixed" do NOT clear a reviewer FAIL; the next authoritative PASS does.

### Manager-Actions / Manager-Panel Behavior

- [ ] When the latest verdict blocks closeout, `manager-actions` does NOT emit `action_code=manager_formal_closeout`.
- [ ] The panel/action output shows the blocker (`latest_verdict_rejected`, `verdict_scope_insufficient:*`) and the recommended next action (repair + re-review).
- [ ] When a visible chat/log PASS/closeout contradicts the latest structured FAIL, `task supervisor-check` emits a `review_truth_conflict` finding with severity `error`.

### Recovery

- [ ] Worker addresses `required_fix` and `blocking_files` from the latest verdict.
- [ ] Worker resubmits to `review_course`.
- [ ] `review_course` issues a new verdict with `verdict_target` that covers the remaining layer(s) until the scope is `full_subject`.

## Revision-First Gate (Package 1)

The Revision-First Gate exists to prevent worker_course / worker_qbank from continuing production on a new batch or new subject while a review rejection or manager high-priority correction is still open.

### Triggers (any one enters revision-first state)

- [ ] `review_course` returns verdict `rejected` (minor) on the active batch — `revision_priority="minor"` is auto-set.
- [ ] `review_course` returns `manager_action` — `revision_priority="manager"` is auto-set.
- [ ] manager emits a high-priority correction against the active task — `revision_priority="manager"` is set explicitly.
- [ ] user requests "先修某批 / 暂停扩产" — `revision_priority="user"` is set explicitly.

### Behavior while revision-first is active

- [ ] `workflow_gate_status(task)` returns `gate="revision_first"` with a clear `next_action` directing the worker to address the revision scope first.
- [ ] `next_batch_continuation_gate()` returns `should_continue=False` and surfaces a blocker explanation.
- [ ] `select_next_subject()` returns `None` (no rollover to next subject).
- [ ] `manager-panel` prints a `== Revision-First Blockers ==` section ABOVE any `== Subject Continuation ==` or `== Next Executable Actions ==` section.
- [ ] `manager-actions` does NOT emit `action_code=continue_next_batch` or `action_code=select_next_subject` for any task in a workflow that has revision-first active.

### Stale Execution Context Anomaly

- [ ] If worker_course / worker_qbank produces new topic / batch / subject evidence (in `local_facts.upsert_status` text, pane output, or worker logs) while revision-first is still active, `task supervisor-check` emits a `stale_execution_context` finding.
- [ ] The finding MUST include: `task_id`, `workflow_id`, `expected_revision_scope` (from `scope_topic` / `scope_files`), `observed_new_scope` (from worker status text), and `recommended_action`.

### Evidence Packet Validation

- [ ] Every worker batch report must carry a complete evidence packet before closeout can advance.
- [ ] Required fields: `workflow_id`, `task_id`, `batch_range`, `items_count`, `qql_count`, `manifest_evidence`.
- [ ] `task_event_scanner.validate_evidence_packet(packet)` returns the list of missing field names; supervisor flags any closeout attempt with an incomplete packet.

### Recovery Conditions (revision-first is cleared when ALL of the following hold)

- [ ] Worker produces the revision scope (e.g. accepted_revision, repaired QA files, re-submitted batch).
- [ ] Worker reports evidence packet with all required fields.
- [ ] `review_course` re-reviews and verdict becomes `approved` (or a new flow status that supersedes revision).
- [ ] Manager explicitly calls `tasks.clear_revision_priority(task_id, actor=manager)`.

### Block Continuation / Next-Subject If

- [ ] Any task in the workflow has `revision_priority` non-empty and not yet cleared.
- [ ] `stale_execution_context` finding is currently active for the task.
- [ ] Latest batch evidence packet is missing one or more required fields.

## Worker Context Guard (Package 4)

Pane ready is not enough to continue long-chain production. If any worker
surface shows context exhaustion, unproven readiness, or an unconsumed
high-priority inbox while still producing, manager must stop trusting the
old context and recover with a small, explicit handoff.

### Block Continuation If

- [ ] Health shows `context_exhausted`, `ready_unproven`, `CLI not ready`, or `inbox_recovery_needed` for the worker.
- [ ] Worker logs/pane contain `context window exceeds limit`, `100% context used`, or `interrupted prompt`.
- [ ] Worker has a high-priority inbox item that is unread or not ACKed, but later logs show continuing production.
- [ ] Status says blocked while pane/log evidence shows new production (`status_pane_truth_conflict`).

### Recovery

- [ ] Do not auto C-c / kill / restart from the checklist.
- [ ] Manager-panel / manager-actions should show the affected agent, latest evidence, `allow_continue_original_task=false`, and a recommended action.
- [ ] Preferred recovery is one of: `interrupt_old_context_and_read_inbox`, `restart_worker_runtime`, `reassign_small_batch`, or `split_task_into_revision_batch`.
- [ ] Re-dispatch as a small batch after the worker has read the inbox and the runtime is proved ready.

## Artifact Consistency Gate (Package 2)

Before `manager-closeout` runs, the artifact consistency verifier
(`eduflow.store.subject_verifier.verify_subject`) must return
`status="pass"` for the subject. The verifier is the machine-reproducible
replacement for worker self-audit and manager oral judgment.

Invariants checked (each is a `blocking_reasons` entry when violated):

- **`qql_count == manifest_claimed_total`**: the manifest must enumerate
  the canonical QQL set. Stale or partial manifest is a hard block.
- **`items_count <= qql_count`**: items are derived from QQL; if items
  have grown past the canonical set (e.g. yesterday's 0606 378/324 case),
  the worker hand-wrote entries that don't trace back to QA. Hard block.
- **No format errors**: unclosed `### Question` blocks (e.g. `**Item 10 [F]`
  emitted without a preceding heading) are surfaced as
  `consistency_format_error` and fail closeout.
- **Difficulty values are F/S/C only**: `**Difficulty**: 1` (or `2`, `3`,
  `Easy`, `low/med/high`) is a `consistency_invalid_difficulty` block.
- **Manifest is not a substitute for content**: if QQL layer is empty
  but manifest has rows, the subject is `fail` — manifest cannot stand
  on its own as completion evidence.
- **Batch/package PASS does not promote to subject PASS**: only
  `scope="subject"` results can satisfy this gate. A `verify_package`
  result is always rejected here, even if it returns `status="pass"`.

The compact summary (used by `task subject-inventory` and
`task manager-panel`) carries a `consistency` field with:
`drifts`, `format_errors`, `invalid_difficulty_files`, `scoped_total`,
`drift_count`, `format_error_count`, `invalid_difficulty_count`.

A `pass` at `scoped_total=189` does NOT mean the original
300-400 expansion target is met — it means the *current scope* is
internally consistent. Manager must read `scoped_total` against the
target, not the verdict alone.

## Subject Continuation Gate (Package 5)

After a batch is delivered (batch-closeout), the manager must decide the next step:

### Next Batch Continuation Gate (`next_batch_continuation_gate`)

- [ ] Latest batch is `delivered` with `verdict=approved`.
- [ ] Subject closeout is NOT `closeout_completed`.
- [ ] QA/item counts are below standard range (or batch-level scope).
- [ ] Manager inbox is clear (no P0 unreviewed high-priority items).
- **Recommendation**: continue next batch (read-only; no auto-dispatch).

Block continuation if:
- Subject is already `closeout_completed`.
- QA/item counts meet or exceed the standard range (subject may be ready for closeout, not next batch).

### Next Subject Selection Gate (`select_next_subject`)

- [ ] Exclude `closeout_completed` subjects.
- [ ] Prefer subjects with existing assets (qa_count > 0, item_count > 0, evidence present) over empty ones.
- [ ] Avoid repetition: if the most recently in_progress task belongs to a subject, deprioritize it.
- [ ] Return auditable explanation: why selected, why others skipped.
- [ ] If no candidates remain, return safe default workflow (refresh inventory, scan manifests, await reviewer).

### Manager Panel Integration

- [ ] P0 anomalies and manager-action items take precedence over continuation recommendations.
- [ ] `== Subject Continuation ==` section shows `select_next_subject()` recommendation.
- [ ] Active subjects show `next_batch_continuation_gate()` result with coverage info.
- [ ] When no P0 blocking and no next candidate, panel shows default workflow actions (not idle).
- [ ] `task subject-inventory` (extended) is the manager's default read-only input for pipeline visibility.
