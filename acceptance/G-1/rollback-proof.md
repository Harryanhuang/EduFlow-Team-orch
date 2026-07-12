# G-1 Rollback Proof

Revision under test: `cc95c5a488a8cd699dff515eadf431277669ffc6`
Baseline revision: `bde14c5ce94aacd99ef80f9c11b65092dcf25fc3`
Environment: disposable detached worktree `/tmp/eduflow-g1-rollback-cc95c5a-019f559d`

## Procedure

1. Created a disposable detached worktree at the implementation revision.
2. Produced the complete binary diff from the baseline to the implementation
   revision and reverse-applied it with `git apply --reverse --index`.
3. Verified `git diff --quiet <baseline> -- .`; exit 0 proved the temporary
   worktree content exactly matched the baseline.
4. Ran `/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest` in the
   reverted worktree.

## Evidence

| Check | Exit | Result |
|---|---:|---|
| Exact content comparison with baseline | 0 | PASS |
| Baseline full pytest | 0 | PASS — 3014 passed in 252.77s |

The original dirty production checkout was never changed. Restoring the
implementation is implicit: the shared implementation worktree was never
modified by the disposable reverse patch. Current-revision focused and full
tests are recorded separately in `test-results.txt` after this package is
made complete.

Result: PASS — code rollback is reproducible in a disposable worktree. This
does not authorize credential rollback or any production state rollback.
