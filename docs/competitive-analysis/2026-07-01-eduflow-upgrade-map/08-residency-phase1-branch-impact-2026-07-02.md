---
title: EduFlow residency phase1 新分支影响报告
date: 2026-07-02
status: draft
tags:
  - EduFlow
  - git-baseline
  - residency
  - Feishu
  - execution-prompts
---

# EduFlow residency phase1 新分支影响报告

## 结论

需要改，而且不是轻微措辞调整。

当前 `master` 仍停在 `91f0a87 Clarify project entrypoint with visual README`，但本地已经出现新分支：

```text
feat/2026-07-01-residency-phase1
```

该分支不是单点提交，而是从 Phase 0 到 Phase 5 的连续实现：

```text
76d4b43 docs(residency): Phase 0 现状审计报告
6dc5941 feat(cards): Phase 1 外显卡片协议 v2
e904eee feat(residency): Phase 2 warm residency 配置
617e298 feat(residency): Phase 3 idle-to-warm 自动回收
78fb55a feat(residency): Phase 4 wake 路径 + 失败 ALERT
88a7503 feat(residency): Phase 5 主群体验收敛
```

差异规模约为 28 个文件、4953 行新增、47 行删除。它直接实现了此前规划中的一部分 P0/P1 能力，所以 `06-claude-code-module-prompts.md` 必须从“从零实现 Card Protocol v2 / 外显状态”改成“识别、吸收、加固现有分支能力”。

## 新分支已经带来的能力

| 能力 | 主要文件 | 判断 |
| --- | --- | --- |
| Phase 0 现状审计 | `docs/plans/2026-07-01-phase0-residency-audit.md` | 已经把主群外显和温备驻留作为独立问题域建模。 |
| Card Protocol v2 | `src/eduflow/feishu/cards_v2.py`, `cards_v2_schema.py` | 已有 card type、角色 allow-list、必填字段、校验、渲染。M9 不能再从零写一套。 |
| Residency policy | `src/eduflow/runtime/residency.py`, `runtime/config.py`, `eduflow.toml` | 已定义 `resident / warm / cold`，并有 `常驻 / 温备` 外显标签。 |
| team 外显字段 | `src/eduflow/commands/team.py` | `team --json` 已新增 `residency` 字段，M1/M2 必须消费。 |
| idle-to-warm 回收 | `src/eduflow/commands/sleep_idle.py` | 已有 `residency-sleep`，默认 dry-run，`--apply` 有真实副作用。 |
| wake 路径与失败 ALERT | `src/eduflow/commands/residency_wake.py`, `wake_alert.py` | 已有 `residency-wake` 与 wake failure alert。 |
| 主群体验收敛 | `send.py`, `say.py`, `watchdog.py`, 场景测试 | 外显纪律已经不只是文档约束，开始进入 runtime/command 层。 |

## 对原规划的影响

| 模块 | 原判断 | 新判断 |
| --- | --- | --- |
| M0 基线审计 | 只读当前 HEAD | 必须同时识别 `feat/2026-07-01-residency-phase1` 是否存在、是否已 merge、是否与当前 dirty worktree 冲突。 |
| M1 Employee Read Model | 读取 status/heartbeat/log/inbox/task | 必须把 residency 作为一等状态：`residency_label`, `policy_mode`, `last_sleep_at`, `last_wake_at`, `sleep_decision`, `wake_status`。 |
| M2 Ops Dashboard | 聚合 top actions | 必须新增 residency top actions：warm agent 有高优未读、wake failed、sleep candidate、policy mismatch。 |
| M3 Feishu Snapshot Cards | 新增 employee/team cards | 应复用 `cards_v2.py`，不要在 `cards.py` 里另造平行协议。 |
| M4 Drift Explainer | runtime/status/task drift | 诊断 taxonomy 要加入 `warm_residency_expected`, `wake_failed`, `sleep_suppressed_active_task`, `residency_policy_mismatch`。 |
| M5 Harness Surface Audit | 扫 prompt/identity/skill/workflow | 扫描面要加入 `runtime/residency.py`, `store/agent_residency.py`, `feishu/cards_v2*.py`, `residency-sleep/wake`。 |
| M9 Card Protocol v2 | 从零实现协议 | 改为 hardening/adoption：审查现有协议、补缺口、接入 M3/M2，不重复实现。 |
| M10 Workspace Policy | 后续隔离执行 | 仍然后置。residency 是更靠前的运行态效率层，应该先稳定。 |

## 更新后的执行顺序

如果 `feat/2026-07-01-residency-phase1` 已合并到当前工作分支：

```text
M0 rebaseline
-> M1 Employee Read Model consuming residency
-> M2 Ops Dashboard with residency actions
-> M3 Feishu Snapshot Cards on cards_v2
-> M4/M5 drift + surface audit
-> M6/M8 evidence + workflow recommend
-> M9 card protocol hardening only if gaps remain
-> M10 workspace policy
```

如果该分支尚未合并：

```text
M0 rebaseline
-> M0.5 Residency Phase1 Branch Review
-> merge / cherry-pick / adapt decision
-> M1/M2/M3
```

我的建议是先做 M0.5，而不是直接让 Claude Code 跳到 M1。原因很简单：M1/M2/M3 的字段边界会被这条分支改变；如果不先确认分支质量，Claude Code 很容易重复造一套 `card_protocol.py` 或忽略 `residency`。

## 新增 M0.5 的最小审计重点

M0.5 不需要大改代码，第一轮只做 branch review 和合并影响判断。

必须确认：

1. `cards_v2.py` 的 card type 是否覆盖 EduFlow 当前主群外显：ACK / START / PROGRESS / HANDOFF / BLOCKED / REVIEW / CLOSEOUT / ALERT / RECORDED。
2. role allow-list 是否符合角色边界：manager 才能 CLOSEOUT，review_course 才能 REVIEW，auto_ops 才能 ALERT。
3. `team --json` 新增 `residency` 是否保持向后兼容。
4. `residency-sleep` 默认 dry-run 是否安全，`--apply` 是否只在显式调用时发生副作用。
5. `residency-wake` 失败 ALERT 是否不会制造重复主群噪音。
6. `agent_residency.json` 是否属于 facts 层，不应被测试污染真实 `.eduflow-team-state`。
7. 新测试是否覆盖 config、sleep、wake、主群收敛与 messaging。

建议验收命令：

```bash
python -m pytest tests/unit/test_cards_v2.py \
  tests/unit/test_residency.py \
  tests/unit/test_residency_sleep.py \
  tests/unit/test_residency_wake.py \
  tests/unit/test_residency_convergence.py \
  tests/unit/test_commands_messaging.py
./scripts/eduflowteam workflow validate --strict
```

## 需要提醒 Claude Code 的风险

- 不要在 M3/M9 里新建第二套卡片协议。若 `src/eduflow/feishu/cards_v2.py` 存在，优先复用或加固它。
- 不要把 `residency-sleep --apply` 放进普通测试或 smoke。默认只跑 dry-run / isolated env。
- 不要把 `温备` 误判成 `stopped`。温备是可唤醒的低成本待命态，不是失败态。
- 不要把 `team --json` 的新增字段当 breaking change。旧消费者可以忽略 `residency`，新消费者应使用它。
- 不要急着做 container/worktree。新分支已经说明当前更优先的是运行态成本和主群可读性。

## 一句话重新定位

这条新分支把 EduFlow 的目标从“让飞书看见团队状态”推进到“让公司 AI 员工有可管理的驻留成本和结构化外显纪律”。所以后续升级方案必须围绕 `employee read model + residency + cards_v2 + ops dashboard` 合并规划，而不是把它们当成三个互不相干的模块。
