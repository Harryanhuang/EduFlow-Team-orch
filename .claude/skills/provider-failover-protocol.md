---
name: provider-failover-protocol
description: SOP for handling Claude Code / LLM provider failures (API key expiry, rate limit, proxy down, route unavailable). Use when any agent shows provider_unavailable, fallback_chain_exhausted, API error, or auth_failure.
metadata:
  type: workflow
  generated_by: auto_ops
  date: 2026-06-24
  source: worker_course provider_unavailable incident 2026-06-24 (20min→5min fix)
---

# Provider Failover Protocol

## Use When

- Agent pane shows: `provider_unavailable`, `fallback_chain_exhausted`, `API error`, `auth_failure`
- `claudeteam health` shows: `runtime_status_env_drift` with `live_env_unavailable`
- Agent reports "当前卡在：provider 问题"
- After CC Switch proxy (127.0.0.1:15721) restart or upstream change

## Diagnosis Steps

### 1. Identify the Failed Provider

```bash
# Check agent's current runtime config
claudeteam team <agent> | grep -i "provider\|model\|route"

# Check agent pane for error details
tmux capture-pane -t EduFlowTeam:<agent> -p | tail -20
```

Record: which route, which provider, which model.

### 2. Check CC Switch Proxy

```bash
curl -s http://127.0.0.1:15721/v1/models | python3 -m json.tool
```

- Empty model list = proxy alive but no models loaded (upstream misconfigured)
- Connection refused = proxy down, restart needed
- Model list present = proxy OK, issue is upstream

### 3. Check Upstream API

```bash
# Test specific route (replace with actual route name)
curl -s http://127.0.0.1:15721/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"<model_name>","messages":[{"role":"user","content":"ping"}],"max_tokens":5}'
```

Response:
- 200 OK = route works, issue may be elsewhere
- 401/403 = API key expired
- 502/503 = upstream server error
- Timeout = network/rate limit

### 4. Check Route Configuration

```bash
# Where routes are configured
cat .eduflow-team-state/agents/<agent>/identity.md | grep -i "route\|provider\|model"
```

Known routes:
- `course_backup_minimax` → minimax API (was failing 2026-06-24)
- `course_backup_glm_5_2` → supxh_glm_5_2/GLM5.2 (stable fallback)
- `ops_primary` → anthropic-proxy (stable)
- `builder_primary` → anthropic-proxy (stable)
- `qbank_primary` → anthropic-proxy (stable)

## Failover Actions

### Route Switch (Most Common)

When one route fails and another is known-stable:

1. Update agent's runtime config to point to working route
2. Restart agent pane:
   ```bash
   tmux send-keys -t EduFlowTeam:<agent> "/exit" Enter
   sleep 2
   tmux send-keys -t EduFlowTeam:<agent> "claude" Enter
   ```
3. Verify pane shows new provider in welcome line
4. Send test message to confirm working

### API Key Refresh

When 401/403:

1. Check if key was rotated — consult manager
2. Update env var in agent's runtime config
3. Restart agent pane (same as above)

### Proxy Restart

When CC Switch is down:

```bash
# Check if process is alive
ps aux | grep "15721" | grep -v grep

# If dead, restart (location varies by deployment)
# Contact worker_builder for restart
```

### Escalation Path

If none of the above works within 5 minutes:

1. Report to manager with diagnosis summary:
   ```bash
   eduflow send manager auto_ops "provider failover 阻塞：[agent] 的 [route] 不通，已尝试 [动作X/Y/Z]，均失败。需要 [人工介入/上游检查/API key 更新]" 高
   ```
2. If blocking a critical path (e.g., course production), recommend route switch even if not ideal

## Timeline Expectations

| Step | Target Time |
|------|-------------|
| Diagnosis (steps 1-4) | 2 min |
| Route switch / fix | 3 min |
| Verification | 1 min |
| Total | **5 min** |

If > 5 min without resolution: escalate to manager.

## Known Provider Issues

| Provider | Route | Last Failure | Root Cause | Status |
|----------|-------|-------------|-----------|--------|
| minimax | course_backup_minimax | 2026-06-24 00:10 | API error on redirect | Fixed: switched to glm_5_2 |
| anthropic-proxy | ops_primary | 2026-06-21 | auth_failure false positive (gh auth login footer) | Fixed: watchdog.py markers refined |
| CC Switch | 127.0.0.1:15721 | 2026-06-24 | /v1/models returns empty | Upstream misconfigured |

## Anti-Patterns

- **Don't** restart agent pane without checking if it's mid-task (lost context)
- **Don't** switch routes without verifying the new route works first
- **Don't** assume "provider_unavailable" means API down — check proxy, route, and key
- **Don't** spend > 5 min diagnosing without escalating — the protocol exists to save time
- **Don't** let runtime guard stale label persist after fix — reset it:
  ```bash
  claudeteam set-runtime <agent> <working_route>
  ```
