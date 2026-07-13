# G-1 Known Risks and Blocking Conditions

Submission target: `58d926778dde76724467b2eab307e80b0a1c5ea3`
Result: FAIL/BLOCKED

| Severity | Risk | Owner | Deadline | Impact | Mitigation / evidence |
|---|---|---|---|---|---|
| High | Structured `runtime_operator` identity is not provisioned. The tracked placeholder is not an identity and cannot authorize takeover entry or recovery. | Project Owner / security owner | explicit identity-appointment checkpoint | AC-G-1-04 and human-takeover operational appointment remain unproven | keep production enter/recover prohibited; code fails closed; complete appointment through the approved identity process |
| High | Durable owner approval evidence is pending for trust, ownership, SLO, and takeover governance. | Project Owner / control-plane owner | explicit owner-approval checkpoint | AC-G-1-04 and the control-plane owner veto cannot pass | retain `FAIL`; obtain a durable approval record, then request formal REVIEW |

No Critical, Medium, or Low risk is recorded. The table has exactly two High
open risks, matching `summary.md`'s `0/2/0/0` tally. The former Flow Memory
dependency risk is closed by the published, pinned, audited, clean-install
evidence for `flow-memory==0.1.1`.

## Deferred platform facts

The following are truthful future-platform facts, not counted as additional
open Gate risks because G-1 neither removes nor cuts over these mechanisms:

- UNKNOWN production compatibility metrics continue to block compatibility
  removal; the repository baseline is not production telemetry.
- Flow Memory reports `user_version=0`; version `0.1.1` is published through
  PyPI Trusted Publishing and pinned by EduFlow. Schema versioning and any
  migration/read-source cutover remain future owner-gated work.
- recovery remains human-checkpointed rather than probe-gated, and the
  cross-operation automatic failure-budget/reset model remains a later Gate
  obligation.

These deferrals do not weaken the two current blockers, authorize G0, or
turn unknown platform state into PASS evidence.
