### 1. AP 生产口头分工已发生但 task/workflow truth 未落地

触发时间：2026-06-23 00:45 CST

触发原因：

- Manager 已在群聊中声明 AP Calculus AB、AP Physics 1、AP Statistics、AP Psychology、AP Computer Science A 已分工，并要求走 workflow/task/review/inbox 链路，但结构化 task truth 中未看到今晚 4-5 个 AP 学科对应的新 task-backed workflow。
- Supervisor 明确报出 `manager_claim_without_task_truth`，认为 manager 群消息声称已派工，但 task/inbox/workflow 没有同范围真实落地证据。
- Manager 后续又说“确认后我立刻建 task 并派工”，与此前“4/5 个学科已派工”的口径不一致。

现场证据：

- `./scripts/eduflowteam task supervisor-check --json` 返回 `health_status=escalated_failure`，`primary_reason=status_surface_truth_lag`，并包含 `manager_claim_without_task_truth`。
- `.eduflow-team-state/facts/logs.jsonl` 中 `log_1782145919739_daf67dfdbe`：manager 声称 AP Calculus AB、AP Physics 1、AP Statistics、AP Psychology 已派工。
- `.eduflow-team-state/facts/logs.jsonl` 中 `log_1782146026186_b1aad8df85`：manager 声称 AP Computer Science A 也已纳入进行中。
- `./scripts/eduflowteam task list` 当前只显示旧任务到 `T-32`，未见今晚 AP 4-5 学科的 task-backed workflow。
- `./scripts/eduflowteam inbox manager` 显示老板刚指定学科的消息仍有未读：`msg_1782146658646_2f5f0742f0` 与 `msg_1782146665445_c70e8c47b4`。
- `./scripts/eduflowteam task review-queue --reviewer review_course` 返回无待 review 任务，说明当前还没有把今晚 AP 学科产出送入 review queue。

介入动作：

- Codex 准备按最低有效力度软提醒 manager：先消费老板指定学科消息，然后把今晚 AP 学科生产补成 task/workflow 可追踪状态；明确每个学科 owner、reviewer、workflow_id、gate，以及下一步 QA/review 入口。

临时结果：

- Gap 已记录；尚未确认 manager 是否完成 task-backed dispatch。

明天修复建议：

- 为 AP 知识库生产新增正式 workflow 模板，例如 `ap-knowledge-base-optimization`，把“学科选择 -> task 创建 -> worker 分配 -> 产物提交 -> QA/review -> closeout”固化成 gate，避免 manager 先口头分工、事后再补 task truth。

### 2. T-33 已创建但未挂 workflow/reviewer

触发时间：2026-06-23 00:51 CST

触发原因：

- Codex 软提醒后，manager 已消费老板最新学科范围消息并创建 `T-33 AP Calculus AB 逐单元题库生产`，但该任务仍是普通 task，没有挂载 `workflow_id`、`workflow_gate` 或 `reviewer`。
- 这会导致后续生产仍可能停留在口头分工和普通任务描述，无法形成“生产 -> QA/review -> closeout”的可验证链路。

现场证据：

- `./scripts/eduflowteam inbox manager` 复查为 no unread，说明 manager 已消费最新消息。
- `./scripts/eduflowteam task get T-33` 显示任务已创建，状态为 `待处理`，assignee 为 `worker_course`。
- `./scripts/eduflowteam task workflow-status T-33` 显示 `workflow_id=-`、`gate=no_workflow`、`gate_status=not_mounted`、`reviewer=-`、`next_action=mount_workflow`。
- `./scripts/eduflowteam task review-queue --reviewer review_course` 返回 no tasks awaiting review。

介入动作：

- Codex 准备继续以最低有效力度提醒 manager：不要重建大计划，只需把 T-33 补挂 `ap-knowledge-base-optimization` 或现有最接近 workflow，设置 reviewer 为 `review_course`，并把当前 gate 明确到 Unit 1 production / QA handoff。

临时结果：

- T-33 已存在，但 workflow truth 仍未合格；需下一轮复查 manager 是否完成挂载或给出可验证替代链路。

明天修复建议：

- `task create` 在 AP 生产语境下应默认拒绝无 workflow/reviewer 的任务，或自动提示使用 `task flow-create/dispatch --workflow ... --stage ... --owner ...`。

### 3. Manager 声称五科 workflow 已补齐但结构化状态仍为 no_workflow

触发时间：2026-06-23 00:56 CST

触发原因：

- Manager 在群聊中声称 AP 五科 task truth 已补齐，`workflow_id=ap-knowledge-base-optimization`，但实际 workflow 列表中没有这个 workflow，T-33 至 T-37 的结构化状态仍然显示 `workflow_id=-`。
- T-33 还从 `进行中` 变为 `已取消`，而 T-34 至 T-37 虽已创建，却都只是普通待处理 task，没有 reviewer、workflow gate 或 review handoff。

现场证据：

- `.eduflow-team-state/facts/logs.jsonl` 中 `log_1782147143699_1952f4f4f3`：manager 声称五科 `workflow_id=ap-knowledge-base-optimization` 已补齐。
- `./scripts/eduflowteam workflow list` 只显示 `igcse-9subject-sprint`、`igcse-item-level-prototype`、`igcse-subject-launch`、`realrun-to-workflow`、`runtime-failover-hardening`，没有 `ap-knowledge-base-optimization`。
- `./scripts/eduflowteam task workflow-status T-33` 显示 `workflow_id=-`、`gate=no_workflow`、`reviewer=-`，且 status 为 `已取消`。
- `./scripts/eduflowteam task workflow-status T-34` 至 `T-37` 均显示 `workflow_id=-`、`gate=no_workflow`、`reviewer=-`。
- AP Calculus AB 目录下当前可见 `02-框架与规划/AP Calculus AB_题库优化版_知识点框架.md`，但没有看到 Unit 1 items/manifest 等题库生产证据。

介入动作：

- Codex 准备升级到结构修复建议：要求 manager 停止声称不存在的 workflow 已挂载，并改用现有 workflow 工具可验证地创建/派发 AP Calc AB Unit 1 的 workflow-backed task；若 AP 专属 workflow 不存在，先明确使用现有最接近 workflow 的临时替代，并把“明天新增 AP workflow 模板”作为系统修复项。

临时结果：

- 五科任务已有普通 task 壳，但仍未达到今晚要求的 workflow/task/review/inbox 可追踪链路；需要继续扶正。

明天修复建议：

- 正式新增并注册 `ap-knowledge-base-optimization` workflow；在 workflow 不存在时，manager 不应报告 `workflow_id` 已补齐，系统应校验 workflow id 是否存在。

### 4. Codex 结构兜底创建 T-39 后发现 manager 已创建 T-38，出现重复任务风险

触发时间：2026-06-23 01:03 CST

触发原因：

- Codex 根据 `T-33/T-34/T-35/T-36/T-37` 均为 `no_workflow` 的证据，创建了 workflow-backed 兜底任务 `T-39 AP Calculus AB Unit 1 题库生产与复核`。
- 随后复查发现 manager 已创建 `T-38 AP Calculus AB 逐单元题库生产`，且 `T-38` 已正确挂载 `igcse-subject-launch`、`reviewer=review_course`，并处于 `review_handoff_gate`。
- 若不收敛，worker_course 可能同时看到 `T-38` 和 `T-39`，造成重复生产或状态分叉。

现场证据：

- `./scripts/eduflowteam task get T-38` 显示 `workflow_id=igcse-subject-launch`、`workflow_gate=review_handoff_gate`、`reviewer=review_course`、`status=in_progress`。
- `./scripts/eduflowteam task get T-39` 显示 Codex 创建的兜底任务也挂载 `workflow_id=igcse-subject-launch`，但仍处于 `dispatch_acceptance_gate`。
- `.eduflow-team-state/facts/logs.jsonl` 中 manager 已声明 `T-33 已取消，T-38 为 workflow-backed 正式任务`。

介入动作：

- Codex 准备将 `T-38` 设为唯一权威 AP Calculus AB Unit 1 生产任务，并取消/标记 `T-39` 为重复兜底任务，避免并行分叉。

临时结果：

- Codex 尝试用 `task update T-39 --status 已取消` 取消重复任务，但系统拒绝 flow task 使用 legacy update；随后已发 manager 指令，要求生产口径只认 `T-38`，忽略 `T-39`，并不要再创建 AP Calculus AB Unit 1 重复任务。
- 后续 patrol 需持续确认 worker_course 是否只围绕 `T-38` 推进，避免 `T-39` 被误消费。

明天修复建议：

- 结构修复前应优先全量扫描最新 task list 和 manager 最近 1-2 分钟日志；系统也应提供“按标题/学科查重后再创建 task”的安全接口。

### 5. T-38 Unit 1 产物落在项目 content 目录，未进入 Obsidian AP 知识库目标目录

触发时间：2026-06-23 01:13 CST

触发原因：

- T-38 已进入 `submitted_for_review`，manager 与 worker_course 均声称 AP Calculus AB Unit 1 已生产完成并提交 review_course，但实际新增 items/manifest 位于 EduFlow-Team-orch 项目内 `content/ap-calculus-ab/...`。
- 用户指定的 AP 知识库交付路径是 `/Volumes/Halobster/Obsidian Edu/留学公司知识库/01-留学课程通用知识/03-AP知识库`；该目录下 AP Calculus AB 当前只看到原有框架、Topic 页面与专题资源，没有 Unit 1 items/manifest/evidence 文件。
- QA 自检与 manager 口径存在数量不一致：QA 自检写“所有 33 个文件”和“Manifest 新增行数：11”，而 manager/worker 口径为 12 subtopics / 36 items / manifest 新增 12 行。

现场证据：

- `./scripts/eduflowteam task workflow-status T-38` 显示 `gate=quality_gate`、`gate_status=awaiting_review_verdict`、`reviewer=review_course`。
- `content/ap-calculus-ab/subtopics/unit1/QA-自检.md` 存在，写明状态为 `submitted_for_review`，但总文件数为 33、manifest 新增行数为 11。
- `content/ap-calculus-ab/qa-manifest.csv` tail 显示 Unit 1 新增行从 `U1.1.1` 到 `U1.4.2`，共 11 行。
- `find /Volumes/Halobster/Obsidian Edu/.../AP Calculus AB` 未发现 `subtopics/unit1`、`qa-manifest.csv` 或 Unit 1 items 文件，只看到框架与 Topic 页面。

介入动作：

- Codex 准备提醒 manager：review_course verdict 必须同时检查内容质量和交付路径；若 review PASS，只能代表项目 content 目录内产物通过，不能直接声明 Obsidian AP 知识库已交付。需要补齐到目标知识库路径或明确标记为“项目内暂存，待同步”。

临时结果：

- T-38 仍在等待 review_course verdict；尚未确认路径问题是否被 review_course 纳入 verdict。

明天修复建议：

- AP workflow 应显式区分 `working_dir` 与 `delivery_dir`，并在 closeout gate 检查目标 Obsidian 知识库路径下的实际产物；manifest/QA 自检数量应由脚本统计，避免口头数量和文件事实不一致。

### 6. T-38 review_course 已给 CONDITIONAL PASS，但 manager/task truth 尚未消费 verdict

触发时间：2026-06-23 01:19 CST

触发原因：

- review_course 已在群聊/日志中给出 T-38 AP Calculus AB Unit 1 复核 verdict：`CONDITIONAL PASS`，但结构化 task truth 仍显示 `verdict=pending`、`gate_status=awaiting_review_verdict`。
- manager inbox 中仍有 review_course 发来的 verdict 消息未读，说明 manager 还没有消费 verdict 并派发返修。
- 若不扶正，manager 可能继续等待或误判为 review 仍未完成，影响 AP Calc AB Unit 1 收口和下一单元推进。

现场证据：

- `.eduflow-team-state/facts/logs.jsonl` 中 `log_1782148629674_d6d9cc2258`：review_course verdict 为 `CONDITIONAL PASS`，内容质量 PASS，但数量一致性与 Obsidian 目标路径交付均需返修。
- `./scripts/eduflowteam task get T-38` 仍显示 `verdict=pending`，`workflow_gate_status=awaiting_review_verdict`。
- `./scripts/eduflowteam inbox manager` 显示 review_course → manager 的 `msg_1782148723439_1c03b7f809` 未读，内容为 T-38 `CONDITIONAL PASS` verdict。

介入动作：

- Codex 准备软提醒 manager：先消费 verdict，再派 worker_course 做两项最小返修：修正 QA 自检数量，并将 Unit 1 产物同步到 Obsidian AP Calculus AB 目标目录；返修后重新 submit-review T-38。

临时结果：

- 待确认 manager 是否消费 verdict、更新 task truth，并派发返修。

明天修复建议：

- review_course 输出 verdict 后，应自动写回 task verdict/gate 或至少触发 manager 必读高优消息；避免 verdict 只存在群聊而 task truth 长时间 pending。

### 7. T-38 返修已落地到 Obsidian，但 task gate 卡在 manager_action

触发时间：2026-06-23 01:23 CST

触发原因：

- worker_course 已报告 T-38 Unit 1 CONDITIONAL PASS 返修完成，且实际 Obsidian 目标目录已出现 Unit 1 items、QA 自检与 `qa-manifest.csv`。
- QA 自检数量已修正为 36 item files + 1 QA = 37 文件，manifest U1 subtopic 12 行。
- 但 T-38 结构化状态仍为 `blocked` / `verdict=manager_action` / `workflow_gate=revision_first`，下一步要求 manager 判断 scope/direction；review queue 为空，说明还没有重新送 review_course。
- manager inbox 仍有 worker_course 返修完成消息未读。

现场证据：

- `./scripts/eduflowteam task workflow-status T-38` 显示 `status=blocked`、`verdict=manager_action`、`next_action=manager_decide_scope_or_direction_before_any_other_action`。
- `./scripts/eduflowteam inbox manager` 显示 `msg_1782148846743_a527d8cdaf` 未读，内容为 T-38 Unit 1 返修完成，但 re-submit 失败，等待经理处理。
- Obsidian 目标目录下已存在 `/AP Calculus AB/02-题库/items/Unit 1/` 的 36 个 item 文件与 `QA-自检.md`。
- Obsidian 目标目录下已存在 `/AP Calculus AB/02-题库/qa-manifest.csv`，tail 显示 U1.1.1 至 U1.4.2 共 12 行。
- Obsidian 目标 `QA-自检.md` 已写明总文件数 37、manifest 新增行数 12。

介入动作：

- Codex 准备提醒 manager：先消费返修完成消息，确认 scope 不变，然后只做一件事：将 T-38 重新送 review_course 复核目标路径与数量一致性；不要 closeout，不要进入 Unit 2。

临时结果：

- 待确认 manager 是否消费返修完成消息并恢复 T-38 review flow。

明天修复建议：

- `manager_action` gate 应提供明确的“返修完成后重新送审”快捷动作，避免 worker 完成返修后因 gate 需要 manager 判断而无法 submit-review。

### 8. T-38 FULL PASS 只存在于日志，task truth 未同步 closeout

触发时间：2026-06-23 01:28 CST

触发原因：

- review_course 已在日志中给出 `T-38 AP Calculus AB Unit 1 返修复审 verdict：FULL PASS`，并声明 `Closeout 完成`。
- 但结构化 task truth 仍显示 `status=submitted_for_review`、`verdict=pending`，review queue 仍列出 T-38，说明 manager 或 review/task 工具尚未消费 FULL PASS。
- 如果不扶正，后续 AP Calculus AB Unit 2 或其他学科会建立在“口头完成但 workflow 未关闭”的不一致状态上。

现场证据：

- `.eduflow-team-state/facts/logs.jsonl` 中 `log_1782149131303_22d7a5c038`：review_course 声明 T-38 Unit 1 返修复审 `FULL PASS`，QA 数量、Obsidian 目标路径、数学/tone/格式抽检均通过，并写明 `Closeout 完成`。
- `./scripts/eduflowteam task get T-38` 显示 `status=submitted_for_review`、`workflow_gate=revision_first`、`workflow_gate_status=revision_priority_active_manager`、`verdict=pending`。
- `./scripts/eduflowteam task workflow-status T-38` 显示 `status=submitted_for_review`、`verdict=pending`、`next_action=manager_decide_scope_or_direction_before_any_other_action`。
- `./scripts/eduflowteam task review-queue --reviewer review_course` 仍显示 T-38 `awaiting review`。

介入动作：

- Codex 准备软提醒 manager：当前唯一真相是“日志 FULL PASS、task truth 未关闭”；请消费 review_course 的 FULL PASS，并用 task/review/closeout 工具把 T-38 从 review queue 中关闭，再同步最小状态包。

临时结果：

- 待确认 manager 是否将 T-38 的 FULL PASS 写回 task truth，并从 review queue 移除。

明天修复建议：

- review_course 的 FULL PASS verdict 应自动触发 task verdict 写回或 manager 必处理 closeout action；review queue 不应在日志 closeout 后继续显示 pending。

### 9. T-38 已 closeout 后，AP 后续队列仍未形成干净 workflow truth

触发时间：2026-06-23 01:33 CST

触发原因：

- T-38 已经被 manager 消费并落到 `delivered / verdict=approved`，review queue 已清空。
- 但 Codex 早先兜底创建的重复任务 T-39 仍处于 `queued`，如果被 worker_course 或 manager 误消费，会重新触发 AP Calculus AB Unit 1 的重复生产。
- manager 选择的其余四科 `T-34 AP Computer Science A`、`T-35 AP Physics 1`、`T-36 AP Statistics`、`T-37 AP Psychology` 仍是 plain task/backlog，没有 `workflow_id`、`reviewer`、`gate` 等结构化字段；下一科若直接开跑，会重演“口头 workflow 已补齐但 task truth 无 workflow”的问题。
- `supervisor-check --json` 仍返回 `health_status=repair_needed`，主因包括 `stale_task_backlog`、`status_surface_truth_lag`、`worker_context_risk`、`manager_idle_too_long`，说明状态面仍存在可见性/同步风险。

现场证据：

- `./scripts/eduflowteam task get T-38` 显示 `status=delivered`、`verdict=approved`。
- `./scripts/eduflowteam task review-queue --reviewer review_course` 显示 `no tasks awaiting review`。
- `./scripts/eduflowteam task list` 显示 `T-39 [queued] AP Calculus AB Unit 1 题库生产与复核`，仍挂 `workflow_id=igcse-subject-launch`。
- `./scripts/eduflowteam task list` 显示 `T-34/T-35/T-36/T-37` 均为 `待处理`，且没有 workflow/reviewer/gate 结构化字段。
- `./scripts/eduflowteam task supervisor-check --json` 返回 `health_status=repair_needed`、`primary_reason=status_surface_truth_lag`，auto summary 包含 `stale_task_backlog` 与 `worker_context_risk`。

介入动作：

- Codex 准备提醒 manager：先清理/隔离 T-39 重复队列；启动下一科前必须用 workflow/task 工具创建或补齐 workflow-backed 权威任务，并明确 reviewer、目标路径、单元范围、QA 标准和 closeout 格式。

临时结果：

- 待确认 manager 是否隔离 T-39，并将下一科 AP Computer Science A 或 AP Calculus AB Unit 2 按 workflow-backed 任务正式启动。

明天修复建议：

- task 系统需要提供“duplicate/superseded”状态或 flow-task 安全取消接口；AP backlog 任务应支持一键升级为 workflow-backed task，避免 manager 只在 desc 里写 workflow 要求而结构化字段为空。

### 10. T-38 Unit 1 通过内容 review，但单题文件缺少题库智能体结构化上下文字段

触发时间：2026-06-23 01:37 CST

触发原因：

- T-38 AP Calculus AB Unit 1 已完成 review_course FULL PASS，并落地为 `delivered / verdict=approved`。
- 抽查 Obsidian 目标目录下的 item 文件后，题目本身数学与格式可用，但单题文件只包含 `id/difficulty/calculator/type` frontmatter、Options、Answer、Explanation。
- 用户今晚目标是为后续题库智能体建设打基础，验收要求包含 Unit/Topic/Subtopic、知识点定义、核心概念、常见考法、易错点、题型方向、难度层级、解析背景等；这些字段没有在单题文件内显式落地。
- 目前 Unit/Topic/Subtopic 主要存在于文件名和 manifest 行中，题库智能体若只读取单题文件，会缺少稳定上下文。

现场证据：

- `find .../AP Calculus AB/02-题库/items/Unit 1 -name 'U*.md' | wc -l` 显示 36 个 item 文件。
- 抽查 `U1.1.1-F.md` 与 `U1.4.2-C.md`：frontmatter 只有 `id`、`difficulty`、`calculator`、`type`，正文为题干、选项、答案、解析，没有显式 Unit/Topic/Subtopic、知识点定义、常见考法、易错点、题型方向或解析背景字段。
- `grep -RIl` 检查 Unit/Topic/Subtopic/知识点/核心概念/常见考法/易错/题型/解析背景等字段，36 个 item 文件没有形成字段级覆盖，主要命中 QA 文件或 manifest 层信息。
- `qa-manifest.csv` 能看到 U1.1.1 至 U1.4.2 的 subtopic 名称，但 item 文件本体缺少可独立消费的结构化上下文。

介入动作：

- Codex 准备提醒 manager：不要把 T-38 Unit 1 返工为大规模内容重写，但下一轮 AP Unit/学科生产必须把题库智能体字段纳入 QA checklist；若继续 AP Calculus AB Unit 2 或切到 AP CSA，单题文件至少应补充 unit/topic/subtopic、knowledge_point、core_concept、common_mistake、exam_pattern、question_type、explanation_context 等字段。

临时结果：

- T-38 Unit 1 仍可作为“题目质量通过”的样本，但作为题库智能体基础标准仅为部分达标；需要下一轮生产验证字段标准。

明天修复建议：

- 制定 AP qbank item schema，并把 schema 校验加入 workflow gate；review_course 的 PASS 应区分“题目质量 PASS”和“qbank-agent schema PASS”，避免二者混在一起。

### 11. 主线可运行但 runtime/健康面仍有红项，存在生产可见性风险

触发时间：2026-06-23 01:43 CST

触发原因：

- T-40 AP Calculus AB Unit 2 已成功创建并进入 `in_progress`，说明 manager 与 worker_course 主线当前可推进。
- 但本轮 `health` 仍返回红项，`supervisor-check --json` 仍显示 `health_status=repair_needed`，主因包括 `worker_context_risk`，同时 runtime readiness 中 worker_course 为 `ready_unproven`、worker_qbank 为 `env_drift`。
- 若后续切到 AP Statistics / AP Psychology 依赖 worker_qbank，或 worker_course 长任务继续推进，当前健康面异常可能导致“群聊口头在动，但实际 pane/inbox/task 状态不同步”的旧问题复发。

现场证据：

- `./scripts/eduflowteam health` 显示 `❌ 3 red check(s)`。
- `health` 中 `runtime operational readiness` 显示 `worker_course: ready_unproven`、`worker_qbank: env_drift`，同时 `anna: pane_missing`、`Luke_recorder: env_drift`。
- `./scripts/eduflowteam task supervisor-check --json` 显示 `health_status=repair_needed`、`primary_reason=worker_context_risk`，auto summary 包含 `worker_context_risk` 与 `manager_recently_active`。
- `.eduflow-team-state/facts/status.json` 显示 manager 已更新为 `T-38 Unit 1 batch closeout 完成；T-40 AP Calc AB Unit 2 生产中`，说明任务主线与健康红项并存。

介入动作：

- Codex 暂不做 runtime 重启或结构修复，避免打断已启动的 T-40 主线；本轮只记录风险，并在后续 patrol 中重点核对 worker_course 是否持续产出、worker_qbank 在切到 Statistics/Psychology 前是否恢复可证明 readiness。

临时结果：

- T-40 主线继续观察；下一轮 patrol 必须复查 `health`、worker_course inbox/log、T-40 task truth、Obsidian Unit 2 产物。

明天修复建议：

- 将 `ready_unproven/env_drift` 与实际任务依赖绑定：当下一任务需要某 agent 时，启动 gate 应先做对应 agent 的 smoke/readiness 证明；否则只把异常埋在 health 输出里，manager 容易忽略。

### 12. T-40 Unit 2 已启动，但 worker/status/产物面暂未同步进度

触发时间：2026-06-23 01:46 CST

触发原因：

- manager 已创建 `T-40 AP Calculus AB Unit 2 题库生产`，task truth 显示 `in_progress`，且 brief 已包含 qbank-agent schema 门槛。
- 但 `.eduflow-team-state/facts/status.json` 中 worker_course 仍显示旧状态 `T-38 Unit 1 已重新提交复核`，没有更新为 T-40 Unit 2 生产中。
- Obsidian 目标目录 `/AP Calculus AB/02-题库/items/` 目前只看到 `Unit 1`，尚未出现 `Unit 2` 目录或临时产物。
- 这可能只是刚启动后的正常延迟，也可能是 worker_course 状态面没有外显生产进展；若持续不更新，会导致 manager 误判“无阻塞”但 monitor 无法确认生产链在动。

现场证据：

- `./scripts/eduflowteam task get T-40` 显示 `status=in_progress`、`workflow_id=igcse-subject-launch`、`reviewer=review_course`、`workflow_next_action=submit_review`。
- `./scripts/eduflowteam task workflow-status T-40` 显示 `gate=review_handoff_gate`、`gate_status=waiting_review_handoff`、`verdict=pending`。
- `./scripts/eduflowteam inbox worker_course` 显示无未读消息，说明 worker_course 已消费或没有待处理 inbox。
- `sed -n '1,260p' .eduflow-team-state/facts/status.json` 显示 worker_course 状态仍停留在 `T-38 Unit 1 已重新提交复核`。
- `find .../AP Calculus AB/02-题库/items -maxdepth 2 -type f` 当前只列出 Unit 1 文件，没有 Unit 2 文件。

介入动作：

- Codex 准备轻量提醒 manager：当前唯一真相是 T-40 task 已 in_progress，但 worker/status/Obsidian 产物面暂未显示 Unit 2 进展；请只回传 T-40 心跳状态包，不要求重启、不要求返工。

临时结果：

- 待确认 manager 或 worker_course 是否更新 T-40 生产心跳，或是否出现 Unit 2 产物 / submit-review。

明天修复建议：

- flow task 进入 `in_progress` 后，应要求 assignee 在 1-3 分钟内写入 `started/current_summary` 或过程心跳；否则 supervisor/monitor 无法区分“刚启动”与“无外显生产进展”。

### 13. 夜间 heartbeat 自动化提示词滞后于当前 T-40 主线

触发时间：2026-06-23 01:56 CST

触发原因：

- Codex 准备创建 35 分钟巡检 heartbeat 时发现当前线程已存在 active heartbeat，不能重复创建。
- 既有自动化仍主要要求检查 `T-38/T-34~T-37`，但当前生产主线已推进到 `T-40 AP Calculus AB Unit 2`，若不更新，后续自动巡检可能继续围绕旧 closeout 和 plain backlog 展开，漏掉 Unit 2 的 QA/manifest/submit-review/verdict/closeout 链路。

现场证据：

- `$HOME/.codex/automations/ap-overnight-monitor-patrol/automation.toml` 显示 `kind=heartbeat`、`rrule=FREQ=MINUTELY;INTERVAL=35;COUNT=15`、`status=ACTIVE`。
- 旧 prompt 写明重点检查 `T-38/T-34~T-37 等 task truth`，没有显式跟进 `T-40 AP Calculus AB Unit 2`。
- 本轮 task truth 显示 `T-40 [in_progress]`、`workflow_gate=review_handoff_gate`、`workflow_next_action=submit_review`、`verdict=pending`。

介入动作：

- Codex 使用 Codex App heartbeat automation update，将既有 `ap-overnight-monitor-patrol` 更新为当前主线版本：重点跟进 `T-40 Unit 2`，同时保留 `T-39` 重复 queued 风险与 `T-34~T-37` workflow-backed 任务要求。

临时结果：

- heartbeat 仍为 active，35 分钟一次、15 次，约 8 小时 45 分；后续巡检提示词已对齐当前 AP overnight monitor 真相。

明天修复建议：

- 长时监控任务应把“当前主线 task id / 下一个风险 task id / 已 closeout task id”做成可更新状态，而不是写死在 heartbeat prompt 中，避免自动巡检随着生产推进逐步失焦。

### 14. T-40 Unit 2 抽查发现选择题双正确，且 Obsidian Unit 2 未见独立 manifest

触发时间：2026-06-23 02:00 CST

触发原因：

- `T-40 AP Calculus AB Unit 2` 已进入 `submitted_for_review`，review_course 正在复核。
- Codex 对待 review 产物做最小抽查时，发现 `U2.3.3-C.md` 的 A/B 两个选项代数等价，形成双正确选择题；这会直接破坏题库智能体后续训练/出题的单答案假设。
- 产物已双写到 Obsidian Unit 2 目录，但该目录下未见独立 `qa-manifest.csv` 或 manifest 文件；目前 Unit 2 manifest 行只确认存在于项目根 `content/ap-calculus-ab/qa-manifest.csv`，目标知识库侧 manifest 同步证据不足。

现场证据：

- `./scripts/eduflowteam task get T-40` 显示 `status=submitted_for_review`、`workflow_gate=quality_gate`、`workflow_gate_status=awaiting_review_verdict`、`verdict=pending`。
- `./scripts/eduflowteam task review-queue --reviewer review_course` 显示 T-40 正在等待 review_course 复核。
- `content/ap-calculus-ab/subtopics/unit2/U2.3.3-C.md` 中题干为 `f(x)=e^x/(x^2+1)`，正确化简结果为 `g(x)=x^2+1-2x`，A 选项是 `x^2+1-2x`，B 选项是 `x^2-2x+1`，两者代数等价；文件却标记 `Answer B`，并解释“选项 A 虽然代数式相同，但通常要求按降幂排列”。
- `find .../AP Calculus AB/02-题库/items/Unit 2 -maxdepth 1 \\( -iname '*manifest*' -o -iname '*.csv' \\)` 未返回文件。
- `grep '^U2\\.' content/ap-calculus-ab/qa-manifest.csv | wc -l` 显示 11 行 Unit 2 manifest 记录。

介入动作：

- Codex 准备向 manager 发出窄范围纠偏：要求 review_course 在 verdict 中明确标记 `U2.3.3-C` 为 NEEDS_FIX，worker_course 只修该题的干扰项/答案唯一性，并补齐 Obsidian 侧 manifest 同步证据；不要扩大到 Unit 3 或重写整批。

临时结果：

- T-40 暂不能 closeout；等待 manager/review_course 消费该缺陷并触发最小返修。

明天修复建议：

- AP qbank workflow 的 QA gate 应新增“MCQ 选项唯一正确性/等价表达式冲突”自动检查；manifest gate 应明确“项目根 manifest”与“Obsidian 目标路径 manifest”的交付口径，避免 QA 自检只写通过但目标侧无证据。

### 15. T-40 review_course FULL PASS 与 Codex blocker 证据冲突

触发时间：2026-06-23 02:02 CST

触发原因：

- Codex 已向 manager 发送 `U2.3.3-C` 双正确 blocker 与 Obsidian manifest 证据不足问题。
- review_course 随后发出 `T-40 AP Calculus AB Unit 2 复核 verdict：FULL PASS`，但 verdict 内容没有处理 `U2.3.3-C` 的 A/B 等价选项问题，并声称 Obsidian Unit 2 目录存在 `qa-manifest.csv 与项目内一致`。
- manager 在 FULL PASS 后才 ACK Codex blocker，并再次转发给 review_course；review_course ACK 了 blocker，但 task truth 仍在 `submitted_for_review / verdict=pending`，review 口径已经出现“先 PASS、后收到 blocker”的顺序冲突。

现场证据：

- `.eduflow-team-state/facts/logs.jsonl` 显示 `log_1782151159197_34608e339f`：review_course 发出 `FULL PASS`，内容包含“目标路径交付：Obsidian ... Unit 2/ 已同步全部文件，qa-manifest.csv 与项目内一致”。
- 同一轮稍后日志显示 `log_1782151169263_681480acf4`：manager 才 ACK Codex blocker 消息 `msg_1782151153224_5c52589d97`。
- 再后日志显示 `log_1782151171671_ea40d15871`：review_course ACK manager 转发的 blocker，要求关注 `U2.3.3-C` 双正确。
- `content/ap-calculus-ab/subtopics/unit2/U2.3.3-C.md` 中 A 选项 `x^2+1-2x` 与 B 选项 `x^2-2x+1` 代数等价，文件标记 `Answer B`。
- `find .../AP Calculus AB/02-题库/items/Unit 2 -maxdepth 1 \\( -iname '*manifest*' -o -iname '*.csv' \\)` 未返回任何文件。
- `./scripts/eduflowteam task get T-40` 仍显示 `status=submitted_for_review`、`verdict=pending`。

介入动作：

- Codex 准备提醒 manager：不要消费该 FULL PASS closeout；要求 review_course 追加/修正 verdict，以 Codex blocker 后的证据为准。若 `U2.3.3-C` 未修且 Obsidian manifest 证据未补齐，T-40 必须保持 NEEDS_FIX 或 CONDITIONAL PASS，不能 closeout。

临时结果：

- T-40 当前应视为“待修正 verdict / 需返工”，而不是完成。

明天修复建议：

- review_course 在发 PASS 前应检查是否有未读高优先级 inbox 或 manager/codex_monitor 新增 blocker；manager closeout gate 应拒绝消费早于最新 blocker 的 verdict。

### 16. T-40 修复后最终 FULL PASS 已出，但 task truth 被重置回 in_progress

触发时间：2026-06-23 02:09 CST

触发原因：

- worker_course 已完成 `U2.3.3-C` 窄修，review_course 随后给出修复后最终 `FULL PASS`。
- 但几乎同时 manager 将 `T-40` 重置为 `in_progress`，声称让 worker_course 重新 submit-review，以确保 review_course 复核修复后文件版本。
- 当前 task truth 因此显示 `status=in_progress`、`workflow_gate=review_handoff_gate`、`next_action=submit_review`、`verdict=pending`，与日志中的最终 FULL PASS 冲突。

现场证据：

- `.eduflow-team-state/facts/logs.jsonl` 显示 `log_1782151325644_6834aa4e49`：review_course 发出 `T-40 AP Calculus AB Unit 2 最终复核 verdict：FULL PASS`，并确认 `U2.3.3-C` 答案唯一性恢复、manifest U2 记录一致。
- 同一轮日志显示 `log_1782151327057_3ae3aace0d`：manager 说 `T-40 已重置为 in_progress，让 worker_course 重新 submit-review`。
- `./scripts/eduflowteam task get T-40` 显示 `T-40 [in_progress]`、`verdict=pending`。
- `./scripts/eduflowteam task workflow-status T-40` 显示 `gate=review_handoff_gate`、`next_action=submit_review`。
- Codex 本地验证项目与 Obsidian 两边 `U2.3.3-C.md` 均已修复为 A=`x^2-1`、B=`x^2-2x+1`；Obsidian `02-题库/qa-manifest.csv` 有 11 行 U2 记录。

介入动作：

- Codex 准备提醒 manager：不要重复拉 worker_course 重新生产；应消费 review_course 最新最终 FULL PASS，将 `T-40` task truth 对齐为 approved/delivered 或 batch closeout，并记录 evidence keys。若系统要求重新 submit-review，则只执行结构化 submit/review 消费，不再修改内容。

临时结果：

- T-40 产物面与 review 日志已可支持 closeout，但 task truth 暂未对齐，不能在监控总结里记为正式完成。

明天修复建议：

- task workflow 应支持“post-fix verdict supersedes earlier verdict”的原子状态转换，避免 manager 为了重审而手动回退 gate，造成最终 verdict 与 task truth 顺序倒挂。

### 17. T-40 closeout 后 manager 继续 AP Calculus AB Unit 3，存在多学科目标偏移风险

触发时间：2026-06-23 02:12 CST

触发原因：

- 今晚用户目标是完成 AP 知识库优化的 4-5 个学科样本，并为题库智能体沉淀可复用标准。
- `T-38` 和 `T-40` 已完成 AP Calculus AB Unit 1/2，证明了 qbank-agent schema 与 QA/review/closeout 链路。
- manager 在 `T-40` closeout 后直接启动 `T-41 AP Calculus AB Unit 3`，虽是 workflow-backed，但如果继续深挖同一学科，会挤占 AP Computer Science A、AP Physics 1、AP Statistics、AP Psychology 的启动与 QA 时间，偏离“4-5 个学科”目标。

现场证据：

- `./scripts/eduflowteam task get T-40` 显示 `status=delivered`、`verdict=approved`、`workflow_gate=batch_closeout_gate`、`closeout_status=batch_closeout_completed`。
- `.eduflow-team-state/facts/logs.jsonl` 显示 manager 同步：`T-40 Unit 2 已 batch closeout`，并写明“下一步：继续 AP Calculus AB Unit 3”。
- `./scripts/eduflowteam task get T-41` 显示 `T-41 [in_progress] AP Calculus AB Unit 3 题库生产`、`workflow_id=igcse-subject-launch`、`reviewer=review_course`、`next_action=submit_review`。
- `.eduflow-team-state/facts/status.json` 显示 manager 当前 task 为 `T-41 AP Calc AB Unit 3 生产中`，而 AP Computer Science A / Physics 1 / Statistics / Psychology 仍未进入正式 workflow-backed 生产状态。

介入动作：

- Codex 准备提醒 manager：`T-41` 可继续作为同学科深化样本，但不得替代今晚 4-5 学科目标；应立即规划下一轮把 AP CSA / Physics 1 / Statistics / Psychology 至少各创建或升级为 workflow-backed 权威任务，并给出学科状态矩阵。

临时结果：

- 待 manager 回传 4-5 学科状态矩阵与下一学科 workflow 启动计划。

明天修复建议：

- manager closeout gate 应要求检查“今晚目标维度”是否是按学科推进还是按 unit 推进；当目标是多学科样本时，系统应限制连续启动同一学科过多 unit，除非 manager 明确说明这是用户批准的策略调整。

### 18. heartbeat 巡检基线需要从 T-40 更新到 T-41~T-45

触发时间：2026-06-23 02:11 CST

触发原因：

- `T-40 AP Calculus AB Unit 2` 已正式 closeout，当前生产主线推进到 `T-41 AP Calculus AB Unit 3`。
- manager 已补齐多学科 workflow-backed 任务：`T-42 AP Computer Science A Unit 1`、`T-43 AP Physics 1 Unit 1`、`T-44 AP Statistics Unit 1`、`T-45 AP Psychology Unit 1`。
- 既有 heartbeat prompt 若继续主要盯 `T-40`，后续自动巡检容易漏掉 `T-41` 的 Obsidian 同步/submit-review，以及 `T-42~T-45` 是否从 assigned 真正启动。

现场证据：

- `./scripts/eduflowteam task get T-40` 上轮已显示 `delivered / approved / batch_closeout_gate passed`。
- `./scripts/eduflowteam task get T-41` 显示 `in_progress`、`workflow_gate=review_handoff_gate`、`next_action=submit_review`。
- `./scripts/eduflowteam task get T-42~T-45` 显示均为 workflow-backed assigned/待 worker acceptance。
- `find content/ap-calculus-ab/subtopics/unit3 -name 'U*.md' | wc -l` 显示项目侧已有 21 个 Unit 3 item，schema 字段覆盖 21/21。
- `find .../AP Calculus AB/02-题库/items/Unit 3 -name 'U*.md' | wc -l` 显示 Obsidian Unit 3 当前 0 个 item，说明尚未交付/送审。

介入动作：

- Codex 更新 `ap-overnight-monitor-patrol` heartbeat prompt，将当前基线改为：T-38/T-40 已完成，重点跟进 T-41 Unit 3 生产/同步/送审，以及 T-42~T-45 是否真正启动并形成多学科样本。

临时结果：

- 后续 heartbeat 巡检将优先检查 `T-41~T-45`，并继续防止“只深挖 AP Calc、其它四科停在 assigned”的目标偏移。

明天修复建议：

- 长时监控自动化应从 task truth 自动读取 active/in_progress/assigned 任务列表，而不是依赖人工更新 prompt 中的 task id。

### 19. T-41 Unit 3 产物已完成并自称 submitted_for_review，但 task truth 未送审

触发时间：2026-06-23 02:13 CST

触发原因：

- `T-41 AP Calculus AB Unit 3` 项目侧与 Obsidian 侧均已出现完整 Unit 3 item 产物，QA 自检也写明 `Status: submitted_for_review`。
- 但 task truth 仍显示 `in_progress`、`workflow_gate=review_handoff_gate`、`workflow_next_action=submit_review`，review queue 为空。
- 这意味着 worker/文件层已经完成交付口径，但 workflow/task/review 链路没有结构化送审，review_course 不会收到正式待审任务。

现场证据：

- `find content/ap-calculus-ab/subtopics/unit3 -name 'U*.md' | wc -l` 显示 21 个 Unit 3 item。
- `find .../AP Calculus AB/02-题库/items/Unit 3 -name 'U*.md' | wc -l` 显示 Obsidian 目标目录也有 21 个 Unit 3 item。
- `content/ap-calculus-ab/subtopics/unit3/QA-自检.md` 写明 Unit 3 共 7 个 subtopic、21 题、QA 7 项通过、manifest 已同步、Obsidian 已交付，并写 `Status: submitted_for_review`。
- `grep '^U3\\.' content/ap-calculus-ab/qa-manifest.csv | wc -l` 和 Obsidian `02-题库/qa-manifest.csv` 均显示 7 行 U3 manifest 记录。
- `./scripts/eduflowteam task get T-41` 显示 `status=in_progress`、`verdict=pending`。
- `./scripts/eduflowteam task workflow-status T-41` 显示 `next_action=submit_review`。
- `./scripts/eduflowteam task review-queue --reviewer review_course` 显示无待审任务。

介入动作：

- Codex 准备提醒 manager：不要改内容、不进入 Unit 4；只让 worker_course 执行结构化 submit-review，并让 review_course 按题目质量与 qbank-agent schema 分开复核。

临时结果：

- T-41 当前状态应记录为“产物已完成，待结构化送审”，不能记为 review 中或完成。

明天修复建议：

- worker 完成 QA 自检并写入 `submitted_for_review` 状态时，应自动触发 `task submit-review` 或至少阻止 QA 文件先行声称 submitted，避免文件状态与 task truth 分裂。

### 20. T-41 review_course 已给 FULL PASS，但 task truth/review queue 未消费 verdict

触发时间：2026-06-23 02:18 CST

触发原因：

- `review_course` 已在日志中给出 `T-41 AP Calculus AB Unit 3` 的 FULL PASS verdict，并明确题目质量 PASS、qbank-agent schema PASS、数量与 Obsidian 交付通过。
- 但 task truth 仍显示 `submitted_for_review / verdict=pending`，review queue 仍显示 T-41 awaiting review。
- 如果 manager 不消费该 verdict，后续会出现“群聊说 closeout，但结构化 truth 仍待审”的状态分裂，影响下一轮巡检和最终完成统计。

现场证据：

- `.eduflow-team-state/facts/logs.jsonl` 中 `log_1782152169822_6c12e3980e` 显示：`T-41 AP Calculus AB Unit 3 复核 verdict：FULL PASS`，并列出题目质量、schema、manifest、Obsidian 同步均通过。
- `./scripts/eduflowteam task get T-41` 显示 `status=submitted_for_review`、`verdict=pending`。
- `./scripts/eduflowteam task workflow-status T-41` 显示 `gate=quality_gate`、`gate_status=awaiting_review_verdict`、`next_action=review_course_review`。
- `./scripts/eduflowteam task review-queue --reviewer review_course` 仍显示 T-41 awaiting review。

介入动作：

- Codex 准备提醒 manager：只消费 review_course 最新 FULL PASS，将 T-41 task truth 对齐为 approved/delivered 或 batch closeout，清空 review queue；不改内容、不进入 Unit 4，直到 closeout 证据写入 task truth。

临时结果：

- T-41 当前应记录为“review PASS 已出，待 manager closeout 消费”，不能记为正式完成。

明天修复建议：

- review_course 发出结构化 PASS 时应自动写回 task verdict 或触发 manager closeout gate；manager closeout 不应依赖人工从聊天日志复制 verdict。

### 21. T-41 closeout 后继续启动 AP Calculus AB Unit 4，四个目标学科仍未真正生产

触发时间：2026-06-23 02:21 CST

触发原因：

- 今晚目标是 4-5 个 AP 学科形成可复用题库智能体基础标准。
- AP Calculus AB 已连续完成 Unit 1、Unit 2、Unit 3，并继续启动 `T-46 AP Calculus AB Unit 4`。
- `T-42 AP Computer Science A`、`T-43 AP Physics 1`、`T-44 AP Statistics`、`T-45 AP Psychology` 虽已补成 workflow-backed task，但仍停留在 assigned / waiting_worker_acceptance，实际 Unit 1 item 产物均为 0。
- 若继续让 worker_course 深挖 AP Calc，会把“4-5 学科样本”变成“1 个学科多 Unit 样本”，偏离用户目标。

现场证据：

- `./scripts/eduflowteam task get T-41` 显示 `delivered / approved / batch_closeout_gate passed`。
- `./scripts/eduflowteam task get T-46` 显示 `T-46 [in_progress] AP Calculus AB Unit 4 题库生产`、`workflow_id=igcse-subject-launch`、`next_action=submit_review`。
- `./scripts/eduflowteam task workflow-status T-42~T-45` 均显示 `status=assigned`、`gate=dispatch_acceptance_gate`、`gate_status=waiting_worker_acceptance`、`next_action=worker_start_or_ack`。
- `find .../AP Computer Science A/02-题库/items/Unit 1 -name 'U*.md' | wc -l` 为 0。
- `find .../AP Physics 1/02-题库/items/Unit 1 -name 'U*.md' | wc -l` 为 0。
- `find .../AP Statistics/02-题库/items/Unit 1 -name 'U*.md' | wc -l` 为 0。
- `find .../AP Psychology/02-题库/items/Unit 1 -name 'U*.md' | wc -l` 为 0。
- `find content/ap-calculus-ab/subtopics/unit4 -name 'U*.md' | wc -l` 暂为 0，说明 Unit 4 刚启动，仍有机会调整执行节奏。

介入动作：

- Codex 准备提醒 manager：不要继续开 AP Calc Unit 5；T-46 可保留但不应吞掉主线资源。请立即让 T-42~T-45 中至少 2 个任务进入 started/in_progress，并回传 5 学科状态矩阵；若 worker_course 单线程被 T-46 占用，应使用 worker_builder/worker_qbank 或重新分配 owner。

临时结果：

- 待 manager 消费提醒并将多学科任务从 assigned 推进到真实生产。

明天修复建议：

- 多学科目标应有 scheduler guard：当目标维度是“学科数”时，连续同一学科 Unit 任务超过 2 个后，manager 必须显式确认策略，否则自动优先启动其它学科的 workflow task。

### 22. patrol 基线已转向 T-42/T-43/T-46，但 manager 新指令又把 worker_course 拉回 Calc 优先

触发时间：2026-06-23 02:27 CST

触发原因：

- 前一轮介入后，`T-42 AP Computer Science A Unit 1` 已进入结构化送审，`T-43 AP Physics 1 Unit 1` 也进入 `in_progress`，说明多学科主线开始恢复。
- 但 manager 最新给 worker_course 的高优先级指令写明“当前只激活 T-46 AP Calculus AB Unit 4”“不要同时推进多科”，随后又要求 `T-46` 优先完成，`T-43` 在 T-46 提交后再启动。
- 这会再次把今晚目标从“4-5 个 AP 学科样本”拉回“AP Calculus AB 连续 Unit 深挖”，并让 `T-43/T-44/T-45` 的 workflow-backed 任务停在结构上存在、实际不产出的状态。

现场证据：

- `./scripts/eduflowteam inbox worker_course` 显示未读高优先级消息 `msg_1782152532535_5bd9fffab1`：`当前只激活 T-46 AP Calculus AB Unit 4。T-43/T-44/T-45 你已接单但请暂缓启动，等我后续通知。不要同时推进多科。`
- `./scripts/eduflowteam inbox worker_course` 显示未读高优先级消息 `msg_1782152601199_a4ce55324f`：`T-46 AP Calculus AB Unit 4 仍是当前第一优先级，请先完成并 submit-review。T-43 AP Physics 1 Unit 1 已置为 in_progress，但请在 T-46 提交后再启动。T-44/T-45 继续暂缓。`
- `./scripts/eduflowteam task get T-42` 显示 `submitted_for_review`、`workflow_gate=quality_gate`、`workflow_next_action=review_course_review`，review queue 中已有 T-42。
- `./scripts/eduflowteam task get T-43` 显示 `in_progress`、`workflow_gate=review_handoff_gate`、`workflow_next_action=submit_review`。
- `./scripts/eduflowteam task get T-46` 显示 `in_progress`，且 AP Calculus AB Unit 4 项目侧和 Obsidian 侧均已有 21 个 item。
- Obsidian 实际产物计数显示 `AP Computer Science A / AP Physics 1 / AP Statistics / AP Psychology` 的 Unit 1 item 当前仍均为 0，而 AP Calculus AB Unit 1~4 已分别有产物。

介入动作：

- Codex 准备以最低力度软提醒 manager：保持 `T-42` 复核推进；不要再把 `T-43` 暂缓在 Calc 后面；`T-46` 可以完成送审但不能继续开 Calc Unit 5；请把下一生产资源转向 `T-43`，并为 `T-44/T-45` 给出明确启动窗口或改派 worker_builder/worker_qbank。

临时结果：

- 当前状态应记录为：`T-42` 待 review；`T-43` 名义 in_progress 但有被 manager 暂缓风险；`T-44/T-45` 仍 assigned 未启动；`T-46` in_progress 且已有完整文件，但不能计入“新增学科样本”。

明天修复建议：

- scheduler/manager 应支持“目标维度锁”：当用户目标是多学科覆盖时，派单策略必须按 subject diversity 排序；同一学科连续启动新 Unit 前，应检查其它目标学科是否已有至少一个 Unit 完成并通过 review。

### 23. T-42 已进入送审状态，但 AP CSA 目标题库目录没有 Unit 1 item 产物

触发时间：2026-06-23 02:28 CST

触发原因：

- `T-42 AP Computer Science A Unit 1` 在 task truth 中已是 `submitted_for_review`，review queue 也显示 awaiting review。
- 但用户指定的 Obsidian 产物路径下没有 `02-题库/items/Unit 1` item 文件，甚至浅层目录中没有 `02-题库/items` 结构。
- 如果 review_course 只按 task queue 复核并给 PASS，会把“结构化送审”误判成“实际产物已交付”，破坏今晚对题库智能体基础字段的验收。
- 同时 manager 给 review_course 的复核顺序又把 `T-46 AP Calc Unit 4` 排在 `T-42 AP CSA` 前面，进一步削弱非 Calc 学科闭环优先级。

现场证据：

- `./scripts/eduflowteam task get T-42` 显示 `status=submitted_for_review`、`workflow_gate=quality_gate`、`workflow_gate_status=awaiting_review_verdict`、`workflow_next_action=review_course_review`。
- `./scripts/eduflowteam task review-queue --reviewer review_course` 显示 `T-42 AP Computer Science A Unit 1` awaiting review。
- `./scripts/eduflowteam inbox review_course` 显示 manager 消息 `msg_1782152903412_67f1c23d7c`：复核顺序为 `T-46 -> T-42 -> T-43 -> T-44 -> T-45`。
- `find "/Volumes/Halobster/Obsidian Edu/.../AP Computer Science A/02-题库/items/Unit 1" -name 'U*.md'` 计数为 0。
- `find "/Volumes/Halobster/Obsidian Edu/.../AP Computer Science A" -maxdepth 5 -type d` 只看到既有 Topic 页面与规划目录，没有目标题库 items 目录结构。
- `rg -l 'AP Computer Science A|Computer Science A|CSA Unit 1|T-42' .` 在项目 `content/` 下未发现 AP CSA Unit 1 题库 item 产物，仅发现计划/监控文档。

介入动作：

- Codex 准备提醒 manager 与 review_course：`T-42` review 必须先做 artifact existence gate；若目标 item/manifest 缺失，应 verdict `NEEDS_FIX` 或退回 worker_builder 补齐，而不是 PASS。
- 同时要求 manager 不要把 `T-46` 的 Calc review 排在非 Calc 学科闭环前面，除非 `T-42` 明确退回返工。

临时结果：

- `T-42` 当前状态应标为“待 review，但产物存在性风险阻塞”；不能计为 AP CSA 已完成，也不能作为题库智能体可用样本。

明天修复建议：

- `task submit-review` 应内置 artifact existence gate：提交送审前必须验证目标目录、item 数、manifest 行数与 QA 文件存在；缺任一项时阻止进入 `quality_gate`，并把缺口写入 task evidence。

### 24. heartbeat 自动巡检基线滞后于 T-42/T-46 最新状态

触发时间：2026-06-23 02:31 CST

触发原因：

- 35 分钟 heartbeat 仍把 `T-42/T-43` 描述为“开始处理/应确认是否 in_progress 与产物出现”，但实际状态已变化为：`T-42` 已 submitted_for_review 且暴露 artifact 缺失风险；`T-46` 已 submitted_for_review；`T-43` 虽为 in_progress 但曾被 manager 暂缓到 T-46 后。
- 若 heartbeat 不更新，下轮自动 patrol 可能漏掉 `T-42` 空产物送审、`T-46` 抢占 review 顺序、`T-43` 名义 in_progress 但实际未产出的风险。

现场证据：

- `/Users/huanganan/.codex/automations/ap-overnight-monitor-patrol/automation.toml` 旧 prompt 写明：`T-42 AP Computer Science A Unit 1 已从 assigned 推进到开始处理/应确认是否 in_progress 与产物出现`，`T-46` 仍写 `in_progress`。
- `./scripts/eduflowteam task get T-42` 当前显示 `submitted_for_review`、`quality_gate`、`awaiting_review_verdict`。
- `./scripts/eduflowteam task get T-46` 当前显示 `submitted_for_review`、`quality_gate`、`awaiting_review_verdict`。
- AP CSA 目标路径巡检显示 `02-题库/items/Unit 1` 下没有 `U*.md`。

介入动作：

- Codex 已用 Codex App automation_update 更新 `ap-overnight-monitor-patrol` heartbeat prompt，把基线改为：T-42 送审但 artifact gate 风险；T-46 送审但不得替代多学科目标；T-43 需确认 T-46 后是否真实生产；T-44/T-45 仍需启动窗口或改派。

临时结果：

- 后续 heartbeat patrol 将优先盯 T-42 artifact existence gate、T-46 review 抢占风险、T-43/T-44/T-45 非 Calc 学科实际产物推进。

明天修复建议：

- heartbeat prompt 应由 task truth 自动生成“当前 active/review/assigned task matrix”，并把上一轮 gap note 中的高风险事项自动带入下一轮巡检重点，减少人工更新遗漏。

### 25. T-42 已有 REVISION REQUIRED verdict，但返修尚未真正落到 worker_builder 执行

触发时间：2026-06-23 02:34 CST

触发原因：

- `review_course` 已明确给出 `T-42 AP CSA Unit 1` 返修结论：当前只有知识点条目、QA 与 manifest，没有实际 MCQ item 文件，必须返修。
- 但 task truth 仍显示 `status=submitted_for_review`、`verdict=pending`，`workflow_gate=revision_first`，并没有把 reviewer verdict 消费成明确返修任务状态。
- `worker_builder` 当前状态为待命中，未见正在执行“生成 actual MCQ item 文件”的返修动作；如果 manager 不继续推动，T-42 会停在“知道要返修但无人返修”的半同步状态。

现场证据：

- `.eduflow-team-state/facts/logs.jsonl` 中 `review_course` 最新 verdict 写明：`T-42 AP CSA Unit 1 返修复核 verdict：REVISION REQUIRED`，并列出无实际 item 文件、qbank-agent schema FAIL、需要每个 subtopic 生成 1-3 道 MCQ item。
- `./scripts/eduflowteam task get T-42` 显示 `verdict=pending`、`workflow_gate=revision_first`、`workflow_next_action=worker_repair_revision_scope_before_any_other_action`。
- `./scripts/eduflowteam inbox worker_builder` 显示无未读消息。
- `.eduflow-team-state/facts/status.json` 显示 `worker_builder` 状态为 `待命中`，任务为 `T-42 已重新提交复核，待命`。
- Obsidian 目标路径 `/AP Computer Science A/02-题库/items/Unit 1/` 当前仅有 `AP_Computer_Science_A_Unit_1_知识点条目.md`、`qa-manifest.csv`、`QA-自检.md`，无 `U*.md` actual item。

介入动作：

- Codex 准备提醒 manager：立即消费 `review_course` 的 REVISION REQUIRED verdict，将 T-42 返修派回 worker_builder；返修 scope 只做 actual MCQ item 文件、manifest 改成 AP Calc 一致格式、完成后重新 submit-review。

临时结果：

- T-42 当前状态应记录为“需返工/风险阻塞”，不能计为 AP CSA 已完成；它可以作为知识点条目草稿，但尚不能作为题库智能体 actual item 样本。

明天修复建议：

- reviewer 的 `REVISION REQUIRED` 应自动写回 task verdict/revision scope，并生成可执行返修 inbox；manager 不应手工转述，避免 verdict 与 worker 执行状态脱节。

### 26. health/supervisor 持续 worker_context_risk，但当前主线仍有真实产出

触发时间：2026-06-23 02:34 CST

触发原因：

- `./scripts/eduflowteam task supervisor-check --json` 与 `./scripts/eduflowteam health` 持续报告 `health_status=escalated_failure`、`primary_reason=worker_context_risk`，且 health 中还有 router/watchdog flapping、worker_course ready_unproven 等红/黄项。
- 但实时 tmux 显示 `worker_course` 仍在执行 `Generate Physics Unit 1 items`，项目侧也已经出现 AP Physics 1 Unit 1 文件，因此暂时不是“生产链卡死”。
- 需要记录 runtime 风险并持续观察，避免在当前真实产出中途贸然重启 worker_course。

现场证据：

- `./scripts/eduflowteam task supervisor-check --json` 显示 `health_status=escalated_failure`、`primary_reason=worker_context_risk`、`recommended_action=trigger_supervisor_repair`、`consecutive_issue_count=9`。
- `./scripts/eduflowteam health` 显示 `worker_course: ready_unproven`，`router stability: 65 respawns, 65 stalls`，`watchdog stability: 68 respawns`。
- `tmux capture-pane -t EduFlowTeam:worker_course` 显示正在运行 `general-purpose Generate Physics Unit 1 items`。
- `find content/ap-physics1/subtopics/unit1 -name 'U*.md' | wc -l` 已显示项目侧有 11 个 Physics Unit 1 item 文件，样例文件含标准 YAML frontmatter 与 Options/Answer/Explanation。

介入动作：

- Codex 暂不重启 runtime；先持续监控 worker_course 是否继续产出、是否完成 submit-review、是否出现上下文耗尽或停止响应。
- 若下一轮出现项目侧文件数不增长、worker_course pane 无进展、或 inbox 未消费导致 T-43 卡住，再升级为 runtime repair 或要求 manager 重启/改派。

临时结果：

- 当前 runtime 风险被记录为“高风险观察中”，不是立即 operator fallback。

明天修复建议：

- supervisor 的 `worker_context_risk` 应给出具体 agent、上下文阈值、最后一次成功产出时间、是否建议安全重启；避免监控人员只能看到笼统红灯，难以判断是观察还是修复。

### 27. T-42 返修已生成 actual MCQ 文件，但 qbank-agent schema 字段仍不合格

触发时间：2026-06-23 02:40 CST

触发原因：

- `T-42 AP Computer Science A Unit 1` 返修后已从 0 个 actual item 增至 15 个 `U*.md` 文件，并有 `qa-manifest.csv`。
- 但抽查发现这些文件只包含 `id/difficulty/type/calculator/subject/unit/topic/subtopic/learning_objective` 等字段，缺少用户明确要求和 task brief 要求的 `knowledge_point/core_concept/exam_pattern/question_type/common_mistake/explanation_context`。
- 正文结构使用 `**Options:**`、`**Answer:**`、`**Explanation:**`，不是 AP Calc/Physics 样本中更稳定的 `## Options`、`## Answer`、`## Explanation` 标题结构；对后续题库智能体解析不够稳。
- 若 review_course 只按“已有 MCQ 文件 + manifest”给 PASS，会再次把不达标 schema 误判为完成。

现场证据：

- `find ".../AP Computer Science A/02-题库/items/Unit 1" -maxdepth 1 -name 'U*.md' | wc -l` 显示 15。
- `rg -l 'knowledge_point:' ".../AP Computer Science A/02-题库/items/Unit 1"/*.md | wc -l` 为 0；`core_concept:`、`exam_pattern:`、`question_type:`、`common_mistake:`、`explanation_context:` 也均为 0。
- `rg -l '## Options|## Answer|## Explanation' ".../AP Computer Science A/02-题库/items/Unit 1"/*.md | wc -l` 为 0，而 `Options/Answer/Explanation` 只以加粗行形式出现。
- 抽样文件 `U1.1.1-F.md` 的 YAML frontmatter 包含 `learning_objective`，但无上述 qbank-agent 字段。
- `./scripts/eduflowteam task get T-42` 仍显示 `verdict=pending`、`workflow_gate=revision_first`、`workflow_next_action=worker_repair_revision_scope_before_any_other_action`。

介入动作：

- Codex 准备提醒 manager/review_course：T-42 返修只能算“actual item 数量补齐”，不能算 schema PASS；需要 worker_builder 在每个 item 的 frontmatter 补齐 qbank-agent 字段，并统一正文标题后再 review。

临时结果：

- T-42 当前状态应记录为“需返工/部分返修完成”：actual item 文件已出现，但题库智能体 schema 不达标，不能 closeout。

明天修复建议：

- 为 AP item 生产增加统一模板/validator：提交前自动检查 frontmatter 必填字段、正文标题、Answer 唯一性与 manifest 对齐；schema 不通过时禁止 submit-review。

### 28. T-43 Physics 已有 Obsidian item 产物，但 QA 数量、manifest、task truth 不一致

触发时间：2026-06-23 02:44 CST

触发原因：

- `T-43 AP Physics 1 Unit 1` 文件层已经出现大批 actual item，且 Obsidian 目标路径已同步 45 个 `U*.md`。
- 字段巡检显示 45/45 均含 `knowledge_point/core_concept/exam_pattern/question_type/common_mistake/explanation_context` 与 `## Options/## Answer/## Explanation`。
- 但 `QA-自检.md` 仍写 `总题数: 39`、`13 个子主题`，同时文件清单实际列到 15 个 subtopic / 45 item；目标目录没有 `qa-manifest.csv`。
- task truth 仍显示 `T-43 status=in_progress`、`workflow_next_action=submit_review`，说明文件层已接近提交，但 workflow/review 链路尚未结构化送审。

现场证据：

- `find ".../AP Physics 1/02-题库/items/Unit 1" -maxdepth 1 -name 'U*.md' | wc -l` 显示 45。
- `rg -l 'knowledge_point:' ".../AP Physics 1/02-题库/items/Unit 1"/*.md | wc -l`、`core_concept:`、`exam_pattern:`、`question_type:`、`common_mistake:`、`explanation_context:` 均为 45。
- `rg -l '## Options' ... | wc -l`、`## Answer`、`## Explanation` 均为 45。
- `QA-自检.md` 写明 `总题数: 39`、`已生成 qa-manifest.csv`，但 `find ".../AP Physics 1/02-题库/items/Unit 1" -name '*manifest*' | wc -l` 为 0。
- `./scripts/eduflowteam task get T-43` 显示 `status=in_progress`、`workflow_gate=review_handoff_gate`、`workflow_next_action=submit_review`。

介入动作：

- Codex 准备提醒 manager：不要 closeout T-43；先要求 worker_course 修正 QA 数量与 manifest，补齐 `qa-manifest.csv`，再执行结构化 `submit-review T-43`。

临时结果：

- T-43 当前应标为“生产中/待结构化送审，QA/manifest 风险”；不能记为已完成或待 closeout。

明天修复建议：

- 生产脚本提交前应自动对比 `U*.md` 实际计数、QA 自检声明、manifest 行数与 task evidence；三者不一致时阻止 submit-review，并提示具体差异。

### 29. worker_builder/manager API quota 异常打断 T-42 返修与 T-43 结构化送审纠偏

触发时间：2026-06-23 02:47 CST

触发原因：

- `worker_builder` 已开始执行 T-42 AP CSA Unit 1 二次 schema 返修，写出 `/tmp/update_ap_csa_unit1.py`，但 pane 随后显示 `429 You've reached your usage limit`，返修未落地。
- `manager` 收到 Codex 对 T-43 Physics 的 QA/manifest/submit-review 纠偏后，pane 也出现 API retry，导致 manager 未及时把 T-43 修 QA/补 manifest/submit-review 指令落给 worker_course。
- 当前两个非 Calc 学科都在关键收口点卡住：T-42 actual item 存在但 schema 0/15；T-43 item 文件和字段完整但 QA/manifest/task handoff 不一致。

现场证据：

- `tmux capture-pane -t EduFlowTeam:worker_builder` 显示已写 `/tmp/update_ap_csa_unit1.py`，随后报 `API Error: Request rejected (429) · You've reached your usage limit for this period`。
- T-42 目标路径 15 个 `U*.md` 存在，但 `knowledge_point/core_concept/exam_pattern/question_type/common_mistake/explanation_context/## Options/## Answer/## Explanation` 计数仍均为 0。
- `tmux capture-pane -t EduFlowTeam:manager` 显示 manager 正在处理 Codex 的 T-43 纠偏消息 `msg_1782153925446_0d1ee40e1b` 时出现 `API error · Retrying`。
- T-43 Obsidian 目标路径已有 45 个 `U*.md`，但 `qa-manifest.csv` 缺失，`./scripts/eduflowteam task get T-43` 仍显示 `in_progress`、`workflow_next_action=submit_review`。

介入动作：

- Codex 先记录 runtime gap；下一步优先尝试最低力度补救：让 manager/可用 runtime 改派或重试结构化收口。
- 若 manager/worker_builder 因 quota 继续不可用，考虑 operator fallback 仅限生成/修正 manifest 与执行 task submit-review 等结构化收口动作，不大规模改写题目内容。

临时结果：

- T-42：返修卡在 schema 二次修复中，不能 closeout。
- T-43：文件层可用度高，但仍需 QA/manifest/task truth 对齐后送 review。

明天修复建议：

- runtime guard 应在 429/quota 时自动切换 provider 或改派同能力 worker，并把未完成的 exact revision scope 重新投递；不能让 pane retry 成为唯一恢复机制。

### 30. 触发最小 operator fallback：仅做 T-42 schema 结构修复与 T-43 manifest/submit-review 收口

触发时间：2026-06-23 02:48 CST

触发原因：

- `worker_builder` 在执行 T-42 schema 二次返修时明确触发 429 quota，上游 pane 已无法继续完成已写好的结构修复脚本。
- `manager` 与 `worker_course` 也在处理 T-43 收口时进入 API retry，导致 T-43 文件层完成后仍未补 manifest/提交 review。
- 若继续等待，非 Calc 学科闭环会停在“有产物但 workflow/review 不落地”的状态，影响今晚 QA 追踪目标。

现场证据：

- `tmux capture-pane -t EduFlowTeam:worker_builder` 显示 `/tmp/update_ap_csa_unit1.py` 已写出，但随后 `API Error: Request rejected (429)`。
- `tmux capture-pane -t EduFlowTeam:manager` 显示处理 Codex T-43 纠偏消息时多次 `API error · Retrying`。
- T-42 当前 15 个 actual MCQ 文件存在，但 qbank-agent 字段计数仍为 0/15。
- T-43 当前 45 个 Physics item 文件已在 Obsidian 目标路径，字段 45/45 完整，但 `qa-manifest.csv` 缺失，task truth 仍为 `in_progress`。

介入动作：

- Codex 准备执行最小 operator fallback：
  1. 运行 worker_builder 已生成的 `/tmp/update_ap_csa_unit1.py`，只补 T-42 frontmatter 必填字段与正文标题，不改题目内容。
  2. 为 T-43 生成/同步 `qa-manifest.csv`，修正 QA 自检中的数量口径。
  3. 对 T-43 执行结构化 `task submit-review`，必要时对 T-42 在 schema 校验通过后重新 submit-review。

临时结果：

- 待执行后重新用字段计数、manifest 存在性、review queue/task truth 验证。

明天修复建议：

- 系统应提供“结构修复型 fallback”内置工具，限定只修 schema/manifest/task truth，不改题目内容；并在 runtime 429 时由 manager 自动授权或改派，不依赖 Codex 人工判断。

### 31. review 队列已恢复但 manager 未读旧消息积压，存在旧 verdict 覆盖新事实风险

触发时间：2026-06-23 02:53 CST

触发原因：

- Codex operator fallback 后，T-42/T-43 已重新进入 `review_course` review queue，但 manager inbox 仍有 20 条未读消息，其中包含 T-42 早期 CONDITIONAL PASS、REVISION REQUIRED、T-46 CONDITIONAL PASS 等旧 verdict。
- 当前 artifact truth 已变化：T-42 15/15 item 已补齐 qbank-agent 字段和标准标题；T-43 45/45 item 与 manifest/QA 已补齐；但旧 inbox 消息如果被 manager 后续消费，可能把任务状态倒退或错误 closeout。
- T-44/T-45 仍停在 assigned，若 manager 被旧消息牵引，今晚 4-5 学科目标会继续偏向 Calc 单科扩展，而不是多学科闭环。

现场证据：

- `./scripts/eduflowteam task review-queue --reviewer review_course` 显示 T-42、T-43、T-46 均 awaiting review。
- `./scripts/eduflowteam inbox manager` 显示 20 unread，包含多条 02:52 的旧 T-42/T-46 verdict/开始复核/完成交接消息。
- Obsidian 产物抽查：T-42 `U*.md` 数量 15，`knowledge_point/core_concept/exam_pattern/question_type/common_mistake/explanation_context/## Options/## Answer/## Explanation` 均为 15/15。
- Obsidian 产物抽查：T-43 `U*.md` 数量 45，manifest 与 QA 存在，核心字段和标准标题均为 45/45。
- Obsidian 产物抽查：T-46 `U*.md` 数量 21，核心字段和标准标题 21/21，但 Unit 4 目录只见 `QA-自检.md`，未见 Unit 4 内 `qa-manifest.csv`。

介入动作：

- Codex 准备给 manager 发一条低力度收口提醒：以当前 review queue + artifact truth 为唯一真相，不消费旧 verdict 做 closeout；要求 review_course 按 T-42/T-43/T-46 最新产物出新 verdict，并在 verdict 后再由 manager 结构化 closeout。

临时结果：

- 介入前状态：T-42/T-43/T-46 均待 review；T-44/T-45 仍未启动，需在 T-42/T-43 出 verdict 后尽快推动至少一个新学科进入生产。

明天修复建议：

- inbox/read 模块应支持“旧 verdict 失效”或按 task version/submit-review timestamp 过滤，manager closeout 时只允许消费最新 submit-review 之后的 authoritative verdict。

### 32. manager 处理最新收口提醒时再次 API retry，需绕过 manager 给 review_course 窄指令

触发时间：2026-06-23 02:56 CST

触发原因：

- Codex 已向 manager 投递 `msg_1782154478947_776443ac8b`，要求以最新 review queue 与 artifact truth 为唯一真相，但 manager pane 在处理该消息时出现 `API error · Retrying`。
- review_course 当前 inbox 无未读，review queue 仍有 T-42/T-43/T-46 等待复核；如果继续等待 manager 消费，T-42/T-43 的最新产物 verdict 会继续延迟。
- T-44/T-45 仍 assigned，今晚多学科目标需要先让 T-42/T-43 至少一个非 Calc 学科完成 QA verdict 后推动下一科。

现场证据：

- `tmux capture-pane -t EduFlowTeam:manager -p -S -80` 显示 `codex → manager（msg_1782154478947_776443ac8b）` 后出现 `API error · Retrying in 1s · attempt 3/10`。
- `./scripts/eduflowteam inbox manager` 显示 manager 仍有 21 unread，含 Codex 最新提醒与多条旧 verdict。
- `./scripts/eduflowteam inbox review_course` 显示 no unread messages。
- `./scripts/eduflowteam task review-queue --reviewer review_course` 显示 T-42、T-43、T-46 awaiting review。

介入动作：

- Codex 准备绕过 manager，直接给 review_course 发窄范围指令：只基于当前 review queue 与最新 artifact truth 审 T-42/T-43/T-46，忽略旧 verdict，出具新的 authoritative verdict。

临时结果：

- 待 review_course 消费后再核对 task truth 是否写入 verdict；如果 verdict 出现但 task truth 未消费，再记录并推动 manager closeout 对齐。

明天修复建议：

- runtime guard 对 manager pane 的 API retry 应触发自动 provider fallback 或代理 closeout handoff；review 队列已有任务时，不应因为 manager retry 阻塞 reviewer 接收最新复核口径。

### 33. review_course runtime 声明为不可用 deepseek 配置，导致最新 verdict 无法落地

触发时间：2026-06-23 03:00 CST

触发原因：

- review_course 已收到 Codex 最新复核口径 `msg_1782154650029_f7d458f9f8`，但 pane 持续 `API error / 429 / retry`，未消费该消息。
- `runtime verify review_course --json --live-smoke` 显示当前声明 runtime 为 `review_backup_deepseek`，但环境校验失败：`env_profile 'claude_proxy_deepseek_backup' not in config`。
- T-42/T-43/T-46 已在 review queue 等待 verdict，reviewer runtime 配置错误会直接阻断 QA 闭环，并拖住 T-44/T-45 启动。

现场证据：

- `./scripts/eduflowteam inbox review_course` 显示 `msg_1782154650029_f7d458f9f8` unread。
- `tmux capture-pane -t EduFlowTeam:review_course -p -S -80` 显示处理该消息时出现 `API error · Retrying`。
- `./scripts/eduflowteam runtime verify review_course --json --live-smoke` 返回 `verdict=env_drift`、`declared_runtime=review_backup_deepseek`、`env_ok=false`、`mismatches=[\"env_profile 'claude_proxy_deepseek_backup' not in config\"]`。
- `./scripts/eduflowteam task review-queue --reviewer review_course` 显示 T-42、T-43、T-46 均 awaiting review。
- 最新 artifact QA：T-42 15/15 schema+标题齐；T-43 45/45 schema+标题齐且 manifest/QA 存在；T-46 21/21 schema+标题齐但 Unit 4 manifest 缺失且 QA 仍写 8/24。

介入动作：

- Codex 准备执行 runtime repair：把 review_course 切回配置存在且可验证的 runtime（优先 `review_primary` 或 `review_backup_minimax`），做 smoke verify，再让 review_course 消费最新复核口径并输出 authoritative verdict。

临时结果：

- 介入前状态：review 队列卡住，T-42/T-43 不应再等旧 reviewer pane 自愈；T-46 应保持 NEEDS_FIX 风险，不可 closeout。

明天修复建议：

- runtime config 应在切换前验证 `env_profile` 是否存在；禁止把 agent 切到未配置 profile 的 runtime。runtime guard 发现 `env_drift` 后应自动选择链路中下一个可用 runtime 并重新投递未读高优消息。

### 34. review_course 切回 primary 后 smoke failed，最新复核消息仍未消费

触发时间：2026-06-23 03:02 CST

触发原因：

- Codex 依据 #33 做 runtime repair，将 review_course 从不可用的 `review_backup_deepseek` 切回配置存在的 `review_primary`。
- 切换命令完成后返回 `outcome=smoke_failed`，后续 verify 仍为 `smoke_failed`，说明 reviewer 不能稳定恢复工作。
- 最新复核口径消息仍未读，T-42/T-43/T-46 verdict 继续卡住。

现场证据：

- `./scripts/eduflowteam runtime switch review_course review_primary --reason ap_monitor_review_queue_blocked_env_drift --json` 返回 `outcome=smoke_failed`、`verdict=smoke_failed`。
- `./scripts/eduflowteam runtime verify review_course --json --live-smoke` 返回 `declared_runtime=review_primary`、`env_ok=true`、`smoke_ok=false`、`smoke_verdict=failed`。
- `./scripts/eduflowteam inbox review_course` 仍显示 `msg_1782154650029_f7d458f9f8` unread。

介入动作：

- Codex 准备继续 runtime repair：切到配置链路中的下一候选 `review_backup_minimax`，做 smoke verify；若仍失败，再考虑 operator review fallback，只对 T-42/T-43/T-46 输出结构化 QA verdict，不大规模改写内容。

临时结果：

- review queue 仍阻塞；T-42/T-43 产物可审但缺 authoritative verdict；T-46 仍有 QA/manifest mismatch 风险。

明天修复建议：

- runtime switch 工具在 smoke failed 后应自动尝试下一个 fallback，并把失败 runtime 标记 cooling down，避免 agent 停在不可用 provider 上等待人工二次切换。

### 35. review_course runtime 修复到 minimax 成功，但复核消息仍需重新消费

触发时间：2026-06-23 03:03 CST

触发原因：

- 在 #34 的 `review_primary` smoke failed 后，Codex 继续切换到配置存在的 `review_backup_minimax`。
- runtime 已恢复为 `proved_ready`，但原复核口径消息 `msg_1782154650029_f7d458f9f8` 仍处于 unread，review queue 尚未产出新 verdict。
- 需要把 runtime 恢复与业务队列恢复分开验证，避免误把“pane ready”当“review 已完成”。

现场证据：

- `./scripts/eduflowteam runtime switch review_course review_backup_minimax --reason ap_monitor_review_primary_smoke_failed --json` 返回 `outcome=ready`、`verdict=proved_ready`。
- `./scripts/eduflowteam runtime verify review_course --json --live-smoke` 返回 `declared_runtime=review_backup_minimax`、`env_ok=true`、`smoke_ok=true`、`pane_clean=true`、`inbox_state=consumed`。
- `./scripts/eduflowteam inbox review_course` 仍显示 `msg_1782154650029_f7d458f9f8` unread。

介入动作：

- Codex 准备重新提醒 review_course 消费最新复核口径，并在下一轮检查 T-42/T-43/T-46 是否出现 authoritative verdict 与 task truth 对齐。

临时结果：

- runtime 层已恢复；业务层仍待 review_course 消费消息并输出 verdict。

明天修复建议：

- runtime repair 完成后应自动重新投递/置顶未读高优消息，并触发一次 inbox consumer smoke，确认 agent 不只是 ready，而是真的开始处理积压任务。

### 36. 触发 operator review fallback：只写结构化 QA verdict，不改 AP 内容

触发时间：2026-06-23 03:05 CST

触发原因：

- review_course runtime 已恢复为 `review_backup_minimax` 且 `proved_ready`，但业务层仍未消费 `msg_1782154650029_f7d458f9f8` 与 `msg_1782155025986_962d959747`。
- manager 仍存在 env drift / 429，无法稳定消费旧 verdict 或推动 closeout。
- T-42/T-43/T-46 已长期停在 `submitted_for_review` / `verdict=pending`，review queue 不动会阻塞 T-44/T-45 启动，影响今晚 4-5 学科目标。
- Codex 已完成 artifact QA：T-42/T-43 可结构化通过；T-46 仍有 QA/manifest mismatch，必须拒绝并返修，不能误 closeout。

现场证据：

- `./scripts/eduflowteam inbox review_course` 显示 2 unread：`msg_1782154650029_f7d458f9f8`、`msg_1782155025986_962d959747`。
- `./scripts/eduflowteam task review-queue --reviewer review_course` 显示 T-42、T-43、T-46 awaiting review。
- `./scripts/eduflowteam task get T-42/T-43/T-46` 均为 `submitted_for_review`、`verdict=pending`。
- T-42 artifact QA：15 个 `U*.md`，manifest/QA 存在，Unit/Topic/Subtopic、knowledge_point/core_concept/exam_pattern/question_type/difficulty/common_mistake/explanation_context、`## Options/## Answer/## Explanation` 均 15/15。
- T-43 artifact QA：45 个 `U*.md`，manifest/QA 存在，核心字段与标准标题均 45/45；QA 写 15 subtopics、45 items，与 manifest 一致。
- T-46 artifact QA：21 个 `U*.md`，核心字段与标准标题 21/21，但 Unit 4 目录 `manifest_files=0`，QA 仍写 `子主题数 8`、`题目总数 24`、`manifest 8 行`，实际 21 items/7 subtopics。
- 代码核查：`task review` 只写 review outcome / latest_authoritative_verdict，不自动 manager closeout。

介入动作：

- Codex 准备执行最小 operator review fallback：
  1. `task review T-42 --actor review_course --approve`，evidence 标明 operator fallback、15 item/schema/manifest/QA PASS。
  2. `task review T-43 --actor review_course --approve`，evidence 标明 operator fallback、45 item/schema/manifest/QA PASS。
  3. `task review T-46 --actor review_course --reject`，reason 指向 Unit 4 QA/manifest mismatch，要求修正 manifest 与 QA 7/21/7。

临时结果：

- 待执行后验证 task truth、review queue 与 latest_authoritative_verdict 是否对齐；不做 manager closeout，不直接修改 AP 内容。

明天修复建议：

- 增加“operator review fallback”显式工具和标记字段，限定只在 reviewer runtime 卡死且 artifact QA 已可复核时使用；所有 fallback verdict 必须带 evidence_packet、artifact counts、字段计数和原因，便于第二天复盘。

### 37. operator review fallback 首次写入失败：review_reason 使用了非法枚举

触发时间：2026-06-23 03:07 CST

触发原因：

- Codex 按 #36 尝试用 `task review` 写入 T-42/T-43/T-46 结构化 verdict，但 `--reason` 使用了自定义字符串。
- `task review` 对 `review_reason` 有固定枚举，非法 reason 被拒绝，导致三条 verdict 均未写入。

现场证据：

- `./scripts/eduflowteam task review T-42 ... --reason operator_review_fallback_artifact_qa_pass_runtime_blocked` 返回 `invalid review_reason`，合法值包括 `approved_for_delivery`、`changes_requested` 等。
- T-43 同样因 `operator_review_fallback_artifact_qa_pass_runtime_blocked` 被拒绝。
- T-46 因 `operator_review_fallback_manifest_qa_mismatch` 被拒绝。
- 后续 `task get T-42/T-43/T-46` 均仍为 `submitted_for_review`、`verdict=pending`，说明失败没有污染 task truth。

介入动作：

- Codex 准备用合法枚举重试：T-42/T-43 使用 `approved_for_delivery`，T-46 使用 `changes_requested`，把 operator fallback 原因保留在 `--summary` 和 `--evidence-json` 中。

临时结果：

- 结构化 verdict 尚未落地；review queue 仍等待处理。

明天修复建议：

- CLI 应在 `task review --help` 中列出合法 `--reason` 枚举，或者允许 `evidence_json.reason` 承载自定义 fallback 原因，避免 operator 在紧急修复时反复试错。

### 38. operator review fallback 成功落地，review queue 清空但 manager 未 closeout

触发时间：2026-06-23 03:12 CST

触发原因：

- #36/#37 后 Codex 使用合法 review_reason 重试 operator fallback，T-42/T-43/T-46 的结构化 verdict 已写入 task truth。
- 这是对 reviewer runtime/inbox 卡住的最小结构化兜底，不是 manager closeout；仍需防止 manager 后续消费旧 inbox verdict 导致状态回滚。

现场证据：

- `./scripts/eduflowteam task review-queue --reviewer review_course` 返回 `no tasks awaiting review`。
- `./scripts/eduflowteam task get T-42` 显示 `status=delivered`、`verdict=approved`、`review_reason=approved_for_delivery`，summary 标记 `Operator fallback review`，artifact count 15。
- `./scripts/eduflowteam task get T-43` 显示 `status=delivered`、`verdict=approved`、`review_reason=approved_for_delivery`，summary 标记 `Operator fallback review`，artifact count 45。
- `./scripts/eduflowteam task get T-46` 显示 `status=in_progress`、`verdict=rejected`、`review_reason=changes_requested`，summary 指出 Unit 4 manifest 缺失、QA 仍写 8/24/8。
- `./scripts/eduflowteam inbox manager` 仍有 21 unread，其中包含 02:52 左右旧 review verdict 与旧进度消息。

介入动作：

- Codex 已将 heartbeat 巡检基线更新为最新 task truth，避免下一轮继续按旧 `submitted_for_review` 状态判断。
- Codex 不做 manager closeout、不改 AP 内容，只把 T-42/T-43/T-46 的 review truth 从阻塞状态扶正。

临时结果：

- T-42/T-43 可作为已通过 QA 的题库智能体基础样本，但需要 manager 后续只按当前 task truth 做 closeout。
- T-46 保持返修态；T-44/T-45 仍未启动，下一步应推动 manager 或 worker_course 启动新学科。

明天修复建议：

- 增加 review fallback 后的 manager reconciliation 工具：自动生成“当前唯一真相”并标记旧 verdict 为 stale，防止 manager 从 unread inbox 恢复时误消费旧消息。

### 39. manager runtime live-smoke 与 health 摘要不一致，且现场仍出现 429

触发时间：2026-06-23 03:12 CST

触发原因：

- health 摘要显示 manager `proved_ready`，但 live-smoke 直接验证返回 `env_drift`，tmux 现场仍停在 Kimi/usage limit 429。
- manager inbox 未消费 Codex 02:54 的扶正指令，T-44/T-45 继续停在 assigned，生产链有停滞风险。

现场证据：

- `./scripts/eduflowteam runtime verify manager --json --live-smoke` 返回 `verdict=env_drift`，`declared_runtime=manager_backup_qwen_plus`，declared Kimi env 与 live DashScope/Qwen env 不一致。
- `tmux capture-pane -t EduFlowTeam:manager -p -S -80` 显示 `API Error: Request rejected (429)`，并停在 `You've reached your usage limit`。
- `./scripts/eduflowteam inbox manager` 显示 `msg_1782154478947_776443ac8b` 等 21 unread。
- `./scripts/eduflowteam task get T-44/T-45` 均为 `assigned`、`workflow_gate_status=waiting_worker_acceptance`。

介入动作：

- Codex 准备执行 runtime repair：优先把 manager 切到 `manager_backup_minimax` 并 live-smoke 验证；若仍不可用，则绕过 manager 做窄范围 worker_course 指令，仅推动 T-44/T-45 worker acceptance / start，不做内容改写。

临时结果：

- 介入前状态：manager 不可作为稳定 closeout/dispatch owner；T-42/T-43 已通过但未 manager closeout，T-44/T-45 未启动。

明天修复建议：

- health 应把 live-smoke 结果与 pane 最近错误合并进最终红黄灯；当 pane 出现 429 且 env_drift 时，不应继续显示 manager `proved_ready`，并应自动切换到下一可用 runtime。

### 40. T-44/T-45 worker acceptance 已有日志信号，但 task truth 仍停在 assigned

触发时间：2026-06-23 03:14 CST

触发原因：

- supervisor-check 检出 T-44 AP Statistics Unit 1、T-45 AP Psychology Unit 1 均存在 worker_course accepted/started 日志信号，但 task truth 仍为 `assigned` / `waiting_worker_acceptance`。
- manager runtime 虽已切到 `manager_backup_minimax` 且 live-smoke ready，但 tmux pane 仍出现 API retry，manager inbox 仍 21 unread，短时间内不能依赖 manager 自动消化旧消息后推进结构状态。
- 如果不做最小扶正，T-44/T-45 会继续表现为“已派单但未启动”，影响 4-5 学科目标。

现场证据：

- `./scripts/eduflowteam task supervisor-check --json` 返回 `worker_accepted_missing_transition`：
  - T-44 `log_id=log_1782151593171_9eb5223e5d`，建议 transition to in_progress。
  - T-45 `log_id=log_1782151596201_8048c19a97`，建议 transition to in_progress。
- `./scripts/eduflowteam task get T-44/T-45` 均显示 `status=assigned`、`workflow_gate=dispatch_acceptance_gate`、`workflow_next_action=worker_start_or_ack`。
- `./scripts/eduflowteam runtime verify manager --json --live-smoke` 返回 `proved_ready`，但 `tmux capture-pane -t EduFlowTeam:manager` 仍显示 `API error · Retrying`。

介入动作：

- Codex 准备先查 task CLI 是否支持安全的 workflow/flow transition；若有结构化 transition 命令，则把 T-44/T-45 最小推进到 `in_progress`，并保留 worker_course 作为 owner，不改任何 AP 内容。
- 若没有安全 transition 命令，则向 worker_course 发窄指令：只处理 T-44/T-45 acceptance/start 与产物生产，不绕过 review queue。

临时结果：

- 介入前状态：T-42/T-43 delivered/approved；T-46 in_progress/rejected；T-44/T-45 assigned 但有 acceptance 日志，需结构同步。

明天修复建议：

- inbox/log accepted signal 应自动驱动 task workflow gate 从 `dispatch_acceptance_gate` 到 `production_in_progress`，或至少生成可一键确认的 manager action；避免 worker 已经开始但 dashboard 仍显示未启动。

### 41. Codex 最小结构修复：T-44/T-45 已从 assigned 推进到 in_progress

触发时间：2026-06-23 03:15 CST

触发原因：

- #40 已确认 T-44/T-45 有 worker acceptance 日志但 task truth 未推进。
- manager 虽切换 runtime 后 live-smoke ready，但 inbox 未读旧消息仍多，pane 仍有 API retry 现场，不宜等待其自行恢复后再处理已确认的结构状态漂移。

现场证据：

- `./scripts/eduflowteam task flow-transition T-44 --to in_progress --actor worker_course` 返回 `transitioned T-44 -> in_progress`，并自动向主群发布 stage reassurance。
- `./scripts/eduflowteam task flow-transition T-45 --to in_progress --actor worker_course` 返回 `transitioned T-45 -> in_progress`，并自动向主群发布 stage reassurance。
- 本动作只改 task/workflow 状态，不改 AP 知识库内容，不新增题目。

介入动作：

- Codex 使用 EduFlow task workflow 工具做最小结构同步，保持 `worker_course` 为 actor/owner，让生产链继续沿 workflow 走。
- 下一步立即验证 T-44/T-45 task/workflow 状态、worker_course inbox 与实际 AP 产物是否开始出现。

临时结果：

- T-44 AP Statistics Unit 1 和 T-45 AP Psychology Unit 1 已进入 `in_progress`，从“未启动/等待接受”转为“生产中”。

明天修复建议：

- 将 supervisor-check 的 `worker_accepted_missing_transition` 从 dry-run 提示升级为可控 auto-advance：当 accepted log、assignee、workflow gate 三类证据一致时，可自动推进到 `in_progress` 并记录 action event。

### 42. T-44/T-45 已 in_progress 但 gate 跳到 review handoff，目标目录仍无产物

触发时间：2026-06-23 03:17 CST

触发原因：

- #41 的最小结构修复把 T-44/T-45 从 assigned 推进到 in_progress，但 workflow status 显示 gate 已到 `review_handoff_gate` / `next_action=submit_review`。
- AP Statistics 与 AP Psychology 目标目录下尚未出现 `U*.md`、`QA-自检.md` 或 `qa-manifest.csv`，说明不应进入 review handoff。
- worker_course inbox 仍有旧消息 `T-44/T-45 继续按序等待`，可能让 worker 继续忽略新学科生产。

现场证据：

- `./scripts/eduflowteam task workflow-status T-44` 显示 `status=in_progress`、`gate=review_handoff_gate`、`gate_status=waiting_review_handoff`、`next_action=submit_review`。
- `./scripts/eduflowteam task workflow-status T-45` 同样显示 `review_handoff_gate` / `submit_review`。
- `find "$APBASE/AP Statistics" ...` 与 `find "$APBASE/AP Psychology" ...` 未返回 Unit 1 item、QA 或 manifest 文件。
- `./scripts/eduflowteam inbox worker_course` 仍显示旧 unread：`T-46 已收到。请立即开始 T-43... T-44/T-45 继续按序等待。`

介入动作：

- Codex 准备给 worker_course 发窄指令：当前唯一真相为 T-44/T-45 已 in_progress，但无产物；先执行 T-44 AP Statistics Unit 1 的实际 item/QA/manifest 生产，完成后再 submit-review，不要直接提交空 review。

临时结果：

- 介入前状态：T-44/T-45 是生产中但无文件证据，必须按 workflow 回到生产动作，而不是 review handoff。

明天修复建议：

- `flow-transition assigned -> in_progress` 不应自动把 gate 推到 `review_handoff_gate`；应该进入 `production_in_progress`，并要求 evidence_files 或 item_count 出现后才能开放 submit-review。

### 43. Codex 已向 worker_course 发出 T-44 窄生产指令

触发时间：2026-06-23 03:18 CST

触发原因：

- #42 确认 T-44/T-45 状态已经 in_progress，但实际产物为空，且 worker_course 仍有旧 unread 指示其继续等待 T-44/T-45。
- manager inbox 未读旧消息多，短期内不适合作为唯一调度入口；为了不让今晚多学科目标停滞，Codex 按 intervention ladder 采用“direct role instruction”。

现场证据：

- `./scripts/eduflowteam inbox worker_course` 显示旧 unread `msg_1782153006545_9105651980`，内容为 `T-44/T-45 继续按序等待`。
- T-44/T-45 task truth 已是 `in_progress`，但 AP Statistics/Psychology 目标目录无产物。

介入动作：

- Codex 执行：
  - `./scripts/eduflowteam send worker_course codex "<T-44 窄指令>" 高`
- 返回 `local_id=msg_1782155879857_9ba82aea1b`。
- 指令要求 worker_course：忽略旧等待口径；先做 T-44 AP Statistics Unit 1 actual items、QA、manifest；产物一致后再 submit-review；不要扩 Unit 2，不要空 review，不改 T-42/T-43/T-46。

临时结果：

- 等待下一轮验证 worker_course 是否消费该消息、是否开始生成 AP Statistics Unit 1 文件。

明天修复建议：

- 当 manager runtime 卡住时，direct role instruction 应有系统级“supersedes stale inbox”标记，避免 worker 同时看到旧等待口径和新执行口径。

### 44. worker_course live-smoke 与 tmux 现场不一致，新 T-44 指令未消费且 AP Statistics 仍 0 item

触发时间：2026-06-23 03:18 CST

触发原因：

- Codex 已向 worker_course 发出 T-44 AP Statistics 窄生产指令，但 worker_course inbox 仍显示该消息 unread。
- runtime verify 返回 `proved_ready`，但 tmux pane 现场仍显示 Kimi 429 API retry，说明 live-smoke/inbox_state 与实际工作 pane 不一致。
- AP Statistics Unit 1 目标目录 item count 仍为 0，生产未真正开始。

现场证据：

- `./scripts/eduflowteam inbox worker_course` 显示 2 unread：旧 `msg_1782153006545_9105651980` 与新 `msg_1782155879857_9ba82aea1b`。
- `tmux capture-pane -t EduFlowTeam:worker_course -p -S -120` 显示 `API Error: Request rejected (429)` 和 `API error · Retrying`。
- `./scripts/eduflowteam runtime verify worker_course --json --live-smoke` 返回 `proved_ready`、`runtime=course_backup_qwen_plus`，与 pane 现场冲突。
- AP Statistics Unit 1 目标目录 `find ... -name 'U*.md' | wc -l` 返回 0。

介入动作：

- Codex 准备执行 runtime repair：将 worker_course 从 `course_backup_qwen_plus` 切到下一候选 `course_backup_minimax` 并做 live-smoke；若恢复，则等待其消费 T-44 指令并开始产物生成。

临时结果：

- 介入前状态：T-44/T-45 虽为 in_progress，但 T-44 无文件产物，worker_course 实际不可用。

明天修复建议：

- runtime verify 应检查当前 tmux pane 最近 N 行是否仍有 API retry/429；如果有，不应返回 `pane_clean=true` 或 `inbox_state=consumed`。

### 45. worker_course runtime switch 出现短暂状态不同步，二次验证后确认 minimax 已接管

触发时间：2026-06-23 03:19 CST

触发原因：

- Codex 按 #44 切换 worker_course 到 `course_backup_minimax`，首次 switch 返回 `ready_unproven` 且 exit code 2。
- 紧随其后的 `runtime list worker_course --json` 仍显示 `current_runtime=course_backup_qwen_plus`，但二次 live-smoke 与 tmux pane 又显示 minimax 已实际接管。
- 这类短暂不同步会误导监控判断，必须记录。

现场证据：

- `./scripts/eduflowteam runtime switch worker_course course_backup_minimax --reason ap_monitor_worker_course_qwen_429_t44_unread --json` 返回 `outcome=ready_unproven`、`verdict=ready_unproven`、`from_runtime=course_backup_qwen_plus`。
- 随后 `./scripts/eduflowteam runtime list worker_course --json` 一度仍显示 `selected=true` 在 `course_backup_qwen_plus`。
- 二次 `./scripts/eduflowteam runtime verify worker_course --json --live-smoke` 返回 `verdict=proved_ready`、`declared_runtime=course_backup_minimax`、`env_ok=true`、`smoke_ok=true`。
- `tmux list-panes -t EduFlowTeam:worker_course` 显示 live env 为 `ANTHROPIC_BASE_URL=https://api.minimaxi.com/anthropic`、`ANTHROPIC_MODEL=MiniMax-M3`。

介入动作：

- Codex 以二次 live-smoke + tmux 启动命令为准，暂判 worker_course runtime 已恢复。
- 下一步继续验证 inbox 是否消费 `msg_1782155879857_9ba82aea1b`，以及 AP Statistics Unit 1 是否出现 item/QA/manifest 文件。

临时结果：

- worker_course runtime 层已恢复；业务层是否恢复仍待 inbox 与文件产物验证。

明天修复建议：

- runtime switch 应在写 current_runtime 前后保持原子性；若返回 `ready_unproven`，应明确说明是否已写入 state，避免 `runtime list` 与 `runtime verify` 短时间给出相反结论。

### 46. worker_course runtime 切到 minimax 后业务仍未恢复，T-44 新指令未消费

触发时间：2026-06-23 03:21 CST

触发原因：

- #45 确认 worker_course tmux/env 已切到 minimax，但业务层仍没有消费 T-44 窄生产指令。
- health 将 worker_course 标为 `ready_unproven` 且 runtime guard 需要 manager action，说明 runtime guard 未认可恢复。
- AP Statistics Unit 1 仍无任何 item 产物。

现场证据：

- `./scripts/eduflowteam inbox worker_course` 仍显示 `msg_1782155879857_9ba82aea1b` unread。
- `tmux capture-pane -t EduFlowTeam:worker_course -p -S -100` 显示仍停在旧启动 prompt/重试现场，没有处理新 inbox 的过程输出。
- `find .../AP Statistics/02-题库/items/Unit 1 -name 'U*.md' | wc -l` 返回 0。
- `./scripts/eduflowteam health` 显示 `worker_course: ready_unproven`，runtime guard: `needs_manager_action` / `escalation_needed`，route `course_backup_qwen_plus->course_backup_minimax`，`escalation=fallback_chain_exhausted`。

介入动作：

- Codex 准备尝试 lifecycle/runtime 层 clean restart 或 rehire worker_course，使其从新 pane 读取 inbox；仍不直接改 AP 内容。

临时结果：

- T-44/T-45 暂时只能标记为“结构 in_progress，但生产未落地 / runtime 风险阻塞”。

明天修复建议：

- runtime guard escalation 后应提供一键 clean restart + inbox replay；不要只把 pane 留在 half-ready 状态，让 task truth 显示 in_progress 但 agent 不消费消息。

### 47. worker_course fallback chain 抖动，Codex 准备 reidentify 唤醒 inbox 消费

触发时间：2026-06-23 03:22 CST

触发原因：

- worker_course runtime events 显示 watchdog 在 `course_backup_qwen_plus` 与 `course_backup_minimax` 间多次切换，均为 `ready_unproven`。
- worker_course 有 live pane，但仍未消费 T-44 新指令，说明仅 runtime switch 不足以恢复业务。
- `reidentify <agent>` 的实现只向单 agent pane 注入 identity/init prompt，不重启全队、不改内容，是当前最低力度的 inbox replay 尝试。

现场证据：

- `./scripts/eduflowteam runtime events --last 20 --json` 显示 worker_course 近期多条 `provider_unavailable` / `ready_unproven`，route 在 qwen/minimax 间抖动。
- `src/eduflow/commands/reidentify.py` 说明该命令 `Does NOT spawn a new pane or restart the CLI — only sends the init prompt as a fresh user message`。
- `./scripts/eduflowteam inbox worker_course` 仍显示 `msg_1782155879857_9ba82aea1b` unread。

介入动作：

- Codex 准备执行 `./scripts/eduflowteam reidentify worker_course`，让 worker_course 重新读取 identity 并处理 inbox。

临时结果：

- 待验证：worker_course 是否 ack/read T-44 指令，AP Statistics Unit 1 是否开始出现 item/QA/manifest。

明天修复建议：

- runtime guard 在 `ready_unproven + inbox unread` 持续存在时，应自动触发单 agent reidentify 或 clean inbox replay，而不是只做 provider fallback 抖动。

### 48. reidentify worker_course 后仍未消费 T-44 指令，Statistics 产物仍为空

触发时间：2026-06-23 03:24 CST

触发原因：

- Codex 已按 #47 执行 `reidentify worker_course`，但 25 秒后业务层仍无恢复。
- worker_course pane 仍停留在 API retry 状态，未运行 inbox 处理命令。
- AP Statistics Unit 1 目录仍没有 item 文件。

现场证据：

- `./scripts/eduflowteam reidentify worker_course` 返回 `re-injected identity init into worker_course`。
- 25 秒后 `./scripts/eduflowteam inbox worker_course` 仍显示 `msg_1782155879857_9ba82aea1b` unread。
- `tmux capture-pane -t EduFlowTeam:worker_course -p -S -120` 仍显示 `API error · Retrying`。
- `find .../AP Statistics/02-题库/items/Unit 1 -name 'U*.md' | wc -l` 仍返回 0。

介入动作：

- Codex 准备评估单 agent clean restart（fire/hire 或等价 lifecycle 操作），目标只恢复 worker_course inbox 消费，不停全队、不改 AP 内容。

临时结果：

- T-44/T-45 继续标记为：结构 in_progress，但生产未落地，worker_course runtime 阻塞。

明天修复建议：

- reidentify 应有 post-check：如果注入后 N 秒内 inbox unread 不下降、pane 仍有 retry，应自动升级到 clean restart，而不是让 operator 手动判断。

### 49. 准备执行 worker_course 单 agent clean restart

触发时间：2026-06-23 03:24 CST

触发原因：

- runtime switch 与 reidentify 均未让 worker_course 消费 T-44 指令。
- 继续等待会让 T-44/T-45 虽显示 in_progress 但没有产物，影响今晚多学科目标。
- 单 agent `fire/hire` 只作用于 worker_course，不停 manager/review_course/worker_builder，力度低于 operator 内容 fallback。

现场证据：

- `src/eduflow/commands/fire.py` 显示 `fire <agent>` 只 kill 指定 agent tmux window，并拒绝 fire manager。
- `src/eduflow/commands/hire.py` 显示 `hire <agent>` 只为指定 agent 创建 window 并 provision pane。
- #48 已记录 reidentify 后 T-44 指令仍 unread、AP Statistics 仍 0 item。

介入动作：

- Codex 准备执行：
  - `./scripts/eduflowteam fire worker_course`
  - `./scripts/eduflowteam hire worker_course`
- 目标是让 worker_course 从 clean pane 重新读取 inbox，继续 T-44 AP Statistics Unit 1 生产。

临时结果：

- 待执行后验证 runtime、inbox read/ack、T-44 文件产物。

明天修复建议：

- 将 `ready_unproven + unread high-priority + reidentify failed` 固化为自动 clean restart 梯度，减少夜间人工操作。

### 50. worker_course 单 agent clean restart 后仍未恢复业务消费

触发时间：2026-06-23 03:26 CST

触发原因：

- Codex 已执行单 agent `fire/hire worker_course`，但重启后仍未消费 T-44 高优指令，也未写入 AP Statistics 产物。
- runtime verify 与 tmux/inbox/文件证据继续冲突：verify 显示 `proved_ready`，但业务层仍卡住。

现场证据：

- `./scripts/eduflowteam fire worker_course && ./scripts/eduflowteam hire worker_course` 返回 `fired: worker_course` 与 `hired: worker_course`。
- 35 秒后 `./scripts/eduflowteam inbox worker_course` 仍显示 2 unread，包括 `msg_1782155879857_9ba82aea1b`。
- 35 秒后 `tmux capture-pane -t EduFlowTeam:worker_course -p -S -140` 仍显示 `API error · Retrying`。
- AP Statistics Unit 1 `U*.md` count 仍为 0。
- 同轮 `runtime verify worker_course --json --live-smoke` 返回 `proved_ready` / `course_primary`，说明 readiness verdict 仍不能代表业务恢复。

介入动作：

- Codex 记录 clean restart 失败；下一步只允许两类低风险恢复：
  1. 强制稳定到已知可用 fallback 并再次 reidentify/inbox replay；
  2. 若仍失败，为避免全线停摆，执行最小 operator fallback seed，仅针对 T-44 创建可审查的最小题库样本，并明确标记 fallback。

临时结果：

- T-44/T-45 仍是“结构 in_progress / 生产未落地 / worker_course runtime 阻塞”。

明天修复建议：

- 将 runtime readiness 从“CLI 能响应 smoke”改为“CLI 能消费指定 inbox 并产生状态或文件变化”；当前 smoke 与真实业务恢复脱节。

### 51. T-44/T-45 有启动信号但目标目录仍 0 item，manager 未消费启动消息

触发时间：2026-06-23 03:30 CST

触发原因：

- worker_course 在日志/manager inbox 中已发送 T-44 AP Statistics、T-45 AP Psychology “开始处理”信号。
- 但 AP Statistics / AP Psychology Unit 1 目标目录仍没有 `U*.md`、QA 或 manifest 文件，说明生产尚未落地。
- manager inbox 未读数增至 24，包含 worker_course 03:22-03:23 的 T-44/T-45 启动消息；manager 没有消费这些信号并更新更可靠的调度状态。

现场证据：

- `.eduflow-team-state/facts/logs.jsonl` 显示：
  - `log_1782155721712_f436e0228b`：worker_course 说 `AP Statistics Unit 1 题库生产（T-44）` 已开始处理。
  - `log_1782155724506_ccc4145ff3`：worker_course 说 `AP Psychology Unit 1 题库生产（T-45）` 已开始处理。
- `./scripts/eduflowteam inbox manager` 显示 24 unread，其中包括：
  - `msg_1782156179658_02db10ba85`：T-45 开始处理。
  - `msg_1782156180623_7a93729a11` / `msg_1782156181576_032a074306`：T-44 开始处理。
- `find .../AP Statistics/02-题库/items/Unit 1 -name 'U*.md' | wc -l` 返回 0。
- `find .../AP Psychology/02-题库/items/Unit 1 -name 'U*.md' | wc -l` 返回 0。
- `./scripts/eduflowteam task get T-44/T-45` 均为 `in_progress`，但 `workflow_gate=review_handoff_gate`、`next_action=submit_review`，与空目录不一致。

介入动作：

- Codex 先记录该不一致，暂不把 T-44/T-45 视为真实生产落地，也不允许基于启动口头信号进入 review。
- 下一步继续验证 worker_course 是否有后续文件变化；若仍没有，将按 intervention ladder 继续做最小扶正，优先修 workflow gate / inbox 消费，最后才考虑 operator fallback seed。

临时结果：

- T-44/T-45 当前状态应标为：生产中信号存在，但产物未落地，风险阻塞。

明天修复建议：

- manager closeout/进度面板必须区分 `started_signal` 与 `artifact_written`；没有 item/QA/manifest 文件时，不应把 gate 推到 `review_handoff_gate` 或允许 submit-review。

### 52. runtime verify 绿灯继续与 tmux/产物真相冲突，worker_course 被 manager-actions 判为上下文耗尽

触发时间：2026-06-23 03:32 CST

触发原因：

- `runtime verify` 对 manager / review_course / worker_course 均返回 `proved_ready`，但 live tmux pane 显示 manager 与 worker_course 仍卡在 Kimi 429/API retry。
- manager-actions 明确将 worker_course 标为 `worker_context_exhausted`，建议 `restart_worker_runtime`。
- T-44/T-45 仍无文件产物，说明 runtime 绿灯没有转化为生产恢复。

现场证据：

- `./scripts/eduflowteam runtime verify worker_course --json --live-smoke` 返回 `verdict=proved_ready`、`declared_runtime=course_primary`、`smoke_ok=true`。
- `tmux capture-pane -t EduFlowTeam:worker_course -p -S -80` 显示 `API Error: Request rejected (429)`，仍停在 CLI retry。
- `tmux capture-pane -t EduFlowTeam:manager -p -S -80` 同样显示 Kimi 429 usage limit。
- `./scripts/eduflowteam task manager-actions` 输出 context guard blocker：
  - `blocker=worker_context_exhausted`
  - `affected_agent=worker_course`
  - `recommended_action=restart_worker_runtime`
  - `allow_continue_original_task=false`
- AP Statistics / AP Psychology Unit 1 `U*.md` count 均为 0。

介入动作：

- Codex 记录该 runtime readiness 冲突，暂不把 `proved_ready` 作为业务恢复证据。
- 下一步评估是否进入 operator fallback seed：仅在继续等待/重启无效且 T-44/T-45 目标会停摆时，做最小可审查样本并显式标记 fallback，不做大规模改写。

临时结果：

- T-44/T-45 状态维持为：生产中信号存在，但无产物，worker_course runtime/context 风险阻塞。

明天修复建议：

- `runtime verify` 应加入“最新 pane 错误 + inbox 消费 + 文件/状态变化”三联验证；只做 API smoke 会误判长上下文 pane 的真实可用性。

### 53. 触发 T-44 最小 operator fallback seed：只建可审查样本，不冒充完整 Unit

触发时间：2026-06-23 03:35 CST

触发原因：

- worker_course 多轮 runtime switch / reidentify / fire-hire 后仍未在 AP Statistics Unit 1 目标目录写入任何 item。
- manager 与 worker_course pane 现场仍显示 429/API retry，manager 未消费 worker_course 的 T-44/T-45 启动消息。
- T-44/T-45 已被结构推进到 `in_progress`，但实际产物为空；继续等待会让今晚 4-5 学科目标停在“假启动”。
- AP Statistics 已有 `AP Statistics_题库优化版_知识点框架.md` 与 Unit 1 Topic 页面，可作为 fallback seed 的知识源，避免凭空生成。

现场证据：

- T-44/T-45 task truth：`in_progress`，但 `evidence-account` 缺 `items_count`、`manifest_evidence`、`manifest_rows`、review verdict。
- AP Statistics / AP Psychology Unit 1 目标目录 `U*.md` count 均为 0。
- `manager-actions` 显示 `worker_context_exhausted`，recommended_action=`restart_worker_runtime`，但 restart 已执行后仍无产物。
- AP Statistics 框架文件包含 Unit 1 Topic 1.1 的 Subtopic 1.1.1 / 1.1.2 结构字段：定义、核心概念、常见考法、易错点、题型、难度、解析背景。

介入动作：

- Codex 准备执行最小 operator fallback seed：
  - 范围仅 T-44 AP Statistics Unit 1 Topic 1.1。
  - 产出 2 个 subtopics × F/S/C = 6 个 item。
  - 同步 `QA-自检.md` 与 `qa-manifest.csv`。
  - 明确标记为 `operator_fallback_seed`，不声明完整 Unit 1 完成，不 submit review，后续仍需 worker_course 或 review_course 扩展/复核。

临时结果：

- 待执行后验证：6 个 item 是否包含 qbank-agent schema、`## Options` / `## Answer` / `## Explanation`，manifest/QA 是否与 6 item 一致。

明天修复建议：

- 系统应提供“fallback seed”一键工具：输入 task id、知识源、最小范围，自动生成带 fallback 标记的样本、manifest、QA，并阻止 manager 将其误判为完整交付。

### 54. T-44 AP Statistics operator fallback seed 已落地，但 task evidence-account 尚未同步

触发时间：2026-06-23 03:38 CST

触发原因：

- Codex 按 #53 执行最小 operator fallback seed，已在 AP Statistics Unit 1 目标目录写入 6 个可审查 item、QA 与 manifest。
- 但 `task evidence-account` 仍显示 T-44 缺 items_count / manifest_evidence / review verdict，说明结构化 task truth 还不知道这个 seed。
- 必须明确 seed-only 状态，避免 manager 或后续自动流程把 6 题 seed 误判为完整 Unit 1 交付。

现场证据：

- `find .../AP Statistics/02-题库/items/Unit 1 -name 'U*.md' | wc -l` 返回 6。
- 目标目录存在：
  - `U1.1.1-F.md` / `U1.1.1-S.md` / `U1.1.1-C.md`
  - `U1.1.2-F.md` / `U1.1.2-S.md` / `U1.1.2-C.md`
  - `QA-自检.md`
  - `qa-manifest.csv`
- 字段检查显示 `unit/topic/subtopic/knowledge_point/core_concept/exam_pattern/question_type/common_mistake/difficulty/explanation_context/operator_fallback_seed` 均为 6/6。
- 标题检查显示 `## Options` / `## Answer` / `## Explanation` 均为 6/6。
- `./scripts/eduflowteam task evidence-account --task-id T-44 --json` 仍显示 `items_count=null`、`manifest_evidence=null`、`latest_authoritative_review_verdict={}`、`closeout_ready=false`。

介入动作：

- Codex 已完成 seed 文件写入与基础 QA 验证。
- Codex 不 submit-review、不 closeout T-44；下一步只同步“seed-only 当前真相”，要求 manager/review_course 不得把它当完整 Unit 1。

临时结果：

- T-44 现在从“0 产物”变为“operator fallback seed 6 items 可审查”，但仍是未完成 / 需扩展 / 待正式 review。

明天修复建议：

- task evidence-account 应支持记录 `operator_fallback_seed` 类型 evidence，包含 seed item count、manifest path、QA path、full_unit_complete=false，避免文件层证据和 task truth 长期脱节。

### 55. 准备同步 T-44 seed-only 当前真相，防止 manager/review_course 误 closeout

触发时间：2026-06-23 03:38 CST

触发原因：

- #54 已确认 T-44 文件层有 6 item fallback seed，但 task evidence-account 仍为空。
- manager / review_course inbox 仍有旧消息，且 manager pane 现场存在 API retry 风险；如果后续只看到“Statistics 有文件”，可能误判为完整 Unit 1。

现场证据：

- T-44 task truth 仍为 `in_progress` / `verdict=pending`。
- `QA-自检.md` 已明确写入 `seed_only_not_full_unit`，但该信息尚未同步到 manager/review_course 的工作口径。

介入动作：

- Codex 准备向 manager 与 review_course 发送短指令：
  - 当前唯一真相：T-44 只有 operator fallback seed 6 items，不是完整 Unit 1。
  - 不得 closeout，不得空 submit-review。
  - 后续要么 review seed schema，要么让 worker_course 扩完整 Unit 1 后再 submit-review。

临时结果：

- 待发送后验证 inbox 是否出现消息；不期待 manager 立即消费，但要让结构化消息存在。

明天修复建议：

- fallback seed 写入后应自动发布一条 `seed_only` 状态事件到 task timeline，供 manager/reviewer/auto_ops 统一消费。

### 56. T-44 seed-only 口径已同步给 manager 与 review_course

触发时间：2026-06-23 03:40 CST

触发原因：

- #55 准备同步 seed-only 真相，防止 T-44 被误 closeout。

现场证据：

- `./scripts/eduflowteam send manager codex "<seed-only 当前真相>" 高` 返回 `local_id=msg_1782157190194_e56ade2c1b`。
- `./scripts/eduflowteam send review_course codex "<seed-level verdict 口径>" 高` 返回 `local_id=msg_1782157190232_311bc79dae`。

介入动作：

- Codex 已明确告知 manager：
  - T-44 只有 6 item operator fallback seed，不是完整 Unit 1。
  - 不得 closeout，不得把 seed 当完整交付。
  - T-45 Psychology 仍无产物，继续标风险阻塞。
- Codex 已明确告知 review_course：
  - 若审，只能审 seed schema/格式/概念质量。
  - 不得输出 T-44 full PASS，不得 closeout。

临时结果：

- seed-only 真相已进入 manager/review_course inbox；等待后续 patrol 验证是否被消费。

明天修复建议：

- 所有 operator fallback seed 消息应自动带 `full_unit_complete=false` 和 `review_scope=seed_only` 结构化字段，防止自然语言口径被忽略。

### 57. 03:47 patrol 发现心跳基线过旧、manager 高优未读与 T-45/T-46 卡点仍在

触发时间：2026-06-23 03:47 CST

触发原因：

- 本轮 fast patrol 不是正常无异常巡检：supervisor-check 仍给出 `health_status=escalated_failure`，并点名 `runtime_unhealthy`、`manager_high_priority_unread`、`stale_task_backlog`、`worker_context_risk`、`manager_idle_too_long`。
- 线程已有 active heartbeat，但自动化提示词里的当前基线仍是旧口径：仍写 T-44/T-45 `assigned/dispatch_acceptance_gate`，而 task truth 已是 `in_progress/review_handoff_gate`，且 T-44 已有 operator fallback seed。

现场证据：

- `./scripts/eduflowteam health` 显示 `runtime guard needs_manager_action: worker_course`、`escalation_needed: worker_course`，并显示 `anna` 无 tmux window、`worker_qbank` env drift。
- `./scripts/eduflowteam task supervisor-check --json` 输出 `primary_reason=runtime_unhealthy`，并列出：
  - `T-45 stale_task`：in_progress 超 30m 无 meaningful progress。
  - `T-46 latest_verdict_rejected_blocks_closeout`：latest authoritative verdict=rejected。
  - `msg_1782157190194_e56ade2c1b`：manager high-priority unread，内容是 T-44 seed-only 真相。
  - `runtime:worker_course worker_context_exhausted`。
- `./scripts/eduflowteam inbox manager` 显示 manager 仍有 25 unread，其中包含 `msg_1782157190194_e56ade2c1b`。
- 产物盘点：
  - T-46 AP Calculus AB Unit 4：21 个 `U*.md`，`QA-自检.md` 存在，`qa-manifest.csv` 缺失。
  - T-44 AP Statistics Unit 1：6 个 seed `U*.md`，`QA-自检.md` 与 `qa-manifest.csv` 存在，但不是 full Unit 1。
  - T-45 AP Psychology Unit 1：0 个 `U*.md`，无 QA，无 manifest。

介入动作：

- Codex 准备更新本线程 heartbeat prompt，让后续巡检使用最新 task truth，避免下一轮自动巡检按旧基线误判 T-44/T-45。
- Codex 准备给 manager 发一条窄范围指令：先消费 T-44 seed-only 真相；修复 T-46 manifest/QA 后重提 review；T-45 若 worker_course 仍不可用，标风险阻塞并给出最小 recovery 路径。

临时结果：

- 暂未改 AP 知识库内容；只做监控基础设施与 manager workflow 扶正。

明天修复建议：

- heartbeat prompt 应由 patrol 脚本自动从 task truth/artifact truth 生成短基线，避免人工提示词过期。
- supervisor-check 的 AP 任务关注列表应支持按本轮目标 task id 过滤，减少旧 IGCSE 任务噪音。

### 58. 已更新 heartbeat 基线并向 manager 发出窄范围扶正指令

触发时间：2026-06-23 03:48 CST

触发原因：

- #57 已确认自动巡检提示词基线过旧，且 manager 仍有 T-44 seed-only 高优消息未读。
- T-46 仍是 rejected，T-45 仍 0 产物；若 manager 继续按旧 inbox 消息推进，可能出现 T-44 seed 被误 closeout、T-46 未返修即完成、T-45 空提交。

现场证据：

- `codex_app.automation_update` 已更新 automation `ap-overnight-monitor-patrol`。
- `./scripts/eduflowteam send manager codex --stdin 高` 返回 `local_id=msg_1782157733253_096a972009`。
- 随后 `./scripts/eduflowteam inbox manager` 显示 manager unread 从 25 增至 26，说明新指令已进入 inbox。

介入动作：

- Codex 更新本线程 heartbeat prompt，写入最新基线：
  - T-42/T-43 为 package 级 approved，不是 subject closeout。
  - T-46 缺 Unit 4 `qa-manifest.csv` 且 QA 需修 7/21/7。
  - T-44 只有 operator fallback seed，`full_unit_complete=false`。
  - T-45 仍 0 item/无 QA/无 manifest。
- Codex 给 manager 发出最小三步指令：
  1. 消费 T-44 seed-only 真相，禁止 closeout/空 submit-review。
  2. 推 T-46 只修 manifest/QA 后重新 submit-review。
  3. 若 worker_course 仍不可用，把 T-45 标风险阻塞并同步 recovery。

临时结果：

- 后续 patrol 将按新基线运行。
- manager 指令已入 inbox，但尚未确认被消费；下一轮重点检查 `msg_1782157733253_096a972009` 是否 read/ack，以及 task truth 是否变化。

明天修复建议：

- manager inbox 应支持“当前真相置顶/撤销旧 verdict”机制，避免新指令和 02:52 旧消息混在同一未读堆里。

### 59. runtime verify 与 tmux live pane 再次矛盾，核心三角色实际卡在 Kimi 429

触发时间：2026-06-23 03:51 CST

触发原因：

- #58 发给 manager 的扶正指令需要 manager 消费，但 live tmux 显示 manager 正在 API retry，无法可靠消费。
- review_course 与 worker_course 同样显示 Kimi 429/usage limit；这会阻断 T-46 返修复核、T-44 seed-only 复核和 T-45 继续生产。

现场证据：

- `./scripts/eduflowteam runtime verify manager --json --live-smoke` 返回 `verdict=proved_ready`、`smoke_ok=true`、`pane_clean=true`。
- `./scripts/eduflowteam runtime verify review_course --json --live-smoke` 返回 `verdict=proved_ready`、`smoke_ok=true`、`pane_clean=true`。
- `./scripts/eduflowteam runtime verify worker_course --json --live-smoke` 返回 `verdict=proved_ready`、`smoke_ok=true`、`pane_clean=true`。
- 但 `tmux capture-pane` 显示：
  - manager pane: `API Error: Request rejected (429)`，并且 `API error · Retrying in 21s · attempt 7/10`。
  - review_course pane: `API Error: Request rejected (429)`。
  - worker_course pane: `API Error: Request rejected (429)`。
- review queue 仍为空，说明 review 链没有实际推进。

介入动作：

- Codex 准备执行 runtime 层最小修复：优先检查可用 runtime/switch/reidentify/hire 命令，避免继续只靠 inbox 催促。
- 修复目标是让 manager/review_course/worker_course 至少能消费当前高优消息并恢复 T-46/T-44/T-45 的 workflow 链。

临时结果：

- 暂未改 AP 知识库内容。
- 当前不可信 surface：`runtime verify --live-smoke`；当前可信 surface：tmux live pane + review queue + artifact truth。

明天修复建议：

- runtime verify 必须检测 pane 最近 N 行中的 `429`、`usage limit`、`Retrying`，并在发现时返回 `blocked`，不能只用独立 smoke test 判 ready。

### 60. 已对 manager/review_course 做 runtime 最小切换修复，worker_course 仍需重建

触发时间：2026-06-23 03:53 CST

触发原因：

- #59 确认核心三角色 live pane 卡在 Kimi 429，manager/review_course 无法可靠消费当前 AP 任务高优消息。

现场证据：

- `./scripts/eduflowteam runtime list manager --json` 显示 manager 可用链：`manager_primary`(dashscope)、`manager_backup_qwen_plus`(kimi)、`manager_backup_minimax`(minimax)，当前原为 `manager_backup_minimax`。
- `./scripts/eduflowteam runtime list review_course --json` 显示 review_course 可用链：`review_primary`(dashscope)、`review_backup_qwen_plus`(kimi)、`review_backup_minimax`(minimax)，当前原为 `review_backup_minimax`。
- runtime events 显示此前多次 provider fallback，worker_course 在 qwen/minimax 间反复 `ready_unproven`。

介入动作：

- Codex 执行：
  - `./scripts/eduflowteam runtime switch manager manager_primary --reason ap_monitor_live_pane_kimi_429_despite_verify_ready --json`
  - `./scripts/eduflowteam runtime switch review_course review_primary --reason ap_monitor_live_pane_kimi_429_despite_verify_ready --json`
- 两条命令均返回 `outcome=ready`、`verdict=proved_ready`。

临时结果：

- manager 与 review_course 已完成命令层 runtime 切换；还需 tmux live pane 复核是否真正脱离 429。
- worker_course declared runtime 虽是 `course_primary`，但 tmux pane 显示 Kimi 429，存在 pane/declared state 错位；下一步需对 worker_course 做重建或跨池切换。

明天修复建议：

- runtime switch 完成后应自动校验 pane header/base_url/provider 与 declared runtime 一致，发现错位时强制 rehire/reidentify。

### 61. runtime switch 后 health 变绿但 live pane 仍在旧 429 retry

触发时间：2026-06-23 03:55 CST

触发原因：

- #60 执行 runtime switch 后，health/status 层显示 manager/review_course/worker_course 均 `proved_ready`，但 live tmux 仍显示旧会话在 API retry，说明仅切换 runtime 声明不足以恢复实际执行。

现场证据：

- `./scripts/eduflowteam health` 显示：
  - manager: `proved_ready (runtime=manager_primary, pool=dashscope_coding)`
  - review_course: `proved_ready (runtime=review_primary, pool=dashscope_coding)`
  - worker_course: `proved_ready (runtime=course_backup_minimax, pool=minimax_official)`
- 但 `tmux capture-pane` 仍显示：
  - manager: `API error · Retrying ... attempt 8/10`
  - review_course: `API error · Retrying ... attempt 8/10`
  - worker_course: `API error · Retrying ... attempt 6/10`
- review queue 仍为空，且 manager 最新高优消息尚未被证实消费。

介入动作：

- Codex 准备升级到 pane/runtime 重建：优先使用项目已有 `fire`/`hire`/`reidentify` 命令重启对应 agent pane，再验证 inbox 消费和 tmux 现场。

临时结果：

- 当前 runtime truth 仍以 tmux live pane 为准；health 的 `proved_ready` 只能视为声明层恢复。

明天修复建议：

- `runtime switch` 后应自动杀掉或中断旧 provider retry 中的 pane，并以新 runtime 重启；否则会出现 declared runtime 与实际 pane execution 不一致。

### 62. 已重建 review_course 与 worker_course pane，manager 受保护未强杀

触发时间：2026-06-23 03:57 CST

触发原因：

- #61 确认 runtime switch 只改变声明层，live pane 仍在旧 429 retry；需要重建实际执行 pane，才能恢复 review 与生产链。

现场证据：

- `./scripts/eduflowteam fire manager` 返回 `refusing to fire manager (kill the tmux session yourself if you mean it)`，manager 受保护未被强杀。
- `./scripts/eduflowteam fire review_course` 返回 `✅ fired: review_course`。
- `./scripts/eduflowteam fire worker_course` 返回 `✅ fired: worker_course`。
- `./scripts/eduflowteam hire review_course` 返回 `✅ hired: review_course (claude-code) → EduFlowTeam:review_course`。
- `./scripts/eduflowteam hire worker_course` 返回 `✅ hired: worker_course (claude-code) → EduFlowTeam:worker_course`。

介入动作：

- Codex 未强杀 manager，避免破坏 manager 保护机制。
- Codex 已重建 review_course 与 worker_course pane，下一步验证新 pane 是否不再显示 429，并检查是否消费：
  - review_course: `msg_1782157190232_311bc79dae`
  - worker_course: `msg_1782155879857_9ba82aea1b`

临时结果：

- review_course / worker_course 执行位已重新拉起；是否真正恢复仍待 tmux 与 inbox 验证。

明天修复建议：

- 为 manager 提供安全的 `restart-manager-pane --preserve-state` 工具，避免监控员在 manager 卡 429 时只能手动强杀或等待。

### 63. pane 重建后 25 秒复核仍显示核心三角色卡在 429 retry

触发时间：2026-06-23 03:59 CST

触发原因：

- #62 重建 review_course 与 worker_course pane 后，需要确认是否真实恢复；25 秒后 tmux 仍显示 API retry，说明重建未解除 provider/CLI 卡死。

现场证据：

- `sleep 25 && tmux capture-pane ...` 显示：
  - review_course: `API error · Retrying in 35s · attempt 8/10`
  - worker_course: `API error · Retrying in 0s · attempt 7/10`
  - manager: `API Error: Request rejected (429)` 与 `API error · Retrying in 30s · attempt 7/10`
- `./scripts/eduflowteam inbox review_course` 仍显示 `msg_1782157190232_311bc79dae` unread。
- `./scripts/eduflowteam inbox worker_course` 仍显示 `msg_1782155879857_9ba82aea1b` unread。

介入动作：

- Codex 准备尝试最小中断恢复：向 manager/review_course/worker_course pane 发送 `C-c` 中断旧 retry，再让其处理最新 inbox；不改 AP 知识库内容，不执行 closeout。

临时结果：

- 当前生产链处于 runtime 阻塞态：
  - T-46 返修/复核无法靠 review_course 正常推进。
  - T-44 seed-only verdict 不能靠 review_course 正常消费。
  - T-45 full production 不能靠 worker_course 正常推进。

明天修复建议：

- fire/hire 应确认旧 CLI 进程是否真正退出；若新 pane 仍继承旧 retry，应提供强制清理子进程与干净启动的命令。

### 64. 已中断核心三角色旧 retry，准备让其只处理最新 inbox

触发时间：2026-06-23 04:01 CST

触发原因：

- #63 确认 manager/review_course/worker_course 仍在 429 retry；继续等待会导致 T-46/T-44/T-45 workflow 链停摆。

现场证据：

- `tmux send-keys ... C-c` 后复核显示三处 pane 均出现 `Interrupted · What should Claude do instead?`。
- manager pane 仍显示待处理最新 inbox 指令：`msg_1782157733253_096a972009`。
- review_course pane 需处理 T-44 seed-only 指令：`msg_1782157190232_311bc79dae`。
- worker_course pane 需处理 T-44/T-45 不允许空提交指令：`msg_1782155879857_9ba82aea1b`。

介入动作：

- Codex 准备向三个 pane 输入最小恢复指令：
  - manager：只读并消费最新 AP 监控指令，给三行状态包。
  - review_course：只消费 T-44 seed-only 消息，不输出 full Unit PASS。
  - worker_course：只消费 T-44/T-45 当前真相，先同步 blocker/next step，不空 submit-review。

临时结果：

- 已从 provider retry 卡死推进到可输入恢复指令状态；是否能成功执行仍待验证。

明天修复建议：

- pane 被中断后应自动注入“只处理最新 inbox”的 recovery prompt，并记录 message id，减少人工 tmux 操作。

### 65. 恢复指令已注入但未被执行，关键 inbox 仍未读

触发时间：2026-06-23 04:03 CST

触发原因：

- #64 注入恢复指令后，35 秒复核发现指令停留在 Claude Code prompt 中，没有产生 read/ack 或状态同步。

现场证据：

- `tmux capture-pane` 显示 manager/review_course/worker_course prompt 中均有 Codex 注入的恢复指令文本，但未见执行结果。
- `./scripts/eduflowteam inbox manager` 仍显示 `msg_1782157733253_096a972009` unread。
- `./scripts/eduflowteam inbox review_course` 仍显示 `msg_1782157190232_311bc79dae` unread。
- `./scripts/eduflowteam inbox worker_course` 仍显示 `msg_1782155879857_9ba82aea1b` unread。

介入动作：

- Codex 准备对三个 pane 再发送一次 `Enter`，触发已输入恢复指令提交。

临时结果：

- 当前不能把“恢复指令已注入”视为“执行链已恢复”；仍按 runtime/消息消费阻塞处理。

明天修复建议：

- tmux 注入恢复指令后，应自动验证 prompt 是否提交成功；若仍停在输入框，工具层应重发 Enter 或改用 paste-buffer + Enter。

### 66. 补发 Enter 后核心三角色仍回到 API retry，消息消费未恢复

触发时间：2026-06-23 04:06 CST

触发原因：

- #65 补发 Enter 后需要验证恢复指令是否执行；25 秒复核显示 manager/review_course/worker_course 再次进入 API retry，关键 inbox 仍未读。

现场证据：

- `tmux capture-pane` 显示：
  - manager: 恢复指令已提交后又出现 `API error · Retrying in 3s · attempt 6/10`。
  - review_course: 恢复指令已提交后又出现 `API error · Retrying in 0s · attempt 6/10`。
  - worker_course: 恢复指令已提交后又出现 `API error · Retrying in 0s · attempt 6/10`。
- `tail -n 40 .eduflow-team-state/facts/logs.jsonl` 未出现 manager/review_course/worker_course 对最新 AP 恢复指令的 read/ack；只看到 Hermes/auto_ops 继续报监督异常。
- inbox 仍显示：
  - manager: `msg_1782157190194_e56ade2c1b` 与 `msg_1782157733253_096a972009` 未读。
  - review_course: `msg_1782157190232_311bc79dae` 未读。
  - worker_course: `msg_1782155879857_9ba82aea1b` 未读。

介入动作：

- Codex 已停止继续叠加指令，避免制造更多未读消息和旧上下文噪音。
- 当前巡检将生产链状态标为 runtime/message-consumption blocked；下一轮 heartbeat 优先复核是否自动恢复，或决定是否需要更强 runtime 清理 / operator fallback。

临时结果：

- T-46 仍不能通过正常 worker/review 链完成 manifest/QA 返修。
- T-44 seed-only 真相仍未被 manager 正式消费，review_course 也未正式给 seed-level verdict。
- T-45 仍无产物，且 worker_course 未消费 recovery 指令。

明天修复建议：

- 需要一条“强制干净重启 agent CLI + 清空当前 retry 输入 + 指定 runtime + 自动 read 最新 inbox”的一键 recovery 命令。
- runtime guard 应在连续 2 次 pane retry 后阻止继续投递自然语言指令，改走结构化 recovery。

### 67. 04:04 patrol 复核仍未恢复，task/artifact truth 无实质变化

触发时间：2026-06-23 04:04 CST

触发原因：

- 新一轮 heartbeat/patrol 继续发现 manager/review_course/worker_course 未消费关键 AP 消息，T-46/T-44/T-45 没有新产出或新 review。
- `team` 状态已显示 manager/review_course 处于待接单，worker_course 处于 runtime guard 受阻；继续堆自然语言指令会增加噪音。

现场证据：

- `./scripts/eduflowteam task supervisor-check --json` 仍返回 `health_status=escalated_failure`，`primary_reason=runtime_unhealthy`，`consecutive_issue_count=9`。
- `./scripts/eduflowteam health` 显示：
  - manager: `proved_ready`，但 tmux live pane 仍显示 Kimi `429 usage limit`。
  - review_course: `smoke_failed`。
  - worker_course: `proved_ready`，但 runtime guard 仍 `needs_manager_action/escalation_needed`。
- `tmux capture-pane` 显示 manager/review_course/worker_course 均在处理恢复指令后回到 `API Error: Request rejected (429)`。
- `./scripts/eduflowteam inbox manager` 仍显示 26 unread，包含：
  - `msg_1782157190194_e56ade2c1b`：T-44 seed-only 真相。
  - `msg_1782157733253_096a972009`：03:47 patrol 最新三步指令。
- `./scripts/eduflowteam inbox review_course` 仍显示 `msg_1782157190232_311bc79dae` unread。
- `./scripts/eduflowteam inbox worker_course` 仍显示 `msg_1782155879857_9ba82aea1b` unread。
- AP 目录实物：
  - T-46: `U_COUNT=21`、`QA=yes`、`MANIFEST=no`。
  - T-44: `U_COUNT=6`、`QA=yes`、`MANIFEST=yes`，仍是 seed。
  - T-45: `U_COUNT=0`、`QA=no`、`MANIFEST=no`。

介入动作：

- Codex 不再向 manager/review_course/worker_course 追加自然语言指令。
- Codex 准备只读排查 runtime/env 配置，确认为什么 declared `primary` 仍打到 Kimi 429。
- `./scripts/eduflowteam reset --yes` 属全局重置，当前不执行。

临时结果：

- 当前生产链继续按 runtime/message-consumption blocked 处理。
- 正常 workflow 无法推进 T-46 返修、T-44 seed-level review、T-45 production。

明天修复建议：

- 需要将 `runtime verify`、`health`、`team` 三个 surface 的“ready/待接单/受阻”统一成单一 runtime truth，避免监控员面对互相矛盾的绿色/红色信号。
- 提供非全局、单 agent 的 `clean-restart --runtime <runtime> --consume-latest-inbox <msg_id>`。

### 68. 准备对 T-46 做最小 operator fallback，补 manifest 与 QA 计数

触发时间：2026-06-23 04:04 CST

触发原因：

- T-46 AP Calculus AB Unit 4 只剩结构性 QA/manifest 缺口，但正常 worker/review 链已连续多轮卡在 runtime/message-consumption blocked。
- 缺口很窄：21 个 item 已存在，schema/title 已在前序巡检通过；当前阻塞是缺 `qa-manifest.csv`，以及 `QA-自检.md` 仍写旧的 8/24/8 口径。

现场证据：

- `./scripts/eduflowteam task get T-46`：`status=in_progress`、`verdict=rejected`、`review_reason=changes_requested`。
- `./scripts/eduflowteam task evidence-account --task-id T-46 --json`：`latest_authoritative_review_verdict.verdict=rejected`，`items_count=21`，缺 `manifest_evidence/manifest_rows`。
- AP 目录盘点：
  - `/AP Calculus AB/02-题库/items/Unit 4/` 下 `U_COUNT=21`。
  - `QA-自检.md` 存在。
  - `qa-manifest.csv` 不存在。
- manager/review_course/worker_course live pane 仍显示 Kimi 429，关键 inbox 未读，无法依赖正常 review 链及时完成此窄修复。

介入动作：

- Codex 准备做最小 operator fallback：
  - 读取 Unit 4 现有 item frontmatter 与相邻 Unit manifest 格式。
  - 新增 Unit 4 `qa-manifest.csv`。
  - 只修 `QA-自检.md` 中的计数口径为 7 subtopics / 21 items / 7 manifest rows。
- 边界：不改 21 个题目正文，不扩 Unit，不宣称 T-46 已 review approved；修完后只标为“operator fallback structure fixed，待 review/任务真相同步”。

临时结果：

- 待执行文件层窄修复并复核。

明天修复建议：

- 当 reviewer 已指出机械性 QA/manifest 缺口且 worker runtime 卡死时，系统应提供 `operator-fallback-structure-fix` 标准流程，自动写入 task evidence，避免人工编辑后 task truth 脱节。

### 69. T-46 operator fallback 结构修复已落盘并通过文件层复核

触发时间：2026-06-23 04:10 CST

触发原因：

- #68 已确认 T-46 的剩余缺口是窄范围结构问题，且正常 worker/review 链不可用。

现场证据：

- 修改文件：
  - `/Volumes/Halobster/Obsidian Edu/留学公司知识库/01-留学课程通用知识/03-AP知识库/03-学科知识/AP Calculus AB/02-题库/items/Unit 4/QA-自检.md`
  - `/Volumes/Halobster/Obsidian Edu/留学公司知识库/01-留学课程通用知识/03-AP知识库/03-学科知识/AP Calculus AB/02-题库/items/Unit 4/qa-manifest.csv`
- 文件层复核：
  - `U_COUNT=21`
  - `MANIFEST_LINES=7`
  - `QA_EXISTS=yes`
  - `rg` 检查未发现 QA 中残留旧口径 `24`、`8 行`、`子主题数 8`、`题目总数 24`。
  - frontmatter 字段覆盖：`unit/topic/subtopic/knowledge_point/core_concept/exam_pattern/question_type/common_mistake/difficulty/explanation_context = 21/21`。
  - 正文标题覆盖：`## Options/## Answer/## Explanation = 21/21`。

介入动作：

- Codex 新增 Unit 4 `qa-manifest.csv`，7 行，对应 U4.1.1 至 U4.3.2，每行 `items_count=3`、`question_count=3`、`difficulty_mix=F:1|S:1|C:1`。
- Codex 将 `QA-自检.md` 中的旧计数修为：
  - 子主题数 7
  - 题目总数 21
  - manifest 7 行
  - 状态 `operator_fallback_structure_fixed_pending_review`
- Codex 未修改任何 `U*.md` 题目正文。

临时结果：

- T-46 文件层结构缺口已修复；但 task truth 仍是 `in_progress/rejected`，review_course 未正式复核，不能宣称 approved 或 closeout。

明天修复建议：

- operator fallback 结构修复完成后，task evidence-account 应支持写入 `manifest_rows=7`、`manifest_evidence=qa-manifest.csv`、`operator_fallback_structure_fixed=true`，并自动把任务推进到 `pending_review_after_operator_fix`，避免文件层和 task truth 脱节。

### 70. runtime verify 显示 ready 但 live tmux 仍停在 Kimi 429 与未消费消息

触发时间：2026-06-23 04:14 CST

触发原因：

- 04:14 巡检中，`runtime verify --live-smoke` 对 manager/review_course/worker_course 均返回 `proved_ready`、`smoke_ok=true`、`pane_clean=true`、`inbox_state=consumed`，但实际 inbox 与 tmux 现场显示最新高优消息仍未被消费，三条窄范围恢复指令均因 Kimi 429 usage limit 被拒绝。
- 该矛盾会让 supervisor/manager 误判生产链已恢复，从而继续把 T-44/T-45/T-46 当作可自然推进，实际 review/worker/manager 并没有执行最新指令。

现场证据：

- `./scripts/eduflowteam runtime verify manager --json --live-smoke` 返回 `verdict=proved_ready`、`pane_clean=true`、`inbox_state=consumed`。
- `./scripts/eduflowteam runtime verify review_course --json --live-smoke` 返回 `verdict=proved_ready`、`pane_clean=true`、`inbox_state=consumed`。
- `./scripts/eduflowteam runtime verify worker_course --json --live-smoke` 返回 `verdict=proved_ready`、`pane_clean=true`、`inbox_state=consumed`。
- `tmux capture-pane -t EduFlowTeam:manager -p -S -120` 仍显示处理 `msg_1782157733253_096a972009` 时 `API Error: Request rejected (429)`。
- `tmux capture-pane -t EduFlowTeam:review_course -p -S -120` 仍显示处理 `msg_1782157190232_311bc79dae` 时 `API Error: Request rejected (429)`。
- `tmux capture-pane -t EduFlowTeam:worker_course -p -S -120` 仍显示处理 `msg_1782155879857_9ba82aea1b` 时 `API Error: Request rejected (429)`。
- `eduflowteam inbox manager` 仍有 26 unread；`review_course` 1 unread；`worker_course` 2 unread；review queue empty。

介入动作：

- 暂不继续叠加自然语言指令，避免在同一 429 runtime 上堆积旧上下文。
- 将本轮 runtime truth mismatch 标记为生产链风险，后续只基于 task truth + artifact truth + live tmux/inbox 交叉判断，不接受 `proved_ready` 单点结论。
- 下一步检查是否存在安全的单 agent runtime clean restart / provider 切换命令；若没有，将保持 T-44/T-45/T-46 为未完成/阻塞状态，不做虚假 closeout。

临时结果：

- 生产链仍未证实恢复；T-46 文件层已修但 task truth 仍 rejected/in_progress；T-44 仍 seed-only；T-45 仍 0 artifacts。

明天修复建议：

- 修复 `runtime verify` 的 pane_clean/inbox_state 判定：live pane 出现 429、quota、API retry、Interrupted 后，不得返回 `proved_ready`。
- 将未消费高优 inbox message id 纳入 runtime verify 的强校验，只有实际 `read --ack` 后才允许标记 consumed。
- 增加 provider fallback 的端到端 smoke：不仅检查 shell/env，还要检查 agent 能成功消费一条 harmless inbox 或输出状态包。

### 71. T-46 文件层已修复但 workflow 仍停在 rejected/in_progress，review queue 为空

触发时间：2026-06-23 04:18 CST

触发原因：

- T-46 AP Calculus AB Unit 4 的 operator fallback 结构修复已在文件层落盘并复核通过，但 `task get T-46` 仍显示 `status=in_progress`、`verdict=rejected`、`workflow_gate=revision_first`、`workflow_next_action=worker_repair_revision_scope_before_any_other_action`。
- `task review-queue --reviewer review_course` 为空，导致 review_course 即便恢复也没有结构化队列可消费。
- manager/review/worker runtime 仍存在未消费消息和旧 429 残留，不能等待自然同步。

现场证据：

- `AP Calculus AB/02-题库/items/Unit 4` 文件层：21 个 U*.md、`QA-自检.md`、`qa-manifest.csv`、manifest 7 data rows。
- `task get T-46`：`status=in_progress`、`verdict=rejected`、`review_reason=changes_requested`，latest summary 仍是旧缺口“manifest missing / QA 8/24/8”。
- `task evidence-account --task-id T-46 --json`：仍缺 `manifest_evidence` / `manifest_rows`，且 blocking reasons 包含 `latest_review_verdict_blocks_closeout:rejected`。
- `task review-queue --reviewer review_course`：no tasks awaiting review。

介入动作：

- 准备做最小 workflow 结构扶正：将 T-46 在 task/workflow 层重新送入 review queue，明确其状态是 `operator fallback structure fixed, pending review`，而不是 approved/closeout。
- 边界：不写正式 PASS，不做 manager closeout，不改题目正文，不触碰 T-44/T-45 内容。

临时结果：

- 待执行 `submit-review` 或等效 task truth sync，并随后复核 review queue 是否出现 T-46。

明天修复建议：

- 增加 operator fallback 后的标准状态：`pending_review_after_operator_fix`，允许记录 manifest rows 和 QA 修复证据，同时禁止自动 approved。

### 72. T-46 已重新挂回 review queue，避免文件层修复后无人复核

触发时间：2026-06-23 04:19 CST

触发原因：

- #71 记录后执行最小 workflow 结构扶正，目标是让 T-46 从旧 `rejected/in_progress` 状态回到可复核队列，而不是由 Codex 直接宣称完成。

现场证据：

- 执行 `./scripts/eduflowteam task submit-review T-46 --actor worker_course`。
- 命令返回：`submitted T-46 for review status=submitted_for_review verdict=pending`。
- `./scripts/eduflowteam task review-queue --reviewer review_course` 显示 T-46 正在 awaiting review。
- `task get T-46` 显示 `status=submitted_for_review`、`verdict=pending`、`reviewer=review_course`，但 workflow gate 仍保留 `revision_first/revision_priority_active_minor`，说明还需要 reviewer 或 manager 后续清 gate。

介入动作：

- Codex 仅执行结构化 submit-review，同步 review queue。
- 未做 review approved，未 closeout，未改动 AP Calculus AB 题目正文。

临时结果：

- T-46 当前状态应表述为：文件层 operator fallback 结构修复完成，已重新送审，等待 review_course 正式复核；不能称为完成。

明天修复建议：

- `submit-review` 后应支持附带 operator fallback evidence，例如 manifest rows、QA fixed flag、schema/title count，避免 reviewer 需要重新从零找证据。
- workflow gate 在重新送审时应从 `worker_repair_revision_scope_before_any_other_action` 切换为 `review_after_revision`，减少 status/gate 文案冲突。

### 73. T-46 重新送审后仍未被 review_course 消费，准备 operator fallback review

触发时间：2026-06-23 04:23 CST

触发原因：

- T-46 AP Calculus AB Unit 4 已在上一轮由 Codex 做最小结构扶正并重新 `submit-review`，但本轮巡检仍显示 review queue 中 T-46 等待 review_course，review_course live tmux 停在旧 Kimi 429 报错现场，没有消费新 review queue。
- health/supervisor-check 连续显示 `escalated_failure/runtime_unhealthy`，并指出 worker_course runtime guard escalated、manager 高优未读、worker_context_risk。
- 若继续等待 reviewer 自愈，T-46 会卡住 package 级闭环，同时 T-44/T-45 仍无正常 worker 产能推进。

现场证据：

- `task review-queue --reviewer review_course`：T-46 awaiting review。
- `task get T-46`：`status=submitted_for_review`、`verdict=pending`，但 latest authoritative review 仍是旧 rejected。
- `tmux capture-pane -t EduFlowTeam:review_course -p -S -80`：仍停在处理 `msg_1782157190232_311bc79dae` 的旧 Kimi `API Error: Request rejected (429)`。
- T-46 文件层复核：`U_COUNT=21`、`MANIFEST_ROWS=7`；frontmatter 字段 `unit/topic/subtopic/knowledge_point/core_concept/exam_pattern/question_type/common_mistake/difficulty/explanation_context = 21/21`；正文 `## Options/## Answer/## Explanation = 21/21`；`QA-自检.md` 已显示子主题数 7、题目总数 21、manifest 7 行。

介入动作：

- 准备执行最小 operator fallback review：仅对 T-46 Unit 4 package 级产物做 QA 判定，并将 task verdict 从 pending 更新为 approved。
- 边界：这不是 full subject closeout，不代表 AP Calculus AB 全科完成；不改任何题目正文；不 closeout T-44/T-45；不把 T-44 seed 当 full Unit。

临时结果：

- 待执行结构化 task review 并立即复核 task truth / review queue / evidence-account。

明天修复建议：

- review_course runtime 卡死时，应有自动 fallback reviewer 或 queue reassign 机制，且 operator fallback verdict 应在 task truth 中显式标记 fallback 来源、证据路径、抽检范围和非 subject closeout 边界。

### 74. T-46 operator fallback review 已通过，但 evidence-account 未保留 item/manifest 证据

触发时间：2026-06-23 04:24 CST

触发原因：

- #73 后执行结构化 fallback review，T-46 task truth 已变为 `delivered/approved`，但 `evidence-account` 中 `items_count`、`manifest_evidence`、`manifest_rows` 仍为空，导致 closeout evidence 仍弱。

现场证据：

- 执行 `./scripts/eduflowteam task review T-46 --actor review_course --approve ... --evidence item_count=21 --target "AP Calculus AB Unit 4 items"`。
- 命令返回：`reviewed T-46 outcome=approve status=delivered verdict=approved`。
- `task review-queue --reviewer review_course` 返回 no tasks awaiting review。
- `task get T-46` summary 明确写入：`Operator fallback review: AP Calculus AB Unit 4 artifact QA PASS after structure fix; 21 items, schema/title 21/21, QA 7/21/7, manifest rows 7... no subject closeout.`
- `task evidence-account --task-id T-46 --json` 仍显示 `items_count=null`、`manifest_evidence=null`、`manifest_rows=null`，missing evidence 包含 `items_count`、`manifest_evidence`、`manifest_rows`。

介入动作：

- 暂不继续改 task 状态，避免把 package-level fallback approval 误推成 subject closeout。
- 后续巡检对 T-46 使用文件层证据作为主要真相，task truth 作为 package approved 证据；仍不得宣称 AP Calculus AB 全学科 closeout。

临时结果：

- T-46 当前可表述为：Unit 4 package 级 operator fallback approved；文件层满足题库智能体基础字段；evidence-account 仍不完整，不能 subject closeout。

明天修复建议：

- 修复 `task review --evidence` 写入 evidence_packet/evidence-account 的链路，至少支持 `item_count`、`manifest_rows`、`manifest_evidence`、`qa_path`、`operator_fallback=true`。
- evidence-account 应能读取 Obsidian 目标路径中的 qa-manifest.csv 作为补强证据，而不是只依赖 review command packet。

### 75. 04:26 patrol 显示生产链仍未恢复，旧高优消息含过期事实仍未消费

触发时间：2026-06-23 04:26 CST

触发原因：

- T-46 已在 04:24 由 Codex operator fallback package review 标为 `delivered/approved`，但 manager inbox 仍有旧高优消息 `msg_1782157733253_096a972009` 未读，该消息仍写着 “T-46 仍 rejected / 缺 qa-manifest / QA 需改 7/21/7”，已经是过期事实。
- T-44/T-45 自上一轮以来没有新增真实产物，worker_course 未能继续推进完整 Unit 1。
- health/supervisor-check 仍为 `escalated_failure/runtime_unhealthy`，并继续指出 manager_high_priority_unread、worker_context_risk、agent_failover_escalation。

现场证据：

- `eduflowteam inbox manager`：仍有 26 unread，包含 `msg_1782157733253_096a972009`。
- `eduflowteam task review-queue --reviewer review_course`：no tasks awaiting review。
- `task get T-46`：`status=delivered`、`verdict=approved`，summary 标明 `Operator fallback review ... no subject closeout`。
- AP artifact counts：T-44 AP Statistics Unit 1 仍为 `U_COUNT=6`、QA yes、manifest yes、manifest rows 8；T-45 AP Psychology Unit 1 仍为 `U_COUNT=0`、QA no、manifest no。
- runtime verify 对 manager/review_course/worker_course 仍返回 `proved_ready`，但 live tmux 三个 pane 仍停在旧 Kimi 429 报错和未处理指令现场。

介入动作：

- 本轮不继续叠加自然语言提醒，避免旧 runtime pane 积压更多互相冲突的指令。
- 保持 T-46 为 package-level fallback approved，不允许 manager 基于旧 inbox 回滚到 rejected，也不允许升级为 subject closeout。
- 继续把 T-44 标为 seed-only/in_progress，把 T-45 标为 risk blocked。

临时结果：

- 今晚 5 个 AP 学科/单元中，T-42/T-43/T-46 已形成 package 级题库智能体基础；T-44 只有 seed；T-45 无产物。
- runtime/manager 消费链仍是当前最大系统风险。

明天修复建议：

- manager inbox 应支持“事实过期”标记：当 task truth 已更新到 newer verdict 时，旧高优消息中含过期 task state 的指令不得再作为执行依据。
- 增加 stale high-priority message reconciler：自动将已被 task truth superseded 的 nudge 标记为 superseded/read-state-desync，避免 manager 恢复后回滚。
- 对 T-44/T-45 应提供可恢复的 worker_course clean-restart + resume brief，而不是让旧 pane 带着 429 上下文继续等待。

### 76. 04:30 patrol 连续确认 T-44/T-45 无新增产物，runtime 与 inbox 阻塞仍未恢复

触发时间：2026-06-23 04:30 CST

触发原因：

- 04:30 新一轮 patrol 再次确认，T-44 AP Statistics Unit 1 与 T-45 AP Psychology Unit 1 没有新增真实生产产物，worker_course 未能推进完整 Unit 1。
- manager/review_course/worker_course 的 inbox 与 live pane 仍显示旧高优消息未被真实消费，存在 manager 恢复后按过期事实行动的风险。
- runtime verify 仍返回 `proved_ready`，但 live tmux 仍停在旧 Kimi 429 报错现场，监督面与真实执行面继续矛盾。

现场证据：

- `task get T-44`：`status=in_progress`、`verdict=pending`、`workflow_gate=review_handoff_gate`、`workflow_next_action=submit_review`，但 evidence-account 仍缺 `items_count/manifest/review verdict`。
- `task get T-45`：`status=in_progress`、`verdict=pending`，evidence-account 仍缺 `items_count/manifest/review verdict`。
- AP artifact counts：T-44 仍为 `U_COUNT=6`、QA yes、manifest yes、manifest rows 8；T-45 仍为 `U_COUNT=0`、QA no、manifest no。
- `eduflowteam inbox manager`：仍有 26 unread，包含过期高优消息 `msg_1782157733253_096a972009`。
- `eduflowteam inbox review_course`：仍有 T-44 seed-only 边界消息未读。
- `eduflowteam inbox worker_course`：仍有高优消息未读/未同步。
- `runtime verify` 对 manager/review_course/worker_course 返回 `proved_ready`，但 `tmux capture-pane` 仍显示三者停在旧 Kimi 429 报错与未完成指令现场。

介入动作：

- 本轮不新增自然语言催办，不直接大规模改写 T-44/T-45 内容。
- 保持 T-44 为 seed-only/in_progress，T-45 为 risk blocked，T-46 为 Unit 4 package fallback approved 但非 subject closeout。
- 下一轮继续观察是否有 runtime 真实恢复信号：新 pane 输出、inbox ack/read 状态变化、task truth 更新、artifact 变化，至少两类证据一致才改状态。

临时结果：

- 今晚当前可稳态确认的 package 级产物仍是 T-42、T-43、T-46；T-44 只有 seed，T-45 未产出。
- 生产链未恢复，worker_course 仍不是可信生产来源。

明天修复建议：

- 为 worker_course 增加 clean restart + current truth resume brief 的一键恢复命令，并清理旧 Kimi 429 pane 输入残留。
- 增加 manager stale-inbox reconciler，自动把过期高优消息标记为 superseded，避免恢复后按旧事实回滚。
- 对 T-44/T-45 建立“最小 seed / full unit / package approved”三档状态，不允许 seed-only 被 workflow next_action 误读为可 submit-review。

### 84. 05:04 patrol smoke 状态抖动回 proved_ready，但生产链仍无恢复

触发时间：2026-06-23 05:04 CST

触发原因：

- 上一轮 review_course/worker_course 显示 `smoke_failed`，本轮 `health` 又回到 `proved_ready`，但 live tmux、inbox、task、artifact 均没有任何新变化。
- supervisor 连续异常仍为 19，primary reason 仍是 `runtime_unhealthy`。
- 这说明 smoke/readiness 状态存在抖动，不能作为恢复判据。

现场证据：

- `task supervisor-check --json`：`health_status=escalated_failure`、`primary_reason=runtime_unhealthy`、`consecutive_issue_count=19`。
- `health`：manager/review_course/worker_course 显示 `proved_ready`，但 worker_course runtime guard 仍 `needs_manager_action=true`、`escalation_needed=true`、`fallback_chain_exhausted`。
- `inbox manager`：仍 26 unread；`inbox review_course`：仍 1 unread；`inbox worker_course`：仍 2 unread。
- `task review-queue --reviewer review_course`：仍无待审任务。
- `tmux capture-pane`：manager/review_course/worker_course 仍停在旧 Kimi 429/interrupted prompt，没有执行最新高优消息。
- Workflow truth：T-44/T-45 仍 `review_handoff_gate / waiting_review_handoff` 且 `evidence_keys=-`。
- Artifact truth：T-42 `U=15 QA=yes manifest=yes rows=21`；T-43 `U=45 QA=yes manifest=yes rows=15`；T-46 `U=21 QA=yes manifest=yes rows=7`；T-44 `U=6 QA=yes manifest=yes rows=8`；T-45 `U=0 QA=no manifest=no rows=0`。

介入动作：

- 本轮不发送新催办，不做 AP 内容 fallback，不执行 runtime destructive 操作。
- 继续以 live tmux + inbox 消费 + task/artifact 变化作为恢复判据。
- 保持 T-44 seed-only / T-45 risk blocked / T-42 T-43 T-46 package-level only。

临时结果：

- 生产链仍无新产物、无新 review、无新 verdict、无 manager closeout。
- smoke 状态抖动本身成为系统修复重点：`proved_ready` 不等于恢复生产。

明天修复建议：

- readiness 判定必须引入最新 pane 内容 hash、最新 inbox ack、最新 task/artifact mutation 三类信号。
- 对连续异常 19 这类状态，自动进入 runtime repair required，而不是继续在 proved_ready/smoke_failed 间摆动。
- 为 AP overnight monitor 增加“readiness oscillation”告警类型，专门记录 smoke 抖动但业务证据不变的场景。

### 83. 05:01 patrol review_course/worker_course 从假 ready 恶化为 smoke_failed

触发时间：2026-06-23 05:01 CST

触发原因：

- 本轮 `health` 不再只是显示核心角色 `proved_ready`，review_course 和 worker_course 已转为 `smoke_failed`。
- supervisor 连续异常升到 19，primary reason 仍是 `runtime_unhealthy`。
- inbox、review queue、task workflow、artifact 四个面仍无恢复，说明 AP 生产链继续停摆。

现场证据：

- `task supervisor-check --json`：`health_status=escalated_failure`、`primary_reason=runtime_unhealthy`、`consecutive_issue_count=19`。
- `health`：review_course `smoke_failed`，worker_course `smoke_failed`；worker_course runtime guard 仍 `needs_manager_action=true`、`escalation_needed=true`、`fallback_chain_exhausted`。
- `inbox manager`：仍 26 unread；`inbox review_course`：仍 1 unread；`inbox worker_course`：仍 2 unread。
- `task review-queue --reviewer review_course`：仍无待审任务。
- `tmux capture-pane`：manager/review_course/worker_course 仍停在旧 Kimi 429 与 interrupted prompt，没有执行最新 read/ack。
- Workflow truth：T-44/T-45 仍 `review_handoff_gate / waiting_review_handoff` 且 `evidence_keys=-`。
- Artifact truth：T-42 `U=15 QA=yes manifest=yes rows=21`；T-43 `U=45 QA=yes manifest=yes rows=15`；T-46 `U=21 QA=yes manifest=yes rows=7`；T-44 `U=6 QA=yes manifest=yes rows=8`；T-45 `U=0 QA=no manifest=no rows=0`。

介入动作：

- 本轮不做 AP 内容 fallback，不做 destructive runtime 操作。
- 继续将生产链状态判定为 runtime blocked，而不是等待中的正常生产。
- 保持 T-44 seed-only 不 submit-review，T-45 risk blocked。

临时结果：

- 生产侧没有新文件、新 review、新 verdict 或 manager closeout。
- runtime 证据从“可疑 ready”升级为明确 `smoke_failed`，明天修复优先级应上调。

明天修复建议：

- 优先提供 review_course/worker_course clean restart + smoke-test + inbox reconciliation 的一键命令。
- smoke_failed 时 supervisor 不应继续建议普通 manager action，应直接进入 runtime repair required。
- 将 latest truth packet 持久化为恢复脚本输入，避免 pane 恢复后按旧 02:52/03:48 信息回滚。

### 82. 04:58 patrol 无新增证据，workflow gate 与文件层继续脱节

触发时间：2026-06-23 04:58 CST

触发原因：

- 新一轮 patrol 仍未发现 manager/review_course/worker_course 真实消费最新高优消息。
- T-44/T-45 的 workflow gate 显示 `review_handoff_gate / waiting_review_handoff / next_action=submit_review`，但文件层和 evidence layer 均不支持 submit-review 或 closeout。
- live tmux 仍停在旧 Kimi 429，中断现场没有前进，说明生产链仍未恢复。

现场证据：

- `health`：manager/review_course/worker_course 仍显示 `proved_ready`，但 worker_course runtime guard 仍 `needs_manager_action=true`、`escalation_needed=true`、`fallback_chain_exhausted`。
- `inbox manager`：仍 26 unread；`inbox review_course`：仍 1 unread；`inbox worker_course`：仍 2 unread。
- `task review-queue --reviewer review_course`：仍 `no tasks awaiting review`。
- `tmux capture-pane`：manager/review_course/worker_course 仍停在旧 `API Error: Request rejected (429)` 后的 interrupted prompt。
- Workflow truth：T-42/T-46 仍 `revision_first / revision_priority_active_minor`；T-43 `file_evidence_gate / review_passed`；T-44/T-45 仍 `review_handoff_gate / waiting_review_handoff` 且 `evidence_keys=-`。
- Artifact truth：T-42 `U=15 QA=yes manifest=yes rows=21`；T-43 `U=45 QA=yes manifest=yes rows=15`；T-46 `U=21 QA=yes manifest=yes rows=7`；T-44 `U=6 QA=yes manifest=yes rows=8`；T-45 `U=0 QA=no manifest=no rows=0`。

介入动作：

- 本轮继续不发送新催办，不做 AP 内容 fallback，不执行 runtime destructive 操作。
- 保持 T-44 不允许空 submit-review，T-45 标记 risk blocked。
- 保持 T-42/T-43/T-46 仅 package-level 可用于题库智能体基础，不升级为 full subject closeout。

临时结果：

- 当前生产链仍卡住；本轮没有新增 production、review、QA 或 manager closeout 证据。

明天修复建议：

- workflow gate 应增加 file-evidence precondition：无 `U*.md + QA + manifest + evidence_packet` 时不得进入 `waiting_review_handoff/submit_review`。
- 对 T-44 seed-only 建立独立 gate，避免 seed 被误读为 full Unit 1 handoff。
- 恢复 worker_course 前必须执行 stale inbox reconciliation，废弃旧等待口径，再消费最新 T-44/T-45 truth packet。

### 81. 04:54 patrol pane ready 时间戳更新但现场仍未前进

触发时间：2026-06-23 04:54 CST

触发原因：

- 本轮 `health` 显示 manager pane ready 心跳刷新到 `0s ago`，review_course/worker_course 约 `3m ago`，但 live tmux 内容仍停在旧 Kimi 429 与中断提示。
- task、inbox、review queue、artifact 四个面均没有新变化，说明 pane ready/heartbeat 仍不足以证明 agent operational。
- T-44/T-45 仍未推进，4-5 学科目标的后两项仍缺正式生产闭环。

现场证据：

- `task supervisor-check --json`：`health_status=escalated_failure`、`primary_reason=runtime_unhealthy`、`consecutive_issue_count=17`。
- `health`：manager/review_course/worker_course 均显示 `proved_ready`，但 worker_course runtime guard 仍有 `needs_manager_action`、`escalation_needed`、`fallback_chain_exhausted`。
- `tmux capture-pane`：manager/review_course/worker_course 的可见输出仍是旧的 `API Error: Request rejected (429)`，未执行最新 inbox read/ack 指令。
- `inbox manager`：仍 26 unread；`inbox review_course`：仍 1 unread；`inbox worker_course`：仍 2 unread。
- `task review-queue --reviewer review_course`：仍无待审任务。
- Task truth：T-42/T-43/T-46 仍 `delivered/approved`，T-44/T-45 仍 `in_progress/pending`。
- Artifact truth：T-42 `U=15 QA=yes manifest=yes rows=21`；T-43 `U=45 QA=yes manifest=yes rows=15`；T-46 `U=21 QA=yes manifest=yes rows=7`；T-44 `U=6 QA=yes manifest=yes rows=8`；T-45 `U=0 QA=no manifest=no rows=0`。

介入动作：

- 本轮继续观察，不追加新消息，不做内容 fallback，不做 runtime destructive 操作。
- 继续将 live tmux + inbox 消费 + task/artifact 变化作为恢复判据，而不是接受 pane ready 时间戳。
- 保持 T-44 seed-only 和 T-45 blocked 标记，防止错误 closeout。

临时结果：

- 生产链仍未真实恢复；本轮没有新增文件、review handoff、verdict 或 manager closeout 证据。

明天修复建议：

- 将 `pane ready` 拆成两个指标：CLI shell 可输入、agent 已成功完成一轮最新指令。只有后者可解除 runtime blocker。
- runtime verify 应采样 pane 最新可见内容 hash；若多轮 hash 不变且含 429/interrupted，应判定为 stale pane。
- 恢复脚本应自动生成 current-truth resume packet，先废弃旧 02:52 verdict，再处理最新 T-44/T-45/T-46 状态。

### 80. 04:51 patrol 连续异常升至 17，AP 生产链仍未真实恢复

触发时间：2026-06-23 04:51 CST

触发原因：

- 新一轮 patrol 显示 supervisor 连续异常从 15/16 继续升到 17，primary reason 仍是 `runtime_unhealthy`。
- manager/review_course/worker_course 的 inbox 未读数量没有下降，review queue 仍为空，说明生产链没有恢复真实消费。
- T-44/T-45 仍无新增产物，今晚 4-5 学科目标仍停在 3 个 package-level + 1 个 seed-only + 1 个 blocked。

现场证据：

- `task supervisor-check --json`：`health_status=escalated_failure`、`primary_reason=runtime_unhealthy`、`consecutive_issue_count=17`，reasons 仍包含 `manager_high_priority_unread`、`stale_task_backlog`、`process_visibility_stale`、`worker_context_risk`、`manager_idle_too_long`。
- `health`：manager/review_course/worker_course 显示 `proved_ready`，但 worker_course runtime guard 仍 `needs_manager_action=true`、`escalation_needed=true`、`fallback_chain_exhausted`。
- `inbox manager`：仍 26 unread，含 `msg_1782157733253_096a972009`。
- `inbox review_course`：仍有 T-44 seed-only 边界消息 `msg_1782157190232_311bc79dae` 未读。
- `inbox worker_course`：仍有 2 unread，含 T-44/T-45 恢复生产消息 `msg_1782155879857_9ba82aea1b`。
- `task review-queue --reviewer review_course`：仍 `no tasks awaiting review`。
- `tmux capture-pane`：manager/review_course/worker_course 仍停在旧 Kimi `API Error: Request rejected (429)`，没有执行最新 inbox 消费命令。
- Artifact truth：T-42 `U=15 QA=yes manifest=yes rows=21`；T-43 `U=45 QA=yes manifest=yes rows=15`；T-46 `U=21 QA=yes manifest=yes rows=7`；T-44 `U=6 QA=yes manifest=yes rows=8`；T-45 `U=0 QA=no manifest=no rows=0`。

介入动作：

- 本轮继续不追加自然语言催办，避免把消息堆给不可消费 pane。
- 不做新的 AP 内容 fallback，不修改 AP 知识库。
- 保持验收边界：T-42/T-43/T-46 仅 package-level 可用；T-44 seed-only；T-45 risk blocked。

临时结果：

- 当前没有新鲜生产、review 或 closeout 证据；系统层仍处于 runtime/inbox 恢复失败状态。
- 明确禁止将 `proved_ready` 单独作为恢复证据；必须等 live tmux、inbox、task/artifact 至少两面出现一致变化。

明天修复建议：

- 对 manager/review_course/worker_course 增加 hard reset recovery：清掉旧 429 输入现场，重建 pane 后先消费最新高优 truth packet。
- 为 supervisor 增加“连续异常阈值升级”动作：超过 N 次时停止重复报 ready，转为 runtime repair required。
- 增加 AP manifest consistency gate，阻止 T-42/T-44 这类 manifest rows 与 `U*.md` 范围不一致的 package 被误读为可 closeout。

### 79. 04:46 patrol runtime 仍是假恢复，manifest 证据账户不一致

触发时间：2026-06-23 04:46 CST

触发原因：

- 新一轮 patrol 显示 `runtime verify --live-smoke` 对 manager/review_course/worker_course 均返回 `proved_ready`，但 live tmux 现场仍停在旧 Kimi 429 中断提示，关键高优 inbox 未见真实消费。
- T-44/T-45 仍无新增生产推进；T-44 只有 seed，T-45 仍无产物。
- 文件层发现 T-42/T-44 的 `qa-manifest.csv` 行数与当前 item 范围不一致，不能把 package review 扩大解释为 full closeout。

现场证据：

- `task supervisor-check --json`：`health_status=escalated_failure`、`primary_reason=runtime_unhealthy`、`consecutive_issue_count=15`，reasons 包含 `manager_high_priority_unread`、`stale_task_backlog`、`process_visibility_stale`。
- `runtime verify manager/review_course/worker_course --json --live-smoke`：三者均返回 `proved_ready`。
- `tmux capture-pane`：manager/review_course/worker_course 仍停在旧 `API Error: Request rejected (429)`，并显示针对最新高优消息的命令未被真实执行。
- `inbox manager`：仍有 26 unread，包含 `msg_1782157733253_096a972009`。
- `inbox review_course`：仍有 T-44 seed-only 边界消息 `msg_1782157190232_311bc79dae` 未读。
- `inbox worker_course`：仍有 2 unread，包含 T-44/T-45 生产恢复消息 `msg_1782155879857_9ba82aea1b`。
- Artifact truth：T-42 `U_COUNT=15`、QA yes、manifest yes、manifest rows 21；T-43 `U_COUNT=45`、manifest rows 15；T-46 `U_COUNT=21`、manifest rows 7；T-44 `U_COUNT=6`、manifest rows 8；T-45 `U_COUNT=0`、QA no、manifest no。
- Schema/title 抽查：T-42 15/15、T-43 45/45、T-46 21/21、T-44 seed 6/6 均具备 qbank-agent 字段和标准标题。

介入动作：

- 本轮不追加自然语言催办，不做新的内容 fallback，避免继续堆叠到当前不可消费的 pane。
- 将 T-42/T-43/T-46 继续限定为 package-level 可用基础，不升级为 subject/full closeout。
- 将 T-44 继续标记为 seed-only，不允许空 submit-review 或 full Unit 1 closeout。
- 将 T-45 继续标记为 risk blocked / no artifacts。

临时结果：

- 生产链仍未恢复，当前可用基础仍为 3 个 package-level 单元 + 1 个 seed-only 单元；第 5 个 AP Psychology 无文件产物。
- T-42/T-44 manifest 行数需要明天做 evidence-account reconciliation，避免后续题库智能体读取到过宽或陈旧清单。

明天修复建议：

- `runtime verify` 应把 live pane 旧 429 残留、高优 inbox 未消费、task/artifact 无变化纳入 hard fail，而不是仅凭 smoke 返回 `proved_ready`。
- 增加 manifest verifier：对 `U*.md` 数量、manifest rows、manifest topic/subtopic 范围、QA 自检数字做一致性检查，并写回 task evidence packet。
- 为 AP overnight 任务增加 clean restart + stale inbox reconciliation 流程，恢复后先废弃过期高优事实，再消费最新 truth packet。

### 77. 04:34 patrol 连续第 15 次 supervisor escalation，AP 生产链仍无新增推进

触发时间：2026-06-23 04:34 CST

触发原因：

- 新一轮 patrol 显示 supervisor-check 的 `consecutive_issue_count` 已到 15，primary reason 仍是 `runtime_unhealthy`，生产链没有恢复迹象。
- T-44/T-45 仍没有新增真实产物，manager/review_course/worker_course 仍未真实消费关键 inbox。
- `runtime verify` 继续返回 `proved_ready`，但 live tmux 三个核心 pane 仍停留在旧 Kimi 429 报错现场，说明 runtime readiness 判定仍不可作为单点真相。

现场证据：

- `supervisor-check --json`：`health_status=escalated_failure`、`primary_reason=runtime_unhealthy`、`consecutive_issue_count=15`，auto reasons 包含 `manager_high_priority_unread`、`stale_task_backlog`、`process_visibility_stale`、`worker_context_risk`。
- `inbox manager`：仍有 26 unread，包含过期高优消息 `msg_1782157733253_096a972009`。
- `inbox review_course`：仍有 T-44 seed-only 边界消息未读。
- `inbox worker_course`：仍有高优消息未读/状态不同步。
- Artifact truth：T-44 仍 `U_COUNT=6`、QA yes、manifest yes、manifest rows 8；T-45 仍 `U_COUNT=0`、QA no、manifest no。
- `tmux capture-pane`：manager/review_course/worker_course live tail 均仍停在旧 Kimi `API Error: Request rejected (429)`。

介入动作：

- 本轮不做新的内容 fallback，不新增自然语言催办，避免继续堆叠到不可消费 pane。
- 继续将 T-42/T-43/T-46 视为 package-level 可用基础，将 T-44 标为 seed-only，将 T-45 标为 risk blocked。
- 继续防止 manager 恢复后按旧高优消息回滚 T-46 或误 closeout T-44。

临时结果：

- 当前生产链仍未恢复；今晚目标已经有 3 个 package-level 可用基础，另 1 个 seed-only，1 个无产物阻塞。

明天修复建议：

- runtime verify 必须把 live pane 旧 429 和未消费高优消息作为 failed readiness 条件。
- 对 manager/review_course/worker_course 提供 clean pane restart + stale inbox reconciliation，而不是只报告 proved_ready。
- 为 AP overnight monitor 增加“连续 N 次无新增产物”升级策略，明确何时允许 operator fallback seed 或何时停止生产侧等待。

### 78. 04:38 patrol 仍无新鲜执行证据，T-44/T-45 继续停产

触发时间：2026-06-23 04:38 CST

触发原因：

- 新一轮 patrol 没有发现任何新鲜 task 状态、review queue、artifact 或 live pane 消费证据。
- manager/review_course/worker_course 的 inbox 未读状态和 live tmux 旧 429 现场持续存在，生产链仍无法自恢复。
- T-44/T-45 仍是今晚 4-5 科目标中的主要缺口：一个 seed-only，一个 0 产物。

现场证据：

- `inbox manager`：仍 26 unread，包含过期事实消息 `msg_1782157733253_096a972009`。
- `inbox review_course`：仍 1 unread，T-44 seed-only 边界消息未被真实消费。
- `inbox worker_course`：仍 2 unread。
- `task review-queue --reviewer review_course`：no tasks awaiting review。
- `task get T-44`：`status=in_progress`、`verdict=pending`、`workflow_next_action=submit_review`，但文件层仍只有 seed。
- `task get T-45`：`status=in_progress`、`verdict=pending`，文件层仍 0 产物。
- Artifact truth：T-44 `U_COUNT=6`、QA yes、manifest yes、manifest rows 8；T-45 `U_COUNT=0`、QA no、manifest no。
- `runtime verify` 对三核心 agent 仍返回 `proved_ready`，但 live tmux manager/review_course/worker_course 均仍停在旧 Kimi `API Error: Request rejected (429)`。

介入动作：

- 本轮不追加自然语言催办，不做新的 operator fallback 内容生产，避免越过监控边界和污染旧 pane。
- 保持状态判定：T-42/T-43/T-46 package-level 可用；T-44 seed-only；T-45 risk blocked。
- 下一轮继续寻找新鲜恢复证据，尤其是 worker_course 是否真的消费 inbox 或 AP Statistics/Psychology 是否出现新增文件。

临时结果：

- 生产链仍卡住；本轮没有可确认的新产出或 QA 进展。

明天修复建议：

- 建立 stale pane hard reset 策略：连续多轮 live pane 停在同一旧 429 且 task/artifact 无变化时，自动触发 clean restart，而不是继续报 `proved_ready`。
- 将 T-44/T-45 的恢复动作拆成可执行 resume packet：目标路径、最小 topic 范围、禁止 closeout 边界、完成后必须 submit-review。

### 85. 05:10 patrol 连续异常升至 21，生产链仍未形成新 review handoff

触发时间：2026-06-23 05:10 CST

触发原因：

- 新一轮 patrol 显示 supervisor-check 仍是 `health_status=escalated_failure`，`primary_reason=runtime_unhealthy`，且 `consecutive_issue_count` 已升至 21。
- manager 仍有 26 条 unread，review queue 为空，说明此前的关键纠偏消息没有形成新的 task/review 消费闭环。
- `health` 虽显示 manager/review_course/worker_course 为 `proved_ready`，但同时还有 2 个 red checks、worker_course runtime guard 仍需要 manager action，不能把 ready 当作业务恢复。

现场证据：

- `./scripts/eduflowteam task supervisor-check --json`：`health_status=escalated_failure`、`primary_reason=runtime_unhealthy`、`consecutive_issue_count=21`，auto reasons 包含 `runtime_unhealthy`、`agent_failover_escalation`、`manager_high_priority_unread`、`stale_task_backlog`、`process_visibility_stale`、`worker_context_risk`、`manager_idle_too_long`。
- `./scripts/eduflowteam health`：`❌ 2 red check(s)`；`runtime guard needs_manager_action: worker_course`、`runtime guard escalation_needed: worker_course`；router/watchdog 仍有 flapping/stall 迹象。
- `./scripts/eduflowteam inbox manager`：仍为 `26 unread`，包含 03:48 的 Codex 高优纠偏 `msg_1782157733253_096a972009`。
- `./scripts/eduflowteam task review-queue --reviewer review_course`：`no tasks awaiting review`。
- `.eduflow-team-state/facts/status.json`：manager/review_course/worker_course task 仍为 `initializing` 或旧状态，没有显示 T-44/T-45 新生产进展。

介入动作：

- 已记录本 gap note；本轮先不追加自然语言催办，避免继续堆叠到尚未证明可消费的 manager inbox。
- 继续执行 task truth、artifact truth、live tmux 的交叉核对，寻找是否存在真实业务恢复证据。
- 当前状态仍按保守口径处理：T-42/T-43/T-46 仅为 package-level 可用基础，T-44 为 seed-only，T-45 为风险阻塞。

临时结果：

- 截至本次 patrol，没有新的正式 review handoff，也没有证据表明 T-44/T-45 已恢复为完整生产。

明天修复建议：

- `proved_ready` 不应覆盖 `supervisor-check` 连续异常、inbox 未消费、review queue 为空、task/artifact 无变化等硬证据。
- runtime 恢复流程需要把 worker_course 的 guard escalation 转成明确的 clean restart / stale inbox reconciliation 操作，而不是反复发 Hermes 告警。
- gap note 写入顺序需要维护，避免后续巡检按尾部读取时漏掉较新的 #79-#84 记录。

### 86. 05:12 runtime verify 误报 inbox consumed，与实际 inbox/live pane 冲突

触发时间：2026-06-23 05:12 CST

触发原因：

- `runtime verify --live-smoke` 对 manager/review_course/worker_course 均返回 `proved_ready` 且 `inbox_state=consumed`，但实际 inbox 与 live tmux 证据相反。
- 该误报会让 supervisor 或 manager 误以为生产链已恢复，从而跳过 T-44/T-45 的真实生产恢复和 stale inbox reconciliation。

现场证据：

- `./scripts/eduflowteam runtime verify manager --json --live-smoke`：`verdict=proved_ready`、`inbox_state=consumed`。
- `./scripts/eduflowteam runtime verify review_course --json --live-smoke`：`verdict=proved_ready`、`inbox_state=consumed`。
- `./scripts/eduflowteam runtime verify worker_course --json --live-smoke`：`verdict=proved_ready`、`inbox_state=consumed`。
- `./scripts/eduflowteam inbox review_course`：仍有 1 unread，`msg_1782157190232_311bc79dae`，内容是 T-44 seed-only review 边界。
- `./scripts/eduflowteam inbox worker_course`：仍有 2 unread，包含 `msg_1782155879857_9ba82aea1b`，要求 T-44/T-45 不空 submit-review 并恢复生产。
- `tmux capture-pane`：manager/review_course/worker_course live pane 均停在旧 `API Error: Request rejected (429)` 与 `Interrupted · What should Claude do instead?` 场景，没有显示这些 inbox 被真实消费后的业务输出。

介入动作：

- 已记录本 gap note；本轮不把 `runtime verify` 的 `proved_ready/consumed` 作为恢复依据。
- 继续以 task truth + artifact truth + live tmux + inbox 列表为准，维持 T-44 seed-only、T-45 risk blocked 的判定。
- 暂不追加新催办，避免把更多指令写入 manager/worker_course 未可靠消费的上下文。

临时结果：

- runtime readiness 判定仍不可用作单点真相；当前业务链没有新鲜恢复证据。

明天修复建议：

- 修复 `runtime verify` 的 inbox_state 判定：必须读取同一 state_dir 的真实 unread/ack 状态，并把高优未读消息作为 hard fail。
- live-smoke 不应只验证模型可调用，还要验证 pane 已脱离旧错误上下文并能消费最新指定 message id。
- 对 AP overnight 这类生产监控增加 “verify says consumed but inbox lists unread” 的 supervisor anomaly 类型。

### 87. 05:16 patrol 无新增产物或 review handoff，T-44/T-45 缺口继续扩大

触发时间：2026-06-23 05:16 CST

触发原因：

- 新一轮 patrol 与 05:10/05:12 基线相比没有恢复：supervisor 仍为 `escalated_failure/runtime_unhealthy`，review queue 仍为空，manager/review_course/worker_course inbox 未读状态未消化。
- 文件层没有新增产物：T-44 仍只有 6 个 seed item，T-45 仍 0 个 item、无 QA、无 manifest。
- status/logs 没有显示 T-44/T-45 新生产或正式 review handoff，生产链仍停在旧上下文与告警循环里。

现场证据：

- `./scripts/eduflowteam task supervisor-check --json`：`health_status=escalated_failure`、`primary_reason=runtime_unhealthy`、`consecutive_issue_count=21`，auto reasons 仍包含 `manager_high_priority_unread`、`stale_task_backlog`、`process_visibility_stale`、`worker_context_risk`、`manager_idle_too_long`。
- `./scripts/eduflowteam health`：仍有 `❌ 2 red check(s)`，`runtime guard needs_manager_action: worker_course` 与 `runtime guard escalation_needed: worker_course` 未解除。
- `./scripts/eduflowteam inbox manager`：仍 `26 unread`；`review_course` 仍 `1 unread`；`worker_course` 仍 `2 unread`。
- `./scripts/eduflowteam task review-queue --reviewer review_course`：`no tasks awaiting review`。
- Artifact truth：AP Statistics Unit 1 仍 `U=6 / QA=yes / manifest=yes / rows=8 / latest=2026-06-23 03:37:32`；AP Psychology Unit 1 仍 `U=0 / QA=no / manifest=no`。
- `task get/workflow-status`：T-44、T-45 均仍 `in_progress / verdict=pending / workflow_gate=review_handoff_gate / next_action=submit_review`，但没有可提交的完整 Unit 产物。
- `.eduflow-team-state/facts/status.json`：manager/review_course/worker_course 仍显示 `initializing` 或旧状态；`.eduflow-team-state/facts/logs.jsonl` 最新主线仍是 Hermes 告警/旧交付回声，没有 T-44/T-45 新业务完成证据。

介入动作：

- 已记录本 gap note；本轮不追加新的自然语言催办，不做新的内容 fallback，避免继续向未可靠消费的 inbox/pane 堆叠指令。
- 继续维持保守验收状态：T-42/T-43/T-46 为 package-level usable；T-44 为 seed-only；T-45 为 risk blocked。
- 下一轮优先检查是否出现真正恢复信号：inbox unread 减少、live tmux 跳出旧 429、review queue 出现有效任务、T-44/T-45 文件时间戳更新。

临时结果：

- 本轮没有可确认的新产出、QA 或 review 进展；今晚 4-5 学科目标仍停在 3 个 package-level + 1 个 seed-only + 1 个 blocked。

明天修复建议：

- 为 T-44/T-45 增加明确的 resume packet 和 hard gate：未达到完整 Unit 产物前禁止 submit-review，T-45 0 产物必须显示为 risk blocked 而不是 in_progress。
- supervisor 连续异常计数不应在无业务恢复时停留不升级；连续多轮 21 且产物无变化时应触发 clean runtime recovery 或明确停机告警。
- 将 AP artifact snapshot 写入 task evidence-account，避免 task truth 只显示 `submit_review` 而缺少 items_count/manifest_rows 导致 manager 误判。

### 88. 05:18 patrol 四类证据一致指向生产链实质未恢复

触发时间：2026-06-23 05:18 CST

触发原因：

- 本轮不只是状态文件异常；supervisor、health、inbox/review queue、artifact 文件层、live tmux、evidence-account 六类证据一致显示 AP 生产链仍未恢复。
- `health` 继续显示三核心 agent `proved_ready`，但 live tmux 仍停在旧 Kimi 429/Interrupted 场景，说明 runtime readiness 仍是假恢复。
- T-44/T-45 仍是今晚目标缺口：T-44 只有 seed，T-45 没有任何题库产物。

现场证据：

- `./scripts/eduflowteam task supervisor-check --json`：`health_status=escalated_failure`、`primary_reason=runtime_unhealthy`、`consecutive_issue_count=21`；最新 checked_at 约 05:17，仍推荐 `trigger_supervisor_repair`。
- `./scripts/eduflowteam health`：三核心 agent 显示 `proved_ready`，但仍有 `❌ 2 red check(s)`，且 worker_course runtime guard 仍为 `needs_manager_action/escalation_needed`。
- `./scripts/eduflowteam inbox manager/review_course/worker_course`：manager 26 unread、review_course 1 unread、worker_course 2 unread；`review-queue --reviewer review_course` 仍 `no tasks awaiting review`。
- Artifact truth：AP Statistics Unit 1 仍 `U=6 / QA=yes / manifest=yes / rows=8 / latest=2026-06-23 03:37:32`；AP Psychology Unit 1 仍 `U=0 / QA=no / manifest=no`；T-42/T-43/T-46 文件时间戳也无新变化。
- `tmux capture-pane`：manager、review_course、worker_course 均停在旧 `API Error: Request rejected (429)` 与 `Interrupted · What should Claude do instead?`，没有最新 inbox 消费后的业务输出。
- `task evidence-account`：T-44/T-45 仍缺 `items_count/manifest_evidence/manifest_rows/latest_authoritative_review_verdict`；T-46 仍缺 `items_count/manifest_rows/subject_verifier_status` 且 `verdict_scope=package`。

介入动作：

- 已记录本 gap note；本轮不发送新催办、不做内容 fallback，避免向不可消费上下文继续堆积指令。
- 继续维持保守状态：T-42/T-43/T-46 是 package-level usable；T-44 seed-only；T-45 risk blocked。
- 下一轮如果仍无恢复，应考虑是否已满足连续阻塞审计条件，并在最终总结中把 runtime clean restart / stale inbox reconciliation 列为明日最高优先级。

临时结果：

- 没有新增生产、QA、review 或 closeout；当前 4-5 学科目标仍未达到 full target，只形成 3 个 package-level 样本、1 个 seed 样本、1 个阻塞样本。

明天修复建议：

- 建立“六类证据一致异常”升级策略：当 supervisor/health/inbox/artifact/tmux/evidence-account 都无恢复时，自动停止虚假 ready 轮询并执行 clean runtime recovery。
- 修复 evidence-account 写入：operator fallback review 必须把 item_count、manifest_rows、artifact path、scope 写入可机器验证字段。
- T-44/T-45 应提供明确 recovery task：先 clean worker_course pane，再消费最新高优消息，再产出或显式阻塞，不允许继续停在 `in_progress/pending` 空状态。

### 89. 05:20 patrol 连续异常升至 22，仍无 inbox 消费或产物推进

触发时间：2026-06-23 05:20 CST

触发原因：

- 新一轮 supervisor-check 的 `consecutive_issue_count` 从 21 升到 22，说明监督异常继续恶化。
- inbox/review queue、task/workflow、AP 文件层与 live tmux 均没有显示生产链恢复。
- manager/review_course/worker_course 虽被 health 标为 `proved_ready`，但三者 live pane 仍停在旧 Kimi 429，不具备消费最新 AP overnight 指令的证据。

现场证据：

- `./scripts/eduflowteam task supervisor-check --json`：`health_status=escalated_failure`、`primary_reason=runtime_unhealthy`、`consecutive_issue_count=22`，auto reasons 包含 `manager_high_priority_unread`、`stale_task_backlog`、`process_visibility_stale`、`worker_context_risk`、`manager_idle_too_long`。
- `./scripts/eduflowteam health`：仍 `❌ 2 red check(s)`，worker_course runtime guard 仍 `needs_manager_action/escalation_needed`。
- `./scripts/eduflowteam inbox manager/review_course/worker_course`：manager 仍 26 unread，review_course 仍 1 unread，worker_course 仍 2 unread；`review-queue --reviewer review_course` 仍为空。
- Artifact truth：T-44 AP Statistics Unit 1 仍只有 `U=6 / QA=yes / manifest=yes / rows=8 / latest=2026-06-23 03:37:32`；T-45 AP Psychology Unit 1 仍 `U=0 / QA=no / manifest=no`。
- `task get/workflow-status`：T-44/T-45 均仍 `in_progress / pending / review_handoff_gate / next_action=submit_review`，但没有可提交的完整产物。
- `tmux capture-pane`：manager/review_course/worker_course 均仍停在旧 `API Error: Request rejected (429)` 与 `Interrupted` 提示，没有新的业务执行输出。

介入动作：

- 已记录本 gap note；本轮不继续发送自然语言催办、不做内容 fallback，避免越过监控边界或污染不可消费的运行态。
- 继续保持验收口径：T-42/T-43/T-46 package-level usable；T-44 seed-only；T-45 risk blocked。
- 下一轮若仍维持同一阻塞，将按 blocked audit 视为连续目标轮次同一阻塞，准备判断是否已达到无法继续推进的阻塞条件。

临时结果：

- 本轮没有新增产物、QA、review handoff 或 manager closeout 可信证据；今晚目标仍未从 3 package + 1 seed + 1 blocked 进一步推进。

明天修复建议：

- 对 `consecutive_issue_count` 持续上升但无 runtime recovery 的情况，supervisor 应自动触发 clean pane restart 或明确升级为硬阻塞，而不是继续重复告警。
- 建立 stale inbox reconciliation：恢复后先清理/标记过期高优消息，再按最新 AP truth packet 消费，防止旧 02:52 verdict 回滚当前事实。
- T-44/T-45 应拆出最小恢复任务并绑定产物 gate；未生成完整 Unit 产物前不允许 task truth 继续提示 `submit_review`。

### 90. 05:22 patrol 连续异常升至 23，runtime 假 ready 与业务停摆继续并存

触发时间：2026-06-23 05:22 CST

触发原因：

- supervisor-check 的 `consecutive_issue_count` 从 22 升至 23，生产监督异常继续恶化。
- `health` 仍将 manager/review_course/worker_course 标为 `proved_ready`，但 live tmux 仍停在旧 Kimi 429/Interrupted 场景，未看到最新 inbox 消费或业务输出。
- AP 文件层没有新增：T-44 仍 seed-only，T-45 仍 0 产物，今晚 4-5 学科目标无法继续推进。

现场证据：

- `./scripts/eduflowteam task supervisor-check --json`：`health_status=escalated_failure`、`primary_reason=runtime_unhealthy`、`consecutive_issue_count=23`，recommended action 仍是 `trigger_supervisor_repair`。
- `./scripts/eduflowteam health`：三核心 agent 仍显示 `proved_ready`，但仍有 `❌ 2 red check(s)`，worker_course runtime guard 仍为 `needs_manager_action/escalation_needed`。
- `./scripts/eduflowteam inbox manager/review_course/worker_course`：manager 仍 26 unread，review_course 仍 1 unread，worker_course 仍 2 unread。
- `./scripts/eduflowteam task review-queue --reviewer review_course`：仍 `no tasks awaiting review`。
- Artifact truth：AP Statistics Unit 1 仍 `U=6 / QA=yes / manifest=yes / rows=8 / latest=2026-06-23 03:37:32`；AP Psychology Unit 1 仍 `U=0 / QA=no / manifest=no`。
- `tmux capture-pane`：manager/review_course/worker_course 均停在旧 Kimi `API Error: Request rejected (429)` 与 `Interrupted · What should Claude do instead?`，没有新的执行回声。

介入动作：

- 已记录本 gap note；本轮继续不追加新催办、不做内容 fallback、不改 AP 知识库。
- 维持保守验收口径：T-42/T-43/T-46 为 package-level usable；T-44 seed-only；T-45 risk blocked。
- 下一轮若仍无恢复，将继续按阻塞审计记录，并准备最终总结中的系统级修复清单。

临时结果：

- 没有新增生产、QA、review handoff 或 closeout 证据；当前停留在 3 个 package-level 样本 + 1 个 seed-only 样本 + 1 个阻塞样本。

明天修复建议：

- runtime readiness 必须把 live pane 是否脱离旧 429、是否真实消费最新 message id、是否产生业务状态变化纳入 hard gate。
- supervisor 连续异常超过阈值时，应停止重复 `proved_ready` 展示，直接触发 clean restart / stale inbox reconciliation。
- T-44/T-45 需要单独 recovery playbook：清理 worker_course 旧上下文、消费最新高优消息、明确产物范围，随后重新提交 review。

### 91. 05:24 runtime repair 前置记录：连续阻塞已满足最低修复触发条件

触发时间：2026-06-23 05:24 CST

触发原因：

- 从 05:10 到 05:22 多轮巡检持续显示同一阻塞：supervisor escalated failure、核心 inbox 未消费、review queue 为空、AP 文件层无新增、核心 tmux 卡旧 Kimi 429。
- supervisor 连续异常已升至 23，生态自修复没有形成任何可见业务恢复。
- 继续只观察已无法让 T-44/T-45 恢复生产；根据 monitor skill 的 Intervention Ladder，已进入可考虑 runtime repair 的阶段。

现场证据：

- `supervisor-check --json`：`consecutive_issue_count=23`、`health_status=escalated_failure`、`primary_reason=runtime_unhealthy`。
- `health`：仍显示 `proved_ready`，但 worker_course runtime guard 仍 `needs_manager_action/escalation_needed`，并有 `❌ 2 red check(s)`。
- `inbox`：manager 26 unread、review_course 1 unread、worker_course 2 unread；`review-queue` 为空。
- `tmux capture-pane` / `eduflowteam peek`：manager/review_course/worker_course 均停在旧 Kimi 429 与 Interrupted 提示。
- `eduflowteam --help`：存在 `fire`、`hire`、`up`、`reidentify`、`runtime verify/switch`、`runtime-guard clear` 等 lifecycle/runtime 命令；单 agent fire/hire 是可能的最小 runtime repair 面。

介入动作：

- 已先记录本 gap note，准备仅做最小 runtime repair 探查/动作。
- 边界：不改 AP 知识库内容，不清空任务队列，不重置全队状态，不覆盖已有产物；如执行，只针对卡住的核心 agent，优先 review_course/worker_course，目标是脱离旧 429 并消费最新 inbox。
- 介入后必须立即用 health、runtime verify、inbox、review queue、tmux、artifact snapshot 交叉验证。

临时结果：

- 尚未执行 runtime repair；当前仅完成前置记录与命令面确认。

明天修复建议：

- 产品化一个 `runtime clean-restart <agent> --consume-latest-inbox` 命令，避免 operator 组合 fire/hire/reidentify/runtim-guard clear。
- supervisor 应在连续 N 次相同阻塞后自动生成 runtime repair packet，而不是只推荐 `trigger_supervisor_repair`。
- runtime repair 后必须自动废弃旧高优事实、保留最新 truth packet，防止重启后按旧 verdict 回滚。

### 92. 05:28 patrol 复核确认 runtime verify 假阳性，准备最小重启 worker_course

触发时间：2026-06-23 05:28 CST

触发原因：

- 新一轮 patrol 后，`runtime verify --live-smoke` 对 manager/review_course/worker_course 均返回 `proved_ready` 且 `inbox_state=consumed`，但实际 inbox 与 live tmux 证据完全相反。
- manager 仍有 26 unread，review_course 仍有 1 unread，worker_course 仍有 2 unread；review queue 为空。
- T-44/T-45 仍未恢复生产：AP Statistics 只有 6 个 operator fallback seed items，AP Psychology 仍 0 items。

现场证据：

- `./scripts/eduflowteam runtime verify manager/review_course/worker_course --json --live-smoke`：均返回 `verdict=proved_ready`、`smoke_ok=true`、`inbox_state=consumed`。
- `./scripts/eduflowteam inbox manager`：仍显示 `26 unread`，其中 `msg_1782157733253_096a972009` 高优纠偏未读。
- `./scripts/eduflowteam inbox review_course`：仍显示 `msg_1782157190232_311bc79dae` 未读。
- `./scripts/eduflowteam inbox worker_course`：仍显示 `msg_1782153006545_9105651980`、`msg_1782155879857_9ba82aea1b` 未读。
- `tmux capture-pane -t EduFlowTeam:manager/review_course/worker_course`：三个 pane 均停在旧 Kimi `API Error: Request rejected (429)` 与 `Interrupted · What should Claude do instead?`，没有消费最新消息。
- Artifact snapshot：T-44 `U=6 / QA=yes / manifest=yes / rows=8`，T-45 `U=0 / QA=no / manifest=no`。

介入动作：

- 已按 monitor skill 先记录 gap note。
- 准备执行最小 runtime repair：优先单独重启 `worker_course`，目标是脱离旧 429 上下文，恢复 T-44/T-45 生产能力。
- 边界：不清空任务队列、不重置全队、不改 AP 知识库内容、不把 T-44 seed 当 full Unit 1、不 closeout T-45。

临时结果：

- 尚未执行重启；本条为介入前记录。

明天修复建议：

- `runtime verify` 不能只看 smoke；必须同时校验 live pane 是否仍卡旧错误、目标 message id 是否从 inbox 消失或有 ACK 日志、task/artifact 是否有新鲜变化。
- supervisor 连续异常超过阈值时应自动屏蔽 false ready，并给出明确的 per-agent clean restart 指令。

### 93. 05:28 operator 命令探查误触 `fire --help`

触发时间：2026-06-23 05:28 CST

触发原因：

- Codex 在确认 lifecycle 命令帮助面时执行 `./scripts/eduflowteam fire --help`，该 CLI 未按 help 处理，而是把 `--help` 当作 agent 名执行。
- 项目状态中此前已有一个 `--help` 误触 agent 记录；本次命令返回 `✅ fired: --help`，随后 `hire --help` 返回 `unknown agent: --help`。

现场证据：

- 命令输出：`✅ fired: --help`。
- 同组命令随后输出：`❌ unknown agent: --help (not in team.json)`。
- `.eduflow-team-state/facts/status.json` 里此前已有 `"--help": {"status": "已停止", "task": "误触 help 状态记录，忽略"}`，本次未影响 manager/review_course/worker_course 等真实 agent。

介入动作：

- 立即记录 gap note，后续不再使用 `fire --help` / `hire --help` 形式探查。
- 继续只针对真实 agent `worker_course` 做最小 runtime repair。

临时结果：

- 未发现真实生产 agent 被停止；但 CLI help 误触本身会污染状态面，需在明天清理或由工具层修复。

明天修复建议：

- lifecycle 命令必须优先处理 `--help`，不能把 flag 当 agent 名。
- 清理历史 `--help` 伪 agent 状态，避免 supervisor/status 继续把误触记录当作真实团队成员。

### 94. 05:30 worker_course 最小重启后恢复读框架，但 review_course pane 缺失

触发时间：2026-06-23 05:30 CST

触发原因：

- 已执行 `fire worker_course && hire worker_course`，worker_course 脱离旧 Kimi 429 pane，开始执行 inbox/框架读取。
- 修复后 `health` 暴露新阻塞：`review_course: no tmux window`，导致后续 T-44/T-45 的正式 QA/review 无法落地。
- supervisor-check 仍维持 `health_status=escalated_failure`，说明系统级监督状态尚未恢复。

现场证据：

- 命令输出：`✅ fired: worker_course`、`✅ hired: worker_course (claude-code) → EduFlowTeam:worker_course`。
- `tmux capture-pane -t EduFlowTeam:worker_course`：worker_course 不再停在旧 429，已加载 `/inbox` skill，并读取 `AP Statistics_题库优化版_知识点框架.md`。
- `./scripts/eduflowteam health`：worker_course pane ready 且心跳 2s；但 `review_course: no tmux window`，总计 `❌ 4 red check(s)`。
- `tmux list-windows -t EduFlowTeam`：窗口列表没有 `review_course`。
- `./scripts/eduflowteam inbox review_course`：仍有 `msg_1782157190232_311bc79dae` 未读；`review-queue` 仍为空。

介入动作：

- 已完成 worker_course 单 agent 最小 runtime repair。
- 准备继续执行最小修复：仅 `hire review_course`，目标是恢复 QA/review 消费能力。
- 继续维持边界：不 closeout T-44，不把 seed PASS 当 full Unit 1 verdict，不改 AP 内容，不动 manager/全队状态。

临时结果：

- worker_course 有恢复迹象，正在查看 AP Statistics 框架；尚未看到新 U*.md 或 submit-review。
- review_course 缺失会阻断后续 QA，因此需要立即补回。

明天修复建议：

- `health` 和 supervisor 应区分“生产 worker 已恢复”和“review role 缺席”，避免一个角色恢复后掩盖另一个关键 gate 缺失。
- runtime repair 后应自动跑 `tmux list-windows` 和关键 role 存活检查，把 missing review role 作为 hard blocker。

### 95. 05:32 review_course 补回后 inbox 清零，但产物层尚未恢复

触发时间：2026-06-23 05:32 CST

触发原因：

- Codex 介入执行 `hire review_course`，修复 #94 中发现的 review pane missing。
- 修复后 worker_course/review_course 均已脱离旧 429，并消费了 unread inbox；但 AP Statistics / AP Psychology 文件层仍未新增，生产恢复尚未被产物证明。

现场证据：

- 命令输出：`✅ hired: review_course (claude-code) → EduFlowTeam:review_course`。
- `./scripts/eduflowteam health`：manager、review_course、worker_builder、worker_course 均为 `proved_ready`；红项从 4 个降回 2 个外围项。
- `./scripts/eduflowteam inbox review_course`：`no unread messages`。
- `./scripts/eduflowteam inbox worker_course`：`no unread messages`。
- `./scripts/eduflowteam task review-queue --reviewer review_course`：仍 `no tasks awaiting review`。
- `tmux capture-pane -t EduFlowTeam:worker_course`：worker_course 正在读取 AP Statistics Unit 1 seed 文件/框架，但尚未输出完成状态。
- Artifact snapshot：AP Statistics 仍 6 个 `U*.md`，文件时间仍为 03:37；AP Psychology 仍 0 个 `U*.md`。

介入动作：

- 已完成 `review_course` 最小 hire 恢复。
- 暂不发送新催办，给 worker_course 一个短窗口完成当前 AP Statistics 读取/扩展；继续以产物新增、submit-review、review verdict 作为恢复证据。

临时结果：

- runtime 主链从“旧 429 卡死”恢复为“agent 可读 inbox/可执行命令”。
- 业务状态仍未恢复到产物层：T-44 仍 seed-only，T-45 仍 0 产物。

明天修复建议：

- runtime repair 后的成功标准必须分两层：runtime 可执行只是第一层，产物/任务状态新鲜变化才是业务恢复。
- review_course 消费 seed-only 边界消息后，应自动写一个 seed-level verdict 或等待完整 submit-review 的明确状态，避免静默清 inbox。

### 96. 05:35 heartbeat 监控基线更新，避免下一轮沿用旧 05:12 状态

触发时间：2026-06-23 05:35 CST

触发原因：

- 当前线程已有 `ap-overnight-monitor-patrol` heartbeat 自动化，周期为 30 分钟，但 prompt 基线停留在 05:12，仅记录到 #86。
- 05:28-05:32 已发生新的关键介入：worker_course fire/hire、review_course hire、gap note #92-#95，旧 prompt 会导致下一轮巡检误把旧 runtime 卡死状态作为最新边界。

现场证据：

- `${CODEX_HOME}/automations/ap-overnight-monitor-patrol/automation.toml`：`rrule=FREQ=MINUTELY;INTERVAL=30`，prompt 旧基线为 `截至 2026-06-23 05:12 CST`。
- `automation_update` 返回：`Updated automation in the app`，`automationId=ap-overnight-monitor-patrol`。

介入动作：

- 已更新 heartbeat prompt 到 05:32 基线：记录 T-42/T-43/T-46 package-level usable、T-44 seed-only、T-45 blocked，以及 worker_course/review_course 已重启但业务产物未恢复。
- 明确下一轮不要把 runtime 恢复当业务恢复，必须继续查产物新增、submit-review 或 blocker。

临时结果：

- 自动巡检的状态基线已同步到最新现场；没有新增 AP 内容修改。

明天修复建议：

- 监控 heartbeat 应由 gap note 自动生成最新基线摘要，避免人工更新遗漏。
- 自动化 prompt 应只保留最近关键事实和固定巡检协议，避免过长旧历史稀释当前真相。

### 97. 05:37 T-44 Statistics 产物恢复，但 supervisor 仍报连续异常 25

触发时间：2026-06-23 05:37 CST

触发原因：

- worker_course 重启后实际执行 `/tmp/generate_ap_stats_u1.py`，AP Statistics Unit 1 从 6 个 seed 扩展到 45 个 items，并提交 review_course。
- 但 `supervisor-check` 仍显示 `health_status=escalated_failure`、`consecutive_issue_count=25`，runtime/status 面没有及时反映业务恢复。
- manager inbox 仍有大量旧 unread，且 supervisor 捕捉到 manager 对旧 worker_builder 委派做了二手状态回答，存在状态同步污染风险。

现场证据：

- `tmux capture-pane -t EduFlowTeam:worker_course`：worker_course 运行 `python3 /tmp/generate_ap_stats_u1.py`，随后执行 `eduflow send manager worker_course "T-44 AP Statistics Unit 1 已提交 review_course 复核。产物：45 items..."`。
- Artifact snapshot：`AP Statistics/02-题库/items/Unit 1` 下 `U*.md` 数量从 6 变为 45；AP Psychology 仍为 0。
- `./scripts/eduflowteam task review-queue --reviewer review_course`：出现 `T-44 ... awaiting review reviewer=review_course`。
- `./scripts/eduflowteam task supervisor-check --json`：`consecutive_issue_count=25`，reasons 包含 `runtime_unhealthy`、`agent_failover_escalation`、`manager_high_priority_unread`、`status_surface_truth_lag`、`worker_context_risk`、`manager_idle_too_long`。
- manager inbox 仍有 25 unread，其中包含旧 02:52 verdict 与当前 T-44 提交消息。

介入动作：

- 已记录本 gap note。
- 下一步立即对 T-44 做文件层 QA 抽查：数量、manifest rows、QA 文件、frontmatter 必备字段、`## Options/## Answer/## Explanation` 标题、是否只覆盖 Unit 1。
- 等待 review_course 正式 verdict；不得把 worker_course 自报完成当作 T-44 完成。

临时结果：

- T-44 从 seed-only 进入“待 review / 文件层待 QA”状态。
- T-45 仍 0 产物，仍为风险阻塞。
- runtime 主链业务有恢复迹象，但 supervisor/status 仍未同步。

明天修复建议：

- supervisor 应在产物层和 review queue 出现新鲜进展后降低或重分类 runtime escalation，而不是继续单调累加 consecutive issue。
- manager inbox 的旧 verdict / 旧派单消息需要按 task scope 自动归档，避免恢复后被二次消费造成回滚。

### 98. 05:39 T-44 Statistics 全量提交后 manifest 行数与 item 文件数不一致

触发时间：2026-06-23 05:39 CST

触发原因：

- T-44 AP Statistics Unit 1 已从 seed-only 扩展为 45 个 `U*.md`，并提交 review_course。
- Codex 文件层抽查发现 `qa-manifest.csv` 数据行数为 55，与 45 个 item 文件不一致；这会影响题库智能体后续按 manifest 导入/索引。
- manager 已 ACK worker_course 的 “schema/manifest 一致” 自报，但文件层证据不支持该说法。

现场证据：

- `find ".../AP Statistics/02-题库/items/Unit 1" -name 'U*.md' | wc -l`：`45`。
- `tail -n +2 ".../AP Statistics/02-题库/items/Unit 1/qa-manifest.csv" | wc -l`：`55`。
- `./scripts/eduflowteam task get T-44`：状态为 `submitted_for_review`，workflow gate 为 `quality_gate / awaiting_review_verdict`。
- `./scripts/eduflowteam task review-queue --reviewer review_course`：`T-44 awaiting review`。
- logs：worker_course 自报 `45 items（15 subtopics × 3 difficulties）+ QA-自检.md + qa-manifest.csv`；manager 随后 ACK 并同步 “schema/manifest 一致”。

介入动作：

- 已记录 gap note。
- 下一步需要向 review_course/manager 同步唯一真相：T-44 不得 PASS，review 必须检查 manifest 与 45 item 文件一一对应；若 manifest 55 行属旧 seed 残留或重复行，需 worker_course 窄返修 manifest/QA，不改题目内容。
- Codex 暂不直接改 AP Statistics 内容，先让正式 review 链处理。

临时结果：

- T-44 状态从 seed-only 提升为 `submitted_for_review`，但 QA 风险为 `manifest_count_mismatch`。
- 不能 closeout，也不能标为已完成；当前应标为“待 review / 需重点查 manifest”。

明天修复建议：

- worker submit-review 前应强制运行 manifest-file parity gate：item file count、manifest rows、QA stated counts 三者必须一致。
- manager ACK worker 自报时应自动抽查 manifest rows，不能复述“manifest 一致”作为事实。

### 99. 05:40 Codex 纠偏消息误投到 codex inbox，review/manager 未收到

触发时间：2026-06-23 05:40 CST

触发原因：

- Codex 准备把 T-44 `U*.md=45 / manifest_rows=55` 的质量纠偏同步给 review_course 和 manager。
- 执行 `eduflowteam send codex review_course ...` 与 `send codex manager ...` 后，CLI 回显为 `inbox: codex ← review_course` / `inbox: codex ← manager`，说明参数顺序与预期相反，消息被投到 Codex inbox，而不是目标 agent。

现场证据：

- 命令输出：`📥 inbox: codex ← review_course [local_id=msg_1782164413381_422d8426ae]`。
- 命令输出：`📥 inbox: codex ← manager [local_id=msg_1782164413417_83defb8383]`。
- 该误投未修改 task truth、review queue 或 AP 文件，但会造成“以为已提醒，实际未提醒”的监控假象。

介入动作：

- 已记录本 gap note。
- 下一步立即查 `eduflowteam send` 正确参数顺序，并重发给 review_course/manager。
- 若 Codex inbox 出现误投消息，后续只作为误投证据，不作为生产链有效 ACK。

临时结果：

- T-44 manifest mismatch 纠偏尚未可靠送达 review_course/manager。

明天修复建议：

- `send` 命令应在回显中明确 `from -> to` 并支持 `--from/--to` 参数，避免 operator 误判位置参数。
- 监控工具应检测自发消息是否投回 codex inbox，并提示“可能参数顺序错误”。

### 100. 05:42 T-44 manifest mismatch 需修正为 schema 口径待判定

触发时间：2026-06-23 05:42 CST

触发原因：

- Codex 初步发现 `U*.md=45 / qa-manifest.csv 数据行=55` 后，按“manifest 行数与 item 文件数不一致”提醒 review_course/manager。
- 进一步拆分 manifest 后发现 55 行由 45 条 item rows + 10 条 SUMMARY rows 组成；`item_id` 唯一数为 45，未发现重复 item_id。
- 因此问题不应粗暴定性为旧 seed 残留或重复行，而应改为：manifest 是否允许混合 item rows 与 topic/unit summary rows，需要 review_course 按导入 schema 判定。

现场证据：

- `item_files=45`。
- `total_manifest_rows=55`。
- `item_rows=45`。
- `summary_rows=10`。
- `unique_item_ids=45`。
- `duplicate_item_ids` 输出为空。
- `./scripts/eduflowteam inbox review_course`：manager 已根据前一版口径发送 `manifest-file parity 冲突` 高优消息 `msg_1782164536409_15aa5c2567`。

介入动作：

- 已记录本 gap note，修正 Codex 前一条 QA 表述。
- 下一步同步给 review_course/manager：不要仅因总行数 55 判 FAIL；请按 schema 判定 summary rows 是否允许。若 qbank 导入要求 manifest 只含 item rows，则要求 worker_course 窄修为 45 item-only rows 或拆分 summary；若允许 summary rows，则确认 QA 文档需明确 total rows 与 item rows 的区别。

临时结果：

- T-44 仍为 `submitted_for_review / awaiting_review_verdict`。
- QA 风险从 `manifest_count_mismatch` 修正为 `manifest_schema_ambiguity`。

明天修复建议：

- manifest 标准需要明确：是否允许 SUMMARY 行；若允许，文件名/字段中应区分 `item_manifest_rows` 与 `summary_rows`，避免巡检误报。
- Codex patrol 脚本应同时统计 total rows、item rows、summary rows、unique item ids，而不是只比较总行数和文件数。

### 101. 05:45 T-44 review_course 已给 REVISION REQUIRED，但 task truth 未同步

触发时间：2026-06-23 05:45 CST

触发原因：

- review_course 在日志中已给出 T-44 AP Statistics Unit 1 正式复核 verdict：`REVISION REQUIRED`，原因是 manifest-file parity gate 未通过。
- 但结构化任务状态仍是 `submitted_for_review / verdict=pending`，review queue 仍显示 `T-44 awaiting review`。
- 若 manager 只读 worker_course “完成”自报或 review queue 表面状态，可能误判为仍在审，或跳过窄返修。

现场证据：

- `logs.jsonl` / tmux：review_course 输出 `T-44 AP Statistics Unit 1 复核 verdict：REVISION REQUIRED ❌（manifest-file parity gate 未通过）`。
- review verdict 明确文件层实测：45 个 `U*.md`；45 条 item_id 数据行；额外 10 行 SUMMARY；要求删除 SUMMARY 行或仅保留汇总在 `QA-自检.md`，不改题目内容。
- `./scripts/eduflowteam task get T-44`：仍为 `submitted_for_review`，`verdict=pending`。
- `./scripts/eduflowteam task workflow-status T-44`：仍为 `quality_gate / awaiting_review_verdict`。
- `./scripts/eduflowteam task review-queue --reviewer review_course`：仍显示 T-44 awaiting review。

介入动作：

- 已记录本 gap note。
- 下一步提醒 manager：消费 review_course 的 REVISION REQUIRED，按 workflow 将 T-44 转为窄返修；派 worker_course 只修 `qa-manifest.csv`/`QA-自检.md`，删除或拆分 SUMMARY rows，不改 45 个题目内容；修完后重新 submit-review。

临时结果：

- T-44 当前状态应标为“需返工 / manifest parity narrow repair”，不是完成，也不是可 closeout。
- T-45 仍为 0 items 风险阻塞。

明天修复建议：

- review_course 输出 verdict 时必须同步写入 task truth，否则 review queue 与日志会分叉。
- task review gate 应提供 `record-verdict` 或 `review-fail` 的单步命令，避免 verdict 停留在聊天日志里。

### 102. 05:50 T-44 review gate PASS 未落到 task truth

触发时间：2026-06-23 05:50 CST

触发原因：

- T-44 AP Statistics Unit 1 的窄返修已完成，review_course 已在日志/运行态给出正式 `PASS` verdict。
- 但结构化 task truth 仍停在 `submitted_for_review / verdict=pending`，review queue 仍显示 T-44 awaiting review。
- 如果 manager 不消费该 PASS 并落账，今晚第 4 个学科会停在“文件与 review 已通过、workflow 未完成”的半闭环状态，后续 T-45 recovery 也会被阻塞。

现场证据：

- `logs.jsonl`：review_course 输出 `T-44 AP Statistics Unit 1 返修复核 verdict：PASS ✅（review gate），按 manager 要求暂不 closeout`。
- `./scripts/eduflowteam task get T-44`：`status=submitted_for_review`，`verdict=pending`，`workflow_gate_status=awaiting_review_verdict`。
- `./scripts/eduflowteam task review-queue --reviewer review_course`：仍显示 `T-44 awaiting review`。
- 文件层复核：`AP Statistics/02-题库/items/Unit 1/` 下 `U*.md=45`，`QA-自检.md=yes`，`qa-manifest.csv rows=45 / item_rows=45 / summary_rows=0`。
- review_course inbox 与 worker_course inbox 均为空，说明当前不是 reviewer 未收到，而是 verdict 未写回 task/workflow。

介入动作：

- 已记录本 gap note。
- 下一步给 manager 发送窄提醒：消费 review_course 的 T-44 PASS，按 workflow 将 T-44 task truth 写为 approved/delivered 或至少记录 approved verdict/evidence packet；同步 review queue；不要做 subject closeout，边界仍是 Unit 1 package-level PASS。
- 同时要求 manager 在 T-44 落账后明确启动/恢复 T-45 Psychology，或标出 blocker。

临时结果：

- T-44 文件层与 review gate 可判为 PASS，但结构化完成尚未成立。
- T-45 仍为 `in_progress / pending` 且文件层 0 items、无 QA、无 manifest，继续列为风险阻塞。

明天修复建议：

- review_course 的 PASS/REVISION verdict 应强制调用 task verdict 写回命令，避免 review queue 残留。
- manager closeout prompt 应要求“先落 task truth，再发口头同步”，并区分 package-level PASS 与 subject closeout。

### 103. 06:02 T-45 已进 review queue 但 review_course 未消费

触发时间：2026-06-23 06:02 CST

触发原因：

- T-45 AP Psychology Unit 1 已由 worker_course 生成产物并结构化提交 review。
- task truth 已进入 `submitted_for_review / quality_gate / awaiting_review_verdict`，review queue 也显示 T-45 awaiting review。
- 但 review_course inbox 为空，tmux 现场仍停留在上一轮 T-44 处理后待命状态，没有开始 T-45 复核信号。
- 如果不提醒，T-45 可能停在“已提交但 reviewer 未被触发”的半自动断点，影响今晚第 5 个学科闭环。

现场证据：

- `./scripts/eduflowteam task get T-45`：`status=submitted_for_review`，`verdict=pending`，`workflow_gate_status=awaiting_review_verdict`。
- `./scripts/eduflowteam task review-queue --reviewer review_course`：显示 `T-45 awaiting review`。
- `./scripts/eduflowteam inbox review_course`：`no unread messages`。
- 文件层复核：`AP Psychology/02-题库/items/Unit 1/` 下 `U*.md=15`，`QA-自检.md=yes`，`qa-manifest.csv rows=15 / item_rows=15 / summary_rows=0`。
- `logs.jsonl`：manager 已同步 `T-45 AP Psychology Unit 1 已提交 review_course 复核`，但尚未出现 review_course 对 T-45 的 started/verdict。

介入动作：

- 已记录本 gap note。
- 下一步给 review_course 发送窄提醒：从 review queue 消费 T-45，复核 15 items、QA、manifest、schema、题目质量与 tone tokens；完成后把 PASS/REVISION verdict 写回 task truth。
- 同步给 manager：不要把 T-45 文件层提交当完成，必须等 review verdict + task truth。

临时结果：

- T-45 当前状态为“待 review”，不是完成。
- 文件层已具备 review 前置条件；问题在 queue/inbox 触发链。

明天修复建议：

- task submit-review 应确保 reviewer inbox 收到可消费消息；review queue 与 inbox 不能分叉。
- review_course idle 时应主动 poll `task review-queue`，不能只依赖 inbox 推送。

### 104. 06:10 五个 AP 单元已闭环但状态/健康面仍滞后报错

触发时间：2026-06-23 06:10 CST

触发原因：

- T-42/T-43/T-44/T-45/T-46 当前 task truth 均为 `delivered / approved`，review queue 为空，AP 产物文件层也存在 QA 与 manifest。
- 但 `status.json` 中 manager 仍停在 T-45 提交 review 前后的旧任务摘要，worker_course 仍显示 `T-45 AP Psychology Unit 1 已提交 review_course 复核`，没有反映 T-45 已 PASS 并落账。
- `supervisor-check` 仍报 `escalated_failure / runtime_unhealthy`，并带有 `status_surface_truth_lag`、`manager_high_priority_unread`、`worker_context_risk` 等历史/状态面异常。
- 若后续只看 status/health，可能误判业务链仍卡在 T-45 待审或 runtime 不可用；若只看 task truth，又会忽略监控面持续假红。

现场证据：

- `./scripts/eduflowteam task get T-42/T-43/T-44/T-45/T-46`：五个 task 均为 `delivered`，`verdict=approved`。
- `./scripts/eduflowteam task review-queue --reviewer review_course`：`no tasks awaiting review`。
- `status.json`：`review_course` 已显示 `T-45 AP Psychology Unit 1 PASS（Unit 1 package-level），verdict 已写回 task truth`；但 `manager` 仍显示 `T-45 ... task truth 仍是 submitted_for_review / verdict...`，`worker_course` 仍显示 `T-45 ... 已提交 review_course 复核`。
- 产物计数：CSA 15、Physics 45、Calc AB 21、Statistics 45、Psychology 15 个 `U*.md`，五者均有 `QA-自检.md` 与 `qa-manifest.csv`。
- `supervisor-check --json`：`health_status=escalated_failure`，`primary_reason=runtime_unhealthy`，`consecutive_issue_count=31`。

介入动作：

- 已记录本 gap note。
- 下一步给 manager 发送窄提醒：只做状态包同步，不改内容，不做 full subject closeout；把五个 AP 单元同步为 package-level delivered/approved，并明确 T-42/T-46 gate/evidence 残留是明天流程修复项。

临时结果：

- 业务闭环证据强于 status 面；当前不需要内容返修。
- 仍需下一轮 patrol 确认 status 是否刷新，以及 supervisor 是否继续假红。

明天修复建议：

- manager/review_course verdict 写回 task truth 后，应自动刷新 `facts/status.json` 的 agent task 摘要，避免旧状态误导监控。
- supervisor-check 应区分“业务阻塞型 runtime unhealthy”和“历史/外围状态面假红”，避免在主链已闭环时持续 escalated_failure。

### 105. 06:16 T-42 manifest 仍混入 SUMMARY 行，和 T-44 parity 规则冲突

触发时间：2026-06-23 06:16 CST

触发原因：

- 最新巡检确认 T-42 AP Computer Science A Unit 1 已有 15 个 actual MCQ item，且 item frontmatter 与 `## Options / ## Answer / ## Explanation` 标题齐全。
- 但 `qa-manifest.csv` 当前为 21 个数据行，其中 15 个 item 行 + 5 个 topic SUMMARY + 1 个 unit SUMMARY。
- 同夜 T-44 AP Statistics Unit 1 已因 manifest 中 SUMMARY 行被 review_course 判为 manifest-file parity gate 未通过，并要求删除 SUMMARY 行；T-42 若保留 SUMMARY，后续题库智能体解析仍可能按 data row 消费到空 item_id 行。

现场证据：

- `AP Computer Science A/02-题库/items/Unit 1/`：`U*.md=15`，`QA-自检.md=yes`，`qa-manifest.csv=yes`。
- 产物计数命令结果：`rows=21 / item_rows=15 / summary_rows=6`。
- `head/tail qa-manifest.csv` 显示 `1,1.1,SUMMARY`、`1,1.5,SUMMARY`、`1,Unit 1,SUMMARY` 等无 `item_id` 行。
- T-44 既有 review verdict 已明确：`qa-manifest.csv` 仅保留 item 行，汇总信息应放在 `QA-自检.md`，否则下游解析器可能误读。

介入动作：

- 已记录本 gap note。
- 下一步给 manager 发送软提醒：不要改题目内容，不升级为 full subject closeout；只让 manager 确认 T-42 manifest parity 口径，并安排最小窄修或标为明天流程修复项。

临时结果：

- manager 已 ACK 并派 worker_course 做今晚窄修，不改题目内容。
- 文件层复查已通过：`AP Computer Science A/02-题库/items/Unit 1/qa-manifest.csv` 现为 `rows=15 / item_rows=15 / summary_rows=0`。
- T-42 仍保持 package-level approved / usable，未升级为 full subject closeout。

明天修复建议：

- 将 manifest parity 规则固化为通用检查：若 manifest 是 per-item schema，则禁止空 `item_id` 的 SUMMARY 行进入 `qa-manifest.csv`。
- review_course 对所有 AP package PASS 前应统一执行 `item_files == manifest item_rows` 与 `summary_rows == 0` 检查，汇总信息统一写入 `QA-自检.md`。

### 106. 08:32 复盘确认：AP 生产顺序偏离且 worker_builder 越权参与内容生产

触发时间：2026-06-23 08:32 CST

触发原因：

- 用户复盘指出两条红线：昨晚 AP 题库没有按“一个学科完成后再进入下一个学科”的节奏推进；`worker_builder` 也参与了内容生产。
- 复查 task truth、logs 与既有 gap note 后，发现这两点均有证据支撑，且昨晚监控最终总结过度强调 package-level delivered/approved，没有足够突出这两个生产组织层面的严重问题。

现场证据：

- `docs/plans/2026-06-23-ap-overnight-monitor-gap-note.md` 第 17、21、22 条已记录：AP Calculus AB 连续推进 Unit 1、Unit 2、Unit 3，并继续启动 `T-46 AP Calculus AB Unit 4`；同时 `T-42/T-43/T-44/T-45` 一度仍停在 assigned / waiting_worker_acceptance 或实际产物为 0。
- 第 22 条现场证据显示 manager 给 `worker_course` 的高优先级指令为：`当前只激活 T-46 AP Calculus AB Unit 4。T-43/T-44/T-45 你已接单但请暂缓启动，等我后续通知。不要同时推进多科。` 这与“4-5 个 AP 学科形成样本”的目标发生冲突。
- `.eduflow-team-state/facts/logs.jsonl` 显示 `1782153377653 manager say`：`T-42 AP CSA Unit 1 被 REVISION REQUIRED：缺少 actual MCQ item 文件。已派 worker_builder 返修，scope 限定为每个 subtopic 生成 U1.x.x-F/S/C.md 真实 MCQ 文件，并改 qa-manifest.csv 格式。`
- `.eduflow-team-state/facts/logs.jsonl` 显示 `1782153368670 worker_builder worker_builder_stage_ack`：`builder 已接单：T-42 被 review_course 判定 REVISION REQUIRED：目标路径缺少 actual MCQ item 文件。请返修...`
- `.eduflow-team-state/facts/logs.jsonl` 显示 `1782153617249 manager ack`：`T-42 返修完成：已在 02-题库/items/Unit 1/ 生成 15 道 actual MCQ item 文件...`
- `./scripts/eduflowteam task get T-42` 显示 `assignee: worker_builder`、`owner: worker_builder`，任务标题为 `AP Computer Science A Unit 1 题库生产`，并最终记录 `item_count=15`。
- 既有系统记忆/日志曾明确 `worker_builder` 角色边界是 agent 系统建设 / 运行维修 / 自动化编排，不负责课程内容建设；昨晚 AP CSA item 生成与 schema/content 返修越过了该边界。

介入动作：

- 已记录本 gap note。
- 当前先不直接修改 AP 内容，也不重写 task truth；本条作为复盘纠偏依据，供后续 manager 规则、workflow gate 和角色权限修复使用。

临时结果：

- 昨晚五个 AP Unit 的 package-level 产物可用性不等于生产流程健康。
- T-42 AP CSA 的最终产物虽然文件层可用，但其生产路径违反角色边界：builder 参与 actual MCQ 生成/返修，应标记为流程红线事件。
- AP Calculus AB 连续 Unit 深挖挤占其他学科启动窗口，说明“4-5 学科目标”在执行中被误读为“先 Calc 多 Unit，再补其他 Unit package”，不是用户期望的串行学科完成策略。

明天修复建议：

- manager prompt 与 workflow gate 增加硬规则：`worker_builder` 不得作为课程内容生产 owner/assignee；只能做工具、模板、校验器、runtime、workflow 修复。内容任务只能派给 `worker_course` 或明确的课程生产角色。
- task 创建层增加 role-scope validation：当任务标题/brief 包含 `题库生产`、`actual MCQ`、`课程研发`、`items` 等内容生产关键词时，拒绝 `worker_builder` 作为 assignee/owner，除非显式标记为 tool/template/schema-only。
- AP overnight manager closeout 必须按用户定义的策略写清：是“一个完整学科再下一个学科”，还是“每学科一个 Unit package 样本”。若目标是完整学科，不能用 Unit package-level approved 替代学科完成。
- 监控总结必须区分“产物层可用”与“流程层合规”；出现红线事件时，最终总结必须置顶风险，而不是放在明天修复项里弱化。

### 107. 08:35 复盘确认：AP 题库内容多为结构合格但质量偏低

触发时间：2026-06-23 08:35 CST

触发原因：

- 用户质疑昨晚生产出的 AP 题库内容质量不高。
- Codex 复查五个 AP Unit 的实际 item 文件与 QA 自检后，确认昨晚 review/QA 主要证明了字段、文件、manifest、答案一致性等结构层合格，但没有充分证明题目质量、AP 风格、干扰项质量、解析深度和认知层级。

现场证据：

- 机器扫描五个 Unit 产物显示字段完整、标题完整、答案格式完整，但内容质量指标偏弱：
  - `AP Statistics Unit 1`：45 题中 `exp<120` 字符占 62.2%，大量解析只是定义或一步计算，如 `U1.8.2-F.md` 解析仅 `IQR = Q3 - Q1 = 13 - 5 = 8.`。
  - `AP Psychology Unit 1`：15 题中 `exp<120` 字符占 46.7%，如 `U1.1.2-F.md` 只是问 `What is a hypothesis?`，解析为一句定义。
  - `AP Computer Science A Unit 1`：15 题中 `stem<90` 占 46.7%，generic stem 占 80.0%，如 `U1.5.1-F.md` 只问 `(int) 4.9` 的值。
  - `AP Calculus AB Unit 4`：解析较完整，但 21 题中 `stem<90` 占 76.2%，多为公式套用型题干。
  - `AP Physics 1 Unit 1`：题干和解析相对最好，但 generic stem 占 75.6%，仍偏模板化。
- 抽样文件证据：
  - `AP Statistics/02-题库/items/Unit 1/U1.3.1-F.md`：题目为 40 人中 10 人喜欢茶，问 relative frequency，解析仅一步 `10 / 40 = 0.25`。
  - `AP Statistics/02-题库/items/Unit 1/U1.7.1-F.md`：问 `symmetric/skewed right/uniform` 描述哪个特征，选项为 Center/Spread/Shape/Outliers，解析仅一句。
  - `AP Psychology/02-题库/items/Unit 1/U1.2.2-S.md`：体重秤每次读数不同，问 low reliability，题干与干扰项过直。
  - `AP Computer Science A/02-题库/items/Unit 1/U1.3.1-F.md`：`(3 + 4) * 2`，作为 AP CSA 题库样本过于基础，干扰项质量一般。
- `QA-自检.md` 的检查项多为结构项：文件命名、位置、YAML frontmatter、题目结构、难度覆盖、答案一致性、manifest 一致性；没有明确要求 AP 真题风格、干扰项诊断、认知层级、情境真实性、解析教学价值。
- 少量 draft-token 扫描命中为误报（如句首 `Starting...`、`Validity...`），不是主要问题；主要问题是题目浅、解析薄、干扰项弱。

介入动作：

- 已记录本 gap note。
- 当前不直接大规模改写 AP 知识库内容；先把质量结论回报用户，并建议明天将这些 Unit 标为 `structure-pass / content-needs-upgrade`，不能作为高质量题库智能体训练金样本直接使用。

临时结果：

- 五个 Unit 可作为 schema/manifest/workflow 样本，但不宜作为高质量内容样本。
- `AP Physics 1` 与 `AP Calculus AB` 相对可用度较高；`AP Statistics`、`AP Psychology`、`AP Computer Science A` 需要明显内容升级。
- 昨晚 `review_course PASS` 标准偏低，基本等同“结构 + 答案一致性 PASS”，没有达到“题库智能体内容质量 PASS”。

明天修复建议：

- 给 AP 题库新增内容质量 rubric：题干情境质量、AP 风格贴合度、干扰项诊断质量、解析教学价值、认知层级、非平凡性、答案唯一性、难度真实性。
- review_course PASS 必须拆成两个 verdict：`schema_pass` 与 `content_quality_pass`；只有两者都通过才能标为 qbank-agent ready。
- 对昨晚五个 Unit 做二阶段升级：每个 subtopic 保留 1 题基础题，另补至少 1 道场景型 / 推理型 / 常见错误诊断题；解析必须解释为什么其他选项错。
- 题库智能体建设应优先把这些产物归入 `seed / draft`，不要归入 `golden`。

### 108. 08:40 worker_course 反复出错但缺少复盘学习闭环

触发时间：2026-06-23 08:40 CST

触发原因：

- 用户指出 `worker_course` 多次生产出错后，系统只做局部返修，没有把错误转成下一轮生产前必须消费的经验、模板、校验器或 review gate，导致相同类型问题反复出现。
- 复查昨晚 gap notes、task truth 与产物 QA 结果后，确认这是系统性流程缺陷，不是单个 task 的偶发失败。

现场证据：

- `T-38 AP Calculus AB Unit 1` 曾出现交付路径错误、QA 计数/manifest 不一致、Obsidian 产物未同步等问题；后续修复主要落在当前产物，没有看到对应的 worker_course brief/template/validator 持久更新。
- `T-40 AP Calculus AB Unit 2` 曾出现 MCQ 双正确选项、manifest/Obsidian 证据误报等问题；后续生产仍继续依赖人工巡检与 review_course 捕捉，而不是在生产前自动拦截。
- `T-43 AP Physics 1 Unit 1` 曾出现 QA 计数声称 `39/13`，实际产物为 `45/15`，且 manifest 证据缺失；说明 worker_course 自检口径与实际文件 truth 没有绑定。
- `T-44/T-45` 一度出现 task/status/inbox/review queue 与实际产物不同步，任务进入 started/in_progress 或待 review 语义，但文件层产物为空或 review 未真正消费。
- 昨晚最终通过的五个 Unit 中，结构字段基本齐全，但内容质量仍偏浅：大量定义题、一步计算题、弱干扰项、短解析；说明 review_course 的 PASS 没有把“上一轮内容质量缺陷”提升为下一轮硬门槛。
- runtime/context 层也反复出现 `worker_course ready_unproven`、旧 inbox 指令污染、routing/context 不稳定等问题；这些问题被当作当轮巡检异常处理，没有形成 worker 启动前的健康检查与清理协议。

介入动作：

- 已记录本 gap note，将 `worker_course` 反复出错定义为“缺少错误复盘与学习闭环”的系统问题，而不是继续归因于某个具体 task 没做好。
- 当前不直接重写 AP 内容；优先要求明天修复 worker_course 的生产协议、记忆消费、校验器和 review gate。

临时结果：

- 昨晚 worker_course 产出的 AP package 只能视为 `structure-pass / content-needs-upgrade` 或 `seed draft`，不能作为题库智能体的 golden 样本。
- manager/review_course/Codex 监控都需要承担一部分责任：生产错误被修掉了，但错误类型没有进入下一轮生产的强制前置检查，所以系统会重复犯同类错。

明天修复建议：

- 建立 `worker_course known failure modes` 文件或 task memory，每次新生产任务启动前必须由 manager 明确注入并要求 worker_course ACK。
- 每次 `REVIEW REQUIRED`、Codex QA catch、manifest/path/schema/content 失败后，必须写一条 `lesson learned`：失败类型、触发证据、下次生产前检查项、对应 validator 或 rubric 更新。
- 更新 worker_course brief 模板：强制包含交付路径、item count、manifest parity、frontmatter schema、唯一答案、干扰项诊断、解析深度、AP 风格、Obsidian sync 证据。
- 增加自动校验器：路径存在、文件数等于 manifest item_rows、无 SUMMARY 行、每题唯一正确答案、字段完整、解析最低长度/包含错误选项解释、题干非模板化比例。
- review_course PASS 前必须检查“上一轮失败类型是否复发”；若复发，不允许 PASS，只能给 `REVISION REQUIRED` 并同步 manager。
- manager closeout 不得只说“已修复当前任务”；必须说明是否已把错误沉淀到 worker_course 的下一轮生产约束里。

### 109. 08:41 用户真实意图被误读：应先打磨完整第一学科样板，再进入下一学科

触发时间：2026-06-23 08:41 CST

触发原因：

- 用户进一步澄清：昨晚 AP 生产的本意不是“同时铺开 4-5 个学科/Unit package”，而是先把第一个学科打磨完整，沉淀生产经验、QA 标准、模板和复盘机制，再进入第二个学科，以便后续学科生产更快、更稳。
- 昨晚 manager 实际执行更接近“多 Unit / 多学科并行凑样本”，没有把第一学科作为可复制样板完成后再扩展，导致错误经验没有前置沉淀，后续学科继续重复踩坑。

现场证据：

- 昨晚最终 baseline 记录为 5 个 AP Unit package-level delivered/approved：AP CSA Unit 1、AP Physics 1 Unit 1、AP Statistics Unit 1、AP Psychology Unit 1、AP Calculus AB Unit 4；均不是 full subject closeout。
- 既有 gap note 第 106 条已确认：manager 一度连续推进 AP Calculus AB Unit 1-4，同时 T-42/T-43/T-44/T-45 仍有 assigned、waiting_worker_acceptance、实际产物为空或 review 未消费等状态。
- 第 108 条已确认：worker_course 反复出错后没有形成 `known failure modes`、lesson learned、模板更新、validator 更新或 review gate 强化；说明第一学科经验没有变成第二学科的生产加速器。
- 第 107 条已确认：五个 Unit 多数只达到结构层合格，内容质量偏浅，不能作为题库智能体 golden 样本；这与“先打磨第一个学科为样板”的质量目标不一致。
- Codex 监控总结和 manager closeout 曾使用 `package-level usable` 表述，容易弱化“完整学科样板尚未完成”的事实。

介入动作：

- 已记录本 gap note，将目标偏差定义为生产策略误读：正确策略应是 `Subject 1 golden path -> retro/lesson learned -> template/rubric/validator update -> Subject 2 faster run`。
- 当前不直接改写 AP 内容；本条作为明天重设 manager 指令、workflow gate 与验收标准的依据。

临时结果：

- 昨晚产物只能视为分散 Unit seed，不是用户想要的“第一个完整学科样板”。
- 进入第二学科前应补齐第一学科的样板闭环：内容质量、题型覆盖、QA rubric、自动 validator、review 标准、worker_course 复盘记忆。

明天修复建议：

- manager 的 AP 生产策略改为串行样板制：一次只激活一个学科，完成 `subject-level` 样板验收后，才能启动下一学科。
- 每个学科 closeout 前必须输出 `subject playbook`：目录结构、题目 schema、manifest 规则、常见错误、质量 rubric、可复用 prompt、validator 结果、review verdict。
- 第一学科完成后必须开一次 retro：列出生产错误、质量缺陷、workflow 卡点、角色边界问题，并更新 worker_course brief、review_course rubric、manager dispatch checklist。
- 第二学科启动时必须显式消费第一学科 playbook，并在 task brief 中声明“哪些经验已经继承，哪些差异需要调整”。
- 禁止用 `Unit package approved` 替代 `subject sample complete`；状态命名应区分 `unit_seed_ready`、`subject_sample_ready`、`qbank_agent_ready`。

### 110. 08:50 AP 线没有独立 workflow，成熟度明显低于 IGCSE 线

触发时间：2026-06-23 08:50 CST

触发原因：

- 用户指出 AP 线的 workflow 可能没有 IGCSE 线搭建得好。
- Codex 复查 workflow registry、`docs/workflows/igcse-subject-launch` 与昨晚 AP task truth 后，确认 AP 当前没有独立注册的 `ap-knowledge-base-optimization` workflow，昨晚实际借用了 `igcse-subject-launch`，而 AP 特有的学科样板制、qbank-agent schema、manifest item-only、内容质量 rubric、seed/package/subject 状态都没有形成专门 gate。

现场证据：

- `./scripts/eduflowteam workflow list` 只显示：`igcse-9subject-sprint`、`igcse-item-level-prototype`、`igcse-subject-launch`、`realrun-to-workflow`、`runtime-failover-hardening`；没有 `ap-knowledge-base-optimization`。
- `docs/workflows/igcse-subject-launch/README.md` 已有明确 Primary Chain、Required Result、Core Gates、Mounted Gate Contract，并要求 IGCSE course tasks carry `workflow_id=igcse-subject-launch`。
- `docs/workflows/igcse-subject-launch/checklist.md` 已有 closeout blocker、manager boundary gate、review verdict authority gate、revision-first gate、worker context guard、artifact consistency gate、subject continuation gate 等成熟约束。
- 昨晚 AP 任务 `T-38/T-40/T-41/T-42/T-43/T-44/T-45/T-46` 多数使用 `workflow_id=igcse-subject-launch`，说明 AP 是借 IGCSE 线的通用 gate 跑，而不是走 AP 专属 workflow。
- gap note #1-#3 已记录 manager 曾声称五科 `workflow_id=ap-knowledge-base-optimization` 已补齐，但 registry 中不存在该 workflow，task truth 仍显示 no_workflow。
- gap note #106/#109 已记录 AP 生产策略被误读为 Unit package 并行，而不是完整第一学科样板；这正是 AP 缺少专属 workflow goal gate 的表现。

介入动作：

- 已记录本 gap note。
- 当前不直接新增 workflow 文件或改代码；先把 AP workflow 成熟度缺口纳入今天维修包，建议作为 P0/P1 修复内容处理。

临时结果：

- AP 线当前不是没有 workflow 工具可用，而是没有 AP 专属 workflow 产品化层；借用 IGCSE workflow 可以提供部分 task/review/closeout gate，但覆盖不了 AP 题库智能体建设的核心差异。
- 继续用 `igcse-subject-launch` 跑 AP，会反复出现 scope 命名不准、evidence-account 字段不匹配、Unit package 与 subject sample 混淆、qbank-agent readiness 缺失等问题。

明天修复建议：

- 正式新增并注册 `ap-knowledge-base-optimization` workflow。
- AP workflow 必须包含：subject sample first gate、AP qbank item schema gate、manifest item-only parity gate、content quality rubric gate、role boundary gate、lesson learned/retro gate、seed/package/subject/qbank-agent ready 状态。
- manager 创建 AP 任务时应默认挂 `ap-knowledge-base-optimization`，若 workflow 不存在或未挂载，task create/dispatch 应阻止或显式报错。
- AP workflow 的 closeout target 应明确区分 `unit_seed`、`unit_package`、`subject_sample`、`full_subject`、`qbank_agent_ready`，禁止 package PASS 自动升级。
- 将 `docs/workflows/igcse-subject-launch` 中成熟的 gate 迁移/改写为 AP 版本，而不是继续直接复用 IGCSE 名称和 evidence 口径。

### 111. 08:52 workflow 搭建本身缺少“可复制生产线”验收标准

触发时间：2026-06-23 08:52 CST

触发原因：

- 用户进一步指出：AP workflow 没有搭出专属层，背后说明“搭建 workflow”这件事本身也缺少完整对齐标准。
- 若 workflow 搭建阶段没有定义什么叫一条可复制生产线，后续每次切到新学科/新任务都会重新临场拼装，导致目标、角色、gate、QA、复盘、状态命名反复漂移。

现场证据：

- `igcse-subject-launch` 已经形成较成熟的 README/checklist/roles/trigger/handoff-template，但 AP 昨晚没有先复制并改造成 `ap-knowledge-base-optimization`，而是直接借用 IGCSE workflow。
- gap note #1-#3 显示 manager 曾口头声称 AP workflow 已补齐，但 registry 中不存在 `ap-knowledge-base-optimization`，task truth 仍 no_workflow 或借 IGCSE workflow。
- gap note #106/#109/#110 显示 AP 生产目标、角色边界、Unit/package/subject 状态和题库智能体 QA 标准都没有在 workflow 搭建阶段先对齐。
- 昨晚多个问题本质上不是执行层不知道怎么做，而是 workflow 没有提供“进入下一学科前必须沉淀并验收”的生产线标准。

介入动作：

- 已记录本 gap note。
- 当前先不直接修改 workflow 文件；将其纳入今天 repair package 的上层修复：新增 workflow-building standard，即先验收生产线，再允许用它跑下一学科/任务。

临时结果：

- AP 缺少独立 workflow 不是孤立问题，而是 workflow 搭建方法论缺口。
- 后续不能只说“为 AP 新增一个 workflow”，还要定义“新增 workflow 什么时候算搭好了”。

明天修复建议：

- 建立 `workflow readiness standard`：每条新 workflow 必须具备 README、roles、trigger、checklist、handoff-template、task mount rule、review gate、artifact verifier、evidence-account mapping、closeout target、retro/lesson learned gate。
- 新 workflow 上线前必须跑一个 pilot：只跑一个最小 subject/task，完成后输出 playbook 和 gap retro，才能进入下一 subject/task。
- workflow registry 不允许 manager 口头声明不存在的 workflow_id；task create/dispatch 必须校验 workflow_id 已注册。
- 每条 workflow 必须定义“可复制标准”：输入边界、角色边界、交付物 schema、QA/rubric、review verdict 写回、失败复盘、下一轮继承方式。
- 将 workflow 搭建也拆成标准任务：`design -> dry-run -> pilot -> retro -> register -> production use`，不能边生产边临时补 workflow。
