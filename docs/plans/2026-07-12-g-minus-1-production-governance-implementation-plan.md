# G-1 Production Facts and Governance Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task.

**Goal:** Produce machine-verifiable production topology, state/config inventory, historical-plan ledger, trust/ownership governance, and an executable human-takeover circuit breaker that satisfy AC-G-1-01 through AC-G-1-05.

**Architecture:** Keep production discovery read-only and dependency-injected. The topology auditor composes existing runtime path/config/tmux/watchdog facts into a deterministic, redacted JSON report; Markdown inventories are generated or verified against explicit schemas. A small file-backed human-takeover state becomes the common fail-closed guard for automated recovery, while operator enter/status/recover actions remain explicit and auditable.

**Tech Stack:** Python 3.10+ stdlib, existing EduFlow runtime/store patterns, pytest, Markdown governance ledgers, tmux/ps/git read-only probes.

---

## Gate invariants

- Work only in `codex/eduflow-upgrade-gates`; never alter the user's dirty checkout.
- Do not emit configuration values, environment values, tokens, secrets, or full command lines containing credentials.
- Unknown checkout, revision, PID ownership, config source, memory DB, credential source, or control-plane owner makes G-1 fail closed.
- Every production behavior change follows RED → GREEN → adjacent negative test.
- G-1 does not send external messages, rotate credentials, rewrite Git history, or switch production data sources.
- `worker_review` owns the formal REVIEW; `manager` remains the only CLOSEOUT owner and does not implement artifacts.

## Task 1: Freeze baseline and AC mapping

**Files:**
- Create: `acceptance/G-1/baseline-status.txt`
- Create: `acceptance/G-1/ac-task-test-map.md`

**Steps:**
1. Record branch, HEAD, `git status --short`, Python version, config path, state directory, and the original dirty-worktree file list without secret values.
2. Record the clean baseline `2768 passed` result and five existing warnings.
3. Map AC-G-1-01..05 and every G-1 veto to the task, automated test, runtime command, and evidence file that proves it.
4. Verify that no acceptance claim relies only on prose.

## Task 2: Build the read-only production-topology auditor

**Files:**
- Create: `tests/unit/test_audit_production_topology.py`
- Create: `scripts/audit_production_topology.py`
- Create: `docs/operations/eduflow-production-topology.md`

**RED:**
1. Add tests for deterministic JSON containing daemon, pane, and agent-process records with PID, absolute checkout, commit SHA, Python/CLI runtime, config path/hash, state dir, Lark profile, tmux session, daemon profile, and startup entry.
2. Add negative tests for dead/corrupt PID, command-entry drift, unknown checkout/revision, pane cwd drift, missing tmux/ps/git, and config hash changes.
3. Add redaction tests proving config values, environment values, token-like strings, and sensitive command arguments never appear.
4. Run `python3 -m pytest tests/unit/test_audit_production_topology.py -q` and capture the expected missing-module/script failure.

**GREEN:**
5. Implement injected subprocess/filesystem probes using existing `runtime.paths`, `runtime.config`, watchdog daemon specs, tmux enumeration, `ps`, and `git -C`.
6. Emit stable JSON with top-level `ok`, `generated_at`, `checkout`, `config`, `state`, `daemons`, `panes`, `agent_processes`, `errors`, and `redactions`.
7. Return non-zero when a live production process cannot be tied to checkout/revision/config/state.
8. Run focused tests, then render the Markdown topology from the real production checkout/state.
9. Manually cross-check at least three live panes against tmux, ps, cwd, Git HEAD, and config SHA-256; record commands and redacted results.

**Commit:** one Lore commit for auditor + topology baseline.

## Task 3: Establish the historical-plan ledger

**Files:**
- Create: `tests/unit/test_plan_status_index.py`
- Create: `docs/plans/PLAN_STATUS_INDEX.md`

**RED/GREEN:**
1. Write a test that enumerates every top-level `docs/plans/*.md` except the index and requires exactly one index row per file.
2. Require status in `historical|active|superseded|observation-only`; active rows require Gate/Task links.
3. Require every `DONE` assertion to carry code plus commit/test evidence; unproved items must be labelled unverified or incomplete.
4. Run the focused test and prove it fails because the index is missing.
5. Build the index from current files, treating old plan text as claims rather than implementation truth.
6. Re-run focused tests and a duplicate/supersession negative test.

**Commit:** one Lore commit for the historical-plan ledger.

## Task 4: Establish state, configuration, and credential-source inventory

**Files:**
- Create: `tests/unit/test_state_config_inventory.py`
- Create: `docs/operations/state-and-config-inventory.md`

**RED/GREEN:**
1. Write a schema test requiring inventory rows for inbox, task snapshot/events, generic events, cursor, seen, runtime status, switch events, loop runs, workflow assets, Skill assets, identity assets, memory DB, config, token cache, and agent secret source.
2. Require authoritative location, writer, reader, owner, permissions, backup, retention, recovery, and migration requirement for every row.
3. Require explicit disclosure of legacy/fallback paths and reject unknown memory DB or credential sources.
4. Prove the test fails while the inventory is absent.
5. Populate the inventory from current code and real runtime path/config facts without secret values.
6. Re-run the focused test and manually verify the active memory DB path and permissions.

**Commit:** one Lore commit for state/config inventory.

## Task 5: Implement human-takeover state and fail-closed guard

**Files:**
- Create: `tests/unit/test_human_takeover.py`
- Create: `src/eduflow/runtime/human_takeover.py`
- Create: `src/eduflow/commands/human_takeover.py`
- Modify: `src/eduflow/cli.py`
- Modify: `src/eduflow/commands/watchdog.py`
- Modify: `src/eduflow/commands/runtime_switch.py`
- Create: `tests/integration/test_human_takeover_circuit_breaker.py`

**RED:**
1. Specify durable states `inactive|active|recovering`, reason/source/actor/entered_at/recovery_steps, generation, and append-only audit events.
2. Test idempotent enter, status JSON, unauthorized recovery rejection, explicit operator recovery, corrupt-state fail closed, and secret redaction.
3. Test that repeated runtime-switch recovery failures enter takeover and that all subsequent automatic switch attempts stop before side effects.
4. Test that manual read-only status remains available while automated writes are blocked.
5. Run focused tests and confirm failures are caused by the missing module/command/guard.

**GREEN:**
6. Implement atomic local state writes and append-only audit using existing state-dir/path conventions.
7. Implement `eduflow human-takeover status|enter|recover --json`; recovery requires configured operator/admin identity and a reason.
8. Add a shared guard to watchdog/failover automatic switch paths; do not broaden the feature to G0 message retry or G3 Workflow repair yet.
9. Re-run unit/integration tests and existing runtime-switch/watchdog suites.
10. Execute a controlled isolated-state simulation: exceed switch failure budget, observe `active`, prove a new automated action is rejected, inspect operator-visible reason/steps, recover explicitly, and prove action eligibility returns.

**Commit:** one Lore commit for executable takeover.

## Task 6: Publish trust, SLO, ownership, and exception governance

**Files:**
- Create: `tests/unit/test_g_minus_1_governance_docs.py`
- Create: `docs/architecture/TRUST_MODEL.md`
- Create: `docs/operations/CONTROL_PLANE_SLO.md`
- Create: `docs/operations/HUMAN_TAKEOVER_RUNBOOK.md`
- Create: `docs/governance/OWNERSHIP.md`
- Create: `docs/governance/DECISION_AND_EXCEPTION_PROCESS.md`
- Create: `docs/governance/COMPATIBILITY_DEBT.md`

**RED/GREEN:**
1. Test complete authority rows for member/operator/admin/manager/worker/reviewer/builder/runtime operator/recorder and tool/credential/file/external-system dimensions.
2. Test required owners, REVIEW=`worker_review`, CLOSEOUT=`manager`, manager dispatch-only, and exception owner/reason/scope/expiry/removal-test fields.
3. Test six approved SLOs and circuit-breaker thresholds with explicit human-takeover transitions.
4. Prove missing documents fail, then add the minimum complete governance records.
5. Re-run focused tests and inspect that no credential value or unbounded exception exists.

**Commit:** one Lore commit for governance documents.

## Task 7: Run Gate verification and produce the nine-file acceptance package

**Files:**
- Create: `acceptance/G-1/summary.md`
- Create: `acceptance/G-1/changed-files.txt`
- Create: `acceptance/G-1/test-results.txt`
- Create: `acceptance/G-1/fault-injection-results.txt`
- Create: `acceptance/G-1/security-results.txt`
- Create: `acceptance/G-1/migration-results.txt`
- Create: `acceptance/G-1/rollback-proof.md`
- Create: `acceptance/G-1/known-risks.md`
- Create: `acceptance/G-1/review-verdict.md`

**Verification commands:**
1. `./scripts/eduflowteam health --json`
2. `./scripts/eduflowteam runtime list --json`
3. `./scripts/eduflowteam workflow validate --strict`
4. `python3 scripts/audit_production_topology.py --json`
5. `python3 -m compileall -q src tests scripts`
6. `python3 -m pytest`
7. `python3 -m pip check`
8. `git diff --check`
9. Ruff, configured type checker scope, secret scan, `pip-audit`, and Node audit when applicable.
10. Roll back the G-1 code commits in a disposable verification worktree, prove baseline tests still run, then restore and re-run focused tests.

Record command, UTC/local timestamp, revision, exit code, complete result summary, and any N/A rationale. Full pytest count must be at least 2768 with no new skip/xfail.

## Task 8: Independent REVIEW and closeout checkpoint

1. Give a fresh reviewer the AC map, diff, nine-file package, real topology evidence, and veto list.
2. Reviewer independently reruns representative commands and returns PASS, allowed CONDITIONAL PASS, or FAIL in `review-verdict.md`.
3. Fix every finding with TDD and refresh all affected evidence.
4. Do not enter G0 until `review-verdict.md` is PASS (or contract-valid CONDITIONAL PASS) and the manager closeout field records the Gate decision.

