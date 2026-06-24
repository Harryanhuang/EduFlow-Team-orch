---
name: context-overflow-recovery
description: SOP for handling agent context window overflow (when context window exceeds limit, 100% context used, /clear to save NNN tokens). Use when any agent pane shows context exhaustion markers or stops producing for >5 min while context >300k tokens.
metadata:
  type: workflow
  generated_by: worker_builder
  date: 2026-06-24
  source: T-47 AP Physics 2 incident 2026-06-24 (worker_course 433.2k tokens, manual recovery)
---

# Context Overflow Recovery Protocol

## Why This Exists

Claude Code agents accumulate context from file reads, bash output, and tool
calls. At ~300k+ tokens (varies by model), the pane shows `context window
exceeds limit` or `100% context used` markers. At 433k+ tokens Claude Code
displays `new task? /clear to save NNN tokens` and the agent becomes idle,
waiting for human input.

**Without intervention, the agent stays idle until manually triggered.**

`worker_course` 2026-06-24 hit 433.2k tokens mid-T-47 AP Physics 2 production
(12/42 U15 Quantum items done, 30 remaining). Manual recovery in 14 minutes
validated this protocol.

## When to Use

| Symptom | Action |
|---------|--------|
| `eduflow health` shows `context_exhausted` for an agent | Run recovery |
| Agent idle >5min during active task + last 20 lines contain `new task?` or `/clear to save` | Run recovery |
| Agent pane contains `context window exceeds limit` / `100% context used` markers | Run recovery |
| Agent dropped to `✻ Compacting` then became idle | Already mid-compact; just nudge |
| Auto-flag from watchdog | Watchdog auto-runs this protocol |

## DO NOT Use

- If agent is actively producing (writing files, `✻ Crunched` for <5min) — let it finish
- If agent just started a task (context <100k) — not yet a problem
- If `eduflow health` shows `context_exhausted` but agent's most recent output is `Wrote N lines to ...` within last 2 minutes — agent already recovered itself

## Recovery Steps

### Step 1: Diagnose (≤30s)

```bash
eduflow peek <agent> 50 | tail -40
```

Look for:
- `new task? /clear to save NNN tokens` → context full, recovery needed
- `context window exceeds limit` → context full
- `100% context used` → context full
- `Compacting` / `Compacted` → already in compaction, wait

### Step 2: Check on-disk state (≤30s)

Verify progress is preserved on disk:

```bash
# For AP tasks:
find ./content/<subject>/subtopics -name "*.md" -not -name "QA-*" 2>/dev/null | wc -l

# For IGCSE tasks:
find ./content/<subject>/items -name "*.md" 2>/dev/null | wc -l

# Compare to last reported count in pane ("12/42 items done" etc.)
```

If on-disk count ≥ pane-reported count, the agent's "stuck" state is just
a trigger issue — proceed with Step 3.

### Step 3: Trigger recovery (≤2min)

**Preferred method — auto via watchdog** (recommended):
Watchdog checks `_pane_context_exhausted()` every health tick. When detected:
1. Snapshot current pane state
2. Run `eduflow reidentify <agent>` to re-inject identity init
3. Inject: `Run \`/compact\` to reduce context, then \`eduflow inbox <agent>\` to continue. Do NOT use /clear unless /compact fails.`

**Manual fallback** (when watchdog is paused or unavailable):

```bash
# Step 3a: send recovery instruction via inbox (router will inject to pane)
eduflow send <agent> worker_builder "context 超限恢复：先运行 /compact（不要 /clear），然后跑 eduflow inbox <agent> 读最新未读消息，按消息内容继续当前 task。已落盘的 items 不受影响。" 高

# Step 3b: if no response in 60s, force reidentify
eduflow reidentify <agent>
```

### Step 4: Verify recovery (≤5min)

```bash
# Watch pane activity
eduflow peek <agent> 20  # every 30s

# Confirm item count increases
# (for AP tasks)
find ./content/<subject>/subtopics -name "*.md" -not -name "QA-*" 2>/dev/null | wc -l
```

If pane shows `Compacting...` then `Compacted` then resumes file writes, recovery succeeded.

If pane stays idle 5+ minutes after injection, escalate to:
```bash
eduflow send manager worker_builder "context recovery failed for <agent>: 注入后 5min 无响应，需要人工 /clear" 高
```

## Why `/compact` not `/clear`

`/compact` compresses the conversation history while preserving task context:
- In-progress task state survives
- Files just written remain in context
- Skill paths learned remain
- Compaction summary Claude Code generates usually preserves constraints

`/clear` wipes everything:
- Loses in-context knowledge of the syllabus
- Loses nuance from already-written items
- Forces complete re-read of disk state
- Loses task progress narrative
- Worker needs `reidentify` to remember who it is

**When to use `/clear` despite the cost:**
- `/compact` failed (still context full after compact)
- Agent stuck in confused state (wrong task, repeating self)
- Operator-initiated reset (rare)

## Preventive Measures (apply at task start)

For long-running production tasks (>30min, expected >200 items):

1. **Tell agent in dispatch** to `/compact` proactively every 5 subtopics
2. **Memory packet prepend** is automatic via `eduflow send` (see `send.py:72`)
3. **Checkpoint task state**: agent should write "completed: 12/42" to a status file after each subtopic, so even if context is lost, `/compact` can rebuild from disk
4. **Batch by `worker-course-production-checklist` 5-topic limit** — never ask agent to do >5 subtopics without checkpoint

## Integration with Watchdog

The watchdog should add this auto-recovery to its main loop. Pseudocode:

```python
# In commands/watchdog.py main loop:
pane_text = tmux.capture_pane(target, lines=80)
if _pane_context_exhausted(pane_text) and "new task?" in pane_text:
    log(f"⚠️  {agent}: context exhausted, auto-recovering")
    # 1. snapshot disk state for the operator
    snap = snapshot_progress(agent)
    log(f"   snapshot: {snap}")
    # 2. inject recovery instruction (NOT /clear)
    tmux.inject(target,
        "Run `/compact` (NOT /clear), then `eduflow inbox <agent>` and continue. "
        "Disk state preserved.",
        submit_keys=adapter.submit_keys())
```

This auto-path was demonstrated manually on 2026-06-24 with T-47
(12 → 42 → 276 items in 14 minutes via inbox trigger, no /clear needed).

## Related

- `workflow-recovery-patterns` — broader recovery patterns
- `provider-failover-protocol` — for runtime/provider issues (different from context)
- `worker-course-production-checklist` — 5-topic batch limit prevents context overflow
- `reidentify` (CLI) — `/compact` recovery tool
