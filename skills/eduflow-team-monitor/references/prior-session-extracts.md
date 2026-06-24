# Prior Session Extracts

This file stores distilled monitoring lessons from older Codex sessions. Keep entries short and action-oriented. Do not paste full conversations here.

## Session `019ede4a-d0ff-78d3-8ca1-36019a2d101b`

Status: unavailable via local `codex_app.read_thread` / `list_threads` during skill creation.

Attempted lookup:

- Direct `read_thread` with the provided id failed argument validation.
- `list_threads` query for the exact id returned no matches.
- Keyword search for EduFlow/IGCSE/monitor/Feishu returned no matching local thread.

How to merge when available:

- Extract recurring patrol commands and compare with `SKILL.md`.
- Add only durable action rules, not raw chat history.
- Classify findings under `gap-taxonomy.md` categories.
- If the prior session contains a different monitoring target, add a short “variant” section rather than changing the core EduFlow IGCSE flow.

## 2026-06-21 IGCSE Overnight Monitor

Source:

- `docs/plans/2026-06-21-igcse-overnight-monitor-gap-note.md`

Durable actions extracted:

- Always validate claims across artifact truth, task truth, inbox truth, runtime truth, and status truth.
- Treat manager/reviewer group text as insufficient for closeout unless task and artifact evidence agree.
- Record every Codex intervention as a gap note with trigger, evidence, action, temporary result, and tomorrow fix.
- Prefer manager nudges first, but escalate to direct worker/reviewer or structure repair when the exact handoff is stuck.
- For model/runtime failures, verify live tmux env and actual post-switch behavior; registry status alone is not enough.
- For subject work, distinguish package checkpoint from subject closeout.
- For QBank and import/dedup, require explicit review/authorization before apply.
- For workflow claims, require structured workflow id/gate state, not only chat wording.
- For message backlog, inspect unread/read/ack and oldest message age before trusting status summaries.
