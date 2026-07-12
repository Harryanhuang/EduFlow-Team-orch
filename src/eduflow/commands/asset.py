"""`eduflow asset` — read-only asset registry CLI (M7 initial version).

Subcommands:

  eduflow asset list [--type <type>] [--json]
  eduflow asset recommend "<task text>" [--json]
  eduflow asset validate [--json]
  eduflow asset drift-check [--json]

Hard rules:

  - Read-only. Never copies, installs, promotes, or deletes assets.
  - Uses `src/eduflow/store/asset_registry.py`; never re-implements
    the registry inline.
  - Never sends Feishu, never dispatches tasks.
  - All subcommands support --json for stable machine output.
"""
from __future__ import annotations

from eduflow.store import asset_registry
from eduflow.util import (
    error_exit, maybe_print_help, pop_bool_flag, pop_flag, print_json,
    usage_error,
)


USAGE = (
    "usage:\n"
    "  eduflow asset list [--type <type>] [--json]\n"
    "  eduflow asset recommend \"<task text>\" [--json]\n"
    "  eduflow asset validate [--json]\n"
    "  eduflow asset drift-check [--json] [--show-remediation]\n"
    "\n"
    "asset types: workflow | skill | identity_rule | patrol_reference |\n"
    "             memory_candidate | cli_check\n"
)


def _filter_by_type(assets: list[asset_registry.Asset],
                    asset_type: str) -> list[asset_registry.Asset]:
    if not asset_type:
        return assets
    if asset_type not in asset_registry.VALID_ASSET_TYPES:
        valid = ", ".join(asset_registry.VALID_ASSET_TYPES)
        raise ValueError(
            f"unknown asset type: {asset_type} (valid: {valid})"
        )
    return [a for a in assets if a.asset_type == asset_type]


def _cmd_list(rest: list[str]) -> int:
    as_json = pop_bool_flag(rest, "--json")
    asset_type = pop_flag(rest, "--type") or ""
    if rest:
        return usage_error(USAGE)
    try:
        assets = _filter_by_type(asset_registry.scan_all(), asset_type)
    except ValueError as exc:
        return error_exit(f"❌ {exc}")
    if as_json:
        print_json({"assets": [a.to_dict() for a in assets],
                    "count": len(assets)})
        return 0
    if not assets:
        print("no assets found")
        return 0
    print("asset_id\tasset_type\tstatus\ttitle\tpath")
    for asset in assets:
        print(
            f"{asset.asset_id}\t{asset.asset_type}\t{asset.status}\t"
            f"{asset.title}\t{asset.path}"
        )
    return 0


def _cmd_recommend(rest: list[str]) -> int:
    as_json = pop_bool_flag(rest, "--json")
    if not rest or rest[0].startswith("-"):
        return usage_error(USAGE)
    task_text = " ".join(rest)
    rows = asset_registry.recommend(task_text)
    if as_json:
        print_json({"recommendations": rows, "query": task_text})
        return 0
    print(f"recommend :: query={task_text}")
    if not rows:
        print("  no confident asset recommendation")
        return 0
    for row in rows:
        print(
            f"- asset_id={row['asset_id']} type={row['asset_type']} "
            f"confidence={row['confidence']} matched={','.join(row['matched_terms'])} "
            f"path={row['path']}"
        )
    return 0


def _cmd_validate(rest: list[str]) -> int:
    as_json = pop_bool_flag(rest, "--json")
    if rest:
        return usage_error(USAGE)
    report = asset_registry.validate()
    if as_json:
        print_json({"validate": report})
        return 0 if report["ok"] else 1
    print(
        f"validate :: ok={str(report['ok']).lower()} "
        f"errors={len(report['errors'])} warnings={len(report['warnings'])}"
    )
    summary = report.get("summary") or {}
    if summary:
        print(
            f"  total={summary.get('total', 0)} "
            f"workflows={summary.get('workflows', 0)} "
            f"skills={summary.get('skills', 0)} "
            f"identities={summary.get('identities', 0)}"
        )
    for err in report["errors"]:
        print(f"  ERROR: {err}")
    for warn in report["warnings"]:
        print(f"  WARN : {warn}")
    return 0 if report["ok"] else 1


def _cmd_drift_check(rest: list[str]) -> int:
    as_json = pop_bool_flag(rest, "--json")
    show_remediation = pop_bool_flag(rest, "--show-remediation")
    if rest:
        return usage_error(USAGE)
    report = asset_registry.drift_check()
    if as_json:
        print_json({"drift_check": report})
        return 0 if report["ok"] else 1
    summary = report.get("summary") or {}
    print(
        f"drift_check :: ok={str(report['ok']).lower()} "
        f"errors={summary.get('errors', 0)} "
        f"warnings={summary.get('warnings', 0)} "
        f"info={summary.get('info', 0)}"
    )
    findings = report.get("findings") or []
    if not findings:
        print("  no drift findings")
    for f in findings:
        severity = str(f.get("severity") or "-")
        prefix = {
            "error": "ERROR", "warn": "WARN ", "info": "INFO ",
        }.get(severity, severity.upper())
        bits = [
            f"category={f.get('category')}",
            f"asset_id={f.get('asset_id') or '-'}",
        ]
        if "missing" in f:
            bits.append(f"missing={','.join(f['missing'])}")
        if "paths" in f:
            bits.append(f"paths={','.join(f['paths'])}")
        if "candidate_statuses" in f:
            bits.append(f"candidate_statuses={','.join(f['candidate_statuses'])}")
        bits.append(f"severity={severity}")
        print(f"  {prefix}: {' '.join(bits)}")
        if show_remediation:
            for line in f.get("remediation") or []:
                print(f"    -> {line}")
    return 0 if report["ok"] else 1


def main(argv: list[str]) -> int:
    rest = list(argv)
    if maybe_print_help(rest, USAGE):
        return 0
    if not rest:
        return usage_error(USAGE)
    subcommand = rest[0]
    args = rest[1:]
    if subcommand == "list":
        return _cmd_list(args)
    if subcommand == "recommend":
        return _cmd_recommend(args)
    if subcommand == "validate":
        return _cmd_validate(args)
    if subcommand == "drift-check":
        return _cmd_drift_check(args)
    return usage_error(USAGE)
