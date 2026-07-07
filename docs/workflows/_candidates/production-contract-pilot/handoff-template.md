# Repair Handoff Template (production-contract-pilot)

Use this scaffold to compose the manager → worker_course repair message.
Fill the placeholders from the Loop Contract (`task loop-contract
<T-id> --json`).

## Template

```text
open: <task_id>
phase: <current_phase>
why: <one-line summary joined from failed_checks>
repair_brief: <2-4 sentences, specific>
do: <allowed_actions joined by "; ">
do_not: <forbidden_actions joined by "; ">
deliver: <next_required_output>
evidence: <evidence_refs joined by " | ">
ack_required: <True | False>
deadline: <optional wall-clock deadline>
```

## Worked Example (from a real IGCSE Accounting 0452 retry)

```text
open: T-12
phase: curriculum_in_progress
why: review rejected with missing syllabus section 2.1; 1 blocking file
repair_brief: expand per-topic items to 9 in items/T1.1.md; ensure QQL
             references match.
do: rerun scope section 2.1 only; do not produce full T2 yet.
do_not: do not edit the QQL layer; do not modify item format spec.
deliver: re-submit for review with updated items/T1.1.md.
evidence: task:T-12 | items/T1.1.md
ack_required: True
deadline: next manager cadence (within 30 min)
```

## Sending the Message

```bash
./scripts/eduflowteam send worker_course manager "$(cat /tmp/handoff.txt)" 高
```

The worker reads the message, parses `open / phase / why / repair_brief /
do / do_not / deliver / evidence / ack_required`, and treats it as the
authoritative repair contract for the next round. Review_course uses
the same contract fields to anchor its verdict.

## What Does NOT Belong in the Handoff

- Worker commands that bypass review (`do_not_review_after_repair`)
- Owner changes (`switch_owner: ...`) — those go through `task dispatch`
- Priority escalation beyond `高` — that requires manager override
- Memory writes — the pilot writes no memory during the run

## Recovery If the Handoff Was Misread

If worker_course reports it cannot interpret the contract, manager
re-sends the message as plain text (no contract fields) and treats the
pilot entry as `incomplete`. Record the outcome in `acceptance-log.md`
under the `worker_less_off_track` column (`False`).
