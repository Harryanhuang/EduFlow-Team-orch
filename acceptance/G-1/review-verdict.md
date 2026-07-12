# G-1 Independent Final Re-REVIEW Verdict

Reviewer: independent Codex reviewer (fresh read-only review after both Task 8 security remediations)

Review scope: the two authoritative 2026-07-12 Gate documents; the current
G-1 worktree delta over
`bde14c5ce94aacd99ef80f9c11b65092dcf25fc3`, including revision
`cc95c5a488a8cd699dff515eadf431277669ffc6`; all nine acceptance records;
and the current Task 8 source and tests.  This reviewer performed no production
takeover, config change, credential action, external send, approval write, or
manager action.

Verdict: FAIL

Formal-status note: this is independent supporting review evidence, not the
required formal `worker_review` REVIEW event.  It cannot substitute for that
event or authorize a manager CLOSEOUT.

## Evidence verified

- `acceptance/G-1/` contains all nine required records.  The package contract
  test passed independently in this review.  `changed-files.txt` exactly
  separates the committed baseline-to-`cc95c5a4` changes from the current
  uncommitted Task 7/8 delta: six modified tracked paths and eight untracked
  paths.  The listed current paths match independent `git diff --name-status`,
  `git ls-files --others --exclude-standard`, and `git status --short` output.
- The current test ledger records the final full suite as **3161 passed in
  289.02s**, plus zero-exit `compileall -q src tests scripts`, `pip check`, and
  `git diff --check`.  These are recorded final-run evidence, rather than a
  claim that this reviewer repeated the 289-second full suite.  This reviewer
  independently reran the Task 8 negative and side-effect tests plus the
  runtime CLI and package-contract tests: **24 passed**; `git diff --check`
  also exited zero.
- **Task 8 remediation 1 is closed.**  `runtime_switch._authorized_actors()`
  now preserves configured strings and applies the shared
  `is_provisioned_actor_id` check before returning any authorization set.
  Consequently placeholder-shaped values, `your_` values, and empty string
  entries invalidate the whole set.  The parametrized tests at
  `tests/unit/test_human_takeover.py:225-241` prove rejection.
- **Task 8 remediation 2 is closed.**  Each explicitly present authority field
  (`admins`, `runtime_operators`, or `runtime_operator`) is independently
  shape-validated at `src/eduflow/commands/runtime_switch.py:38-56`; any
  malformed value makes `_authorized_actors()` return an empty set even if a
  different field contains a syntactically valid actor.  The integration-level
  CLI negative cases at `tests/unit/test_human_takeover.py:244-272` further
  prove rejection occurs before either prepared audit or restart.  Missing
  fields remain intentionally valid-and-empty; they are not malformed
  configured authority values.
- The disposable reverse-apply proof records an exact baseline comparison and
  **3014 passed** at the baseline.  This is valid code-rollback evidence only;
  it does not claim a production-state, credential, or approval rollback.

## Remaining blockers (not remediated)

1. **High — real structured `runtime_operator` appointment is still pending.**
   The deployed configuration's template actor row is a placeholder, not a
   usable structured identity.  The implementation correctly rejects it;
   no placeholder or invented identity may be used to satisfy AC-G-1-04.
2. **High — durable owner approval evidence is still pending.**  Governance
   documents correctly describe draft ownership and do not itself appoint or
   approve an actor.  Required owner authorization must be recorded by the
   authorized owner, not manufactured in this acceptance package.
3. **Medium — security/supply-chain evidence remains incomplete.**
   `security-results.txt` records unavailable Ruff, Pyright/mypy, secret
   scanner, and `pip-audit`, and an `npm audit` `ENOLOCK` result.  They are not
   `not_applicable`; AC-GLOBAL-04 cannot pass until the authorized security
   checkpoint supplies the scanners and handles the Node lockfile.
4. **Medium — formal acceptance ownership is incomplete.**  The required
   `worker_review` REVIEW is still pending.  Even a future PASS review cannot
   substitute for the real appointment, owner evidence, or security evidence;
   manager remains the only CLOSEOUT owner after all required criteria pass.

## Decision

The two Task 8 security findings are **remediated and independently verified**.
They are not current reasons to reject this revision.  However the remaining
two High external checkpoints mean AC-GLOBAL-05 is not satisfied, and the
missing security/supply-chain evidence separately prevents a conditional pass.

**G-1 status: FAIL.  G0: not authorized.  Formal `worker_review` REVIEW:
pending.  Manager CLOSEOUT: prohibited.**

Next actions are intentionally owner-gated: provision a real structured
`runtime_operator`, record durable owner approval evidence, complete the
approved security-scanner and Node-lockfile checkpoint, refresh the package,
then obtain a formal independent `worker_review` REVIEW.  Do not create a
placeholder appointment, approval, scanner result, or CLOSEOUT event.

Result: FAIL
