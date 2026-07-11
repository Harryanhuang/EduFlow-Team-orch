# Task 6.2 Fix Report — Compose state mount + docs alignment

## What changed

1. `docker-compose.yml`
   - Changed the state bind mount from `./team-data:/data` to `./team-data:/home/eduflow/.eduflow`, matching the non-root `eduflow` user's home layout declared by the Dockerfile (`EDUFLOW_STATE_DIR=/home/eduflow/.eduflow`).
   - Updated the file header comment to describe `/home/eduflow/.eduflow` instead of `/data`.
   - Extended the `EDUFLOW_ROUTER_STALE_S` comment to mention Linux NAT timeout risk for long-poll WebSocket connections on the default bridge network.

2. `Dockerfile`
   - Replaced the `network_mode: host` / `--network host` recommendation with guidance to use the default bridge network and tune `EDUFLOW_ROUTER_STALE_S` if NAT timeouts cause stalls.

3. `docs/DEPLOYMENT.md`
   - Refreshed the Docker deployment steps:
     - `docker compose exec --workdir /home/eduflow/.eduflow eduflow eduflow init` (was `/data`).
   - Refreshed the compose mounts table to use `/home/eduflow/...` paths and explicitly mark read-only mounts (`lark-cli/config.json`, `claude.json`, `codex/auth.json`, `kimi/config.json`).

## `docker compose config` result

Validated successfully. Output confirms:

- `eduflow` service binds `./team-data` to `/home/eduflow/.eduflow`.
- Credential mounts target `/home/eduflow/.lark-cli/config.json`, `/home/eduflow/.claude/.credentials.json`, `/home/eduflow/host-claude.json`, `/home/eduflow/.codex/auth.json`, and `/home/eduflow/.kimi/config.json`.
- Read-only mounts are correctly flagged (`read_only: true`).
- No `network_mode: host` is present.

## Full suite test result

```bash
python3 tests/run.py
```

Result: `tests: 2285 passed, 42 failed`

This matches the stated baseline of 42 pre-existing failures; no new failures were introduced by these documentation / compose changes.

## Commit SHA and subject

- **SHA:** `31706396129b5175a00d571dfd43c8e7fe4b4a26`
- **Subject:** `security: align compose state mount and docs with non-root Dockerfile`

## Concerns

None. The changes are limited to comments, documentation, and compose mount paths; no runtime code was modified.
