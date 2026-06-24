---
name: workflow-recovery-patterns
description: Recovery patterns for common failure modes during sprint execution. Use when worker crashes, reviews stall, files mismatch, or cadence breaks.
metadata:
  type: experience
  generated_by: manager
  date: 2026-06-22
---

# Workflow Recovery Patterns

## Failure 1: worker_course context exceeds limit

**Symptom**: API Error 400 invalid params, context window exceeds limit (2013)

**Recovery**:
1. worker_course crashes mid-batch
2. Dispatch worker_builder: "重启 worker_course pane，确认 files 已保存"
3. worker_builder uses tmux to restart pane
4. Files preserved on disk, in-context state lost
5. worker_course resumes from where files were saved

**Prevention**:
- Batch ≤5 topics per cycle
- Use Python scripts for batch operations (lower context than CLI Edit)
- Send compression hints when context >85%

## Failure 2: review_course stale evidence

**Symptom**: review_course verdict based on outdated file scan, doesn't match current file

**Recovery**:
1. Manager: peek review_course pane for actual content
2. If mismatch: re-send file evidence (timestamps, diff)
3. Manager can re-trigger review after evidence updates

**Example (0478 T-31)**:
- review_course initially said 31 errors
- After Math T3 + fixes: 0 errors
- Manager: re-verify with file evidence

## Failure 3: Worker lazy mode (Luke_recorder issue)

**Symptom**: agent has "lazy: CLI starts on first message" but messages don't reach inbox

**Recovery**:
1. Manager tries send → agent shows "inbox empty"
2. Cannot directly trigger CLI start
3. **Plan B**: manager executes the work themselves, marks as such
4. Document this in skill as lesson learned

## Failure 4: Worker self-proclaimed completion without verification

**Symptom**: worker_course says "100 topics done" but file shows only 50

**Recovery**:
1. Manager: count files independently (Python count of items/QQL)
2. Cross-reference with worker report
3. If mismatch: send clarification, request diff
4. Do NOT trust report alone

## Failure 5: Manifest out of sync after expansion

**Symptom**: items added but qa-manifest.csv unchanged

**Recovery**:
1. worker_builder: Python script to regenerate manifest from items/ directory
2. Verify row count matches items count
3. re-send review_course for final verification

## Cadence Patterns

### 5-min cadence after dispatch

```bash
# Every 5 min while task active:
1. inbox manager (new messages?)
2. peek worker_<role> (pane status)
3. If progress → log it
4. If stuck → diagnose
5. say group (5-min progress report, even if no change)
6. ScheduleWakeup 300s
```

### When to break cadence

- Task ACCEPT verdict → switch to verify + closeout (no more cadence)
- Boss confirms "stop" → terminate cadence loop
- Agent needs >30min work → still cadence, longer reports

## Escalation

- worker fails 3 times → escalate to worker_builder for infra
- review fails 3 times → escalate to boss for scope decision
- qbank fails 3 times → escalate to boss for technical decision
