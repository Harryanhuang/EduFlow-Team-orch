from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "operations" / "state-and-config-inventory.md"

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
    text = DOC.read_text(encoding="utf-8")
    assert "src/eduflow/runtime/paths.py" in text
    assert "eduflow_memory.db" in text
    assert "src/eduflow/memory/db.py" in text
    assert "src/eduflow/runtime/agent_auth.py" in text
    assert "EDUFLOW_SECRETS_FILE" in text
    assert "$STATE/.env" in text
    assert "secret values" in text.lower()
    assert "unknown memory db location is a deployment failure" in text.lower()
    assert "unknown credential source must block" in text.lower()
