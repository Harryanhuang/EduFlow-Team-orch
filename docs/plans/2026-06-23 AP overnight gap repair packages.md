# 2026-06-23 AP Overnight Gap 维修任务包

## 目标

把 `2026-06-23-ap-overnight-monitor-gap-note.md` 里的 AP overnight 监控问题，从流水账整理成今天可执行的维修包。

核心判断：

- 昨晚的问题不是“题目做得慢”或“某个 worker 不稳定”，而是生产策略、workflow gate、复盘学习、review 标准、runtime 恢复五条链同时松了。
- 用户真实意图是：先打磨一个完整 AP 学科样板，沉淀 playbook / rubric / validator / failure modes，再进入第二学科加速复制。
- 昨晚实际执行成了多 Unit / 多学科并行凑 package-level approved，且有 builder 越权生产内容、worker_course 重复犯错、review PASS 偏结构化、runtime 假 ready 等红线。
- 更上层的问题是：当前 workflow 还不够智能。它更像 task/review 的流程壳，能挂 gate、派 reviewer、写状态，但还不能自动理解“目标维度、角色边界、产物 schema、质量标准、失败复盘、下一轮继承”这些生产线知识。
- 所以今天不能只补一个 AP workflow 名字；必须先定义 workflow readiness standard，即一条 workflow 什么条件下才算真的搭好了、能复制到下一个学科或任务。
- 今天优先修“以后不会再这么跑偏”的系统约束，再考虑补内容质量。

## 总体优先级

### P0：先修会导致方向跑偏或虚假完成的问题

- Workflow 搭建本身必须有 readiness 标准：未通过 `design -> dry-run -> pilot -> retro -> register -> production use`，不得进入正式批量生产。
- AP 生产策略必须改为 `Subject 1 golden path -> retro -> template/rubric/validator update -> Subject 2 faster run`。
- `worker_builder` 不得参与课程题目内容生产，只能做工具、模板、validator、runtime/workflow 修复。
- Unit/package PASS 不得冒充 full subject closeout 或 qbank-agent ready。
- Review verdict 必须写回 task truth，不能停留在群聊或日志。
- Runtime readiness 必须证明 agent 能消费 inbox 并推进 task/artifact，不能只看 smoke green。

### P1：修会导致同类错误反复出现的问题

- worker_course 每次失败后必须沉淀 lesson learned，并在下一次 brief 前置消费。
- AP item schema、manifest parity、QA 自检、review rubric 必须机器化。
- Workflow gate 必须以文件证据为前置条件，空目录/seed-only 不允许进入 full review handoff。
- stale inbox / stale verdict 必须可标记 superseded，防止恢复后按旧事实回滚。

### P2：修质量与可见性

- 内容质量 PASS 与 schema PASS 拆开。
- Seed / package / subject / qbank-agent ready 四档状态拆开。
- heartbeat / supervisor / evidence-account 自动生成当前 truth packet，减少人工提示词过期。

## 维修总原则

今天的维修不是“把 AP 题目补完”，而是把生产线变聪明。

当前 workflow 的问题：

- 能记录任务，但不能保证任务目标被正确理解。
- 能挂 reviewer，但不能保证 reviewer 的 verdict 写回 task truth。
- 能显示 gate，但不能保证 gate 绑定实际文件证据。
- 能让 manager 继续派单，但不能阻止错误策略，例如没打磨完第一学科就进入下一个学科。
- 能让 worker 返修当前问题，但不能强制把错误沉淀成下一轮 brief / validator / rubric。

维修后的 workflow 应该像生产线，而不是流程清单：

- 进入生产前知道目标维度。
- 派工前知道角色边界。
- 交付前知道产物 schema。
- review 前知道 QA 标准。
- closeout 前知道 scope。
- 失败后知道如何复盘并继承到下一轮。

## 问题域归类

### A. 生产目标被误读

对应 gap：

- 17, 21, 22, 106, 109

典型症状：

- 用户要的是先打磨完整第一学科样板，manager 执行成 AP Calculus AB 多 Unit 深挖 + 其他学科各做 Unit package。
- 最终总结用了 `package-level usable`，但没有足够强调不是 full subject sample。
- manager closeout 追产量信号，而不是样板闭环。

根因：

- manager prompt / workflow 没有把目标维度锁死为 `subject sample first`。
- task 状态里缺少 `unit_seed_ready`、`subject_sample_ready`、`qbank_agent_ready` 的区别。

### B. 角色边界失守

对应 gap：

- 25, 27, 29, 30, 106

典型症状：

- `worker_builder` 被派去生成 AP CSA actual MCQ item 文件。
- builder 的工具/系统建设角色被临时拿来补课程内容，形成红线事件。

根因：

- task assign 没有 role-scope validation。
- manager 在 runtime/worker_course 卡住时缺少合规 fallback 选择。

### C. worker_course 不复盘，同类错误反复出现

对应 gap：

- 5, 10, 14, 28, 40-45, 51-54, 98, 100, 108

典型症状：

- 路径错、manifest/QA 数量错、双正确选项、旧 seed 残留、空产物进入 review handoff。
- 错误被修掉当前 task，但没有更新 worker_course brief、模板、validator、review gate。

根因：

- 没有 `known failure modes` 记忆。
- 没有强制 `lesson learned -> prompt/template/validator/rubric update`。
- worker_course 自检是自然语言声明，不是脚本统计。

### D. Workflow / task truth / review verdict 不同步

对应 gap：

- 1-9, 15-16, 19-20, 31-38, 41-43, 71-74, 101-103

典型症状：

- manager 声称 workflow 已补齐，但 task truth 仍 `no_workflow`。
- review_course 给 PASS/REVISION，task verdict 仍 pending，review queue 仍 awaiting。
- worker 写 `submitted_for_review`，但没有结构化 submit-review。
- operator fallback review 写了 verdict，但 evidence-account 没记 item_count/manifest_rows。

根因：

- 群聊、inbox、review queue、task truth、evidence-account 不是同一个状态机。
- review_course verdict 没有强制调用 task review 写回。

### E. Artifact / manifest / schema gate 不够硬

对应 gap：

- 10, 14, 23, 27-28, 53-54, 68-74, 79, 98-100, 105, 107

典型症状：

- 有 item 文件但缺 qbank-agent 字段。
- manifest 有 SUMMARY 行或总行数与 item 文件口径混乱。
- QA 自检写 8/24/8，实际 7/21/7。
- 内容质量浅，但 review PASS 主要证明结构合格。

根因：

- 没有 AP qbank item schema validator。
- manifest 标准未明确 item-only 还是允许 summary rows。
- review rubric 没拆 schema_pass 与 content_quality_pass。

### F. Runtime 假 ready 与恢复链断裂

对应 gap：

- 29, 33-35, 39, 44-52, 59-67, 70, 75-96

典型症状：

- `runtime verify` 返回 `proved_ready / inbox_state=consumed`，但 tmux 仍卡 Kimi 429，inbox 仍 unread。
- fire/hire、runtime switch、reidentify 后，pane 或 state 短暂不同步。
- supervisor 连续异常 20+，但 health 仍出现 green ready。

根因：

- readiness 只证明 API smoke，不证明业务消费。
- runtime switch 不一定清理旧 retry pane。
- 缺少 `clean-restart + consume-latest-inbox + stale-inbox reconciliation` 一键恢复。

### G. Stale inbox / stale verdict 回滚风险

对应 gap：

- 31, 32, 57-58, 75-76, 79-82, 89-90, 99

典型症状：

- manager inbox 长期 20+ unread，其中旧 verdict 和新事实混在一起。
- task truth 已更新，但旧高优消息仍写过期状态。
- Codex 误投消息到自己 inbox，造成“以为提醒了”的假象。

根因：

- inbox 没有 task version / submit timestamp / superseded 标记。
- send 命令位置参数容易误用，回显不够防错。

## 今天维修任务包

### 包 0：Workflow readiness standard，把 workflow 从流程壳升级为智能生产线

优先级：P0

目标：

- 定义“一条 workflow 什么叫搭好了”。
- 以后新学科、新课程线、新任务线不能边生产边临时补 workflow。
- AP workflow 上线前必须先通过 readiness 标准。

建议改动：

1. 新增 `workflow readiness standard` 文档，定义 workflow 必备组件：
   - README
   - roles
   - trigger
   - checklist
   - handoff-template
   - task mount rule
   - review gate
   - artifact verifier
   - evidence-account mapping
   - closeout target
   - retro / lesson learned gate
2. 新 workflow 生命周期固定为：
   `design -> dry-run -> pilot -> retro -> register -> production use`
3. `workflow register` 或等价流程必须检查：
   - workflow_id 已注册。
   - task create/dispatch 能挂载该 workflow。
   - reviewer 能收到 review queue。
   - verdict 能写回 task truth。
   - evidence-account 能读取关键证据。
   - closeout target 不会被误升级。
4. 新 workflow 必须先跑一个 pilot：
   - 只选一个最小 subject/task。
   - 跑完输出 playbook。
   - 跑完输出 failure modes。
   - 修正 brief/rubric/validator 后，才允许进入第二 subject/task。
5. manager 不得口头声明不存在的 workflow_id；若 registry 没有该 workflow，task dispatch 应阻止或显式报错。

验收：

```bash
./scripts/eduflowteam workflow list
rg -n "workflow readiness|design -> dry-run -> pilot -> retro -> register -> production use|evidence-account mapping|lesson learned gate" docs src scripts
```

完成标准：

- 能回答：这个 workflow 的目标是什么、谁能生产、谁能 review、产物长什么样、怎么验收、怎么 closeout、失败后怎么进入下一轮。
- AP workflow 未通过 readiness 前，不允许 manager 宣称它已经补齐。

### 包 1：AP 样板制生产策略与状态命名

优先级：P0

目标：

- 把 AP 生产策略从“并行凑 Unit package”改成“先完成一个完整学科样板，再复制到第二学科”。
- 防止 manager 再把 Unit package approved 当 subject sample complete。

建议改动：

1. 新增 AP 生产 playbook 文档，固定流程：
   `Subject 1 golden path -> retro -> update brief/rubric/validator -> Subject 2 run`。
2. manager AP dispatch checklist 增加：
   - 当前唯一激活 subject。
   - 本 subject 完整验收范围。
   - 进入下一 subject 前必须输出 retro/playbook。
3. task/status 增加或约定四档状态：
   - `unit_seed_ready`
   - `unit_package_ready`
   - `subject_sample_ready`
   - `qbank_agent_ready`
4. closeout 文案禁止使用“完成 AP 学科”描述 Unit package。

验收：

```bash
rg -n "Subject 1 golden|subject_sample_ready|unit_package_ready|qbank_agent_ready|seed" docs prompts skills src
./scripts/eduflowteam task get <AP_TASK_ID>
./scripts/eduflowteam task workflow-status <AP_TASK_ID>
```

完成标准：

- manager 的 AP 任务 brief 中能明确写出“当前学科未 subject_sample_ready 前，不启动下一学科 full production”。
- 最终总结模板能区分 Unit/package/subject/qbank-agent ready。

### 包 2：角色边界 guard，禁止 builder 生产课程内容

优先级：P0

目标：

- `worker_builder` 不得成为 `题库生产 / actual MCQ / 课程内容 / item generation` 任务 owner/assignee。
- builder 只能做工具、模板、schema、validator、workflow、runtime 修复。

建议改动：

1. 在 task dispatch/create/assign 层加 role-scope validation。
2. 当标题或 brief 命中以下关键词时拒绝 builder：
   - `题库生产`
   - `actual MCQ`
   - `课程内容`
   - `items`
   - `Unit`
   - `知识点条目生成`
3. 允许 builder 的范围必须显式标记：
   - `tool-only`
   - `template-only`
   - `schema-only`
   - `validator-only`
   - `runtime repair`
4. manager prompt 中加入红线：课程内容只能由 `worker_course` 或课程生产角色承担。

验收：

```bash
./scripts/eduflowteam task dispatch worker_builder "AP Computer Science A Unit 1 题库生产" --stage course
# 期望：拒绝，并提示 builder role-scope violation

./scripts/eduflowteam task dispatch worker_builder "AP item schema validator 修复" --stage engineering
# 期望：允许
```

完成标准：

- 再创建内容生产 task 时，builder 不能被选为 owner/assignee。
- 红线事件能被 supervisor 或 scan-anomalies 检出。

### 包 3：worker_course 复盘学习闭环

优先级：P0

目标：

- 每次 worker_course 出错后，不只返修当前文件，还要把错误沉淀到下一轮生产前置约束。

建议改动：

1. 新增 `worker_course known failure modes` 文件，至少包含：
   - delivery path 错误。
   - manifest rows 与 item files 不一致。
   - QA 自检数字与文件事实不一致。
   - MCQ 双正确/等价选项。
   - qbank-agent schema 缺字段。
   - seed-only 被误当 full unit。
   - submit-review 前无产物。
2. 新增 lesson learned 模板：
   - 失败类型。
   - 触发证据。
   - 当前修复。
   - 下次生产前检查项。
   - 对应 validator/rubric 是否已更新。
3. manager 每次派 worker_course 前必须注入 known failure modes，并要求 ACK。
4. review_course PASS 前必须检查“上一轮失败类型是否复发”。

验收：

```bash
rg -n "known failure|lesson learned|worker_course|failure modes|上一轮失败" docs prompts skills src
```

完成标准：

- 新 AP 任务 brief 中能看到上一轮 failure modes 被消费。
- 任一 REVIEW REQUIRED 后，必须有 lesson learned 记录或 task evidence。

### 包 4：AP item schema、manifest、QA validator

优先级：P0

目标：

- 把 AP 题库提交前检查从自然语言自报改成机器可复现 validator。

建议改动：

1. 新增 AP qbank validator，输入 Unit item 目录，检查：
   - `U*.md` 数量。
   - frontmatter 必填字段：
     `unit/topic/subtopic/knowledge_point/core_concept/exam_pattern/question_type/common_mistake/difficulty/explanation_context`
   - 正文标题：
     `## Options`、`## Answer`、`## Explanation`
   - `Answer` 唯一。
   - manifest item rows 与 item files 一致。
   - SUMMARY rows 是否允许，若不允许则 fail。
   - QA 自检数字与文件事实一致。
2. manifest 标准先定为 item-only：
   - `qa-manifest.csv` 只保留 item rows。
   - 汇总写入 `QA-自检.md`。
3. submit-review 前强制跑 validator。
4. validator 输出写入 task evidence-account。

验收：

```bash
python3 scripts/ap_qbank_verify.py "/Volumes/Halobster/Obsidian Edu/留学公司知识库/01-留学课程通用知识/03-AP知识库/03-学科知识/AP Statistics/02-题库/items/Unit 1"
python3 scripts/ap_qbank_verify.py ".../AP Psychology/02-题库/items/Unit 1"
```

完成标准：

- T-42/T-43/T-44/T-45/T-46 的 validator 能给出结构化报告。
- 有 SUMMARY 行、缺 manifest、QA 数字不一致、缺字段时会 fail。

### 包 5：review verdict 自动写回 task truth

优先级：P0

目标：

- review_course 的 PASS / REVISION REQUIRED / REJECT 不再只存在于日志或群聊。
- review queue 与 task verdict 必须同步。

建议改动：

1. review_course 输出 verdict 时必须调用或触发：
   - `task review <id> --approve`
   - `task review <id> --reject`
   - `task review <id> --manager-action`
2. 增加 anomaly：
   - `review_pass_log_but_task_pending`
   - `revision_required_log_but_task_pending`
   - `review_queue_contains_task_with_authoritative_verdict`
3. manager closeout 前必须检查 task verdict，不接受群聊 PASS。
4. review fallback verdict 必须写入 evidence packet：
   - item_count
   - manifest_rows
   - qa_path
   - manifest_path
   - operator_fallback
   - verdict_scope

验收：

```bash
./scripts/eduflowteam task review-queue --reviewer review_course
./scripts/eduflowteam task get T-44
./scripts/eduflowteam task evidence-account --task-id T-44 --json
```

完成标准：

- review_course PASS 后 review queue 不残留该 task。
- task verdict、latest_authoritative_review_verdict、evidence-account 三者一致。

### 包 6：workflow gate 文件证据前置

优先级：P1

目标：

- 没有文件证据时，task 不得进入 `review_handoff_gate / submit_review`。
- seed-only 不得进入 full Unit review handoff。

建议改动：

1. `flow-transition assigned -> in_progress` 不应直接跳到 `review_handoff_gate`。
2. 新增或约定 gate：
   - `production_in_progress`
   - `artifact_ready_gate`
   - `seed_ready_gate`
   - `review_handoff_gate`
3. `submit-review` 前检查：
   - `U*.md > 0`
   - `QA-自检.md` 存在
   - `qa-manifest.csv` 存在
   - validator PASS
   - `full_unit_complete=true`，或明确 `review_scope=seed_only`
4. T-44 这类 seed-only 必须显示 `seed_ready_gate`，不能提示 `submit_review`。

验收：

```bash
./scripts/eduflowteam task workflow-status T-44
./scripts/eduflowteam task submit-review T-45 --actor worker_course
# 若 T-45 仍 0 item，期望拒绝
```

完成标准：

- 空产物 task 无法 submit-review。
- seed-only task 不会被误显示为 full unit handoff。

### 包 7：runtime clean restart 与真实 operational readiness

优先级：P0

目标：

- 修复 `proved_ready` 假阳性。
- runtime 恢复必须证明 agent 能消费指定 inbox、脱离旧 429、产生业务变化。

建议改动：

1. `runtime verify --live-smoke` 增加 hard fail：
   - pane 最近 N 行含 `429`、`usage limit`、`Retrying`、`Interrupted`。
   - 高优 inbox 仍 unread。
   - pane content hash 多轮不变。
2. 新增命令：
   - `runtime clean-restart <agent> --runtime <runtime> --consume-latest-inbox`
3. clean restart 步骤：
   - 中断旧 retry。
   - fire/hire 指定 agent。
   - 确认 pane env 与 declared runtime 一致。
   - reidentify。
   - 消费最新 truth packet。
   - 观察 inbox/read、task/log、artifact 至少一类业务变化。
4. supervisor 连续异常超过阈值时，不再继续展示 green ready，转为 `runtime_repair_required`。

验收：

```bash
./scripts/eduflowteam runtime verify worker_course --json --live-smoke
tmux capture-pane -t EduFlowTeam:worker_course -p -S -80
./scripts/eduflowteam inbox worker_course
```

完成标准：

- live pane 卡 429 时 verify 不得返回 proved_ready。
- clean restart 后必须看到 inbox 被消费或明确 blocker 输出。

### 包 8：stale inbox / stale verdict reconciliation

优先级：P1

目标：

- 防止 manager 恢复后消费旧 verdict / 旧高优消息，把 task truth 回滚。

建议改动：

1. inbox message 增加 task_id、task_version、submit_review_timestamp 或 evidence_version。
2. task truth 更新后，旧消息可标记：
   - `superseded`
   - `stale_verdict`
   - `stale_instruction`
3. manager closeout 只能消费最新 submit-review 之后的 authoritative verdict。
4. `send` 命令增加防错：
   - 支持 `--from` / `--to`。
   - 回显清晰显示 `from -> to`。
   - 若发送到 codex 自己，提示 operator 确认。

验收：

```bash
./scripts/eduflowteam inbox manager
./scripts/eduflowteam task get T-46
```

完成标准：

- T-46 已 approved 后，旧的 “T-46 rejected/缺 manifest” 高优消息不再能驱动 manager 操作。
- send 误投风险显著降低。

### 包 9：内容质量 rubric 与二阶段升级

优先级：P1

目标：

- 让 review_course 不再只给结构 PASS。
- 昨晚产物先标 seed/draft，再做内容升级，不进入 golden。

建议改动：

1. review verdict 拆成：
   - `schema_pass`
   - `content_quality_pass`
   - `qbank_agent_ready`
2. AP 内容质量 rubric：
   - AP 真题风格贴合。
   - 情境真实性。
   - 干扰项诊断质量。
   - 解析教学价值。
   - 认知层级。
   - 非平凡性。
   - 答案唯一性。
   - 难度真实性。
3. 每个 subtopic 至少保留：
   - 1 道基础题。
   - 1 道场景型 / 推理型 / 常见错误诊断题。
4. 解析必须解释为什么错误选项错。

验收：

```bash
rg -n "content_quality_pass|schema_pass|qbank_agent_ready|干扰项|解析教学价值|AP 真题风格" docs prompts skills
```

完成标准：

- review_course 能给出 schema PASS 但 content NEEDS_UPGRADE 的 verdict。
- 昨晚五个 Unit 不再被标为 golden。

## 建议执行顺序

### 第一轮：先封住红线

1. 包 0：Workflow readiness standard，把 workflow 从流程壳升级为智能生产线。
2. 包 1：AP 样板制生产策略与状态命名。
3. 包 2：角色边界 guard。
4. 包 7：runtime clean restart 与真实 operational readiness。

原因：

- 这四个不先修，后面继续生产仍会跑偏、越权或假恢复。尤其是包 0 不修，后面只是继续补单条 workflow，而不是修“搭 workflow 的方法”。

### 第二轮：让链路可验收

1. 包 4：AP item schema、manifest、QA validator。
2. 包 5：review verdict 自动写回 task truth。
3. 包 6：workflow gate 文件证据前置。

原因：

- 这三个决定“完成”到底是不是完成。

### 第三轮：让系统变聪明

1. 包 3：worker_course 复盘学习闭环。
2. 包 8：stale inbox / stale verdict reconciliation。
3. 包 9：内容质量 rubric 与二阶段升级。

原因：

- 这三个修复重复犯错、旧消息回滚和内容浅的问题。

## 今天不建议先做的事

- 不建议直接大规模重写 AP 题目内容。
- 不建议继续扩更多 AP 学科。
- 不建议把昨晚的 Unit package 当 golden 样本。
- 不建议只改 manager prompt，不加 validator / gate / evidence-account。
- 不建议只重启 runtime，不修 `proved_ready` 假阳性。

## 今日成功标准

今天不是以“多产几科”为成功标准，而是以“下一次不会按同样方式失败”为成功标准。

最低成功线：

1. workflow readiness standard 建立：以后 workflow 必须经过 design / dry-run / pilot / retro / register / production use。
2. AP 生产策略固定为先完整学科样板，再复制下一学科。
3. builder 不能再接课程内容生产任务。
4. worker_course 有 known failure modes 和 lesson learned 机制。
5. AP qbank validator 能跑，能抓 manifest/schema/QA 数字问题。
6. review PASS 能写回 task truth。
7. runtime verify 不再对旧 429 pane 给 false ready。
