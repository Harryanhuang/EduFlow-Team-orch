# G-1 AC-to-task/test/evidence map

This map prevents baseline collection from being mistaken for Gate acceptance. Every row requires direct evidence before the G-1 verdict can be `PASS`.

| Requirement | Implementation / verification task | Test or command | Required evidence |
|---|---|---|---|
| AC-G-1-01 Production topology complete | Inventory every EduFlow daemon, tmux pane, and primary Agent process; correlate PID, absolute checkout, revision, Python/CLI runtime, config path/hash, state dir, Lark profile, and entrypoint; sample three live panes | process inventory, `tmux list-panes`, revision/runtime/config/state inspection, three-pane correlation check | `production-topology.md`, sanitized machine-readable inventory, command transcript, three sampled correlations |
| AC-G-1-02 Data truth inventory complete | Map inbox, task, event, cursor, seen, runtime status, switch event, loop run, workflow asset, Skill asset, and memory DB to writers, readers, backup, permissions, and migration requirements | inventory completeness/schema check plus repository/runtime source tracing | `data-truth-inventory.md` with no missing required store or ownership field |
| AC-G-1-03 Legacy plan completion traceable | Classify every legacy plan as historical, active, superseded, or observation-only; link each DONE claim to code, commit, or test evidence | plan-index completeness check; validate all DONE evidence links | `legacy-plan-ledger.md` and link-validation transcript |
| AC-G-1-04 Trust model approved | Define a complete permission matrix for member, operator, admin, manager, worker, reviewer, builder, runtime operator, and recorder; document least privilege for every credential/tool | matrix completeness check; credential/tool coverage check; owner review | `trust-model.md`, review record, and approval evidence |
| AC-G-1-05 SLO and human takeover executable | Define SLOs and simulate repeated runtime-switch failure or retry exhaustion; enter `human_takeover`, stop new automation, and expose cause/recovery steps to operator | controlled takeover scenario and observable-state assertions | `slo-and-takeover.md`, scenario transcript, CLI/JSON state evidence, recovery evidence |
| VETO-1 No production process lacks checkout/revision | Reconcile every live production process to an absolute checkout and revision | topology reconciliation command/check | zero unmatched processes in `veto-checks.md` |
| VETO-2 Actual memory DB is known | Identify the authoritative memory DB path, owner, readers/writers, and schema/version without exposing stored values | runtime/config/source correlation and safe metadata inspection | authoritative DB record and corroborating evidence in `veto-checks.md` |
| VETO-3 Control-plane owner specified | Name the accountable control-plane owner and escalation path | ownership completeness check and owner review | approved ownership entry in `veto-checks.md` / trust model |
| VETO-4 Credential sources known | Inventory each credential source and consumer without recording secret values | sanitized config/env/secret-provider source tracing | complete redacted credential-source ledger in `veto-checks.md` |
| VETO-5 Human takeover path exists | Provide and exercise a documented takeover trigger, automation stop, operator visibility, and recovery path | same controlled scenario as AC-G-1-05 plus negative assertions that new automation stops | passing takeover transcript and operator-visible recovery evidence in `veto-checks.md` |

## Gate decision rule

G-1 may pass only when all five AC rows have complete direct evidence and all five veto checks report zero active vetoes. Baseline unit tests, compilation, dependency checks, and clean diffs are supporting evidence, not substitutes for production/runtime verification or approval.
