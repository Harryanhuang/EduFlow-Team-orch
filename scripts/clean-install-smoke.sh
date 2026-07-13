#!/usr/bin/env bash
# Validate that the published dependency graph installs without sibling workspaces.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${1:-$(mktemp -d)/eduflow-clean-venv}"
STATE_DIR="$VENV_DIR/state"
BUILD_REVISION="$(git -C "$ROOT" rev-parse --verify HEAD)"

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip
EDUFLOW_BUILD_REVISION="$BUILD_REVISION" "$VENV_DIR/bin/python" -m pip install "$ROOT"
export EDUFLOW_STATE_DIR="$STATE_DIR"
export EDUFLOW_CONFIG_FILE="$STATE_DIR/eduflow.toml"
export EDUFLOW_TEAM_FILE="$STATE_DIR/team.json"
export EDUFLOW_RUNTIME_CONFIG="$STATE_DIR/runtime_config.json"
export FLOW_MEMORY_DB="$STATE_DIR/flow_memory.db"

VERSION_JSON="$VENV_DIR/version.json"
"$VENV_DIR/bin/eduflow" version --json > "$VERSION_JSON"
"$VENV_DIR/bin/python" - "$VERSION_JSON" "$BUILD_REVISION" <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
assert payload["eduflow"], payload
assert payload["flow_memory"] == "0.1.1", payload
assert payload["revision"] == sys.argv[2], payload
PY

HEALTH_JSON="$VENV_DIR/health.json"
if "$VENV_DIR/bin/eduflow" health --json > "$HEALTH_JSON"; then
    health_rc=0
else
    health_rc=$?
fi
"$VENV_DIR/bin/python" - "$HEALTH_JSON" "$health_rc" <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
rc = int(sys.argv[2])
if rc not in (0, 1):
    raise SystemExit(f"health returned unexpected exit code {rc}")
if payload["ok"] != (rc == 0) or not isinstance(payload["bad"], int):
    raise SystemExit(f"health JSON must be valid and agree with its exit code: {payload}")
PY

"$VENV_DIR/bin/python" -c 'import eduflow; import flow_memory; from eduflow.memory import init_schema; init_schema(); from eduflow.commands import router; assert callable(router.main)'
