---
name: eduflow-team-monitor
description: Use when monitoring EduFlow Team real runs in Feishu/Lark, especially IGCSE subject production chains. Guides Codex to inspect runtime truth, keep topic -> QA -> review -> manager closeout moving, intervene minimally, and record gap notes for later system upgrades.
---

# EduFlow Team Monitor

Use this skill for overnight or long-running EduFlow Team monitoring, especially when the user asks to watch a Feishu group, keep IGCSE production running, diagnose stuck agents, collect gap notes, or synthesize prior monitoring sessions into a reusable operating playbook.

## Core Job

Keep the chain moving:

`topic -> QA/items/QQL -> review_course verdict -> manager closeout -> next safe action`

Prefer ecosystem self-repair. Intervene only when the chain is stuck, drifting, or about to corrupt output. Every intervention must be recorded in the gap note before or immediately after acting.

## Setup

Work from the project root:

```bash
cd /Volumes/Halobster/Codex相关/EduFlow-Team-orch
source scripts/eduflow-team-env.sh
```

Default gap note:

```text
docs/plans/YYYY-MM-DD-igcse-overnight-monitor-gap-note.md
```

If no current gap note exists, create one before the first intervention.

If the user provides a prior Codex thread/session id, first try to read that thread. If unavailable, search recent threads by project/task keywords. If still unavailable, do not invent details; ask for an export or continue with the available gap notes and leave a placeholder in `references/prior-session-extracts.md`.

## Fast Patrol Loop

Run these checks first. Do not trust one surface alone.

```bash
./scripts/eduflowteam team --json
./scripts/eduflowteam task auto-ops-production --send-manager
./scripts/eduflowteam task auto-ops-context --send-manager
./scripts/eduflowteam health
sed -n '1,260p' .eduflow-team-state/facts/status.json
tail -n 120 .eduflow-team-state/facts/logs.jsonl
```

## Context Patrol

Auto_ops must run a context patrol whenever monitoring a live team, before
long-task dispatch, and at least once per regular patrol cadence:

```bash
./scripts/eduflowteam task auto-ops-context --send-manager
```

This command is the first data source for context pressure. It captures each
agent pane, parses known context footer/limit markers, prints a team snapshot,
and sends the same structured report to manager.

Rules:

- `80-89%` / `level=warning`: report to manager; recommend smaller next packet.
- `90-99%` / `level=compact_recommended`: report to manager as blocking for long work; manager must run real `eduflow compact <agent>` or `/compact <agent>` before assigning more long work.
- `100%`, `level=exhausted`, or context limit markers: report to manager as blocking; recommend restart/reidentify after compact is rejected or too late.
- `level=ok` with `marker=no_context_pressure_signal` means no parseable context pressure was visible in recent pane output. It is not proof that the context is low.
- Do not replace this with a text reminder such as “please compact context.” Use the command output or real compact/restart commands.

Read `references/context-patrol.md` when changing patrol cadence, manager
message format, or deciding what to do when CLI footer data is unavailable.

## Production Patrol

Auto_ops must pair every context patrol with a production patrol. Context tells
whether an agent can safely continue; production patrol tells what each agent
is doing, whether handoffs are stuck, and what manager should decide next.

Lightweight patrol commands:

```bash
./scripts/eduflowteam team --json
./scripts/eduflowteam task auto-ops-production --send-manager
./scripts/eduflowteam inbox manager
```

Use heavier checks only when the lightweight patrol shows drift, stuck work, or
unclear ownership:

```bash
./scripts/eduflowteam task supervisor-check --json
./scripts/eduflowteam task review-queue --reviewer review_course
tail -n 120 .eduflow-team-state/facts/logs.jsonl
```

Auto_ops production reports to manager must include:

- active agents and their current production/review/repair role
- `待接单` or unread high-priority inbox owners
- in-progress production tasks and review tasks
- blocked agents or runtime guard escalation
- stale status or no heartbeat risks
- one recommended manager action, or `no_action` if the team is healthy

Read `references/production-patrol.md` when changing production report format,
deciding whether to nudge manager, or classifying an agent as active, idle,
blocked, stale, or waiting for review.

When runtime/model truth matters, check live tmux, not just status files:

```bash
tmux list-windows -t EduFlowTeam
tmux list-panes -t EduFlowTeam:manager -F '#{pane_pid}\t#{pane_current_command}\t#{pane_start_command}'
tmux list-panes -t EduFlowTeam:review_course -F '#{pane_pid}\t#{pane_current_command}\t#{pane_start_command}'
tmux capture-pane -t EduFlowTeam:manager -p -S -120
tmux capture-pane -t EduFlowTeam:review_course -p -S -120
```

For handoff checks:

```bash
./scripts/eduflowteam inbox manager
./scripts/eduflowteam inbox worker_course
./scripts/eduflowteam inbox review_course
./scripts/eduflowteam task review-queue --reviewer review_course
```

## Prior Session Synthesis

When asked to “沉淀成 skill” from one or more monitoring sessions:

1. Read the gap note and any provided thread summaries.
2. Extract actions, not just problems:
   - patrol commands used
   - evidence surfaces checked
   - conditions that triggered intervention
   - exact intervention type
   - post-intervention verification
   - later productization suggestion
3. Merge repeated cases into durable rules.
4. Keep raw history in references, not in `SKILL.md`.
5. Mark unverifiable sessions as unavailable rather than filling gaps from memory.

Use `references/prior-session-extracts.md` for session-specific distilled lessons.

## Truth Hierarchy

Use this order when surfaces disagree:

1. File/artifact truth: actual `content/` files, manifests, item/QQL counts, verifier output.
2. Task truth: `.eduflow-team-state/tasks.json`, `task get`, review queue.
3. Inbox truth: unread/read/ack state and message ids.
4. Runtime truth: live tmux process, pane output, provider/model env, health.
5. Status truth: `facts/status.json`.
6. Group/log narration: useful, but never enough for closeout alone.

Do not declare a subject complete from manager text alone. A subject closeout needs subject-wide inventory evidence.

## Common Patrol Questions

Ask these each loop:

- Is there a live production task, review task, repair task, or closeout task?
- Did a worker claim “sent to review” while `review_course` inbox/review queue is empty?
- Did `review_course` say PASS/MINOR/NEEDS_FIX while task verdict is still pending?
- Did manager say closeout while task truth or artifact truth disagrees?
- Did a batch closeout happen while subject manifest still has backlog?
- Is manager waiting for user when there is a safe, already-requested next action?
- Is a worker using a failed provider despite a configured fallback?
- Is health saying down while tmux or logs show live panes, or the reverse?
- Are old high-priority messages or stale task instructions re-entering the chain?
- Is workflow only mentioned in chat, or is `workflow_id`/gate state actually present?

## Intervention Ladder

Use the lowest effective step.

1. Observe only: if the chain is moving and evidence is fresh.
2. Soft nudge manager: when manager has enough authority to repair the chain.
3. Direct role instruction: when manager is not consuming a verdict/result and one worker/reviewer needs a narrow action.
4. Structure repair: update task/review/inbox state only when group text and structured truth diverge.
5. Runtime repair: switch/restart/rehire only after provider/runtime failure is evidenced.
6. Operator fallback: directly verify or edit artifacts only when content/review chain is blocked and delay risks stopping the run.

Before steps 2-6, add or append a gap note.

## Gap Note Template

```markdown
### N. Short problem title

触发时间：YYYY-MM-DD HH:MM CST

触发原因：

- Why ecosystem self-repair is not enough.

现场证据：

- Command/file/message evidence.
- Include task id, message id, agent, or file path when possible.

介入动作：

- What Codex did or is about to do.

临时结果：

- What changed, or what needs next verification.

明天修复建议：

- Product/system fix so Codex does not need to do this again.
```

## Safe Manager Nudge Pattern

Use short, specific instructions. Avoid broad “please handle” messages.

```text
当前唯一真相：<task/batch/subject state>.
请只做三件事：
1. <consume/ack exact message or verdict>
2. <dispatch exact worker/reviewer action>
3. <update task/status/closeout after evidence>
边界：不要 <wrong action>. 完成后用最小状态包同步。
```

## Workflow Rules

For IGCSE subject work, require `workflow_id=igcse-subject-launch` or equivalent gate state.

If an agent says “按 workflow” but task truth lacks workflow/gate state, record a gap and nudge manager to formalize it.

Minimum gates:

- dispatch acceptance
- production in progress
- submitted for review with reviewer set
- review PASS/MINOR/NEEDS_FIX written to task truth
- repair dispatch when needed
- package closeout
- subject closeout only after subject-wide inventory verifier passes

## Runtime Rules

`pane ready` is not `agent operational`.

After model/runtime switch, verify:

- live tmux spawn command/env matches expected provider/model
- pane output shows successful new call, not old interrupted input
- latest high-priority inbox is consumed or explicitly reconciled
- status/log/task state changes after the switch

If provider quota/429 appears, prefer cross-provider runtime fallback. Do not accept same-pool fallback without a smoke test.

## Closeout Rules

Batch closeout is not subject closeout.

For a package/batch:

- exact topic set known
- each topic meets expected item/QQL count and difficulty distribution
- review_course verdict exists or operator fallback is explicitly labeled
- task verdict/closeout state is synced or gap-recorded

For a subject:

- full topic count from outline/inventory is covered
- root manifest location is correct
- items/QQL/QA counts match expected subject standard
- per-topic difficulty distribution passes
- Question IDs are bidirectionally aligned
- old fragment/orphan files are quarantined or accounted for
- manager explicitly says subject closeout, not package checkpoint

## References

Read `references/gap-taxonomy.md` when summarizing prior runs, planning tomorrow's fixes, or deciding whether a symptom belongs to runtime, message processing, workflow, artifact quality, QBank, or visibility.

Read `references/prior-session-extracts.md` when the user references an earlier Codex thread/session or asks to combine multiple monitoring days.
