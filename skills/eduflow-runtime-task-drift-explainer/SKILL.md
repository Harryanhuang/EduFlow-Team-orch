---
name: eduflow-runtime-task-drift-explainer
description: Explain runtime/status/task drift for EduFlow P0 status-trust upgrade. Read-only diagnosis skill that turns existing primitives (team, health, runtime verify, runtime-guard, task ops-dashboard, supervisor-check, inbox, residency) into a structured drift report plus safe next-action routing. No Python runtime logic, no state changes, no Feishu sends.
---

# EduFlow Runtime / Task Drift Explainer

Use this skill when an EduFlow agent looks wrong in the team panel, Feishu card, or ops dashboard, and you need to decide whether the problem is runtime, status surface, task truth, inbox, context, residency, or environment drift.

This skill is an operator cognition layer, not a new daemon. It only combines existing read-only commands.

## When to use

- `team --json` or an employee card shows stale/blocked/unknown display.
- `task ops-dashboard` reports `stale_display`, `waiting_inbox`, `blocked`, `warm_idle`, or `unknown`.
- A Feishu snapshot card shows an agent as idle while the group believes work is in progress.
- `health` reports env drift, pane missing, inbox not consumed, or runtime guard cooldown.
- A warm-residency agent is expected to be on standby but appears stopped, or a wake path fails.
- You need a short, evidence-backed diagnosis packet before routing to manager/worker_builder.

## Role boundary

| Role | Permission | What it does |
| --- | --- | --- |
| `auto_ops` | monitor only | Runs the read-only command ladder, fills the evidence template, reports to manager. Never repairs runtime or task state. |
| `worker_builder` | repair after dispatch | Repairs config/CLI/runtime only after manager explicitly dispatches. Does not self-dispatch. |
| `manager` | read + dispatch | Reads the lite report and decides who owns the fix. Does not perform the repair itself. |
| `worker_course`, `review_course`, `worker_qbank` | not runtime repair owners | They own content/task execution; runtime repair must not be delegated to them. |

## Read-only first command ladder

Run these in order. Stop when the diagnosis is clear. Do not jump to wake/sleep commands unless residency is clearly involved.

1. `./scripts/eduflowteam team --json`
   - Snapshot of declared status, residency label, heartbeat age per agent.
2. `./scripts/eduflowteam task ops-dashboard --json`
   - Aggregated display verdicts, top actions, residency counts, degraded sources.
3. `./scripts/eduflowteam health`
   - Session/pane/env drift/runtime readiness/runtime guard state.
4. `./scripts/eduflowteam runtime verify <agent>`
   - Per-agent env/smoke/pane/inbox operational readiness verdict.
5. `./scripts/eduflowteam runtime-guard`
   - Recent switch/cooldown/escalation records.
6. `./scripts/eduflowteam task auto-ops-context`
   - Context guard anomalies (context exhausted, unsafe long context, status/pane truth conflict).
7. `./scripts/eduflowteam task auto-ops-production`
   - Production anomalies not covered by auto-ops-context.
8. `./scripts/eduflowteam task supervisor-check --json`
   - Supervisor-level health, anomalies, runtime guard agents.
9. `./scripts/eduflowteam inbox <agent>`
   - Pending messages and high-priority unread state.
10. `./scripts/eduflowteam residency-sleep --agent <agent> --json`
    - **Dry-run only.** Use only to confirm a warm agent is a sleep candidate.
11. `./scripts/eduflowteam residency-wake <agent> --json`
    - Use only when explicit pre-warm or wake-path verification is needed; not a first diagnostic step.

## Diagnosis taxonomy

| Key | Meaning | Typical evidence |
| --- | --- | --- |
| `runtime_dead` | Pane or CLI process is gone, or health shows session down / pane missing. | `health` red tmux section; `runtime verify` returns `pane_missing`; tmux window absent. |
| `env_drift` | Live environment does not match declared `env_profile`. | `runtime verify` returns `env_drift` with `mismatches`; `health` yellow `runtime_status_env_drift`. |
| `fallback_cooldown` | Runtime guard has a non-zero cooldown or recent cross-pool switch due to failure/rate-limit. | `runtime-guard` shows `cooldown_until`; `supervisor-check` shows `runtime_guard` failure/switch. |
| `inbox_not_consumed` | High-priority unread message exists and is not acknowledged/started/completed. | `runtime verify` `inbox_state=not_consumed`; `inbox <agent>` shows unread high-priority. |
| `context_blocked` | Pane contains context-limit markers or context guard flagged unsafe long context. | `health` red `context_exhausted`; `auto-ops-context` reports `worker_context_exhausted` or `unsafe_long_context_execution`. |
| `task_truth_drift` | Task state, verdict, or owner does not match group/log narration. | `task get`, `review-queue`, `manager-panel` disagree with Feishu text or agent log. |
| `production_stale` | Artifact/file truth is older than task state claims. | Verifier output, manifest mtime, or content files lag behind task `updated_at`. |
| `status_lag` | Declared status is old while heartbeat/log is fresh (or the reverse). | `team --json` shows `updated_at_ms` much older than `heartbeat_ms`; `display_verdict=stale_display`. |
| `external_state_mismatch` | EduFlow internal state disagrees with an external system (Feishu cursor, qbank verifier, subject inventory). | `health` router cursor stale; qbank verifier FAIL while task closeout is green. |
| `warm_residency_expected` | Agent is configured `warm` (`温备`) and is correctly in low-cost standby, not stopped. | `team --json` `residency=温备`; `display_verdict=warm_idle`; no unread/high-priority/active task. |
| `wake_failed` | Warm agent needed for work but wake path could not bring CLI/pane to ready. | `ops-dashboard` `residency.wake_failed>0`; `residency-wake` returns failure; `runtime verify` stays non-ready. |
| `sleep_suppressed_active_task` | Warm agent should be eligible to sleep but has an active task; sleep must be deferred. | `residency-sleep --dry-run` returns `keep_active_task`; task list shows in-progress assignee. |
| `sleep_suppressed_unread_inbox` | Warm agent should be eligible to sleep but has unread inbox; sleep must be deferred. | `residency-sleep --dry-run` returns `keep_unread_inbox`; `inbox <agent>` shows unread. |
| `residency_policy_mismatch` | Resident agent flagged as sleep candidate, or warm/cold policy contradicts observed runtime. | `ops-dashboard` top action shows resident + `sleep_ok`; `team --json` label conflicts with `runtime-status.json`. |

## Evidence template

Capture these items before producing the output template:

- `affected_agent`: exact agent name.
- `commands_run`: list the commands above that were executed.
- `team_json_excerpt`: `residency`, `status`, `task`, `updated_at_ms`, `heartbeat_ms`.
- `runtime_verify_verdict`: one of `proved_ready`, `ready_unproven`, `env_drift`, `smoke_failed`, `inbox_not_consumed`, `pane_missing`, `unknown`.
- `runtime_guard_bits`: `cooldown_until`, `needs_manager_action`, `escalation_needed`, `last_failure_reason`, `route`.
- `task_truth_bits`: current task id/status/owner/verdict, review queue presence, manager action packet.
- `inbox_bits`: unread count, high-priority count, latest message age and ack state.
- `residency_bits`: `residency_mode`, `residency_label`, `sleep_decision`, `wake_status`, `last_sleep_at`, `last_wake_at`.
- `health_red_yellow`: any red or yellow lines from `health`.

## Safe next action routing

| Diagnosis | Owner | Safe next action |
| --- | --- | --- |
| `runtime_dead` | worker_builder (after manager dispatch) | Re-spawn pane/CLI; verify `runtime verify <agent>` reaches `proved_ready`. |
| `env_drift` | worker_builder (after manager dispatch) | Reconcile `env_profile` vs live env; re-run `runtime verify --live-smoke`. |
| `fallback_cooldown` | manager | Review `runtime-guard` history; decide whether to clear cooldown or let it expire. |
| `inbox_not_consumed` | affected agent / manager | Agent consumes or acks high-priority inbox; if agent is warm, consider `residency-wake` first. |
| `context_blocked` | manager + worker_builder | Halt original long task; agent reads inbox; runtime restart if pane exhausted. |
| `task_truth_drift` | manager | Reconcile task state with evidence; dispatch correct owner to update task. |
| `production_stale` | manager / content owner | Refresh artifact/inventory; re-run verifier; update task evidence. |
| `status_lag` | auto_ops (monitor) or manager | Note display staleness; if heartbeat/log fresh, no repair; if stale persists, route to worker_builder. |
| `external_state_mismatch` | manager | Identify authoritative external source; update internal state or external check. |
| `warm_residency_expected` | auto_ops (acknowledge) | No action; record that warm standby is intentional and low-cost. |
| `wake_failed` | worker_builder (after manager dispatch) | Diagnose wake path (CLI binary, env, pane spawn); retry wake; alert if repeated. |
| `sleep_suppressed_active_task` | auto_ops (monitor) | No sleep; ensure active task remains assigned and tracked. |
| `sleep_suppressed_unread_inbox` | auto_ops (monitor) | No sleep; flag inbox for agent/manager consumption. |
| `residency_policy_mismatch` | manager + worker_builder | Fix residency config in `eduflow.toml`; re-run `team --json` to confirm label. |

## Do not do

- Do not add new Python runtime logic.
- Do not modify the task state machine.
- Do not modify Feishu send logic.
- Do not make `manager` the repair owner.
- Do not execute `residency-sleep --apply` as part of diagnosis.
- Do not restart panes, switch runtimes, or clear guard state without manager dispatch.
- Do not trust a single surface; always cross-check `team`, `health`, `runtime verify`, and `task`.

## Output template

```markdown
## Runtime/Task Drift Explainer

- affected_agent:
- diagnosis:
- confidence:
- evidence_used:
- what_is_not_the_problem:
- safe_next_action:
- owner:
- user_visible_update_needed:
- do_not_do:
```

## Example cases

### 1. Display stale but heartbeat fresh

- Commands: `team --json`, `runtime verify worker_course`, `health`.
- Evidence: `team --json` shows `updated_at_ms` 35 min ago, `heartbeat_ms` 1 min ago, `residency=温备`.
- `runtime verify worker_course` returns `proved_ready`, `inbox_state=no_pending`.
- Diagnosis: `status_lag`.
- What is not the problem: runtime is not dead, env has not drifted, inbox is empty.
- Safe next action: auto_ops records the staleness; if status does not refresh, ask manager whether to nudge agent to update status.
- Owner: auto_ops (monitor) / manager (dispatch nudge).
- User-visible update needed: No immediate update; can mention "display catch-up pending" if user asks.
- Do not do: restart pane, send Feishu message, mark agent blocked.

### 2. High-priority inbox unread and not consumed

- Commands: `team --json`, `runtime verify review_course`, `inbox review_course`, `task ops-dashboard --json`.
- Evidence: `inbox review_course` shows one `high` priority message, unread, 90s old; `runtime verify` returns `inbox_not_consumed`.
- Diagnosis: `inbox_not_consumed`.
- What is not the problem: pane is ready, env matches, no context exhaustion.
- Safe next action: review_course consumes/acks the message; if the message requires manager authority, manager dispatches next step.
- Owner: review_course (consume) / manager (dispatch if authority needed).
- User-visible update needed: Only if the high-priority item came from a user-visible request and is now delayed.
- Do not do: clear inbox manually, restart review_course pane.

### 3. Runtime env drift

- Commands: `health`, `runtime verify worker_builder`, `runtime-guard`.
- Evidence: `health` yellow `runtime_status_env_drift: worker_builder ANTHROPIC_API_KEY mismatch`; `runtime verify` returns `env_drift` with mismatches `["ANTHROPIC_API_KEY differs"]`, `cached=false` after `--live-smoke`.
- Diagnosis: `env_drift`.
- What is not the problem: pane exists, CLI is responsive, no inbox backlog.
- Safe next action: manager dispatches worker_builder to reconcile `env_profile` and live shell env; re-run `runtime verify --live-smoke`.
- Owner: worker_builder (after manager dispatch).
- User-visible update needed: No; this is an infra repair.
- Do not do: send Feishu pretending the agent is broken, switch runtime without env fix.

### 4. Warm residency is expected low-cost standby, not stopped

- Commands: `team --json`, `task ops-dashboard --json`, `runtime verify worker_qbank`.
- Evidence: `team --json` shows `residency=温备`, `status=待命`, no blocker, heartbeat 2 min ago; `ops-dashboard` shows `warm_idle=1`; `runtime verify` shows `pane ready` but CLI idle banner.
- Diagnosis: `warm_residency_expected`.
- What is not the problem: agent is not stopped, not crashed, not blocked.
- Safe next action: auto_ops acknowledges warm standby; no wake unless high-priority work arrives.
- Owner: auto_ops.
- User-visible update needed: Optional — explain "温备 = on-call standby, will wake on next assignment" if user is confused.
- Do not do: restart, wake, or mark as blocked.

### 5. Wake failed on a warm agent

- Commands: `task ops-dashboard --json`, `residency-wake worker_course --json`, `runtime verify worker_course`, `runtime-guard`.
- Evidence: `ops-dashboard` `residency.wake_failed=1`; `residency-wake worker_course --json` returns `wake_status=failed` with reason `cli_spawn_timeout`; `runtime verify` returns `pane_missing`; `runtime-guard` shows `last_failure_reason=wake_failed`.
- Diagnosis: `wake_failed`.
- What is not the problem: env is correct, no inbox backlog, no active task.
- Safe next action: manager dispatches worker_builder to inspect CLI spawn command, binary PATH, and pane layout; retry `residency-wake`; if repeated, escalate to worker_builder + record gap note.
- Owner: worker_builder (after manager dispatch).
- User-visible update needed: Yes — a brief note that the standby agent is being woken and may be delayed.
- Do not do: ask content worker to fix spawn; ignore repeated failures.
