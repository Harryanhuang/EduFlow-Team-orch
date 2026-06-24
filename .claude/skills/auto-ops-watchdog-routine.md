---
name: auto-ops-watchdog-routine
description: Structured auto-ops daily/watchdog routine for monitoring agent health, daemon status, and issue escalation. Use when auto_ops wakes for routine patrol or is triggered by a watchdog event.
metadata:
  type: workflow
  generated_by: auto_ops
  date: 2026-06-24
  source: auto_ops recurring patrol pattern distilled from 50+ patrol cycles
---

# Auto-ops Watchdog Routine

## Use When

- auto_ops receives `继续之前未完成的工作；如已完成则确认并待命。`
- watchdog triggers a stall/health event
- Boss/manager requests team status report

## Routine Checklist

Run this sequence on every patrol wake. Skip only steps that are clearly redundant with the current state (e.g., if you just checked 30 seconds ago).

### Step 1: Inbox Scan

```bash
eduflow inbox auto_ops
```

- For each unread message: process per identity rules (ACK → execute → report)
- If inbox empty: proceed to Step 2

### Step 2: Daemon Health

```bash
claudeteam health
```

Check:
- `router`: alive/stable, stall reason, respawn count
- `watchdog`: alive
- `task-publish`: alive
- `hermes-supervisor`: running or not (config-consistent)

Record anomalies. If respawn count is climbing (>5 in 24h), flag root cause.

### Step 3: Agent Panel (tmux)

```bash
tmux list-windows -t EduFlowTeam
```

For each active agent pane:
- Capture bottom 30 lines: `tmux capture-pane -t EduFlowTeam:<agent> -p | tail -30`
- Look for: API errors, crash loops, stuck prompts ("> 5 min no output on active task), provider_unavailable
- Check `claudeteam team` for status lag between runtime guard and actual pane state

### Step 4: Per-Agent Status

```bash
claudeteam team
```

For each agent compare:
- `claudeteam team` status label vs actual pane state
- If mismatch > 10 min: flag as "status lag" and recommend runtime guard reset

### Step 5: Issue Ledger Check

```bash
cat .eduflow-team-state/issue_ledger.md
```

- Review unresolved items
- Check if any "进行中" items are stale (>2h with no update)
- Update resolved items

### Step 6: Report

Post to manager if:
- Any red/yellow health item
- Any agent crashed or stuck
- Respawn rate elevated
- New issue found or old issue stale

Format:

```bash
eduflow send manager auto_ops "巡检报告：daemon [状态] | agents [N/N healthy] | 发现 [异常项] | 建议 [动作]"
```

If all clean: post brief confirmation or skip (don't spam when healthy).

### Step 7: Status Update

```bash
eduflow status auto_ops 待命 "巡检完成：[一句话 summary]"
```

## Watchdog Event Response

When triggered by watchdog (not routine):

1. Immediately capture the affected pane state
2. Check daemon health
3. If daemon dead: report to manager, recommend respawn
4. If agent stuck: check provider, API key, context limit
5. If provider issue: follow `provider-failover-protocol` skill
6. Report within 2 minutes of trigger

## Anti-Patterns

- **Don't** spam group chat with routine "all clean" reports — silent is fine
- **Don't** run tmux capture in a tight loop — 30s minimum between checks
- **Don't** report stale pane state as current — always capture fresh
- **Don't** skip issue ledger updates — the ledger is the source of truth for historical issues

## Cadence

| Mode | Interval | Scope |
|------|----------|-------|
| Routine patrol | 5-10 min | Full 7-step |
| Watchdog trigger | Immediate | Steps 1-3, report |
| Boss request | On demand | Full + extra detail |
