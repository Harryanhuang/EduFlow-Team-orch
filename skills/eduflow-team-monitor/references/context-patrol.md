# Context Patrol Reference

Use this when auto_ops monitors team context health or manager receives an
`auto_ops context snapshot`.

## Primary Command

```bash
./scripts/eduflowteam task auto-ops-context --send-manager
```

This command captures recent pane text for every configured agent, parses known
context pressure markers, prints a snapshot, and sends it to manager.

## Snapshot Fields

- `agent`: team role name.
- `level`: one of `ok`, `warning`, `compact_recommended`, `exhausted`,
  `no_session`, `no_window`, or `unknown`.
- `pct`: parsed context percentage when available.
- `marker`: exact parser marker, for example `context_usage=92%` or
  `100% context used`.
- `allow_continue_original_task`: `false` means no more long work on that pane
  until recovery.
- `recommended_action`: machine-readable next action.

## Decision Matrix

| Signal | Meaning | Auto_ops action | Manager action |
| --- | --- | --- | --- |
| `ok`, `no_context_pressure_signal` | No parseable pressure in recent pane output | Include in snapshot only | Continue, but do not treat as proof of low context |
| `warning`, `80-89%` | High context but not at compact gate | Send snapshot to manager | Split next work packet; avoid long monolithic tasks |
| `compact_recommended`, `90-99%` | Compact gate crossed | Send high-priority snapshot to manager | Run real `eduflow compact <agent>` or `/compact <agent>` before long work |
| `exhausted`, `100%`, context limit marker | Current pane is no longer safe for long work | Send high-priority snapshot to manager | Restart/reidentify if compact is rejected or too late |
| `no_session` / `no_window` | Runtime surface missing | Send high-priority snapshot to manager | Restore team runtime or rehire agent |

## Reporting Contract

Auto_ops report to manager must include:

```text
auto_ops context snapshot
agents=<N> risks=<M>
- <agent>: level=<level> pct=<pct> marker=<marker> allow_continue_original_task=<true|false> recommended_action=<action>
```

If any row has `allow_continue_original_task=false`, auto_ops should state:

```text
Context gate blocks long work for: <agents>. Manager must decide compact vs restart before assigning more long tasks.
```

## Important Boundaries

- Auto_ops reports and recommends; manager owns the final compact/restart
  decision unless a standing runtime guard has already acted.
- A text message asking an agent to compact is not recovery. Recovery requires
  the real command: `eduflow compact <agent>` or `/compact <agent>`.
- Missing footer data is uncertainty, not safety. Continue observing and split
  work smaller when the pane has been active for a long time.
