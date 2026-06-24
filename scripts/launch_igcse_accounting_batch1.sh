#!/usr/bin/env bash

set -euo pipefail

ROOT="/Volumes/Halobster/Codex相关/EduFlow-Team-orch"

# shellcheck source=/dev/null
. "$ROOT/scripts/eduflow-team-env.sh"

export PYTHONPATH="${PYTHONPATH:-$ROOT/src}"

CLI=(python3 -m eduflow.cli)
TASK_IDS=()

dispatch_task() {
  local title="$1"
  local output
  output="$("${CLI[@]}" task dispatch worker_course "$title" \
    --stage curriculum \
    --owner worker_course \
    --by manager \
    --desc "优化 topic 结构并产出题库前置 QA")"
  printf '%s\n' "$output"
  TASK_IDS+=("$(printf '%s' "$output" | sed -n 's/^✅ dispatched \\(T-[0-9]\\+\\):.*/\\1/p')")
}

echo "== Dispatch Batch 1 =="
dispatch_task "IGCSE Accounting 0452 Topic 1 - The fundamentals of accounting"
dispatch_task "IGCSE Accounting 0452 Topic 2 - Sources and recording of data"
dispatch_task "IGCSE Accounting 0452 Topic 3 - Verification of accounting records"

echo
echo "== Assign Reviewer =="
for task_id in "${TASK_IDS[@]}"; do
  if [ -z "$task_id" ]; then
    echo "❌ failed to resolve dispatched task id" >&2
    exit 1
  fi
  "${CLI[@]}" task assign-reviewer "$task_id" --reviewer review_course --by manager
done

echo
echo "== Snapshot =="
"${CLI[@]}" task manager-overview

cat <<'EOF'

Next recommended actions:
1. manager sends the batch kickoff message to the group
2. worker_course completes Topic 1-3 optimization + QA drafts
3. worker_course submits the dispatched task ids for review
4. review_course approves / rejects / manager_action with structured summary
5. auto_ops outputs a gap note after Batch 1 closes
EOF
