# runtime-failover-hardening

Runtime 容灾机制升级：把"写 runtime-status + respawn ready"升级为 detect failure → select cross-pool backup → hard-switch → live env verify → API smoke → inbox recovery verify → mark proved_ready 的完整闭环。

- workflow_id: `runtime-failover-hardening`
- status: `active`
- owner: `worker_builder`

## Primary Chain

```text
manager -> worker_builder -> auto_ops -> review_course -> manager
```

manager 是 workflow caller 与正式决策 owner；worker_builder 实施改造；auto_ops 跑端到端 smoke；review_course 复核字段口径与边界。

## Core Gates

- `runtime_reality`
- `repair_acceptance_contract`
- `file_evidence_gate`
- `stale_state_reconciliation`

## Acceptance Gates

- `runtime_reality`: runtime verify 必须真实反映 live tmux env，不能只读 stale runtime-status。
- `repair_acceptance_contract`: 切换后必须由 env verify + API smoke + inbox recovery 三项共同证明 proved_ready，不能只看 ready marker。
- `file_evidence_gate`: 17 条 gap case 映射到代码路径必须留下文件级证据（含 `scripts/`、`runtime/`、`commands/health.py` 等修改点）。
- `stale_state_reconciliation`: 健康检查显示 `import path matches EDUFLOW_ROOT`，避免 `/opt/homebrew/bin/eduflow` 命中旧包导致本项目修改不生效。

## 触发条件

昨晚（2026-06-20 夜到 2026-06-21 早）生产暴露 5 个容灾断点 + 1 个阻塞性前提问题：

1. runtime-status 与 live tmux env 漂移（gap-65, gap-127）
2. 429 / Qoder code=112 / usage allocated quota exceeded 出现后不切换（gap-60, gap-96）
3. 切到同额度池的 fallback 继续 429（gap-123）
4. ready ≠ recovered，restart_with_runtime 只看 ready marker，不验 env / smoke / inbox（gap-63, gap-121）
5. 切换后最新高优 inbox 没有被消费（gap-121, gap-124）
6. 全局 `/opt/homebrew/bin/eduflow` 吃到旧 EduFlow 包，本项目修改不生效（gap-98, gap-120）

## 阶段

1. **design** ✅ — Explore 阶段完成（Workflow `wf_fc38f7ff-377`），两个 Explore subagent 产出 code-sweep + gap-sweep，主 agent 综合成最终计划。
2. **implement** ✅ — 14 步实施完成：
   - [x] Step 1: `scripts/eduflow-team-env.sh` 加 PYTHONPATH，健康 自检
   - [x] Step 2: `runtime/verify.py` 新共享模块（15 个测试）
   - [x] Step 3: `runtime/failover.py` 新共享模块（8 个测试）
   - [x] Step 4: `eduflow.toml` env_profiles 加 pool_id / provider_family
   - [x] Step 5: `runtime/config.py` `fallback_runtime` 跨池优先
   - [x] Step 6: `runtime/lifecycle.py` `restart_with_runtime` proved-ready gate（4 个新测试）
   - [x] Step 7: `commands/watchdog.py` 改 `_guard_agent_runtimes` 走 `execute_fallback_loop`
   - [x] Step 8: `feishu/deliver.py` 改 `_inject_to_pane` 走 `execute_fallback_loop`
   - [x] Step 9: `commands/runtime.py` + `runtime_switch.py` + `runtime_verify.py` + `runtime_events.py` 新 CLI（11 个测试）
   - [x] Step 10: `commands/health.py` 加 runtime operational readiness 区块 + import-path 自检
3. **smoke** ⏳ — 端到端 smoke 4 步（见 checklist）
4. **regression** ✅ — `python3 tests/run.py` 1395 passed (1 pre-existing lazy-pane 失败与本任务无关)
5. **closeout** ⏳ — 登记 workflow + 任务台账，manager 验收

## 证据

- smoke: `eduflowteam health` 显示 `import path matches EDUFLOW_ROOT` ✅
- smoke: `eduflowteam runtime verify manager` 正确显示 `env_drift` (ANTHROPIC_BASE_URL expected=deepseek live=fast.sbbbbbbbbb.xyz) — 抓到 gap-127 ✅
- smoke: `eduflowteam runtime events --last 5` 显示 manager 切换历史 ✅
- smoke: health readiness 区块区分 proved_ready / env_drift，critical agent 错误标红 ✅
- tests: 1395 passed, 1 pre-existing fail ✅

## 任务台账

- T-19: runtime failover hardening — 完成实现 → worker_builder
- T-20: runtime failover hardening — 复核行为文案与状态口径 → review_course
- T-21: runtime failover hardening — 端到端 smoke 验证 → auto_ops
- T-22: runtime failover hardening — 验收与复盘 → manager

## Forbidden Moves

- 不允许只回写 `runtime-status.json` 的 `ready=true` 而不跑 env verify / API smoke / inbox recovery。
- 不允许把"同额度池 fallback"误标为跨池切换（必须 cross_pool=true 才算 proved_ready）。
- 不允许在 429 / Qoder code=112 出现后继续轮询同一个 pool。
- 不允许用全局 `/opt/homebrew/bin/eduflow` 跑本项目代码，必须走本项目 `scripts/eduflowteam` 或 `eduflow-team-env.sh`。
- 不允许 review_course 用"差不多可以"作为 verifier 字段口径。
- 不允许 auto_ops 越过 watcher 角色主导流程收口。

## Reassurance Boundary

- worker_builder 只报告实施进度与单元测试结果，不抢 manager 正式验收结论。
- review_course 只复核字段口径与边界是否成立，不直接宣告"全部修复完成"。
- auto_ops 只汇报 smoke 步骤证据，不替代 manager 做最终 closeout。
- manager 是 workflow caller 和正式决策 owner，closeout 时必须显式声明 proved_ready 与剩余 follow-up。
