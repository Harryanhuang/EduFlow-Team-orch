---
name: agent-hiring-checklist
description: Complete checklist for hiring a new agent in the EduFlow team. Covers identity creation, team config, tmux provisioning, skill installation, and verification.
---

# Agent Hiring Checklist

新 agent 雇佣完整流程检查清单。用于 worker_builder 或 manager 雇佣新 agent 时逐项确认。

## 阶段一：基础配置

- [ ] 确定 agent 名称（按团队命名规范：`worker_<domain>` / `review_<domain>`）
- [ ] 确定 runtime 配置（新建或复用 `runtime_registry` 条目）
- [ ] 确定 `eduflow.toml` 中的 `[team.agents.<name>]` 段
  - [ ] `runtime` 字段（必填）
  - [ ] `role` 字段（必填，一句话角色描述）
  - [ ] `specialty` 字段（推荐，技能标签列表）
  - [ ] `tone` 字段（推荐，LLM 输出风格）
  - [ ] `notes` 字段（推荐，包含外显规则和红线）
  - [ ] `card_color` 字段（推荐，飞书卡片颜色）
  - [ ] `lazy` 字段（可选，默认 false）

## 阶段二：身份文件

- [ ] 创建 `.eduflow-team-state/agents/<name>/identity.md`
  - [ ] 第一行：`# <name> — <角色描述>`
  - [ ] 第二行：`You are **<name>**, a team worker. Your role is **<角色>** running on **<cli>** (model: \`<model>\`).`
  - [ ] `## Your job` 章节：核心职责 + ACK + 汇报流程
  - [ ] `## Argument-order contract` 章节：send/say 参数顺序
  - [ ] `## Working directory rule` 章节
  - [ ] `## Quick reference` 章节：常用命令
  - [ ] `## Memory vs log` 章节

> **提示**：通常不需要手动创建 identity.md，执行 `eduflow hire <name>` 时系统会自动调用 `identity.write()` 生成。手动创建仅用于特殊定制。

## 阶段三：Tmux 与启动

- [ ] `eduflow hire <name>` 创建 tmux window
- [ ] 确认 pane 状态为 "待命"（非 "initializing" 持续超过 2 分钟）
- [ ] `eduflow reidentify <name>` 注入 init prompt
- [ ] `eduflow peek <name>` 确认 agent 已醒（"空闲" / "已处理 N 条"）
- [ ] `eduflow team` 确认 heartbeat 在最近 1 分钟内

> **⚠️ 关键教训（2026-06-28）**：如果中途修改了 runtime 配置（如从错误的 runtime 改为正确的），
> **必须 kill 旧 pane + rehire** 才能生效。`reidentify` 只注入文本，不会重启 tmux pane，
> 旧的 env_vars（包括 API token）会持久化在 pane 中，导致 401 认证失败。
> 正确流程：`tmux kill-window -t <session>:<agent>` → `eduflow hire <agent>` → `eduflow reidentify <agent>`。

## 阶段四：Skill 安装

- [ ] 扫描与 agent 核心职责相关的 skill
- [ ] 从 codex 目录（`/Volumes/Halobster/Codex相关/skills/`）复制到项目 `.claude/skills/`
- [ ] `eduflow reidentify <name>` 确保 agent 识别到新 skill
- [ ] 更新 `.claude/skills/skill-registry.md`

## 阶段五：验证与验收

- [ ] 发一条测试任务到 agent inbox（`eduflow send <name> worker_builder "测试任务：回复收到"`）
- [ ] 确认 agent ACK 了消息（`eduflow read <local_id>` 查看 ACK 状态）
- [ ] 确认 agent 用 `say` 回复了用户（如 chat.publish 配置允许）
- [ ] 确认 agent 用 `send` 回复了 manager
- [ ] 确认 `eduflow peek <name>` 显示已处理 N 条

## 阶段六：Onboarding 指引

- [ ] 确认 `new-agent-onboarding.md` skill 可被新 agent 访问
- [ ] agent 首次启动后应自动走 onboarding 流程
- [ ] 确认 agent 向 manager 报到（`eduflow send manager <name> "新员工报到"`）

## 验收完成

全部勾选后，向 manager 发送雇佣完成报告：

```bash
eduflow send manager worker_builder "T-<id> 完工：新 agent <name> 已雇佣。
基础配置 ✅ | 身份文件 ✅ | Tmux 启动 ✅ | Skill 安装 ✅ | 验证 ✅ | Onboarding ✅
Agent 名称: <name>
Runtime: <runtime_name>
CLI: <cli> + <model>
已安装 Skill: <列表>
验证结果: 测试任务已 ACK + 回复正常"
```
