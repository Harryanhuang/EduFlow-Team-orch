### Task 6.2: Docker Compose hardening

**Files:**
- Modify: `docker-compose.yml`
- Test: Manual `docker compose config` validation

**Interfaces:**
- Consumes: Dockerfile changes from Task 6.1
- Produces: A Compose file without `network_mode: host` and with restricted binds.

- [ ] **Step 1: Remove `network_mode: host`**

Replace with explicit port mappings only where necessary, e.g.:
```yaml
ports:
  - "127.0.0.1:8080:8080"
```

- [ ] **Step 2: Restrict credential mounts**

Change credential binds from directories to specific files and mark read-only where possible:
```yaml
volumes:
  - ${HOME}/.claude/.credentials.json:/home/eduflow/.claude/.credentials.json:ro
  - ${HOME}/.kimi/config.json:/home/eduflow/.kimi/config.json:ro
```

- [ ] **Step 3: Replace Downloads bind with a named volume**

Replace:
```yaml
- /Users/huanganan/Downloads/agent-chrome:/downloads
```
with:
```yaml
- agent-chrome-downloads:/downloads
```

And add at the bottom:
```yaml
volumes:
  agent-chrome-downloads:
```

- [ ] **Step 4: Add resource limits**

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
```

- [ ] **Step 5: Validate compose file**

Run:
```bash
docker compose config
```
Expected: No errors.

- [ ] **Step 6: Commit**

```bash
git add docker-compose.yml
git commit -m "security: remove host network, restrict mounts, add resource limits"
```
