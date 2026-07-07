# Evolution Packet Template

> One memory/workflow/skill candidate packet produced from existing task
> signals. Read-only surface; never writes memory automatically. Generated
> by `task evolution-packet <task_id> [--json]`.

## Required Fields

| Field | Type | Source | Empty default |
|-------|------|--------|---------------|
| `source_task_id` | string | command arg | required |
| `source_event` | enum (`review_rejected`, `manager_action`, `runtime_incident`, `repair_cycle_ge2`) | derived from triggers | required |
| `trigger_reason` | string | human-readable explanation of why this candidate fired | required |
| `content` | string | 1-3 sentence summary, evidence-backed | `""` |
| `scope` | string | `"workflow:<workflow_id>"` or `"agent:<owner>"` when workflow is empty | `""` |
| `kind` | enum (`workflow_rule`, `agent_skill`, `memory_fact`) | derived from event | `""` |
| `evidence_refs` | list[string] | `["task:<source_task_id>"]` plus non-empty `task.loop_evidence_ref`, `task.verdict_target`, and explicit reviewer actor when present | `["task:<source_task_id>"]` |
| `reuse_reason` | string | short phrase: when/how the next similar task should reuse this candidate | `""` |
| `confidence` | enum (`low`, `medium`, `high`) | see threshold table below | `"low"` |
| `recommended_action` | enum (`remember`, `review_only`, `ignore`) | derived from kind and confidence | `"review_only"` |

## Trigger → Source Event Mapping

| Trigger | source_event | kind |
|---------|--------------|------|
| `latest_authoritative_verdict.outcome == "reject"` (with non-empty `required_fix`) | `review_rejected` | `workflow_rule` |
| `manager_action_type` present (any non-empty value) | `manager_action` | `agent_skill` |
| `status == "failed"` OR `loop_status == "failed"` | `runtime_incident` | `workflow_rule` |
| `loop_cycle_count >= 2` | `repair_cycle_ge2` | `workflow_rule` |

If none of the triggers fire, return `{"candidates": []}` and **do not** create a candidate.

## Confidence Threshold Table

| Trigger combination | confidence |
|--------------------|------------|
| `review_rejected` AND (`required_fix` non-empty AND `blocking_files` non-empty) | `high` |
| `manager_action` (with reason text) | `medium` |
| `runtime_incident` (status=failed with explicit reason) | `medium` |
| `repair_cycle_ge2` only | `medium` |
| any trigger with only `loop_evidence_ref` and no other evidence | `low` |

## `recommended_action` Decision

| condition | recommended_action |
|-----------|---------------------|
| `confidence == "high"` AND `evidence_refs` has ≥ 2 entries | `remember` |
| otherwise | `review_only` |
| no trigger (should never reach this branch) | `ignore` |

## Red Lines

- Do not call flow-memory, write memory, archive state, or run auto-promotion.
- Do not invent evidence; if `evidence_refs` cannot be built from the task, do not emit a candidate.
- Content must be ≤ 280 characters and reference only fields already present on the task.
- One task → at most one candidate per call. Do not aggregate across tasks.
