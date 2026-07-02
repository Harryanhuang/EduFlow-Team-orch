---
title: EduFlow 状态可信层升级基线报告（P0 rebaseline）
date: 2026-07-02
status: draft
tags:
  - EduFlow
  - baseline
  - status-trust
  - P0
---

# EduFlow 状态可信层升级基线报告（P0 rebaseline）

> 本报告为 P0 实施前的只读基线。当前工作在 `feat/2026-07-01-residency-phase1` worktree：
> `/Volumes/Halobster/Obsidian Edu/留学公司知识库/11-Eduflow Team 多智能体项目/EduFlow-Team-orch-phase1`

## 1. Git HEAD 与分支状态

- 当前分支：`feat/2026-07-01-residency-phase1`
- 当前 HEAD：`88a7503 feat(residency): Phase 5 主群体验收敛`
- 分支历史（新→旧）：
  - `88a7503` Phase 5 主群体验收敛
  - `78fb55a` Phase 4 wake 路径 + 失败 ALERT
  - `617e298` Phase 3 idle-to-warm 自动回收
  - `e904eee` Phase 2 warm residency 配置
  - `6dc5941` Phase 1 外显卡片协议 v2
  - `76d4b43` docs(residency): Phase 0 现状审计报告
- 与 master 差异：约 28 文件、+4953 / -47 行。
- 主工作区 `EduFlow-Team-orch` 的 `master` 仍有大量未提交修改（memory MCP / runtime failover / watchdog 等），未与本分支合并。

## 2. 已验收的 phase1 能力

运行命令：

```bash
python3 -m pytest tests/unit/test_cards_v2.py \
  tests/unit/test_residency.py \
  tests/unit/test_residency_sleep.py \
  tests/unit/test_residency_wake.py \
  tests/unit/test_residency_convergence.py \
  tests/unit/test_commands_messaging.py -q
```

结果：全部通过（100%）。

已存在能力：

| 能力 | 主要文件 |
| --- | --- |
| Card Protocol v2 | `src/eduflow/feishu/cards_v2.py`, `cards_v2_schema.py` |
| Residency policy | `src/eduflow/runtime/residency.py`, `src/eduflow/store/agent_residency.py`, `eduflow.toml` |
| Sleep/Wake CLI | `src/eduflow/commands/sleep_idle.py`, `src/eduflow/commands/residency_wake.py`, `src/eduflow/commands/wake_alert.py` |
| Team 外显字段 | `src/eduflow/commands/team.py` 已新增 `residency` |
| 主群体验收敛 | `src/eduflow/commands/say.py`, `send.py`, `watchdog.py` |

## 3. 当前 primitives 列表

### runtime
- `src/eduflow/runtime/residency.py`：resident / warm / cold 策略，SleepSignals，sleep_decision，默认 idle=600s / handoff=300s / wake=60s，默认常驻 agent（manager, auto_ops, Luke_recorder）。
- `src/eduflow/store/agent_residency.py`：持久化 residency 台账（last_active_at, last_handoff_at, last_sleep_at, last_wake_at）。
- `src/eduflow/runtime/config.py`：`load_residency_policy`。
- `src/eduflow/commands/sleep_idle.py`：`residency-sleep`（默认 dry-run，`--apply` 才副作用）。
- `src/eduflow/commands/residency_wake.py`：`residency-wake`。
- `src/eduflow/commands/wake_alert.py`：wake failure ALERT。
- 既有：tmux, watchdog, pidlock, failover, verify, wake, server_metrics, lifecycle, runtime_guard, runtime_switch, runtime_events。

### task
- `src/eduflow/store/tasks.py`：flow-task schema v2，stage/status，review verdict authority，subject closeout gate，QBank lifecycle，dedup/import gate，revision-first gate。
- `src/eduflow/commands/task.py`：create/dispatch/review/submit-review/manager-overview/manager-panel/scan-anomalies/manager-actions/supervisor-check/evidence-account/publish-scan/publish-run。
- 支持模块：`task_event_scanner.py`, `task_publish_gate.py`, `task_publish_render.py`, `task_evidence_account.py`, `subject_verifier.py`, `ap_subject_verifier.py`。

### Feishu
- `src/eduflow/feishu/cards.py`：基础 card v2 构建函数。
- `src/eduflow/feishu/cards_v2.py` + `cards_v2_schema.py`：结构化协议、验证、角色 allow-list、必填字段。
- `src/eduflow/feishu/slash.py`：14 个零 LLM slash 命令（/team /health /usage /tmux /send /dispatch /submit /assign-reviewer /review-queue /manager-overview /compact /stop /clear /help）。

### workflow
- active workflows（6）：`ap-knowledge-base-optimization`, `igcse-9subject-sprint`, `igcse-item-level-prototype`, `igcse-subject-launch`, `realrun-to-workflow`, `runtime-failover-hardening`。
- `src/eduflow/commands/workflow.py`：list/recommend/use/validate/maintenance。
- `tasks.py` workflow 集成：workflow_gate_status, required_workflow_id_for_task。

### memory
- `src/eduflow/memory/`：candidate, DB, event bridge, packet, search, vector, obsidian export, constraints, audit。
- `src/eduflow/store/memory.py`：per-agent memory store。
- `src/eduflow/commands/remember.py/recall.py/forget.py/memory_cli.py`。

## 4. P0 模块建议顺序与预计触碰文件

| 模块 | 顺序 | 预计主要文件 | 关键依赖 |
| --- | --- | --- | --- |
| M1 Employee Read Model | 1 | `src/eduflow/store/employee_read_model.py`（新）, `src/eduflow/store/local_facts.py`, `src/eduflow/store/agent_residency.py`, `src/eduflow/runtime/residency.py`, `tests/unit/test_employee_read_model.py`（新） | 消费 residency + status + heartbeat + log + inbox + task |
| M2 Ops Dashboard CLI | 2 | `src/eduflow/commands/task.py`, `tests/unit/test_commands_task.py` | M1 read model |
| M3 Feishu Snapshot Cards | 3 | `src/eduflow/feishu/cards.py`, `src/eduflow/feishu/cards_v2.py`, `src/eduflow/feishu/slash.py`, `tests/unit/test_feishu_cards.py`, `tests/unit/test_feishu_slash.py` | M1 + M2；复用 cards_v2 |
| M4 Drift Explainer Skill | 4 | `skills/eduflow-runtime-task-drift-explainer/SKILL.md`（新） | 只读 skill |
| M5 Harness Surface Audit Skill | 4 | `skills/eduflow-harness-surface-audit/SKILL.md`（新） | 只读 skill |

## 5. 命令输出摘要

### workflow validate

```bash
./scripts/eduflowteam workflow validate --strict
```

输出：

```text
✅ workflow registry strict valid (6 active workflows)
- ap-knowledge-base-optimization
- igcse-9subject-sprint
- igcse-item-level-prototype
- igcse-subject-launch
- realrun-to-workflow
- runtime-failover-hardening
```

### team --json

```bash
./scripts/eduflowteam team --json
```

输出：`[]`（当前 phase1 worktree 无运行中的 agent 状态文件）。

### task list

```bash
./scripts/eduflowteam task list | head -80
```

输出：`📋 no matching tasks`

### rg 搜索 task primitives

```bash
rg -n "manager-panel|auto-ops-context|auto-ops-production|supervisor-check|evidence-account|review-queue" \
  src/eduflow/commands/task.py tests/unit/test_commands_task.py
```

命中：
- `task.py` 中 `review-queue`, `manager-panel`, `evidence-account`, `supervisor-check` 的 docstring 与 dispatch 注册。
- `tests/unit/test_commands_task.py` 中大量 `manager-panel` 与 `supervisor-check` 测试用例。

## 6. 不能碰的范围

- 真实的 `.eduflow-team-state/` 运行数据：只读，测试必须用 `isolated_env()`。
- 真实 Feishu 发送：新卡片只返回 dict，真正 send 仍由 `feishu/deliver.py` / `commands/say.py` 负责。
- 真实 runtime 切换 / tmux pane 生命周期：新的 operator cognition 层只观察，不修改。
- `residency-sleep --apply` 只能在显式调用时发生副作用；普通测试与 dashboard 只跑 dry-run / isolated env。
- 不要把 `温备` 误判成 `stopped`；温备是可唤醒的低成本待命态。

## 7. 已有测试入口

- `python3 -m pytest tests/unit/test_cards_v2.py`
- `python3 -m pytest tests/unit/test_residency*.py`
- `python3 -m pytest tests/unit/test_commands_messaging.py`
- `python3 -m pytest tests/unit/test_local_facts.py`
- `python3 -m pytest tests/unit/test_commands_task.py`
- `python3 -m pytest tests/unit/test_feishu_slash.py tests/unit/test_feishu_cards.py`
- `./scripts/eduflowteam workflow validate --strict`

## 8. 核心定位

本次 P0 不是重造 orchestration（tmux 生命周期、task 状态机、residency 回收、Feishu 传输都已存在），而是补 **operator cognition layer**：把已有的 status、residency、task gate、health、card v2 schema 聚合成稳定的员工读模型、ops dashboard、飞书 snapshot、drift 解释与 surface 审计。
