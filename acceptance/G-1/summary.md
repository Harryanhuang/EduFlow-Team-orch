# G-1 Acceptance Summary

Gate: G-1
Revision: 58d926778dde76724467b2eab307e80b0a1c5ea3
Config generation: production `edc3a3ac9b8f328e`; isolated implementation config is intentionally distinct
Environment: isolated `codex/eduflow-upgrade-gates` worktree plus read-only production probes against the deployed checkout
Acceptance result: PASS
Mandatory criteria passed/total: 12/12
Open Critical/High/Medium/Low: 0/0/0/0
Rollback tested: yes — disposable worktree reverse-applied the target patch to `bde14c5ce94aacd99ef80f9c11b65092dcf25fc3` and proved exact tree equality; current full pytest also passed
Reviewer: worker_review — T-172 delivered and approved; REVIEW `log_1783916128818_c7c38dd6ae` binds `00c9d0f978a68f8f6469bf898064f6382b60b05a`
Manager closeout: PASS — CLOSEOUT `log_1783916506671_d734d310a7`; G-1 closed and G0 authorized

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

`Revision` is the immutable implementation submission target. Formal task
`T-172` reviewed the subsequent evidence-complete target
`00c9d0f978a68f8f6469bf898064f6382b60b05a`; this post-event refresh records
the already-issued REVIEW and CLOSEOUT without changing the reviewed candidate.

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
durable owner approval receipt in `owner-checkpoint.md`, not by an unverified
chat statement.

## Current decision

All twelve machine criteria are satisfied. Formal task `T-172` has
Status: delivered and Verdict: approved. The detailed reviewer-to-manager
message is `msg_1783916096247_873f6b9ba4`; the formal REVIEW is
`log_1783916128818_c7c38dd6ae`. Both explicitly name
`docs/plans/2026-07-12-eduflow-upgrade-acceptance-standard.md` and
`docs/plans/2026-07-12-eduflow-governed-team-operating-system-master-plan.md`.
Manager CLOSEOUT `log_1783916506671_d734d310a7` accepted the authoritative
ledger as AC-GLOBAL-01..07 plus AC-G-1-01..05 and stated that G-1 closed and
G0 authorized. G0 not completed: this decision permits the next Gate to begin
but does not claim any G0 criterion has passed.

Kenny remains provisioned only as the structured `runtime_operator`. The
general-operator placeholder remains a deny-all sentinel and is not appointment
evidence or general Slash authority.

The current submission passed the complete 3203-node regression. A read-only
production refresh at 2026-07-13T09:43:44+08:00 remained `ok=true` with three
daemons, eleven panes, eleven agent processes, zero suspects, and no audit
errors. The exact command, raw redacted JSON, output digest, production revision,
and config generation are persisted in `production-topology-refresh.json`.
Production now has the dedicated runtime-authority row in addition to the
general-operator deny-all sentinel. The historical
3014-test baseline rollback run was not repeated; the current exact rollback
content proof and focused acceptance-package tests are recorded separately.
