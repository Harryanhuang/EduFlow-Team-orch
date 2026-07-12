import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
from types import SimpleNamespace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/operations/state-and-config-inventory.md"
_WRAPPER_COMMAND = r'''
set -euo pipefail
unset ROOT
. "$1/scripts/eduflow-team-env.sh"
exec python3 "$2" --live-root "$1" --collect-in-wrapper
'''

REQUIRED_COLUMNS = {
    "asset", "authoritative location/store", "writer", "reader", "owner",
    "permissions", "backup", "retention", "recovery", "migration requirement",
}
REQUIRED_ASSETS = {
    "inbox", "task snapshot", "task events", "generic events", "router cursor",
    "router seen set", "runtime status", "runtime switch events", "loop runs",
    "workflow assets", "skill assets", "identity assets", "memory database",
    "unified config", "tenant token cache", "agent secret source",
    "scheduled task store",
}


def _table(text: str, marker: str) -> tuple[list[str], dict[str, list[str]]]:
    lines = [line for line in text.splitlines() if line.startswith("|")]
    start = next(i for i, line in enumerate(lines) if marker.lower() in line.lower())
    cells = lambda line: [cell.strip() for cell in line.strip("|").split("|")]
    header = [cell.lower() for cell in cells(lines[start])]
    rows = {}
    for line in lines[start + 2:]:
        values = cells(line)
        if len(values) == len(header):
            rows[values[0]] = values
        elif rows:
            break
    return header, rows


def _validate_document(text: str, probe: dict) -> None:
    header, rows = _table(text, "authoritative location/store")
    assert set(header) == REQUIRED_COLUMNS
    assert REQUIRED_ASSETS <= {name.lower() for name in rows}
    for name in REQUIRED_ASSETS:
        values = rows[name]
        assert all(cell and cell.lower() not in {"unknown", "tbd", "?"} for cell in values)

    memory = dict(zip(header, rows["memory database"]))
    meta = probe["memory"]
    assert meta["backend"] == "flow_memory.storage.sql.SqliteBackend"
    assert "$STATE/flow_memory.db" in memory["authoritative location/store"]
    assert "$STATE/eduflow_memory.db" in memory["authoritative location/store"]
    assert meta["db_mode"] == "0644" and "0644" in memory["permissions"]
    assert "security risk" in memory["permissions"].lower()
    assert "FLOW_MEMORY_DB" in memory["migration requirement"]
    for value in (
        meta["package_version"], meta["schema_fingerprint"], meta["source_git_head"],
        meta["source_sha256"], meta["source_module"],
    ):
        assert str(value) in text
    assert f"dirty={str(meta['source_dirty']).lower()}" in text
    assert "user_version=0" in text and "missing migration-version risk" in text
    assert "sqlite_schema objects" in text
    for table_name, table_meta in meta["key_schema"].items():
        assert table_name in text
        for column in table_meta["columns"]:
            assert column in text
        for index in table_meta["indexes"]:
            assert index in text

    for name, mode in probe["runtime_modes"].items():
        values = dict(zip(header, rows[name]))
        assert mode == "0644"
        assert "0644" in values["permissions"]
        assert probe["directory_modes"]["state"] == "0700"
        child = "facts" if name in {
            "inbox", "generic events", "runtime status", "runtime switch events",
        } else "state"
        assert probe["directory_modes"][child] in values["permissions"]
    identity = dict(zip(header, rows["identity assets"]))
    assert probe["directory_modes"]["agents"] == "0755"
    assert "0755" in identity["permissions"] and "0700" in identity["permissions"]
    assert "non-traversable" in text

    cred_header, cred_rows = _table(text, "selected credential source")
    assert set(cred_header) == {
        "agent", "selected runtime", "env profile", "cli",
        "selected credential source", "source type/mode", "selection evidence",
    }
    assert {row["agent"] for row in probe["credentials"]} == set(cred_rows)
    for actual in probe["credentials"]:
        values = dict(zip(cred_header, cred_rows[actual["agent"]]))
        assert values["selected runtime"] == actual["runtime"]
        assert values["env profile"] == actual["env_profile"]
        assert values["cli"] == actual["cli"]
        assert values["selected credential source"] == actual["source_path"]
        assert values["source type/mode"] == f"{actual['source_type']}; {actual['source_mode']}"
        assert "current_runtime_status" in values["selection evidence"]
        assert set(actual["reference_names"]) <= set(probe["root_env_keys"])
    assert "$ROOT/.env" in text
    assert "$STATE/.env` is agent_auth fallback only" in text
    assert "production topology PASS" in text


def _fixture_probe() -> dict:
    key_schema = {
        "memory_items": {"columns": ["id", "scope", "content"], "indexes": ["idx_mi_scope"]},
        "active_constraints": {"columns": ["id", "scope", "content"], "indexes": ["idx_ac_scope"]},
    }
    return {
        "memory": {
            "backend": "flow_memory.storage.sql.SqliteBackend",
            "package_version": "fixture-0.1.0",
            "db_mode": "0644",
            "schema_fingerprint": "fixture-schema-fingerprint",
            "source_git_head": "fixture-git-head",
            "source_dirty": True,
            "source_sha256": "fixture-source-sha256",
            "source_module": "/fixture/flow_memory/storage/sql.py",
            "key_schema": key_schema,
        },
        "runtime_modes": {name: "0644" for name in (
            "inbox", "task snapshot", "task events", "generic events",
            "router cursor", "router seen set", "runtime status", "runtime switch events",
        )},
        "directory_modes": {"state": "0700", "facts": "0755", "agents": "0755"},
        "root_env_keys": ["FIXTURE_AUTH_TOKEN"],
        "credentials": [{
            "agent": "fixture_agent", "runtime": "fixture_runtime",
            "env_profile": "fixture_profile", "cli": "claude-code",
            "source_path": "$ROOT/.env", "source_type": "env_profile reference",
            "source_mode": "0600",
            "reference_names": ["FIXTURE_AUTH_TOKEN"],
        }],
    }


def test_inventory_contract_with_fixture_probe(tmp_path: Path):
    """Portable unit contract: no production path, subprocess, DB, or secrets."""
    text = DOC.read_text(encoding="utf-8")
    probe = _fixture_probe()
    # Substitute only live-generated values; the structure remains the real doc.
    replacements = {
        "0.1.0": "fixture-0.1.0",
        re.search(r"schema fingerprint `([^`]+)`", text).group(1): "fixture-schema-fingerprint",
        re.search(r"source git HEAD `([^`]+)`", text).group(1): "fixture-git-head",
        re.search(r"source SHA-256 `([^`]+)`", text).group(1): "fixture-source-sha256",
        re.search(r"source module `([^`]+)`", text).group(1): "/fixture/flow_memory/storage/sql.py",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    _, credential_rows = _table(text, "selected credential source")
    lines = text.splitlines()
    credential_header_seen = False
    out = []
    for line in lines:
        if line.startswith("| Agent | Selected runtime"):
            credential_header_seen = True
            out.append(line)
            continue
        if credential_header_seen and line.startswith("|---"):
            out.append(line)
            out.append("| fixture_agent | fixture_runtime | fixture_profile | claude-code | $ROOT/.env | env_profile reference; 0600 | selected by `current_runtime_status`, correlated with production topology PASS |")
            credential_header_seen = False
            continue
        if line.startswith("| ") and line.split("|", 2)[1].strip() in credential_rows:
            continue
        out.append(line)
    _validate_document("\n".join(out), probe)


def test_hermes_selected_env_source_is_root_not_state() -> None:
    text = DOC.read_text(encoding="utf-8")
    hermes_lines = [
        line for line in text.splitlines()
        if line.startswith("- Hermes is selected through")
    ]
    assert len(hermes_lines) == 1
    assert "`$ROOT/.env`" in hermes_lines[0]
    assert "`$STATE/.env`" not in hermes_lines[0]


def test_live_probe_wrapper_parsing_uses_mocked_subprocess(monkeypatch, capsys, tmp_path: Path):
    payload = _fixture_probe()
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: SimpleNamespace(
        returncode=0, stdout=json.dumps(payload), stderr="",
    ))
    assert main(["--live-root", str(tmp_path)]) == 0
    parsed = json.loads(capsys.readouterr().out)
    assert parsed == payload
    assert all("value" not in key.lower() for row in parsed["credentials"] for key in row)


def test_env_profile_source_requires_root_file_key_not_ambient_export(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("ROOT_TOKEN=discarded-value\n", encoding="utf-8")
    keys = _env_key_names(env_file)
    assert keys == {"ROOT_TOKEN"}
    assert _resolve_profile_source(["ROOT_TOKEN"], keys) == "$ROOT/.env"
    try:
        _resolve_profile_source(["AMBIENT_ONLY_TOKEN"], keys)
    except RuntimeError as exc:
        assert "not declared in $ROOT/.env" in str(exc)
    else:
        raise AssertionError("ambient-only export must not prove root .env authority")


def test_wrapper_command_uses_positional_argv_and_never_interpolates_live_root(
    monkeypatch, capsys, tmp_path: Path,
):
    marker = tmp_path / "must-not-execute"
    hostile = tmp_path / f'bad";touch $({marker});`touch {marker}`'
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda argv, **kwargs: (
        calls.append((argv, kwargs)) or SimpleNamespace(
            returncode=0, stdout=json.dumps(_fixture_probe()), stderr="",
        )
    ))
    assert main(["--live-root", str(hostile)]) == 0
    assert not marker.exists()
    argv, _ = calls[0]
    assert argv[:3] == ["bash", "-c", _WRAPPER_COMMAND]
    assert argv[3] == "eduflow-inventory"
    assert argv[4] == str(hostile)
    assert str(hostile) not in _WRAPPER_COMMAND
    assert calls[0][1]["env"]["ROOT"] == ""
    json.loads(capsys.readouterr().out)


def _env_key_names(path: Path) -> set[str]:
    """Return only assignment LHS names; RHS bytes are discarded immediately."""
    keys = set()
    with path.open("r", encoding="utf-8") as stream:
        for raw in stream:
            line = raw.lstrip()
            if line.startswith("export "):
                line = line[7:].lstrip()
            equals = line.find("=")
            key = line[:equals].strip() if equals >= 0 else ""
            if equals >= 0 and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
                keys.add(key)
    return keys


def _resolve_profile_source(reference_names: list[str], root_env_keys: set[str]) -> str:
    missing = sorted(set(reference_names) - root_env_keys)
    if missing:
        raise RuntimeError(f"env_profile references not declared in $ROOT/.env: {missing}")
    return "$ROOT/.env"


def _mode(path: Path) -> str:
    return f"{path.stat().st_mode & 0o777:04o}" if path.exists() else "absent"


def _git_metadata(module: Path) -> tuple[str, bool]:
    repo = module.parent
    while repo != repo.parent and not (repo / ".git").exists():
        repo = repo.parent
    head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], check=True,
        text=True, capture_output=True,
    ).stdout.strip()
    dirty = bool(subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"], check=True,
        text=True, capture_output=True,
    ).stdout.strip())
    return head, dirty


def _collect_live(root: Path) -> dict:
    """Collect paths/schema/config metadata only; never select memory rows or secret values."""
    import importlib.metadata
    import inspect
    from flow_memory.storage import get_backend
    from flow_memory.storage.paths import get_path_provider
    from eduflow.runtime import config, lifecycle, tunables

    state = Path(os.environ["EDUFLOW_STATE_DIR"])
    backend = get_backend()
    db = get_path_provider().memory_db_file()
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        schema_rows = conn.execute(
            "SELECT type,name,tbl_name,coalesce(sql,'') FROM sqlite_schema "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
        ).fetchall()
        normalized = [
            "|".join(" ".join(str(cell).lower().split()) for cell in row)
            for row in schema_rows
        ]
        fingerprint = hashlib.sha256("\n".join(normalized).encode()).hexdigest()
        user_version = conn.execute("PRAGMA user_version").fetchone()[0]
        key_schema = {}
        for table in ("memory_items", "active_constraints", "task_capsules", "sensitive_memory_items"):
            columns = [row[1] for row in conn.execute(f'PRAGMA table_info("{table}")')]
            indexes = [row[1] for row in conn.execute(f'PRAGMA index_list("{table}")')]
            key_schema[table] = {"columns": columns, "indexes": sorted(indexes)}
    finally:
        conn.close()

    module = Path(inspect.getsourcefile(backend.__class__)).resolve()
    source_head, source_dirty = _git_metadata(module)
    raw_profiles = tunables.load().get("env_profiles", {})
    root_env_keys = _env_key_names(root / ".env")
    credentials = []
    for agent in config.agent_names():
        status = lifecycle.current_runtime_status(agent)
        runtime_name = str(status.get("runtime") or status.get("selected_runtime") or "")
        if not runtime_name:
            raise RuntimeError(f"{agent}: current runtime status missing")
        selected = config.resolved_agent_config(agent, runtime_name=runtime_name)
        if selected.get("selected_runtime") != runtime_name:
            raise RuntimeError(f"{agent}: current runtime {runtime_name} absent from configured chain")
        profile_name = str(selected.get("env_profile") or "")
        profile = raw_profiles.get(profile_name, {})
        references = sorted({
            match.group(1) for value in profile.values() if isinstance(value, str)
            for match in [re.fullmatch(r"\$\{([A-Z0-9_]+)\}", value)] if match
        })
        if not references:
            raise RuntimeError(f"{agent}: selected env_profile reference source unresolved")
        source_path = _resolve_profile_source(references, root_env_keys)
        credentials.append({
            "agent": agent, "runtime": runtime_name, "env_profile": profile_name,
            "cli": str(selected.get("cli") or ""), "source_path": source_path,
            "source_type": "env_profile reference", "source_mode": _mode(root / ".env"),
            "reference_names": references,
        })

    runtime_paths = {
        "inbox": state / "facts/inbox.json", "task snapshot": state / "tasks.json",
        "task events": state / "task-events.jsonl", "generic events": state / "facts/logs.jsonl",
        "router cursor": state / "router.cursor", "router seen set": state / "router.seen",
        "runtime status": state / "facts/runtime-status.json",
        "runtime switch events": state / "facts/runtime-switch-events.jsonl",
    }
    return {
        "memory": {
            "backend": backend.__class__.__module__ + "." + backend.__class__.__name__,
            "package_version": importlib.metadata.version("flow-memory"),
            "db": str(db), "db_mode": _mode(db), "user_version": user_version,
            "sqlite_schema_object_count": len(schema_rows), "schema_fingerprint": fingerprint,
            "key_schema": key_schema, "source_module": str(module),
            "source_sha256": hashlib.sha256(module.read_bytes()).hexdigest(),
            "source_git_head": source_head, "source_dirty": source_dirty,
            "legacy_db": str(state / "eduflow_memory.db"),
            "legacy_mode": _mode(state / "eduflow_memory.db"),
        },
        "runtime_modes": {name: _mode(path) for name, path in runtime_paths.items()},
        "directory_modes": {
            "state": _mode(state), "facts": _mode(state / "facts"),
            "agents": _mode(state / "agents"),
        },
        "root_env_keys": sorted(root_env_keys),
        "credentials": credentials,
        "source_modes": {
            "root_env": _mode(root / ".env"), "state_env": _mode(state / ".env"),
            "codex_auth": _mode(Path.home() / ".codex/auth.json"),
            "kimi_shared": _mode(Path.home() / ".kimi/credentials/kimi-code.json"),
            "lark_profile": _mode(Path.home() / ".lark-cli/config.json"),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-root", type=Path, required=True)
    parser.add_argument("--collect-in-wrapper", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if not args.collect_in_wrapper:
        run = subprocess.run(
            ["bash", "-c", _WRAPPER_COMMAND, "eduflow-inventory",
             str(args.live_root), str(Path(__file__).resolve())],
            text=True, capture_output=True, env={**os.environ, "ROOT": ""},
        )
        if run.returncode:
            sys.stderr.write(run.stderr)
            return run.returncode
        print(run.stdout.strip())
        return 0
    probe = _collect_live(args.live_root.resolve())
    _validate_document(DOC.read_text(encoding="utf-8"), probe)
    print(json.dumps(probe, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
