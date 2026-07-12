# G-1 Known Risks and Blocking Conditions

Submission target: `2296dc08c14eae9de34accdf43d4a11c6b8ba68f`
Result: FAIL/BLOCKED

| Severity | Risk | Owner | Deadline | Impact | Mitigation / evidence |
|---|---|---|---|---|---|
| High | Structured `runtime_operator` identity is not provisioned. The tracked placeholder is not an identity and cannot authorize takeover entry or recovery. | Project Owner / security owner | explicit identity-appointment checkpoint | AC-G-1-04 and human-takeover operational appointment remain unproven | keep production enter/recover prohibited; code fails closed; complete appointment through the approved identity process |
| High | Durable owner approval evidence is pending for trust, ownership, SLO, and takeover governance. | Project Owner / control-plane owner | explicit owner-approval checkpoint | AC-G-1-04 and the control-plane owner veto cannot pass | retain `FAIL`; obtain a durable approval record, then request formal REVIEW |
| Medium | Ruff executes but reports 486 repository findings; the type-checker, secret-scanner, and `pip-audit` remain unavailable. A complete Node lockfile and offline clean-install proof now exist, but `registry.npmmirror.com` approval and audit-advisory freshness remain unproven. | security owner | approved tooling/source checkpoint and clean results before Gate PASS | AC-GLOBAL-04 cannot pass | repair Ruff findings without weakening rules; approve or replace the Node registry source; run an approved fresh audit; provision exact type-checker, TruffleHog/Gitleaks, and `pip-audit` tools/scopes |

No Critical or Low risk is recorded. The table has exactly two High and one
Medium open risks, matching `summary.md`'s `0/2/1/0` tally.

## Deferred platform facts

The following are truthful future-platform facts, not counted as additional
open Gate risks because G-1 neither removes nor cuts over these mechanisms:

- UNKNOWN production compatibility metrics continue to block compatibility
  removal; the repository baseline is not production telemetry.
- Flow Memory reports `user_version=0`; schema versioning and any migration or
  read-source cutover remain future owner-gated work.
- recovery remains human-checkpointed rather than probe-gated, and the
  cross-operation automatic failure-budget/reset model remains a later Gate
  obligation.

These deferrals do not weaken the three current blockers, authorize G0, or
turn unknown platform state into PASS evidence.
