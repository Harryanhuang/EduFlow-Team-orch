# Task 6.2 Report: Docker Compose hardening

## What changed

Modified `docker-compose.yml` to align with the Task 6.1 Dockerfile (non-root `eduflow` user, `HOME=/home/eduflow`) and reduce the container's attack surface:

1. **Removed `network_mode: host`** from the `eduflow` service. The service now uses the default Docker bridge network.
2. **Restricted credential mounts**:
   - Moved all credential binds from `/root/...` to `/home/eduflow/...`.
   - Replaced directory mounts for `.codex` and `.kimi` with file-level mounts:
     - `${HOME}/.codex/auth.json` → `/home/eduflow/.codex/auth.json:ro`
     - `${HOME}/.kimi/config.json` → `/home/eduflow/.kimi/config.json:ro`
   - Marked read-only (`:ro`) for files that do not need to write token refreshes back to the host (`lark-cli/config.json`, `codex/auth.json`, `kimi/config.json`, `host-claude.json`).
   - Left `.claude/.credentials.json` read-write so Claude OAuth token refreshes persist back to the host, matching the original behavior.
   - Left `.lark-cli/cache` and `.claude/projects` as narrowly-scoped directory mounts because they contain runtime cache / usage-log files that are not single-file credentials.
3. **Replaced the host Downloads bind** with a named volume:
   - Removed `/Users/huanganan/Downloads/agent-chrome:/downloads`
   - Added `agent-chrome-downloads:/downloads`
   - Declared `agent-chrome-downloads:` in the top-level `volumes:` section.
4. **Added resource limits** to the `eduflow` service:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2.0'
         memory: 4G
   ```
5. **Updated comments** to describe the non-root user layout and remove the obsolete host-network justification.

## Validation

Ran:

```bash
docker compose config
```

Result: **passed** (exit code 0). The resolved Compose file shows:

- `eduflow` service is on the default bridge network (`networks: default`).
- Credential bind targets are all under `/home/eduflow/`.
- `.codex/auth.json` and `.kimi/config.json` mounts are `read_only: true`.
- `agent-chrome-downloads` is a named volume mounted at `/downloads`.
- Resource limits are present (`cpus: 2`, `memory: 4294967296`).

> Note: `docker compose config` interpolates values from `.env`, so the emitted config contained live credential values on this workstation. Operators should avoid sharing the raw output.

## Commit

```
7bced0ff security: remove host network, restrict mounts, add resource limits
```

## Self-review findings

- Task 6.2 brief steps 1–5 are complete.
- The existing `docker compose up` workflow is preserved; no new build-time requirements were introduced.
- No secrets were committed; the change is limited to `docker-compose.yml`.

## Concerns

1. **Stale deployment docs**: `docs/DEPLOYMENT.md` still documents the old `/root/.codex` and `/root/.kimi` mount paths. It should be updated to match `/home/eduflow/...`.
2. **Missing host credential files on this workstation**: `~/.claude/.credentials.json` and `~/.kimi/config.json` do not exist here. `docker compose config` still passes, but `docker compose up` would cause Docker to create empty directories at those host paths. This is pre-existing behavior for the `.credentials.json` mount and acceptable on hosts where the files are present; on this host an operator would need to create/extract them before running the container.
3. **Long-poll behavior without host networking**: The original comment noted that `network_mode: host` helped avoid NAT timeouts on Linux for `lark-cli event +subscribe`. With the default bridge, the operator may need to tune `EDUFLOW_ROUTER_STALE_S` (suggested 300 s) if the WebSocket goes quiet.
4. **Source bind mount permissions**: `./src:/app/src` remains RW for hot reload. Because the Dockerfile now runs as `eduflow`, file ownership on Linux hosts may need adjustment so the container user can write the editable-install metadata.
