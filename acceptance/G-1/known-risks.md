# G-1 Known Risks and Blocking Conditions

Submission target: `175a7f31e0538ac646d9a6c523ba14638f662372`
Result: FAIL/BLOCKED

| Severity | Risk | Owner | Deadline | Impact | Mitigation / evidence |
|---|---|---|---|---|---|
| High | Structured `runtime_operator` identity is not provisioned. The tracked placeholder is not an identity and cannot authorize takeover entry or recovery. | Project Owner / security owner | explicit identity-appointment checkpoint | AC-G-1-04 and human-takeover operational appointment remain unproven | keep production enter/recover prohibited; code fails closed; complete appointment through the approved identity process |
| High | Durable owner approval evidence is pending for trust, ownership, SLO, and takeover governance. | Project Owner / control-plane owner | explicit owner-approval checkpoint | AC-G-1-04 and the control-plane owner veto cannot pass | retain `FAIL`; obtain a durable approval record, then request formal REVIEW |
| Medium | Current Ruff, TruffleHog, official npm audit, base/optional pip-audit, and full-source mypy checks are clean, but the actual Flow Memory runtime dependency remains undeclared/unpublished. | dependency owner | publish/declare checkpoint before Gate PASS | AC-GLOBAL-04 cannot pass and dependency provenance remains incomplete | finish Flow Memory Trusted Publisher release, then declare and audit the dependency without relying on an editable sibling checkout |

No Critical or Low risk is recorded. The table has exactly two High and one
Medium open risks, matching `summary.md`'s `0/2/1/0` tally.

## Deferred platform facts

The following are truthful future-platform facts, not counted as additional
open Gate risks because G-1 neither removes nor cuts over these mechanisms:

- UNKNOWN production compatibility metrics continue to block compatibility
  removal; the repository baseline is not production telemetry.
- Flow Memory reports `user_version=0`; its `0.1.1` release code is merged but
  PyPI Trusted Publisher setup is still waiting for authenticated account
  access. Schema versioning and any migration/read-source cutover remain future
  owner-gated work.
- recovery remains human-checkpointed rather than probe-gated, and the
  cross-operation automatic failure-budget/reset model remains a later Gate
  obligation.

These deferrals do not weaken the three current blockers, authorize G0, or
turn unknown platform state into PASS evidence.
