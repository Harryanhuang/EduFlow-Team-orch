# Loop Contract Template

> One actionable handoff packet per task. Read-only render produced by
> `task loop-contract <task_id> [--json]`. Do not invent values: if the
> underlying task/evidence/delivery field is unknown, leave the field
> empty (string `""` or empty list `[]`).

## Required Fields

| Field | Type | Source | Empty default |
|-------|------|--------|---------------|
| `task_id` | string | command arg | required |
| `workflow_id` | string | `task.workflow_id` | `""` |
| `current_phase` | string | `task.stage + task.status` (e.g. `review_repair`, `submitted_for_review`, `in_progress`, `delivered`, `failed`, `blocked`) | `""` |
| `owner` | string | `task.owner` or `task.assignee` | `""` |
| `iteration` | int | `task.loop_cycle_count` | `0` |
| `delivery.state` | string | latest matching inbox message `delivery_state`; empty when no handoff message | `""` |
| `delivery.inbox_local_id` | string | latest matching inbox `local_id` | `""` |
| `delivery.ack_required` | bool | `True` iff there is a matching high-priority handoff message | `False` |
| `delivery.ack_state` | string | latest matching inbox `ack_state` | `""` |
| `delivery.ack_deadline` | string | hardcoded rule: handoff with `priority ∈ {高, high, urgent, P0, P1}` ⇒ mandatory; else empty | `""` |
| `passed_checks` | list[string] | empty in v1; populated by readiness-check (Package 5) | `[]` |
| `failed_checks` | list[string] | one entry each of: `required_fix`, `blocking_files`, `review_reason`, `loop_stop_reason` (non-empty only) | `[]` |
| `allowed_actions` | list[string] | `task.loop_recommended_action` when present; else empty | `[]` |
| `forbidden_actions` | list[string] | empty in v1 (reserved for Package 6 manager panel) | `[]` |
| `next_required_output` | string | one short sentence: `review verdict`, `repair iteration`, `manager action`, `evidence packet`, etc., derived from `task.stage/status` and `loop_status` | `""` |
| `evidence_refs` | list[string] | one `task:<task_id>` plus any non-empty `task.loop_evidence_ref` | `["task:<task_id>"]` |

## Handoff Usage (manager → repair worker)

```text
open: <task_id>
phase: <current_phase>
why: <failed_checks joined by ";">
repair_brief: <short instruction>
do: <allowed_actions joined by ";">
do_not: <forbidden_actions joined by ";">
deliver: <next_required_output>
evidence: <evidence_refs joined by ";">
ack_required: <True/False>
```

## Triggers That Should Produce `failed_checks`

- `task.required_fix` non-empty
- `task.blocking_files` non-empty
- `task.review_reason` non-empty
- `task.loop_stop_reason` non-empty

## Red Lines

- Do not invent evidence; if `loop_evidence_ref` is empty, omit it from `evidence_refs`.
- Do not mutate task state; this template is a render-only surface.
- `next_required_output` must be a short verb phrase, not narrative text.
