# Residency Sleep — Operator Regression Playbook

> 配套方案: 留学公司知识库/11-Eduflow Team 多智能体项目/2026-07-01 EduFlow 群聊外显与温备驻留方案 v0.1 §设计二
> 实现: `src/eduflow/commands/sleep_idle.py` + `src/eduflow/store/agent_residency.py`
> 验收覆盖: `tests/unit/test_residency_sleep.py` (27 tests)

This is the **riskiest phase** of the rollout.  Plan §设计二
mandates dry-run first, then enable real sleeps after one full dry
cycle.  This playbook walks that path.

## Pre-conditions

- Phase 1 + Phase 2 deployed (`cards_v2.py` + `residency.py` + `team` 面板列)
- 9-agent 团队已起过 (`eduflow up` 完成)
- `eduflow.toml` 已有 `[team.residency]` 块
- 一台真机或 sandbox 跑,不要直接在生产主群做 apply

## Step 1 — 纯 dry-run 看决策矩阵

```bash
# 不接 --apply,默认 dry-run:只打印 decision,不发送任何 Ctrl-C
eduflow residency-sleep
```

**预期:** 9 行,每行格式
`[dry-run] agent_name  mode=resident|warm  decision=<reason>  idle=Ns  since_handoff=Ns`

预期 decision 分布:
- manager / auto_ops / Luke_recorder → `keep_resident`
- worker_course / review_course / worker_builder / worker_qbank / Hermes → `keep_under_idle_timeout`(刚启动,idle 不到 600s)或 `would_sleep`(已超过 600s)
- worker_syllabus → idle 阈值 300s,可能更早 would_sleep

## Step 2 — 排除 active task / unread inbox 干扰

```bash
# 让 worker_course 处于 active task 状态
eduflow status worker_course 进行中 "audit"
# 再扫一次,应该 keep_active_task
eduflow residency-sleep --agent worker_course
```

**预期:** `decision=keep_active_task`;`applied=false`;`/` 面板上 worker_course 仍显示 `进行中` 而非 `温备`。

```bash
# 给 worker_course 发一条高优未读消息
eduflow send worker_course manager "请继续 0580 Batch 2" 高
eduflow residency-sleep --agent worker_course
```

**预期:** `decision=keep_unread_inbox`。

## Step 3 — 真实 sleep(单 agent,apply)

```bash
# 选一个 warm 但 idle 时间确实够长的 worker
eduflow residency-sleep --apply --agent worker_qbank
```

**预期:**
- 该 worker 的 tmux pane 收到 Ctrl-C,CLI 退出回到 shell
- local_facts 里该 worker 状态变为 `温备`
- `agent_residency.json` 里该 worker 有 `last_sleep_at` 时间戳
- **`/` 面板里 `温备` 状态可见**(residency 列显示 `温备`,status 列显示 `温备`)

```bash
# 立即查 /team
eduflow team
```

**预期:** worker_qbank 行 `温备  温备  ...`(residency 列 + status 列都显示温备)。

## Step 4 — 后续 wake(Phase 4 自动化,Phase 3 仅人工验证)

```bash
# 给温备状态的 worker_qbank 发消息
eduflow send worker_qbank manager "Batch 7 验证" 高
# 预期: lazy wake 路径触发,CLI 重新 spawn
# 这是 send.py 现成的 lazy wake 逻辑(Phase 1 已有),Phase 3 不用动
```

**预期:** worker_qbank 的 pane 重新 spawn CLI,5-30s 后 ready,`last_wake_at` 被 stamp,`/` 面板从 `温备` 回到 `进行中`。

## Step 5 — 整体 sweep(全 team apply)

```bash
# 全队 sweep,真实生效
eduflow residency-sleep --apply
```

**预期:**
- 所有 warm 且 idle 超时的 agent 进入 `温备`
- resident agent(manager/auto_ops/Luke_recorder)永远不 sleep
- 实际只有 worker_syllabus / worker_qbank 等"长时间不接活"的会真 sleep
- 任何 active task / unread inbox / cooldown 的 agent 不被 sleep

## Step 6 — 接入周期 sweep(可选,Phase 3 末)

当前没有自动周期调用 `sweep()`(plan §设计二 说"auto_ops / runtime_guard 周期检查"是 Phase 3 触发点之一)。**v1 推荐先手动跑** + 用 `cron` / `launchd` 兜底:

```bash
# /etc/cron.d/eduflow-residency (示例,谨慎启用)
*/5 * * * *  /path/to/eduflow residency-sleep --apply
```

**注意:**
- 第一次部署先以 dry-run 跑 1-2 天,人工核对决策合理后再加 `--apply`
- 任何 sleep 决策出现"明明在跑却被 sleep",先 `eduflow status <agent>` 查 status,然后关掉 cron 排查

## 通过条件

- Step 1: dry-run 决策矩阵与预期完全一致
- Step 2: active task / unread inbox 100% 不被 sleep
- Step 3: 单 agent apply 后,该 agent 状态变 `温备`,pane 保留,Ctrl-C 有效
- Step 4: 给温备 agent 发消息能正确 wake 回来
- Step 5: 整队 sweep 不会误关 active 状态的 agent
- Step 6: 真实环境跑 1-2 天无异常,老板主观确认主群噪音下降

任何一条不通过,优先 `eduflow residency-sleep --json` 看决策原因,
不要急着改 sleep_idle.py / agent_residency.py 重新上线。

## 未覆盖风险(从 Phase 0 审计继承)

1. **Runtime 切换期间拒绝 sleep**:`in_cooldown` 信号来自
   `runtime-guard-state.json`,若该文件不存在或 stale,cooldown 防御失效。
   已写测试 `test_warm_during_cooldown_keeps_running` 覆盖决策逻辑。
2. **跨 session 状态**:`agent_residency.json` 走 `runtime/paths.facts_dir()`,
   按 `EDUFLOW_STATE_DIR` 重读,跨 session 隔离(已验证)。
3. **`last_active_at` 时钟源**:`touch_active` 必须由所有"保持 agent 醒着"
   的路径调用。Phase 4 会接入 `send.py` / `read --ack` / `task_publish`
   三个点。**v1 缺这些 stamp,idle_age_s 永远是 inf,不会 sleep。**
   这是 Phase 3 与 Phase 4 的依赖边界,跑前需要先在 send.py 加 stamp。
4. **Pane 不存在时 `tmux.has_window=False`**:Step 3 测试中跳过 Ctrl-C,
   但 `温备` 状态仍 stamp(测试用例 `test_residency_sleep_cli_apply_flag_does_real_work`)。
   真实环境若 `eduflow up` 之前 sweep,会导致状态写但 pane 没退。

## 关联文件

- 方案: `2026-07-01 EduFlow 群聊外显与温备驻留方案 v0.1.md` §设计二
- 审计: `docs/plans/2026-07-01-phase0-residency-audit.md`
- sleep 决策: `src/eduflow/runtime/residency.py` (`sleep_decision` / `should_sleep`)
- sleep 实现: `src/eduflow/commands/sleep_idle.py` (`sleep_if_idle` / `sweep` / `main`)
- 持久化: `src/eduflow/store/agent_residency.py`
- 单元测试: `tests/unit/test_residency_sleep.py` (27 tests)
