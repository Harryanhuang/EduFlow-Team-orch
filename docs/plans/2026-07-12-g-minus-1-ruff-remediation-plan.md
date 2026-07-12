# G-1 Ruff Remediation Plan

**Status:** active cleanup plan under the authoritative 2026-07-12 master plan
and acceptance contract.

**Gate boundary:** G-1 Task 7 only. This work may make the mandatory Ruff check
green; it does not approve governance, appoint an actor, satisfy another
scanner, issue REVIEW/CLOSEOUT, or authorize G0.

## Baseline

Command:

```bash
uvx --offline ruff==0.15.10 check src tests scripts --statistics
```

Result: 486 findings: 254 F401, 71 F841, 41 F541, 34 E701, 26 E741,
15 E402, 15 E731, 12 E401, 8 E702, 7 F811, and 3 F821.

Distribution: 228 under `src`, 204 under `tests`, and 54 under `scripts`.
The compatibility re-export shim `src/eduflow/memory/__init__.py` accounts for
133 intentional F401 findings; `scripts/audit_production_topology.py` accounts
for 44 compact-statement findings.

## Non-negotiable constraints

- Do not add global Ruff ignores or weaken the selected rule set.
- Do not run Ruff unsafe fixes against the repository.
- Preserve the public compatibility exports of `eduflow.memory`.
- Treat F821, F811, F841, and ambiguous-name findings as possible correctness
  defects, not formatting noise.
- Lock behavior with focused tests before each production-code batch.
- Keep each commit single-purpose, spec-reviewed, quality-reviewed, and Lore
  formatted.
- Do not touch the production dirty checkout.
- Run the full regression once after all Ruff batches, not after each mechanical
  batch; focused and adjacent tests gate every intermediate commit.

## Execution batches

### Batch R1: Compatibility re-export contract

1. Add a deterministic characterization test that captures every explicit
   compatibility re-export with its source module, name, and alias; require the
   legacy `from flow_memory import *` bridge to remain exactly once, and verify
   representative runtime imports used by EduFlow. Dynamic wildcard names are
   covered by the adjacent memory regression rather than unstable namespace
   enumeration because legacy tests attach compatibility doubles at runtime.
2. Verify the test passes before cleanup.
3. Represent intentional re-exports explicitly through a stable `__all__` or
   explicit aliases; do not delete them and do not hide the whole file behind a
   blanket F401 suppression.
4. Require Ruff clean for the shim and run the memory-focused regression suite.

### Batch R2: Production correctness findings

1. Address the three F821 undefined names first with failing regression tests.
2. Resolve F811, F841, E741, E731, E402, and F541 in `src` one file or tightly
   coupled surface at a time.
3. Prefer deletion of dead imports/assignments; preserve values with documented
   intent where evaluation has a side effect.
4. Run each module's focused tests and the complete `src` Ruff check.

### Batch R3: Test-suite hygiene

1. Remove genuinely unused imports and variables in tests.
2. Rename ambiguous variables and replace lambda assignments without changing
   scenario semantics.
3. Split multi-import statements and move imports only where fixture/bootstrap
   ordering remains intact.
4. Run every touched test file plus `ruff check tests`.

### Batch R4: Script readability and behavior lock

1. Add or reuse focused tests for each touched script.
2. Expand E701/E702 compact statements without altering exit codes, output,
   redaction, or read-only behavior.
3. Resolve remaining script imports, variables, and lambda assignments.
4. Run script-focused tests, `py_compile`, and `ruff check scripts`.

### Batch R5: Gate verification

1. Run `ruff check src tests scripts` and require zero findings.
2. Run compileall, full pytest, pip check, and Git diff checks once.
3. Refresh all affected G-1 evidence ledgers with raw counts and commands.
4. Obtain independent specification and quality reviews.
5. Keep G-1 FAIL if any owner, authority, type, secret, dependency-audit,
   registry-provenance, formal REVIEW, or CLOSEOUT checkpoint remains absent.

## Rollback

Each batch is an independent Lore commit and can be reverted without reverting
the Node lockfile or prior G-1 evidence work. If a focused regression changes
behavior, revert that batch and keep its Ruff findings open rather than adding
an ignore.
