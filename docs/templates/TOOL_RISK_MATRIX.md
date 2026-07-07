# Tool Risk Matrix Template

> Deterministic risk classifier for EduFlow command/tool surfaces. Read-only;
> does not block, intercept, or modify any command. Used by
> `task tool-risk --command "..." --json`.

## Levels

| Level    | Definition                                    | Examples (non-exhaustive)                                                                                  |
|----------|-----------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| **Low**     | Read-only / status / search / evidence explain | `status`, `read`, `get`, `list`, `grep`/`search`, `task evidence-explain`, `task loop-status`, `task loop-list`, `task loop-contract`, `task tool-risk`, `task evolution-packet`, `task readiness-check`, `peek`, `recall`, `team`, `inbox` (read) |
| **Medium**  | Local file creation or non-critical local write | `task create`, `task update` (status-only), `task log append`, `say` (in-process, not to user), local file edits inside `content/` / `output/` worktrees |
| **High**    | Coordination / runtime write or external-but-reversible | `send`, `say --to user`, `task dispatch`, `task review` (writes verdict), `task reidentify`, `runtime switch`, `task assign-reviewer`, `task submit-review` |
| **Critical** | Destructive or external production               | `reset`, `down`, `fire`, `hire`, `task archive`, `task archive-schedule`, `rm -rf .eduflow-team-state`, `delete` of state files, external deploy / publish to production surfaces |

## Tool Risk Output Schema

```json
{
  "risk_level": "Low|Medium|High|Critical",
  "access_mode": "auto|auto_review|manager_only|blocked",
  "reason": "<short human-readable reason>",
  "requires_preflight": true|false,
  "requires_human_confirm": true|false
}
```

| risk_level | access_mode          | requires_preflight | requires_human_confirm |
|------------|----------------------|--------------------|------------------------|
| Low        | `auto`               | false              | false                  |
| Medium     | `auto`               | false              | false                  |
| High       | `auto_review`        | true               | false                  |
| Critical   | `manager_only`       | true               | true                   |

## Required Coverage Matrix

The classifier MUST classify each of these patterns:

```text
send                                  (High)
say --to user                         (High)
task dispatch                         (High)
task review                           (High)
reidentify                            (High)
fire / hire / reset / down            (Critical)
rm -rf / delete state / external deploy (Critical)
```

The classifier MUST default to **Medium** when the command token is unrecognized.

## Detection Hints (for `task tool-risk`)

1. Tokenize command on whitespace; honor `--to user` as a single intent marker.
2. Strip known flags (`--json`, `--to <recipient>`, `--reason <text>`).
3. Match the first non-flag verb against the level table.
4. If multiple intents present (e.g. `send worker_course manager 'fix'`), pick the
   highest level among the matched intents.

## Red Lines

- Never mutate command behavior based on risk classification; this surface is read-only.
- Never auto-promote a `Medium` to `High` based on unverified sender context.
- `requires_human_confirm` is advisory output; no command actually blocks on it.
