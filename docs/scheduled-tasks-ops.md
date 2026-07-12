# D scheduler — operator ops notes

This is the minimum companion doc for the D scheduled-task system
delivered across packages P0-P8.  It only covers day-to-day operator
needs; design rationale is in
`docs/plans/2026-07-11-scheduled-tasks.md`.

## Concepts

* **D rule** — a recurring business rule (`daily`, `weekly`, `once`).
  Persisted as `D-<n>` and kept in `state/scheduler/rules.json`.
* **D occurrence** — one due cycle for a rule, keyed
  `D-<n>:<UTC scheduled_at>` so re-ticks are idempotent.  Lives in
  `state/scheduler/occurrences.json`.
* **D lane** — a per-agent snapshot bound to an occurrence.  Lives
  in `state/scheduler/lanes.json`.
* **Notification ledger** — append-only JSONL of `create`,
  `supplement_confirm`, `occurrence_started`, `result_or_failure`,
  `manager_reminder`, `user_notification`, and `workflow_demoted`
  events.  Lives in `state/scheduler/notifications.jsonl`.
* **Heartbeat** — last scheduler tick / success / lag.  Lives in
  `state/scheduler/heartbeat.json`.
* **Cursor** — `state/scheduler/cursor.json` (separate from the T
  task-publish cursor).

## Start the scheduler

`eduflow task-publish --once` runs the scheduler tick once and exits.
The long-running variant is already wired into the existing
`task-publish` command:

```bash
# one-shot (debug / dev)
eduflow task-publish --once --to manager

# long-running loop (default behaviour)
eduflow task-publish
```

The scheduler tick:

1. calls `eduflow.scheduling.engine.reconcile(now_ms)` to handle any
   missed due cycles and lost notifications,
2. calls `eduflow.scheduling.engine.tick(now_ms)` to advance the
   schedule and create new `awaiting_manager` occurrences,
3. writes the heartbeat and updates the scheduler cursor.

It never creates user-visible T tasks.  Every cycle still requires
manager confirmation; manager dispatch is invoked from the manager
skill, not from the scheduler.

## Inspect the panel / health

`eduflow task manager-panel` and `eduflow health` both include a
read-only D scheduler section.  Sections are sourced from the
scheduler store only — they do not mutate state.

### `task manager-panel` — D scheduler rows

* `awaiting_manager` — D occurrences still awaiting the manager's
  call.  `next_action: task schedule confirm-occurrence <key> --as manager`.
* `running` — currently dispatched; nothing required yet.
* `blocked` — previous cycle still running; default behaviour blocks
  parallel dispatch.  `next_action: task schedule skip-occurrence <key> --as manager --reason clear`.
* `recent_failure` — last cycle failed via `fail-pause`.  `next_action: task schedule fail-pause <key> --as manager --reason triage`.
* `attention_required` — rule status; capacity exceeded.  `next_action: task schedule resume <D-id> --as manager` (after triage).
* `due_soon` — rule with an upcoming `next_due_utc`.
* `scheduler_lag=warn` — heartbeat older than the warn threshold.

### `health` — D scheduler section

```
D scheduler:
  ✅ heartbeat=ok last_tick=<s> ago lag=ok pending=N running=N blocked=N attention_required=N
  ℹ️   consecutive_skip=N consecutive_failure=N
```

When the scheduler raises, the heartbeat row flips to:

```
  ⚠️ heartbeat=error ... error=<ExceptionClass>: <message>
```

This is a red check that blocks the `health` exit code.  Triage by
inspecting the error and the rule's `next_due_utc` for malformed
input.

## Lifecycle CLI summary

| Command (run with the correct `--as` actor) | Effect |
|--------------------------------------------|--------|
| `eduflow task schedule create-draft --as user ...` | Create a draft D rule.  Does not yet tick. |
| `eduflow task schedule confirm-draft <D-id> --as user\|manager` | Confirm a draft rule (binds owner + version). |
| `eduflow task schedule pause\|resume\|cancel <D-id> --as user\|manager` | Lifecycle the rule. |
| `eduflow task schedule confirm-occurrence <key> --as manager` | Manager confirms an awaiting occurrence. |
| `eduflow task schedule skip-occurrence <key> --as manager --reason <text>` | Skip a cycle.  Used when backlog must be cleared. |
| `eduflow task schedule dispatch <key> --as manager` | Bind lanes + mark the occurrence `running`. |
| `eduflow task schedule add-lane <key> --agent <name> --inputs-json {...}` | Record a single lane snapshot. |
| `eduflow task schedule report <key> --lane <lane-id> --status done\|failed` | Worker reports back to the manager. |
| `eduflow task schedule fail-pause <key> --as manager --reason <text>` | Mark cycle failed; rule -> `attention_required`. |
| `eduflow task schedule list [--status active\|paused\|...]` | Print all D rules (read-only). |

`worker` role cannot confirm or dispatch rules — `report` is its only
allowed verb.

## Workflow evolution (5 stable / 2 deviation)

Observations are recorded by `record_outcome(rule_id, ..., result=...)`
in `eduflow.scheduling.workflow_evolution`.

* **5 stable completions** with the same `(target, artifact, role,
  ordered lane agents)` and no repeat failure pattern in the last 5
  -> phase becomes `candidate`, `candidate_payload(rule_id)` returns
  the frozen spec draft.
* Manager approves (`approve_candidate(rule_id, actor='manager')`)
  -> phase becomes `approved`.  Workflow is now a **frozen snapshot
  only**; every cycle still requires manager confirmation, never an
  auto-dispatcher.
* **2 consecutive signature deviations or failures** post-approval ->
  the rule auto-demotes back to `exploration` and appends a
  `workflow_demoted` user notification.
* **Healthy review** is due when either 30 days have elapsed since
  the last review (or approval) OR `since_review_count` >= 10
  successful runs (`health_review_due(...)` returns True).

## Archive

Default retention is **90 days** (configurable per call).  The
archiver is dry-run by default and protects `awaiting_manager`,
`running`, `confirmed`, `blocked` occurrences no matter the age.

```python
from eduflow.store import scheduled_tasks
# dry-run (default) — returns candidate list without mutating state
scheduled_tasks.archive_old_records(
    cutoff_ms=scheduled_tasks.retention_cutoff_ms(now_ms=now_ms, retention_days=90),
    dry_run=True,
)
# apply
scheduled_tasks.archive_old_records(
    cutoff_ms=scheduled_tasks.retention_cutoff_ms(now_ms=now_ms, retention_days=90),
    dry_run=False,
)
```

The archiver rewrites eligible occurrence rows in place (keeps `id`
and `rule_id`, replaces noisy `context` with a compact `summary`,
adds `archived` / `archived_at` markers, and removes the
lane / notification rows that belong to those occurrences).  Active /
unfinished references are NEVER touched.

## Failure-isolation contract

These properties are pinned by the integration test
`tests/integration/test_scheduled_tasks_e2e.py`:

* Scheduler tick failure **must not** break the regular
  `task-publish` loop; its cursor stays at zero.
* Re-tick is idempotent: a second `tick(now_ms)` at the same
  wall-clock instant creates zero new occurrences.
* `tick` writes state BEFORE appending the notification; `reconcile`
  replays lost `occurrence_due` notifications exactly once per
  occurrence.
* Memory subsystem outage is fully absorbed by
  `eduflow.scheduling.memory_bridge`; the bridge never raises.
* Scheduler outage is observable in `health` and in the manager-panel
  `scheduler_lag` row but is NOT fatal for the T publish path.
* No D cycle ever produces a user-visible T task.

## Storage summary

All D scheduler state lives under `state/scheduler/`:

```
state/scheduler/
  rules.json           # D rules (CAS / version-protected writes)
  occurrences.json     # one record per due cycle (idempotency key)
  lanes.json           # per-occurrence lane snapshots
  notifications.jsonl  # append-only ledger
  heartbeat.json       # last tick / lag / error
  cursor.json          # scheduler cursor (NOT the T publish cursor)
  meta.json            # D-ID sequence counter
  evolution.json       # P8 workflow evolution record per rule
```
