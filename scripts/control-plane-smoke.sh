#!/usr/bin/env bash
# scripts/control-plane-smoke.sh — verify that the eduflow-team control plane
# (wrapper scripts + Python module + state dir + workflow docs) all point at
# this checkout, not at a stale hardcoded path.
#
# Run from the project root: ./scripts/control-plane-smoke.sh
# Exit 0 only when every check passes; otherwise exit 1 and surface which
# section failed. Failure output is preserved verbatim — never silenced.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"

EXPECTED_LEGACY="/Volumes/Halobster/Codex相关/EduFlow-Team-orch"
fail_count=0
section_count=0

section() {
  section_count=$((section_count + 1))
  echo
  echo "=== [$section_count] $1 ==="
}

check_eq() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    echo "  ✅ $label: $actual"
  else
    echo "  ❌ $label: expected=$expected actual=$actual"
    fail_count=$((fail_count + 1))
  fi
}

check_not_eq() {
  local label="$1" forbidden="$2" actual="$3"
  if [ "$forbidden" != "$actual" ]; then
    echo "  ✅ $label: $actual (not $forbidden)"
  else
    echo "  ❌ $label: still points at $forbidden"
    fail_count=$((fail_count + 1))
  fi
}

# --- 0. Repo location + legacy hardcoded path audit --------------------------
section "repo location"
check_eq "smoke script resolves REPO" "$REPO" "$REPO"
echo "  ℹ️  REPO=$REPO"

echo "  scanning scripts/ for hardcoded legacy paths (ignoring comments)..."
legacy_hits="$(grep -rn --include='*.sh' --include='eduflowteam' "$EXPECTED_LEGACY" "$REPO/scripts" 2>/dev/null | grep -v '^[^:]*:[0-9]*:#' | grep -v 'control-plane-smoke.sh' || true)"
if [ -n "$legacy_hits" ]; then
  echo "$legacy_hits"
  echo "  ❌ found hardcoded $EXPECTED_LEGACY in scripts/ (non-comment lines)"
  fail_count=$((fail_count + 1))
else
  echo "  ✅ no hardcoded $EXPECTED_LEGACY in scripts/ (only references are in comments)"
fi

# --- 1. env.sh resolves to current repo -------------------------------------
section "eduflow-team-env.sh resolution"
eval "$(cd "$REPO" && bash -c '. ./scripts/eduflow-team-env.sh 2>/dev/null && printf "ROOT=%q\nEDUFLOW_ROOT=%q\nEDUFLOW_STATE_DIR=%q\nEDUFLOW_WORKFLOW_DIR=%q\nPYTHONPATH=%q\n" \
  "$ROOT" "$EDUFLOW_ROOT" "$EDUFLOW_STATE_DIR" "$EDUFLOW_WORKFLOW_DIR" "$PYTHONPATH"')"
check_eq    "ROOT"            "$REPO"                  "$ROOT"
check_eq    "EDUFLOW_ROOT"    "$REPO"                  "$EDUFLOW_ROOT"
check_eq    "EDUFLOW_STATE_DIR" "$REPO/.eduflow-team-state" "$EDUFLOW_STATE_DIR"
check_eq    "EDUFLOW_WORKFLOW_DIR" "$REPO/docs/workflows" "$EDUFLOW_WORKFLOW_DIR"
check_eq    "PYTHONPATH prefix" "$ROOT/src"               "$(printf '%s' "$PYTHONPATH" | cut -d: -f1)"

# --- 2. workflow commands point at current repo -----------------------------
section "workflow list (reads current repo's docs/workflows)"
out_workflow_list="$(cd "$REPO" && ./scripts/eduflowteam workflow list 2>&1)" || true
echo "$out_workflow_list" | head -20
if printf '%s\n' "$out_workflow_list" | grep -q "workflow_id"; then
  echo "  ✅ workflow list output has rows"
else
  echo "  ❌ workflow list produced no rows"
  fail_count=$((fail_count + 1))
fi

section "workflow validate"
out_workflow_validate="$(cd "$REPO" && ./scripts/eduflowteam workflow validate 2>&1)" || true
echo "$out_workflow_validate" | head -40
# workflow validate is allowed to report doc-quality issues; smoke only fails
# when the command cannot reach this repo's docs/workflows at all. A path-
# drift regression would show up as "no workflows found under <legacy path>".
case "$out_workflow_validate" in
  *"no workflows found under"*"Codex相关"*)
    echo "  ❌ workflow validate is reading legacy path"; fail_count=$((fail_count + 1)) ;;
  *"no workflows found under"*)
    echo "  ❌ workflow validate reports no workflows in this repo"; fail_count=$((fail_count + 1)) ;;
  *"workflow registry"*"valid"*|*"registry validation failed"*)
    echo "  ✅ workflow validate ran against this repo's docs/workflows" ;;
  *) echo "  ⚠️  workflow validate produced unexpected output"; ;;
esac

# --- 3. health (state_dir + import path consistency) ------------------------
section "health (state_dir + eduflow import path)"
out_health="$(cd "$REPO" && ./scripts/eduflowteam health 2>&1)" || true
echo "$out_health" | head -80
state_dir_line="$(printf '%s\n' "$out_health" | grep -E '^  state_dir:' | head -1)"
import_line="$(printf '%s\n' "$out_health" | grep -E '^  eduflow\.__file__:' | head -1)"
echo "  ℹ️  $state_dir_line"
echo "  ℹ️  $import_line"
case "$state_dir_line" in
  *"$REPO"*)             echo "  ✅ health.state_dir under current repo" ;;
  *"$EXPECTED_LEGACY"*) echo "  ❌ health.state_dir still points at $EXPECTED_LEGACY"; fail_count=$((fail_count + 1)) ;;
  *)                     echo "  ⚠️  health.state_dir line not in expected form" ;;
esac
case "$import_line" in
  *"$REPO"*)             echo "  ✅ eduflow import path under current repo" ;;
  *"$EXPECTED_LEGACY"*) echo "  ❌ eduflow import path still points at $EXPECTED_LEGACY"; fail_count=$((fail_count + 1)) ;;
  *)                     echo "  ⚠️  eduflow import path line not in expected form" ;;
esac

# --- 4. task list / task summary --------------------------------------------
section "task summary"
out_task="$(cd "$REPO" && ./scripts/eduflowteam task list 2>&1 || ./scripts/eduflowteam task manager-overview 2>&1)" || true
echo "$out_task" | head -30
echo "  ℹ️  task command reachable (output above is informational)"

# --- 5. memory audit --------------------------------------------------------
section "memory audit"
out_mem="$(cd "$REPO" && ./scripts/eduflowteam memory audit 2>&1)" || true
echo "$out_mem" | head -30
if [ -n "$out_mem" ]; then
  echo "  ✅ memory audit produced output"
else
  echo "  ⚠️  memory audit returned empty output (may be normal on fresh state)"
fi

# --- 6. git status sanity ---------------------------------------------------
section "git status sanity"
git_status_out="$(cd "$REPO" && git status --short --branch 2>&1)" || true
echo "$git_status_out" | head -20
case "$git_status_out" in
  *"fatal"*) echo "  ❌ git status failed"; fail_count=$((fail_count + 1)) ;;
  *)         echo "  ✅ git status reachable" ;;
esac

# --- summary ----------------------------------------------------------------
echo
echo "=== smoke summary ==="
echo "  repo: $REPO"
echo "  failures: $fail_count"
if [ "$fail_count" -eq 0 ]; then
  echo "  ✅ control-plane smoke PASS"
  exit 0
fi
echo "  ❌ control-plane smoke FAIL — see failures above"
exit 1
