#!/usr/bin/env bash

set -euo pipefail

ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

# shellcheck source=/dev/null
. "$ROOT/scripts/eduflow-team-env.sh"

export PYTHONPATH="${PYTHONPATH:-$ROOT/src}"
export LARK_CLI_SUPERVISOR_PROFILE="${LARK_CLI_SUPERVISOR_PROFILE:-hermes-supervisor}"

MODE="${1:---json}"

case "$MODE" in
  --json)
    exec python3 -m eduflow.cli task supervisor-check --json
    ;;
  --advance)
    exec python3 -m eduflow.cli task supervisor-check --json --advance
    ;;
  --send)
    exec python3 -m eduflow.cli task supervisor-check --json --send
    ;;
  --advance-send|--send-advance)
    exec python3 -m eduflow.cli task supervisor-check --json --advance --send
    ;;
  *)
    echo "usage: $0 [--json|--advance|--send|--advance-send]" >&2
    exit 1
    ;;
esac
