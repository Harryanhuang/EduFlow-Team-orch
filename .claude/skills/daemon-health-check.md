---
name: daemon-health-check
description: Structured daemon health verification template for auto_ops and worker_builder. Use when checking router/watchdog/task-publish health, diagnosing stalls, or reporting daemon status to manager.
metadata:
  type: workflow
  generated_by: auto_ops
  date: 2026-06-24
  source: daemon health check patterns from 100+ patrol cycles
---

# Daemon Health Check

## Use When

- Routine patrol by auto_ops
- Watchdog triggers stall alert
- Manager requests daemon status
- After router restart / respawn event
- worker_builder verifying repair

## Daemon Checklist

### 1. Process Alive Check

```bash
ps aux | grep -E "eduflow\.(router|watchdog|task-publish)" | grep -v grep
```

Expected: 3 PIDs, all running. Each line shows `eduflow.cli router`, `eduflow.cli watchdog`, `eduflow.cli task-publish`.

Record PIDs for cross-reference.

### 2. PID File Consistency

```bash
cat .eduflow-team-state/pids/router.pid
cat .eduflow-team-state/pids/watchdog.pid
cat .eduflow-team-state/pids/task-publish.pid
```

Compare with Step 1 PIDs. Mismatch = stale pidfile (process restarted without cleanup).

### 3. Stale Stall Detection

```bash
eduflow health | grep -A5 "router stall"
```

Key fields:
- `router stall reason`: "none" = healthy, anything else = investigate
- `threshold`: should be 1800s (not 0 — if 0, display bug, not real issue)

### 4. Respawn Rate

```bash
eduflow health | grep "respawn"
```

Healthy baseline: 0-1 respawns/day. Escalating pattern:
- 2-5/day: monitor, check lark-cli subscribe idle timeout
- 5-15/day: investigate root cause (previously: lark-cli 600s idle timeout)
- >15/day: critical, report to manager immediately

### 5. Daemon Startup Log

```bash
tmux capture-pane -t EduFlowTeam:router -p | grep -i "start\|listen\|error\|stall" | tail -10
```

Look for:
- Clean startup: "router started", "listening"
- Errors: API auth failures, config missing
- Stalls: timeout messages

### 6. Cross-Agent Health

```bash
eduflow team
```

All agents should show:
- Status: 待命 or 进行中 (not 已停止 unless intentional)
- Heartbeat: < 5 min ago
- No `runtime_status_env_drift` warning (unless known/acceptable)

## Health Report Template

```bash
eduflow send manager auto_ops "Daemon 健康报告：
router: [alive/dead] PID=[N] respawns=[N/day] stall=[none/reason]
watchdog: [alive/dead] PID=[N]
task-publish: [alive/dead] PID=[N]
hermes-supervisor: [running/not-running] pid_file=[consistent/stale]
agents: [N/N healthy] | 异常: [list or 无]"
```

## Known Issues Reference

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| Router stall threshold=0 display | Display bug, actual=1800s | No action needed |
| Router respawn flapping | lark-cli subscribe idle timeout 600s | Increase threshold (done: 1800s) |
| PID file stale | Process killed without cleanup | worker_builder removes stale pidfile |
| auth_failure false positive | `deliver.py` markers matched `gh auth login` footer | watchdog.py already fixed, deliver.py pending |

## Anti-Patterns

- **Don't** check daemon health via `ps aux` only — always cross-reference with pidfile and `eduflow health`
- **Don't** report "daemon dead" without checking if it was intentionally stopped
- **Don't** reset watchdog respawn counter without logging why
