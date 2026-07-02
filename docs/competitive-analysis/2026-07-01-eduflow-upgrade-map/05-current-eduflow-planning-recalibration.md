---
title: EduFlow 当前状态下的整体规划合理性复盘
date: 2026-07-01
status: draft
tags:
  - EduFlow
  - planning
  - roadmap
  - Feishu
  - workflow
---

# EduFlow 当前状态下的整体规划合理性复盘

## 结论

整体方向是合理的，但执行顺序需要校准。

2026-07-02 追加校准：本地新增 `feat/2026-07-01-residency-phase1` 分支后，规划还需要再前移一层。该分支已经实现 `cards_v2`、`resident / warm / cold` 驻留策略、`residency-sleep`、`residency-wake`、wake failure ALERT 和主群体验收敛。因此后续 P0 不应再从零实现 Card Protocol v2，而应先做 `M0.5 Residency Phase1 分支审计`，确认是否 merge/adapt，再让 Employee Read Model、Ops Dashboard、Feishu Cards 直接消费 `residency + cards_v2`。

EduFlow 现在已经不是“缺一个多智能体框架”的阶段。当前代码和运行态已经有：

- 多 CLI agent adapter：Claude Code、Codex、Gemini、Kimi、Qwen、Qoder CN、Hermes。
- tmux runtime、router、watchdog、runtime guard、runtime verify、failover events。
- 飞书 slash/control plane、card v2、publish gate、dedup。
- task store、manager panel、supervisor check、evidence account、subject verifier、AP verifier。
- workflow registry、candidate、promotion、gap-map、strict validate。
- memory packet、candidate、promotion、Obsidian export。

所以规划不能再按“从零搭建 agent orchestration”来排。真正的当前瓶颈是：

**已有 primitive 很多，但 manager、auto_ops、老板在飞书里还不能稳定地 30 秒看懂：谁在做、卡在哪、证据够不够、下一步谁接、是否可收口。**

换句话说，EduFlow 下一阶段首先要补的是 **operator cognition layer**，不是再加一层复杂编排引擎。

## 本轮重新校准依据

本地检查到的事实：

- `./scripts/eduflowteam workflow validate --strict` 通过，当前有 6 条 active workflow。
- `./scripts/eduflowteam team --json` 显示团队正在真实运行，manager、auto_ops、worker_course、worker_builder、review_course 等都有状态。
- 当前运行态已经暴露典型痛点：`外显陈旧但实际功能正常`，说明 read model / status freshness 比新 agent 更急。
- `./scripts/eduflowteam workflow recommend "agent 外显陈旧但实际功能正常，想制定优化方案"` 没有给出 confident recommendation，说明 workflow 推荐词库还没有覆盖 ops/status-drift 类问题。
- `./scripts/eduflowteam task manager-panel` 在本轮只读检查中没有及时返回，被中断。这说明面向 operator 的聚合视图需要 timeout / fallback / light snapshot。
- 仓库已有 `docs/plans/2026-07-01-ecc-to-eduflow-team-skill-upgrade-plan.md`，其中的判断更贴近现状：不要重复造 runtime guard、verification gate 或 workflow engine，而要做解释层、审计层、规则蒸馏层。

## 对原升级总纲的判断

| 规划方向 | 是否合理 | 校准意见 |
| --- | --- | --- |
| 飞书员工信息展示层 | 非常合理 | 应提升为 P0，不是 UI 美化，而是当前产品第一阻塞点。 |
| 员工能力画像 | 合理 | 第一版从现有 `eduflow.toml`、status、heartbeat、runtime-status 派生 read model，不要先做复杂安装系统。 |
| workflow 快速通道 | 非常合理 | 现有 workflow registry 已经 strict valid；下一步是接 status-drift / ops-dashboard，而不是直接自动执行。 |
| Work Environment Contract | 合理但不应 P0 | 先做 task workspace metadata / worktree policy；container-use 放 P2。 |
| 阶段化编排管线 | 部分合理 | EduFlow 已经有 task status、workflow gate、review queue；重点是解释这些 gate，不是照搬新 pipeline。 |
| verify/fix loop | 合理但应变窄 | 不要做通用 verification-loop；先做 evidence-account explainer，把已有 gate 翻译成角色可执行 verdict。 |
| 外部反馈回流 | 合理但后置 | GitHub/CI/CRM/审批回流重要，但当前先修本地状态可信度。 |
| 记忆、Skill、handoff 沉淀 | 合理 | 应和 Luke_recorder / Hermes / worker_builder 的 distill 链路结合。 |
| ECC 能力目录与选择安装 | 中长期合理 | 第一版不做 installer，先做 read-only asset registry / drift-check。 |

## 需要修正的最大误区

### 误区 1：把 EduFlow 当成还缺 orchestration

不准确。EduFlow 已经有 orchestration 的主体：

```text
manager -> task -> inbox -> pane -> status -> review -> closeout -> memory/workflow
```

当前缺的是让这条链路在飞书里“可信、可读、可判断”。

### 误区 2：过早做 capability selective install

ECC 的 selective install 很有启发，但 EduFlow 当前还没到“多用户安装市场”的阶段。现在更该做：

```text
asset registry first
capability install later
```

也就是先统一登记已有资产：

- workflow
- skill
- identity rule
- patrol reference
- memory candidate
- CLI check
- Feishu card type

等这些资产能被 list/recommend/validate/drift-check，再做 employee pack / install-state。

### 误区 3：把 workflow 变成自动执行引擎

现有 docs 明确说 workflow 不是自动执行引擎，这个边界应该继续保留。

workflow 在 EduFlow 里的价值更像“协作高速公路”：

- 给 manager 调用入口。
- 给 worker/reviewer 边界。
- 给 closeout 证据。
- 给真实运行复盘。
- 给 repeated work 晋升路线。

自动执行可以以后再说，但现在更重要的是 route、gate、evidence、visible status。

### 误区 4：继续靠自然语言 marker 做外显

当前 Feishu card 已经有 v2 基础，publish gate 也很细，但状态外显仍会被自然语言摘要影响。`外显陈旧但实际功能正常` 这种问题，说明需要结构化 employee read model：

```yaml
agent:
declared_status:
latest_heartbeat:
latest_direct_signal:
latest_inbox_state:
current_task:
task_truth:
runtime_health:
context_pressure:
status_freshness:
display_verdict: active | stale_display | blocked | idle | unknown
recommended_next_action:
```

## 重新排序后的路线图

### P0：先让飞书里的状态可信

目标：老板和 manager 在飞书里 30 秒看懂团队状态。

建议做：

1. `employee_read_model.py`
   - 聚合 status、heartbeat、logs、inbox、runtime-status、task truth。
   - 明确区分 `真实卡住` 与 `外显陈旧但功能正常`。

2. `eduflow task ops-dashboard --json/--text`
   - 聚合 team status、runtime guard、context patrol、production patrol、manager actions、review queue、高优未读。
   - 必须有 timeout / degraded mode。

3. `eduflow-feishu-employee-cards`
   - 飞书卡片显示 employee status、current task、workflow gate、next owner、staleness reason。

4. `eduflow-runtime-task-drift-explainer`
   - 不是新守护进程。
   - 只是把现有 `health/runtime verify/runtime guard/team/task scanner` 输出解释成 diagnosis + safe next action。

5. `eduflow-harness-surface-audit`
   - 扫描 AGENTS/CLAUDE、identity、skills、workflow、runtime registry、memory、Feishu slash。
   - 识别重复规则、陈旧身份、prompt 过载、资产漂移。

### P1：把现有 gate 变成角色可执行语言

目标：减少 manager 临场判断和 review/worker 的误解。

建议做：

1. `eduflow-evidence-account-explainer`
   - 把 evidence account / subject verifier / review queue 变成 `PASS | NEEDS_FIX | BLOCKED | OBSERVE` packet。

2. `card protocol v2`
   - 结构化 `ACK / STARTED / PROGRESS / HANDOFF / REVIEW_VERDICT / BLOCKER / ALERT / CLOSEOUT`。
   - 减少中文字符串 marker 依赖。

3. `asset registry` 初版
   - read-only 登记 skill/workflow/identity rule/patrol reference/memory candidate/CLI check。
   - 提供 `asset list/recommend/validate/drift-check`。

4. `workflow recommend` 扩展
   - 覆盖 `status_lag`、`task_truth_drift`、`runtime_reality`、`external_state_mismatch`、`capability_gap`。

5. `manager command policy audit-only`
   - 先只审计 manager 是否越权执行长命令/写文件/修系统。
   - 不立刻 block，避免误伤真实处理。

### P2：再补隔离执行和能力供应链

目标：降低并行编辑风险，开始治理 skill/workflow/employee pack。

建议做：

1. task workspace / worktree policy
   - `workspace_mode: shared | worktree | container`
   - 先做 metadata + worktree，不急着 container。

2. `capability-pack-doctor`
   - 从 read-only asset registry 演进而来。
   - 检查缺失、重复、陈旧、过权、来源不明。

3. container-use 接入
   - 只给高风险 builder 任务、依赖安装、批量迁移使用。

4. external feedback routing
   - PR/CI/飞书评论/表格状态/CRM 回复回流原 owner。

5. runtime lane eval
   - 用真实 manager/course/review/qbank/builder 任务评估模型和 CLI 底座。

### P3：最后做跨 CLI employee pack / installer

目标：把 EduFlow 从单团队项目变成可复制的公司 AI 员工产品。

建议做：

1. employee pack schema。
2. capability install-state。
3. selective install plan/apply/repair/uninstall。
4. cross CLI packaging。
5. hosted/private company workspace 版本。

这部分是 ECC 启发最大的地方，但不应该抢 P0。

## 对“四个 EduFlow 原生 skill”的修正

更贴合当前项目的四个原生 skill 应该是：

| Skill | 装给谁 | 优先级 | 作用 |
| --- | --- | --- | --- |
| `eduflow-feishu-employee-cards` | `manager`, `auto_ops` | P0 | 把员工状态、任务、workflow gate、staleness reason 显示到飞书。 |
| `eduflow-runtime-task-drift-explainer` | `auto_ops`, `worker_builder`, `manager-lite` | P0 | 解释 runtime/status/task drift，给 safe next action。 |
| `eduflow-evidence-account-explainer` | `review_course`, `worker_course`, `worker_qbank`, `manager-lite` | P1 | 把已有 evidence gate 翻译成角色可执行 verdict packet。 |
| `eduflow-asset-registry-doctor` | `worker_builder`, `Hermes`, `Luke_recorder`, `manager-governance` | P1/P2 | 管 skill/workflow/identity/memory 资产漂移，后续再演进到 capability pack doctor。 |

注意：`capability-pack-doctor` 可以作为未来名字，但当前更准确的第一版是 `asset-registry-doctor`。因为现在要治理的是已有资产漂移，不是安装系统。

## 最小可执行的下一步

如果只做一个最小版本，建议这样切：

```text
Week 1:
1. employee_read_model.py
2. task ops-dashboard --json/--text
3. Feishu employee/team snapshot card
4. runtime-task-drift-explainer skill
```

验收标准：

- 对当前 `外显陈旧但实际功能正常` 能输出明确分类。
- 任何 agent 状态能说明 freshness 来源：heartbeat、latest log、inbox、task truth、runtime。
- 飞书卡片能给出 top 3 actions，不要求老板读 CLI。
- dashboard 命令 5 秒内返回；重项失败时输出 degraded snapshot。

## 最终判断

当前整体规划应该保留三个大方向：

1. **EduFlow = 飞书可见的公司 AI 员工操作系统。**
2. **workflow = 重复协作的高速公路，不是自动执行引擎。**
3. **ECC = 能力供应链的中长期参照，不是当前要照搬的安装包。**

但路线图要改成：

```text
先统一状态可信度
→ 再解释现有 gate
→ 再治理资产漂移
→ 再做隔离 workspace
→ 再做 capability pack / selective install
→ 最后产品化成跨 CLI 公司员工系统
```

这样更符合 EduFlow 现在的真实成熟度，也更贴合你当前“先在飞书里显示信息”的产品定位。
