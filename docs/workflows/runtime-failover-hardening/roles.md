# Roles

## worker_builder
唯一实现执行位。负责 14 步实施：import drift / 新模块 (verify, failover, runtime CLI) / 核心逻辑改造 (fallback_runtime cross-pool, lifecycle proved-ready) / watchdog+deliver 走 failover loop / health 区块扩展。每个改动带对应单元测试。

## auto_ops
验收案例汇总 + 端到端 smoke 验证。负责：(1) 从 gap note 提炼 GIVEN/WHEN/THEN 表（17 条）(2) 跑 4 步手动 smoke (3) 确认 runtime-switch-events.jsonl 字段完整 (4) 把验收证据回填到 README 证据段。

## review_course
只读复核。负责：(1) runtime verify 输出文案是否符合 proved_ready/ready_unproven/env_drift/smoke_failed/inbox_not_consumed/pane_missing 口径 (2) health readiness 区块是否正确区分 critical vs non-critical (3) runtime events 输出是否包含 trigger/cross_pool/env_ok/smoke_ok 字段 (4) 不通过要给出具体返修条目。

## manager
验收 + 跟踪。负责：(1) 给 worker_builder 派单 (2) 挂 workflow + 任务台账 (3) 验收 closeout (4) 把 runtime-failover-hardening 升级为生产 workflow 或降级回退。
