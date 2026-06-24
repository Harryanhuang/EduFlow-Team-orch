# Handoff

## 给 review_course 的交接
复核范围：
1. `eduflowteam runtime verify <agent>` 输出格式 — 每个字段是否符合 proved_ready/ready_unproven/env_drift/smoke_failed/inbox_not_consumed/pane_missing 口径
2. `eduflowteam health` runtime operational readiness 区块 — 是否正确区分 critical agents (manager/review_course/worker_course/worker_builder/worker_qbank) vs non-critical (auto_ops/anna)
3. `eduflowteam runtime events --json` 输出 — 是否包含 ts/agent/from_runtime/to_runtime/reason/outcome/trigger/cross_pool/env_ok/smoke_ok 字段
4. 不通过要给出具体返修条目，不要只说"差不多可以"

## 给 manager 的交接
验收范围：
1. 任务 T-19/T-20/T-21/T-22 是否都在台账上
2. workflow runtime-failover-hardening 是否在 docs/workflows/ 下登记
3. 17 条验收案例是否每条都有对应代码路径
4. 测试 1395 passed, 1 pre-existing fail — pre-existing fail 是否与本任务无关
5. smoke 4 步是否都跑过（第 4 步模拟 429 需等下次故障）

## 给 auto_ops 的交接
验证范围：
1. 跑 `eduflowteam health` 看 import-path 自检
2. 跑 `eduflowteam runtime verify manager` 看 env_drift
3. 跑 `eduflowteam runtime events --last 5` 看切换历史
4. 等下次 runtime 故障时观察 watchdog 是否跨池切换（不再同池循环）
5. 把证据回填到 docs/workflows/runtime-failover-hardening/README.md 证据段
