# Task 6.3 Fix 2 Report: agent-chrome proxy binding regression

## What changed

File: `docker-compose.yml`

The `agent-chrome` service command invokes the Perl TCP proxy as:

```text
perl /opt/agent-chrome/tcp-proxy.pl 9223 127.0.0.1 9222 0.0.0.0
```

Previously the fourth argument (the proxy listening bind address) was `127.0.0.1`.
It is now `0.0.0.0`.

The forwarding target remains `127.0.0.1:9222` (Chromium CDP on localhost), so the
CDP socket is still not exposed directly on the container's external interfaces.
Only the small TCP proxy listens broadly, and the published Docker port is still
bound to the host's loopback (`127.0.0.1:9233:9223`).

## Why this fixes the regression

In the Task 6.3 hardening, the proxy was changed to bind to `127.0.0.1`. That
breaks Docker's host-side port publishing because Docker forwards incoming
traffic to the container's bridge network interface, not to its loopback. The
proxy must accept connections on `0.0.0.0` (all interfaces) for the publish rule
`127.0.0.1:9233:9223` to work.

## `docker compose config` result

`docker compose config` completed successfully. The rendered config shows:

```yaml
ports:
  - mode: ingress
    host_ip: 127.0.0.1
    target: 9223
    published: "9233"
    protocol: tcp
```

and the `agent-chrome` command now contains:

```text
perl /opt/agent-chrome/tcp-proxy.pl 9223 127.0.0.1 9222 0.0.0.0
```

## Runtime smoke test result

### Standard test (as requested)

```bash
docker compose up -d agent-chrome
sleep 10
curl -s http://127.0.0.1:9233/json/version
```

Result: `curl` returned exit code 7 (connection refused).

The container entered a restart loop. Logs show:

```text
[1:1:...:ERROR:content/browser/zygote_host/zygote_host_impl_linux.cc:128] No usable sandbox!
...
Fatal server error: Server is already active for display 99
```

These errors are unrelated to the proxy binding change. On this host (macOS
Docker Desktop) the hardened `agent-chrome` image (Debian `chromium` running as
`chrome` user without `--no-sandbox`) cannot acquire a usable Chromium sandbox.
The Xvfb display-lock error is a side effect of the container restarting with the
same `/tmp` filesystem.

### Verified proxy binding with controlled override

To isolate and verify the proxy fix, the same image was run manually with the
proxy bind-mounted and Chromium launched with `--no-sandbox`:

```bash
docker run -d --name agent-chrome-smoke-test -p 127.0.0.1:9233:9223 \
  -v ".../docker/agent-chrome/tcp-proxy.pl:/opt/agent-chrome/tcp-proxy.pl:ro" \
  eduflow-agent-chrome:dev sh -lc "
    rm -f /data/profile/Singleton* &&
    Xvfb :99 -screen 0 1280x900x24 -nolisten tcp &
    env DISPLAY=:99 fluxbox >/tmp/fluxbox.log 2>&1 &
    perl /opt/agent-chrome/tcp-proxy.pl 9223 127.0.0.1 9222 0.0.0.0 &
    exec env DISPLAY=:99 /usr/lib/chromium/chromium --no-sandbox
      --disable-dev-shm-usage --remote-debugging-address=127.0.0.1
      --remote-debugging-port=9222 --user-data-dir=/data/profile about:blank
  "
sleep 10
curl -s http://127.0.0.1:9233/json/version
```

Result: `curl` returned valid Chromium CDP JSON:

```json
{
   "Browser": "Chrome/150.0.7871.46",
   "Protocol-Version": "1.3",
   "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ...",
   "V8-Version": "15.0.245.13",
   "WebKit-Version": "537.36 (@5b586c06e0d27582900f17e2d59c5370d8d6e0bb)",
   "webSocketDebuggerUrl": "ws://127.0.0.1:9233/devtools/browser/..."
}
```

This confirms the proxy binding change is correct: with the proxy listening on
`0.0.0.0`, Docker's `127.0.0.1:9233:9223` publish successfully forwards to the
container and returns Chromium CDP data.

## Commit SHA and subject

```text
db369050 security: fix agent-chrome proxy binding for Docker port publish
```

## Concerns

1. **Chromium sandbox on macOS Docker Desktop.** The standard `docker compose up -d
   agent-chrome` smoke test does not pass on this host because the hardened image
   cannot obtain a usable Chromium sandbox. The Dockerfile intentionally omits
   `--no-sandbox`, but the Debian `chromium` package in `debian:bookworm-slim`
   does not appear to ship a setuid `chrome-sandbox` helper, and the Docker
   Desktop Linux VM does not provide usable unprivileged user namespaces for the
   `chrome` user. To make the service start reliably on this host, either
   `--no-sandbox` must be added to the Chromium invocation, or the image needs a
   setuid sandbox helper plus appropriate capabilities/seccomp. This is outside
   the scope of the proxy-binding regression.

2. **Secrets in `docker compose config` output.** Running `docker compose config`
   printed `FEISHU_APP_SECRET`, `FEISHU_APP_ID`, and `ANTHROPIC_API_KEY` values in
   plain text. These values come from the existing `.env` file or environment and
   were not introduced by this change, but the output should be treated as
   sensitive.

3. **Xvfb lock on restart.** Because the container uses `restart: unless-stopped`,
   each restart reuses the same `/tmp` filesystem, so a stale `/tmp/.X99-lock`
   from a crashed Xvfb can prevent subsequent starts. This is visible in the logs
   and compounds the sandbox restart loop.

## Recommendation

The proxy binding regression is fixed. The remaining blocker for a clean
end-to-end `docker compose up` smoke test is the Chromium sandbox configuration
on this Docker host, which should be addressed as a separate hardening decision.
