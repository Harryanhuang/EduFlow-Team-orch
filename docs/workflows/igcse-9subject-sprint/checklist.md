# checklist: igcse-9subject-sprint

## Sprint Setup (pre-dispatch)

- [ ] All 9 subjects confirmed: 0452, 0606, 0610, 0620, 0653, 0478, 0455, 0580, 0625
- [ ] Current content inventory done (topic counts, QA counts, item counts)
- [ ] Dispatch priority order set (most ready → least ready)
- [ ] Runtime health: all agents proved_ready
- [ ] review_course inbox clear (no backlog)

## Per-Subject Pre-Dispatch Checklist

- [ ] Subject slug confirmed (e.g. igcse-physics-0625)
- [ ] `topic-outline.md` read (or flagged as missing)
- [ ] `qa-manifest.csv` scanned for consistency vs actual files
- [ ] Sprint brief written (1 paragraph: what exists, what's missing, target)
- [ ] QA naming convention confirmed (Q-<topic-id>-<nn>, F:2|S:4|C:3)

## Per-Batch Checklist (before review_course)

- [ ] Batch scope: 4-8 topics, same domain/level
- [ ] QA files: each has Question / Answer / Explanation / Tags / Difficulty
- [ ] No duplicate Q-IDs within subject
- [ ] Difficulty mix: roughly F:2 | S:4 | C:3 per topic
- [ ] Difficulty values are Foundation/Standard/Challenge (numeric `1`/`2`/`3` is invalid)
- [ ] QA files written to `qa-question-level/` dir
- [ ] Manifest updated: topic_id, qa_file, question_count, difficulty_mix
- [ ] Items files: each topic has at least one items/ file
- [ ] **Artifact consistency check** (Package 2): `eduflow.store.subject_verifier.verify_subject` returns `status="pass"` for the subject OR the drift is explicitly accepted as a scoped batch (e.g. 189/189/189 is internally consistent even if the original 300-400 target is not met)

## Per-Review Checklist

- [ ] review_course received handoff with file paths
- [ ] review_course verdict: PASS / minor / FAIL
- [ ] **verdict_target declared** (Package 3 — scope must match closeout target; partial scopes like `qql_only` / `items_only` cannot satisfy full_subject closeout)
- [ ] If minor: revision produced within 10 minutes
- [ ] If PASS: manager closeout gate checked — **`verify_subject` must return `pass` for `manager-closeout` to be allowed** (Package 2: items vs QQL drift, format errors, invalid difficulty, and missing QQL with manifest-only are all hard blocks) AND **`latest_authoritative_verdict.verdict_scope` must be `full_subject`** (Package 3: a QQL-only PASS does not promote to subject closeout)
- [ ] If FAIL: root cause logged before advancing, `required_fix` and `blocking_files` carried to the next worker round

## Block Sprint If

- [ ] Runtime health degrades (more than 2 agents smoke_failed)
- [ ] review_course backlog exceeds 5 pending batches
- [ ] A single subject has more than 3 open minor repairs
- [ ] A batch has FAIL verdict (structural issue, not minor)
- [ ] Manager directly produces/repairs content instead of dispatching `worker_course`.
- [ ] Manager directly runs Python/file verification and treats it as verdict instead of dispatching `review_course` or `worker_builder`.
- [ ] Manager claims "已派工 / 已执行 / 已 closeout" but task, inbox, workflow, or verifier truth does not match.
- [ ] Manager starts the next subject while the current subject is not fully closed out.
- [ ] **A subject's `verify_subject` result has `consistency.drift_count > 0` for blocking drifts** (items > QQL, or QQL ≠ manifest). Items are derived from QQL; a drift means hand-written or duplicated entries that don't trace back to QA.
- [ ] Revision-First Gate is active for any subject in the sprint (revision_priority != "" or stale_execution_context detected).
- [ ] **Latest review verdict on a subject is not authoritative for subject closeout** (Package 3): `verdict=rejected` / `manager_action` / `pending`, or `verdict_scope` is `qql_only` / `items_only` / `manifest` / `package` when target is `full_subject`. See Review Verdict Authority Gate.
- [ ] **Worker self-reported "已修好" without a fresh reviewer PASS** (Package 3). Manager must wait for review_course re-review, not act on the worker's word.

## Manager Boundary Gate (Package 5)

Manager is the sprint owner, not the production worker and not the reviewer.
Every sprint advance must land in task / inbox / workflow / evidence.

### Boundary Findings

- [ ] `manager_direct_content_execution`: block sprint advance; dispatch `worker_course` for content repair.
- [ ] `manager_direct_verification_execution`: block sprint advance; dispatch `review_course` for verdict or `worker_builder` for path/tool verification.
- [ ] `manager_claim_without_task_truth`: block until task-backed dispatch or worker inbox evidence exists.
- [ ] `premature_next_subject`: block next subject; finish current subject closeout gate first.
- [ ] `inactive_role_runtime_drift`: do not treat non-production role state as live sprint progress.

### Action Surface Requirements

- [ ] `task manager-actions` shows the blocker as an action packet with owner/assignee and next action.
- [ ] `task manager-panel` shows boundary blockers before continuation / next-subject work.
- [ ] Boundary blockers are not downgraded to generic warnings.
- [ ] Normal manager closeout remains allowed when review, artifact, evidence, and closeout gates pass.

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

Sprint expansion must pause when a worker pane is visually ready but the
runtime/context is not trustworthy.

### Block Sprint Expansion If

- [ ] Health distinguishes `pane ready` from `proved_ready`, and the worker is `ready_unproven`, `context_exhausted`, `CLI not ready`, or `inbox_recovery_needed`.
- [ ] Worker logs/pane show `context window exceeds limit`, `100% context used`, or `interrupted prompt`.
- [ ] A worker has a high-priority unread/unACKed inbox item while later logs show continuing production.
- [ ] Status says blocked but pane/log evidence shows production.

### Recovery

- [ ] Do not auto C-c / kill / restart from the checklist.
- [ ] Manager-panel / manager-actions must show affected agent, latest evidence, recommended action, and `allow_continue_original_task=false`.
- [ ] Prefer `interrupt_old_context_and_read_inbox` first when inbox is pending; use `restart_worker_runtime` only as an explicit operator action.
- [ ] Reassign only a small batch after recovery, not the full sprint lane.

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

## Artifact Consistency Gate (Package 2)

`task subject-inventory` and `task manager-panel` show the artifact
consistency verifier result for each subject. Manager must read
`consistency.scoped_total` to see the current internally-consistent
count, and check it against the original sprint target:

- `scoped_total=189` with original target 300-400 → closeout-able as a
  SCOPED batch only. Manager must explicitly choose to accept the
  reduced scope, not let the verifier `pass` quietly substitute for
  the expansion target.
- `consistency.drift_count > 0` (any kind) → subject is not closeout-ready
  regardless of `status` field on the worker task.
- `consistency.format_error_count > 0` (e.g. `**Item 10 [F]` blocks) →
  worker must repair before review handoff.
- `consistency.invalid_difficulty_count > 0` → worker must rewrite
  `**Difficulty**` to F/S/C before review handoff.

If `verify_subject` blocks a `manager-closeout`, the manager must NOT
use `--skip-verifier` to bypass it — that escape hatch exists for
test-only fixtures and is logged when used. The right action is to
dispatch the worker to repair the drift and re-verify.

## Sprint Closeout Checklist

- [ ] All 9 subjects: current state documented
- [ ] Each subject: QA gap identified and ranked
- [ ] Each subject: next_action stated (continue / closeout / backlog)
- [ ] Each subject: `verify_subject` status documented; scoped_total read against target
- [ ] Open issues: logged with root cause
- [ ] All agents: inbox clear
