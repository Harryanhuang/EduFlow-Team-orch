# G-1 Known Risks and Blocking Conditions

Submission target: `58d926778dde76724467b2eab307e80b0a1c5ea3`
Result: PASS (zero open Gate risks; formal REVIEW pending)

No Critical, High, Medium, or Low Gate risk is open, matching `summary.md`'s
`0/0/0/0` tally. The former Flow Memory
dependency risk is closed by the published, pinned, audited, clean-install
evidence for `flow-memory==0.1.1`.

## Closed owner checkpoints

| Closed checkpoint | Evidence |
|---|---|
| Structured runtime authority | Kenny / `ou_557e95aadc346010e58dbc71090123f3`, provisioned under `team.runtime_operators`, config generation `edc3a3ac9b8f328e` |
| Governance approval | OWNER comment `https://github.com/Harryanhuang/EduFlow-Team-orch/issues/7#issuecomment-4953662798`; revision/blob bindings in `owner-checkpoint.md` |

Formal `worker_review` REVIEW and manager CLOSEOUT are ordered process gates,
not waived risks. Until they complete, the overall acceptance result remains
FAIL and G0 remains unauthorized.

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

These deferrals do not authorize G0 or turn unknown platform state into PASS
evidence for later Gates.
