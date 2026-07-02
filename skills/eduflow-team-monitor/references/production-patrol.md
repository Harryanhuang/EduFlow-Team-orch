# Production Patrol Reference

Use this when auto_ops monitors what the EduFlow agents are producing, not just
whether their context is safe.

## Primary Commands

Run these every patrol:

```bash
./scripts/eduflowteam team --json
./scripts/eduflowteam task auto-ops-production --send-manager
./scripts/eduflowteam inbox manager
```

`auto-ops-production` is the first structured data source. It reads local
status, heartbeats, high-priority unread inbox, runtime guard state, and
manager task buckets, then prints/sends a compact `auto_ops production
snapshot`.

Run these when ownership, review, or completion is unclear:

```bash
./scripts/eduflowteam task manager-overview
./scripts/eduflowteam task supervisor-check --json
./scripts/eduflowteam task review-queue --reviewer review_course
tail -n 120 .eduflow-team-state/facts/logs.jsonl
```

## What Auto_ops Must Track

- `manager`: is it consuming user/worker messages and dispatching, or waiting.
- `worker_course`: current course/content production line and latest handoff.
- `review_course`: current review queue, verdict status, or waiting state.
- `worker_syllabus`: active syllabus/assessment skill work and unread tasks.
- `worker_builder`: runtime/build repair state and escalation flags.
- `worker_qbank`: qbank scan/import/fix state.
- `Hermes` / `Luke_recorder`: knowledge/recording tasks and stale visibility.
- Any fired/lazy/unknown agent that still appears in status output.

## Production State Classes

| State | Meaning | Manager-facing action |
| --- | --- | --- |
| `active` | Agent is working and recently updated status/heartbeat | no_action unless blocked |
| `waiting_review` | Production submitted but reviewer queue/verdict pending | ask manager to assign or nudge review_course |
| `waiting_manager` | Worker/reviewer reported result; manager has unread or no closeout | ask manager to consume exact message id |
| `waiting_worker` | Manager dispatched but worker has unread or no ACK | ask manager to nudge/reinject or verify pane |
| `blocked` | Agent reports blocker or runtime guard escalation | ask manager to route repair or decide |
| `stale` | Status/heartbeat old for an active task | ask manager/auto_ops to peek pane and report |
| `idle` | No unread, no active task, no recent blocker | no_action |

## Production Snapshot Format

Auto_ops should send manager a compact report like:

```text
auto_ops production snapshot
active=<N> blocked=<N> waiting_manager=<N> waiting_review=<N> stale=<N>
- manager: state=<state> task=<short task> next=<action/no_action>
- worker_course: state=<state> task=<short task> next=<action/no_action>
- review_course: state=<state> task=<short task> next=<action/no_action>
- worker_syllabus: state=<state> task=<short task> next=<action/no_action>
- worker_builder: state=<state> task=<short task> next=<action/no_action>
manager_next_action=<one concrete action or no_action>
```

Keep the report short. Do not paste full logs, long task lists, or artifact
evidence unless manager asks for details.

## Escalation Rules

- If manager has unread user messages, that is the top production risk.
- If a worker has high-priority unread from manager, report `waiting_worker`.
- If review_course has no visible review but manager says “waiting review,”
  report task/status truth drift.
- If an agent is `blocked` but health says ready, report the blocker as a
  production issue, not only a runtime issue.
- If context patrol says `allow_continue_original_task=false`, production
  status must include the same agent as blocked until compact/restart is done.
