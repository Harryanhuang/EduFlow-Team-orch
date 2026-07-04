# EduFlow 双层 Loop Engineering 实施方案

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
> **给 Claude：**先阅读“Claude 执行手册”，按 Step 0-12 逐步执行；每一步必须满足对应验收标准后才能进入下一步。

**目标：**把 Loop Engineering 做进 EduFlow，但不是只做“单个 agent 自我修复循环”。EduFlow 要实现的是双层循环：第一层提升单个 agent 的执行效率，第二层让 manager / worker / reviewer / verifier / memory 之间的团队协作变成可观察、可返修、可停止、可沉淀的团队闭环。

**架构：**`flow task` 仍然是唯一任务真相源。第一层是 **Agent Loop**：单个角色通过 deterministic check / role-local check 形成“执行 -> 检查 -> 返修 -> 停止”的循环，并把证据挂回 task。第二层是 **Team Loop**：从 `workflow_id`、task events、review verdict、closeout gate 中推导团队协作阶段、下一责任人、返修轮次和卡点。workflow 文档仍然是协作协议，不变成自动执行引擎；Loop 层只负责让协议实例可观察、可修复、可复盘。

**技术栈：**只用 Python 标准库、现有 `eduflow.store.tasks`、现有 task events、现有 workflow registry、现有 evidence account / closeout gate、现有 memory capsules、JSON/JSONL state files、`pytest`。不新增数据库，不新增依赖。

---

## 中文总览

### 要实现的最终效果

实现后，EduFlow 会从“多 agent 派工 + workflow 协议”升级成“有闭环能力的团队操作系统”：

```text
单个 agent:
接任务 -> 执行 -> 自检/确定性检查 -> 失败返修 -> 通过或停止

整个团队:
manager 派工 -> worker 执行 -> reviewer/checker 审核
-> 失败返修 -> 再审核 -> manager closeout -> memory/workflow 沉淀
```

最终你应该可以用一个命令看懂任务循环状态：

```bash
task loop-status T-123
```

输出同时包含两层状态：

```text
agent_loop:
  loop_status: repair_needed
  cycle_count: 2
  evidence_ref: loop_runs/L-000001/meta.json

team_loop:
  workflow_id: igcse-subject-launch
  phase: team_repair_needed
  next_owner: worker_course
  cycle_count: 1
  recommended_action: send_repair_handoff
```

这意味着 manager 不再只是在“盯人”，而是在“盯循环”：当前在哪一步、下一棒是谁、返修几轮、证据在哪里、是否该停止、是否该沉淀 workflow/memory/skill。

## 目标与差距

| 目标能力 | 当前 EduFlow 状态 | 差距 | 方案补齐方式 |
|---|---|---|---|
| 单个 agent 有执行闭环 | worker 主要靠自报完成，manager 追问 | 缺少结构化检查、返修、停止条件 | 新增 Agent Loop：`task loop-check`、loop evidence archive、stop rules |
| 验收权力边界清楚 | 执行 agent、review agent、manager 都可能说“完成” | 自检、正式验收、最终关闭容易混成一个动作 | 明确三层验收：worker self-check、review agent official review、manager closeout |
| 团队协作有循环状态 | workflow 是静态协作协议，task 有状态 | 缺少“这个 workflow 实例走到哪一拍”的 read model | 新增 `team_loop_account`，从 task events/review/closeout 推导 `phase/next_owner/cycle_count` |
| loop 证据可追踪 | 证据散在聊天、日志、测试输出 | 缺少每轮循环的 evidence ref | 新增 `$EDUFLOW_STATE_DIR/loop_runs/<loop_id>/` 证据目录，task row 只存轻量引用 |
| manager 会主动使用 loop | manager identity 现在不知道 `loop-check` | 功能可能实现但无人调用 | 修改 `eduflow.toml` 的 manager/worker_builder notes，并 `reidentify` |
| 派工和 task id 对齐 | `send` 会通知 worker，但不创建 task；`task dispatch` 创建 task，但不是 worker 指令本身 | loop 需要 `task_id`，ad-hoc send 没有 task id | Phase 0.5 要求 loop-verified builder work 先 `task dispatch` 再 `send` |
| manager 不被长测试卡住 | 同步跑 pytest 可能阻塞 manager pane | manager 是唯一入口，不能被 30 分钟测试占住 | `task loop-check --background` |
| loop 状态进入 manager 主信息面 | publish gate 有，但 render 层不显示 loop | manager 在卡片/面板里看不到 loop 摘要 | Task 7 接入 `task_publish_render.py` |
| team loop 不因事件字段变化悄悄坏掉 | `review_flow`/event 字段仍在演进 | read model 容易 silent drift | 加 `team_loop_account_event_contract` 集成测试 |
| workspace 风险可见 | task 有 workspace metadata，但 loop 前无 preflight | shared/dirty workspace 可能污染证据 | Task 3 加 workspace preflight，记录 dirty state |
| 失败不无限返修 | 当前靠人判断 | 缺少 same failure / regression / max cycles 停止规则 | Task 4 加 stop rules 和 failure fingerprint |
| 覆盖课程/题库主业务 | v1 先做 builder code-repair | curriculum/qbank 占大多数工作，v1 覆盖面窄 | Phase 7 再加 `manifest-check`、`syllabus-coverage-check` |
| 重复问题能沉淀 | memory/workflow 已有，但 loop 不触发沉淀 | 缺少“多次同类失败 -> 更新协议”的机制 | Team Loop 记录 repeated repair cycles，manager 手动 crystallize，后续自动候选 |

### 当前最重要的缺口

1. **采用缺口：**如果 manager 的身份指令不知道 `loop-check`，这个功能实现了也不会被调用。因此 Task 0.5 必须先做。
2. **派工缺口：**`send` 和 `task dispatch` 当前分离。Loop 要挂证据，必须有正式 `task_id`。
3. **团队 read model 缺口：**现在可以知道 task status，但不能直接知道团队循环阶段。`team_loop_account` 是 Team Loop 的第一块砖。

### 不做什么

- 不把 workflow 文档变成自动执行引擎。
- 不让 `loop passed` 等于正式交付。
- 不绕过 reviewer verdict 和 manager closeout。
- 不在 v1 做 subjective content quality loop。内容质量仍然需要 reviewer authority。
- 不新增数据库，不新增依赖。

## CTO 决策

```text
Layer 1: Agent Loop
task -> role-local work/check/repair -> loop evidence archive
     -> task loop summary fields

Layer 2: Team Loop
workflow protocol -> manager dispatch -> member execution loop
                  -> review/check gate -> repair routing
                  -> manager closeout/crystallize
```

先做贴合 EduFlow 现有主干的最小版本，不先发明一个独立 loop engine。EduFlow 已经有 task ownership、review authority、publish gate、manager closeout、memory capsule、workflow contract、workspace metadata；Loop 层必须嵌进去，而不是另起炉灶。

关键判断：大多数 Loop Engineering 讨论的是单 agent 对自己输出的循环。EduFlow 确实需要这一层，但更重要的是团队循环：manager、worker、reviewer、verifier、memory 围绕一个固定 workflow 协议不断完成“执行 - 审核 - 返修 - 收口 - 沉淀”。

## 当前代码基础

- `src/eduflow/store/tasks.py` 已经负责 flow task 的 status、verdict、review outcome、meaningful task events。
- `src/eduflow/store/tasks.py` 已经有 workspace metadata：`workspace_mode`、`workspace_path`、`workspace_branch`、`workspace_base_commit`；`workspace_evidence_ref` 是 row field，但不是 `create_flow` 参数。
- `src/eduflow/store/task_publish_gate.py` 明确只信 store-produced task event，不信 actor 自报 diff。
- `src/eduflow/store/task_publish_render.py` 是 manager 看到 task 更新的渲染层；如果 manager 要用 loop，loop 摘要必须进入这里。
- `src/eduflow/commands/task.py` 已有 `evidence-explain` 和 manager closeout，Loop 不能绕过它们。
- `src/eduflow/memory/capsules.py` 从 task row 重建 task memory，所以 loop 状态必须落回 task row，否则 compact/reidentify 后会丢上下文。
- `src/eduflow/commands/send.py` / `read.py` 是异步 inbox/tmux 通讯面，不是可靠的同步 “agent finished” callback。
- `eduflow.toml` 是 agent instruction 的 canonical source；`src/eduflow/agents/identity.py` 会渲染到 `$EDUFLOW_STATE_DIR/agents/<agent>/identity.md`，`eduflow reidentify <agent>` 会重新注入。
- `docs/workflows` 已经定义重复协作协议。Loop Engineering 要让这些协议实例可观察、可改进，而不是替代它们。

## 非目标

- 不新增数据库。
- 不新增依赖。
- v1 不做 autonomous builder dispatch。
- v1 不做 LLM checker agents。
- 不把 `docs/workflows` 当执行引擎。
- v1 不新增一套 team-loop 状态机；先从现有 task events 推导。
- 不允许 loop `passed` 设置 `delivered`、`approved`、`closeout_completed` 或 `manager_action_allowed`。
- v1 不做主观内容质量 loop；内容质量仍然需要 reviewer authority。

## 产品表面

一个写命令，两个读命令：

```bash
./scripts/eduflowteam task loop-check <task_id> [--spec code-repair] [--max-cycles N] [--new-run] [--allow-unscoped-workspace] [--background]
./scripts/eduflowteam task loop-status <task_id|loop_id>
./scripts/eduflowteam task loop-list [--task-id T-1] [--status repair_needed|passed|stopped|failed]
```

为什么 v1 不做 `loop-start`：单独 start 会制造生命周期歧义。`loop-check` 没有 active run 时创建，有 active run 时追加 cycle，一个命令更不容易误用。

为什么 v1 不做 `team-loop-start`：workflow dispatch 本身就已经启动协作协议。Team Loop 第一版最有价值的是 `task loop-status <task_id>` 同时显示 `agent_loop` 和 `team_loop`。

历史任务可能有 `workspace_mode=""`。新的 loop-verified builder work 必须显式传 `--workspace-mode shared` 或 `worktree`；旧的 unscoped task 需要 `--allow-unscoped-workspace`，并把风险写入 loop evidence。

预期操作路径：

```text
manager creates a builder task with workspace metadata via task dispatch
manager sends the task id to worker_builder via send
manager runs task loop-check T-123 --background
if failed, command prints worker_builder handoff packet
worker_builder fixes in the declared workspace
manager runs task loop-check T-123 --background again
if passed, manager uses existing review/closeout path as appropriate
```

预期团队循环路径：

```text
manager dispatches workflow-backed task
team_loop phase=dispatching/member_execution/reviewing
worker submits evidence
reviewer approves or rejects
if rejected, team_loop phase=team_repair_needed and next_owner is explicit
after repeated cycles, manager can see loop health and crystallize protocol fixes
```

## 验收责任分层

循环的核心不是“谁说完成就完成”，而是每个任务都有验收合约，并且不同角色的验收权力不同。

```text
执行 agent：自检验收，只能证明“我交上来之前跑过标准”
review agent / deterministic checker：正式验收，可以给 accepted / changes_requested
manager：最终确认，可以 closeout_completed
```

最小实现不新增复杂权限系统，只在 task event 和 loop summary 里区分来源：

```text
loop.self_check_passed by worker_builder
loop.review_check_passed by review_agent
task.closeout_completed by manager
```

状态含义：

- `self_check_passed`：执行 agent 的提交条件，不是完成条件。
- `review_check_passed`：正式验收证据，可以支持 manager closeout。
- `manager_closeout`：任务真正结束。

因此 `loop passed` 必须继续被解释为“当前 acceptance spec 检查通过”，不能解释为“任务已经完成”。执行 agent 必须先自检，减少低级返工；review agent 仍然拥有正式验收权；manager 仍然拥有最终关闭权。

## 双层架构

### 第一层：Agent Loop

Agent Loop 提升单个角色自己的执行质量。

循环单位：

- one task
- one role
- one local verification spec
- one sequence of checker/repair cycles

例子：

- `worker_builder` runs code repair until deterministic checks pass or stop rules trigger.
- `worker_qbank` runs qbank verification until manifest/count/path evidence is complete.
- `review_course` can later run a read-only review checklist loop before emitting an authoritative verdict.

第一层状态由 task row 的轻量 loop 字段和 `loop_runs/<id>/` 证据目录共同表达。

### 第二层：Team Loop

Team Loop 提升多个角色之间的协作质量。

循环单位：

- one workflow-backed task or task family
- one `workflow_id`
- one protocol instance
- one sequence of handoff, execution, review, repair, and closeout cycles

Team Loop 不是“更多 agent loops”。它回答的是：

- Which collaboration protocol is active?
- Which role owns the next move?
- Is the team in execution, review, repair, closeout, or blocked state?
- How many review/repair cycles have happened?
- Did the same handoff failure repeat?
- Should the workflow contract or memory be updated after closeout?

第二层在 v1 是 read model。它从现有 task row、task events、review verdict、loop evidence、closeout gate 推导，不新增 workflow engine。

## Agent Loop 状态模型

task row 只保存轻量字段：

```json
{
  "loop_run_id": "L-000001",
  "loop_status": "repair_needed",
  "self_check_status": "passed",
  "review_check_status": "pending",
  "manager_closeout_status": "blocked",
  "loop_cycle_count": 2,
  "loop_stop_reason": "",
  "loop_recommended_action": "send_builder_handoff",
  "loop_evidence_ref": "loop_runs/L-000001/meta.json",
  "loop_updated_by": "manager"
}
```

重证据放到 loop archive：

```text
$EDUFLOW_STATE_DIR/
  loop-runs.json
  loop_runs/
    L-000001/
      meta.json
      cycle-001-checker.txt
      cycle-001-diff.patch
      cycle-001-preflight.json
```

真相源规则：

- 当前 loop 状态以 task row 为准。
- loop archive 是证据和 cycle history。
- 如果 task row 和 archive 不一致，命令打印 `loop_state_drift`，对 operator-facing 状态仍信 task row。
- self-check 只代表执行 agent 自检通过；review-check 才是正式验收证据；manager closeout 才是完成。

Agent Loop 状态：

- `running`
- `checking`
- `repair_needed`
- `passed`
- `stopped`
- `failed`

终态：

- `passed`
- `stopped`
- `failed`

停止原因：

- `all_green`
- `max_cycles`
- `same_failure_repeated`
- `no_failure_reduction`
- `regression_detected`
- `checker_unavailable`
- `workspace_policy_blocked`

## Team Loop 状态模型

Team Loop account 是推导出来的，不手工编辑：

```json
{
  "task_id": "T-123",
  "workflow_id": "igcse-subject-launch",
  "phase": "team_repair_needed",
  "cycle_count": 2,
  "current_owner": "worker_course",
  "next_owner": "worker_course",
  "last_gate": "review_verdict_authority_gate",
  "last_review_reason": "changes_requested",
  "loop_health": "repairing",
  "stuck_reason": "",
  "recommended_action": "send_repair_handoff",
  "agent_loop": {
    "run_id": "L-000001",
    "status": "repair_needed"
  }
}
```

团队阶段：

- `protocol_missing`
- `dispatching`
- `member_execution`
- `member_loop_repair`
- `reviewing`
- `team_repair_needed`
- `manager_action_blocked`
- `manager_closeout_ready`
- `closed`
- `stale_or_stuck`

Team cycle count 只在 review/repair 轮次上递增，不是每次 status 更新都递增。一次 reject/rework verdict 后接一轮 worker 修复，算一个 team loop cycle。

## Claude 执行手册

下面这部分是交给 Claude 的施工入口。你可以把“总提示词”先发给 Claude，然后按步骤逐步推进。每个步骤都对应后面的详细 Task；Claude 执行时要以对应 Task 的文件、代码片段和测试命令为准。

### 交给 Claude 的总提示词

```text
你现在在 EduFlow-Team-orch 仓库中，实现 docs/plans/2026-07-04-loop-engineering-execution-layer.md 里的 EduFlow 双层 Loop Engineering 方案。

执行规则：
1. 按“Claude 执行手册”的步骤顺序执行，不要跳步。
2. 每一步只做该步骤对应 Task 的范围，不做额外重构。
3. 每一步先写失败测试，再实现最小代码，再跑该步骤验收测试。
4. Loop pass 绝不能绕过 review verdict、delivery、manager closeout。
5. 执行 agent 的 self-check 只是提交条件；review agent / deterministic checker 的 review-check 才是正式验收证据；manager closeout 才是完成。
6. workflow 文档仍然是协作协议，不要做新的自动执行引擎。
7. 不新增数据库，不新增依赖。
8. 每一步完成后汇报：改了哪些文件、跑了哪些测试、是否通过、是否有剩余风险、下一步是什么。
9. 如果测试失败，先修复当前步骤；不要带着红灯进入下一步。
```

### 执行节奏

- 每一步完成后都建议单独 commit，commit message 使用本方案每个 Task 里的 Lore commit 示例。
- 如果 Claude 的上下文快满，停在当前步骤边界，输出下一步编号、已完成测试、未完成测试和当前风险。
- 如果发现现有代码和方案里的文件名有偏差，优先相信仓库现状，但必须在汇报里说明偏差和替代路径。

### Step 0：锁定现有 review/closeout 权限边界

对应详细任务：Task 0。

**给 Claude 的提示词：**

```text
请执行 Step 0，对应 Task 0：Lock the Existing Gate Contract。
目标是先用 characterization tests 锁定 EduFlow 现有 gate 合同，证明 loop evidence 不能自动 delivery，不能让 evidence-explain 变成 PASS，也不能打开 manager closeout。
只创建 tests/integration/test_loop_engineering_truth_contract.py，不实现功能代码。
完成后运行 Task 0 指定 pytest，确认失败原因是 tasks.set_loop_evidence 尚未实现。
```

**验收标准：**

- 新增 `tests/integration/test_loop_engineering_truth_contract.py`。
- 测试表达了 loop pass 不能改变 `status`、`verdict`、`closeout_status`。
- 测试表达了 loop pass 不能让 `evidence-explain` 给出正式 PASS。
- 运行 `pytest -q tests/integration/test_loop_engineering_truth_contract.py`，失败原因是缺少 `tasks.set_loop_evidence`。
- 没有修改生产代码。

### Step 1：让 manager 和 worker_builder 知道如何使用 loop

对应详细任务：Task 0.5。

**给 Claude 的提示词：**

```text
请执行 Step 1，对应 Task 0.5：Align Agent Instructions and Dispatch Path。
目标是解决采用缺口：manager 和 worker_builder 的身份提示必须知道 task loop-check、task dispatch、builder handoff、--background 的使用规则。
请只修改 canonical source：eduflow.toml，以及相关 identity 测试。不要直接改 .eduflow-team-state/agents/.../identity.md。
先写失败测试，再更新 eduflow.toml，再运行 pytest -q tests/unit/test_agents_identity.py -k loop。
```

**验收标准：**

- `tests/unit/test_agents_identity.py` 有 loop 相关测试。
- `eduflow.toml` 的 manager notes 明确要求 builder loop work 先 `task dispatch` 再 `send`。
- manager notes 明确使用 `task loop-check <task_id> --background`。
- worker_builder notes 明确不能削弱、删除、跳过测试。
- 测试 `pytest -q tests/unit/test_agents_identity.py -k loop` 通过。
- 文档或汇报里写清楚上线后要执行 `./scripts/eduflowteam reidentify manager` 和 `./scripts/eduflowteam reidentify worker_builder`。

### Step 2：把 loop 摘要挂回 task row

对应详细任务：Task 1。

**给 Claude 的提示词：**

```text
请执行 Step 2，对应 Task 1：Add Task-Native Loop Summary Fields。
目标是在 flow task 上增加轻量 loop summary fields，并实现 tasks.set_loop_evidence。
要求：set_loop_evidence 只能更新 loop_* 和 check summary 字段，不能碰 status、verdict、latest_authoritative_verdict、evidence_packet、closeout_status。
同时要表达三层验收边界：self_check_status、review_check_status、manager_closeout_status。
请先补 store 和 command 测试，再实现 tasks.py 与 task.py 的最小变更，最后跑 Task 1 指定的三组 pytest。
```

**验收标准：**

- `src/eduflow/store/tasks.py` 有合法 `LOOP_STATUSES`。
- flow task 默认包含 `loop_run_id`、`loop_status`、`loop_cycle_count`、`loop_stop_reason`、`loop_recommended_action`、`loop_evidence_ref`、`loop_updated_by`。
- flow task 默认包含 `self_check_status`、`review_check_status`、`manager_closeout_status`。
- `tasks.set_loop_evidence(...)` 会校验 status，会 emit task event，但不提升正式交付状态。
- 测试明确 self-check pass 不等于 review-check pass，不等于 manager closeout。
- `task get` 只在存在 `loop_run_id` 时显示 loop 摘要。
- Task 0 的 gate contract 测试转为通过。
- Task 1 指定 pytest 全部通过。

### Step 3：建立 loop evidence archive

对应详细任务：Task 2。

**给 Claude 的提示词：**

```text
请执行 Step 3，对应 Task 2：Add Loop Evidence Archive。
目标是在 EduFlow state dir 下建立 loop_runs 证据目录和 loop-runs.json 索引，用来保存每一轮 checker 输出、diff、preflight、fingerprint 和 meta.json。
不要新增数据库，不新增依赖。请使用现有 state_file/state_dir、flock、read_json、write_json 风格。
先写 tests/unit/test_store_loop_runs.py，再实现 src/eduflow/store/loop_runs.py。
```

**验收标准：**

- 新增 `src/eduflow/store/loop_runs.py`。
- 支持 active run 复用，terminal run 不复用。
- 每轮 cycle 写入 `cycle-XXX-checker.txt`、`cycle-XXX-preflight.json` 等 artifact。
- `loop-runs.json` 和 `loop_runs/<loop_id>/meta.json` 同步记录核心状态。
- `pytest -q tests/unit/test_store_loop_runs.py` 通过。

### Step 4：执行 workspace preflight

对应详细任务：Task 3。

**给 Claude 的提示词：**

```text
请执行 Step 4，对应 Task 3：Add Workspace Preflight。
目标是在 loop-check 真正跑测试前记录 workspace policy，避免 unscoped 或 dirty workspace 的证据污染。
请新增 src/eduflow/runtime/loop_preflight.py 和对应测试。
shared workspace 可以继续，但必须记录 shared_workspace_risk；worktree 必须要求 workspace_path 存在；缺 workspace_mode 默认失败，除非显式 allow_unscoped。
```

**验收标准：**

- 新增 `src/eduflow/runtime/loop_preflight.py`。
- 缺 `workspace_mode` 且没有 allow escape hatch 时失败。
- `workspace_mode=worktree` 要求真实路径。
- `workspace_mode=shared` 允许但标记风险。
- 如果 git 可用，记录 dirty 状态和最多 50 行 `git status --short`。
- `pytest -q tests/unit/test_runtime_loop_preflight.py` 通过。

### Step 5：实现 deterministic loop specs 和 runner

对应详细任务：Task 4。

**给 Claude 的提示词：**

```text
请执行 Step 5，对应 Task 4：Add Deterministic Verification Specs and Runner。
目标是实现第一版 deterministic checker：先支持 code-repair spec，运行 pytest -q 和 compileall，并生成 failure fingerprint、stop rules、regression detection。
只做确定性检查，不引入 LLM reviewer，不做主观内容质量判断。runner 需要支持 self-check 和 review-check 两种 mode；两者可以复用同一套 commands，但写入的 task event/source 不同。
请先写 loop_specs 和 loop_runner 的失败测试，再实现最小 runner。
```

**验收标准：**

- 新增 `src/eduflow/runtime/loop_specs.py` 和 `src/eduflow/runtime/loop_runner.py`。
- `code-repair` spec 明确包含 `pytest -q` 和 `python3 -m compileall -q src`。
- unknown spec 会报错。
- runner 能区分 passed / repair_needed / stopped / failed。
- runner 能记录 check mode：`self_check` 或 `review_check`。
- same failure repeated、no failure reduction、regression detected、max cycles 都有测试。
- failure fingerprint 做过路径和耗时归一化，避免每次无意义变化。
- Task 4 指定 pytest 全部通过。

### Step 6：暴露 task loop-check / loop-status / loop-list CLI

对应详细任务：Task 5。

**给 Claude 的提示词：**

```text
请执行 Step 6，对应 Task 5：Add task loop-check, loop-status, and loop-list。
目标是让 operator 可以用 CLI 创建或追加 loop run，并能查看 agent_loop 和 team_loop 摘要。
loop-check 默认复用 active run，只有 --new-run 才新建。--background 必须存在，避免 manager pane 被长测试卡住。
请先写 CLI 测试，再改 src/eduflow/commands/task.py。
```

**验收标准：**

- `task loop-check <task_id>` 能创建或追加 active loop run。
- `task loop-check` 能把最新 loop summary 写回 task row。
- `task loop-status <task_id|loop_id>` 能显示 agent loop。
- `task loop-list` 能按 task_id/status 过滤。
- `--background` 参数存在，并有测试覆盖。
- loop CLI 不改变正式 `status`、`verdict`、`closeout_status`。
- Task 5 指定 pytest 通过。

### Step 7：生成 builder handoff packet

对应详细任务：Task 6。

**给 Claude 的提示词：**

```text
请执行 Step 7，对应 Task 6：Add Builder Handoff Packet。
目标是当 loop-check 发现 repair_needed 或 stopped 时，生成 manager 可以直接转发给 worker_builder 的返修包。
返修包必须包含 task_id、loop_id、失败命令、失败摘要、证据路径、禁止事项和建议重跑命令。
不要自动 send 给 worker_builder，v1 由 manager 手动转发。
```

**验收标准：**

- 有 builder handoff 的生成函数和测试。
- handoff 明确红线：不要削弱、删除、跳过测试；不要改无关文件。
- handoff 包含 `eduflow task loop-check <task_id> --background` 的重跑提示。
- CLI 在 repair_needed/stopped 时能打印 handoff。
- Task 6 指定 pytest 通过。

### Step 8：把 loop evidence 接进现有 manager-facing surfaces

对应详细任务：Task 7。

**给 Claude 的提示词：**

```text
请执行 Step 8，对应 Task 7：Wire Loop Evidence Into Existing Surfaces。
目标是让 loop 状态进入现有 surfaces：task get、task publish render、evidence-explain、memory capsules。
注意：evidence-explain 只能把 loop evidence 当 supporting evidence，不能因此 PASS。
请优先保持现有 render 风格，不做 UI 大改。
```

**验收标准：**

- `task_publish_render.py` 在 task 有 loop evidence 时显示 compact loop summary。
- `evidence-explain` 显示 loop supporting evidence，但不授予正式 verdict。
- memory capsule 能带上 loop blockers/evidence refs。
- Loop-only task events 不被当成正式交付播报。
- Task 7 指定测试通过。

### Step 9：建立 team_loop_account read model

对应详细任务：Task 8。

**给 Claude 的提示词：**

```text
请执行 Step 9，对应 Task 8：Add Team Loop Account Read Model。
目标是实现第二层 Team Loop：从 workflow_id、task events、review verdict、closeout gate 和 agent_loop summary 推导团队协作阶段。
这是 read model，不允许手动编辑，不允许变成第二套 workflow engine。
Team Loop 必须把 self-check、review-check、manager closeout 分开显示，不能把 worker 自检当成正式验收。
请先写 store 测试和 event contract 集成测试，再实现 src/eduflow/store/team_loop_account.py，并把 task loop-status 接入 team_loop 区块。
```

**验收标准：**

- 新增 `src/eduflow/store/team_loop_account.py`。
- 能推导 `phase`、`cycle_count`、`current_owner`、`next_owner`、`last_gate`、`loop_health`、`stuck_reason`、`recommended_action`。
- 能显示 `self_check`、`review_check`、`manager_closeout` 三个状态。
- `cycle_count` 只按 review/repair 轮次递增，不按普通 status 更新递增。
- 有 `team_loop_account_event_contract` 测试，防止 task event 字段漂移。
- `task loop-status <task_id>` 同时显示 `agent_loop` 和 `team_loop`。
- Task 8 指定 pytest 通过。

### Step 10：补充 workflow candidate 文档

对应详细任务：Task 9。

**给 Claude 的提示词：**

```text
请执行 Step 10，对应 Task 9：Add Workflow Candidate Documentation。
目标是把 code-repair loop 和 team-collaboration loop 写成 docs/workflows 里的候选协作协议。
文档要说明何时使用、何时停止、manager 如何转发 handoff、为什么 loop pass 不等于 delivery。
不要把 workflow 文档写成自动执行引擎。
```

**验收标准：**

- 新增或更新 `docs/workflows` 下相关候选 workflow 文档。
- 文档明确区分 Agent Loop 和 Team Loop。
- 文档明确 manager closeout authority 不被 loop 取代。
- 文档包含 builder code-repair 的标准操作路径。
- 文档包含 repeated failure 后沉淀 memory/workflow 的建议。

### Step 11：跑端到端 smoke

对应详细任务：Task 10。

**给 Claude 的提示词：**

```text
请执行 Step 11，对应 Task 10：Add End-to-End Smoke。
目标是用 integration smoke 验证双层 loop：builder task 能生成 agent-loop evidence，workflow-backed task 能显示 team-loop review/repair phase。
请只写必要 smoke，不要把所有边界都塞进集成测试；边界已经在 unit tests 覆盖。
```

**验收标准：**

- 新增 `tests/integration/test_loop_engineering_flow.py`。
- smoke 覆盖 agent loop evidence 写入。
- smoke 覆盖 team_loop phase 推导。
- smoke 验证 loop pass 不提升正式 delivery/verdict/closeout。
- `pytest -q tests/integration/test_loop_engineering_flow.py` 通过。

### Step 12：最终验收和交付报告

对应详细任务：Task 11。

**给 Claude 的提示词：**

```text
请执行 Step 12，对应 Task 11：Final Verification。
目标是跑完 targeted tests、existing gate regression tests，以及可承受范围内的 full suite。
最后输出中文交付报告：改动文件、实现了哪些目标、目标与差距补齐情况、测试结果、未测试风险、上线时需要执行的 reidentify 命令。
如果 full suite 太慢或失败，必须列出失败测试、失败原因和下一步建议，不要假装完成。
```

**验收标准：**

- Task 11 targeted tests 全部通过。
- existing gate regression tests 全部通过，尤其是 task publish gate、commands task、full workflow。
- 手动 CLI smoke 路径可执行，至少说明 task id 如何替换。
- 汇报确认不新增 dependencies，不新增 database。
- 汇报确认 loop pass 不绕过 review/closeout。
- 汇报包含 `./scripts/eduflowteam reidentify manager` 和 `./scripts/eduflowteam reidentify worker_builder` 的上线动作。

## 详细实现任务

下面是每一步的代码级实现说明。Claude 执行时应先看上面的步骤提示词，再进入对应 Task 取具体文件、代码片段、测试命令和 commit message。

## Task 0：锁定现有 Gate 合同

**Files:**
- Create: `tests/integration/test_loop_engineering_truth_contract.py`

**Step 1: Write the failing characterization tests**

```python
from tests.helpers import isolated_env, run_cli
from eduflow.store import tasks


def test_loop_pass_never_auto_delivers_subject_task():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 sample",
            stage="curriculum",
            owner="worker_course",
        )

        # This function is added in Task 1.
        assert tasks.set_loop_evidence(
            tid,
            loop_run_id="L-000001",
            loop_status="passed",
            loop_cycle_count=1,
            loop_stop_reason="all_green",
            loop_evidence_ref="loop_runs/L-000001/meta.json",
            actor="manager",
        )

        row = tasks.get(tid)
        assert row["status"] == "queued"
        assert row["verdict"] == "pending"
        assert row["closeout_status"] == ""


def test_loop_pass_does_not_make_evidence_explain_pass():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 sample",
            stage="curriculum",
            owner="worker_course",
        )
        tasks.set_loop_evidence(
            tid,
            loop_run_id="L-000001",
            loop_status="passed",
            loop_cycle_count=1,
            loop_stop_reason="all_green",
            loop_evidence_ref="loop_runs/L-000001/meta.json",
            actor="manager",
        )

        rc, out, err = run_cli(["task", "evidence-explain", tid, "--json"])
        assert rc == 0, err
        assert '"verdict": "PASS"' not in out
        assert '"manager_action_allowed": true' not in out
```

**Step 2: Run to verify failure**

```bash
pytest -q tests/integration/test_loop_engineering_truth_contract.py
```

Expected: fails because `tasks.set_loop_evidence` does not exist.

**Step 3: Do not implement here**

This task only pins the contract. The next task makes it pass.

**Step 4: Commit**

```bash
git add tests/integration/test_loop_engineering_truth_contract.py
git commit -m "Guard loop evidence from bypassing review gates

Loop Engineering must support existing EduFlow authority, not replace it.
These characterization tests prove loop pass evidence cannot auto-deliver
or grant manager closeout.

Constraint: Existing subject closeout depends on authoritative review evidence
Confidence: high
Scope-risk: narrow
Tested: pytest -q tests/integration/test_loop_engineering_truth_contract.py"
```

## Task 0.5：对齐 Agent 指令和派工路径

**Files:**
- Modify: `eduflow.toml`
- Test: `tests/unit/test_agents_identity.py`

**Step 1: Write failing identity tests**

Add tests that prove the rendered prompts teach loop usage from config:

```python
def test_manager_identity_mentions_loop_check_for_builder_tasks(isolated_env):
    from eduflow.agents import identity

    text = identity.render("manager")
    assert "task loop-check" in text
    assert "task dispatch" in text
    assert "--background" in text
    assert "worker_builder" in text


def test_worker_builder_identity_mentions_builder_handoff(isolated_env):
    from eduflow.agents import identity

    text = identity.render("worker_builder")
    assert "Builder handoff" in text
    assert "Do not weaken tests" in text
    assert "please re-run: eduflow task loop-check" in text
```

If `identity.render` is not public in this repo, use the existing test helper pattern in `tests/unit/test_agents_identity.py` and assert against `identity.init_prompt(...)` or the generated identity file after `identity.write(...)`.

**Step 2: Run failing tests**

```bash
pytest -q tests/unit/test_agents_identity.py -k loop
```

Expected: missing loop instructions.

**Step 3: Update manager notes in `eduflow.toml`**

Append a compact rule to `[team.agents.manager].notes`:

```text
Loop Engineering builder rule: for builder work that needs deterministic
verification, first create a formal task with `eduflow task dispatch
worker_builder "<title>" --stage builder --owner worker_builder
--workspace-mode shared --by manager`, then notify worker_builder with
`eduflow send worker_builder manager "T-<id>: <title>" 高`.
Run `eduflow task loop-check T-<id> --background`; if it prints a Builder
handoff, forward that handoff verbatim to worker_builder. After worker_builder
reports a fix, run loop-check again. Do not use loop pass as CLOSEOUT.
```

Why `eduflow.toml`, not `.eduflow-team-state/agents/.../identity.md`: runtime identity files are rendered artifacts. `eduflow reidentify <agent>` rewrites them from config.

**Step 4: Update worker_builder notes in `eduflow.toml`**

Append:

```text
Loop Engineering: when manager sends a Builder handoff, preserve its red
lines. Fix root cause, do not weaken/delete/skip tests, and do not edit
unrelated files. After fixing, report:
`eduflow send manager worker_builder "Fixed T-<id>, please re-run:
eduflow task loop-check T-<id> --background" 高`. Do not declare delivery
from your own loop result; manager owns closeout.
```

**Step 5: Run tests**

```bash
pytest -q tests/unit/test_agents_identity.py -k loop
```

Expected: pass.

**Step 6: Manual activation note**

After merging, reload running agents:

```bash
./scripts/eduflowteam reidentify manager
./scripts/eduflowteam reidentify worker_builder
```

**Step 7: Commit**

```bash
git add eduflow.toml tests/unit/test_agents_identity.py
git commit -m "Teach manager and builder to use loop checks

The loop feature is dead code unless the resident agents know when to
invoke it. This wires builder-loop behavior into the canonical team
config that renders identity.md.

Constraint: Runtime identity files are generated from eduflow.toml
Rejected: Editing .eduflow-team-state/agents/*.identity directly | generated runtime artifact
Confidence: high
Scope-risk: moderate
Tested: pytest -q tests/unit/test_agents_identity.py -k loop"
```

## Task 1：给 Task 增加原生 Loop 摘要字段

**Files:**
- Modify: `src/eduflow/store/tasks.py`
- Modify: `src/eduflow/commands/task.py`
- Test: `tests/unit/test_store_tasks_flow.py`
- Test: `tests/unit/test_commands_task.py`
- Test: `tests/integration/test_loop_engineering_truth_contract.py`

**Step 1: Write store tests**

Add to `tests/unit/test_store_tasks_flow.py`:

```python
def test_set_loop_evidence_updates_only_loop_fields():
    tid = tasks.create_flow(
        "worker_builder",
        "Repair runtime verifier",
        stage="builder",
        owner="worker_builder",
    )

    assert tasks.set_loop_evidence(
        tid,
        loop_run_id="L-000001",
        loop_status="repair_needed",
        loop_cycle_count=1,
        loop_stop_reason="",
        loop_recommended_action="send_builder_handoff",
        loop_evidence_ref="loop_runs/L-000001/meta.json",
        actor="manager",
    )

    row = tasks.get(tid)
    assert row["loop_run_id"] == "L-000001"
    assert row["loop_status"] == "repair_needed"
    assert row["loop_cycle_count"] == 1
    assert row["loop_recommended_action"] == "send_builder_handoff"
    assert row["status"] == "queued"
    assert row["verdict"] == "pending"


def test_set_loop_evidence_rejects_unknown_status():
    tid = tasks.create_flow("worker_builder", "Repair", stage="builder", owner="worker_builder")
    try:
        tasks.set_loop_evidence(tid, loop_run_id="L-1", loop_status="magic", actor="manager")
    except ValueError as e:
        assert "invalid loop_status" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_self_check_pass_does_not_count_as_review_or_closeout():
    tid = tasks.create_flow("worker_builder", "Repair", stage="builder", owner="worker_builder")
    tasks.set_loop_evidence(
        tid,
        loop_run_id="L-000001",
        loop_status="passed",
        self_check_status="passed",
        review_check_status="pending",
        manager_closeout_status="blocked",
        actor="worker_builder",
    )

    row = tasks.get(tid)
    assert row["self_check_status"] == "passed"
    assert row["review_check_status"] == "pending"
    assert row["manager_closeout_status"] == "blocked"
    assert row["verdict"] == "pending"
    assert row["closeout_status"] == ""
```

Add to `tests/unit/test_commands_task.py`:

```python
def test_task_get_shows_loop_summary_fields():
    tid = tasks.create_flow("worker_builder", "Repair runtime", stage="builder", owner="worker_builder")
    tasks.set_loop_evidence(
        tid,
        loop_run_id="L-000001",
        loop_status="passed",
        loop_cycle_count=1,
        loop_stop_reason="all_green",
        loop_evidence_ref="loop_runs/L-000001/meta.json",
        actor="manager",
    )
    rc, out, err = run_cli(["task", "get", tid])
    assert rc == 0, err
    assert "loop_run_id: L-000001" in out
    assert "loop_status: passed" in out
    assert "loop_evidence_ref: loop_runs/L-000001/meta.json" in out
```

**Step 2: Run failing tests**

```bash
pytest -q tests/unit/test_store_tasks_flow.py -k loop_evidence
pytest -q tests/unit/test_commands_task.py -k loop_summary
pytest -q tests/integration/test_loop_engineering_truth_contract.py
```

Expected: `set_loop_evidence` missing.

**Step 3: Implement minimal task fields**

In `src/eduflow/store/tasks.py`:

- Add `LOOP_STATUSES = frozenset({...})`.
- Add these defaults to flow task creation:

```python
"loop_run_id": "",
"loop_status": "",
"loop_cycle_count": 0,
"loop_stop_reason": "",
"loop_recommended_action": "",
"loop_evidence_ref": "",
"loop_updated_by": "",
"self_check_status": "",
"review_check_status": "",
"manager_closeout_status": "",
```

- Add loop fields to `_FLOW_SEMANTIC_DEFAULTS`.
- Add loop fields to `_MEANINGFUL_EVENT_FIELDS` so task event consumers can see the loop state change.
- Add:

```python
def set_loop_evidence(
    task_id: str,
    *,
    loop_run_id: str,
    loop_status: str,
    loop_cycle_count: int = 0,
    loop_stop_reason: str = "",
    loop_recommended_action: str = "",
    loop_evidence_ref: str = "",
    self_check_status: str = "",
    review_check_status: str = "",
    manager_closeout_status: str = "",
    actor: str = "",
    emit_event: bool = True,
) -> bool:
    ...
```

Implementation rules:

- Only schema version 2 tasks are supported.
- Validate `loop_status` against `LOOP_STATUSES`.
- Clamp `loop_cycle_count` to `>= 0`.
- Validate check summary statuses against `""`, `pending`, `passed`, `failed`, `blocked`.
- Do not touch `status`, `verdict`, `latest_authoritative_verdict`, `evidence_packet`, or `closeout_status`.
- Emit a normal task transition event using `_append_task_event`.

In `src/eduflow/commands/task.py`, update `_fmt_task` to print loop fields only when `loop_run_id` is present.
If check summary fields are present, print them as `self_check_status`, `review_check_status`, and `manager_closeout_status`.

**Step 4: Run tests**

```bash
pytest -q tests/unit/test_store_tasks_flow.py -k loop_evidence
pytest -q tests/unit/test_commands_task.py -k loop_summary
pytest -q tests/integration/test_loop_engineering_truth_contract.py
```

Expected: pass.

**Step 5: Commit**

```bash
git add src/eduflow/store/tasks.py src/eduflow/commands/task.py \
  tests/unit/test_store_tasks_flow.py tests/unit/test_commands_task.py \
  tests/integration/test_loop_engineering_truth_contract.py
git commit -m "Attach loop evidence summary to flow tasks

Loop state is operator-facing task evidence, not a parallel source of
completion truth. The task row now carries only compact loop summary
fields while preserving existing review and closeout authority.

Constraint: Task events and memory capsules derive from task state
Rejected: Store loop state only under loop_runs | it would disappear from panels and memory
Confidence: high
Scope-risk: moderate
Tested: pytest -q tests/unit/test_store_tasks_flow.py -k loop_evidence
Tested: pytest -q tests/unit/test_commands_task.py -k loop_summary
Tested: pytest -q tests/integration/test_loop_engineering_truth_contract.py"
```

## Task 2：新增 Loop Evidence Archive

**Files:**
- Create: `src/eduflow/store/loop_runs.py`
- Test: `tests/unit/test_store_loop_runs.py`

**Step 1: Write failing tests**

```python
from eduflow.store import loop_runs


def test_create_or_get_active_run_reuses_existing_run(isolated_env):
    first = loop_runs.create_or_get_active(task_id="T-1", spec="code-repair", max_cycles=3)
    second = loop_runs.create_or_get_active(task_id="T-1", spec="code-repair", max_cycles=3)

    assert second["id"] == first["id"]
    assert second["task_id"] == "T-1"
    assert second["status"] == "running"


def test_append_cycle_writes_artifacts(isolated_env):
    run = loop_runs.create_or_get_active(task_id="T-1", spec="code-repair", max_cycles=3)
    updated = loop_runs.append_cycle(
        run["id"],
        checker_output="FAILED test_x.py",
        diff_text="diff --git a/x b/x",
        preflight={"workspace_mode": "shared"},
        failed_commands=["pytest -q"],
        passed_commands=[],
        failure_fingerprint="abc123",
        status="repair_needed",
        stop_reason="",
    )

    assert updated["cycle_count"] == 1
    assert updated["status"] == "repair_needed"
    assert loop_runs.artifact_path(run["id"], "cycle-001-checker.txt").exists()
    assert loop_runs.artifact_path(run["id"], "cycle-001-preflight.json").exists()


def test_terminal_run_is_not_reused(isolated_env):
    run = loop_runs.create_or_get_active(task_id="T-1", spec="code-repair", max_cycles=1)
    loop_runs.update_status(run["id"], status="passed", stop_reason="all_green")

    next_run = loop_runs.create_or_get_active(task_id="T-1", spec="code-repair", max_cycles=1)
    assert next_run["id"] != run["id"]
```

**Step 2: Run failing tests**

```bash
pytest -q tests/unit/test_store_loop_runs.py
```

Expected: import failure.

**Step 3: Implement minimal archive store**

Use existing primitives only:

- `eduflow.runtime.paths.state_file("loop-runs.json")`
- `eduflow.runtime.paths.state_dir() / "loop_runs" / loop_id`
- `from eduflow.util import flock, read_json, write_json`

Implement:

```python
TERMINAL_STATUSES = frozenset({"passed", "stopped", "failed"})

def create_or_get_active(*, task_id: str, spec: str, max_cycles: int) -> dict: ...
def get(loop_id: str) -> dict | None: ...
def list_runs(*, task_id: str = "", status: str = "") -> list[dict]: ...
def append_cycle(loop_id: str, *, checker_output: str, diff_text: str,
                 preflight: dict, failed_commands: list[str],
                 passed_commands: list[str], failure_fingerprint: str,
                 status: str, stop_reason: str) -> dict: ...
def update_status(loop_id: str, *, status: str, stop_reason: str = "") -> dict: ...
def artifact_path(loop_id: str, filename: str) -> Path: ...
def evidence_ref(loop_id: str) -> str: ...
```

Keep metadata duplicated in `loop-runs.json` and `meta.json`. The task row is still authoritative for current operator state.

**Step 4: Run tests**

```bash
pytest -q tests/unit/test_store_loop_runs.py
```

Expected: pass.

**Step 5: Commit**

```bash
git add src/eduflow/store/loop_runs.py tests/unit/test_store_loop_runs.py
git commit -m "Archive loop checker evidence by task

Loop cycles need durable command output and diff evidence, but tasks.json
should only carry a compact pointer. This adds a small JSON archive under
the existing EduFlow state directory.

Constraint: No database or dependency for v1
Confidence: high
Scope-risk: narrow
Tested: pytest -q tests/unit/test_store_loop_runs.py"
```

## Task 3：新增 Workspace Preflight

**Files:**
- Create: `src/eduflow/runtime/loop_preflight.py`
- Test: `tests/unit/test_runtime_loop_preflight.py`

**Step 1: Write failing tests**

```python
from pathlib import Path
from eduflow.runtime import loop_preflight


def test_worktree_mode_requires_existing_path(tmp_path):
    result = loop_preflight.check_workspace(
        workspace_mode="worktree",
        workspace_path=str(tmp_path / "missing"),
        allow_unscoped=False,
        cwd=tmp_path,
        run=lambda *a, **k: None,
    )
    assert result["ok"] is False
    assert result["reason"] == "workspace_path_missing"


def test_shared_mode_allows_check_but_flags_risk(tmp_path):
    result = loop_preflight.check_workspace(
        workspace_mode="shared",
        workspace_path="",
        allow_unscoped=False,
        cwd=tmp_path,
        run=lambda *a, **k: None,
    )
    assert result["ok"] is True
    assert result["shared_workspace_risk"] is True


def test_missing_mode_refuses_without_escape_hatch(tmp_path):
    result = loop_preflight.check_workspace(
        workspace_mode="",
        workspace_path="",
        allow_unscoped=False,
        cwd=tmp_path,
        run=lambda *a, **k: None,
    )
    assert result["ok"] is False
    assert result["reason"] == "workspace_policy_missing"
```

**Step 2: Run failing tests**

```bash
pytest -q tests/unit/test_runtime_loop_preflight.py
```

Expected: import failure.

**Step 3: Implement minimal preflight**

Implement:

```python
def check_workspace(*, workspace_mode: str, workspace_path: str,
                    allow_unscoped: bool, cwd: Path,
                    run=subprocess.run) -> dict:
    ...
```

Rules:

- Missing `workspace_mode` fails unless `allow_unscoped=True`.
- `worktree` requires a real `workspace_path`.
- `container` and `external_artifact` are recorded but not executed in v1; return `ok=False` with reason `unsupported_workspace_mode_for_loop`.
- `shared` is allowed for check-only evidence and sets `shared_workspace_risk=True`.
- If `git status --short` works, include `git_dirty` and up to 50 status lines.
- If git fails, record `git_status_unavailable=True` and continue.

**Step 4: Run tests**

```bash
pytest -q tests/unit/test_runtime_loop_preflight.py
```

Expected: pass.

**Step 5: Commit**

```bash
git add src/eduflow/runtime/loop_preflight.py tests/unit/test_runtime_loop_preflight.py
git commit -m "Record workspace policy before loop checks

Loop evidence is only useful when it names the execution workspace. The
preflight rejects unscoped work by default and records shared workspace
risk without creating worktrees.

Constraint: Existing tasks already carry workspace metadata
Confidence: high
Scope-risk: narrow
Tested: pytest -q tests/unit/test_runtime_loop_preflight.py"
```

## Task 4：新增确定性 Verification Specs 和 Runner

**Files:**
- Create: `src/eduflow/runtime/loop_specs.py`
- Create: `src/eduflow/runtime/loop_runner.py`
- Test: `tests/unit/test_runtime_loop_specs.py`
- Test: `tests/unit/test_runtime_loop_runner.py`

**Step 1: Write failing spec tests**

```python
from eduflow.runtime import loop_specs


def test_code_repair_spec_is_explicit():
    spec = loop_specs.resolve("code-repair")
    assert spec["name"] == "code-repair"
    assert ["pytest", "-q"] in spec["commands"]
    assert ["python3", "-m", "compileall", "-q", "src"] in spec["commands"]


def test_unknown_spec_rejected():
    try:
        loop_specs.resolve("content-review")
    except ValueError as e:
        assert "unknown loop spec" in str(e)
    else:
        raise AssertionError("expected ValueError")
```

**Step 2: Write failing runner tests**

```python
from eduflow.runtime import loop_runner


class Proc:
    def __init__(self, returncode, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_run_checker_cycle_passes(tmp_path):
    calls = []
    def fake_run(args, **kwargs):
        calls.append(args)
        return Proc(0, stdout="ok")

    result = loop_runner.run_checker_cycle(
        commands=[["pytest", "-q"]],
        cwd=tmp_path,
        run=fake_run,
    )

    assert result["passed"] is True
    assert result["failed_commands"] == []
    assert calls == [["pytest", "-q"]]


def test_same_failure_repeated_stops():
    previous = {"failed_commands": ["pytest -q"], "failure_fingerprint": "abc"}
    current = {"failed_commands": ["pytest -q"], "failure_fingerprint": "abc"}

    decision = loop_runner.decide_stop(current, previous, cycle=2, max_cycles=5)
    assert decision["status"] == "stopped"
    assert decision["stop_reason"] == "same_failure_repeated"


def test_fingerprint_normalizes_paths_timestamps_and_line_numbers():
    a = loop_runner.fingerprint_failure(
        "FAILED /Users/a/repo/tests/test_x.py::test_case\n"
        "  File '/Users/a/repo/src/foo.py', line 42\n"
        "2026-07-04 12:09:33 ERROR object=0xabc123"
    )
    b = loop_runner.fingerprint_failure(
        "FAILED /Users/b/repo/tests/test_x.py::test_case\n"
        "  File '/Users/b/repo/src/foo.py', line 99\n"
        "2026-07-04 14:22:01 ERROR object=0xdef456"
    )
    assert a == b
```

**Step 3: Run failing tests**

```bash
pytest -q tests/unit/test_runtime_loop_specs.py tests/unit/test_runtime_loop_runner.py
```

Expected: import failures.

**Step 4: Implement specs**

Keep v1 boring:

```python
SPECS = {
    "code-repair": {
        "name": "code-repair",
        "allowed_stages": {"builder"},
        "commands": [
            ["pytest", "-q"],
            ["python3", "-m", "compileall", "-q", "src"],
        ],
    },
}

def resolve(name: str) -> dict:
    ...
```

Do not auto-detect ecosystems yet.

**Step 5: Implement runner**

Implement:

```python
def run_checker_cycle(*, commands: list[list[str]], cwd: Path, run=subprocess.run) -> dict: ...
def fingerprint_failure(text: str) -> str: ...
def decide_stop(current: dict, previous: dict | None, *, cycle: int, max_cycles: int) -> dict: ...
```

Rules:

- Run commands sequentially.
- Capture stdout/stderr.
- Timeout per command: 30 minutes.
- Return command strings, not raw arg arrays, in `passed_commands` / `failed_commands`.
- Fingerprint normalized failing command plus last 80 non-empty output lines.
- Normalize absolute paths, timestamps, memory addresses, Python line numbers, process ids, and repeated whitespace before hashing.
- `all_green` -> status `passed`.
- `checker_unavailable` -> status `failed`.
- `max_cycles`, `same_failure_repeated`, `no_failure_reduction`, `regression_detected` -> status `stopped`.
- Non-terminal failure -> status `repair_needed`.

**Step 6: Run tests**

```bash
pytest -q tests/unit/test_runtime_loop_specs.py tests/unit/test_runtime_loop_runner.py
```

Expected: pass.

**Step 7: Commit**

```bash
git add src/eduflow/runtime/loop_specs.py src/eduflow/runtime/loop_runner.py \
  tests/unit/test_runtime_loop_specs.py tests/unit/test_runtime_loop_runner.py
git commit -m "Run deterministic loop verification specs

The first Loop Engineering lane is a deterministic code-repair checker.
It runs existing Python verification commands, fingerprints failures, and
returns stop decisions without mutating task state.

Rejected: Generic ecosystem detection | code-repair is the only v1 target
Confidence: high
Scope-risk: narrow
Tested: pytest -q tests/unit/test_runtime_loop_specs.py tests/unit/test_runtime_loop_runner.py"
```

## Task 5：新增 `task loop-check`、`loop-status`、`loop-list`

**Files:**
- Modify: `src/eduflow/commands/task.py`
- Test: `tests/unit/test_commands_task.py`

**Step 1: Write failing CLI tests**

```python
def test_loop_check_requires_existing_flow_task():
    rc, out, err = run_cli(["task", "loop-check", "T-missing"])
    assert rc == 1
    assert "no such task" in err


def test_loop_check_rejects_non_builder_stage():
    tid = tasks.create_flow("worker_course", "Content task", stage="curriculum", owner="worker_course")
    rc, out, err = run_cli(["task", "loop-check", tid, "--allow-unscoped-workspace"])
    assert rc == 1
    assert "loop spec code-repair supports stages: builder" in err


def test_loop_status_prints_task_loop_state(monkeypatch):
    tid = tasks.create_flow("worker_builder", "Repair runtime", stage="builder", owner="worker_builder")
    tasks.set_loop_evidence(
        tid,
        loop_run_id="L-000001",
        loop_status="repair_needed",
        loop_cycle_count=1,
        loop_evidence_ref="loop_runs/L-000001/meta.json",
        actor="manager",
    )

    rc, out, err = run_cli(["task", "loop-status", tid])
    assert rc == 0, err
    assert "loop_run_id: L-000001" in out
    assert "loop_status: repair_needed" in out
```

**Step 2: Write execution test with patched runner**

```python
def test_loop_check_records_pass(monkeypatch):
    tid = tasks.create_flow(
        "worker_builder",
        "Repair runtime",
        stage="builder",
        owner="worker_builder",
        workspace_mode="shared",
    )
    monkeypatch.setattr(task_cmd.loop_runner, "run_checker_cycle", lambda **kw: {
        "passed": True,
        "output": "ALL GREEN",
        "failed_commands": [],
        "passed_commands": ["pytest -q"],
        "failure_fingerprint": "",
        "checker_unavailable": False,
    })

    rc, out, err = run_cli(["task", "loop-check", tid])
    assert rc == 0, err
    row = tasks.get(tid)
    assert row["loop_status"] == "passed"
    assert row["loop_stop_reason"] == "all_green"
    assert row["status"] == "queued"


def test_loop_check_background_marks_checking(monkeypatch):
    tid = tasks.create_flow(
        "worker_builder",
        "Repair runtime",
        stage="builder",
        owner="worker_builder",
        workspace_mode="shared",
    )

    class FakePopen:
        pid = 12345
        def __init__(self, *args, **kwargs):
            pass

    monkeypatch.setattr(task_cmd.subprocess, "Popen", FakePopen)

    rc, out, err = run_cli(["task", "loop-check", tid, "--background"])
    assert rc == 0, err
    row = tasks.get(tid)
    assert row["loop_status"] == "checking"
    assert "background started" in out
```

**Step 3: Run failing tests**

```bash
pytest -q tests/unit/test_commands_task.py -k loop
```

Expected: unknown subcommand.

**Step 4: Implement CLI handlers**

In `src/eduflow/commands/task.py`:

- Add usage lines:

```text
task loop-check <task_id> [--spec code-repair] [--max-cycles N] [--new-run] [--allow-unscoped-workspace] [--background]
task loop-status <task_id|loop_id>
task loop-list [--task-id T] [--status S]
```

- Import `loop_runs`, `loop_specs`, `loop_preflight`, `loop_runner`.
- Add:

```python
def _cmd_loop_check(rest: list[str]) -> int: ...
def _cmd_loop_status(rest: list[str]) -> int: ...
def _cmd_loop_list(rest: list[str]) -> int: ...
```

`loop-check` flow:

1. Load task.
2. Require schema version 2.
3. Resolve spec, default `code-repair`.
4. Require task stage in `spec["allowed_stages"]`.
5. Run workspace preflight.
6. If preflight blocks, set loop status `failed` with stop reason `workspace_policy_blocked`.
7. Create or reuse active loop run, unless `--new-run`.
8. Run one checker cycle.
9. Compare against previous cycle and decide status.
10. Append cycle artifacts.
11. Call `tasks.set_loop_evidence`.
12. Print concise status and next action.

When `--background` is passed:

1. Create or reuse the active loop run.
2. Set task loop status to `checking`.
3. Spawn the checker process with `subprocess.Popen(..., start_new_session=True)`.
4. Write `$EDUFLOW_STATE_DIR/loop_runs/<loop_id>/checker.pid`.
5. Print `loop-check background started; use task loop-status <task_id>`.
6. The child process writes artifacts and calls `tasks.set_loop_evidence` on completion.
7. `loop-status` reports `checking` while the pid is live, and the final state afterward.

Use `--background` in manager-driven flows. Synchronous `loop-check` is for local developer tests and short checks only.

Note on stage gating: loop specs are intentionally stricter than ordinary task dispatch. EduFlow may allow a builder-owned task with a non-builder stage, but `code-repair` only verifies `stage=builder`. Add a separate `manifest-check` or `syllabus-coverage-check` spec for curriculum/qbank loops instead of widening `code-repair`.

Do not call `tasks.transition_flow`.
Do not call `send`.
Do not mutate review/closeout fields.

**Step 5: Run tests**

```bash
pytest -q tests/unit/test_commands_task.py -k loop
```

Expected: pass.

**Step 6: Commit**

```bash
git add src/eduflow/commands/task.py tests/unit/test_commands_task.py
git commit -m "Expose task-native loop check commands

Managers can now run one deterministic loop cycle from the task command
surface. The command creates or appends loop evidence and updates task
loop fields without changing delivery or closeout state.

Constraint: Agent completion is asynchronous, so v1 remains manager-mediated
Rejected: Separate loop-start command | one loop-check command covers create and append
Confidence: high
Scope-risk: moderate
Tested: pytest -q tests/unit/test_commands_task.py -k loop"
```

## Task 6：新增 Builder Handoff Packet

**Files:**
- Modify: `src/eduflow/commands/task.py`
- Test: `tests/unit/test_commands_task.py`

**Step 1: Write failing test**

```python
def test_loop_check_failure_prints_builder_handoff(monkeypatch):
    tid = tasks.create_flow(
        "worker_builder",
        "Repair runtime",
        stage="builder",
        owner="worker_builder",
        workspace_mode="shared",
    )
    monkeypatch.setattr(task_cmd.loop_runner, "run_checker_cycle", lambda **kw: {
        "passed": False,
        "output": "FAILED test_runtime.py",
        "failed_commands": ["pytest -q"],
        "passed_commands": [],
        "failure_fingerprint": "abc123",
        "checker_unavailable": False,
    })

    rc, out, err = run_cli(["task", "loop-check", tid])
    assert rc == 0, err
    assert "Builder handoff" in out
    assert "loop_run_id:" in out
    assert "failed_commands:" in out
    assert "Do not weaken tests" in out
    assert "After fixing, ask manager to run:" in out
    assert f"task loop-check {tid}" in out
```

**Step 2: Run failing test**

```bash
pytest -q tests/unit/test_commands_task.py -k builder_handoff
```

Expected: missing handoff.

**Step 3: Implement handoff renderer**

Add a small helper:

```python
def _print_loop_builder_handoff(task: dict, run: dict, cycle: dict) -> None:
    ...
```

Handoff includes:

- Task id/title.
- Loop id.
- Workspace mode/path.
- Evidence ref.
- Failed commands.
- Short checker output tail path.
- Red lines:
  - Do not weaken tests.
  - Fix root cause, not symptom.
  - Do not edit unrelated files.
  - Preserve existing review/closeout gates.
  - After fix, ask manager to run `task loop-check <task_id>`.

If `workspace_mode=shared`, print `shared_workspace_risk=true`.

**Step 4: Run tests**

```bash
pytest -q tests/unit/test_commands_task.py -k loop
```

Expected: pass.

**Step 5: Commit**

```bash
git add src/eduflow/commands/task.py tests/unit/test_commands_task.py
git commit -m "Print builder handoff from failed loop checks

Failed deterministic checks now produce a concise worker_builder repair
packet while leaving the manager in charge of dispatch and closeout.

Rejected: Auto-send handoff in v1 | send/read is asynchronous and not a reliable completion loop
Confidence: high
Scope-risk: narrow
Tested: pytest -q tests/unit/test_commands_task.py -k loop"
```

## Task 7：把 Loop Evidence 接入现有 Surfaces

**Files:**
- Modify: `src/eduflow/store/task_publish_gate.py`
- Modify: `src/eduflow/store/task_publish_render.py`
- Modify: `src/eduflow/memory/capsules.py`
- Modify: `src/eduflow/commands/task.py`
- Test: `tests/unit/test_task_publish_gate.py`
- Test: `tests/unit/test_task_publish_render.py`
- Test: `tests/unit/test_memory_capsules.py`
- Test: `tests/unit/test_commands_task.py`

**Step 1: Add publish-gate test**

```python
def test_loop_only_transition_is_internal():
    before = {"id": "T-1", "schema_version": 2, "status": "in_progress"}
    after = {
        **before,
        "loop_run_id": "L-000001",
        "loop_status": "repair_needed",
        "loop_cycle_count": 1,
    }
    event = {
        "event_id": "E-1",
        "task_id": "T-1",
        "kind": "transition",
        "before": before,
        "after": after,
        "changes": {"loop_status": {"before": "", "after": "repair_needed"}},
        "created_at": 1,
    }

    decision = task_publish_gate.decide_task_event_publish(event, sender="manager")
    assert decision["publish"] is False
    assert decision["reason"] in {"transition_silent", "loop_internal_only"}
```

**Step 2: Add capsule test**

```python
def test_task_capsule_includes_loop_blocker_when_repair_needed(isolated_env):
    tid = tasks.create_flow("worker_builder", "Repair runtime", stage="builder", owner="worker_builder")
    tasks.set_loop_evidence(
        tid,
        loop_run_id="L-000001",
        loop_status="repair_needed",
        loop_cycle_count=1,
        loop_recommended_action="send_builder_handoff",
        loop_evidence_ref="loop_runs/L-000001/meta.json",
        actor="manager",
    )

    capsule = capsules.refresh_from_task_store(tid)
    assert "loop_status=repair_needed" in capsule["blockers"]
    assert capsule["last_evidence_ref"] == "loop_runs/L-000001/meta.json"
```

**Step 3: Add evidence-explain test**

```python
def test_evidence_explain_reports_loop_as_supporting_evidence_not_pass():
    tid = tasks.create_flow("worker_course", "Content", stage="curriculum", owner="worker_course")
    tasks.set_loop_evidence(
        tid,
        loop_run_id="L-000001",
        loop_status="passed",
        loop_cycle_count=1,
        loop_evidence_ref="loop_runs/L-000001/meta.json",
        actor="manager",
    )

    rc, out, err = run_cli(["task", "evidence-explain", tid, "--json"])
    assert rc == 0, err
    assert "loop_runs/L-000001/meta.json" in out
    assert '"manager_action_allowed": true' not in out
```

**Step 4: Add render test**

```python
def test_publish_render_includes_loop_summary_without_verdict():
    task = {
        "id": "T-1",
        "title": "Repair runtime",
        "stage": "builder",
        "status": "in_progress",
        "verdict": "pending",
        "loop_run_id": "L-000001",
        "loop_status": "repair_needed",
        "loop_cycle_count": 2,
        "loop_stop_reason": "",
        "loop_recommended_action": "send_builder_handoff",
    }
    decision = {"task_id": "T-1", "reason": "transition_silent", "delivery_lane": "internal_only"}

    text = task_publish_render.render_publish_message(task, decision)
    assert "Loop:" in text or "loop" in text.lower()
    assert "repair_needed" in text
    assert "结论=approved" not in text
```

**Step 5: Run failing tests**

```bash
pytest -q tests/unit/test_task_publish_gate.py -k loop
pytest -q tests/unit/test_task_publish_render.py -k loop
pytest -q tests/unit/test_memory_capsules.py -k loop
pytest -q tests/unit/test_commands_task.py -k evidence_explain
```

Expected: failures until surfaces are wired.

**Step 5: Implement surface wiring**

`task_publish_gate.py`:

- Keep loop-only changes internal.
- Do not add a user-facing publish reason unless a future product decision needs it.

`task_publish_render.py`:

- Render a compact loop line when `loop_run_id` exists.
- Include `loop_status`, `loop_cycle_count`, `loop_stop_reason`, and `loop_recommended_action` when present.
- Do not render loop status as `verdict` or delivery proof.

`memory/capsules.py`:

- If `loop_status` is `repair_needed`, `stopped`, or `failed`, add a blocker.
- Prefer `loop_evidence_ref` as `last_evidence_ref` when present.
- Set next action:
  - `repair_needed` -> `send_builder_handoff`
  - `stopped` -> `manager_review_loop_stop`
  - `passed` -> keep existing next action; do not auto-close.

`commands/task.py`:

- Include loop fields in `build_evidence_verdict_packet` as supporting evidence:

```python
"loop_evidence": {
    "run_id": task.get("loop_run_id") or "",
    "status": task.get("loop_status") or "",
    "cycle_count": task.get("loop_cycle_count") or 0,
    "stop_reason": task.get("loop_stop_reason") or "",
    "evidence_ref": task.get("loop_evidence_ref") or "",
}
```

- Do not feed loop status into `_classify_evidence_verdict`.

**Step 7: Run tests**

```bash
pytest -q tests/unit/test_task_publish_gate.py -k loop
pytest -q tests/unit/test_task_publish_render.py -k loop
pytest -q tests/unit/test_memory_capsules.py -k loop
pytest -q tests/unit/test_commands_task.py -k evidence_explain
```

Expected: pass.

**Step 8: Commit**

```bash
git add src/eduflow/store/task_publish_gate.py src/eduflow/store/task_publish_render.py \
  src/eduflow/memory/capsules.py src/eduflow/commands/task.py \
  tests/unit/test_task_publish_gate.py tests/unit/test_task_publish_render.py \
  tests/unit/test_memory_capsules.py tests/unit/test_commands_task.py
git commit -m "Surface loop evidence without changing closeout authority

Loop state now appears in publish, memory, and evidence surfaces as
supporting evidence only. It cannot grant delivery or manager closeout.

Constraint: EduFlow publishes and remembers task-derived truth
Confidence: high
Scope-risk: moderate
Tested: pytest -q tests/unit/test_task_publish_gate.py -k loop
Tested: pytest -q tests/unit/test_task_publish_render.py -k loop
Tested: pytest -q tests/unit/test_memory_capsules.py -k loop
Tested: pytest -q tests/unit/test_commands_task.py -k evidence_explain"
```

## Task 8：新增 Team Loop Account Read Model

**Files:**
- Create: `src/eduflow/store/team_loop_account.py`
- Modify: `src/eduflow/commands/task.py`
- Test: `tests/unit/test_store_team_loop_account.py`
- Test: `tests/unit/test_commands_task.py`
- Test: `tests/integration/test_loop_engineering_truth_contract.py`

**Step 1: Write failing account tests**

```python
from eduflow.store import tasks, team_loop_account


def test_team_loop_account_tracks_reviewing_phase(isolated_env):
    tid = tasks.create_flow(
        "worker_course",
        "IGCSE Accounting 0452 production",
        stage="curriculum",
        owner="worker_course",
        workflow_id="igcse-subject-launch",
    )
    tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
    tasks.transition_flow(tid, to_status="assigned", actor="manager")
    tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
    tasks.submit_for_review(tid, actor="worker_course")

    account = team_loop_account.build(tid)
    assert account["workflow_id"] == "igcse-subject-launch"
    assert account["phase"] == "reviewing"
    assert account["next_owner"] == "review_course"
    assert account["cycle_count"] == 0


def test_team_loop_account_tracks_repair_needed_after_review_reject(isolated_env):
    tid = tasks.create_flow(
        "worker_course",
        "IGCSE Accounting 0452 production",
        stage="curriculum",
        owner="worker_course",
        workflow_id="igcse-subject-launch",
    )
    tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
    tasks.transition_flow(tid, to_status="assigned", actor="manager")
    tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
    tasks.submit_for_review(tid, actor="worker_course")
    tasks.review_flow(
        tid,
        outcome="reject",
        actor="review_course",
        review_reason="changes_requested",
        required_fix=["expand manifest evidence"],
        blocking_files=["manifest.csv"],
    )

    account = team_loop_account.build(tid)
    assert account["phase"] == "team_repair_needed"
    assert account["next_owner"] == "worker_course"
    assert account["cycle_count"] == 1
    assert account["last_review_reason"] == "changes_requested"
    assert account["recommended_action"] == "send_repair_handoff"


def test_team_loop_account_marks_protocol_missing(isolated_env):
    tid = tasks.create_flow("worker_builder", "Ad hoc repair", stage="builder", owner="worker_builder")
    account = team_loop_account.build(tid)
    assert account["phase"] == "protocol_missing"
    assert account["workflow_id"] == ""
```

**Step 2: Write failing CLI test**

```python
def test_loop_status_prints_team_loop_section():
    tid = tasks.create_flow(
        "worker_course",
        "IGCSE Accounting 0452 production",
        stage="curriculum",
        owner="worker_course",
        workflow_id="igcse-subject-launch",
    )
    tasks.transition_flow(tid, to_status="assigned", actor="manager")

    rc, out, err = run_cli(["task", "loop-status", tid])
    assert rc == 0, err
    assert "team_loop:" in out
    assert "workflow_id: igcse-subject-launch" in out
    assert "phase: dispatching" in out
```

**Step 3: Write event-schema contract test**

Add to `tests/integration/test_loop_engineering_truth_contract.py`:

```python
def test_team_loop_account_event_contract():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "Contract test",
            stage="curriculum",
            owner="worker_course",
            workflow_id="igcse-subject-launch",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")
        tasks.review_flow(
            tid,
            outcome="reject",
            actor="review_course",
            review_reason="changes_requested",
            required_fix=["fix X"],
            blocking_files=["x.csv"],
        )

        events = tasks.list_task_events(task_id=tid, limit=200)
        last = events[-1]
        after = last.get("after") or {}
        changes = last.get("changes") or {}

        assert "status" in after
        assert "verdict" in after
        assert "review_reason" in after
        assert "required_fix" in after
        assert "blocking_files" in after
        assert "review_reason" in changes
        assert after["review_reason"] in {"changes_requested", "quality_not_met"}
```

This test is deliberately narrow. It pins only the event fields that `team_loop_account.build()` needs.

**Step 4: Run failing tests**

```bash
pytest -q tests/unit/test_store_team_loop_account.py
pytest -q tests/unit/test_commands_task.py -k team_loop
pytest -q tests/integration/test_loop_engineering_truth_contract.py -k team_loop_account_event_contract
```

Expected: import failure and missing CLI output.

**Step 5: Implement `team_loop_account.build`**

Implement a read-only function:

```python
def build(task_id: str) -> dict:
    task = tasks.get(task_id)
    events = tasks.list_task_events(task_id=task_id, limit=200)
    ...
```

Rules:

- Return `{"exists": False, "task_id": task_id}` if no task.
- If no `workflow_id`, phase is `protocol_missing`.
- Apply repair/blocking precedence before generic status mapping:
  - latest authoritative verdict rejected, or review reason `changes_requested` / `quality_not_met` -> `team_repair_needed`.
  - `blocked` with `needs_manager_action` -> `manager_action_blocked`.
  - `closeout_status=closeout_completed` -> `closed`.
- `queued` or `assigned` -> `dispatching`.
- `in_progress` -> `member_execution`, unless `loop_status` is `repair_needed`, `stopped`, or `failed`; then `member_loop_repair`.
- `submitted_for_review` -> `reviewing`, next owner is `reviewer`.
- `delivered` without `closeout_completed` -> `manager_closeout_ready`.
- Count repair cycles from task events where `verdict` changes to `rejected` or `review_reason` changes to a repair reason.
- Include compact `agent_loop` from task loop fields.

Do not write state. Do not inspect workflow docs in v1; `workflow_id` is enough to bind the protocol instance.

**Step 6: Integrate with CLI**

Update `_cmd_loop_status`:

- If input is a task id, print both:

```text
agent_loop:
  loop_run_id: L-000001
  loop_status: repair_needed
team_loop:
  workflow_id: igcse-subject-launch
  phase: team_repair_needed
  cycle_count: 1
  next_owner: worker_course
  recommended_action: send_repair_handoff
```

- If input is a loop id, print only the agent loop archive.

**Step 7: Run tests**

```bash
pytest -q tests/unit/test_store_team_loop_account.py
pytest -q tests/unit/test_commands_task.py -k "loop_status or team_loop"
pytest -q tests/integration/test_loop_engineering_truth_contract.py -k team_loop_account_event_contract
```

Expected: pass.

**Step 8: Commit**

```bash
git add src/eduflow/store/team_loop_account.py src/eduflow/commands/task.py \
  tests/unit/test_store_team_loop_account.py tests/unit/test_commands_task.py \
  tests/integration/test_loop_engineering_truth_contract.py
git commit -m "Derive team loop state from workflow task events

EduFlow's team loop is a collaboration protocol instance, not another
state machine. This read model derives the current phase, cycle count,
next owner, and repair recommendation from existing task truth.

Constraint: Workflow docs define contracts but do not execute them
Rejected: New team-loop lifecycle store | task events already contain the protocol rhythm
Confidence: medium
Scope-risk: moderate
Tested: pytest -q tests/unit/test_store_team_loop_account.py
Tested: pytest -q tests/unit/test_commands_task.py -k \"loop_status or team_loop\"
Tested: pytest -q tests/integration/test_loop_engineering_truth_contract.py -k team_loop_account_event_contract"
```

## Task 9：新增 Workflow Candidate 文档

**Files:**
- Create: `docs/workflows/_candidates/loop-engineering-code-repair/README.md`
- Create: `docs/workflows/_candidates/loop-engineering-code-repair/trigger.md`
- Create: `docs/workflows/_candidates/loop-engineering-code-repair/roles.md`
- Create: `docs/workflows/_candidates/loop-engineering-code-repair/checklist.md`
- Create: `docs/workflows/_candidates/loop-engineering-code-repair/handoff-template.md`
- Create: `docs/workflows/_candidates/loop-engineering-team-collaboration/README.md`
- Create: `docs/workflows/_candidates/loop-engineering-team-collaboration/trigger.md`
- Create: `docs/workflows/_candidates/loop-engineering-team-collaboration/roles.md`
- Create: `docs/workflows/_candidates/loop-engineering-team-collaboration/checklist.md`
- Create: `docs/workflows/_candidates/loop-engineering-team-collaboration/handoff-template.md`

**Step 1: Write docs**

Required content for `loop-engineering-code-repair`:

- Candidate workflow, not active.
- Primary chain: `manager -> deterministic_checker -> worker_builder -> deterministic_checker -> manager`.
- Allowed stage: `builder`.
- Allowed spec: `code-repair`.
- Forbidden: curriculum/content/admissions/school subjective judgment.
- Loop `passed` means deterministic checker passed; it does not mean user delivery.
- Closeout remains manager-owned.

Required content for `loop-engineering-team-collaboration`:

- Candidate workflow, not active.
- Primary chain: `manager -> assigned_member -> reviewer/checker -> manager`.
- A workflow is a collaboration protocol; a team loop is one live protocol instance.
- Required phases: dispatching, member execution, review/check, repair routing, closeout/crystallize.
- Every repair cycle must name next owner, required fix, evidence ref, and stop condition.
- After repeated same-failure cycles, manager updates workflow docs or memory before another run.

**Step 2: Validate candidate**

```bash
PYTHONPATH=src python3 -m eduflow.cli workflow candidate-validate
PYTHONPATH=src python3 -m eduflow.cli workflow candidate-validate --strict
```

Expected: pass.

**Step 3: Commit**

```bash
git add docs/workflows/_candidates/loop-engineering-code-repair \
  docs/workflows/_candidates/loop-engineering-team-collaboration
git commit -m "Document loop engineering workflow candidates

The workflow candidates describe both the agent-level code repair loop
and the team-level collaboration loop. They keep workflow docs as role
and gate contracts rather than execution engines.

Constraint: Workflow registry must not bypass task/review gates
Confidence: high
Scope-risk: narrow
Tested: PYTHONPATH=src python3 -m eduflow.cli workflow candidate-validate --strict"
```

## Task 10：新增端到端 Smoke 测试

**Files:**
- Create: `tests/integration/test_loop_engineering_flow.py`

**Step 1: Write integration test**

Scenario 1: agent loop on builder task.

```python
def test_loop_engineering_builder_flow(monkeypatch):
    with isolated_env():
        tid = tasks.create_flow(
            "worker_builder",
            "Repair runtime verifier",
            stage="builder",
            owner="worker_builder",
            workspace_mode="shared",
        )

        monkeypatch.setattr(task_cmd.loop_runner, "run_checker_cycle", lambda **kw: {
            "passed": False,
            "output": "FAILED first",
            "failed_commands": ["pytest -q"],
            "passed_commands": [],
            "failure_fingerprint": "abc",
            "checker_unavailable": False,
        })
        rc, out, err = run_cli(["task", "loop-check", tid])
        assert rc == 0, err
        assert "Builder handoff" in out
        assert tasks.get(tid)["loop_status"] == "repair_needed"

        monkeypatch.setattr(task_cmd.loop_runner, "run_checker_cycle", lambda **kw: {
            "passed": True,
            "output": "ALL GREEN",
            "failed_commands": [],
            "passed_commands": ["pytest -q"],
            "failure_fingerprint": "",
            "checker_unavailable": False,
        })
        rc, out, err = run_cli(["task", "loop-check", tid])
        assert rc == 0, err
        row = tasks.get(tid)
        assert row["loop_status"] == "passed"
        assert row["loop_stop_reason"] == "all_green"
        assert row["status"] == "queued"

        rc, out, err = run_cli(["task", "get", tid])
        assert rc == 0, err
        assert "loop_status: passed" in out
```

Scenario 2: team loop on workflow-backed review/repair task.

```python
def test_team_loop_review_repair_flow():
    with isolated_env():
        tid = tasks.create_flow(
            "worker_course",
            "IGCSE Accounting 0452 production",
            stage="curriculum",
            owner="worker_course",
            workflow_id="igcse-subject-launch",
        )
        tasks.assign_reviewer(tid, reviewer="review_course", actor="manager")
        tasks.transition_flow(tid, to_status="assigned", actor="manager")
        tasks.transition_flow(tid, to_status="in_progress", actor="worker_course")
        tasks.submit_for_review(tid, actor="worker_course")

        rc, out, err = run_cli(["task", "loop-status", tid])
        assert rc == 0, err
        assert "team_loop:" in out
        assert "phase: reviewing" in out
        assert "next_owner: review_course" in out

        tasks.review_flow(
            tid,
            outcome="reject",
            actor="review_course",
            review_reason="changes_requested",
            required_fix=["add manifest evidence"],
            blocking_files=["manifest.csv"],
        )

        rc, out, err = run_cli(["task", "loop-status", tid])
        assert rc == 0, err
        assert "phase: team_repair_needed" in out
        assert "cycle_count: 1" in out
        assert "next_owner: worker_course" in out
```

**Step 2: Run failing test**

```bash
pytest -q tests/integration/test_loop_engineering_flow.py
```

Expected: fails until earlier tasks are implemented.

**Step 3: Fix wiring only**

No new behavior here. Fix narrow CLI/store wiring defects only.

**Step 4: Run integration test**

```bash
pytest -q tests/integration/test_loop_engineering_flow.py
```

Expected: pass.

**Step 5: Commit**

```bash
git add tests/integration/test_loop_engineering_flow.py
git commit -m "Verify loop engineering flow end to end

The smoke test proves both layers: a builder task can record agent-loop
checker evidence, and a workflow-backed curriculum task can expose the
team-loop review/repair phase without adding a second workflow engine.

Confidence: medium
Scope-risk: moderate
Tested: pytest -q tests/integration/test_loop_engineering_flow.py"
```

## Task 11：最终验收

**Files:**
- No planned edits.

**Step 1: Run targeted tests**

```bash
pytest -q tests/unit/test_agents_identity.py -k loop
pytest -q tests/unit/test_store_loop_runs.py
pytest -q tests/unit/test_runtime_loop_preflight.py
pytest -q tests/unit/test_runtime_loop_specs.py
pytest -q tests/unit/test_runtime_loop_runner.py
pytest -q tests/unit/test_commands_task.py -k loop
pytest -q tests/unit/test_store_tasks_flow.py -k loop_evidence
pytest -q tests/unit/test_store_team_loop_account.py
pytest -q tests/unit/test_task_publish_render.py -k loop
pytest -q tests/integration/test_loop_engineering_truth_contract.py
pytest -q tests/integration/test_loop_engineering_flow.py
```

Expected: all pass.

**Step 2: Run existing gate regression tests**

```bash
pytest -q tests/integration/test_e2e_full_workflow.py
pytest -q tests/unit/test_store_tasks_flow.py
pytest -q tests/unit/test_commands_task.py
pytest -q tests/unit/test_task_publish_gate.py
pytest -q tests/unit/test_task_publish_render.py
pytest -q tests/unit/test_store_team_loop_account.py
```

Expected: all pass.

**Step 3: Run full suite if time allows**

```bash
pytest -q
```

Expected: all pass.

**Step 4: Manual CLI smoke**

```bash
PYTHONPATH=src python3 -m eduflow.cli task dispatch worker_builder "Loop smoke repair" \
  --stage builder \
  --owner worker_builder \
  --by manager \
  --workspace-mode shared

PYTHONPATH=src python3 -m eduflow.cli task loop-check T-<id>
PYTHONPATH=src python3 -m eduflow.cli task loop-status T-<id>
PYTHONPATH=src python3 -m eduflow.cli task get T-<id>
PYTHONPATH=src python3 -m eduflow.cli reidentify manager
PYTHONPATH=src python3 -m eduflow.cli reidentify worker_builder
```

Expected:

- `loop-check` creates or appends a loop run.
- `task get` shows loop summary fields.
- `task loop-status` shows both `agent_loop` and `team_loop` for task ids.
- `$EDUFLOW_STATE_DIR/loop_runs/<loop_id>/cycle-001-checker.txt` exists.
- Task `status`, `verdict`, and `closeout_status` are not promoted by loop pass.
- Running agents can be reidentified so they pick up `eduflow.toml` loop instructions.

## 上线路线

### Phase 0.5：派工路径和 agent 采用对齐

先完成 Task 0.5，再期待 loop 被真实使用。

必须建立的操作规则：

```text
formal builder loop = task dispatch creates T-id + send notifies worker_builder
```

对于需要 loop 验证的临时 builder repair，manager 必须先创建正式 builder task：

```bash
task dispatch worker_builder "<title>" --stage builder --owner worker_builder --workspace-mode shared --by manager
send worker_builder manager "T-<id>: <title>" 高
task loop-check T-<id> --background
```

这一步解决 `eduflow send` 和 `eduflow task dispatch` 的断层：前者能通知 worker，但没有 task id；后者能创建 task row，但不能替代 worker-facing instruction。

### Phase 1：Agent Evidence Loop

完成 Tasks 0-7，然后跑 Tasks 10-11 中的 agent-loop 部分。

operator 使用：

```bash
task loop-check T-123
task loop-status T-123
```

这一步让 EduFlow 有一个可持久化的单 agent 检查循环，但不做自动改动。

### Phase 2：Team Loop Read Model

完成 Task 8，然后跑 Tasks 10-11 的完整双层 smoke。

operator 使用：

```bash
task loop-status T-123
```

它会从现有 task truth 推导协作协议阶段、下一责任人、返修轮次和卡点。

### Phase 3：候选 workflow 文档

完成 Task 9，让 manager 学会使用 builder-stage code repair 和 team collaboration loop 的 workflow candidates。

### Phase 4：manager 中介的返修节奏

使用命令打印出的 handoff packet。manager 手动转发给 `worker_builder`，builder 修复，manager 再跑 `loop-check`。

### Phase 5：worktree 执行隔离

只有 Phase 1 证明有用后，再加入 worktree preparation：

- 复用现有 `workspace_mode=worktree`。
- 记录 branch/base commit/diff evidence。
- 暂不接 container integration。

### Phase 6：可选自动化

只有 read/ack/completion contracts 足够可靠后再做：

- 添加 `--send-builder`。
- `same_failure_repeated` 后拒绝 auto-send。
- 仍然不 auto-deliver。

### Phase 7：课程和题库 loop specs

只有 `code-repair` 证明有用后，再加入非 builder 的 deterministic specs：

- qbank 的 `manifest-check`：
  - manifest row count 和 file count 一致。
  - required columns 存在。
  - required cells 非空。
- curriculum 的 `syllabus-coverage-check`：
  - 每个 syllabus topic 都有 required files。
  - 没有重复 topic ids。
  - required frontmatter keys 存在。

这里不加主观质量 loop。可读性、教学质量、内容真伪仍然需要 reviewer authority。

## 风险与控制

- 风险：Loop 变成另一套 truth source。
  控制：task row 是当前真相；loop archive 只存证据。

- 风险：Team Loop 变成第二套 workflow engine。
  控制：`team_loop_account` 只读，从 task events/workflow_id 推导。

- 风险：resident agents 不知道 loop 存在，所以功能没人调用。
  控制：Task 0.5 更新 canonical `eduflow.toml` agent notes，并要求 `reidentify`。

- 风险：临时 `send` repair 没有 `task_id`，`loop-check` 无法挂证据。
  控制：Phase 0.5 要求 loop-verified builder work 先 formal `task dispatch`。

- 风险：Loop pass 绕过 review/closeout。
  控制：characterization tests，并禁止改 status/verdict/closeout fields。

- 风险：执行 agent 自检被误当成正式验收。
  控制：task event 和 loop summary 明确区分 `self_check`、`review_check`、`manager_closeout`。

- 风险：operator 每轮都开新 run，导致 stop rules 失效。
  控制：`loop-check` 默认复用 active run；`--new-run` 必须显式传。

- 风险：shared workspace 污染证据。
  控制：preflight 记录 workspace mode 和 dirty state；repair handoff 打印 shared risk。

- 风险：builder 为了过检查弱化测试。
  控制：v1 handoff red line；如果真实出现，再加 diff scanner。

- 风险：内容团队误用 code loop 做主观 review。
  控制：v1 spec 只允许 `stage=builder`。

- 风险：checker 卡住。
  控制：per-command timeout、terminal `failed` status、manager-driven checks 使用 `--background`。

- 风险：loop evidence 在 manager 主卡片面不可见。
  控制：Task 7 包含 `task_publish_render.py`。

- 风险：compaction 后 memory 丢 loop 上下文。
  控制：capsule refresh 从 task row 读取 loop fields。

- 风险：Team cycle 机械计数，但漏掉人的协议漂移。
  控制：v1 保守报告 phases 和 repeated repair cycles；manager 手动 crystallize protocol fixes。

- 风险：v1 只覆盖 builder，被认为和课程主业务无关。
  控制：Phase 7 在 v1 证明有用后加入 qbank/curriculum deterministic specs。

## 完成标准

- `task loop-check` 可以创建或追加 active loop run。
- `eduflow.toml` 明确教 manager 和 worker_builder 什么时候使用 loop-check。
- `task loop-status` 和 `task loop-list` 可以查看已有 agent loop evidence。
- `task loop-status <task_id>` 会打印推导出的 `team_loop` 区块。
- `team_loop_account.build()` 能从现有 task truth 推导 phase、cycle count、next owner、recommended action。
- `task loop-status` 能分开显示 self-check、review-check、manager closeout。
- Loop artifacts 持久化在 `$EDUFLOW_STATE_DIR/loop_runs/`。
- Flow tasks 显示 compact loop summary fields。
- Loop-only task events 保持 internal，不直接当正式交付播报。
- manager-facing task render 在有 loop evidence 时显示 compact loop summary。
- Memory capsules 包含 loop blockers/evidence refs。
- `evidence-explain` 只把 loop evidence 当 supporting evidence。
- Loop pass 永远不改变 task delivery、verdict、closeout fields。
- self-check pass 永远不等于 review-check pass，也不等于 manager closeout。
- repeated failure 和 regression stop rules 有测试。
- workspace preflight 记录 shared/dirty workspace risk。
- integration smoke 通过。
- 现有 full workflow closeout test 仍然通过。
- 不新增 dependencies。
