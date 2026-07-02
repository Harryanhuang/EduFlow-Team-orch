# Agent Chrome for web-access

This project can run a dedicated Chromium container for `web-access` so agents
do not touch the host Chrome profile or macOS Keychain.

## Start

```bash
docker compose up -d agent-chrome
```

The container exposes Chrome DevTools Protocol on the host at:

```text
http://127.0.0.1:9233
```

The project-local `web-access` config is pinned to that endpoint:

```text
.claude/skills/web-access/config.env
WEB_ACCESS_CDP_ENDPOINT=http://127.0.0.1:9233
```

## Downloads

Browser downloads are written inside the container to:

```text
/downloads
```

That path is bind-mounted to this host directory:

```text
downloads/agent-chrome/
```

So a PDF downloaded by the container browser appears on the Mac under the
project workspace immediately.

## Verify

```bash
curl -s http://127.0.0.1:9233/json/version
CLAUDE_SKILL_DIR="$PWD/.claude/skills/web-access" node .claude/skills/web-access/scripts/check-deps.mjs
```

Expected result:

```text
browser: ok (Remote CDP (127.0.0.1:9233), port 9233) [WEB_ACCESS_CDP_ENDPOINT]
proxy: ready (Remote CDP (127.0.0.1:9233))
```

## Reset

```bash
pkill -f cdp-proxy.mjs || true
docker compose restart agent-chrome
```

To delete the container browser profile:

```bash
docker compose down
docker volume rm eduflow-team-orch_agent-chrome-profile
```
