# EduFlow runtime image — minimum viable.
#
# Bakes in Python 3.11 + tmux + nodejs/npm (for npx @larksuite/cli) + git
# + the eduflow package itself. Does NOT include the agent CLIs
# (claude / codex / kimi) — each has its own auth and licence
# requirement; derive from this image and add whichever you need.
#
# Volumes:
#   /home/eduflow/.eduflow  - team config + runtime state (mount a host dir)
#   /home/eduflow/.lark-cli - lark-cli OAuth profile (mount your existing one)
#
# Network:
#   lark-cli's event +subscribe long-poll needs to reach
#   open.larksuite.com / open.feishu.cn. The default bridge network is
#   recommended. If you see WebSocket stalls behind NAT (common on
#   Linux bridge networks) or on Docker Desktop, tune
#   EDUFLOW_ROUTER_STALE_S (e.g. 300) so the router respawns faster.
#   Avoid `network_mode: host`; it provides no benefit for outbound
#   long-poll and breaks cross-container DNS on Linux.

# kimi-cli ≥1.0 requires Python ≥3.12; pyproject's
# requires-python = ">=3.10" stays compatible.
FROM python:3.12-slim

# Pinned dependency versions — verify before upgrading.
ARG LARK_CLI_VERSION=1.0.64
ARG CLAUDE_CODE_VERSION=2.1.206
ARG OPENAI_CODEX_VERSION=0.144.1
ARG KIMI_CLI_VERSION=1.48.0
ARG UV_VERSION=0.5.0
ARG EDUFLOW_REVISION

# Pin apt index once; install in one layer to keep the image lean.
# `curl` is required by @larksuite/cli's postinstall script (downloads
# a platform-specific binary blob); slim image doesn't ship it.
RUN set -eu; \
    updated=0; \
    for attempt in 1 2 3; do \
        rm -rf /var/lib/apt/lists/*; \
        if apt-get -o Acquire::Retries=2 update; then \
            updated=1; \
            break; \
        fi; \
    done; \
    test "$updated" = 1; \
    apt-get -o Acquire::Retries=2 install -y --no-install-recommends \
        tmux \
        nodejs \
        npm \
        git \
        curl \
        ca-certificates \
        procps; \
    rm -rf /var/lib/apt/lists/*
# `procps` ships `ps` / `uptime` / `free`. Without it the slim image
# has none of those binaries and `_agent_usage` (ps walk for per-agent
# CPU+RSS) returns zero for every agent — boss saw "manager 0.0% / 0 B"
# in /health card 2026-05-04 even though the panes were running.
# /proc-direct fallbacks added for `_host_cpu` / `_host_mem`, but `ps`
# is the cleanest path for per-pid CPU% (kernel-computed, no two-
# snapshot delta required).

# Pre-install lark-cli at build time so the first `eduflow router`
# invocation doesn't have to fetch+install ~600 deps on cold start.
# A fresh-container `npx` install can fail under slim-image conditions
# (rc=1, install.js error) and router would exit immediately.
RUN npm install --silent --global @larksuite/cli@${LARK_CLI_VERSION} \
    && lark-cli --version

# Install Claude Code CLI so manager + worker_cc panes can actually run
# an agent. Auth: ANTHROPIC_API_KEY env (passed through compose) or
# interactive `claude /login` once inside the container — tokens
# persist via the /home/eduflow/.claude volume across restarts.
RUN npm install --silent --global @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION} \
    && claude --version

# Pre-set claude's global settings so `claude --dangerously-skip-
# permissions` (used by spawn_cmd) never pops the "Yes, I accept"
# dialog, never asks per-tool permission, and skips onboarding +
# theme picker on a fresh container.
RUN mkdir -p /home/eduflow/.claude \
    && printf '%s\n' \
       '{' \
       '  "skipDangerousModePermissionPrompt": true,' \
       '  "hasCompletedOnboarding": true,' \
       '  "theme": "dark",' \
       '  "permissions": {' \
       '    "allow": ["Bash", "Edit", "Read", "Write"]' \
       '  }' \
       '}' > /home/eduflow/.claude/settings.json

# Install Codex CLI + Kimi CLI. Same pattern as claude-code: install
# binaries here, mount host's auth state at runtime via compose so
# container reuses an already-logged-in session.
#   - codex auth: ~/.codex/auth.json (ChatGPT OAuth)
#   - kimi auth:  ~/.kimi/credentials/<cli>.json
RUN npm install --silent --global @openai/codex@${OPENAI_CODEX_VERSION} \
    && codex --version
RUN pip install --no-cache-dir kimi-cli==${KIMI_CLI_VERSION} \
    && kimi --version

# Install `uv` to pull `codex-cli-usage` — the only path to real
# usage percentages for Codex (`/usage` slash card depends on it).
# Install uv and its tools to /usr/local so the non-root runtime user
# can execute them without reaching into /root.
ADD --checksum=sha256:992bd895fb8766eecd090d784d14032aafae7b41d087046974be7c0c560c6c39 \
    https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-installer.sh /tmp/uv-installer.sh
RUN export XDG_BIN_HOME="/usr/local/bin" \
    && export XDG_DATA_HOME="/usr/local/share" \
    && export UV_TOOL_DIR="/usr/local/share/uv/tools" \
    && sh /tmp/uv-installer.sh \
    && rm /tmp/uv-installer.sh \
    && uv tool install codex-cli-usage \
    && ln -sf /usr/local/share/uv/tools/codex-cli-usage/bin/codex-cli-usage /usr/local/bin/codex-cli-usage \
    && codex-cli-usage --help > /dev/null

WORKDIR /app

# Copy only what's needed to install the package — pyproject + src.
# Tests / docs / scenarios stay out of the image to keep it small;
# devs who want the full repo should bind-mount the working tree.
COPY pyproject.toml ./
COPY setup.py ./
COPY src/ ./src/

RUN set -eu; \
    if [ -n "$EDUFLOW_REVISION" ]; then \
        build_revision="$EDUFLOW_REVISION"; \
    else \
        build_revision="sha256:$(find pyproject.toml setup.py src -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum | sha256sum | cut -d ' ' -f1)"; \
    fi; \
    EDUFLOW_BUILD_REVISION="$build_revision" pip install --no-cache-dir .

# Create a non-root runtime user and ensure all state / credential
# directories are writable by that user. Task 6.2 wires compose mounts
# to these paths; until then the image is already prepared.
RUN groupadd -r eduflow \
    && useradd -r -g eduflow -m -d /home/eduflow eduflow \
    && mkdir -p /home/eduflow/.eduflow \
    && mkdir -p /home/eduflow/.lark-cli \
    && mkdir -p /home/eduflow/.codex \
    && mkdir -p /home/eduflow/.kimi \
    && chown -R eduflow:eduflow /home/eduflow

# Defaults so a fresh container has a sensible state layout. Override
# any of these at run time via `docker run -e EDUFLOW_STATE_DIR=...`
# or compose `environment:` if you want a different layout.
ENV EDUFLOW_STATE_DIR=/home/eduflow/.eduflow \
    EDUFLOW_CONFIG_FILE=/home/eduflow/.eduflow/eduflow.toml \
    EDUFLOW_TEAM_FILE=/home/eduflow/.eduflow/team.json \
    EDUFLOW_RUNTIME_CONFIG=/home/eduflow/.eduflow/runtime_config.json \
    LARK_CLI_NO_PROXY=1 \
    HOME=/home/eduflow

VOLUME ["/home/eduflow/.eduflow", "/home/eduflow/.lark-cli"]

USER eduflow

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD eduflow health || exit 1

# Default to a shell so operators attach with `docker exec -it … bash`
# and run `eduflow up` / `eduflow health` manually. A bare
# `eduflow up` as CMD would exit immediately because tmux runs
# detached and the container would have no foreground process.
CMD ["bash"]
