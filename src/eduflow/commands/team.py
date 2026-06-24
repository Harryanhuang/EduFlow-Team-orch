"""`eduflow team [--json]`

Show the latest status for every agent that has reported one. Default:
human-readable single-line per agent:
  `name  status  task  [⛔ blocker]  (Nm ago)  ♥ Nm ago`.

With `--json`, dump a list of status records (each with name, status,
task, blocker, updated_at_ms, heartbeat_ms) so CI / smoke conductors
/ peer agents can parse machine-readable state.
"""
from __future__ import annotations

from eduflow.store import local_facts
from eduflow.util import ago_ms, pop_bool_flag, print_json


def _status_task_with_latest_fact(row: dict) -> str:
    task = str(row.get("task", "") or "")
    agent = str(row.get("agent", "") or "")
    if str(row.get("status") or "") in {"待接单", "已读待确认"}:
        return task
    latest_rows = local_facts.list_logs(agent, limit=1)
    if not latest_rows:
        return task
    latest = latest_rows[-1]
    latest_ts = int(latest.get("created_at", 0) or 0)
    updated_at = int(row.get("updated_at", 0) or 0)
    latest_content = str(latest.get("content", "") or "").strip()
    latest_kind = str(latest.get("type", "") or "")
    if not latest_content:
        return task
    if latest_kind == "say" and any(marker in latest_content for marker in ("verdict", "通过", "退回", "有条件通过")):
        return latest_content
    if latest_ts <= updated_at:
        return task
    return latest_content


def _emit_text(rows: list[dict], heartbeats: dict[str, int]) -> None:
    if not rows:
        print("👥 no agents have reported status yet")
        return
    name_w = max(len(r["agent"]) for r in rows)
    for r in rows:
        line = (
            f"{r['agent'].ljust(name_w)}  "
            f"{r['status']}  {_status_task_with_latest_fact(r)}"
        )
        if r.get("blocker"):
            line += f"  ⛔ {r['blocker']}"
        line += f"  ({ago_ms(r.get('updated_at', 0))})"
        hb = heartbeats.get(r["agent"])
        if hb:
            line += f"  ♥ {ago_ms(hb)}"
        print(line)


def _emit_json(rows: list[dict], heartbeats: dict[str, int]) -> None:
    """Machine-readable shape: a flat list of status records, one per
    agent that has ever upserted. Heartbeat is folded in alongside so
    consumers don't have to cross-reference two structures."""
    out = [
        {
            "agent": r["agent"],
            "status": r["status"],
            "task": _status_task_with_latest_fact(r),
            "blocker": r.get("blocker", ""),
            "updated_at_ms": r.get("updated_at", 0),
            "heartbeat_ms": heartbeats.get(r["agent"], 0),
        }
        for r in rows
    ]
    print_json(out)


def main(argv: list[str]) -> int:
    rest = list(argv)
    as_json = pop_bool_flag(rest, "--json")
    rows = local_facts.list_all_statuses()
    heartbeats = local_facts.all_heartbeats()
    if as_json:
        _emit_json(rows, heartbeats)
    else:
        _emit_text(rows, heartbeats)
    return 0
