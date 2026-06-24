---
name: skill-orchestration-guide
description: Master routing matrix for .claude/skills/ — which agent calls which skills, in what order, and how to resolve conflicts when two skills disagree. Every agent must consult this guide before calling any skill.
metadata:
  type: reference
  generated_by: worker_builder
  date: 2026-06-24
  source: 34-skill audit + boss directive 2026-06-24
---

# Skill Orchestration Guide

## Purpose

This document answers three questions for every agent at task start:
1. **Which skills** should I call for this task?
2. **In what order** do I call them?
3. **What do I do** when two skills give conflicting advice?

---

## Conflict Resolution Rules (Read Before All Else)

| Rule | Meaning |
|------|---------|
| **Specificity wins** | `ap-item-production` beats `item-format-spec` when working on AP; `igcse-qbank-verification` beats `qbank-lifecycle-gates` when verifying IGCSE |
| **Execution-point wins** | The skill closest to the actual `eduflow` command you're about to run is authoritative. If `worker-course-production-checklist` says batch size = 5 and `c-class-expansion-workflow` says 10, use 5 for standard batches, 10 only for C-class expansion |
| **Code beats prose** | If a skill's CLI command doesn't match `src/eduflow/commands/`, use the real CLI. The `item-format-spec` and `ap-review-playbook` schemas are canonical (verified against `ap_subject_verifier.py`); older skills referencing "12 fields" are superseded |
| **Producer decides on own output** | `worker-course-production-checklist` is the final authority on whether YOUR batch is ready to submit. Don't wait for review_course to catch something the checklist should have caught |
| **review_course decides on review** | `review-course-file-evidence-playbook`, `ap-review-playbook`, and `review-criteria` are all inputs; `review-verdict` is the only skill that determines what verdict you issue |
| **Escalate on true ambiguity** | If two skills genuinely contradict on a non-obvious point and none of the above rules apply: `eduflow send manager <agent> "skill 冲突：[skill A] says X, [skill B] says Y，请裁定" 高` |

---

## Agent Routing Matrix

### worker_course

**Core skills (always in order):**

```
1. worker-ack-task          ← every task, no exceptions
2. brainstorming             ← after ACK, before any production
   (lightweight if task is clear; full if ambiguous)
3. [production skill]       ← see scenario table below
4. worker-course-production-checklist ← after every batch, before submit
5. tone-scan-pre-review     ← after checklist, before submit
6. submit-to-review         ← send to review_course, not to manager
```

**Scenario → production skill:**

| Task type | Production skill(s) | Notes |
|-----------|-------------------|-------|
| IGCSE new subject (outline/seed) | `igcse-subject-dispatch` (manager) → brainstorming → free production | No specific item skill needed at outline stage |
| IGCSE item production | `item-format-spec` + `c-class-expansion-workflow` (if >50 items) | item-format-spec for structure; c-class if expanding a C-class subject |
| IGCSE manifest | `manifest-generation` | Run AFTER items are produced, not before |
| AP item production | `ap-item-production` | Follow the 15-key YAML frontmatter exactly |
| AP QA selfcheck | `ap-qa-selfcheck` | Template must end with `本 Unit 状态：**完成**` (NOT `submitted_for_review`) |
| AP manifest sync | `ap-manifest-sync` | After items; verify `data_rows × 3 = file_count` |
| AP content pitfalls | `ap-content-production-pitfalls` | Read BEFORE starting, not after failing |
| Tone scan (all) | `tone-scan-pre-review` | Always run; never skip |

**Do NOT call:** `review-verdict`, `check-closeout`, `review-course-file-evidence-playbook` (these are review_course/manager skills)

---

### review_course

**Core skills (always in order):**

```
1. worker-ack-task                  ← every task
2. [review skill]                   ← see scenario table
3. review-course-file-evidence-playbook ← before issuing verdict
4. review-verdict                   ← issue the verdict (authoritative)
5. (if item prototype) → send to worker_builder for template extraction
```

**Scenario → review skill:**

| Review target | Primary skill | Also consult |
|---------------|--------------|--------------|
| IGCSE items (from worker_course) | `review-criteria` | `item-format-spec` for field check |
| IGCSE full subject artifacts | `review-criteria` | `igcse-qbank-verification` for count consistency |
| AP items (from worker_course) | `ap-review-playbook` | `ap-qbank-verification` for verifier output |
| Item-level prototype (from worker_qbank) | `item-prototype-check` | Bounded scope only; don't expand review |
| Any content | `tone-scan-pre-review` can be run by review_course too | As a secondary check |

**Verdict vocabulary (canonical):** `pass`, `approved`, `minor_required`, `reject`, `conditional_pass`
- Never use `quality_not_met` or `blocked` (legacy from `review-criteria.md`, now fixed)

**Do NOT call:** `brainstorming`, `ap-item-production`, `item-format-spec` as production tools (these are worker_course tools)

---

### worker_builder

**Core skills:**

```
1. worker-ack-task                          ← every task
2. [fix/maintenance skill]                  ← see scenario table
3. provider-failover-protocol               ← when runtime/provider issues
4. daemon-health-check                      ← when daemon health is in scope
5. workflow-recovery-patterns               ← when recovering from failures
```

**Scenario → skill:**

| Task type | Skill(s) |
|-----------|----------|
| Provider failover / runtime issue | `provider-failover-protocol` (use `eduflow runtime switch`, NOT `claudeteam set-runtime`) |
| Template extraction (from review_course verdict) | Free production — read the review verdict, deposit template to workflow assets |
| Daemon issue (router/watchdog) | `daemon-health-check` |
| Sprint failure recovery | `workflow-recovery-patterns` + `igcse-9subject-sprint-lessons` |
| Skill writing / orchestration | This guide (`skill-orchestration-guide`) + brainstorming |
| Any runtime CLI | Use real `eduflow` CLI (check USAGE in `src/eduflow/commands/` if unsure) |

**Do NOT call:** `review-verdict`, `ap-item-production`, `check-closeout` (not your role)

---

### worker_qbank

**Core skills:**

```
1. worker-ack-task                  ← every task
2. [verification skill]             ← see scenario table
3. qbank-lifecycle-gates            ← to derive current lifecycle state
4. qbank-validation-patterns        ← before any verification run
5. submit-to-review                 ← send to review_course
```

**Scenario → verification skill:**

| Task type | Verification skill |
|-----------|-------------------|
| IGCSE QBank verify/scan | `igcse-qbank-verification` (use `scripts/qbank_verify.py`) |
| AP QBank verify | `ap-qbank-verification` (use `scripts/ap_qbank_verify.py`) |
| Schema reference | `qbank-ap-vs-igcse-schema` |
| Dedup before import | `qbank-dedup-content-hash` |
| Unified manifest integration | `qbank-unified-manifest-integration` |

**Critical gate:** Import/dedup requires two keys: `review_course_pass` AND `user/manager_auth`. Never bypass this.

**Do NOT call:** `ap-item-production`, `ap-qa-selfcheck` (worker_course tools), `review-verdict` (review_course tool)

---

### manager

**Core skills (decision and gate skills only):**

```
1. manager-role-red-lines           ← read at session start (always)
2. [dispatch skill]                 ← see scenario table
3. check-closeout                   ← BEFORE any manager-closeout
4. multi-agent-collaboration        ← when coordinating parallel workers
5. provider-failover-protocol       ← when escalating provider issues
```

**Scenario → dispatch/gate skill:**

| Task type | Skill(s) |
|-----------|----------|
| Launch new IGCSE subject | `igcse-subject-dispatch` |
| Close out a subject | `check-closeout` (run ALL gates before announcing) |
| Item prototype expansion decision | `item-prototype-check` (review_course's verdict input) + free decision |
| Parallel worker coordination | `multi-agent-collaboration` (check task list, not "subject lock") |
| Sprint management | `igcse-9subject-sprint-lessons` + `c-class-expansion-workflow` |
| Skill writing | This guide |

**Hard boundary:** manager does NOT produce, repair, or verify content. If tempted, re-read `manager-role-red-lines`.

---

### auto_ops

**Core skills:**

```
1. auto-ops-watchdog-routine        ← daily monitoring routine
2. daemon-health-check              ← daemon status verification
3. provider-failover-protocol       ← when diagnosing provider issues
4. workflow-recovery-patterns       ← when recovering failed workflows
```

**Auto_ops does NOT call:** production skills, review skills, or dispatch skills. Its role is monitoring and escalation only.

---

## Scenario Walkthroughs

### Scenario A: worker_course receives AP Physics 2 item production task

```
1. worker-ack-task          → ACK + notify user + set status 进行中
2. brainstorming            → lightweight preflight (goal, scope, files, constraints)
3. ap-content-production-pitfalls → review known AP pitfalls BEFORE starting
4. ap-item-production       → follow the 15-key YAML template exactly
   (loop per subtopic: produce 3 items F/S/C)
5. worker-course-production-checklist → after each batch of 5 subtopics
6. ap-qa-selfcheck          → after all items produced, write QA-自检.md
   (status line MUST be: 本 Unit 状态：**完成**)
7. tone-scan-pre-review     → run inline Python, verify 0 tone artifacts
8. submit-to-review         → send to review_course with file list
```

### Scenario B: review_course reviews IGCSE subject artifacts

```
1. worker-ack-task          → ACK
2. review-criteria          → review against checklist (coverage, difficulty, errors, duplicates, format)
3. review-course-file-evidence-playbook → sample 5 topics × 3 items, record evidence
4. item-format-spec         → validate field presence in sampled items
5. igcse-qbank-verification → if count consistency is in scope
6. review-verdict           → issue structured verdict with scope declaration
   → send to manager (NOT to worker_course directly for closeout)
```

### Scenario C: manager closes out IGCSE subject

```
1. manager-role-red-lines   → confirm not crossing into production
2. check-closeout           → run ALL gates:
   a. supervisor-check      → verify review verdict is authoritative PASS
   b. artifact consistency  → qql_count == manifest; items_count <= qql_count
   c. revision-first check  → no open revision_priority
   d. worker context guard  → no context_exhausted or ready_unproven
   e. evidence packet       → all required fields present
   f. scope match           → verdict_scope == full_subject for subject closeout
3. ONLY if ALL gates pass → eduflow task manager-closeout <id> --actor manager
```

### Scenario D: worker_qbank verifies IGCSE QBank

```
1. worker-ack-task          → ACK
2. qbank-validation-patterns → pre-check common errors
3. igcse-qbank-verification → run scripts/qbank_verify.py
4. qbank-lifecycle-gates    → derive lifecycle state from verification output
5. (if ready_for_import) → request user/manager authorization (two-key gate)
6. submit-to-review         → if review is needed before import
```

---

## Cross-Reference: Skill Conflicts Resolved

| Conflict | Resolution |
|----------|-----------|
| `review-criteria` says verdict `approved`/`quality_not_met`/`blocked` vs `review-verdict` says `pass`/`minor_required`/`reject` | Use `review-verdict` vocabulary (canonical, aligned with CLI) |
| `ap-qa-selfcheck` template ends with `submitted_for_review` vs `ap_subject_verifier.py` expects `本 Unit 状态：**完成**` | Use `本 Unit 状态：**完成**` (verified against code) |
| `ap-review-playbook` Step 3 lists 12 fields vs `ap-item-production` lists 15 frontmatter keys | 15 keys is correct (verified against `ap_subject_verifier._REQUIRED_FRONTMATTER_KEYS`) |
| `c-class-expansion-workflow` says batch = 10 vs `worker-course-production-checklist` says batch = 5 | Use 5 for standard; 10 only for C-class expansion phase |
| `igcse-qbank-verification` Step 1 has no script path vs `qbank-ap-vs-igcse-schema` names `scripts/qbank_verify.py` | Use `scripts/qbank_verify.py` (verified to exist) |
| `manifest-generation` topic_id parsing vs actual filename convention | Use `topic_N_M.md` → `"N.M"` via split+join (fixed) |
| `provider-failover-protocol` anti-pattern references `claudeteam set-runtime` | Use `eduflow runtime switch` (fixed) |
| `multi-agent-collaboration` references undefined "subject 锁" | Use `eduflow task list --assignee <agent>` to check active tasks per agent (fixed) |

---

## Quick Lookup: Which Skill For Which CLI Command

| CLI Command | Primary Skill | Also See |
|-------------|--------------|----------|
| `eduflow inbox <agent>` | `worker-ack-task` | — |
| `eduflow read <id> --ack ...` | `worker-ack-task` | — |
| `eduflow say <agent> "..." --to ...` | `worker-ack-task` | — |
| `eduflow status <agent> ...` | `worker-ack-task` | — |
| `eduflow send manager <agent> "..."` | `submit-to-review` / `review-verdict` | — |
| `eduflow task dispatch ...` | `igcse-subject-dispatch` | — |
| `eduflow task supervisor-check` | `check-closeout` | — |
| `eduflow task manager-closeout <id> --actor manager` | `check-closeout` | — |
| `eduflow task review-queue --stage ...` | `multi-agent-collaboration` | — |
| `eduflow runtime switch <agent> <rt>` | `provider-failover-protocol` | — |
| `eduflow health` | `daemon-health-check` | `auto-ops-watchdog-routine` |
| `scripts/qbank_verify.py` | `igcse-qbank-verification` | `qbank-lifecycle-gates` |
| `scripts/ap_qbank_verify.py` | `ap-qbank-verification` | `qbank-lifecycle-gates` |

---

## Maintenance

This guide is updated by `worker_builder` when:
- A new skill is added to `.claude/skills/`
- A skill conflict is discovered and resolved
- A new agent role is added to the team

Do NOT edit this file from other agent roles — propose changes via `eduflow send worker_builder` or `eduflow send manager`.
