# Production Contract Pilot — 任务测试安排

> 由 Claude 在 2026-07-07 生成。本文件是 `README.md` 的落地执行版，manager 可以按行勾选、填表、跑命令。

## 目标

在 5-10 个真实 course/qbank review-repair 任务上验证 read-model 是否让 manager 更快、worker 更聚焦、review 更具体、closeout 更轻松。

## 候选任务筛选标准（必须全部满足）

- [ ] `stage` 为 `curriculum` 或 `qbank`
- [ ] 当前状态为 `in_progress`、`blocked`、`submitted_for_review` 之一（即还在流转中）
- [ ] 至少满足以下一条：
  - 之前被 `review_course` reject 过（`required_fix` 非空）
  - `loop_cycle_count >= 1`（已经在 repair loop 里）
  - 有非空的 `manager_action_type`（reviewer 请求 manager 介入）
- [ ] 不是已经 `delivered` / `cancelled` / `failed` 的终止态任务
- [ ] 不涉及正在进行的敏感/大规模状态操作（如正在 closeout 的 subject）

## 当前真实任务扫描结果（2026-07-07）

已执行 `task list --status in_progress/blocked/submitted_for_review` 和
`readiness-check / loop-contract / evolution-packet` 预检。

**活跃任务 6 个**：

| task_id | 当前状态 | workflow | readiness.overall | loop-contract.failed | evolution-packet | 备注 |
|---------|----------|----------|-------------------|---------------------|------------------|------|
| T-2  | in_progress | - | warn | 0 | 无候选 | micro-outline，简单验证任务 |
| T-29 | in_progress | igcse-subject-launch | warn | 0 | 无候选 | AddMath 0606 C-class seed |
| T-30 | in_progress | igcse-subject-launch | warn | 0 | 无候选 | Combined Science 0653 C-class seed |
| T-31 | in_progress | igcse-subject-launch | warn | 0 | 无候选 | Computer Science 0478 C-class seed |
| T-55 | submitted_for_review | ap-knowledge-base-optimization | warn | 0 | 无候选 | AP Chemistry full subject sample |
| T-57 | submitted_for_review | - | warn | 0 | 无候选 | A-Level Physics 样板改造 |

**关键发现**：

- 当前**没有** `blocked` / `failed` / `manager_action` / 已 `reject` 的任务
- 所有 6 个任务的 `evolution-packet` 都返回 `{"candidates": []}`，符合预期
  （触发器未命中）
- `readiness.overall = warn` 的原因都是：
  - `productivity = warn`：worker_course 刚恢复，还没有新的 log 写入
  - `source = warn`：curriculum 任务还没有 evidence_packet / verdict
- **T-55 和 T-57** 已 `submitted_for_review`，是最接近产生 repair 场景的任务
  —— 等 review_course 给出 verdict 后，如果被 reject，立刻进入 pilot

## 推荐的 pilot 测试策略

由于当前没有现成的 reject/failed 任务，建议采用 **"baseline + 跟踪"** 策略：

1. **现在**：把上面 6 个任务作为 baseline 记录到 `acceptance-log.md`（可选）
2. **等待 T-55 / T-57 的 review verdict**：
   - 如果 reject → 立刻对该任务跑完整 pilot 流程（readiness → loop-contract →
     handoff → repair → evolution-packet → acceptance-log）
   - 如果 approve → 该任务不适合 pilot，继续等待下一个 review 周期
3. **对 in_progress 任务（T-29/T-30/T-31）**：等它们 `submit-review` 后被 reject，
   再进入 pilot
4. **不主动制造 reject**：不要为了让 pilot 有数据而去 reject 一个本来可以
   approve 的任务

## Pilot 执行表（第一批跟踪对象，已预填）

| 行号 | task_id | stage | 触发原因 | 已跑 readiness | 已跑 loop-contract | 已派 handoff | 已跑 evolution-packet | 已填 acceptance-log |
|------|---------|-------|----------|----------------|--------------------|--------------|----------------------|---------------------|
| 1 | T-55 | curriculum | 等待 review verdict | ✅ | ✅ | ⬜ | ✅ | ⬜ |
| 2 | T-57 | curriculum | 等待 review verdict | ✅ | ✅ | ⬜ | ✅ | ⬜ |
| 3 | T-29 | curriculum | 等待 submit-review → reject | ✅ | ✅ | ⬜ | ✅ | ⬜ |
| 4 | T-30 | curriculum | 等待 submit-review → reject | ✅ | ✅ | ⬜ | ✅ | ⬜ |
| 5 | T-31 | curriculum | 等待 submit-review → reject | ✅ | ✅ | ⬜ | ✅ | ⬜ |
| 6 | T-2  | curriculum | 等待 submit-review → reject | ✅ | ✅ | ⬜ | ✅ | ⬜ |
| 7 | | | | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 8 | | | | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 9 | | | | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 10 | | | | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |

> ✅ 表示已在 2026-07-07 由 Claude 预跑完成（只读）

## 每个任务的固定命令流程

对表格里的每一个 `task_id`，按顺序执行：

```bash
# 1. readiness check（如果 overall=fail，暂停该任务，先解决 readiness）
./scripts/eduflowteam task readiness-check <TASK_ID> --json

# 2. loop contract（拿到 failed_checks / next_required_output / evidence_refs）
./scripts/eduflowteam task loop-contract <TASK_ID> --json

# 3. 可选：查看证据账户
./scripts/eduflowteam task evidence-explain <TASK_ID> --json

# 4. 用 handoff-template.md 写消息并 send（manager 手动决策，不要 auto-dispatch）
# ./scripts/eduflowteam send worker_course manager "..." 高

# 5. 等 worker 修复 + review 完成后，跑 evolution-packet
./scripts/eduflowteam task evolution-packet <TASK_ID> --json

# 6. 填 acceptance-log.md（手动 append 一行）
```

## 批量预检脚本（只读，安全）

如果你已经填好了候选 task_id，可以用下面这个脚本一次性跑 readiness + loop-contract：

```bash
#!/bin/bash
# pilot-preflight.sh — 只读预检，不修改任何状态
set -euo pipefail
TASKS=(T-?? T-?? T-??)  # 改成你的真实 task id
for tid in "${TASKS[@]}"; do
  echo "=== $tid ==="
  ./scripts/eduflowteam task readiness-check "$tid" --json | jq '.readiness.overall'
  ./scripts/eduflowteam task loop-contract "$tid" --json | jq '.loop_contract | {phase: .current_phase, failed: (.failed_checks | length), next: .next_required_output}'
  ./scripts/eduflowteam task evolution-packet "$tid" --json | jq '.candidates | length'
done
```

> 需要先安装 `jq`。如果没有，去掉 `| jq ...` 直接看原始 JSON。

## 每日节奏建议

- **Day 1**: 收集候选任务，填前 3 行，跑 readiness + loop-contract
- **Day 2-3**: 派发 handoff，等 worker/review 闭环
- **Day 4**: 跑 evolution-packet，填 acceptance-log
- **Day 5**: 再看是否需要补 2-3 个任务到 5-10 个
- **Day 6+**: 按 promotion rule 决定 promote / retire / iterate

## Readiness 阈值观测（Package 5 反思 3 的落地）

阈值常量是按 plan 的"simple thresholds"直接选的（5min heartbeat / 30min log
freshness / 5min delivery freshness），没有真实运行数据校准。T-2 实测显示：
worker_course 14.5 分钟无 heartbeat 会被判 `productivity=fail`，但这可能
只是正常思考间隔。

**观测机制**：新增 `task readiness-check <T-id> --diagnostics` 标志，
输出原始信号值（heartbeat_age_ms、log age、handoff 状态等），供 manager
记录真实分布。

```bash
./scripts/eduflowteam task readiness-check T-2 --json --diagnostics
```

返回 `readiness_diagnostics` 字段，含 `thresholds` + `delivery_signals` +
`productivity_signals` + `source_signals` 四个区块。

### 阈值观测表（manager 每天填一次）

> 每天挑 2-3 个 active task 跑 `readiness-check --diagnostics`，记录下表。
> 一周后回看，如果 `productivity=warn` 的任务里 `heartbeat_age_ms < 30min`
> 占比 > 50%，说明 5min 阈值偏紧。

| 日期 | task_id | heartbeat_age_ms | most_recent_log_age_ms | handoff_count | 实际健康？ | 建议阈值 |
|------|---------|------------------|----------------------|----------------|-----------|----------|
| 2026-07-07 | T-2 | 872751 (~14.5min) | 872946 (~14.5min) | 0 | ? | ? |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |

### 阈值调整原则

- 调大前必须先收集至少 10 个真实样本
- 调整必须改 `src/eduflow/store/operational_readiness.py` 顶部常量
- 调整后重跑 `pytest tests/unit/test_operational_readiness.py` 确认阈值变化
  没有破坏现有测试

## 停止条件

出现以下任一情况，暂停 pilot：

1. 连续 2 个任务 `readiness.overall == fail` 且无法解决
2. `task evolution-packet` 产生了明显错误的候选（如 clean task 也触发）
3. worker_course 反馈 contract 消息反而让它更困惑（`worker_less_off_track=False` 连续出现）
4. 需要启动 Package 8（flow-memory 写入）—— 未授权前禁止

## 填完 acceptance-log 后

统计每列 `True` 数量，对照 promotion rule：

| 维度 | 晋升阈值 |
|------|---------|
| manager_faster | ≥ 7/10 |
| worker_less_off_track | ≥ 6/10 |
| review_more_specific | ≥ 6/10 |
| closeout_easier | ≥ 5/10 |

然后 manager 团队一起决定：promote / retire / iterate。

## 需要我（Claude）下一步做什么？

请在下面选一项：

- [ ] A. 我已经有候选 task id，帮我批量跑 readiness + loop-contract + evolution-packet（只读）
- [ ] B. 帮我写一个 `pilot-preflight.sh` 脚本文件放到 pilot 目录
- [ ] C. 先帮我检查当前真实 task 列表，找出符合标准的候选任务
- [ ] D. 其他：__________
