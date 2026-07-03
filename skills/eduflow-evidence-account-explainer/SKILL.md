---
name: eduflow-evidence-account-explainer
description: Translate the existing EduFlow evidence gate (task_evidence_account, subject verifier, review queue) into a role-friendly PASS | NEEDS_FIX | BLOCKED | OBSERVE verdict packet. Read-only explainer that helps review_course, worker_course, worker_qbank, and manager closeout-lite decide who owns the next move. No new gate logic, no state changes, no Feishu sends.
---

# EduFlow Evidence Account Explainer

Use this skill whenever a flow task is close to a verdict, but the existing primitives — `task evidence-account`, `subject-inventory`, `task review-queue`, `task manager-actions` — return raw fields. The explainer turns those raw fields into one short, role-friendly packet so a reviewer/worker/manager does not have to re-derive the gate.

It does **not** recompute evidence. It reads the existing `task_evidence_account.build_evidence_account` output and the latest authoritative review verdict, then classifies the task into one of four verdicts.

## When to use

- `review_course` is about to write a `full verdict` and wants a one-line pre-check.
- `worker_course` is doing `selfcheck` after submitting for review.
- `worker_qbank` is verifying a `qbank slice` before signing off on `qbank_ready`.
- `manager` is running `closeout-lite` and wants a single paste-ready packet.

Do **not** use it for:

- Production line runtime drift (use `eduflow-runtime-task-drift-explainer`).
- Harness / identity / skill drift (use `eduflow-harness-surface-audit`).
- Asset registration / drift (use `eduflow asset list/validate/drift-check`).

## Role boundary

| Role | Permission | What it does |
| --- | --- | --- |
| `review_course` | read + verdict | Consumes the packet to write `full verdict` (approve / reject / manager_action). Does **not** override subject verifier status — pass/warn/fail is read-only. |
| `worker_course` | read + selfcheck | Consumes the packet to decide whether to expand QA, fix evidence packet, or escalate. Does **not** self-approve subject PASS. |
| `worker_qbank` | read + qbank slice | Consumes the packet to confirm `qbank_readiness` and `subject_verifier_status` before seeding. Does **not** mark subject PASS from package PASS. |
| `manager` | read + dispatch (closeout-lite) | Consumes the packet to decide whether to formal closeout, request more evidence, or roll over. Does **not** re-audit content depth — leave that to `review_course` / `subject verifier`. |

Hard rules:

- `package PASS` never auto-promotes to `subject PASS`. The subject verifier owns the `subject` scope verdict, not a worker self-report.
- `manager` must not deep-audit content from this packet. The packet tells manager **what is missing**, not **whether each item is right**.
- No CLI in this skill writes tasks, dispatches agents, or sends Feishu.

## Read-only command ladder

Run these in order. Stop when the packet is clear. The packet itself can be produced by hand following the template below, or by `eduflow task evidence-explain <task_id> [--json]` (if implemented).

1. `./scripts/eduflowteam task evidence-account --task-id <T> --json`
   - The raw account. Read `missing_evidence`, `conflicting_evidence`, `subject_verifier_status`, `qbank_readiness`, `recommended_action`.
2. `./scripts/eduflowteam task review-queue`
   - Cross-check the task is actually in the queue (and not in some stale lane).
3. `./scripts/eduflowteam task subject-inventory`
   - If the task has a subject slug, confirm subject verifier compact summary.
4. `./scripts/eduflowteam task manager-actions`
   - See what the manager-action layer would route next, but do not let it override this packet's verdict.

The explainer never sends Feishu, never dispatches agents, never mutates the evidence packet.

## Verdict classification

Map the raw `evidence_account` and `latest_authoritative_review` into exactly one of four buckets. The mapping is deterministic; do not improvise.

| Verdict | Required signals |
| --- | --- |
| `PASS` | `closeout_ready == True`, no `conflicting_evidence`, latest review verdict `approved` with scope `full_subject`, subject verifier status `pass` (or `legacy` legacy full-subject evidence path applies), `qbank_readiness` in `{qbank_ready, ready_for_import, needs_user_authorization}` (or empty when qbank step is not yet reached). |
| `NEEDS_FIX` | `missing_evidence` non-empty AND no `conflicting_evidence` AND latest review verdict not blocking (`approved`/`pending`/empty) AND subject verifier status is not `fail`. Manager may still need to dispatch the right repair role. |
| `BLOCKED` | `conflicting_evidence` non-empty (latest review verdict blocks closeout, items/QQL/manifest count drift, subject verifier `fail`/`warn`, qbank not ready, revision priority active), OR `subject_verifier_status == fail`, OR latest review verdict is `rejected` / `manager_action` blocking. |
| `OBSERVE` | `closeout_ready == True` but the latest authoritative review verdict is empty/pending, or the task is waiting for a downstream role (qbank check, manager formal closeout) that is not yet due. Pass exists, but signal is incomplete; do not declare done. |

Tie-breakers (apply in order):

1. If `conflicting_evidence` is non-empty → `BLOCKED`.
2. Else if `subject_verifier_status in {fail, warn}` → `BLOCKED`.
3. Else if `missing_evidence` is non-empty → `NEEDS_FIX`.
4. Else if latest review verdict is `rejected` or `manager_action` → `BLOCKED`. A `rejected` verdict is an explicit closeout block; a `manager_action` verdict is a request-for-decision that has not yet been answered by the manager.
5. Else if latest review verdict is empty/pending → `OBSERVE`.
6. Else if latest review verdict is `approved` and `qbank_readiness` is empty / `qbank_ready` / `ready_for_import` / `needs_user_authorization` → `PASS`.
7. Else `OBSERVE`.

## Confidence rubric

Report `confidence` as one of `high | medium | low`:

- `high`: every required field in the packet has a non-empty source. `latest_authoritative_review` and `subject_verifier_status` are both present and consistent.
- `medium`: latest review verdict is present but `subject_verifier_status` is empty, or qbank_readiness empty but the task is not yet at qbank stage.
- `low`: at least one of `latest_authoritative_review`, `subject_verifier_status`, `items_count` / `qql_count` / `manifest_rows` is missing or sourced from `source_missing`.

## Output template

Paste this template at the top of any review / selfcheck / closeout-lite response. Keep the field order stable so downstream parsers and tests can grep on it.

```markdown
## Evidence Account Verdict Packet

- task_id: <T>
- workflow_id: <workflow_id or '-'>
- verdict: PASS | NEEDS_FIX | BLOCKED | OBSERVE
- confidence: high | medium | low
- missing_evidence: [<list or '-'>]
- conflicting_evidence: [<list or '-'>]
- latest_authoritative_review: reviewer=<reviewer or '-'> verdict=<verdict or '-'> scope=<scope or '-'> at_ms=<at_ms or 0>
- subject_verifier_status: <pass | warn | fail | ''> (source=<subject_verifier | task.verifier_result | source_missing>)
- qbank_readiness: <state or '-'> (source=<task.qbank.lifecycle_state | evidence_packet.qbank_readiness | source_missing>)
- manager_action_allowed: <true | false>
- required_next_owner: <worker_course | review_course | worker_qbank | manager | '-' >
- safe_next_action: <short imperative line, e.g. 'request_review_course_file_evidence'>
- do_not_say_to_user_yet: <one line describing what must stay out of user-facing summary>
```

Field semantics (do not silently change):

- `verdict` — exactly one of the four buckets above; do not collapse `NEEDS_FIX` into `BLOCKED`.
- `confidence` — drive from the confidence rubric, not from personal optimism.
- `missing_evidence` / `conflicting_evidence` — copy from `evidence_account`; never invent.
- `latest_authoritative_review` — pull from `latest_authoritative_verdict` on the task; render `-` when missing.
- `subject_verifier_status` — exactly the field from the verifier result (`pass` / `warn` / `fail` / `''`). Never upgrade `package` PASS into `subject` PASS.
- `qbank_readiness` — exact state string from `task.qbank.lifecycle_state` (or evidence-packet `qbank_readiness` when task has no qbank object yet).
- `manager_action_allowed` — `True` only when the `evidence_account.closeout_ready` is True AND the `recommended_action` is `manager_formal_closeout`. Otherwise `False`.
- `required_next_owner` — derived from the suggested `assignee` in the action packet (or the role owning the missing field: `worker_course` for QA expansion, `review_course` for evidence file check, `worker_qbank` for qbank readiness, `manager` for closeout). Render `-` when ambiguous.
- `safe_next_action` — one short imperative line, never a multi-step plan. This is what manager / reviewer should paste into the next dispatch.
- `do_not_say_to_user_yet` — one line that prevents premature user-facing language. Example: "do not yet say '正式 PASS' until subject verifier returns pass on full subject scope."

## Do not

- Do not call the verifier (`subject_verifier.verify_subject` or `ap_subject_verifier.verify_ap_subject`) to "double-check" — the packet only mirrors what the gate already produced. If the gate is wrong, fix the gate, not the explainer.
- Do not promote `package` / `unit` / `qbank slice` PASS into `subject` PASS.
- Do not have `manager` deep-audit the content; the packet only signals what is missing.
- Do not send Feishu, do not dispatch tasks, do not change `evidence_account` fields.
- Do not output the verdict in any other form than the four buckets (`PASS | NEEDS_FIX | BLOCKED | OBSERVE`).
- Do not change the field order in the template; downstream parsers and tests depend on it.

## Worked example (manager closeout-lite)

Raw `evidence_account` for `T-42` (IGCSE Accounting 0452):

```json
{
  "task_id": "T-42",
  "workflow_id": "igcse-subject-launch",
  "closeout_ready": false,
  "missing_evidence": ["items_count", "manifest_evidence", "manifest_rows"],
  "conflicting_evidence": [],
  "subject_verifier_status": "",
  "qbank_readiness": "",
  "recommended_action": "complete_closeout_evidence_account",
  "latest_authoritative_review_verdict": {"reviewer": "review_course", "verdict": "approved", "verdict_scope": "full_subject", "at_ms": 1720000000000}
}
```

Verdict packet:

```markdown
## Evidence Account Verdict Packet

- task_id: T-42
- workflow_id: igcse-subject-launch
- verdict: NEEDS_FIX
- confidence: medium
- missing_evidence: [items_count, manifest_evidence, manifest_rows]
- conflicting_evidence: []
- latest_authoritative_review: reviewer=review_course verdict=approved scope=full_subject at_ms=1720000000000
- subject_verifier_status: '' (source=source_missing)
- qbank_readiness: '-' (source=source_missing)
- manager_action_allowed: false
- required_next_owner: worker_course
- safe_next_action: request_worker_course_expand_qa_and_evidence_packet
- do_not_say_to_user_yet: do not yet say 'closeout' until items_count + manifest_evidence are filled and subject verifier returns pass on full subject
```

The manager pastes that into the closeout-lite block; it does **not** try to re-derive items_count by reading the content directory.

## Worked example (review_course full verdict)

Raw `evidence_account` for `T-77` (AP Calculus):

```json
{
  "task_id": "T-77",
  "workflow_id": "ap-knowledge-base-optimization",
  "closeout_ready": false,
  "missing_evidence": [],
  "conflicting_evidence": ["items_qql_count_drift:items=378:qql=324", "qbank_not_ready:needs_user_authorization"],
  "subject_verifier_status": "warn",
  "qbank_readiness": "needs_user_authorization",
  "recommended_action": "resolve_evidence_account_conflict",
  "latest_authoritative_review_verdict": {"reviewer": "review_course", "verdict": "rejected", "verdict_scope": "unit", "at_ms": 1720001000000}
}
```

Verdict packet:

```markdown
## Evidence Account Verdict Packet

- task_id: T-77
- workflow_id: ap-knowledge-base-optimization
- verdict: BLOCKED
- confidence: high
- missing_evidence: []
- conflicting_evidence: [items_qql_count_drift:items=378:qql=324, qbank_not_ready:needs_user_authorization]
- latest_authoritative_review: reviewer=review_course verdict=rejected scope=unit at_ms=1720001000000
- subject_verifier_status: warn (source=subject_verifier)
- qbank_readiness: needs_user_authorization (source=task.qbank.lifecycle_state)
- manager_action_allowed: false
- required_next_owner: worker_course
- safe_next_action: resolve_evidence_account_conflict
- do_not_say_to_user_yet: do not yet say 'approved' — items/QQL drift and warn status must be reconciled by worker_course first
```

`review_course` then writes its full verdict, but does **not** override the warn status; it routes the conflict to `worker_course` (items expansion) and waits for a re-verified packet before signing off.

## Worked example (worker_qbank qbank slice)

Raw `evidence_account` for `T-90`:

```json
{
  "task_id": "T-90",
  "workflow_id": "igcse-item-level-prototype",
  "closeout_ready": true,
  "missing_evidence": [],
  "conflicting_evidence": [],
  "subject_verifier_status": "pass",
  "qbank_readiness": "qbank_ready",
  "recommended_action": "manager_formal_closeout",
  "latest_authoritative_review_verdict": {"reviewer": "review_course", "verdict": "approved", "verdict_scope": "full_subject", "at_ms": 1720002000000}
}
```

Verdict packet:

```markdown
## Evidence Account Verdict Packet

- task_id: T-90
- workflow_id: igcse-item-level-prototype
- verdict: PASS
- confidence: high
- missing_evidence: []
- conflicting_evidence: []
- latest_authoritative_review: reviewer=review_course verdict=approved scope=full_subject at_ms=1720002000000
- subject_verifier_status: pass (source=subject_verifier)
- qbank_readiness: qbank_ready (source=task.qbank.lifecycle_state)
- manager_action_allowed: true
- required_next_owner: manager
- safe_next_action: manager_formal_closeout
- do_not_say_to_user_yet: qbank_ready is recorded, but the user-facing 'closeout completed' line must wait for manager closeout
```

`worker_qbank` pastes this as the qbank slice verdict; the manager closeout-lite lane owns the user-facing closeout line.
