---
name: eduflow-harness-surface-audit
description: Read-only audit of EduFlow harness surface. Use to find duplicate rules, drift between identity/skill/workflow/runtime/Feishu/memory, context overhead, and primitive-only gaps. Intended for worker_builder, Hermes, Luke_recorder, and manager. Not for content workers.
---

# EduFlow Harness Surface Audit

Use this skill when the EduFlow harness (prompts, identities, skills, workflows, runtime config, Feishu cards, memory) has grown enough that duplicate rules, drift, or context bloat are suspected. This is a read-only audit skill; it produces a report and recommendations, not code changes.

## Who should use this

Install for:

| role | why |
| --- | --- |
| `worker_builder` | Owns system construction/repair and config-surface integrity. |
| `Hermes` | Knowledge steward; best suited to audit doc/skill/memory drift. |
| `Luke_recorder` | Records repeated boss corrections that become audit input. |
| `manager` | Lite read-only review of the audit output before dispatch. |

Do **not** install for:

- `worker_course`
- `review_course`
- `worker_qbank`

This skill is **not** for content production, course review, or qbank verification.

## When to run

- After a major branch merge (e.g., `feat/2026-07-01-residency-phase1`).
- When a new skill or workflow is added and old rules may overlap.
- When agents start behaving inconsistently and prompt/memory transport drift is suspected.
- When context pressure is climbing and no single file looks responsible.
- When onboarding a new operator who needs a map of "what controls what."

## Read-only first

This skill never modifies real state. Before producing findings, read only:

```bash
# git / project entry
git show --stat --oneline --decorate --name-status HEAD
git branch --list feat/2026-07-01-residency-phase1

# runtime primitives
./scripts/eduflowteam team --json
./scripts/eduflowteam health
./scripts/eduflowteam runtime verify <agent>
./scripts/eduflowteam runtime-guard

# task / workflow primitives
./scripts/eduflowteam task ops-dashboard --json
./scripts/eduflowteam workflow validate --strict
./scripts/eduflowteam workflow promotion-map --manager --summary
./scripts/eduflowteam workflow gap-map
```

## Scan surfaces

Audit the following surfaces. If a file does not exist in the current worktree, record it as `missing` rather than skipping silently.

### Project entry and global rules

- `AGENTS.md` / `CLAUDE.md` — top-level agent behavior and code-modification rules.
- `README.md` — public product narrative and directory map.
- `eduflow.toml` — team config, runtime registry, env profiles, residency policy, publish rules.

### CLI and commands

- `src/eduflow/cli.py` — command registry and dispatch groups.
- `src/eduflow/commands/` — all subcommand modules, especially:
  - `workflow.py`
  - `task.py`
  - `team.py`
  - `health.py`
  - `runtime_verify.py`
  - `runtime_guard.py`
  - `sleep_idle.py` — residency sleep, default dry-run, `--apply` side effects
  - `residency_wake.py` — wake path and failure handling
  - `wake_alert.py` — wake failure ALERT logic

### Runtime and residency

- `src/eduflow/runtime/` — tmux, watchdog, lifecycle, failover, health, config.
- `src/eduflow/runtime/residency.py` — `resident / warm / cold` policy, `sleep_decision`, display labels (`常驻 / 温备`).
- `src/eduflow/runtime/config.py` — residency config loading if present.
- `src/eduflow/store/agent_residency.py` — per-agent residency bookkeeping (`last_active_at`, `last_handoff_at`, `last_sleep_at`, `last_wake_at`).

### Task and workflow

- `src/eduflow/store/task_event_scanner.py` — anomaly taxonomy, manager boundary, context guard, review truth lag, qbank readiness, stale/visibility findings.
- `docs/workflows/README.md` — registry rules and CLI usage.
- `docs/workflows/*/` — active workflow assets.
- `docs/workflows/_candidates/*/` — candidate workflow pool.

### Identity and skills

- `.eduflow-team-state/agents/*/identity.md` — per-agent identity files.
- `skills/` — repo skills, especially `eduflow-team-monitor` references.
- `.claude/skills/` — Claude Code skill registry and local skills.
- `.claude/skills/skill-registry.md` if it exists.

### Feishu / control plane

- `src/eduflow/feishu/cards_v2.py` — structured card protocol v2 public surface.
- `src/eduflow/feishu/cards_v2_schema.py` — card types, role allow-list, required fields, controlled vocabulary.
- `src/eduflow/feishu/cards.py` — v1 card helpers still used by v2 renderer.
- `src/eduflow/feishu/slash.py` — slash command dispatch.

### Runtime facts

- `.eduflow-team-state/facts/runtime-status.json` — current runtime / env_profile / verified_at.
- `.eduflow-team-state/facts/runtime-switch-events.jsonl` — runtime switch audit trail.

### Memory

- `.eduflow-team-state/facts/` — any durable facts beyond runtime-status (e.g., inbox cursors, agent status, heartbeat logs).
- `src/eduflow/memory/` — candidate generation, packet assembly, search, vector store, Obsidian export, constraints, audit.
- `src/eduflow/store/memory.py` — per-agent memory store surface.
- `src/eduflow/commands/memory_cli.py`, `remember.py`, `recall.py`, `forget.py` — memory CLI surface.
- Hermes/Obsidian memory candidates referenced by `memory_cli.py` or skills.

### Visual narrative

- `docs/media/README.md` — asset registry and export notes.
- `docs/media/readme-runtime-map.svg` — runtime architecture diagram.
- `docs/media/readme-delivery-loop.svg` — workflow delivery diagram.
- Any other SVG/PNG referenced by `README.md`.

## Output template

Every harness surface audit must produce this markdown:

```markdown
## EduFlow Harness Surface Audit

### Current surface
- Runtime:
- Task/workflow:
- Identity/skill:
- Memory:
- Feishu/control:

### Duplicate or drift risks
- ...

### README / visual narrative drift
- ...

### Context overhead risks
- ...

### Primitive-only gaps
- ...

### Recommended placement
| finding | should land in identity / workflow / skill / CLI / test / docs |
| --- | --- |
| ... | ... |

### Top next moves
1. ...
```

Fill each section with concrete file paths and role boundaries. Avoid vague statements like "some skills overlap."

### Section guidance

- **Current surface**: one-line inventory of what currently owns each capability. Example: "residency policy lives in `eduflow.toml [team.residency]` and `runtime/residency.py`; `team --json` exposes it."
- **Duplicate or drift risks**: same rule appearing in two places, or a rule in identity that contradicts code. Example: "`worker_course` notes repeat '不能发 CLOSEOUT' while `cards_v2_schema.py` enforces it at send time."
- **README / visual narrative drift**: README says one thing, code/workflow says another. Example: "README says 'local可审计AI团队操作系统' but `docs/workflows/` still reads like a chat-bot script in places."
- **Context overhead risks**: prompt/memory/skill volume that grows without bound. Example: "`eduflow.toml` `notes` for `worker_course` exceeds 1 KB and includes protocol details that should live in a skill."
- **Primitive-only gaps**: something is checkable by existing commands but not surfaced to operators. Example: "`task_event_scanner` detects `secondhand_acceptance_conflict`, but no skill or workflow tells manager what to do with it."
- **Recommended placement**: for each finding, route it to the correct layer using the promotion rules below.
- **Top next moves**: ranked, executable, and assigned to a role. Do not write "consider reviewing."

## Promotion rules

When a repeated pattern or drift is found, promote it to the smallest correct layer:

| pattern | should land in | examples |
| --- | --- | --- |
| Single-role boundary | `identity.md` or `eduflow.toml` notes | "worker_course cannot send CLOSEOUT" |
| Multi-role chain | `docs/workflows/<workflow_id>/` | "review → manager closeout handoff" |
| Machine-judgeable | CLI check / test / `task_event_scanner` | auto-detect duplicate skill IDs, role violations, stale workflow files |
| Operator patrol | monitor skill or reference | `skills/eduflow-team-monitor/references/*.md` |
| Long-term knowledge | Hermes / Obsidian / memory candidate | lessons that outlive the current release |
| One-off incident | case note / gap note | not promoted to reusable asset |

If a finding could land in multiple places, prefer the layer that requires the fewest words to enforce and the least runtime cost to check.

## Prohibitions

This skill is read-only. Do not:

- Modify real `.eduflow-team-state/` files.
- Send Feishu messages.
- Write audit results directly into `identity.md`, workflow files, or skill files unless a separate manager closeout explicitly authorizes the write.
- Execute `residency-sleep --apply` or real wake commands.
- Recommend introducing a new abstraction or dependency for a single-use finding.

## Residency and card protocol notes

This worktree includes `feat/2026-07-01-residency-phase1` capabilities. When auditing, pay special attention to:

- `residency` labels in `team --json` and `eduflow.toml [team.residency]`.
- `cards_v2` role allow-list: only `manager` can send `CLOSEOUT`, only `review_course` can send `REVIEW`, only `auto_ops` / `manager` can send `ALERT`.
- Wake failure ALERT logic in `residency_wake.py` / `wake_alert.py` and whether it can create duplicate main-group noise.
- `sleep_idle.py` default dry-run safety and the explicit `--apply` side-effect boundary.

If these files are missing in a future worktree, record them as `missing` and downgrade any residency-specific findings.

## Example finding

```markdown
### Duplicate or drift risks
- `worker_course` identity.md notes repeat the v2 card protocol forbidden types,
  while `src/eduflow/feishu/cards_v2_schema.py` already enforces the same list.
  Recommended placement: trim identity notes; keep schema as source of truth.
```
