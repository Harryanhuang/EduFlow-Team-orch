"""`eduflow team [--json] [--all] [--current]`

Show the latest status for every agent that has reported one. Default:
human-readable single-line per agent:
  `name  [residency]  status  task  [⛔ blocker]  (Nm ago)  ♥ Nm ago`.

With `--json`, dump a list of status records (each with name,
residency, status, task, blocker, updated_at_ms, heartbeat_ms) so CI
/ smoke conductors / peer agents can parse machine-readable state.

Phase 2 (2026-07-01) added the `residency` column so the boss can
see at a glance which agents are 常驻 (always-on) vs 温备 (may sleep
when idle). The label comes from `config.load_residency_policy`.
"""
from __future__ import annotations

from eduflow.runtime import config, residency
from eduflow.store import local_facts
from eduflow.util import ago_ms, pop_bool_flag, print_json, reject_extra_args


# Phase 4 (2026-07-08 control-plane repair): cap the long fact / log
# tail inside a `/team` line so one fat entry does not blow the panel
# into a multi-screen wall. The same cap applies to the JSON `task`
# field for parity; consumers that need the full text can read
# `workspace <agent>` instead.
_TEAM_LINE_TASK_CAP = 240


def _active_agent_names() -> set[str]:
    agents = config.load_team().get("agents", {}) or {}
    return {
        name
        for name, cfg in agents.items()
        if not (isinstance(cfg, dict) and cfg.get("archived"))
    }


def _residency_label(agent: str) -> str:
    """Return the display label ('常驻' / '温备' / …) for an agent's
    configured residency mode. Best-effort: any config error degrades
    to '未配置' so `/team` never crashes on a malformed residency
    block."""
    try:
        policy = config.load_residency_policy(agent)
        return residency.display_label(policy.mode)
    except Exception:
        return "未配置"


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
    labels = {r["agent"]: _residency_label(r["agent"]) for r in rows}
    res_w = max((len(v) for v in labels.values()), default=2)
    for r in rows:
        line = (
            f"{r['agent'].ljust(name_w)}  "
            f"{labels[r['agent']].ljust(res_w)}  "
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
    consumers don't have to cross-reference two structures.

    Phase 2: `residency` (常驻/温备/…) is folded in too. Consumers on
    the old schema keep working — they just ignore the new key."""
    out = [
        {
            "agent": r["agent"],
            "residency": _residency_label(r["agent"]),
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
    include_all = pop_bool_flag(rest, "--all")
    current_only = pop_bool_flag(rest, "--current")
    if reject_extra_args(rest, "usage: eduflow team [--json] [--all] [--current]"):
        return 1
    rows = local_facts.list_all_statuses()
    known = _active_agent_names()
    if current_only:
        rows = [r for r in rows if r.get("agent") in known]
    elif not include_all:
        rows = [
            r for r in rows
            if not str(r.get("agent") or "").startswith("-")
            and (not known or r.get("agent") in known)
        ]
    heartbeats = local_facts.all_heartbeats()
    if as_json:
        _emit_json(rows, heartbeats)
    else:
        _emit_text(rows, heartbeats)
    return 0
