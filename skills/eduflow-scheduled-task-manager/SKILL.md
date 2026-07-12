---
name: eduflow-scheduled-task-manager
description: Create and manage EduFlow D-ID scheduled tasks (recurring daily / weekly / once rules). Use when the user asks to schedule, remind, or automate any work in the main Feishu/Lark chat. The router only forwards the user message and detected language to this skill — this skill is the only entry that may call the P4 manager_ops APIs (`create_draft_rule`, `confirm_draft_rule`, `pause_rule`, `resume_rule`, `cancel_rule`). Never guess times and never mutate the scheduler store directly.
---

# EduFlow Scheduled Task Manager (D-ID)

This skill is the **only** path that turns a user's natural-language
request into a D scheduled task.  The router (`feishu/router.py`)
already attached two tags to the Decision object so the manager agent
can use them:

- `decision.user_language` — `"zh-CN"` or `"en-US"`, cached per
  `sender_id` across messages.
- `decision.schedule_intent` — `True` if the text matched obvious
  schedule keywords (`schedule / recurring / daily / weekly / reminder`
  or `定时 / 日程 / 周期 / 每周 / 每天 / 提醒 / 周报`).

The router never parses times.  The skill must:

1. Build a structured draft from the user's text (or ask back for
   anything fuzzy).
2. Show a due confirmation packet and wait for explicit user approval.
3. After confirmation, call `manager_ops.create_draft_rule(...)` then
   `manager_ops.confirm_draft_rule(...)` (P4).  For pause / resume /
   cancel echo the D ID and the action; then call the matching
   `manager_ops.pause_rule / resume_rule / cancel_rule`.

## Required fields

Every draft must contain these six fields before it can be turned into
a rule:

| Field             | Meaning                                                       |
| ----------------- | ------------------------------------------------------------- |
| `target`          | Short noun phrase of what the rule is about                   |
| `artifact`        | Concrete deliverable path / filename (e.g. `weekly-report.md`)|
| `frequency`       | One of `once` / `daily` / `weekly`                            |
| `timezone`        | IANA name, defaults to `Asia/Shanghai`                        |
| `due time`        | Local date (for `once`) and/or `HH:MM` time (for daily/weekly)|
| `suggested agent` | Worker name that owns the lane (e.g. `worker_cc`)             |

If any field is missing or fuzzy, **ask the user back** before
constructing the draft.  Do not invent values.

## Clarification policy — fuzzy time markers

The following markers are **always ambiguous**.  When the user uses
them, the skill MUST ask back with the closest concrete alternatives
instead of guessing:

- `下周` — which Monday-Sunday in the user's timezone?
- `周末` — Saturday, Sunday, or the whole weekend?  Which time?
- `下午` — what clock time?
- `每隔一段时间` — explicit interval (`every 30 minutes`)?  Not supported; ask back.
- `明天` / `后天` — explicit date (`2026-07-13`) and time?
- `每周 X` — confirm weekday name and time.
- `上午` / `中午` / `晚上` — what clock time?
- `早上` / `今晚` — what clock time?

The plan forbids `parse_schedule` from resolving these markers.  The
skill must surface a clarification question before any P4 call.

## Flow: natural language → draft → user confirmation → P4 API

1. Receive `decision.text`.  Extract the six required fields; for any
   field that is fuzzy, ask back using the language in
   `decision.user_language`.  Keep clarification rounds short.
2. Build a draft object:

   ```text
   DRAFT (pending D-id):
     target          : <noun phrase>
     artifact        : <path>
     frequency       : once|daily|weekly
     timezone        : <IANA TZ>
     due             : <YYYY-MM-DD HH:MM in TZ>  (≈ <UTC ISO>)
     suggested agent : <worker name>
   Confirm?  (yes / edit <field> / cancel)
   ```

3. **Do not call P4 until the user explicitly says `yes` / `确认` /
   `好` / `确认这个` / similar positive confirmation.**  Treat silence,
   emoji-only replies, and follow-up questions as non-confirmation.
4. After confirmation, call P4 in this exact order so the rule version
   is bound to the user who confirmed:

   ```python
   rule_id = manager_ops.create_draft_rule(
       target=target,
       artifact=artifact,
       frequency=frequency,
       timezone=timezone,
       next_due_utc=next_due_utc_iso,    # already converted to UTC
       created_by="user",
   )
   manager_ops.confirm_draft_rule(
       rule_id,
       actor="user",
       actor_role="user",
       expected_version=1,                # version after create_draft_rule
   )
   ```

5. Echo the assigned D-ID back to the user (e.g. `已创建并激活 D-12`).

## Pause / resume / cancel

These three verbs map 1:1 to `manager_ops.pause_rule` /
`resume_rule` / `cancel_rule`.  Echo format:

- `已暂停 D-12`
- `已恢复 D-12`
- `已取消 D-12`

Always echo the D-ID and the action.  Never write the scheduler store
directly; always call the P4 function so version checks and audit
metadata (`paused_by`, `cancelled_at`) are recorded.

## Authorization

Only the roles listed below may perform the matching operation.  P4
already enforces this and raises `AuthorizationError` otherwise; the
skill MUST pass `actor` and `actor_role` exactly.

| Role      | Allowed operations                                                       |
| --------- | ------------------------------------------------------------------------ |
| `user`    | Create draft for self, confirm own draft, pause/resume/cancel own rule  |
| `manager` | Confirm any draft, pause/resume/cancel any rule, confirm/skipped/dispatch occurrences, add lanes |
| `worker`  | Report back on a lane (`report_back`); nothing else                      |

Workers **cannot** modify the rule, pause, resume, or cancel.  They
also cannot dispatch or skip an occurrence.  Do not impersonate
another role in P4 calls.

## Notification cadence (for awareness)

P5 forbids tick / wait spam.  The scheduler only emits notifications
for these four event kinds:

- `create`             — emitted by P3 engine when an occurrence
                          first becomes `awaiting_manager`
- `supplement_confirm` — emitted by this skill when the user
                          supplements or confirms a draft
- `occurrence_started` — emitted by P4 manager_ops when an
                          occurrence is dispatched (status → running)
- `result_or_failure`  — emitted by P4 manager_ops when a worker
                          reports done / failed on a lane

While an occurrence stays in `awaiting_manager`, the cadence applies:

- **manager reminder** — at most one per occurrence every **30 minutes**
- **user notification** — at most one per occurrence every **2 hours**

Do not invent intermediate reminders.  Do not page on every tick.  When
answering the user about a waiting occurrence, reference the existing
ledger (`notifications.jsonl`) rather than firing a new one.

## Router contract (do not bypass)

- The router only forwards `decision.text`, `decision.user_language`,
  `decision.schedule_intent`, `decision.msg_id`, `decision.sender_id`.
- It MUST NOT call `eduflow.store.scheduled_tasks` directly.  The router
  must not guess times and must not write any D rule / occurrence /
  lane.  This is enforced by `tests/unit/test_scheduled_router.py`.
- This skill must therefore never "auto-create" rules from a chat
  message without an explicit user confirmation step.

## References (P4 API surface)

This skill invokes the deterministic P4 module
`eduflow.scheduling.manager_ops`.  Do not call the store layer directly.

- `create_draft_rule(target, artifact, frequency, timezone,
  next_due_utc, capacity=1, created_by="user") -> str` returns `D-N`.
- `confirm_draft_rule(rule_id, actor, actor_role, expected_version) -> dict`.
- `pause_rule(rule_id, actor, actor_role, expected_version) -> dict`.
- `resume_rule(rule_id, actor, actor_role, expected_version) -> dict`.
- `cancel_rule(rule_id, actor, actor_role, expected_version) -> dict`.
- For occurrence-level ops (confirm / skip / dispatch / fail-pause /
  report), the skill delegates to the P4 functions with the same
  names; the router/skill is not in the dispatch hot-path.

## Failure / fallback

- If `manager_ops` raises `AuthorizationError`, tell the user the
  operation is not allowed and which role would be required.
- If `manager_ops` raises `VersionConflict`, re-read the rule via
  `scheduled_tasks.get_rule(rule_id)` and re-show the due confirmation
  packet so the user can re-confirm against the new version.
- If the user-visible language is ambiguous (e.g. mixed CN/EN lines),
  prefer the cached `decision.user_language` from the session state.
- Never silently drop a request; always echo either the D-ID + action
  (success) or the specific missing field (clarification needed).