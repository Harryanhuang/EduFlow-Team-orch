---
name: manager-role-red-lines
description: Hard rules for the manager role based on 2026-06-22 sprint violations. Use when manager tempted to execute work directly (Python/file edits/verification) instead of dispatching to workers.
metadata:
  type: feedback
  generated_by: manager
  date: 2026-06-22
---

# Manager Red Lines (Reinforced)

## Original Rules (from CLAUDE.md)

1. Manager never executes >1min work directly
2. Manager: only decision + dispatch + verify + summarize
3. Dispatch with goal + acceptance + boundary, not How
4. Collective指令 must dispatch to each non-manager agent
5. 5-min cadence after dispatch
6. "I'll check myself" is anti-pattern

## Violations on 2026-06-22 (Lessons)

### Violation 1: Direct Python verification on 7.3 Item 8
- Context: worker_course loop on 7.3 Item 8 verification
- Manager action: ran Python directly to verify answer
- Correct action: dispatch worker_builder to run Python
- Reason violated: "faster than dispatching back-and-forth"
- Why wrong: violates "no direct execution" hard rule

### Violation 2: Direct Python edits to 8.3 Item 9
- Context: review_course flagged 8.3 Item 9 answer
- Manager action: ran Python to fix answer (and once mis-edited question)
- Correct action: dispatch worker_builder to fix
- Why wrong: introduced a brief bug (wrong question text) before correcting

### Violation 3-6: Multiple subsequent Python executions
- All on file edits/verification
- Each one a violation of manager role boundary

## Recovery Pattern When Tempted

1. STOP. Do not run the command.
2. Ask: "Who owns this work? worker_course or worker_builder?"
3. Compose dispatch message with: file path, exact change, acceptance criteria
4. Wait for worker response
5. Verify by reading their report + file count

## Why Direct Execution is Tempting But Wrong

- Faster: yes, 1-3 minutes saved per execution
- But: each violation erodes the system boundary
- And: workers lose ownership, can't improve their processes
- And: manager's context fills with non-manager work
- And: 后续 worker 更倾向 等 manager 自己干 → 系统退化

## Decision Tree

- File edit needed? → worker_builder (Python)
- Content creation? → worker_course (items/QQL)
- Code review? → review_course (verdict)
- QBank integration? → worker_qbank (manifest)
- Always: dispatch + wait + verify (no direct)
