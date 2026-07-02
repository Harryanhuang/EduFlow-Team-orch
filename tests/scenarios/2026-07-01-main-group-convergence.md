# 主群体验收敛 — Operator Regression Playbook

> 配套方案: 留学公司知识库/11-Eduflow Team 多智能体项目/2026-07-01 EduFlow 群聊外显与温备驻留方案 v0.1 §设计一/§v1成功标准
> 实现: `commands/residency_wake.py` + `commands/watchdog.py` presence 阶段驱动 + `say.py` reassurance 白名单收敛 + `eduflow.toml [auto_ops]`
> 验收覆盖: `tests/unit/test_residency_convergence.py` (13 tests)

Phase 5 是收官步骤:把主群从"agent 聊天记录"收敛成"老板驾驶舱"。
三件事:auto_ops 停止定时刷屏、低价值 reassurance 降级、加手动预热命令。

## Pre-conditions

- Phase 1-4 全部部署
- `eduflow.toml` `[auto_ops]` 已改成 `presence_enabled=false` + `stage_driven=true`
- 9-agent 团队已起

## Step 1 — auto_ops 不再定时刷屏

```bash
# 确认配置
python3 - <<'PY'
import sys; sys.path.insert(0, 'src')
from eduflow.runtime import tunables
ao = tunables.load().get('auto_ops', {})
print('presence_enabled:', ao.get('presence_enabled'))   # False
print('stage_driven:', ao.get('stage_driven'))            # True
print('fallback_after_s:', ao.get('presence_fallback_after_s'))  # 7200
PY
```

**预期:** `presence_enabled=False`,`stage_driven=True`,`fallback=7200`

实际观察(真机跑一段时间):
- 主群不再每 30 分钟出现"运行态简报:...盯盘中,暂无新异常"
- auto_ops 只在发现异常时发 `[ALERT]` 卡
- 超过 2 小时完全静默时,才补一条"在岗"兜底

## Step 2 — 低价值 reassurance 被降级

```bash
# 这些消息现在会被 silence(worker_to_user=false 时)
eduflow say auto_ops "运行态简报：全链路正常" --to user
# 预期: 📝 auto_ops → silenced by [chat.publish.worker_to_user]=false; logged only

eduflow say worker_course "暂无新结果：还在跑" --to user
# 预期: silenced

# 这些真阶段变化仍进主群
eduflow say worker_course "任务已接单：Physics 0625" --to user
# 预期: → main chat

eduflow say auto_ops "发现异常：worker_course 外显陈旧，已回报 manager" --to user
# 预期: → main chat
```

**被降级的 marker(Phase 5 移除)**:暂无新结果 / 处理中但卡在 / 盯盘中 / 盯盘正常 / 巡检正常 / 运行态简报
**保留的 marker**:接单 / 开工 / 交接 / 卡点 / verdict / 发现异常 / 完成交接

## Step 3 — 手动预热温备 agent

```bash
# 场景: manager 知道马上要给 worker_qbank 派一批活,先预热
eduflow residency-wake worker_qbank
# 预期(agent 温备中): ✅ worker_qbank pre-heated (CLI woken)
# 预期(agent 已在线): ✅ worker_qbank already ready (clock reset)
# 预期(无 pane): ❌ worker_qbank has no pane; run eduflow hire ... (ALERT fired)

# JSON 输出
eduflow residency-wake worker_qbank --json
# {"agent":"worker_qbank","woke":true,"already_ready":false,"no_pane":false,"errno":""}
```

**预期:** 预热后 `agent_residency.json` 的 `last_wake_at` 被刷新,下次 sweep 不会立即 sleep 它。

## Step 4 — 老板 30 秒判断(§v1 成功标准)

真机跑一轮真实任务(course 生产 → review → qbank 校验 → builder 修复 → Luke_recorder 记录),然后老板打开主群:

**通过标准(方案 §v1 成功标准 逐条)**:
1. ✅ 主群消息统一为固定卡片类型([ACK]/[START]/[PROGRESS]/[HANDOFF]/[BLOCKED]/[REVIEW]/[CLOSEOUT]/[ALERT]/[RECORDED])
2. ✅ worker 阶段陪跑稳定,低价值消息明显减少(Step 2)
3. ✅ manager 是唯一正式 closeout(Phase 1 validator 强制)
4. ✅ manager/auto_ops/Luke_recorder 常驻(Phase 2 `/team` 显示常驻)
5. ✅ 6 个 worker 温备(Phase 2 `/team` 显示温备)
6. ✅ 温备 agent 无任务时自动退 CLI 保 pane(Phase 3 `residency-sleep --apply`)
7. ✅ 温备 agent 下次任务自动唤醒(Phase 4 send lazy wake / Phase 5 手动预热)
8. ✅ 不误关 active/unread/fallback 中的 agent(Phase 3 决策矩阵 7 guard)

**老板 30 秒扫群检查**:
- 全部卡片都是 `[TYPE] {agent} · {role}` 格式
- 没有 worker 直接宣布"正式成功"(只有 manager `[CLOSEOUT]`)
- 没有一屏"盯盘中/暂无新异常"噪音
- `/team` 面板一眼看清谁常驻谁温备谁进行中

## 通过条件

- Step 1: auto_ops presence 配置正确,真机无定时刷屏
- Step 2: 低价值 6 marker 被 silence,阶段变化 marker 仍进群
- Step 3: `residency-wake` 三种路径(温备唤醒/已在线/无pane)都正确
- Step 4: 老板 30 秒判断通过,§v1 8 条成功标准全绿

## 未覆盖风险

1. **真实任务端到端未在生产群跑**: 全部为单测 + 干跑验证。§v1 成功标准第 1-8 条的真机确认需要老板在真实飞书群观察 1-2 天。
2. **presence baseline 首启**: `_maybe_emit_auto_ops_presence` 首次调用(无历史 surface)会写 baseline 并跳过,从此刻开始计 2h 静默钟。首启当天不会有兜底"在岗"信号,属预期。
3. **手动预热并发**: `residency-wake` 串行执行,同时预热多个 agent 需多次调用;未做批量。

## 关联文件

- 预热命令: `src/eduflow/commands/residency_wake.py` (`eduflow residency-wake`)
- presence 阶段驱动: `src/eduflow/commands/watchdog.py` (`_maybe_emit_auto_ops_presence`)
- reassurance 收敛: `src/eduflow/commands/say.py` (`_worker_reason_override`)
- 配置: `eduflow.toml` `[auto_ops]` (presence_enabled=false / stage_driven=true) + auto_ops notes
- 单元测试: `tests/unit/test_residency_convergence.py` (13 tests)

## 全阶段回归命令

```bash
python3 -m pytest \
  tests/unit/test_cards_v2.py \
  tests/unit/test_residency.py \
  tests/unit/test_residency_sleep.py \
  tests/unit/test_residency_wake.py \
  tests/unit/test_residency_convergence.py \
  tests/unit/test_commands_say.py \
  tests/unit/test_commands_messaging.py \
  tests/unit/test_commands_task.py \
  tests/unit/test_commands_team_workspace.py \
  tests/unit/test_commands_watchdog.py \
  tests/unit/test_runtime_config.py \
  tests/unit/test_local_facts.py \
  --no-header -q
```
