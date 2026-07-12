# G-1 Acceptance Summary

Gate: G-1
Revision: cc95c5a488a8cd699dff515eadf431277669ffc6
Config generation: production `00773fbb4eb5ed7f`; isolated implementation config is intentionally distinct
Environment: isolated `codex/eduflow-upgrade-gates` worktree plus read-only production probes against the deployed checkout
Acceptance result: FAIL
Mandatory criteria passed/total: 9/12
Open Critical/High/Medium/Low: 0/2/1/0
Rollback tested: yes — disposable worktree reverse-applied the full G-1 diff to `bde14c5ce94aacd99ef80f9c11b65092dcf25fc3`; baseline pytest passed
Reviewer: pending independent `worker_review` REVIEW after final evidence refresh
Manager closeout: blocked — manager must not CLOSEOUT before a valid REVIEW and all mandatory criteria pass

## Current decision

This package is deliberately a `FAIL`, not a conditional result. The required
structured `runtime_operator` identity is not provisioned and owner approval
evidence has not been recorded. The tracked placeholder identity is explicitly
not an actor and must not be used as approval or authorization evidence.

The package also records unavailable mandatory security scanners and the Node
audit lockfile failure. Those gaps are not represented as `not_applicable`.
No G0 work is authorized by this package.

Final verification refresh: current-revision full pytest passed 3161 tests
in 289.02s; the disposable rollback baseline passed 3014 tests in
`252.77s`. Production health, runtime list and strict workflow validation
passed; topology had one transient fail-closed legacy-entry observation and a
subsequent clean explicit-production audit.
