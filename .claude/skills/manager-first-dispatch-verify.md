---
name: manager-first-dispatch-verify
description: Playbook for manager to verify a new agent is ready after dispatching a task. Run reidentify + peek to confirm the agent pane is ready before moving to the next task.
---

# Manager 首次派单最小验证 Playbook

每次派单给新 agent（尤其是刚雇佣的）后，manager 必须做最小验证，确认 agent 真正 ready，才能进入下一个任务。

## 什么时候用

- 新 agent 首次被派任务
- agent 刚被 reidentify 后
- agent 长时间无响应，怀疑 pane 未就绪

## 验证步骤

### 1. reidentify（确保身份已注入）

```bash
eduflow reidentify <agent-name>
```

这会：
- 重新生成 identity.md（从 eduflow.toml 读取最新配置）
- 向 tmux pane 注入 init prompt
- 触发 agent 醒来读取 inbox

### 2. peek（确认 pane ready）

```bash
eduflow peek <agent-name>
```

检查输出中是否包含：
- ✅ "空闲" / "待命" / 已处理 N 条 → pane 已就绪
- ❌ "initializing" → 还在启动中，等 30s 再 peek
- ❌ 空白 / 无输出 → pane 可能未正确 provision，检查 tmux

### 3. team 状态确认

```bash
eduflow team 2>&1 | grep <agent-name>
```

确认：
- 状态不是 "initializing"（除非刚 hire）
- heartbeat 时间在最近 1 分钟内

### 4. inbox 确认（可选）

```bash
eduflow inbox <agent-name>
```

如果派了任务但 inbox 为空，说明 deliver 可能没送到，需要检查 router/deliver 日志。

## 验证失败处理

| 现象 | 可能原因 | 处理 |
|------|---------|------|
| peek 输出空白 | pane 未正确 provision | `eduflow down` → `eduflow up` 重拉 |
| peek 显示 zsh parse error | init prompt 格式问题 | `eduflow reidentify <agent>` 重注 |
| peek 显示 "initializing" 超过 2min | CLI 启动慢或卡住 | 检查 tmux pane 内容，必要时 kill 重拉 |
| team 无 heartbeat | agent 未活跃运行 | 检查 pane 是否存活：`tmux list-windows -t EduFlowTeam` |

## 验收标准

验证通过 = 以下全部满足：
- [ ] reidentify 返回 `✅ re-injected`
- [ ] peek 显示 agent 已醒（非 initializing / 非空白）
- [ ] team 状态心跳在 1 分钟内
- [ ] 如果派了任务，inbox 里有对应消息
