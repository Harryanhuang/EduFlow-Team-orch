# EduFlow Team Monitor Gap Taxonomy

Use this reference to classify overnight run issues and convert them into repair work.

## P0/P1 Themes From 2026-06-21

### 1. Message Processing And Consumption

Symptoms:

- Worker says “sent to review” but reviewer inbox is empty.
- Review verdict exists, but manager keeps saying “waiting for verdict”.
- High-priority inbox is read but not acked, or executed but still unread.
- `--no-inject` messages sit in inbox without being consumed.
- `tmux send-keys` text appears in input but is not executed.

Repair direction:

- Add `inbox drain before report` to manager.
- Track unread count, pending ack count, oldest message age.
- Add `inbox reconcile` for messages proven complete by logs/status.
- Treat `read=true` without ack as a separate warning.
- Critical handoffs must return message id and verify recipient inbox/review queue.

### 2. Task Truth / Status Truth Drift

Symptoms:

- Group says PASS/closeout, but task remains `submitted_for_review` or `verdict=pending`.
- Task is `queued` but group says worker accepted it.
- Worker is editing files but task remains `assigned`.
- Status says waiting/idle while files or panes show active progress.

Repair direction:

- Bind worker ACK to `in_progress`.
- Bind `VERDICT: PASS` / `task_completed` to `task review --approve`.
- Add batch closeout command separate from subject closeout.
- Manager closeout must verify task state after public announcement.
- Supervisor should detect `PASS but pending`, `queued with empty inbox`, and `closeout text but task not closed`.

### 3. Workflow Not Enforced

Symptoms:

- Agents mention workflow in chat but task lacks `workflow_id`.
- Review/repair/closeout gates happen through informal messages only.
- Chemistry small packages ran mostly by inbox/logs rather than formal workflow gates.

Repair direction:

- Require `workflow_id=igcse-subject-launch` for IGCSE subject tasks.
- Add package-level gate states.
- Add `workflow gates` or equivalent closeout check before manager closeout.
- Supervisor should flag “workflow mentioned but not mounted”.

### 4. Runtime And Model Drift

Symptoms:

- `runtime-status.json` says one runtime, live tmux env shows another.
- Pane is ready but provider is quota-exhausted or stuck at interrupted input.
- 429/rate limit does not trigger fallback.
- Fallback switches to same quota pool.
- Health says tmux session down while system tmux can list panes.

Repair direction:

- Health must show import path, tmux socket/path/user, live provider/model env.
- Runtime switch must verify live pane env and run API smoke.
- Add `runtime_drift` and `provider_quota_exhausted_but_fallback_available` anomalies.
- After switch, run `post-switch smoke -> inbox consume -> status/log update`.
- Use cross-provider fallback for 429/quota exhaustion.

### 5. Router / Watchdog / Supervisor Flapping

Symptoms:

- Router repeatedly subscribes, catches up missed messages, then exits after idle timeout.
- Multiple router entrypoints compete.
- Health and supervisor disagree about daemon liveness.
- Watchdog missing or unable to restore stable router.

Repair direction:

- Distinguish `down`, `alive`, and `alive-but-flapping`.
- Show recent respawns, reasons, and catch-up counts.
- Deduplicate router entrypoints and pid files.
- Make `down router` safe; do not kill the whole team when a daemon restart is intended.
- Include hermes-supervisor in health.

### 6. Subject Continuation And Rotation

Symptoms:

- Manager waits for user after batch closeout even when subject backlog remains.
- Physics repeats batch after batch while other IGCSE subjects exist.
- A completed subject remains in candidate pool.

Repair direction:

- Add subject backlog table: subject, exam code, topic count, QA count, review status, qbank status, next action.
- Add `next_batch_continuation_gate`.
- Add `select_next_subject` after subject closeout.
- Idle state should mount safe default workflow instead of waiting blankly.

### 7. Artifact Quality And Verifier Gaps

Symptoms:

- Worker self-check claims all topics pass, but machine count disagrees.
- Orphan cleanup deletes valid QQL files.
- Old fragments and new package files mix in the same subject.
- Manifest location differs from expected root path.

Repair direction:

- Use machine preflight for per-topic counts and difficulty.
- Orphan cleanup must use expected Question ID set and quarantine first.
- Subject launch should classify blank/new vs old-half-finished assets.
- Subject closeout requires full inventory verifier, not final package PASS.

### 8. QBank Visibility And Safety

Symptoms:

- Worker_qbank has produced scans/reports, but manager does not externalize them.
- Verifier hardcodes subject list and misses newly completed subjects.
- Dedup dry-run risks modifying QA originals or misclassifies Q-ID collision as duplicate content.

Repair direction:

- QBank gets its own task states: scan, issue-fix, reverify, ready-for-import.
- Verifier should auto-discover `content/igcse-*` subjects or read inventory.
- Apply/dedup requires review gate and explicit authorization.
- Manager must publish compact QBank status after worker_qbank internal report.

### 9. External Visibility And Noise Control

Symptoms:

- Repeated completion messages from same worker/event.
- Status card lags live pane.
- Wrong subject list in status board.
- User cannot see QBank or current package status.

Repair direction:

- Add short-window dedupe by task id + stage + normalized content.
- Maintain a single `visible_truth_snapshot`.
- Manager reports should be minimal and evidence-backed.
- Agent card colors should be stable and documented.

## Intervention Decision Matrix

Observe only:

- Artifact, task, inbox, and status all agree.
- A worker is actively editing or reviewer is actively reviewing within expected time.

Nudge manager:

- Manager narration is stale.
- Manager needs to consume a verdict/result.
- Safe next action exists but manager is idle.

Direct worker/reviewer instruction:

- Manager has not acted after a verdict/result and a narrow handoff is missing.
- A worker is following stale instructions that risk corrupting artifacts.

Repair task/inbox truth:

- Group/log action already happened but structured truth is stale.
- Reviewer is missing from review queue.
- A message is proven executed but unread state keeps polluting supervisor.

Runtime repair:

- Provider quota/429 blocks critical role.
- Pane missing for assigned/reviewing task.
- Health/tmux/runtime surfaces contradict each other.

Operator fallback:

- Production/review chain is blocked and current content can be safely verified or repaired.
- Always label fallback as operator action; do not let manager present it as natural review.
