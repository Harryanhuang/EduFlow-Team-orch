# Task 6.1 Report: Dockerfile Hardening

## What changed

Modified `Dockerfile` only:

- **Pinned dependency versions** via `ARG` directives:
  - `@larksuite/cli@1.0.64`
  - `@anthropic-ai/claude-code@2.1.206`
  - `@openai/codex@0.144.1`
  - `kimi-cli==1.48.0`
  - `uv==0.5.0`

- **Replaced `curl | sh` with a verified install** for `uv`:
  - Used `ADD --checksum=sha256:...` to fetch the installer script with SHA-256 verification.
  - Checksum used: `992bd895fb8766eecd090d784d14032aafae7b41d087046974be7c0c560c6c39`.
  - Installed `uv` and its tool data to `/usr/local/bin` and `/usr/local/share` so the non-root runtime user can execute them.

- **Added a non-root runtime user** `eduflow`:
  - `groupadd -r eduflow && useradd -r -g eduflow -m -d /home/eduflow eduflow`
  - Created writable directories under `/home/eduflow/`: `.eduflow`, `.claude`, `.lark-cli`, `.codex`, `.kimi`.
  - `chown -R eduflow:eduflow /home/eduflow`
  - Set `USER eduflow` before `CMD`.

- **Updated environment defaults** to point state/config at `/home/eduflow/.eduflow`:
  - `EDUFLOW_STATE_DIR=/home/eduflow/.eduflow`
  - `EDUFLOW_CONFIG_FILE=/home/eduflow/.eduflow/eduflow.toml`
  - `EDUFLOW_TEAM_FILE=/home/eduflow/.eduflow/team.json`
  - `EDUFLOW_RUNTIME_CONFIG=/home/eduflow/.eduflow/runtime_config.json`
  - `HOME=/home/eduflow`

- **Added `HEALTHCHECK`**:
  - `HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD eduflow health || exit 1`

- **Updated `VOLUME` declarations and comments** from `/data` / `/root/.lark-cli` to `/home/eduflow/.eduflow` / `/home/eduflow/.lark-cli`.

## Build test results

```text
$ docker build -t eduflow:security-hardened .
... build succeeded ...

$ docker run --rm eduflow:security-hardened id
uid=999(eduflow) gid=999(eduflow) groups=999(eduflow)

$ docker run --rm eduflow:security-hardened lark-cli --version
lark-cli version 1.0.64

$ docker run --rm eduflow:security-hardened claude --version
2.1.206 (Claude Code)

$ docker run --rm eduflow:security-hardened codex --version
codex-cli 0.144.1

$ docker run --rm eduflow:security-hardened kimi --version
kimi, version 1.48.0

$ docker run --rm eduflow:security-hardened uv --version
uv 0.5.0

$ docker run --rm eduflow:security-hardened codex-cli-usage --help
usage: codex-cli-usage [-h] {status,json,daemon,statusline,install} ...
```

The container runs as the `eduflow` user, all pinned CLIs are on `PATH`, and `/home/eduflow/.eduflow` is writable by `eduflow`.

## Commit SHA and subject

- `security: harden Dockerfile with pinned deps, non-root user, and healthcheck`

## Self-review findings

- All four brief requirements satisfied: pinned versions, verified `uv` install, non-root user, healthcheck.
- No `curl | sh` remains in the Dockerfile.
- The `uv` installer checksum was verified independently before being pinned.
- `npm install package@version` relies on npm's registry integrity checks at install time; this is the standard npm integrity mechanism.
- Only `Dockerfile` was changed, per the task scope; `docker-compose.yml` and `lifecycle.py` are intentionally left for Task 6.2.
- Per coordinator direction, the full `docker compose up` workflow will be restored in Task 6.2 by mounting credentials/state under `/home/eduflow/...`.

## Concerns

- **Healthcheck status on a fresh container**: `HEALTHCHECK CMD eduflow health || exit 1` will report `unhealthy` until `eduflow init` / `eduflow up` has been run inside the container. This matches the brief's instruction, but operators should be aware that a freshly-started idle container will not show `healthy`.
- **`docker compose up` not yet functional for non-root**: Because the current `docker-compose.yml` still mounts credentials under `/root/...` and state under `/data`, the non-root `eduflow` user cannot read those mounts. This is expected and will be fixed by Task 6.2 (Docker Compose hardening).
- **Host UID/GID mismatch on Linux bind mounts**: When Task 6.2 mounts a host directory into `/home/eduflow/.eduflow`, Linux users may need to align the host directory ownership with the container's `eduflow` UID (999) or use user-namespaces. This is a normal non-root Docker consideration, not specific to this change.
- **Build-time warning**: `useradd: warning: the home directory /home/eduflow already exists.` This is harmless; it occurs because `/home/eduflow/.claude` is created before the `eduflow` user is added.
