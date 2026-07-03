---
title: EduFlow Asset Routine Check
date: 2026-07-03
status: active
tags:
  - EduFlow
  - Asset-Registry
  - M7
  - Operator-Routine
---

# EduFlow Asset Routine Check

This document records the routine check for the M7 asset registry, the
operator-side read-only audit that keeps the workflow, skill, and identity
assets aligned with the actual repo state.

## Why a routine check

After M6 + M7 landed, the asset registry surfaces three different kinds
of drift that are not visible to the workflow engine itself:

1. **Active workflow missing standard files** (`error`):
   The workflow is `active` and registered, but its `README.md`,
   `trigger.md`, `roles.md`, `checklist.md`, or `handoff-template.md`
   is missing. The workflow engine has no signal that the asset is
   incomplete; the registry does.

2. **Skill frontmatter / identity coverage** (`warning`):
   A skill exists but its `SKILL.md` is missing `name:` or
   `description:` frontmatter, or an `identity.md` is empty. The
   surface still works, but operator visibility is reduced.

3. **Duplicates and post-promotion archives** (`warning` or `info`):
   The same `asset_id` appears in two places (e.g. a skill is mirrored
   under `skills/` and `.claude/skills/`), or an active workflow has
   a matching candidate that is intentionally retained as evidence.
   The registry distinguishes these from real bugs by severity.

## How to run

```bash
./scripts/eduflowteam-routine-check
```

The script runs three checks in order, prints a per-step summary, and
exits non-zero when any step reports an `error`-level finding:

1. `eduflow workflow validate --strict`
2. `eduflow asset validate --json`
3. `eduflow asset drift-check --json --show-remediation`

`info` and `warning` findings are listed but do not change the exit
code. The script is read-only; it never installs, copies, promotes,
or deletes any asset.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | all three checks passed (warnings/info allowed) |
| 1 | one or more checks reported an error |
| 2 | usage / environment error (e.g. REPO not a valid checkout) |

## What is "info" vs "warning" vs "error"

| Severity | Examples | Script behavior |
| --- | --- | --- |
| `error` | active workflow missing `trigger.md`; `identity.md` empty | exits 1 |
| `warning` | duplicate skill, duplicate candidate workflow, identity for unknown agent, skill missing frontmatter | lists, exits 0 |
| `info` | active+candidate pair (expected post-promotion state); gate-keyword mirror drift | lists, exits 0 |

The `info` classification exists so the routine check stays useful
without becoming noisy. The candidate_id_clashes_with_active_workflow
finding, for example, is the expected state after a manager-approved
promotion (per `docs/workflows/README.md`: "The candidate source
under `_candidates/<workflow_id>/` is retained unchanged as
evidence/source archive"). The registry surfaces it as `info` and
attaches a remediation hint so the operator can still act if the
candidate is no longer useful.

## Remediation hints

Every drift finding carries a `remediation` list. The
`--show-remediation` flag of `eduflow asset drift-check` (and the
routine check by default) prints the hints inline:

```text
WARN: category=duplicate_asset asset_id=kimi-webbridge
    -> Identify the canonical copy (the one the team actually loads).
    -> For skills: the canonical home is `skills/<id>/SKILL.md`;
       remove the duplicate under `.claude/skills/<id>/`.
INFO: category=candidate_id_clashes_with_active_workflow asset_id=ap-knowledge-base-optimization
    -> Expected post-promotion state: docs/workflows/README.md
       keeps the candidate as evidence/source archive.
    -> If the candidate is no longer useful as evidence, mark it
       as `case_note_only` in the candidate README or remove the
       directory.
```

Operators are expected to read the hints and decide what to do. The
registry itself never writes.

## Relationship to other tools

- `eduflow workflow validate --strict`: structural check on active
  workflows only. Read-only. The first stage of the routine check.
- `eduflow asset list --json`: discovery; lists all known assets.
- `eduflow asset recommend "<text>" --json`: keyword + gate-keyword
  ranking. Not part of the routine check; used on demand.
- `eduflow asset validate --json`: completeness check. The second
  stage of the routine check.
- `eduflow asset drift-check --json [--show-remediation]`: drift
  detection. The third stage of the routine check.
- `scripts/eduflowteam-routine-check`: the bundled runner for all
  three stages with a stable exit contract.

## When to run

- Before opening a manager-closeout cycle.
- After `worker_builder` updates any workflow assets.
- After adding or removing skills.
- As a CI gate, if/when the team runs CI on this repo.

The script does not depend on the running runtime, so it is safe to
run on a developer's machine, in CI, or in a `worktree`.
