#!/usr/bin/env bash

# Resolve repo root from this script's location. Honor $ROOT override so a
# caller (test harness, redirect harness) can still point at a different
# checkout without editing this file.
if [ -n "${BASH_SOURCE:-}" ]; then
  _EDUFLOW_ENV_SCRIPT="${BASH_SOURCE[0]}"
elif [ -n "${ZSH_VERSION:-}" ]; then
  _EDUFLOW_ENV_SCRIPT="$(eval 'printf "%s" "${(%):-%x}"')"
else
  _EDUFLOW_ENV_SCRIPT="$0"
fi
ROOT="${ROOT:-$(cd "$(dirname "$_EDUFLOW_ENV_SCRIPT")/.." && pwd)}"
unset _EDUFLOW_ENV_SCRIPT

export EDUFLOW_ROOT="$ROOT"
export EDUFLOW_CONFIG_FILE="${EDUFLOW_CONFIG_FILE:-$ROOT/eduflow.toml}"
export EDUFLOW_STATE_DIR="${EDUFLOW_STATE_DIR:-$ROOT/.eduflow-team-state}"
export EDUFLOW_WORKFLOW_DIR="${EDUFLOW_WORKFLOW_DIR:-$ROOT/docs/workflows}"

if [ -f "$ROOT/.env" ]; then
  if ! python3 - "$ROOT/.env" <<'PY'
import stat
import sys

mode = stat.S_IMODE(__import__("os").stat(sys.argv[1]).st_mode)
raise SystemExit(0 if not mode & (stat.S_IRWXG | stat.S_IRWXO) else 1)
PY
  then
    echo "[eduflow-team-env] ERROR: insecure .env permissions; require no group/other access" >&2
    return 1 2>/dev/null || exit 1
  fi
  set -a
  . "$ROOT/.env"
  set +a
fi

# Import-drift guard: make sure Python eats THIS project's src/ before any
# globally installed eduflow package. Without this, `eduflow` binaries that
# resolve to /opt/homebrew/bin fall back to an old install and never see the
# latest code in this checkout.
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

# Local venv guard: if .venv exists and has a bin/, prepend it to PATH so
# its Python/tools win. If it's missing, warn loudly but don't abort — the
# PYTHONPATH line above still makes the right src/ win for Python imports.
if [ -d "$ROOT/.venv/bin" ]; then
  export PATH="$ROOT/.venv/bin:$PATH"
else
  echo "[eduflow-team-env] WARNING: $ROOT/.venv/bin missing; run 'python3 -m venv .venv && .venv/bin/pip install -e .' in $ROOT" >&2
fi

export LARK_CLI_NO_PROXY="${LARK_CLI_NO_PROXY:-1}"
export EDUFLOW_LARK_SEND_AS="${EDUFLOW_LARK_SEND_AS:-bot}"

export PATH="$ROOT/.venv/bin:/Users/huanganan/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
