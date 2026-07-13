# Human Takeover Runbook

**Audience:** on-call admin/runtime operator and `control_plane_owner`

**Safety:** status is read-only. Enter/recover mutate local control state and
require the provisioned structured authorization plus the evidence checkpoints
in this runbook.

## Current production authorization fact

The project owner appointed Kenny for runtime-only authority at
`https://github.com/Harryanhuang/EduFlow-Team-orch/issues/7#issuecomment-4953662798`
(`author_association=OWNER`, applicable revision
`58d926778dde76724467b2eab307e80b0a1c5ea3`). Production provisions the
structured actor `ou_557e95aadc346010e58dbc71090123f3` under
`team.runtime_operators`. The appointment was uniquely resolved through the
Feishu `contact:user:search` scope; no credential value is part of the record.

The general `team.operators` row remains the literal deny-all sentinel
`u_<admin_feishu_id>` until G0 makes an empty Slash allowlist fail closed. It is
not an identity and must not be used as evidence. The CLI reads
`team.admins`, `team.runtime_operators`, and `team.runtime_operator`, rejecting the entire
runtime-authority set when any accepted field is malformed. General `team.operators` have no enter/recover authority. Never substitute a display
name, shell username, placeholder, or invented ID. The appointment does not
waive the live evidence, generation, reason, audit, or recovery checks below.

## 1. Observe without mutation

From the correlated production checkout:

```bash
./scripts/eduflowteam human-takeover status --json
./scripts/eduflowteam health --json
./scripts/eduflowteam runtime list --json
```

Record checkout, revision, config hash, state directory, state, generation, reason, source, entered time, and recovery steps. Do not record credential values. If status is corrupt/unknown or commands point to different checkouts, treat automation as active/blocked and escalate.

## 2. Stop and contain

Confirm guarded automatic runtime switching has stopped before side effects. Do not manually repeat the failing switch, delete takeover state, edit audit JSONL, reset task state, or advance cursor/seen. Preserve the state and audit files for review. Scope external containment to the affected runtime or control path.

## 3. Enter explicitly

Use the real structured actor identifier and a non-secret reason:

```bash
./scripts/eduflowteam human-takeover enter --actor ou_557e95aadc346010e58dbc71090123f3 --reason <NON_SECRET_INCIDENT_REASON> --json
```

This is an operator procedure template, not acceptance evidence. Redact command output before attaching it if future fields can contain sensitive text. Re-run status and verify `active`, the reason/source, and a new generation.

## 4. Diagnose and prove recovery

Required minimum evidence:

1. topology auditor still correlates the affected process to checkout/revision/config/state;
2. the triggering dependency is reachable and its live probe passes;
3. no automatic side effect occurred after takeover entry;
4. audit contains the prepared/failed or enter event without secrets;
5. a controlled isolated-state reproduction no longer fails.

Do not use cached `proved_ready`, a skipped smoke, pane label, or chat statement as recovery proof.

## 5. Recover

**Current limitation:** `human-takeover recover` trusts the supplied `--step` text and does not machine-verify any runtime, provider, topology, or smoke probe. Moving state to `inactive` is therefore not proof that service recovered. Before invoking recover, a human checkpoint by an authorized, provisioned admin/runtime operator must inspect the Step 4 command evidence and record its paths/revision; the CLI must not be described as automatic enforcement.

Copy the generation from the immediately preceding status result. Supply concrete evidence-bearing steps, not “fixed” alone:

```bash
./scripts/eduflowteam human-takeover recover --actor ou_557e95aadc346010e58dbc71090123f3 --reason <NON_SECRET_RECOVERY_REASON> --generation <CURRENT_GENERATION> --step <VERIFIED_STEP> --json
```

If generation is stale, authorization is denied, persistence/audit fails, or a probe fails: stop. Do not retry with guessed values. Re-read status and escalate to `control_plane_owner` and the applicable security/runtime owner.

Follow-up contract: `G1-Runtime-Authority`; owner `runtime_operator`, approval `control_plane_owner`. It must bind recovery to structured admin/runtime-operator authorization and machine-verified live probe evidence. Removal test (stable required test id): `python3 -m pytest tests/integration/test_control_plane_authorization.py -k test_human_takeover_recovery_requires_verified_probe_evidence`. The limitation remains open until that command exists and passes; absence of the test blocks removal and production-operable claims.

## 6. Post-recovery validation

Verify status is `inactive` with the expected new generation, inspect the append-only audit, and run one controlled eligibility/probe check before restoring cadence. Formal REVIEW is `worker_review`; manager remains the only CLOSEOUT owner and is dispatch-only. Record incident owner, impact, timestamps, evidence paths, follow-up decision, and any compatibility exception with expiry/removal test.

## Rollback

There is no safe rollback by deleting or hand-editing takeover state. If a new release caused the incident, revert code in an isolated verified worktree while keeping production takeover active; validate the reverted build, then follow the same authorized recovery transition.
