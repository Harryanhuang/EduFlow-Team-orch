# G-1 Acceptance Summary

Gate: G-1
Revision: 58d926778dde76724467b2eab307e80b0a1c5ea3
Config generation: production `edc3a3ac9b8f328e`; isolated implementation config is intentionally distinct
Environment: isolated `codex/eduflow-upgrade-gates` worktree plus read-only production probes against the deployed checkout
Acceptance result: FAIL
Mandatory criteria passed/total: 12/12
Open Critical/High/Medium/Low: 0/0/0/0
Rollback tested: yes — disposable worktree reverse-applied the target patch to `bde14c5ce94aacd99ef80f9c11b65092dcf25fc3` and proved exact tree equality; current full pytest also passed
Reviewer: pending formal `worker_review` REVIEW after all external checkpoints and final evidence refresh
Manager closeout: blocked — manager must not CLOSEOUT before a valid REVIEW and all mandatory criteria pass

## Submission revision lineage

- implementation: `cc95c5a488a8cd699dff515eadf431277669ffc6`
- remediation: `d578691b8e1d3e0dc6f5221120c4a0d0e4ace6ab`
- security ledger: `2296dc08c14eae9de34accdf43d4a11c6b8ba68f`
- Ruff R3 tests: `af15df34de310907feff3e93681952a443fb0bfb` (Lore carried forward by `6b4ec55a`)
- Ruff R4 scripts: `73e7b3f4cd47cbc48b985ccbf261266fe38b02d2`
- runtime authority consolidation: `21d000e5eca28c1ad5a91ad3485c548f8ce1c389`
- full-source mypy remediation: `175a7f31e0538ac646d9a6c523ba14638f662372`
- published Flow Memory dependency: `ad149069f246abe9bda93f184fd68d0106a4305d`
- topology classifier remediation / submission target: `58d926778dde76724467b2eab307e80b0a1c5ea3`

`Revision` is the immutable submission target. This evidence-only freshness
delta is intentionally not assigned a self-referential revision; the formal
review event must bind the final committed HEAD when the external checkpoints
exist.

## Mandatory criteria ledger

| Criterion | Result | Evidence / blocker |
|---|---|---|
| AC-GLOBAL-01 workspace protection | PASS | isolated scoped worktree and baseline inventory |
| AC-GLOBAL-02 regression tests | PASS | current 3203-node full regression, compileall, pip check, and diff check |
| AC-GLOBAL-03 behavior tests | PASS | RED/GREEN and adjacent negative-path records |
| AC-GLOBAL-04 static and supply chain | PASS | Ruff, TruffleHog, official npm audit, pip-audit, full-source mypy, and a Python 3.10 clean install of the pinned PyPI `flow-memory==0.1.1` dependency are clean |
| AC-GLOBAL-05 unresolved risks | PASS | owner appointment and governance approval are durably bound; zero open Gate risks |
| AC-GLOBAL-06 rollback | PASS | exact reverse-patch tree proof and forward recovery boundaries |
| AC-GLOBAL-07 observable state | PASS | CLI JSON and append-only audit evidence |
| AC-G-1-01 production topology | PASS | correlated daemon, pane, agent, checkout, runtime, config, and state facts |
| AC-G-1-02 data truth inventory | PASS | complete reader, writer, backup, permission, and migration ledger |
| AC-G-1-03 plan traceability | PASS | classified plan index with evidence links |
| AC-G-1-04 approved trust model | PASS | OWNER comment, approved revision blobs, unique Feishu identity resolution, and provisioned runtime authority |
| AC-G-1-05 SLO and human takeover | PASS | isolated fail-closed takeover, visibility, and recovery simulation |

The ledger contains exactly twelve mandatory decision rows. Its twelve `PASS`
rows are the source for `12/12`. The owner-controlled rows are supported by the
durable receipt in `owner-checkpoint.md`, not by an unverified chat statement.

## Current decision

All twelve machine criteria are now satisfied, but this package remains a
deliberate `FAIL` until the formal `worker_review` REVIEW binds the final
committed evidence revision. Kenny is provisioned only as the structured
`runtime_operator`, and the OWNER approval is durably recorded in
`owner-checkpoint.md`. The general-operator placeholder remains a deny-all
sentinel and is not appointment evidence. No G0 work is authorized yet.
This is durable owner approval, but it is not formal REVIEW or CLOSEOUT.

The current submission passed the complete 3203-node regression. A read-only
production refresh at 2026-07-13T09:43:44+08:00 remained `ok=true` with three
daemons, eleven panes, eleven agent processes, zero suspects, and no audit
errors. The exact command, raw redacted JSON, output digest, production revision,
and config generation are persisted in `production-topology-refresh.json`.
Production now has the dedicated runtime-authority row in addition to the
general-operator deny-all sentinel. The historical
3014-test baseline rollback run was not repeated; the current exact rollback
content proof and focused acceptance-package tests are recorded separately.
