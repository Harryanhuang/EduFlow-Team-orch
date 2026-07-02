---
name: manager-first-dispatch-full-coverage
description: Playbook ensuring the first task dispatched to a new agent includes identity confirmation, skill context, and acceptance criteria. Avoids follow-up clarifications.
---

# Manager 首次派单全覆盖 Playbook

新 agent 雇佣完成后，首次派单应一次性包含所有必要信息，避免追补指令。

## 原则

首次派单 ≠ 后续追补。第一条任务消息应包含：

1. **身份确认**：agent 名称 + 角色描述
2. **Skill 上下文**：本次任务需要调用的 skill 名称和路径
3. **验收标准**：明确的完成条件（产出什么 = 任务完成）
4. **汇报要求**：完成后汇报什么、汇报给谁

## 消息模板

```
【T-<id> <任务名称>】

背景：
<2-3 句话说明任务背景和来龙去脉>

你的角色：
<agent 名称>，负责 <一句话职责>。

可用 Skill：
- <skill-name-1>（.claude/skills/<path-1>）— <一句话用途>
- <skill-name-2>（.claude/skills/<path-2>）— <一句话用途>

任务步骤：
1. <步骤一>
2. <步骤二>
3. <步骤三>

验收标准：
- [ ] <标准一>
- [ ] <标准二>
- [ ] <标准三>

汇报要求：
- 完成后 eduflow send manager <name> "<汇报内容>"
- eduflow say <name> "<一句话完工>" --to user
- eduflow remember <name> task_completed "<记录>"

边界：
- <不该做的事>
- <不要动什么>
```

## 验收：一条合格的首次派单

manager 发出前应自检：
- [ ] 消息包含背景（不是"去做 X"三个字）
- [ ] 列出了需要的 skill（名称 + 一句话用途）
- [ ] 有明确的验收 checklist
- [ ] 指定了汇报格式
- [ ] 说明了边界/不该做的事

## 反面示例（❌ 不合格）

```
T-99 去调研一下那个什么老师资料怎么弄的
```

缺少：背景、skill、验收标准、汇报格式、边界。

## 正面示例（✅ 合格）

```
【T-102 雇佣新员工：FindClass 老师资料整理员】

背景：
FindClass 小程序需要上架老师信息，目前资料通过飞书表单收集，
整理到 Obsidian 目录，再通过脚本上传到服务器。

你的角色：
worker_builder，负责搭建新 agent 框架（身份、配置、tmux pane）。

可用 Skill：
- new-agent-onboarding（.claude/skills/new-agent-onboarding.md）— 新 agent 入职指南
- 参考现有 worker_* agent 的 identity.md 格式

任务步骤：
1. 在 eduflow.toml 新增 [team.agents.worker_teacher] 段
2. 创建 identity.md
3. eduflow hire worker_teacher
4. 扫描 codex 目录中与 FindClass 相关的 skill 并安装

验收标准：
- [ ] 新 agent 能正常启动、有完整 identity.md
- [ ] 相关 skill 已安装并可调用
- [ ] 完成后回报 manager（含 agent 名称、skill 清单、启动验证结果）

汇报要求：
- 完成后 eduflow send manager worker_builder "T-102 完工汇报：..."
- eduflow say worker_builder "T-102 完工：..." --to user

边界：
- 不需要实现飞书表单/上传服务器的具体代码，只需把 agent 框架搭好
```

## 记录

每次首次派单后，manager 用 `eduflow log manager task_dispatched "T-<id> first dispatch to <agent>: <summary>"` 记录，便于后续回溯。
