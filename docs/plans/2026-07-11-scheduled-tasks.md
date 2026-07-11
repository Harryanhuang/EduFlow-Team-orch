# 定时任务（D 编号）分包执行方案

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标：** 支持单次、每日、每周定时业务规则。每轮到期都先进入 manager 确认队列，再由 manager 编排一个或多个 agent。对外规则和执行均使用 `D-<序号>`；既有非定时业务继续使用 `T-<序号>`。

**架构决定：** D 是独立 scheduler domain：rule、occurrence、lane、notification ledger、heartbeat 分开持久化并加锁。现有 `tasks.py` 的 T 计数和 flow 状态机不承担 D 轮次。task-publish 仅调用异常隔离的 scheduler tick。workflow 是经 manager 确认后可复用的 lane 编排快照，不是自动派发引擎。memory 仅存上下文摘要，不能驱动调度。

## 所有分包共同规则

- 开始前阅读 `AGENTS.md`、本文件、目标模块和相邻测试；保留工作区无关改动。
- 先写失败测试，再写最小实现；不加依赖、不改 runtime registry、不 reset/merge/force push。
- D 不得改变 T 编号、T 状态机，或产生 user-visible T。若派发基础设施无法承载 D，停止并报告最小适配接口。
- 每次状态先落盘、后通知/派发；派发前重读 active 状态和版本，取消优先。
- 每包跑 focused pytest、相关回归、`git diff --check`；仅 stage 本包文件，按 Lore Commit Protocol 单独提交。
- 最终报告改动文件、API/状态语义、测试、兼容性风险、commit SHA。

## 执行顺序

`P0 契约 → P1 Store → P2 Recurrence → P3 Engine → P4 Manager Ops → P5 Router/Skill → P6 Panel/Health → P7 Memory → P8 Workflow → P9 E2E`。

P6 在 P5 后做；P7/P8 可以提前阅读但不得在 P4 前写代码；P9 只能最后执行。

---

## P0：现状映射与不可回归契约

**范围：** 阅读 `store/tasks.py`、`commands/task.py`、`commands/task_publish.py`、`runtime/paths.py`、`store/task_event_scanner.py`；新增 `tests/unit/test_scheduled_task_contract.py`。不实现 scheduler。

**交付：** 用真实 fixture 锁定 T 创建/编号、普通 publish cursor、manager-panel 入口及 JSON/lock 模式。测试证明普通任务仍生成 T，scheduler import 不改变 T 序列，普通 publish cursor 不可供 scheduler 使用。

**验收：**

```bash
python3 -m pytest tests/unit/test_scheduled_task_contract.py tests/unit/test_store_tasks.py tests/unit/test_commands_task_publish.py -q
git diff --check
```

**给 Claude 的提示词：**

```text
执行 P0，仅建立 D 定时任务的不可回归契约。先读 AGENTS.md、本计划和指定模块。
只新增 tests/unit/test_scheduled_task_contract.py；不要实现 scheduler、修改 tasks.py、
eduflow.toml 或任何无关改动。用真实 fixture 证明 T-ID、T 状态机和普通 publish cursor
与未来 D 域隔离。运行验收；只 stage 本包文件，按 Lore Protocol 提交。报告真实入口、
测试和 SHA。
```

## P1：独立 D rule/occurrence 持久化

**范围：** 新增 `src/eduflow/store/scheduled_tasks.py`、`tests/unit/test_scheduled_task_store.py`；只在 `runtime/paths.py` 增加 scheduler 路径。

**交付：** 独立 D 序号 metadata；rule 保存 version、目标、产物、频率、时区、next due、状态、容量、workflow 状态；occurrence 幂等键固定为 `D-ID:scheduled_at_utc`；另存 lane、通知账本和 heartbeat。复用现有 JSON/lock，所有变更 CAS/version 保护，取消保留审计历史。

**验收：**

```bash
python3 -m pytest tests/unit/test_scheduled_task_contract.py tests/unit/test_scheduled_task_store.py -q
git diff --check
```

**给 Claude 的提示词：**

```text
执行 P1，创建独立 scheduler store。只允许 scheduled_tasks.py、对应测试和
runtime/paths.py 专用路径。D-ID 不能读写 tasks.py metadata；D occurrence 以 D-ID+UTC
时间幂等；rule 写入必须 CAS/version 检查。覆盖独立序号、重复调用、UTC、版本冲突、
非法转移和取消保留历史。先失败后最小实现；禁止把 D 写进 tasks.json。跑验收，Lore
提交，报告 API、状态和 SHA。
```

## P2：recurrence 与时间语义

**范围：** 新增 `src/eduflow/scheduling/recurrence.py`、`tests/unit/test_scheduled_recurrence.py`；不接 router 或派发。

**交付：** 仅 once/daily/weekly；输入/展示 `Asia/Shanghai`，持久化 UTC；函数接受显式 `now`。past once、未知时区、weekly 缺星期/时刻、cron/monthly/间隔表达返回结构化错误，交由 manager 追问。

**验收：**

```bash
python3 -m pytest tests/unit/test_scheduled_recurrence.py -q
git diff --check
```

**给 Claude 的提示词：**

```text
执行 P2，只实现 recurrence 内核。支持 once/daily/weekly、Asia/Shanghai 展示、UTC 存储，
并显式传入 now。拒绝 cron、monthly、interval 和模糊自然语言；不要接 router、创建
occurrence 或通知。覆盖跨日、每周、过去时间和非法频率/时区。跑验收，Lore 提交，
报告函数 API 和错误契约。
```

## P3：scheduler tick、恢复与背压

**范围：** 新增 `src/eduflow/scheduling/engine.py`、`tests/unit/test_scheduled_engine.py`、`tests/unit/test_commands_task_publish_scheduled.py`；修改 `commands/task_publish.py`。

**交付：** `tick(now)` 只检测到期并创建 `awaiting_manager` occurrence，绝不派发。使用独立 heartbeat/错误边界，不复用普通 cursor。reconcile 处理重启中间态、漏通知和错过到点；未知派发不可猜测完成。未确认跨周期 skip；运行中跨周期 `blocked_by_previous_run`，默认不并行；阈值转 `attention_required`。

**验收：**

```bash
python3 -m pytest tests/unit/test_scheduled_engine.py tests/unit/test_commands_task_publish_scheduled.py tests/unit/test_commands_task_publish.py -q
git diff --check
```

**给 Claude 的提示词：**

```text
执行 P3，接入可靠且隔离的 scheduler tick。tick 只能推进到 awaiting_manager，状态先写
再返回通知动作。task-publish 用独立 try/except 调 scheduler；scheduler 出错时普通 T
publish 必须照常运行。测试重复 tick、重启、错过到点、通知重放、跨周期 skip、运行重叠
blocked 和容量 attention_required。派发尚未实现，不能提前派发。跑验收，Lore 提交，
报告恢复策略和 SHA。
```

## P4：manager 操作、授权与多 agent lane

**范围：** 新增 `src/eduflow/scheduling/manager_ops.py`、`tests/unit/test_scheduled_manager_ops.py`；在 `commands/task.py` 增加最小 `task schedule ...` 入口。

**交付：** user 可确认草稿、暂停、恢复、取消；manager 可确认 occurrence、选择 lane、跳过、重派、失败暂停；worker 只能回报。lane 记录 agent、依赖、输入、产物、证据，支持串并行。确认绑定 rule version/occurrence key；派发前重读 active，取消获胜。D lane 不产生 user-visible T。

**验收：**

```bash
python3 -m pytest tests/unit/test_scheduled_manager_ops.py tests/unit/test_commands_task.py -q
git diff --check
```

**给 Claude 的提示词：**

```text
执行 P4，建立确定性的 manager/user scheduler 操作与 D lane。不要改变旧 task dispatch
的 T 语义。写操作必须走明确 CLI/API；自然语言不能直接改 store。测试权限、旧确认、
取消/派发竞态、skip/cancel 用户决定和多 lane 依赖。若执行基础设施只能接受 T，停止并
报告最小 D adapter，不允许隐式创建 T。跑验收，Lore 提交，报告授权矩阵/API/SHA。
```

## P5：manager skill、router 草稿与通知

**范围：** 新增 `skills/eduflow-scheduled-task-manager/SKILL.md`、`tests/unit/test_scheduled_router.py`、`tests/unit/test_scheduled_notifications.py`；修改 `feishu/router.py` 与必要会话状态入口。

**交付：** 自然语言先形成结构化草稿：目标、产物、频率/时间、时区、建议 agent。模糊时间必须追问。user 确认后才调 P4。暂停/恢复/取消回显 D ID 与动作。仅通知创建、补充/确认、开始、结果/失败；单次每 30 分钟提醒 manager、2 小时通知 user。

**验收：**

```bash
python3 -m pytest tests/unit/test_scheduled_router.py tests/unit/test_scheduled_notifications.py -q
git diff --check
```

**给 Claude 的提示词：**

```text
执行 P5，router 只将 user 语言送往 manager skill；不得猜时间或直接写 scheduler store。
创建 manager skill，写明必填字段、追问、到期确认包、权限和通知节奏。下周/周末/下午/
每隔一段时间必须追问。实现“自然语言→草稿→版本绑定 user 确认→P4 API”；暂停恢复取消
需回显确认。禁止 tick/wait 刷屏。跑验收，Lore 提交，报告会话状态、去重和 SHA。
```

## P6：manager panel、health 与队列收敛

**范围：** 修改 `commands/task.py` manager-panel 与 `commands/health.py`；新增 `tests/unit/test_scheduled_manager_panel.py`、`tests/unit/test_scheduled_health.py`。

**交付：** panel 只读显示 due soon、awaiting manager/user、running、blocked、recent failure、scheduler lag、attention required；每项有 D ID、时间、原因和下一步。health 显示 heartbeat、last success、lag、pending/running、连续 skip/failure。积压/最长等待由 P3 状态收敛，UI 不造状态。

**验收：**

```bash
python3 -m pytest tests/unit/test_scheduled_manager_panel.py tests/unit/test_scheduled_health.py tests/unit/test_commands_health.py -q
git diff --check
```

**给 Claude 的提示词：**

```text
执行 P6，仅增加 D scheduler 的只读可观测性。复用现有 manager-panel/health 风格，不能
让 panel 绕过 manager_ops 写状态。展示到期、两类待确认、运行、blocked、失败、lag、
attention_required，以及 heartbeat/计数。每条带原因和 action hint。测试真实 store 到
输出映射和既有 health 回归；跑验收、Lore 提交，报告字段契约/SHA。
```

## P7：memory 摘要与历史归档

**范围：** 修改 `memory/capsules.py`、`memory/packet.py`，在 scheduler store/engine 添加归档查询；新增 `tests/unit/test_scheduled_memory.py`、`tests/unit/test_scheduled_retention.py`。

**交付：** D 可关联 capsule/packet，但仅写规则摘要、workflow 启停、重大失败、明确 user 偏好；普通 tick/reminder/wait 不写 memory。memory 失败不能阻止 scheduler。默认 90 天完整 occurrence/lane/通知审计，之后只保留摘要+证据引用；配置化、dry-run，不归档 active/unfinished 引用。

**验收：**

```bash
python3 -m pytest tests/unit/test_scheduled_memory.py tests/unit/test_scheduled_retention.py tests/unit/test_memory_packet_focused.py -q
git diff --check
```

**给 Claude 的提示词：**

```text
执行 P7，将 D 接入 memory 和安全归档。scheduler store 是唯一事实来源，memory 不可用时
D 必须继续工作。仅保留有决策价值的 D 摘要，禁止 tick 噪声。实现配置化、dry-run 的
90 天归档，不触碰 active/unfinished 引用，并保持 T memory 行为。先写测试、跑验收，
Lore 提交；报告 capsule 字段、归档保护和 SHA。
```

## P8：探索模式到 workflow 复用与降级

**范围：** 新增 `src/eduflow/scheduling/workflow_evolution.py`、`tests/unit/test_scheduled_workflow_evolution.py`；仅在确认的 workflow registry/command 扩展点集成。

**交付：** 初始 exploration，每轮 manager 记录实际 lane/产物/失败。至少五次稳定完成（目标/产物、关键步骤角色、审计证据稳定且无未解决重复失败）才产出 candidate；写资产交 worker_builder，manager 审核启用。每轮仍 manager 确认并冻结 workflow snapshot。连续两次重大偏离/失败降级 exploration；30 天或 10 次成功标记健康复核。

**验收：**

```bash
python3 -m pytest tests/unit/test_scheduled_workflow_evolution.py tests/unit/test_commands_workflow.py -q
git diff --check
```

**给 Claude 的提示词：**

```text
执行 P8，先读 docs/workflows/README.md 与现有 workflow 命令。尊重 manager 调用、
worker_builder 维护资产的边界。实现 5 次可审计稳定运行后才 candidate；启用后每轮仍须
manager 确认，workflow 不能自动派发。两次重大偏离/失败自动降级并通知 user；加 30 天
或 10 successes 健康复核。不要把 builder 维护 T 当成 D 执行。跑验收，Lore 提交，报告
稳定算法、候选边界、降级与 SHA。
```

## P9：端到端、恢复与发布门禁

**范围：** 新增 `tests/integration/test_scheduled_tasks_e2e.py`；只做直接阻断验收的最小修复；更新最小运维文档。

**场景：** 草稿确认；到期→manager→多 lane→聚合；重复 tick/restart/通知故障不二次派发；cancel wins；跨周期未确认 skip、运行中 blocked；补执行、提醒、capacity；5 stable→workflow、2 deviation→探索；scheduler 异常不影响 T publish、health/watchdog/memory。

**验收：**

```bash
python3 -m pytest tests/integration/test_scheduled_tasks_e2e.py -q
python3 tests/run.py
git diff --check
git status --short
```

**给 Claude 的提示词：**

```text
执行 P9，只做 D scheduler 系统验收、最小缺口修复和最小运维文档。先读 P0-P8 提交。
新增 e2e 覆盖本包场景，尤其幂等、恢复、取消竞态、背压和 workflow 降级。发现问题只修
直接阻断验收的最小范围；不得删测试、放宽断言、skip 或重构无关模块。运行 integration、
python3 tests/run.py、diff check。只 stage 本包文件，Lore 提交；报告门禁、SHA、限制。
```

## 完成门槛

- `python3 tests/run.py` 最后一行必须为 `tests: N passed, 0 failed`。
- D/T 编号、存储、用户可见状态彻底隔离；D 每轮不产生 user-visible T。
- scheduler 故障、重启、重复 tick、通知重试、取消竞态均不重复 dispatch，也不影响普通 publish。
- manager 每轮仍是派发决策者；worker 不可变更规则。
- queue/backpressure、长时间待确认、workflow 漂移均在 panel/health 中可见且可收敛。

## Claude 提示词审阅记录

已按 ask-claude skill 发起本机 Claude 审阅，但 CLI 约两分钟无输出并中止；原始请求与结果记录在 `.omx/artifacts/claude-scheduled-task-plan-review-2026-07-11.md`。本计划未声称已获 Claude 审核；P0 开始前应先恢复 Claude CLI 后重新审阅。
