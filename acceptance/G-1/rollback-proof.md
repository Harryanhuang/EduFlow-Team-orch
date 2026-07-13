# G-1 Rollback Proof

Submission target: `58d926778dde76724467b2eab307e80b0a1c5ea3`
Baseline revision: `bde14c5ce94aacd99ef80f9c11b65092dcf25fc3`
Captured: `2026-07-13T09:02:00+08:00`
Environment: private `mktemp` directory with a detached child worktree;
the observed directory ended in `eduflow-g1-rollback.gxDLcq` and the EXIT trap
removed both its registered worktree and private directory.

## Reproducible procedure

```bash
set -euo pipefail
BASE=bde14c5ce94aacd99ef80f9c11b65092dcf25fc3
TARGET=58d926778dde76724467b2eab307e80b0a1c5ea3
TMP_ROOT="${TMPDIR:-/tmp}"
TMP_ROOT="${TMP_ROOT%/}"
TMP_ROOT="$(cd "$TMP_ROOT" && pwd -P)"
TMP_DIR="$(mktemp -d "$TMP_ROOT/eduflow-g1-rollback.XXXXXX")"
WT="$TMP_DIR/worktree"
PATCH="$TMP_DIR/submission.patch"
WT_REGISTERED=0
cleanup() {
  rc=$?
  trap - EXIT INT TERM
  if [[ "${WT_REGISTERED:-0}" -eq 1 ]] &&
    [[ "${WT:-}" == "$TMP_DIR/worktree" ]] &&
    git worktree list --porcelain | grep -Fqx "worktree $WT"; then
    if git worktree remove --force "$WT"; then
      :
    else
      cleanup_rc=$?
      [[ "$rc" -ne 0 ]] || rc=$cleanup_rc
    fi
  fi
  if [[ -n "${TMP_DIR:-}" && "$TMP_DIR" == "$TMP_ROOT"/eduflow-g1-rollback.* ]]; then
    if rm -rf -- "$TMP_DIR"; then
      :
    else
      cleanup_rc=$?
      [[ "$rc" -ne 0 ]] || rc=$cleanup_rc
    fi
  fi
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
git diff --binary "$BASE" "$TARGET" -- > "$PATCH"
PATCH_SHA256="$(shasum -a 256 "$PATCH" | awk '{print $1}')"
PATCH_BYTES="$(wc -c < "$PATCH" | tr -d ' ')"
git worktree add --detach "$WT" "$TARGET"
WT_REGISTERED=1
git -C "$WT" apply --reverse --index "$PATCH"
git -C "$WT" diff --quiet "$BASE" -- .
REVERSED_TREE="$(git -C "$WT" write-tree)"
BASE_TREE="$(git -C "$WT" rev-parse "$BASE^{tree}")"
TARGET_TREE="$(git -C "$WT" rev-parse "$TARGET^{tree}")"
[[ "$REVERSED_TREE" == "$BASE_TREE" ]]
printf 'patch_sha256=%s\npatch_bytes=%s\ntarget_tree=%s\nreversed_tree=%s\nbaseline_tree=%s\n' \
  "$PATCH_SHA256" "$PATCH_BYTES" "$TARGET_TREE" "$REVERSED_TREE" "$BASE_TREE"
```

## Machine evidence

| Check | Exit | Result |
|---|---:|---|
| Generate complete binary patch | 0 | PASS — 762796 bytes |
| Calculate patch SHA-256 | 0 | PASS |
| Create detached target worktree | 0 | PASS |
| Reverse-apply patch to index and worktree | 0 | PASS |
| Exact content comparison with baseline | 0 | PASS |
| Resolve target, reversed, and baseline tree hashes | 0 | PASS |
| Remove disposable worktree and patch | 0 | PASS |

- Patch SHA-256: `6717d46ee7aca86170449c2e7b4a72e2f0115514794125e16bf25cd590344bbe`
- Target tree: `3745d4d59aff4a2c3839c8c7063486b9c38f9072`
- Reversed tree: `05d26313ab96749b599459c5017e811cc1a060f0`
- Baseline tree: `05d26313ab96749b599459c5017e811cc1a060f0`

The equal reversed and baseline tree hashes, together with
`git diff --quiet` exit 0, prove exact repository-content reversal from the
submission target. The status-preserving EXIT trap checks that the worktree is
both inside this run's private directory and present in Git's worktree registry
before removal; it does not clean any fixed or caller-owned path. The source
worktree and production checkout were never modified.

No pytest command was run inside the disposable rollback worktree. The current
submission separately passed the full 3203-node regression; `3014 passed in
252.77s` remains the historical baseline rollback run.

Result: PASS — exact code-content rollback is reproducible. This proof does
not authorize credential rollback, production-state mutation, or data-source
switching.

The owner appointment and production config generation `edc3a3ac9b8f328e` are
outside the immutable implementation patch. Revoking that appointment requires
a new owner record, removal of only the dedicated `team.runtime_operators` row,
TOML validation, fail-closed eligibility proof, and a fresh topology audit. It
must not restore a credential or remove the general deny-all sentinel.
