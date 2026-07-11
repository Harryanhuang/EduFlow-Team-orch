### Task 6.3: `agent-chrome` container hardening

**Files:**
- Modify: `docker/agent-chrome/Dockerfile`, `docker-compose.yml`
- Test: Manual port scan after `docker compose up`

**Interfaces:**
- Consumes: None
- Produces: Chromium CDP and VNC are not exposed to the container network.

- [ ] **Step 1: Restrict Chromium CDP to localhost**

In `docker/agent-chrome/Dockerfile`, change:
```dockerfile
--remote-debugging-address=0.0.0.0
```
to:
```dockerfile
--remote-debugging-address=127.0.0.1
```

Remove or narrow `--remote-allow-origins='*'` to the exact origin needed.

- [ ] **Step 2: Secure or disable VNC**

If VNC is required, set a password:
```dockerfile
RUN mkdir -p ~/.vnc && x11vnc -storepasswd "$(cat /run/secrets/vnc_password)" ~/.vnc/passwd
CMD ["x11vnc", "-usepw", "-forever", "-shared", "-display", ":99"]
```
If VNC is not required, remove the `x11vnc` command entirely.

- [ ] **Step 3: Remove `--no-sandbox` if possible**

If the container already runs as a non-root user with seccomp, remove `--no-sandbox`. If it must stay, add a comment explaining why and reference the threat model.

- [ ] **Step 4: Update compose ports**

Ensure no CDP/VNC ports are published to `0.0.0.0`. If they must be exposed for local debugging, bind only to `127.0.0.1`:
```yaml
ports:
  - "127.0.0.1:9222:9222"
```

- [ ] **Step 5: Commit**

```bash
git add docker/agent-chrome/Dockerfile docker-compose.yml
git commit -m "security: harden agent-chrome CDP/VNC exposure"
```
