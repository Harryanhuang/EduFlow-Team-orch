import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "operations" / "state-and-config-inventory.md"
LIVE_ROOT = Path(os.environ.get(
    "EDUFLOW_INVENTORY_LIVE_ROOT",
    "/Volumes/Halobster/Codex相关/EduFlow-Team-orch",
))

REQUIRED_COLUMNS = {
    "asset",
    "authoritative location/store",
    "writer",
    "reader",
    "owner",
    "permissions",
    "backup",
    "retention",
    "recovery",
    "migration requirement",
}

REQUIRED_ASSETS = {
    "inbox",
    "task snapshot",
    "task events",
    "generic events",
    "router cursor",
    "router seen set",
    "runtime status",
    "runtime switch events",
    "loop runs",
    "workflow assets",
    "skill assets",
    "identity assets",
    "memory database",
    "unified config",
    "tenant token cache",
    "agent secret source",
    "scheduled task store",
}


def _inventory_table() -> tuple[list[str], dict[str, list[str]]]:
    text = DOC.read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if line.startswith("|")]
    header_index = next(
        i for i, line in enumerate(lines) if "authoritative location/store" in line.lower()
    )
    cells = lambda line: [cell.strip() for cell in line.strip("|").split("|")]
    header = [cell.lower() for cell in cells(lines[header_index])]
    rows = {}
    for line in lines[header_index + 2 :]:
        values = cells(line)
        if len(values) == len(header):
            rows[values[0].lower()] = values
    return header, rows


def _wrapper_backend_probe() -> dict:
    """Probe only backend identity/schema metadata and file stats, never rows."""
    code = r'''
import importlib.metadata
import json
import os
import sqlite3
from pathlib import Path
from flow_memory.storage import get_backend
from flow_memory.storage.paths import get_path_provider

backend = get_backend()
db = get_path_provider().memory_db_file()
legacy = Path(os.environ["EDUFLOW_STATE_DIR"]) / "eduflow_memory.db"
conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
try:
    user_version = conn.execute("PRAGMA user_version").fetchone()[0]
    table_count = conn.execute(
        "SELECT count(*) FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchone()[0]
finally:
    conn.close()
print(json.dumps({
    "backend": backend.__class__.__module__ + "." + backend.__class__.__name__,
    "package_version": importlib.metadata.version("flow-memory"),
    "db": str(db),
    "db_mode": oct(db.stat().st_mode & 0o777),
    "schema_user_version": user_version,
    "schema_table_count": table_count,
    "legacy_db": str(legacy),
    "legacy_mode": oct(legacy.stat().st_mode & 0o777),
}))
'''
    command = f'. "{LIVE_ROOT}/scripts/eduflow-team-env.sh"; python3 -'
    completed = subprocess.run(
        ["bash", "-lc", command], input=code, check=True, text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout.splitlines()[-1])


def _live_modes() -> dict[str, str]:
    state = LIVE_ROOT / ".eduflow-team-state"
    paths = {
        "inbox": state / "facts/inbox.json",
        "task snapshot": state / "tasks.json",
        "task events": state / "task-events.jsonl",
        "generic events": state / "facts/logs.jsonl",
        "router cursor": state / "router.cursor",
        "router seen set": state / "router.seen",
        "runtime status": state / "facts/runtime-status.json",
        "runtime switch events": state / "facts/runtime-switch-events.jsonl",
    }
    return {name: oct(path.stat().st_mode & 0o777) for name, path in paths.items()}


def _credential_table() -> tuple[list[str], dict[str, list[str]]]:
    text = DOC.read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if line.startswith("|")]
    header_index = next(
        i for i, line in enumerate(lines) if "selected credential source" in line.lower()
    )
    cells = lambda line: [cell.strip() for cell in line.strip("|").split("|")]
    header = [cell.lower() for cell in cells(lines[header_index])]
    rows = {}
    for line in lines[header_index + 2 :]:
        values = cells(line)
        if len(values) == len(header):
            rows[values[0]] = values
    return header, rows


def _wrapper_credential_probe() -> dict:
    """Resolve config/adapter metadata and stat source paths; never load values."""
    code = r'''
import json
import os
from pathlib import Path
from eduflow.agents import get_adapter
from eduflow.runtime import config

agents = {}
for agent in config.agent_names():
    selected = config.resolved_agent_config(agent)
    adapter = get_adapter(selected.get("cli", "claude-code"))
    slots = adapter.auth_slots()
    agents[agent] = {
        "runtime": selected.get("runtime", ""),
        "cli": selected.get("cli", ""),
        "env_profile": selected.get("env_profile", ""),
        "login_credfile": slots.login_credfile if slots else None,
        "has_auth_slots": slots is not None,
    }
def mode(path):
    p = Path(path).expanduser()
    return oct(p.stat().st_mode & 0o777) if p.exists() else "absent"
state = Path(os.environ["EDUFLOW_STATE_DIR"])
print(json.dumps({
    "agents": agents,
    "modes": {
        "project_env": mode(state / ".env"),
        "codex_auth": mode("~/.codex/auth.json"),
        "kimi_shared": mode("~/.kimi/credentials/kimi-code.json"),
        "lark_profile": mode("~/.lark-cli/config.json"),
    },
}))
'''
    completed = subprocess.run(
        ["bash", "-lc", f'. "{LIVE_ROOT}/scripts/eduflow-team-env.sh"; python3 -'],
        input=code, check=True, text=True, capture_output=True,
    )
    return json.loads(completed.stdout.splitlines()[-1])


def test_inventory_has_required_assets_and_operational_fields():
    header, rows = _inventory_table()
    assert set(header) == REQUIRED_COLUMNS
    assert REQUIRED_ASSETS <= set(rows)
    for name in REQUIRED_ASSETS:
        assert all(cell and cell.lower() not in {"unknown", "tbd", "?"} for cell in rows[name])


def test_inventory_discloses_path_drift_and_legacy_config_fallbacks():
    text = DOC.read_text(encoding="utf-8")
    required = (
        ".eduflow-team-state",
        "~/.eduflow",
        "EDUFLOW_STATE_DIR",
        "EDUFLOW_CONFIG_FILE",
        "eduflow.toml",
        "EDUFLOW_TEAM_FILE",
        "team.json",
        "EDUFLOW_RUNTIME_CONFIG",
        "runtime_config.json",
    )
    assert all(term in text for term in required)


def test_inventory_proves_memory_and_credentials_from_production_sources():
    header, rows = _inventory_table()
    values = dict(zip(header, rows["memory database"]))
    probe = _wrapper_backend_probe()
    authority = values["authoritative location/store"]
    assert probe["backend"] == "flow_memory.storage.sql.SqliteBackend"
    assert probe["db"].endswith("/.eduflow-team-state/flow_memory.db")
    assert probe["db_mode"] == "0o644"
    assert probe["legacy_db"].endswith("/.eduflow-team-state/eduflow_memory.db")
    assert probe["legacy_mode"] == "0o600"
    assert "$STATE/flow_memory.db" in authority
    assert "active" in authority.lower()
    assert "$STATE/eduflow_memory.db" in authority
    assert "legacy" in authority.lower()
    assert "0644" in values["permissions"] and "risk" in values["permissions"].lower()
    assert "FLOW_MEMORY_DB" in values["migration requirement"]
    assert probe["package_version"] in values["reader"]
    assert str(probe["schema_user_version"]) in values["reader"]
    assert str(probe["schema_table_count"]) in values["reader"]


def test_inventory_records_actual_live_modes_for_runtime_files():
    header, rows = _inventory_table()
    for name, mode in _live_modes().items():
        values = dict(zip(header, rows[name]))
        assert mode == "0o644"
        assert "0644" in values["permissions"]
        assert "0700" in values["permissions"]


def test_credential_ledger_matches_live_selected_runtimes_without_values():
    header, rows = _credential_table()
    probe = _wrapper_credential_probe()
    assert set(header) == {
        "agent", "selected runtime", "cli", "selected credential source",
        "source mode", "fallback sources", "selection evidence",
    }
    assert set(probe["agents"]) <= set(rows)
    for agent, actual in probe["agents"].items():
        values = dict(zip(header, rows[agent]))
        assert values["selected runtime"] == actual["runtime"]
        assert values["cli"] == actual["cli"]
        assert actual["env_profile"] in values["selected credential source"]
        assert values["source mode"] == "0600"
        assert "selected" in values["selection evidence"].lower()
    assert probe["modes"] == {
        "project_env": "0o600",
        "codex_auth": "0o600",
        "kimi_shared": "absent",
        "lark_profile": "0o600",
    }
    doc = DOC.read_text(encoding="utf-8")
    assert "Claude Code-credentials" in doc
    assert "~/.codex/auth.json" in doc
    assert "no auth_slots" in doc
    assert "hermes_minimax_m3_primary" in doc
    assert "lark-cli-credentials" in doc
