# Task 6.3 Security Fix Report

## What Changed

### 1. `docker/agent-chrome/tcp-proxy.pl`
- Added an optional fourth `BIND_ADDR` argument.
- Default bind address changed from `0.0.0.0` to `127.0.0.1`.
- Error message now includes the bind address for easier debugging.

### 2. `docker-compose.yml`
- Both `tcp-proxy.pl` invocations in the `agent-chrome` service now pass `127.0.0.1` explicitly as the bind address:
  - `perl /opt/agent-chrome/tcp-proxy.pl 9223 127.0.0.1 9222 127.0.0.1`
  - `perl /opt/agent-chrome/tcp-proxy.pl 10086 host.docker.internal 10086 127.0.0.1`

### 3. `docker/agent-chrome/Dockerfile`
- Removed unused VNC-related packages from the image to reduce attack surface:
  - `x11vnc`
  - `novnc`
  - `websockify`

## Validation

Ran:

```bash
docker compose config
```

Result: **OK** — configuration validated successfully (115 lines of resolved output).

## Commit

- **SHA:** `831f3325b853d5e44d852db94f612b74a1d6d7fc`
- **Subject:** `security: harden agent-chrome internal proxy and remove VNC packages`

## Concerns

None. The host-side port mapping (`127.0.0.1:9233:9223`) already restricted external access from the host; this change closes the remaining internal exposure by binding the proxies to loopback inside the container as well. No runtime behavior changes are expected for EduFlow agents, which connect through the published localhost port.
