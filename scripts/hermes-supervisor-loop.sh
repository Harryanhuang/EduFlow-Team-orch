#!/usr/bin/env bash

set -euo pipefail

ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

# shellcheck source=/dev/null
. "$ROOT/scripts/eduflow-team-env.sh"

export PYTHONPATH="${PYTHONPATH:-$ROOT/src}"
export LARK_CLI_SUPERVISOR_PROFILE="${LARK_CLI_SUPERVISOR_PROFILE:-hermes-supervisor}"
export EDUFLOW_STATE_DIR="${EDUFLOW_STATE_DIR:-$ROOT/.eduflow-team-state}"

INTERVAL_SECONDS="${1:-600}"
SINGLE_SHOT="${2:-}"
LOG_FILE="$EDUFLOW_STATE_DIR/hermes-supervisor.log"
PID_FILE="$EDUFLOW_STATE_DIR/hermes-supervisor.pid"

if ! [[ "$INTERVAL_SECONDS" =~ ^[0-9]+$ ]] || [ "$INTERVAL_SECONDS" -lt 10 ]; then
  echo "usage: $0 [interval_seconds>=10] [--once]" >&2
  exit 1
fi

run_once() {
  local payload
  local checked_at
  checked_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo "[$checked_at] hermes-supervisor check started"
  if ! payload="$(python3 -m eduflow.cli task supervisor-check --json --advance 2>&1)"; then
    echo "[$checked_at] hermes-supervisor check failed"
    printf '%s\n' "$payload"
    return 0
  fi

  if command -v jq >/dev/null 2>&1; then
    local health
    health="$(printf '%s' "$payload" | jq -r '.health_status // empty')"
    local action
    action="$(printf '%s' "$payload" | jq -r '.recommended_action // empty')"
    local alert
    alert="$(printf '%s' "$payload" | jq -r '.user_alert_action // empty')"
    echo "[$checked_at] health=${health:-unknown} action=${action:-unknown} alert=${alert:-unknown}"
    case "$health" in
      healthy_silent|soft_warning_observe)
        return 0
        ;;
      repair_needed|escalated_failure)
        printf '%s\n' "$payload"
        if [ "$action" = "trigger_supervisor_repair" ] || [ "$alert" != "no_alert" ]; then
          if ! python3 -m eduflow.cli task supervisor-check --advance --send >/dev/null; then
            echo "[$checked_at] hermes-supervisor send failed; loop will continue"
          fi
        fi
        return 0
        ;;
    esac
  fi

  printf '%s\n' "$payload"
  return 0
}

if [ "${SINGLE_SHOT:-}" = "--once" ]; then
  run_once
  exit 0
fi

mkdir -p "$EDUFLOW_STATE_DIR"
echo "$$" > "$PID_FILE"
exec >>"$LOG_FILE" 2>&1
trap 'rm -f "$PID_FILE"; echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] hermes-supervisor stopped"; exit 0' INT TERM EXIT
echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] hermes-supervisor loop started interval=${INTERVAL_SECONDS}s pid=$$"

while true; do
  run_once
  sleep "$INTERVAL_SECONDS"
done
