"""`eduflow runtime list [<agent>]` — show resolved runtime chains.

Without `<agent>`, prints every agent's chain. With `<agent>`, prints
that agent's chain with the currently-selected runtime highlighted.

Each line:
  <selected?> <runtime_name>  <env_profile>  pool=<pool_id>
  cli=<cli>  model=<model>   provider=<provider>

The selected line is prefixed with `→` (or `"selected": true` in JSON).
"""
from __future__ import annotations

import sys

from eduflow.runtime import config, lifecycle
from eduflow.util import (
    maybe_print_help, pop_bool_flag, print_json, reject_extra_args,
)


USAGE = "usage: eduflow runtime list [<agent>] [--json]"


def _chain_for_agent(agent: str) -> dict:
    """Resolve the runtime chain + current selected runtime for one agent.

    Returns a dict with:
      agent           — agent name
      current_runtime — name of the runtime marked active in runtime-status.json
      chain           — ordered list of runtime dicts from resolve_runtime_chain
      chain_with_status — same chain annotated with `selected` bool
    """
    try:
        chain = config.resolve_runtime_chain(agent)
    except KeyError as e:
        return {"agent": agent, "current_runtime": "unknown", "chain": [],
                "error": str(e), "chain_with_status": []}
    status = lifecycle.current_runtime_status(agent)
    current = str(status.get("runtime") or "") if status else ""
    annotated = []
    for rt in chain:
        entry = dict(rt)
        entry["selected"] = (current and rt.get("name") == current)
        # Resolve pool_id from env_profile (cheap: just read the profile).
        env_profile_name = str(rt.get("env_profile") or "")
        if env_profile_name:
            try:
                profile = config.env_profile_config(env_profile_name)
                entry["pool_id"] = str(profile.get("pool_id") or "")
                entry["base_url"] = str(profile.get("ANTHROPIC_BASE_URL") or "")
            except KeyError:
                entry["pool_id"] = ""
                entry["base_url"] = ""
        else:
            entry["pool_id"] = ""
            entry["base_url"] = ""
        annotated.append(entry)
    return {
        "agent": agent,
        "current_runtime": current or "unknown",
        "chain": chain,
        "chain_with_status": annotated,
    }


def _emit_text_one(result: dict) -> None:
    agent = result["agent"]
    current = result["current_runtime"]
    chain = result["chain_with_status"]
    error = result.get("error")
    if error:
        print(f"❌ {agent}: {error}")
        return
    print(f"{agent}  (current: {current})")
    if not chain:
        print("  (no runtimes)")
        return
    for rt in chain:
        marker = "→" if rt["selected"] else " "
        pool = rt["pool_id"] or "—"
        url = rt.get("base_url") or ""
        url_short = url.replace("https://", "").replace("http://", "").rstrip("/")
        print(
            f"  {marker} {rt['name']:<32}  "
            f"pool={pool:<20}  "
            f"cli={rt.get('cli', ''):<12}  "
            f"env_profile={rt.get('env_profile') or '—'}"
        )
        if url_short:
            print(f"      base_url: {url_short}  model={rt.get('model', '')}")


def _emit_text(all_results: list[dict]) -> None:
    for result in all_results:
        _emit_text_one(result)
        print()


def main(argv: list[str]) -> int:
    rest = list(argv)
    if maybe_print_help(rest, USAGE):
        return 0
    as_json = pop_bool_flag(rest, "--json")
    if len(rest) > 1:
        print(f"❌ unexpected args: {rest[1:]}\n{USAGE}")
        return 1
    try:
        team = config.load_team()
    except Exception as e:
        print(f"❌ team config load failed: {e}", file=sys.stderr)
        return 1
    agents = sorted(team.get("agents", {}))
    if len(rest) == 1:
        target = rest[0]
        if target not in agents:
            print(f"❌ unknown agent: {target!r}", file=sys.stderr)
            return 1
        agents = [target]

    results = [_chain_for_agent(a) for a in agents]
    if as_json:
        # Strip the raw chain (duplicated) for cleaner JSON output.
        out = [{
            "agent": r["agent"],
            "current_runtime": r["current_runtime"],
            "chain": r["chain_with_status"],
            **({"error": r["error"]} if r.get("error") else {}),
        } for r in results]
        print_json(out)
        return 0
    _emit_text(results)
    return 0
