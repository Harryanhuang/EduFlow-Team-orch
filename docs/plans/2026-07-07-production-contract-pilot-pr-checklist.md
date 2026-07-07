# Production Contract Pilot — PR Reviewer Checklist

> For the PR that lands Package 0-7 of the production-contract pilot on
> branch `feat/production-contract-pilot-2026-07-07`. Reviewer should be
> able to clear this in 20-30 minutes.

## TL;DR

Adds **5 read-only read-models** + **2 small CLI flag fixes** + **1
manager-panel enhancement** + **3 templates** + **4 pilot runbook docs**.
**No task state mutation, no memory writes, no runtime changes, no
behavior changes to send / say / fire / hire / reset.**

Diff: 20 files, +3606 / -9 lines, ~97 new tests (338 → 435).

## What This PR Does (one-liner per piece)

| Surface | Reads | Writes | Stops on read-model error |
|---------|-------|--------|---------------------------|
| `task loop-contract <T-id> [--json]` | task + latest_authoritative_verdict + required_fix + blocking_files + inbox messages | none | n/a |
| `task tool-risk --command "..." [--json]` | command string tokens | none | n/a |
| `task evolution-packet <T-id> [--json]` | task + verdict + loop_cycle_count + status | none | n/a |
| `task readiness-check <T-id> [--json] [--diagnostics]` | heartbeat + logs + inbox + task evidence | none | n/a |
| `task manager-panel` (existing, modified) | above 4 read-models per workflow task | none | yes — degrades to warning line |
| `task review --reject` (flag fix) | task | via existing tasks.review_flow API | n/a |
| `eduflow send --task-id` (flag fix) | n/a | inbox (existing) | n/a |

## Why Now

Without these read-models, manager dispatches repair handoffs blind to
the failure mode. With them, every handoff can carry a deterministic
contract + readiness check + evolution packet candidate, so workers
stop being off-track and reviewers stop re-discovering what manager
already knew.

## Reviewer Steps (in order)

### 1. Read the plan

`docs/plans/2026-07-06-eduflow-production-contract-pilot-packages.md`

It specifies Packages 0-7 (this PR) and Package 8 (paused, not in PR).

### 2. Verify diff scope

```bash
git checkout feat/production-contract-pilot-2026-07-07
git diff --stat master..HEAD
```

Expected: **20 files, mostly +N / -0**. Anything with -lines > 5 in a
file is suspicious — please flag.

### 3. Run tests

```bash
python3 -m pytest tests/unit/test_task_loop_contract.py \
                    tests/unit/test_tool_risk.py \
                    tests/unit/test_evolution_packet.py \
                    tests/unit/test_operational_readiness.py \
                    tests/unit/test_operational_readiness_diagnostics.py \
                    tests/unit/test_manager_panel_minimal_surface.py \
                    tests/unit/test_cli_flag_gaps.py \
                    tests/unit/test_commands_task.py -q
```

Expected: **all pass except 1 pre-existing failure** in
`test_say_keeps_non_whitelisted_worker_message_silenced_when_worker_to_user_disabled`
(verified to be unrelated to this PR — `say` CLI untouched).

### 4. Spot-check the 4 read-models on a real task

Pick any active task (e.g. T-122):

```bash
./scripts/eduflowteam task readiness-check T-122 --json --diagnostics
./scripts/eduflowteam task loop-contract T-122 --json
./scripts/eduflowteam task evolution-packet T-122 --json
./scripts/eduflowteam task tool-risk --command "eduflow reset" --json
./scripts/eduflowteam task manager-panel
```

Verify:
- `loop-contract.delivery.inbox_local_id` is non-empty after a
  `send --task-id T-122 ...` was sent
- `evolution-packet.candidates[0].source_event` is one of the documented
  triggers when task was rejected
- `manager-panel` shows compact `contract: phase=... failed=... delivery=... ...` line

### 5. Verify read-model strictness (no state mutation)

```bash
./scripts/eduflowteam task loop-contract T-122 --json
./scripts/eduflowteam task loop-contract T-122
./scripts/eduflowteam task evolution-packet T-122 --json
./scripts/eduflowteam task evolution-packet T-122
./scripts/eduflowteam task readiness-check T-122 --json
./scripts/eduflowteam task readiness-check T-122 --diagnostics
```

Then re-check the task state hasn't changed:

```bash
./scripts/eduflowteam task get T-122
```

The output should be byte-identical to before the read-model calls.

### 6. Confirm `tool-risk` doesn't block

`tool-risk` only **returns advice**. It does NOT block the command.
Try:

```bash
./scripts/eduflowteam task tool-risk --command "eduflow reset" --json
./scripts/eduflowteam task tool-risk --command "rm -rf /tmp/foo" --json
./scripts/eduflowteam task tool-risk --command "eduflow send worker_course manager 'x' 高" --json
```

Should return `Critical / manager_only` or `High / auto_review` JSON,
without affecting anything else.

## Things NOT to Verify (out of scope)

- Package 8 flow-memory bridge (intentionally paused)
- `review_course → worker_review` global rename in `store/tasks.py`
  (already shipped in T-139 for cards_v2_schema.py; remaining
  >30 hard-coded identifiers intentionally deferred to a separate
  rename task per user's choice "A" — continue defer)
- Real pilot data accumulation (`acceptance-log.md`) — ongoing, not a
  PR-merge blocker
- Threshold tuning (`HEARTBEAT_FRESH_MS / PROGRESS_FRESH_MS /
  DELIVERY_FRESH_MS`) — first-week post-merge observation only

## Risk Inventory

| Risk | Likelihood | Mitigation in PR |
|------|------------|------------------|
| Read-model raises on edge case | medium | manager-panel catches and renders `read-model unavailable` warning; never crashes panel |
| Threshold too tight (5min heartbeat) | low | `--diagnostics` flag + `pilot-execution-plan.md` observation table for first-week tuning |
| CLI flag `--required-fix` ignored by other review callers | low | only `_cmd_review` exposes them; review_flow API signature unchanged |
| send `--task-id` not honored by routing logic | low | flow_memory packet prepending already used `_task_id` extracted from message; our flag is additive |

## Rollback Plan

Each commit is self-contained. To revert without surgery:

```bash
git revert ac618b88
git push origin master
```

Re-running any read-model command after revert returns "unknown
subcommand" — safe degradation.

## Decision Required

| Question | Options |
|----------|---------|
| Merge now or wait for additional pilot data? | (a) merge now; iterate in follow-up PRs; (b) wait until 5+ pilot rows accumulated |
| Threshold tuning window? | (a) one week post-merge; (b) two weeks |
| Should manager-panel `contract:` line be opt-in via flag? | (a) on by default (current); (b) opt-in behind `--contract-line` flag |

## Sign-off checklist

- [ ] Diff scope matches plan (20 files, no surprises)
- [ ] Tests pass (97 new + ~316 existing)
- [ ] Read-models return documented shapes on real tasks
- [ ] No task state mutation after read-model calls
- [ ] `tool-risk` returns advice, doesn't block
- [ ] Decision made on merge / wait / opt-in flag