# 2026-06-21 EduFlow Team Overnight Gap 维修任务包

## 目标

把 `2026-06-21-igcse-overnight-monitor-gap-note.md` 中的 127 条监控 gap，从流水账整理成可并行维修的任务包。

核心判断：

- 昨晚不是 127 个独立 bug，而是 8 条系统链路反复掉线。
- 最重要的不是继续给 manager 写更长提示词，而是把已有 workflow、task、inbox、runtime、health 变成硬约束。
- 优先修“链条自动闭环”，再修“外显好看”。否则消息会继续看起来热闹，但实际状态不同步。

## 总体优先级

### P0：先修会让整条链停住或误 closeout 的问题

- Workflow 没有硬挂载，导致 `igcse-subject-launch` 只停留在口头协作。
- 消息入口读/未读/ACK/执行分裂，导致 verdict、完工、返修没有变成动作。
- Task truth 与群消息/status 漂移，导致 PASS、review、closeout 不能自动反写。
- Runtime fallback 不可靠，429/Qoder quota 后 pane ready 但 agent 不可用。

### P1：修会导致夜间运行反复需要人盯的结构问题

- Router/watchdog/hermes flapping 和 health 误判。
- 学科续航/轮转策略缺失，manager 一没新指令就停，或反复 Physics。
- Artifact verifier 缺失，worker 自检和真实文件不一致。
- QBank 状态不可见且 verifier/dedup gate 不稳定。

### P2：修体验和噪声

- 外显卡片重复、状态板口径错、颜色/角色可读性。
- supervisor 对已完成但未 ACK 的旧消息持续升级。

## 问题域归类

### A. Workflow 没强制执行

对应 gap：

- 19, 20, 24, 26, 54, 56, 58, 59, 61, 62, 68, 69, 72-77, 95, 97, 101-118

典型症状：

- agent 说“按 workflow”，但 task 没有 `workflow_id` 或 gate state。
- worker 完工后没有进入 review queue。
- review PASS 后 task verdict 仍 pending。
- package PASS 被 manager 推成 subject closeout。
- `manager-closeout` 只支持 subject，不支持 batch/package closeout。

根因：

- `docs/workflows/igcse-subject-launch` 已经有 gate 文档，但 task 状态机没有强制使用这些 gate。
- task API 具备雏形：`dispatch`、`submit-review`、`assign-reviewer`、`review`、`manager-closeout`，但缺少“必须走这条路径”的 guard。

### B. 消息处理口不可靠

对应 gap：

- 17, 18, 33, 34, 37, 52, 80, 82-85, 89, 92-94, 102, 104, 106, 116, 121, 124

典型症状：

- `say --to ... --body ...` 被解析成 `agent="--body"`。
- manager 已执行某条高优消息，但 inbox 仍 unread。
- `--no-inject` 高优消息进入 inbox 后没人消费。
- tmux 注入文字停在输入框，没有被 Claude Code 执行。
- 消息多时，worker 做了、manager 没外显，用户看不到反馈。

根因：

- inbox message、pane injected prompt、chat card、status/log 不是同一个状态机。
- read / ack / completed / reconciled 语义不够清楚。

### C. Task truth / Status truth / Log truth 漂移

对应 gap：

- 33, 35, 38, 57, 61, 68, 72-77, 83, 92, 93, 108, 114

典型症状：

- 群里 closeout，task 仍 `submitted_for_review`。
- worker live pane 在修，status 还写旧阶段。
- manager 声称已派 worker，但 inbox 没消息。
- review_course 给 PASS，review queue 仍 awaiting review。

根因：

- 事件识别依赖自然语言和手工命令，没有把关键日志映射到 task transition。
- `task_event_scanner` 能发现一部分异常，但推荐动作经常不精确，且不会自动应用安全修正。

### D. Runtime / 模型 / Provider fallback 不可靠

对应 gap：

- 48, 60, 63, 65-67, 71, 86, 96, 98, 119-127

典型症状：

- Qoder `FORBIDDEN code=112` 后 manager 只会说等充值或人工兜底。
- 429 后没有自然切模型。
- runtime-status 写 DeepSeek/qwen_plus，但 live tmux env 不是。
- 切换后 pane ready，但 inbox 仍未读，review_course 卡在 interrupted prompt。
- fallback 切到同额度池，仍然 429。

根因：

- runtime guard 只证明进程 ready，不证明 agent operational。
- health 展示的 runtime 与 live process env 没有强一致校验。
- 缺少一键 runtime switch CLI 和 post-switch smoke。

### E. Router / Watchdog / Hermes / Health 视图分裂

对应 gap：

- Gap A, Gap B, 27, 28, 38, 40, 42, 53, 55, 81, 87, 122, 125

典型症状：

- router alive-but-flapping：subscribe -> catchup -> idle exit -> respawn。
- 多个 router entrypoint 竞争。
- `eduflowteam down router` 实际 team down。
- health 说 tmux session down，但系统 tmux 能看到 pane。
- supervisor-check 报 hermes down，health 又显示 router/watchdog alive。

根因：

- daemon health 只有 alive/dead，缺少 flapping / drift / inconsistent。
- tmux socket/path/import path 没展示，导致同一 session 多视图。
- daemon 控制命令语义不够安全。

### F. 学科续航与轮转策略缺失

对应 gap：

- 32, 36, 44-46, 54, 59, 61, 79, 88, 95, 97, 99, 113

典型症状：

- batch closeout 后 manager 等老板下一步。
- Physics 连续 T-11 到 T-18，其他 IGCSE 学科没进入轮转。
- 用户目标变化后，manager 仍按旧目标滚动。

根因：

- subject backlog / candidate pool 没有成为 manager 默认输入。
- closeout 后没有 `next_batch_continuation_gate` 和 `select_next_subject`。
- waiting for user 与 safe read-only/default workflow 没有区分。

### G. Artifact verifier / 内容质量 gate 不够硬

对应 gap：

- 25, 49-51, 64, 78, 101-103, 109-112, 115, 118

典型症状：

- worker 自检 11/11 pass，机器统计只有 4/11。
- orphan 清理误删有效 QQL。
- Chemistry 旧分片与新小包混在一起。
- subject inventory / manifest 无法证明横向总量。
- 小包 pass 被误当成整科 pass。

根因：

- 复核仍靠自然语言报告，缺少可复现 verifier。
- orphan、difficulty、ID mapping、manifest path 没有统一检查命令。

### H. QBank 可见性与 apply 安全

对应 gap：

- 16, 33-35, 37, 39, 41, 43, 90

典型症状：

- worker_qbank 已产出 report，但用户看不到反馈。
- `qbank_verify.py` 硬编码学科，漏 Economics/Business。
- dedup dry-run 被误判，map 方向/ID schema 不稳。
- apply 前缺 review gate 和明确授权。

根因：

- QBank 没有自己的 task lifecycle。
- verifier 和 dedup plan 没有进入 workflow gate。

### I. 外显噪声与状态板质量

对应 gap：

- 21, 23, 90-92, 100, 105, 107

典型症状：

- worker_course 三条相同完成消息。
- 状态板写错四科学科名单。
- 外显状态落后 live pane。
- auto_ops/worker_course/review_course 色彩和角色不够区分。

根因：

- task event publish 缺少短窗去重。
- status snapshot 没有统一生成源。

## 并行维修任务包

### 包 0：Workflow 强制挂载与 gate 状态机

优先级：P0

目标：

- 把 `igcse-subject-launch` 从文档 workflow 升级为 task 强制 gate。
- IGCSE 学科任务必须有 `workflow_id`，并能显示当前 gate。
- package/batch closeout、subject closeout 分开。

主改文件：

- `src/eduflow/commands/task.py`
- `src/eduflow/store/tasks.py`
- `src/eduflow/store/task_event_scanner.py`
- `docs/workflows/igcse-subject-launch/*`
- `tests/unit/test_commands_task.py`
- `tests/unit/test_store_tasks_flow.py`

建议实现：

1. 新增/完善 `task workflow-status <task_id>` 或在 `task get` 中显示 gate。
2. `task dispatch` 对 `stage=curriculum` + IGCSE 标题强制要求 `--workflow igcse-subject-launch`，或自动补齐并打印 warning。
3. `task submit-review` 若 workflow 有默认 reviewer，则自动设置 `reviewer=review_course`；不能生成 `reviewer=-`。
4. `task review --approve/--manager-action/--reject` 必须写入 gate evidence。
5. 新增 `task batch-closeout <id> --actor manager`，避免 batch task 误走 subject closeout。
6. `task manager-closeout` 对 subject closeout 保持严格，需要 subject inventory verifier 通过。
7. `scan-anomalies` 新增：
   - `workflow_mentioned_but_not_mounted`
   - `submitted_for_review_without_reviewer`
   - `review_pass_log_but_task_pending`
   - `package_pass_promoted_to_subject_closeout`

验收：

```bash
pytest tests/unit/test_commands_task.py tests/unit/test_store_tasks_flow.py tests/unit/test_task_event_scanner.py
./scripts/eduflowteam task dispatch worker_course "IGCSE Demo 0000 Batch 1" --stage curriculum --owner worker_course --workflow igcse-subject-launch
./scripts/eduflowteam task get T-XXX
./scripts/eduflowteam task submit-review T-XXX --actor worker_course
./scripts/eduflowteam task review-queue --reviewer review_course
```

边界：

- 不要在这个包里修 runtime、router、QBank dedup。
- 不要修改真实 content 产物。

### 包 1：Inbox / ACK / Reconcile 消息处理口

优先级：P0

目标：

- 解决“消息到了但没消费成动作”“已执行但 inbox 未读/未 ACK”的主问题。
- 给 manager/report 前增加 inbox drain 机制。

主改文件：

- `src/eduflow/commands/send.py`
- `src/eduflow/commands/read.py`
- `src/eduflow/commands/inbox.py`
- `src/eduflow/commands/say.py`
- `src/eduflow/store/local_facts.py`
- `src/eduflow/store/task_event_scanner.py`
- `tests/unit/test_commands_messaging.py`
- `tests/unit/test_commands_say.py`

建议实现：

1. 增加 `read --ack completed` / `read --ack reconciled`，help 与实现对齐。
2. 增加 `inbox reconcile <msg_id> --evidence-log <log_id>` 或最小版本：`read <msg_id> --ack reconciled`。
3. supervisor 对 “已有满足条件的 log/status 但 inbox unread” 降级为 `read_state_desync`。
4. manager 高优消息在 report 前必须提示 `inbox drain required`。
5. `--no-inject` 高优消息应进入一个 `requires_polling` 状态，supervisor 能区分“静默待消费”与“阻塞未读”。
6. `tmux inject` 不作为成功证据，send 后返回 message id，后续以 read/ack 为准。
7. `say --to ... --body ...` 参数解析要么兼容正确记录 sender，要么明确报错，不允许 `agent="--body"`。

验收：

```bash
pytest tests/unit/test_commands_messaging.py tests/unit/test_commands_say.py tests/unit/test_local_facts.py
./scripts/eduflowteam send manager codex "测试高优消息" 高 --no-inject
./scripts/eduflowteam inbox manager
./scripts/eduflowteam read <msg_id> --ack reconciled
./scripts/eduflowteam task supervisor-check --json
```

边界：

- 不要改 task transition 规则，那是包 0/2。
- 不要改 router subscribe。

### 包 2：Task truth 自动反写与 manager panel

优先级：P0

目标：

- 将自然语言 PASS / task_completed / worker started 等事件反写为结构化 task truth，或至少生成准确 manager action。
- 减少 Codex 手动 `task review --approve` / `assign-reviewer`。

主改文件：

- `src/eduflow/store/task_event_scanner.py`
- `src/eduflow/store/task_publish_gate.py`
- `src/eduflow/store/task_publish_render.py`
- `src/eduflow/commands/task.py`
- `tests/unit/test_task_event_scanner.py`
- `tests/unit/test_task_publish_gate.py`
- `tests/unit/test_task_publish_render.py`

建议实现：

1. 检测 `review_course` 日志中的 `VERDICT: PASS` / `复核完成 — VERDICT: PASS` / `task_completed`，生成 `safe_task_review_approve` action packet。
2. 检测 `worker_course` accepted/started/completed，生成缺失 transition 建议：
   - stage ACK + task queued/assigned -> in_progress
   - completed + no review inbox -> submit-review + assign-reviewer
3. 检测 `manager say closeout` 但 task pending，生成 manager action，不直接静默改。
4. `manager-panel` 优先显示“下一步可执行动作”，不是只罗列异常。
5. 对 `manager_action` / `repair_in_progress` 不再误报为 waiting review。

验收：

```bash
pytest tests/unit/test_task_event_scanner.py tests/unit/test_task_publish_gate.py tests/unit/test_task_publish_render.py
./scripts/eduflowteam task scan-anomalies
./scripts/eduflowteam task manager-panel
./scripts/eduflowteam task manager-actions
```

边界：

- 不要新增 workflow 文档。
- 不要触碰 runtime/watchdog。

### 包 3：Runtime fallback / live env drift / post-switch smoke

优先级：P0

目标：

- 429/Qoder quota/provider unavailable 后自动或半自动切到可用 runtime。
- `pane ready` 必须升级为 `agent operational`。
- runtime-status 与 live tmux env 不一致时标红。

主改文件：

- `src/eduflow/runtime/lifecycle.py`
- `src/eduflow/runtime/config.py`
- `src/eduflow/commands/watchdog.py`
- `src/eduflow/commands/runtime_guard.py`
- `src/eduflow/commands/health.py`
- `src/eduflow/commands/switch.py`
- `tests/unit/test_runtime_lifecycle.py`
- `tests/unit/test_runtime_config.py`
- `tests/unit/test_commands_runtime_guard.py`
- `tests/unit/test_commands_health.py`
- `tests/unit/test_commands_switch.py`

建议实现：

1. 暴露正式 CLI：`eduflowteam runtime switch <agent> <runtime> --reason ...` 或扩展 `switch`。
2. runtime switch 后执行 smoke：
   - live env 与 env_profile 对齐；
   - pane 不在 interrupted input；
   - 最新 high priority inbox 被消费或有明确 nudge；
   - 可选最小 API 成功标记。
3. health JSON 输出：
   - selected runtime
   - live env model/base url
   - drift fields
   - import path `eduflow.__file__`
4. runtime guard 对 `usage allocated quota exceeded`、`FORBIDDEN code=112`、`quota exceeded` 统一归为 fallback signal。
5. fallback 链优先跨 provider，避免 qwen_plus 与 primary 同池循环。

验收：

```bash
pytest tests/unit/test_runtime_lifecycle.py tests/unit/test_runtime_config.py tests/unit/test_commands_runtime_guard.py tests/unit/test_commands_health.py
./scripts/eduflowteam health --json
./scripts/eduflowteam runtime-guard --json
```

边界：

- 不要改 Feishu router。
- 不要改 task workflow gate。

### 包 4：Router / Watchdog / Hermes / Health 可靠性

优先级：P1

目标：

- 把 alive/dead 升级成 stable/flapping/drift/inconsistent。
- 修复 daemon 控制命令的危险语义。
- 让 health/supervisor/tmux 视图一致或明确标注不一致。

主改文件：

- `src/eduflow/commands/router.py`
- `src/eduflow/commands/watchdog.py`
- `src/eduflow/commands/up.py`
- `src/eduflow/commands/down.py`
- `src/eduflow/commands/health.py`
- `src/eduflow/runtime/watchdog.py`
- `src/eduflow/runtime/tmux.py`
- `src/eduflow/feishu/subscribe.py`
- `src/eduflow/feishu/catchup.py`
- `scripts/hermes-supervisor-loop.sh`
- `tests/unit/test_runtime_watchdog.py`
- `tests/unit/test_commands_up_down.py`
- `tests/unit/test_feishu_subscribe.py`
- `tests/unit/test_feishu_catchup.py`

建议实现：

1. health 展示最近 N 次 router respawn、idle exit、catchup count。
2. router idle threshold 区分“低消息量正常静默”和“subscribe 真 stall”。
3. pid file 校验启动命令来源，发现不同 entrypoint 报 `router_entrypoint_drift`。
4. 新增安全命令：`eduflowteam daemon restart router --dedupe`，或让 `down router` 明确拒绝。
5. health 输出 tmux socket/path/user，底层 tmux 可见但内部不可见时标 `tmux_probe_inconsistent`。
6. hermes-supervisor 纳入主 health。

验收：

```bash
pytest tests/unit/test_runtime_watchdog.py tests/unit/test_commands_up_down.py tests/unit/test_feishu_subscribe.py tests/unit/test_feishu_catchup.py
./scripts/eduflowteam health --json
./scripts/eduflowteam task supervisor-check --json
```

边界：

- 不要改 agent runtime fallback。
- 不要改 workflow/task 状态机。

### 包 5：IGCSE subject backlog / 续航 / 轮转

优先级：P1

目标：

- manager 不再“一没定就停”。
- subject closeout 后能选择下一批或下一学科。
- Physics 不再无限占用 subject-launch。

主改文件：

- `src/eduflow/store/tasks.py`
- `src/eduflow/commands/task.py`
- `src/eduflow/store/task_event_scanner.py`
- `docs/workflows/igcse-subject-launch/checklist.md`
- `tests/unit/test_store_tasks.py`
- `tests/unit/test_commands_task.py`

建议实现：

1. 扩展 `task subject-inventory`：
   - subject slug/code
   - outline topic count
   - manifest covered count
   - closeout status
   - next action
   - next candidate rank
2. 新增 `next_batch_continuation_gate`：
   - latest batch delivered + subject incomplete + inbox empty => recommend next batch.
3. 新增 `select_next_subject`：
   - 排除已完整 closeout subject；
   - 优先有资产但未 closeout 的学科；
   - 避免同一学科重复。
4. manager-panel 对“无下一步”显示 safe read-only/default workflow，而不是 idle。

验收：

```bash
pytest tests/unit/test_store_tasks.py tests/unit/test_commands_task.py tests/unit/test_task_event_scanner.py
./scripts/eduflowteam task subject-inventory
./scripts/eduflowteam task manager-panel
```

边界：

- 不要做真实内容生产。
- 不要自动 apply QBank。

### 包 6：Artifact verifier / subject closeout gate

优先级：P1

目标：

- 用机器可复现检查替代 worker 自检。
- 防止小包 PASS 被误当整科 PASS。
- 防止 orphan 清理误删有效 QQL。

主改文件：

- 可新增 `src/eduflow/store/subject_verifier.py`
- `src/eduflow/store/tasks.py`
- `src/eduflow/commands/task.py`
- `scripts/qbank_verify.py` 只读部分可共用 subject discovery
- `tests/unit/test_store_tasks.py`
- 新增 `tests/unit/test_subject_verifier.py`

建议实现：

1. 新增 subject verifier：
   - topic count
   - QA/items/QQL count
   - per-topic difficulty distribution
   - Question ID bidirectional mapping
   - manifest path
   - orphan candidates with evidence
2. Orphan 清理策略改成 quarantine-first，不直接删除。
3. subject closeout gate 必须读取 verifier 结果。
4. 对旧分片 `-s2/-s3` 等产物，输出 `legacy_fragment_present`，不直接混入通过。
5. package verifier 和 subject verifier 分开，避免 scope 混淆。

验收：

```bash
pytest tests/unit/test_subject_verifier.py tests/unit/test_store_tasks.py
./scripts/eduflowteam task subject-inventory
```

边界：

- 不要修改 content 文件。
- 不要做 QBank dedup apply。

### 包 7：QBank lifecycle / verifier / dedup gate

优先级：P1

目标：

- QBank 状态可见。
- verifier 自动发现新闭环学科。
- dedup/import 必须 review gate + 明确授权。

主改文件：

- `scripts/qbank_verify.py`
- `src/eduflow/store/tasks.py`
- `src/eduflow/commands/task.py`
- `src/eduflow/store/task_event_scanner.py`
- `tests/unit/test_commands_messaging.py`
- 可新增 `tests/unit/test_qbank_verify.py`

建议实现：

1. `qbank_verify.py` 自动发现 `content/igcse-*`，不硬编码 SUBJECTS。
2. 输出 compact summary JSON，避免大输出堵消息口。
3. 新增 qbank task state：
   - scan
   - issue_fix
   - reverify
   - ready_for_import
   - needs_review
   - needs_user_authorization
4. dedup v3.2 apply 前必须有 review_course PASS 和用户/manager 授权。
5. manager-panel 必须展示 QBank 最近报告状态。

验收：

```bash
pytest tests/unit/test_commands_messaging.py
python3 scripts/qbank_verify.py --content-dir content --json
./scripts/eduflowteam task manager-panel
```

边界：

- 不要自动修改题库内容。
- 不要把 dedup apply 和 verifier 改在一个 PR/窗口里。

### 包 8：外显去重 / 状态板 / 卡片视觉

优先级：P2

目标：

- 降低群里重复消息和错误状态板。
- 用户能一眼看见当前真实状态，而不是看到多条互相冲突的卡片。

主改文件：

- `src/eduflow/store/task_publish_gate.py`
- `src/eduflow/store/task_publish_render.py`
- `src/eduflow/feishu/cards.py`
- `src/eduflow/commands/say.py`
- `tests/unit/test_task_publish_gate.py`
- `tests/unit/test_task_publish_render.py`
- `tests/unit/test_feishu_cards.py`
- `tests/unit/test_commands_say.py`

建议实现：

1. 同一 `task_id + stage + normalized_content` 60-120 秒内只发一条用户可见卡。
2. `visible_truth_snapshot` 由 task/status/artifact evidence 生成，不允许手写错学科名单。
3. agent card color 固化：
   - manager blue
   - worker_course purple
   - review_course green
   - auto_ops red
   - worker_builder orange
   - anna yellow
   - worker_qbank 单独设 turquoise/grey，避免和 course 混。
4. manager 状态板必须附 source：task id / subject inventory / qbank report path。

验收：

```bash
pytest tests/unit/test_task_publish_gate.py tests/unit/test_task_publish_render.py tests/unit/test_feishu_cards.py tests/unit/test_commands_say.py
```

边界：

- 不要改 message ACK 语义。
- 不要改 workflow gate。

## 推荐开窗方式

### 第一批同时开 4 个窗口

窗口 1：包 0 Workflow 强制挂载

- 这是主线，优先级最高。
- 先让 IGCSE 任务都能走 formal gate。

窗口 2：包 1 Inbox / ACK / Reconcile

- 解决消息入口不可靠。
- 与包 0 有交叉，但主改文件不同。

窗口 3：包 3 Runtime fallback

- 独立于内容和 workflow。
- 先把 429/Qoder quota 的自动恢复打牢。

窗口 4：包 4 Router / Watchdog / Health

- 独立修 daemon 和 health 视图。
- 注意不要和包 3 同时大改 `health.py`；如果冲突，包 3 只改 agent runtime health，包 4 改 daemon health。

### 第二批开 3 个窗口

窗口 5：包 2 Task truth 自动反写

- 等包 0 的 gate 字段基本定下来后做更稳。

窗口 6：包 5 学科续航与轮转

- 依赖包 0 的 workflow gate，但可以先做 subject inventory 只读扩展。

窗口 7：包 7 QBank lifecycle

- 可以独立做 verifier 自动发现和 compact report。

### 第三批收尾

窗口 8：包 6 Artifact verifier

- 最好在包 0/5 明确 subject/batch closeout 边界后做。

窗口 9：包 8 外显去重与状态板

- 最后修体验，避免前面状态字段还没稳定时反复改 render。

## 包之间的冲突提醒

- 包 0 和包 2 都会碰 `task_event_scanner.py`，先由包 0 定 gate 字段，包 2 再补事件识别。
- 包 3 和包 4 都会碰 `health.py`，建议约定：包 3 负责 agent runtime drift，包 4 负责 daemon/tmux drift。
- 包 5 和包 6 都会碰 subject inventory，建议包 5 先做“读目录/统计候选”，包 6 再做“严格 verifier”。
- 包 7 不要自动 apply qbank dedup，只做 scan/report/lifecycle。
- 包 8 最后做，否则去重规则可能遮住前面调试信号。

## 明天维修验收总清单

最低可接受：

- IGCSE 新任务必须显示 `workflow_id=igcse-subject-launch`。
- worker 完工后 reviewer 自动挂载，不再出现 `reviewer=-`。
- review PASS 后 task 不再长期 `verdict=pending`。
- manager closeout 区分 package/batch/subject。
- 429/Qoder quota 后 health 能显示 fallback 可用性和 live env drift。
- `supervisor-check --json` 不再被已执行但 unread 的旧消息长期污染。
- `qbank_verify.py` 能覆盖当前 `content/igcse-*` 学科。

理想状态：

- 一轮 IGCSE 小包可以从 dispatch 到 review PASS 到 batch closeout 全自动结构化闭环。
- manager-panel 能告诉 manager 下一步做什么，不靠 Codex 盯盘。
- 任何 Codex 介入都能对应一个可机器检测的 anomaly，而不是靠人肉判断。
