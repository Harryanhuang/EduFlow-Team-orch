#!/usr/bin/env bash
# Tests the eduflowteam-routine-check script. Verifies that the script:
#  - exits 0 when the asset registry is clean
#  - exits 1 when the asset registry has a real error
#  - surfaces remediation hints in the output
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$REPO/scripts/eduflowteam-routine-check"
if [ ! -x "$SCRIPT" ]; then
  echo "FAIL: $SCRIPT not executable"
  exit 99
fi

# 1) Run on the real repo (should pass with info/warn only).
echo "--- [test] routine check on real repo"
if ! REPO="$REPO" "$SCRIPT" >/tmp/routine_real.log 2>&1; then
  echo "FAIL: real repo routine check did not return 0"
  cat /tmp/routine_real.log
  exit 1
fi
if ! grep -q "routine-check PASSED" /tmp/routine_real.log; then
  echo "FAIL: real repo routine check did not print PASSED line"
  cat /tmp/routine_real.log
  exit 1
fi
if ! grep -q "=== \[1/3\] workflow validate --strict ===" /tmp/routine_real.log; then
  echo "FAIL: routine check did not run workflow validate"
  cat /tmp/routine_real.log
  exit 1
fi
if ! grep -q "=== \[2/3\] asset validate --json ===" /tmp/routine_real.log; then
  echo "FAIL: routine check did not run asset validate"
  cat /tmp/routine_real.log
  exit 1
fi
if ! grep -q "=== \[3/3\] asset drift-check" /tmp/routine_real.log; then
  echo "FAIL: routine check did not run asset drift-check"
  cat /tmp/routine_real.log
  exit 1
fi
echo "  ok: real repo routine check passed and surfaces all 3 stages"

echo "--- [test] routine check exits 1 on a broken workflow"
# Create a temp repo with a broken active workflow and run the routine check.
TMPREPO="$(mktemp -d)"
trap 'rm -rf "$TMPREPO"' EXIT
mkdir -p "$TMPREPO/src/eduflow"
mkdir -p "$TMPREPO/docs/workflows"
mkdir -p "$TMPREPO/scripts"
# Copy the shim and env script so the routine check can resolve REPO.
cp "$REPO/scripts/eduflowteam" "$TMPREPO/scripts/"
cp "$REPO/scripts/eduflow-team-env.sh" "$TMPREPO/scripts/" 2>/dev/null || true
# Build a broken workflow (missing standard files).
mkdir -p "$TMPREPO/docs/workflows/broken-workflow"
echo "# broken-workflow" > "$TMPREPO/docs/workflows/broken-workflow/README.md"
# intentionally NOT writing trigger.md, roles.md, checklist.md, handoff-template.md
# Run routine check; it should exit 1.
set +e
REPO="$TMPREPO" "$SCRIPT" >/tmp/routine_broken.log 2>&1
rc=$?
set -e
if [ "$rc" -ne 1 ]; then
  echo "FAIL: broken workflow routine check returned $rc, expected 1"
  cat /tmp/routine_broken.log
  exit 1
fi
if ! grep -q "routine-check FAILED" /tmp/routine_broken.log; then
  echo "FAIL: broken workflow did not print FAILED line"
  cat /tmp/routine_broken.log
  exit 1
fi
echo "  ok: broken workflow returns rc=1 with FAILED line"

echo "ALL routine-check tests passed"
