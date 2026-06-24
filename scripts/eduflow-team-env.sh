#!/usr/bin/env bash

ROOT="/Volumes/Halobster/Codex相关/EduFlow-Team-orch"

export EDUFLOW_ROOT="$ROOT"
export EDUFLOW_CONFIG_FILE="$ROOT/eduflow.toml"
export EDUFLOW_STATE_DIR="${EDUFLOW_STATE_DIR:-$ROOT/.eduflow-team-state}"

if [ -f "$ROOT/.env" ]; then
  set -a
  . "$ROOT/.env"
  set +a
fi

# Import-drift guard: make sure Python eats THIS project's src/ before any
# globally installed eduflow package. Without this, `eduflow` /
# `eduflowteam` binaries that resolve to /opt/homebrew/bin fall back to the
# old /Volumes/Halobster/Codex相关/EduFlow/src install and never see the
# new failover code.
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
