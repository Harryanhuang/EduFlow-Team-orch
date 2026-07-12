# G-1 Acceptance Summary

Gate: G-1
Revision: 2296dc08c14eae9de34accdf43d4a11c6b8ba68f
Config generation: production `00773fbb4eb5ed7f`; isolated implementation config is intentionally distinct
Environment: isolated `codex/eduflow-upgrade-gates` worktree plus read-only production probes against the deployed checkout
Acceptance result: FAIL
Mandatory criteria passed/total: 9/12
Open Critical/High/Medium/Low: 0/2/1/0
Rollback tested: yes — disposable worktree reverse-applied the target patch to `bde14c5ce94aacd99ef80f9c11b65092dcf25fc3` and proved exact tree equality; no pytest rerun
Reviewer: pending formal `worker_review` REVIEW after all external checkpoints and final evidence refresh
Manager closeout: blocked — manager must not CLOSEOUT before a valid REVIEW and all mandatory criteria pass

## Submission revision lineage

- implementation: `cc95c5a488a8cd699dff515eadf431277669ffc6`
- remediation: `d578691b8e1d3e0dc6f5221120c4a0d0e4ace6ab`
- security ledger: `2296dc08c14eae9de34accdf43d4a11c6b8ba68f`

`Revision` is the immutable submission target. This evidence-only freshness
delta is intentionally not assigned a self-referential revision; the formal
review event must bind the final committed HEAD when the external checkpoints
exist.

## Mandatory criteria ledger

| Criterion | Result | Evidence / blocker |
|---|---|---|
| AC-GLOBAL-01 workspace protection | PASS | isolated scoped worktree and baseline inventory |
| AC-GLOBAL-02 regression tests | PASS | recorded 3161-test submission run, compileall, pip check, and diff check |
| AC-GLOBAL-03 behavior tests | PASS | RED/GREEN and adjacent negative-path records |
| AC-GLOBAL-04 static and supply chain | FAIL | Node lock and offline install pass, but mirror/advisory freshness is unapproved; Ruff has 486 findings and required type/secret/dependency scanners remain unavailable |
| AC-GLOBAL-05 unresolved risks | FAIL | two High and one Medium open Gate risk remain |
| AC-GLOBAL-06 rollback | PASS | exact reverse-patch tree proof and forward recovery boundaries |
| AC-GLOBAL-07 observable state | PASS | CLI JSON and append-only audit evidence |
| AC-G-1-01 production topology | PASS | correlated daemon, pane, agent, checkout, runtime, config, and state facts |
| AC-G-1-02 data truth inventory | PASS | complete reader, writer, backup, permission, and migration ledger |
| AC-G-1-03 plan traceability | PASS | classified plan index with evidence links |
| AC-G-1-04 approved trust model | FAIL | real runtime authority appointment and durable owner approval are absent |
| AC-G-1-05 SLO and human takeover | PASS | isolated fail-closed takeover, visibility, and recovery simulation |

The ledger contains exactly twelve mandatory decision rows. Its nine `PASS`
rows are the source for `9/12`; the three `FAIL` rows cannot be waived by a
chat statement or by the historical independent supporting review.

## Current decision

This package remains a deliberate `FAIL`. The structured `runtime_operator`
identity is not provisioned, owner approval evidence is not recorded, and the
mandatory security/tooling checkpoint is incomplete. The tracked placeholder
is explicitly not an actor and cannot be used as approval or authorization
evidence. No G0 work is authorized.

The recorded 3161-test submission regression and historical 3014-test baseline
rollback run were not repeated during this evidence-only refresh. Current exact
rollback content proof and the focused acceptance-package test are recorded in
their respective ledgers.
