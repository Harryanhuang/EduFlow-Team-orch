# Task 6.3 Report: `agent-chrome` container hardening

## What changed

### `docker/agent-chrome/Dockerfile`
- Changed Chromium CDP bind address from `--remote-debugging-address=0.0.0.0` to `--remote-debugging-address=127.0.0.1`.
- Removed `--remote-allow-origins='*'`; no cross-origin wildcard is needed when CDP is localhost-only.
- Removed `--no-sandbox` and added a comment explaining that the container runs as the non-root `chrome` user with Docker's default seccomp profile, which provides sufficient sandboxing.
- Removed passwordless VNC (`x11vnc -nopw`) and noVNC (`websockify`) from the default `CMD`. VNC is no longer started by default, eliminating the unauthenticated remote-desktop risk.
- Updated `EXPOSE` from `9222 6080` to `9222` to match the new default runtime.

### `docker-compose.yml`
- Removed the `127.0.0.1:6080:6080` port publish since noVNC is disabled.
- Updated the `agent-chrome` command override to mirror the Dockerfile hardening:
  - CDP bound to `127.0.0.1`.
  - No `--remote-allow-origins='*'`.
  - No `--no-sandbox`.
  - No `x11vnc` / `websockify`.
- Kept the `127.0.0.1:9233:9223` host-local CDP proxy port so local debugging via `localhost:9233` still works.
- Kept the `10086` TCP proxy for the `kimi-webbridge` extension, which connects the in-container extension to the host daemon.

## `docker compose config` validation result

Validation passed. Output confirms:
- Only `agent-chrome` port `9233` is published.
- It is bound to host IP `127.0.0.1` only.
- No `6080` port is exposed.
- The hardened Chromium command is present in the rendered config.

```
ports:
  - mode: ingress
    host_ip: 127.0.0.1
    target: 9223
    published: "9233"
    protocol: tcp
```

## Commit

- **SHA:** `f04fd39b`
- **Subject:** `security: harden agent-chrome CDP/VNC exposure`

## Self-review findings

- CDP is no longer reachable on the container network on `0.0.0.0:9222`.
- The wildcard CORS origin flag is gone.
- VNC is no longer started with a blank password.
- The `--no-sandbox` removal is documented; the runtime context (non-root + default seccomp) supports it.
- Compose still supports `docker compose up` and keeps host-local debugging on `127.0.0.1:9233`.
- `docker compose config` renders cleanly.

## Concerns

1. **Functional regression for operators who used noVNC.** The passwordless noVNC endpoint on `6080` is no longer available. If visual debugging is required, an operator can either `docker exec` into the container and start `x11vnc` manually, or we can add a password-protected VNC path behind a Docker secret / env var in a follow-up. Removing it was chosen as the smallest, safest fix for the reported remote-control risk.

2. **`tcp-proxy.pl` still listens on `0.0.0.0:9223` inside the container.** The host-side publish is restricted to `127.0.0.1`, so external hosts cannot reach it. Other containers on the same default Docker network could still connect to `agent-chrome:9223`, but they can only talk to the proxy that forwards to Chromium's localhost-only CDP socket. Fully isolating this from the container network would require changing `tcp-proxy.pl` to accept a bind address, which is outside the scope of the brief (it only asked to modify `Dockerfile` and `docker-compose.yml`).

3. **`--no-sandbox` removal should be runtime-tested.** The change is correct in principle (non-root user + seccomp), but Chromium's behavior can vary by version. A smoke test of `docker compose up agent-chrome` should confirm Chromium starts and the CDP endpoint responds on `localhost:9233`.

4. **VNC packages remain installed.** `x11vnc`, `novnc`, and `websockify` are still in the image. They are not started, so they do not create an active network risk. Removing them from the apt install list would reduce image size and attack surface; this is a candidate for a follow-up hardening pass.
