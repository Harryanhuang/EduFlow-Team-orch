# Checklist

## Design
- [x] Explore 阶段完成（code-sweep + gap-sweep）
- [x] 计划文档写入 `/Users/huanganan/.claude/plans/joyful-gliding-moler.md`
- [x] 用户 ExitPlanMode 批准

## Implement
- [x] Step 1: import drift 修复 (env.sh + .venv warning + health 自检)
- [x] Step 2: runtime/verify.py + 15 个测试
- [x] Step 3: runtime/failover.py + 8 个测试
- [x] Step 4: eduflow.toml env_profiles 加 pool_id / provider_family
- [x] Step 5: config.fallback_runtime 跨池优先
- [x] Step 6: lifecycle.restart_with_runtime proved-ready gate + 4 个新测试
- [x] Step 7: watchdog._guard_agent_runtimes 走 execute_fallback_loop
- [x] Step 8: deliver._inject_to_pane 走 execute_fallback_loop
- [x] Step 9: runtime CLI (switch + verify + events) + 11 个测试
- [x] Step 10: health runtime operational readiness 区块 + import-path 自检

## Smoke
- [x] health 显示 `eduflow import path matches EDUFLOW_ROOT`
- [x] `eduflowteam runtime verify manager` 正确显示 `env_drift`（gap-127）
- [x] `eduflowteam runtime events --last 5` 显示切换历史
- [ ] 模拟 429 自动跨池切换（需在下次 runtime 故障时观察）
- [ ] fallback 选择不再同池循环（需在下次 runtime 故障时观察）

## Regression
- [x] `python3 tests/run.py` 1395 passed (1 pre-existing lazy-pane 失败与本任务无关)
- [x] health/up/hire/send 不因新增字段失败
- [x] lazy agent Anna 显示 `env_drift` 而不是 hard failure

## Closeout
- [x] 登记 runtime-failover-hardening workflow (docs/workflows/...)
- [x] 登记任务台账 (T-19/T-20/T-21/T-22)
- [ ] manager 验收
- [ ] 复盘文档

## 验收案例覆盖 (17 条)
gap-60 ✅ gap-63 ✅ gap-65 ✅ gap-66 ✅ gap-67 (部分,pane-missing 走 health 区块) gap-71 ✅ gap-86 (manager 派工逻辑,本任务不直接覆盖) gap-96 ✅ gap-98 ✅ gap-119 ✅ gap-120 ✅ gap-121 ✅ gap-123 ✅ gap-124 ✅ gap-125 (health 区块 + tmux 自检) gap-126 ✅ gap-127 ✅
