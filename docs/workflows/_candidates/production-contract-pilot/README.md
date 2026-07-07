# production-contract-pilot

Read-only Production Contract pilot for course / qbank review-repair chain.
Decides whether the 2026-07-06 read-model surfaces (Loop Contract, Tool
Risk, Evolution Packet, Operational Readiness) make manager dispatch
faster, worker repair more focused, and review closeout more specific.

- workflow_id: `production-contract-pilot`
- status: `candidate` (5-10 real task trial; promote or retire based on acceptance-log)
- owner: `manager`
- scope: course / qbank review-repair chain only
- reads: `task loop-contract`, `task readiness-check`, `task evidence-explain`,
  `task evolution-packet`, `task manager-panel`, `task tool-risk`
- writes: **none** (all surfaces are read-only; no automatic memory,
  no auto-repair, no auto-archive, no auto-fire)

## Primary Chain

```text
manager -> read-model surfaces (loop-contract / readiness-check) ->
worker_course (repair) -> review_course (verdict) ->
evolution-packet candidate -> manager acceptance-log
```

manager is the only decider; worker_course executes the repair
described in the Loop Contract; review_course decides the verdict;
manager records whether the read-models helped in this runbook's
acceptance-log.

## When to Use

The pilot applies whenever manager is about to dispatch a repair handoff
on a course or qbank task that:

1. Was previously rejected by review_course (has non-empty `required_fix`)
2. Has `loop_cycle_count >= 1` (i.e. already in a repair loop)
3. Has unresolved `manager_action_type` from a prior review
4. Or: any course/qbank task where manager wants a one-shot readiness
   picture before dispatching

If the task does **not** match any of the above, do not run the pilot —
the existing `task dispatch + assign-reviewer + manager-panel` chain is
already sufficient and the read-model overhead is wasted.

## Pilot Runbook (manager-executable checklist)

For one chosen pilot task, manager executes these six steps in order.
Skip nothing; record observations in `acceptance-log.md` after each
real run.

### Step 1 — Choose a repair-risk task

Pick one course or qbank task where the previous round was either
rejected, failed, or repair-cycled. Do **not** pick clean delivered tasks.

### Step 2 — Run readiness check

```bash
./scripts/eduflowteam task readiness-check <T-id> --json
```

Expected output keys: `delivery`, `productivity`, `source`, `overall`.
Record the verdict for each dimension in `acceptance-log.md`. If
`overall` is `fail`, STOP and resolve the readiness gap first — the
pilot assumes a baseline readiness of `warn` or `pass`.

### Step 3 — Render Loop Contract

```bash
./scripts/eduflowteam task loop-contract <T-id> --json
```

The JSON contains:

- `current_phase` — what worker / review is doing right now
- `failed_checks` — non-empty list of repair instructions
- `allowed_actions` — what the worker may do
- `next_required_output` — what the reviewer is waiting for
- `evidence_refs` — files / loops that anchor the verdict

### Step 4 — Send the repair handoff

Use `LOOP_CONTRACT_TEMPLATE.md` (in `docs/templates/`) plus
`handoff-template.md` (next to this README) to write the manager-to-
worker message. Include:

```text
- task_id: <T-id>
- phase: <current_phase from Loop Contract>
- why: <one-line summary of failed_checks>
- repair_brief: <specific instructions>
- deliver: <next_required_output>
- evidence: <evidence_refs joined>
- ack_required: <True if delivery.warn, else False>
```

Send via the standard dispatcher (`./scripts/eduflowteam send worker_course manager "..." 高`).
Do **not** auto-dispatch from inside a read-model.

### Step 5 — Wait for worker repair + re-review

Standard chain — no changes. The contract is the message, not the
workflow.

### Step 6 — Run evolution-packet after review

```bash
./scripts/eduflowteam task evolution-packet <T-id> --json
```

If a candidate is produced, **do not** auto-promote it into flow-memory
(Package 8 is paused). Instead, copy the candidate JSON into
`acceptance-log.md` so the team can audit later whether the trigger
(`review_rejected / manager_action / runtime_incident / repair_cycle_ge2`)
matched reality.

### Step 7 — Record the outcome

Append one entry to `acceptance-log.md` per real task run. Use the
template at the top of that file.

## Acceptance Log

See `acceptance-log.md` next to this README. The pilot is **promote-or-
retire** based on whether ≥ 7 of 10 entries report the manager was
faster, the worker was less off-track, the review verdict was more
specific, and closeout was easier.

After 5-10 real task runs the manager team decides together whether to:

1. **Promote**: keep the read-models on by default; expand to other
   workflows (e.g. `ap-knowledge-base-optimization`)
2. **Retire**: roll back to the pre-pilot manager chain
3. **Iterate**: tweak thresholds, add new triggers, etc.

## What the Pilot Does NOT Do

- Does not block or gate any command — `task tool-risk` returns advice,
  nothing more
- Does not auto-write to memory or flow-memory (Package 8)
- Does not change `send / say / fire / hire / reset` behavior
- Does not change review verdict authority (review_course still owns verdicts)
- Does not change closeout authority (manager still owns closeout)
- Does not require Feishu / Lark credentials

## Files in this pilot

- `README.md` — this file
- `handoff-template.md` — paste-ready repair message scaffold
- `acceptance-log.md` — per-task outcome table (append-only)

## Related Artifacts (not in this pilot)

- `docs/templates/LOOP_CONTRACT_TEMPLATE.md`
- `docs/templates/TOOL_RISK_MATRIX.md`
- `docs/templates/EVOLUTION_PACKET_TEMPLATE.md`
- `src/eduflow/store/task_loop_contract.py`
- `src/eduflow/store/tool_risk.py`
- `src/eduflow/store/evolution_packet.py`
- `src/eduflow/store/operational_readiness.py`