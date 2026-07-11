### Task 6.1: Dockerfile hardening

**Files:**
- Modify: `Dockerfile`
- Test: Manual `docker build` + `docker run --user ...`

**Interfaces:**
- Consumes: None
- Produces: A Dockerfile with pinned versions, verified installs, and a non-root user.

- [ ] **Step 1: Pin npm package versions and add integrity checks**

Replace lines like:
```dockerfile
RUN npm install --silent --global @larksuite/cli@latest
```
with:
```dockerfile
# Pin lark-cli version; verify via npm view before upgrading.
ARG LARK_CLI_VERSION=1.0.64
RUN npm install --silent --global @larksuite/cli@${LARK_CLI_VERSION}
```

Do the same for `@anthropic-ai/claude-code` and any other global npm package.

- [ ] **Step 2: Replace `curl | sh` with verified install**

Replace:
```dockerfile
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
```
with:
```dockerfile
ARG UV_VERSION=0.5.0
ADD --checksum=sha256:<hash> https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-installer.sh /tmp/uv-installer.sh
RUN sh /tmp/uv-installer.sh && rm /tmp/uv-installer.sh
```
(Replace `<hash>` with the actual SHA-256 for the chosen release.)

- [ ] **Step 3: Add non-root user**

Near the end of `Dockerfile`, before `CMD`:
```dockerfile
RUN groupadd -r eduflow && useradd -r -g eduflow -m -d /home/eduflow eduflow
USER eduflow
```

Ensure the application state directory is writable by this user:
```dockerfile
RUN mkdir -p /home/eduflow/.eduflow && chown -R eduflow:eduflow /home/eduflow
ENV EDUFLOW_STATE_DIR=/home/eduflow/.eduflow
```

- [ ] **Step 4: Add health check**

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD eduflow health || exit 1
```

- [ ] **Step 5: Build and smoke-test**

Run:
```bash
docker build -t eduflow:security-hardened .
docker run --rm eduflow:security-hardened id
```
Expected output contains `eduflow` user, not `root`.

- [ ] **Step 6: Commit**

```bash
git add Dockerfile
git commit -m "security: harden Dockerfile with pinned deps, non-root user, and healthcheck"
```
