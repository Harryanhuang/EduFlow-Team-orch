# 2026-06-21 IGCSE Overnight Monitor Gap Note

## 监控范围

- 飞书群：`oc_31f0f00378bea36dd5e8f69256cc7a5e`
- 观察目标：
  - `topic -> QA -> review -> manager closeout`
  - 尽量让群内现有生态先自修
  - 只在自修明显失效时考虑直接介入

## Codex 介入记录硬规则

用户补充要求：今晚每次 Codex 亲自出手，都必须记录 gap note，方便明天判断“为什么需要人类/主控介入”。

适用范围：

- 给 manager / worker / reviewer / auto_ops 等 agent 发纠偏、催办、停止、重派、标准确认消息。
- 直接修改 task/status/facts/workflow 状态。
- 重启 daemon、router、watchdog 或 agent pane。
- 直接改代码、脚本、测试、内容产物。
- 直接替 agent 做本应由链路完成的 closeout / approve / reject。

记录格式：

- 触发原因：为什么不能继续等生态自修。
- 现场证据：task/status/log/message/file verifier 的关键证据。
- 介入动作：Codex 具体做了什么，尽量写 message id / command / 文件路径。
- 临时结果：介入后现场状态有没有回正。
- 明天修复建议：应该产品化/自动化修哪里，避免再次靠 Codex 出手。

### 31. Codex 介入记录规则被正式固化

触发原因：

- 用户明确要求“每次出手都要记录 gap note”。
- 今晚已经出现多次 Codex 纠偏：例如阻止 Business Studies 0450 从 12-item 达标产物回退到旧 9-item 标准。
- 如果不固定记录模板，明天复盘会混在普通观察日志里，难以区分“生态自修成功”与“Codex 人工兜底”。

现场证据：

- `T-10` 当前仍在 `submitted_for_review`，`verdict=pending`。
- review queue 仍显示 `T-10` awaiting `review_course`。
- 已有 gap 30 记录：manager 在收到纠偏后仍出现旧标准回流，Codex 已向 manager / worker_course 发送停止和纠偏消息。

介入动作：

- 在本 gap note 顶部新增“Codex 介入记录硬规则”。
- 明确后续每次发消息、改状态、重启服务、改代码/产物、替链路收口，都要追加独立 gap 条目。

临时结果：

- 今晚后续监控有了统一判定口径：只观察不算出手；一旦 Codex 对系统施加影响，就必须落 note。

明天修复建议：

- 可以把该模板沉淀为 `eduflowteam gap note add --intervention` 命令，自动带时间、task id、agent、message id、evidence 字段。
- 对人工介入消息增加统一 tag，例如 `codex-intervention`，方便从 logs.jsonl 自动汇总。

## 本轮新增稳定事实

### 1. Economics 0455 已有大规模真实产物

当前 repo 已存在：

- `content/igcse-economics-0455/manifest.md`
- `content/igcse-economics-0455/items/*.md`
- `content/igcse-economics-0455/qa-question-level/*.md`

从目录真相看：

- items 已覆盖多组 topic
- `qa-question-level` 已大规模落盘
- 不是“manager 口头说做完”，而是文件面已有真实生产

配套运行态状态也显示：

- `worker_course` 状态：`完成`
- 文案：`IGCSE Economics 0455 最小闭环：26 topics, 300 QA, manifest 已产出`

### 2. Economics 0455 已进入正式 review，但最终收口证据还不够强

当前状态文件显示：

- `manager`：`进行中`
  - `Economics 0455 review 跟踪 + 其他线推进`
- `review_course`：`进行中`
  - `Economics 0455 26 topics × 300 QA 文件级深度复核`

日志里也有 manager 派给 review 的证据：

- `Economics 0455 最小闭环已生产完毕，请进行正式 review`

但截至本轮检查，尚未看到足够强的“正式 closeout 已完成”证据，例如：

- 明确的最终 review verdict
- manager 的正式收口消息
- status 面已从 review tracking 切到 completed

结论：

- `Economics 0455` 不是没做，而是**真产物已经远远跑在前面**
- 当前主要风险不在生产缺失，而在**正式 review / closeout 证据链仍未完全收口**

### 3. Physics 0625 已从 Batch 1 修复推进到 Batch 2+

日志证据显示：

- `Physics 0625 Batch 1` 先经历了 review 返修
- manager 明确追着修：
  - `Q-1.4-07` 答案修正
  - `2.1 Q-06` 修正
  - items 难度分布调整
- 随后出现：
  - `Physics 0625 Batch 1（topics 1.1-2.4）已通过 review_course 第2轮复检`
  - 并派发 `Batch 2+`

结论：

- `Physics 0625` 这条线不是停住，而是在继续往 question-level QA 扩展
- 但它也再次证明：**review 返修链路已经真实存在，而且 manager 会继续推进**

## 本轮最关键的新 gap

### Gap A：router 不是“完全死掉”，而是“反复 catch-up 后静默抖动退出”

`health` 当前显示：

- `watchdog` alive
- `router` no pid file / not running

进一步看进程与日志后，事实更细：

- `watchdog` 进程存在
- `router` 会被拉起
- `router.log` 连续出现模式：
  - `router subscribing`
  - `catching up X missed message(s)`
  - `no events for 120s+; subscribe likely silently stalled, exiting for respawn`

这说明问题不是：

- router 永远起不来

而是：

- router 能短暂恢复
- 会补抓 missed messages
- 但在短静默窗口中把自己判成 stalled 并退出
- 随后依赖 watchdog 再次拉起

这属于 **半恢复 + 抖动**，不是简单的“启动失败”。

这点很重要，因为明天修的时候方向会不同：

- 不是只修 “拉不起来”
- 而是要修：
  - subscribe 静默检测阈值是否过严
  - idle 群在低消息量时是否被误判
  - catch-up / live subscribe 的切换策略是否不稳定

### Gap B：运行态告警与真实运行面之间存在“半同步”错觉

`health` 会报告：

- router not running

但系统里又同时存在：

- watchdog 日志中的 `router respawned`
- 进程表里短时 router 进程
- router.log 中持续 catch-up 的证据

这意味着 operator 很容易看到两种互相冲突的印象：

1. “router 死了”
2. “router 不是活着吗，还在 catch up”

更准确的表述应该是：

- router **不是完全 down**
- router **也不是稳定 healthy**
- 它处在 **反复重连、可消费部分消息、但会周期性自退** 的抖动状态

### Gap C：worker_builder 当前被占在运行态维修，不能被误当作内容产能

状态文件显示：

- `worker_builder`：`进行中`
- 任务：`修复 router/watchdog 运行问题`

而更早日志里也出现过一次边界冲突：

- manager 曾把 `Physics 0625` 的 question-level 生产派给 `worker_builder`
- `worker_builder` 明确回绝，说明这不是它的职责边界

这说明当前团队已经部分具备了边界自修能力：

- builder 会回推“这不是我的 lane”

但也说明 manager 在高压状态下仍会发生：

- 把运行维修 lane 和内容生产 lane 混用

## 当前判断：是否需要我直接下场修

截至这一轮，我的判断是：

- **内容生产链条暂时不需要我直接下场替做**
  - Economics 有真产物
  - Physics 在继续推进
  - review 链路在工作

- **运行态问题已经到了“接近需要直接介入”的边缘，但还可先再观察一轮 builder 自修结果**
  - manager 已正式把 router/watchdog 修复派给 `worker_builder`
  - `worker_builder` 当前状态也显示正在做这件事
  - 因此先不抢修，保留自修窗口

如果下一轮仍出现下面任一情况，就该考虑直接介入：

1. `router.log` 继续重复 `120s idle -> exit`，没有任何改善
2. `health` 持续多轮报告 router not running
3. `worker_builder` 状态不再推进，或长期卡在 initializing / stuck
4. `Economics 0455` 已 review 很久，但 manager 仍无正式 closeout

## 明天升级修复优先级建议

### P1

- router subscribe 静默检测与 respawn 抖动问题

### P1

- manager closeout 证据链
  - 真产物已存在时，如何更稳定地产生最终 review verdict 与正式收口

### P2

- manager lane 边界稳定性
  - 避免把 `worker_builder` 错派到内容生产

### 32. Codex 介入：学科线在“待命下一学科”处停止

触发原因：

- 用户指出“就停了”“一没有定就停了”，需要验证是否是链条本身缺自动续跑逻辑。
- Accounting 0452 Batch 3 已 PASS closeout 后，manager 对外消息变成“待命下一学科，请老板指示”，但今晚目标是持续跑 IGCSE 实例，不应在已有 backlog 时进入空等。

现场证据：

- 时间：2026-06-21 04:29 CST。
- `./scripts/eduflowteam task list` 仍显示多个未完成/待处理任务：
  - `T-8 IGCSE Physics 0625 Batch 1 topic-outline + QA seed` 为待处理。
  - `T-9 IGCSE Economics 0455 正式复核` 为待处理。
  - `T-7 Accounting 0452` 已在群内 closeout，但 task list 仍为进行中，状态回收不干净。
- `./scripts/eduflowteam inbox manager/worker_course/worker_qbank/worker_builder` 均为空，说明没有 agent 正在等待处理新指令。
- `health` 显示 router/task-publish/watchdog 均 alive，worker_course / worker_qbank pane ready，当前不是运行态整体掉线。

介入动作：

- Codex 准备向 manager 发出续跑纠偏：不要等待老板再定下一科；按现有 backlog 自动推进，并显式挂上 `igcse-subject-launch` workflow。
- 要求 manager 先完成状态回收，再开下一条线：
  1. 回收 `T-7` task 状态为已完成/closeout。
  2. 继续推进 `T-9 Economics 0455 正式复核`，若此前已 PASS 则补齐证据链并 closeout。
  3. 启动 `T-8 Physics 0625` 或下一待处理 IGCSE 学科线，明确 owner=`worker_course`、reviewer=`review_course`、workflow_id=`igcse-subject-launch`。
  4. qbank v3.2 仍保持 review/approval gate，不得自动 apply。

临时结果：

- 待观察 manager 是否从“待命”切回“自动续跑”，并是否把 workflow_id 挂到后续任务。

明天修复建议：

- 给 manager 增加 backlog auto-next 规则：当目标为 overnight run 且已有待处理 IGCSE task 时，closeout 后不得进入“等待老板指示”，必须自动选择下一可执行任务。
- task closeout 应同步更新 task list，避免群内已完成但 task 状态仍为进行中。
- workflow 应成为强制字段：IGCSE 学科线新任务若缺 `workflow_id=igcse-subject-launch`，manager 应自动补挂并对外说明。

### 33. Codex 介入：manager 外显“已执行”，但结构化状态和 inbox 未落地

触发原因：

- manager 收到 Codex 纠偏后在群里宣布“4 项全部执行”，但底层验证不一致。
- 若只看群消息会以为链条恢复；若看任务和 inbox，实际仍可能没有派单，属于今晚“消息处理口/状态同步口”问题的典型样本。

现场证据：

- manager pane 显示“已完成处理：T-7/T-9 状态已更新，T-8 已启动，worker_qbank 查 manifest”。
- 群日志 `log_1781987532251_7de055ca1a` 对外宣称：
  - `T-7 Accounting 0452 已正式 closeout`
  - `T-9 Economics 0455 复核 PASS，task 状态已补齐`
  - `T-8 Physics 0625 已启动`
  - `qbank backlog 盘点已派 worker_qbank`
- 但 `./scripts/eduflowteam task list` 仍显示：
  - `T-7 [进行中]`
  - `T-8 [待处理]`
  - `T-9 [待处理]`
- `./scripts/eduflowteam inbox worker_course/review_course/manager` 均为空。
- `./scripts/eduflowteam inbox worker_qbank` 为空，说明所谓“已派 worker_qbank”没有真实投递。
- `.eduflow-team-state/tasks.json` 里 T-7/T-9 只有 `updated_at` 被刷新，`status/completed_at` 未正确变更。
- `eduflow task` usage 显示正确更新方式应是 `task update <id> --status S --desc D` 或 `task done <id>`；manager 使用了错误参数形态，导致声明与状态不一致。

介入动作：

- Codex 决定直接补齐最小结构化动作：
  1. 用正确 task 命令更新/完成 T-7、T-9。
  2. 将 T-8 从待处理推进到进行中，并向 worker_course 真实投递 Physics 0625 第一批任务。
  3. 向 worker_qbank 真实投递 qbank backlog/manifest 盘点任务，但继续禁止 v3.2 未审先 apply。
  4. 再次验证 task list 与 inbox，而不是只信群消息。

临时结果：

- 已由 Codex 直接补齐结构化状态：
  - `T-7` 已从 `进行中` 改为 `已完成`，desc 补齐 Accounting 0452 closeout 证据。
  - `T-9` 已从 `待处理` 改为 `已完成`，desc 补齐 Economics 0455 closeout 证据。
  - `T-8` 已从 `待处理` 改为 `进行中`。
- 已真实投递两条 inbox：
  - `worker_course ← codex_monitor`：`msg_1781987704853_589fc03482`
  - `worker_qbank ← codex_monitor`：`msg_1781987706089_406e3b6ada`
- 复查 `task list` 已显示 T-7/T-9 完成、T-8 进行中。
- `worker_qbank` 已完成 manifest 盘点并回报：Physics manifest 严重不完整，Economics/Business manifest.md 被 verifier 误报 missing。

明天修复建议：

- manager 对外发布“已派/已更新/已 closeout”前，应强制读取 task list / inbox / message id 作为 postcondition。
- `task update` 错参应返回非零并提示正确 usage，避免只更新 `updated_at` 却被误判成功。
- 群公告应自动附带结构化证据：task_id status、投递 message_id、workflow_id。

### 34. Codex 介入：T-8 Physics 完工但未进入 review gate

触发原因：

- `worker_course` 已完成 T-8 Physics 0625 batch 1，但 `review_course` inbox 为空。
- 这说明链条从“生产完成”到“review_course 复核”又断在消息/派单层，不应继续等。

现场证据：

- `worker_course` pane 显示已完成：
  - Physics 0625 batch 1，topics `1.1 / 1.2 / 2.1 / 2.2`
  - 每个 topic 5 个 QA seed，manifest 已更新 submitted
  - 发现额外问题：`items/2-1-items.md` 和 `items/2-2-items.md` 内容似乎互换
- logs.jsonl 里出现两条异常外显：
  - `log_1781987749891_7e5c90a490` agent=`--body`
  - `log_1781987772344_5dd5b1ece5` agent=`--body`
- 这是已知消息处理问题的复现：`eduflow say --to ... --body ...` 被错误记录为 `agent="--body"`，影响后续消费。
- `./scripts/eduflowteam inbox review_course` 为空，说明 review gate 没有收到真实任务。

介入动作：

- Codex 将向 manager 发出补派 review 指令，要求 manager 用真实 inbox message id 把 T-8 交给 `review_course`，并明确复核重点：
  1. 4 个 topic outline + QA seed 是否达标。
  2. `qa-manifest.csv` 是否同步。
  3. `items/2-1` 与 `items/2-2` 是否存在内容互换。
  4. 复核后由 manager closeout 或退回 worker_course。

临时结果：

- 待 manager/review_course 回应后验证。

明天修复建议：

- `say` 命令需要明确禁止/修复 `--to ... --body` 错位解析，避免 `agent="--body"`。
- worker 完工后应有 `task submit-review` 或等价自动动作，不能只靠群消息触发 review。
- review gate 的 postcondition 应检查 reviewer inbox 或 task event，而不是只检查 logs.jsonl。

### 35. Codex 介入：T-8 已群内 closeout，但 task 状态仍停在进行中

触发原因：

- T-8 Physics 0625 Batch 1 已经过 `review_course` PASS 且 manager 群内 closeout，但结构化 task list 仍未更新。
- 这会导致后续 monitor/manager 误判 T-8 仍在进行中，影响自动续跑和 backlog 选择。

现场证据：

- `review_course` 最终 PASS：
  - `log_1781988161992_2f921b452d`：manifest 修复确认 PASS，4 topic outline + 36 QA + items 全部通过，可 closeout。
  - `log_1781988181496_24ecf80824`：`task_completed`，T-8 PASS。
- manager 已群内 closeout：
  - `log_1781988219521_a6ce7118cd`：`✅ T-8 Physics 0625 Batch 1 正式闭环`，4 topic / 36 QA / 4 items。
- 但 `./scripts/eduflowteam task get T-8` 仍显示：
  - `T-8 [进行中]`
  - desc 仍是启动描述，未记录 PASS closeout。

介入动作：

- Codex 将用正确 task 命令补齐 T-8 结构化状态：
  - `task done T-8`
  - `task update T-8 --desc ...`
- 补完后复查 `task get T-8` 和 `task list`。

临时结果：

- 待执行后验证。

明天修复建议：

- manager 群内 closeout 必须自动调用 `task done` 或等价 closeout API。
- `review_course task_completed` 事件应触发 manager action；manager 消费后必须把 task 状态落库。
- task list 状态应作为 manager closeout 的 postcondition，未更新时禁止对外说“正式闭环”。

### 36. Codex 介入：T-8 closeout 后再次等待老板确认下一批

触发原因：

- manager 在 T-8 Physics 0625 Batch 1 closeout 后再次进入“等待老板确认下一学科 / 下一批次”。
- 今晚目标是持续跑 IGCSE 实例，并且 qbank/manifest 盘点已经明确 Physics 0625 仍有大量 backlog，不应停在人工确认。

现场证据：

- `log_1781988219521_a6ce7118cd`：manager 群内宣布 T-8 Physics Batch 1 正式闭环后，结尾为“等待老板确认下一学科 / 下一批次”。
- `worker_qbank` 盘点结论：
  - Physics 0625 `qa-manifest.csv` 仅 4 行（batch-01: 1.1-2.2）。
  - unified manifest 覆盖 46 topics，仍缺 42 个 topic。
- `task list` 已显示 T-8 完成，但仍有旧任务/后续 Physics backlog 未进入自动续跑。

介入动作：

- Codex 将向 manager 发出续跑指令：
  1. 不跳新学科，优先继续 Physics 0625 下一批。
  2. 按 `igcse-subject-launch` workflow 派 `worker_course` 生产 Physics Batch 2。
  3. owner=`worker_course`，reviewer=`review_course`，完成后走同样 review/返修/closeout 链。
  4. qbank v3.2 继续保持 review/approval gate，未 PASS 不 apply。

临时结果：

- manager 已真实投递 `worker_course`：
  - `msg_1781988495510_ada51f6fe0`
- `worker_course` 已 ACK 并开始生产 Physics Batch 2，选题为：
  - `1.3 Free fall / g / air resistance`
  - `1.4 Scalars and vectors / centre of gravity`
  - `1.5 Density / measuring density`
  - `2.3 Work-energy conservation`
- 但 `task list` 仍没有新增 T-11 / Physics Batch 2 结构化任务，只显示旧的 10 个任务。
- Codex 将补齐结构化 task 记录，避免后续 review/closeout 继续丢状态。

明天修复建议：

- manager 应有 “same subject continuation” 规则：某学科只完成 batch 1 且 manifest/backlog 仍大量缺失时，默认继续本学科下一批，不询问新学科。
- closeout 后的 next-action 生成应优先读取 qbank/manifest gap，而不是回退到“等待老板”。
- 对 overnight goal 增加运行态 flag：`auto_continue=true` 时 manager 不得输出“等待老板确认下一批”。
- manager 派出新 batch 时必须同步创建结构化 task；仅 `remember` + inbox 不足以支撑 review/closeout 自动化。

### 37. Codex 介入：Batch 2 完工送审再次被 `--body` 消息解析吞掉

触发原因：

- worker_course 已完成 Physics 0625 Batch 2，并尝试送 review_course。
- 但 review_course inbox 为空，T-11 task 仍停在 `queued`，说明完工送审没有进入 review gate。
- 这是 `eduflow say --to review_course --body ...` 被错误记录为 `agent="--body"` 的又一次复现。

现场证据：

- `worker_course` pane 已完成 Batch 2：
  - 4 topics: `1.3 / 1.4 / 1.5 / 2.3`
  - 每 topic 9 items，难度 `F:2|S:4|C:3`
  - manifest 已更新到 8 topics
- logs.jsonl 异常记录：
  - `log_1781988784585_87903e2493` agent=`--body`：Batch 2 COMPLETE。
  - `log_1781988784700_4310d3a567` agent=`--body`：试图发给 review_course 复核。
- `./scripts/eduflowteam inbox review_course`：无未读。
- `./scripts/eduflowteam task get T-11`：仍为 `queued`，latest_turn_summary 仍是 `Task created and queued`。

介入动作：

- Codex 将补齐 review gate：
  1. 把 T-11 推进到正确阶段（worker in progress / submitted_for_review）。
  2. assign reviewer=`review_course`。
  3. 给 review_course 真实投递 Batch 2 复核任务，要求检查 items numbering、difficulty labels、manifest sync、content accuracy、无草稿残留。
  4. 验证 review_course inbox 或 ACK。

临时结果：

- 待执行后验证。

明天修复建议：

- 必须修复 `eduflow say` 参数解析，特别是 `--to X --body Y` 不应把 sender 解析成 `--body`。
- worker 完工送审应优先使用 task API（`submit-review` / `assign-reviewer` / inbox send），不要依赖群消息。
- task 状态和 review inbox 应由同一动作原子更新，避免“产出完成但 review gate 未接上”。

### 38. Codex 介入：T-11 PASS 后 closeout API 入口不匹配

触发原因：

- T-11 Physics Batch 2 已 PASS，review_course 也明确写出“可 closeout”。
- 但尝试 `task manager-closeout T-11 --actor manager` 返回 `subject closeout not ready: not_subject`，说明这个任务不能走 subject closeout 专用入口。
- 若不补正，任务列表会继续停留在 submitted_for_review，和群内 closeout 不一致。

现场证据：

- `review_course` 两条 PASS 消息：
  - `msg_1781989094890_ed49a92d27`
  - `msg_1781989100114_6a293738cd`
- 以上明确写出 `可 closeout`。
- `task get T-11` 仍显示 `submitted_for_review`。
- `task manager-closeout T-11 --actor manager` 返回：
  - `❌ subject closeout not ready: not_subject`

介入动作：

- Codex 先记录此入口失配，再用通用 task 完成入口收口 T-11。
- 目标是让 task list、review verdict、群内 closeout 三者一致。

临时结果：

- 待用通用 task 入口完成后验证。

明天修复建议：

- task API 应把 `manager-closeout` 的适用范围在帮助里说清楚，避免 PASS 任务误走入口。
- 不同 task 类型应有明确 closeout 路由，避免 review PASS 后仍卡在 `submitted_for_review`。
- 最终状态必须由单一 source of truth 驱动，不能靠群消息单独宣告闭环。

### P2

- status / health 对“半恢复”状态的表达
  - 不要只给 `alive / dead`
  - 需要能表达 `alive but flapping`

## 当前结论

这轮最重要的不是“又发现了更多内容文件”，而是确认了两件事：

1. **IGCSE 生产链条在继续跑，而且 Economics 0455 的真实产物已经非常重**
2. **真正脆弱的地方正在转向运行层抖动与正式收口证据链，而不是单纯没产出**

## 续跑补充（纠偏后）

### 1. manager 已经部分收敛回正确主线

在补发“不要再并行开新学科、先收口 Economics 0455”的最小纠偏后，状态面出现了一个积极变化：

- `manager` 当前状态变成：
  - `等待 review_course Economics 0455 verdict`

这说明纠偏至少在主线层面已经起作用：

- manager 没有继续把 Physics / 新学科并发拉成新的主线
- 目前最核心的等待点已经收敛到 `Economics 0455 formal verdict`

这不是最终完成，但说明：

- **manager 还不是失控状态**
- **最小纠偏足以把它拉回到正确等待点**

### 2. 运行态最准确描述是 flapping，不是 simple down

用 repo-local 环境重新检查后，当前更准确的运行态如下：

- `router`: alive
- `watchdog`: alive
- `task-publish`: 在 repo-local health 里显示 `no pid file`
- `router.log`: 持续出现
  - subscribe
  - catch up missed messages
  - 120 秒静默
  - 自退
  - 再被 watchdog 拉起

因此明天不要再用“router 死了”这种过粗表述。

更准确的结论是：

- `router` **活着，但在 flapping**
- `watchdog` **能拉起 router，但没解决根因**
- `task-publish` **在 repo-local 运行面上还有稳定性疑点**

### 3. state_dir 不一致仍然是高风险误判源

这一轮再次确认：

- 不 source `scripts/eduflow-team-env.sh` 时，`health` 会落到默认 `~/.eduflow`
- source 后，repo-local `.eduflow-team-state` 的真相又不一样

这意味着：

- 同一时刻可能同时看到两套互相冲突的健康面
- operator 很容易误以为“系统刚刚又坏了”

这条不是新发现，但已经反复影响判断速度，应该继续保留在明天修复清单的高位。

### 4. formal closeout 关键点容易退回到 initializing，拖慢最后一拍

在本轮纠偏已经把主线收敛到 `Economics 0455` 之后，又观察到：

- `manager`: `进行中 | initializing`
- `review_course`: `进行中 | initializing`
- `worker_builder`: `进行中 | initializing`

其中最危险的不是 builder，而是：

- `review_course` 明明已经拿到 `Economics 0455` 的正式 review 指令
- `manager` 明明已经知道当前主线只剩 `Economics 0455 verdict`
- 但两者在 closeout 前的关键窗口仍可能退回 `initializing`

这会带来一个坏结果：

- 生产阶段已经完成
- 但正式收口动作不发生
- 团队表面上“都在线”，实际上最后一拍不落锤

这说明当前系统除了生产与运行问题外，还有一个更细的协作缺口：

- **formal verdict / formal closeout 的最后一拍缺少更强的状态机约束**

明天修的时候建议单列：

- 当 manager 主线已经收敛到 `waiting review verdict`
- 且 review 已收到 formal review 指令
- 这两个角色不应再长时间回到泛化的 `initializing`
- 应该进入更明确的状态：
  - `reviewing_evidence`
  - `awaiting_verdict`
  - `ready_for_closeout`

### 5. status 口径开始互相冲突，说明状态机回流面有断层

这一轮又出现一个更细的断层：

- `manager` 状态：
  - `Economics 0455 等待 review_course 复核`
- `review_course` 状态：
  - `上一轮复核全部完成，待新任务`
- `worker_builder` 状态：
  - `router/watchdog 修复已完工`

但从 repo-local health / supervisor / router log 的真实面看：

- `Economics 0455` 并没有明确 closeout
- `review verdict` 至少没有被 manager 正式消费
- `router` 仍持续 flapping
- `task-publish` 仍有 repo-local 异常信号

这说明问题已经不只是“agent 慢”或“agent 没做”，而是：

- **状态口径和真实待办正在分叉**

更直白地说：

- status.json 里有人说“做完了”
- manager 还在等
- 运行日志又证明其实还没真正稳定

这种情况对明天修复很关键，因为如果只看状态面，会误以为：

- review 已完成
- builder 已修完

但真实上：

- closeout 没发生
- router 没稳定

建议明天把这个问题单列成：

- `status truth lag / status contradiction`

需要的不是单纯“多发提醒”，而是：

- 明确 status 更新必须绑定哪类真相
  - formal verdict 已发送
  - manager 已消费并 closeout
  - runtime 连续稳定一段时间
- 否则 agent 不得把自己标成 `待新任务` / `已完工`

### 6. 任务真相面已能直接证明 closeout 没发生

这一轮进一步确认，问题不只存在于 status 和群消息层。

在 `.eduflow-team-state/tasks.json` 中：

- `T-9`
  - 标题：`IGCSE Economics 0455 正式复核`
  - assignee：`review_course`
  - status：`待处理`

这条证据非常关键，因为它说明：

- `Economics 0455` 的正式 review 并没有在系统真相面完成
- 不是“大家感觉上差不多了”
- 而是 **任务层明确还没被推进**

这也解释了为什么会同时出现：

- `worker_course` 说 Economics 已全部完工
- `review_course` 说上一轮复核已完成
- `manager` 说等 verdict
- 但最终 closeout 还是没发生

因为系统中真正承担 formal review 的那条任务：

- **T-9 还停在待处理**

明天修的时候，这一点应当作为高价值诊断事实保留：

- 不要只查群消息
- 不要只查 status.json
- 要把 task truth 一起对齐

理想状态应该是：

1. manager 派出 `T-9`
2. `review_course` 进入 `in_progress`
3. 给出 verdict
4. `manager` 消费 verdict 并 closeout
5. task truth、status、群消息三面一致

## 00:51 CST 补充

### 7. Economics 0455 已拿到正式 verdict，但 manager 仍停留在“等 verdict”叙事

截至 `2026-06-21 00:51 CST`，新证据已经足够明确：

- `review_course` 已发正式质检结论：
  - `Verdict：不通过（系统性难度分布不合规）`
- 退回主因非常集中：
  - 26 个 topic 的难度分布系统性偏向 Foundation / Standard
  - Challenge 明显不足
- 修复要求也已经明确：
  - 全量调整 26 个 topic 的难度分布
  - Challenge 题不能只改标签，必须补足 evaluation / analysis 深度

但与此同时：

- `manager` 仍在日志里说 `等 verdict 后收口`
- `tasks.json` 中 `T-9` 仍是 `待处理`
- `review_course -> manager` 的 verdict 卡片在 inbox 中仍是 `read=false`

这说明当前最关键的阻塞不再是：

- review 没做完

而是：

- **manager 还没有消费已存在的 formal verdict**
- **task truth 还没从“待处理”推进到修复 / 复审链路**

因此这一轮最重要的最小纠偏不是“催 review”，而是：

- 要求 manager 立刻把 Economics 0455 从“等 verdict”切换为“派修复单 -> 复审 -> closeout”

### 8. 已对 manager 做窄口纠偏，避免它继续走偏

本轮已向 `manager` 发出最小纠偏：

- 明确指出 `review_course` 已给出 Economics 0455 的正式 `不通过`
- 要求它只围绕 `T-9` 收口：
  - 立刻派 `worker_course` 修复
  - 修完再送 `review_course`
  - 把 task truth 从 `待处理` 推进
  - 群里不要继续说“等 verdict”
- 明确约束：
  - **先不要切新学科**

这条纠偏的意义不是接管 manager，而是：

- 防止它继续停留在过时叙事
- 把整个链条重新拉回 `review -> repair -> re-review -> closeout`

### 9. 运行面再次证明“builder 说修好”不能直接等于“系统已稳定”

截至 `2026-06-21 00:51 CST`：

- Hermes 又发了一轮新的高优先级巡检告警
  - `health_bad=2`
  - `router_alive=false`
  - `watchdog_alive=false`
- repo-local `health` 则显示：
  - `router: no pid file`
  - `task-publish: alive`
  - `watchdog: alive`
  - 另有 `manager runtime env drift` warning
- `router.log` 仍持续出现：
  - subscribe
  - catch-up missed messages
  - `no events for 120s+`
  - 自退 / respawn / fallback polling

所以当前最准确的描述仍然是：

- 不是“彻底 down”
- 也不是“已经稳定修复”
- 而是 **runtime 处于反复抖动、状态面和真实面来回打架**

这意味着后续对 `worker_builder` 的要求应该更严格：

- 不再接受单纯的“修复完成 / 全绿闭环”结论
- 必须附可复核事实：
  - repo-local health
  - daemon 实际存活
  - router 是否仍在 fallback / stall

这一条已经做了口径纠偏，后续继续观察。

### 10. `review verdict -> manager 派修 -> worker 修复` 这段链路目前存在“消息到了，但没有被消费成动作”

到 `2026-06-21 00:56 CST` 为止，新的证据说明当前不是“没人提醒”，而是：

- `review_course -> manager` 的 Economics 0455 正式退回卡片已经存在
- 我方也已连续补发多轮最小纠偏给 `manager`
- 也已补发一轮给 `auto_ops`，要求其按职责把异常重新回流 `manager`

但真相面仍然没有变化：

- `manager` 状态仍是 `responding to first message`
- `worker_course` 仍是 `空闲`
- `T-9` 仍是 `待处理`
- `review_course` 的退回卡片仍是 `read=false`

这说明当前更具体的链路问题是：

- **formal review verdict 已生成**
- **但 verdict 没有被 manager 消费成 repair dispatch**

这和前面记录的 `status truth lag` 是同类问题，但更具体：

- 这次不是 status 夸大完成度
- 而是 **消息层、任务层、派工层三者之间没有完成动作转换**

明天修的时候建议单列一个更具体的机制问题：

- `verdict consumed -> dispatch next action`

要点不是“能不能收到消息”，而是：

- manager 读到或未读到 formal verdict 后，如何确保它一定会触发：
  - 派修
  - 改 task truth
  - 改群里状态口径

否则就会出现当前这种情况：

- review 已经给出明确结论
- 但 worker 仍空闲
- task 仍待处理
- manager 仍停留在“等 verdict”叙事

### 11. 这次 Economics 0455 的 repair dispatch 最终是靠“最小直接介入”才重新跑起来

到 `2026-06-21 01:00 CST` 左右，阻塞终于出现了实质性变化：

- `manager` 已正式在群里同步：
  - `Economics 0455 质检不通过（难度分布系统性偏差），已派 worker_course 返修`
- inbox 真相面也出现了新派单：
  - `manager -> worker_course`
  - 明确要求：
    - 26 个 topic 难度分布调整回合规
    - Challenge 题补足 evaluation / analysis 深度
    - 原地修改 `content/igcse-economics-0455/`

这说明链路终于从：

- review 已出 verdict
- 但 manager 不消费

变成了：

- verdict 已被消费
- repair dispatch 已真实发出

但这次恢复并不是纯粹自然发生，而是在连续多轮最小纠偏无效后，进一步做了“最小直接介入”才出现：

- 直接给 `worker_course` 发修复单
- 直接给 `review_course` 预挂复审要求
- 同时把 `manager` 压回只做同步与收口

所以明天修复时，这条经验应保留：

- 当 `formal verdict 已存在 + manager 未消费 + worker 空闲` 连续多轮成立时
- 需要一个明确的升级策略
- 不能无限停留在“继续提醒 manager”

更具体地说，需要系统支持从：

- `soft nudge`

升级到：

- `direct repair bootstrap`

但仍保持边界：

- 不接管全局编排
- 只托起当前卡死的单条 repair / re-review 链路

### 12. Economics 0455 已从“接单口头进度”进入“文件真实改动”阶段，但 task truth 仍明显滞后

到 `2026-06-21 01:05 CST` 左右，Economics 0455 返修又出现了新的积极证据：

- `worker_course` 已在群里明确回报：
  - 已开始返修
  - `6 个并行 agent` 正在处理 26 个 topics
- 文件层也首次出现了真实落盘修改：
  - `content/igcse-economics-0455/qa-question-level/5-1-economic-growth-vs-development-q1.md`
  - `...q2.md`
  - `...q3.md`
  - 一直到 `...q9.md`

这说明当前链路已经从：

- 只说“我开始了”

推进到了：

- **真实文件已开始被改**

但与此同时，任务真相面仍然滞后：

- `T-9` 依然停在 `待处理`

这再次说明当前系统的一个稳定问题不是“没人干活”，而是：

- **task truth 更新明显慢于真实执行**

这类滞后带来的风险是：

- operator 如果只看 `tasks.json`
- 会误以为 Economics 0455 还停在 review 前

而真实上其实已经进入：

- repair in progress

明天修的时候建议把这一层也拆开看：

- `dispatch truth`
- `artifact truth`
- `task truth`

这三层目前并不总是同步推进。

### 13. runtime 真实面已恢复为绿，但群内仍按旧 Hermes 告警叙事推进，说明“运行真相恢复”和“状态口径收敛”是两步

到 `2026-06-21 01:05 CST`：

- repo-local `health` 显示：
  - `router: alive`
  - `task-publish: alive`
  - `watchdog: alive`
- 也就是 runtime 真实面当前是绿的

但群里仍在继续推进一条较旧的 Hermes 修复叙事：

- `auto_ops` 还在按第三轮告警升级
- `manager` 还在同步 `worker_builder` 排查 Python 版本 / pyc 缓存干扰

这说明运行体系又暴露出一个熟悉问题：

- **真实恢复**
- 和
- **口径收敛**

不是同一步完成。

更直白地说：

- 系统可能已经恢复
- 但群消息、状态面、维修叙事还停留在“正在修”

这会带来两类误判：

1. 误以为系统还坏着，于是重复派修
2. 误以为 builder 已经交付了更深层根因，而其实只是口径还没收

因此明天修复应继续强化：

- recovery confirmation gate

也就是：

- 何时从“修复中”切回“已恢复”
- 需要什么 authoritative evidence
- 谁来负责收口旧告警叙事

### 14. Economics 0455 返修已经从单个 topic 扩展到多 topic 的真实文件修改，repair 链路当前是实跑态

到 `2026-06-21 01:10 CST`，Economics 0455 返修已不再是零散试改，而是明显扩展到了多块 syllabus 区域：

- `items/`
  - `1-1-items.md`
  - `2-1-items.md` 到 `2-4-items.md`
  - `3-1-items.md`
  - `5-1-items.md` 到 `5-3-items.md`
  - `6-1-items.md`、`6-2-items.md`
- `qa-question-level/`
  - `1.1`
  - `2.1` 到 `2.4`
  - `3.1`
  - `4.1`
  - `5.1` 到 `5.3`
  - `6.1`、`6.2`
  - 这些 topic 对应的 `q1` 到 `q9` 都已出现最近修改

这说明当前 repair 不是：

- manager 口头说已返修
- worker 只回一句“开始了”

而是已经进入：

- **跨多个 topic 的真实批量改稿阶段**

因此当前更准确的判断应当是：

- `Economics 0455 = repair in progress, artifact truth strong`

而不是此前更弱的：

- `worker_course says started`

### 15. Hermes 第三轮告警已经拿到更明确的根因与修复说明，但仍需留意“修复事实”和“状态面完全收敛”不是同一时刻

这一轮 `worker_builder` 给出了比之前更具体、也更高价值的运行态修复说明：

- 当前结论：
  - `router/watchdog/hermes_monitor` 三 daemon 已恢复运行
  - `eduflow health` 三项全绿
- builder 给出的根因链包括：
  - PATH 中 `$PATH` 未展开，导致 subprocess 找不到 `ps`
  - macOS `ps -o command=` 默认列宽截断，长 Python 路径被截断
  - `expected_cmdline` 与实际 `eduflow` 入口不一致

这比之前那种泛化的“已修复/全绿”要强很多，因为它终于具备了：

- 诊断过程
- 具体根因
- 修复动作
- 当前验证

这属于高价值 gap 收敛。

但仍要注意：

- repo-local `health` 当前为绿
- `worker_builder` / `manager` 状态面也已基本切回待命/恢复
- 可 `auto_ops` 的状态面还可能短时间停留在“继续监测旧告警”

也就是说：

- **运行态真相已经大幅收敛**
- 但 **全体状态面完全收敛** 仍可能慢半拍

这条模式和前面的课程链路是同构的：

- 真相先恢复
- 状态后收敛

因此明天的系统升级最好不要分别零散修，而是统一看成一个更大的系统问题：

- `truth recovered -> state converged`

无论是课程链路还是运行链路，当前都存在这一步经常滞后的问题。

### 16. 题库线已进入主监控，但当前仍停留在 manager 口头派发，worker_qbank 还没有形成正式回执

到 `2026-06-21 01:18 CST`，老板新下的题库任务已经被 manager 口头接住，manager 在日志里明确说：

- `Qbank 题库搭建和验证方案已派 worker_qbank`

但当前 repo-local 真相面仍显示一个典型 gap：

- `manager dispatch truth = yes`
- `worker_qbank execution truth = not yet externally visible`

也就是：

- manager 已经开始按“已派”口径同步
- 但 `worker_qbank` 还没有就这条新题库任务形成正式状态包、阶段性交付、或任何可核验的首轮证据

这条线的主要风险目前不是“技术方案错误”，而是更基础的：

- **任务已派，但没有及时形成 worker 侧外显回执**

因此今晚对题库线的正确盯法不是先判断方案优劣，而是先压实最小执行闭环：

- worker_qbank 先回最小状态包
- 明确本轮覆盖范围
- 明确先交哪份证据
- 明确第一拍 ETA

我已对 `manager` 和 `worker_qbank` 都做了最小纠偏，要求不要继续停在“已派/待命”口径。

这条也再次印证了今晚一个重复出现的系统问题：

- **dispatch happened != execution became externally visible**

明天统一升级时，这应和课程线里的 `verdict issued but not consumed`、运行线里的 `truth recovered but state not converged` 一起处理，而不是分散看成三个孤立问题。

### 17. agent 消息处理口存在系统性滞后，不只是偶发漏回，已成为明天应优先维修的主 gap

到 `2026-06-21 01:20 CST`，今晚已累计出现多次同构症状，基本可以判断：

- 这不是单个 agent 偶发慢回复
- 而是 **消息派发 → agent 消费 → 外显回执 → 状态面收敛** 这一整段处理口存在系统性滞后

当前已拿到的硬证据至少有 4 组：

1. `review_course verdict issued but manager not consumed in time`
- Economics 0455 的正式不通过 verdict 已在 `log_1781974201554_20f4f0ed9b` / `msg_1781974248139_9543c33cf6` 发出
- 但 manager 一度长期停在“等 verdict”，导致 worker_course 没有及时收到返修任务

2. `manager dispatched but worker externalization lagged`
- 老板题库任务已被 manager 派给 `worker_qbank`（`msg_1781974861221_a19d4b6431`）
- 但随后一段时间内没有 worker_qbank 的最小状态包，出现“已派但外部看不到执行”的空窗

3. `message unread/read truth and status truth diverged`
- `review_course` 在 `msg_1781975881809` 收到 Economics 0455 复检任务后仍显示旧状态：`待命 / 待复检`
- `worker_qbank` 在收到 codex + manager 连续催办后，直到真正产出 `msg_1781975962292_6a755f2ef3` 才完成外显
- 说明 inbox 真相、agent 实际动作、status 面并不同步

4. `historical root cause already appeared once, but tonight still有更广义复发`
- 之前 `worker_course` 已明确修过一次消息口 bug：高优消息被 auto-ack，导致 agent 跳过 inbox 消费
- 今晚虽然不是同一个 bug 复现，但更广义的“消息已到 -> 消费/外显/收口慢半拍”仍然持续存在

因此，明天这块不应只按“manager 提示词优化”去修，而应按更具体的消息处理链路拆修：

- message delivery 是否成功
- read / unread / ack 语义是否可靠
- agent 消费消息后是否强制产生最小状态包
- manager 是否必须消费正式 verdict / 完工消息，而不能长期停在旧口径
- status.json / tasks.json / inbox / logs 的 truth sync 是否需要统一收敛机制

今晚我会继续把这块当主监控项盯住；明天则建议把它升为 **P1 系统维修项**。

### 18. 消息一多就卡：不是单条消息漏处理，而是 backlog 下的消费、外显、状态同步一起变慢

到 `2026-06-21 01:31 CST`，这一点已经可以单独列为明天 P1，而不是挂在“manager 没及时看见”下面。

今晚新出现的证据：

- `worker_qbank` 实际已完成题库验证，并在 `msg_1781975962292_6a755f2ef3` 回给 manager：
  - 扫描 5 学科 2086 题
  - 产出 `scripts/qbank_verify.py`
  - 产出 `content/qbank-unified-manifest.csv`
  - 产出 `content/qbank-verification-report.md`
- 但用户随后仍需要问：
  - `Qbank有在行动吗？`
  - `Qbank它的产出为啥没外显汇报`
- manager 后续自己承认：
  - `之前未外显汇报是我的失职——员工回报进了我的内部 inbox，我没有及时消费后同步到群里`

这说明问题不止是“消息没送到”。

更准确的链路问题是：

- 消息能进 inbox
- worker 也可能已经执行完
- 但 manager / 目标 agent 在消息多时没有稳定执行：
  - consume
  - acknowledge
  - summarize externally
  - update status/task

也就是系统在轻负载下能跑，在消息密集、告警密集、多线并发时会出现处理口拥堵。

明天维修建议：

- 给 manager 加一个强制 `inbox drain before report` 机制：每次对外状态同步前，必须先消费未处理的高优消息和 worker 完工消息。
- 给 worker 回报加 `externalization SLA`：高优任务接单后 N 分钟内必须有最小状态包；完工后必须有 `say` + send manager 两条证据。
- 给 inbox 增加 backlog 指标：未读数、pending ack 数、最老未处理消息年龄、同一来源连续消息数。
- 对 `ack_state=pending` 但 `read=true` 的消息做单独告警，因为这类消息最容易造成“看似已读，实则未进入管理闭环”。
- 当消息密集时，manager 应使用固定收口顺序：
  - drain inbox
  - consume formal verdict / worker result
  - sync task/status
  - public report

### 19. workflow 能力存在，但今晚更多是口头使用，没有真正挂到 task/flow 上

系统当前确实有 active workflows：

- `igcse-subject-launch`
- `igcse-item-level-prototype`
- `realrun-to-workflow`

并且 `igcse-subject-launch` 的 gate 正好覆盖今晚暴露的问题：

- `dispatch_acceptance_gate`
- `review_handoff_gate`
- `file_evidence_gate`
- `quality_gate`
- `artifact_standard_gate`
- `repair_acceptance_contract`
- `stale_state_reconciliation`

它的 closeout block 条件也正中 tonight gap：

- PASS 只有 summary-level、缺 file evidence 时不能收口
- minor repair 未回 review 时不能收口
- manager 有未读高优质量指令时不能收口
- artifact truth 与 status summary 不一致时不能收口

但实际 Economics 0455 这轮暴露了一个关键落差：

- manager 口头说了 `Workflow：topic优化 → topic-outline → QA seed → review_course → manager 基于 verdict 收口`
- 但 `T-9` 仍是普通 task，状态仍停在 `待处理`
- task list 里看不到 `workflow_id=igcse-subject-launch`
- 因此 workflow 的 `stale_state_reconciliation` 没有真正把 `T-9 待处理` 这种状态滞后挡下来

结论：

- workflow 不是没有。
- workflow 也不是完全没被提到。
- 真正问题是：**workflow 没有被程序化挂载到执行任务，因此只剩口头约束。**

明天维修建议：

- 下一学科开始时必须用 `task dispatch ... --workflow igcse-subject-launch` 或等价 flow-task 创建，而不是普通 send 派活。
- manager closeout 前必须跑 `workflow gates igcse-subject-launch` / `workflow closeout igcse-subject-launch` 的等价检查。
- auto_ops 盯盘要新增一项：如果 manager 只口头声明 workflow，但 task/flow 无 `workflow_id`，应立即回流纠偏。
- 对所有 IGCSE 学科主线任务，task/status/log 应能显示 workflow_id、当前 gate、下一 gate，而不是只靠聊天叙述。

### 20. 已先把下一学科 workflow 正式挂上，作为今晚临时修正

根据老板要求，已先把下一学科从“口头 workflow”切到正式 task/flow 挂载。

执行结果：

- 新建任务：`T-10`
- 标题：`IGCSE Business Studies 0450 ready-for-qbank 补齐与复核闭环`
- assignee：`worker_course`
- stage：`curriculum`
- owner：`worker_course`
- workflow_id：`igcse-subject-launch`
- status：`assigned`

验证证据：

- `eduflowteam task dispatch ... --workflow igcse-subject-launch` 返回：
  - `dispatched T-10 ... workflow=igcse-subject-launch`
- `eduflowteam task get T-10` 显示：
  - `workflow_id: igcse-subject-launch`
- `.eduflow-team-state/tasks.json` 中 `T-10` 已写入：
  - `"workflow_id": "igcse-subject-launch"`
- `worker_course` 已自动外显接单：
  - `log_1781976848969_8ebf5a2c9b`
  - `课程研发任务已接单：IGCSE Business Studies 0450 ready-for-qbank 补齐与复核闭环（T-10）`

这说明正式 workflow task 的派发比单纯 send 消息更有结构化优势：

- task truth 里有 workflow_id
- worker 接单有自动外显
- 后续可以用 workflow gates/closeout 约束 review 与 manager 收口

后续仍需继续观察：

- `T-10` 是否进入 `in_progress`
- 是否自动走 review handoff gate
- closeout 前是否真的跑 workflow gate
- task/status/log 三个真相面是否同步

### 21. worker_course 完成事件重复外显，说明缺少同窗去重与节流

Business Studies 0450 的 `T-10` workflow 正式挂上后，worker_course 的执行链路能跑通，但完成阶段出现了外显过量：

- `log_1781977126672_8d5146ffce`
  - `Business Studies 0450 T-10 完工 ✅ ... 已送 review_course 审核。`
- `log_1781977127951_96eab32ebc`
  - `business-studies-0450-complete`
- `log_1781977181526_8c52234e91`
  - `课程研发任务已完成并交给 manager...`
- `log_1781977181526_3ce31b4743`
  - 与上一条同毫秒、同内容重复
- `log_1781977182050_d2e66ccf68`
  - 约 0.5 秒后再次重复同内容

这不是课程内容质量问题，而是消息外显口问题：

- 同一完成事件被 `say` / `task_completed` / 自动阶段外显多路触发
- 缺少基于 `task_id + stage + normalized_content + time_window` 的去重
- worker 自报、task flow 状态、manager 同步之间没有节流策略，消息一多时会显得“每个 agent 都在刷存在感”

今晚临时处理：

- 已保留此现象作为 P1 gap，不在实跑中做高风险去重逻辑热改。
- 已将 `worker_course` 卡片颜色从绿色改为紫色，先和 `review_course` 的绿色卡片区分开，降低密集消息时的视觉混淆。

明天维修建议：

- 在 `eduflow say` 或 task event scanner 外显前增加短窗幂等键。
- 对完成类事件设置更严格策略：同一 `task_id` 的 `completed/submitted_for_review` 在 60-120 秒内只允许一条用户可见卡片，其余只写 local log。
- manager 消费 worker 完成消息后，只补充 verdict/next gate，不重复播报 worker 原话。

### 22. MINOR verdict 后 task truth 没有自动同步，且标准方向一度分叉

Business Studies 0450 的 `T-10` 已经正式挂上 `workflow_id=igcse-subject-launch`，但 review 返回 `MINOR` 后又暴露了一个新的 truth-sync gap。

现场事实：

- `review_course` 已在 `log_1781977335331_894f0b7a5e` 给出正式 verdict：`MINOR 修改`。
- 复核结论不是内容失败，而是标准待统一：
  - 内容准确、结构完整、QA/items 一致。
  - 主要问题是 12-item 难度分布不统一，以及是否与 Economics 9-item 标准对齐。
- manager 随后两次外显方向出现短暂分叉：
  - 先说已派 worker_course 修补。
  - worker_course 先接到 `25 topics 从 12-item 调整为 9-item 标准（F:2|S:4|C:3）`。
  - manager 后来改成 `保持 12 items/topic，统一 F:3|S:5|C:4`。
  - worker_course 最新已接到 12-item 方向并开始处理。

问题点：

- `eduflowteam task get T-10` 在 review 已出 `MINOR` 后仍显示：
  - `status=submitted_for_review`
  - `verdict=pending`
  - `latest_turn_summary=Manager assigned reviewer review_course`
- `task scan-anomalies` 因此误判为 `wait_for_review_approval`，继续建议等 review_course verdict。
- 实际正确状态应该是：review 已完成一轮，进入 manager direction / worker repair / re-review gate，而不是继续等待 review。

今晚临时修正：

- 已用 task flow 语义将 `T-10` 从 pending review 修正为：
  - `status=blocked`
  - `verdict=manager_action`
  - `manager_action_type=choose_direction`
  - `review_reason=missing_owner_decision`
- 已同步 `worker_course` status 为：
  - `Business Studies 0450 按 manager 最新方向保持 12 items/topic，统一难度分布至 F:3|S:5|C:4，完成后重送 review_course`

明天维修建议：

- review_course 发出 `MINOR / changes requested / manager direction needed` 后，应自动或半自动写回 task truth，不能只停在聊天日志。
- `MINOR` 应有一等状态，或映射为 `manager_action` / `repair_requested`，但不能继续显示 `verdict=pending`。
- manager 对标准方向的最终拍板应成为 task 的单一事实源，worker/status/scan-anomalies 都应读取同一个字段，避免 9-item 与 12-item 两套标准同时出现。
- `scan-anomalies` 要能识别“已有 MINOR verdict，但等待返修/重审”，不要误报成“尚未 review approved，请 review_course 先完成 verdict”。

### 23. 卡片颜色分工已临时调整，但 pink 需要确认飞书端实际渲染

为降低今晚高消息量下的视觉混淆，已调整 agent 卡片颜色：

- `manager`: blue
- `worker_course`: purple
- `review_course`: green
- `auto_ops`: pink
- `worker_builder`: orange
- `anna`: yellow
- `worker_qbank`: purple（暂未改，后续可单独区分）

本地验证：

- `_channel_card_identity` 对上述 agent 返回预期颜色。
- `simple_card(..., color=...)` header template 不再把 `pink` 回退为 `blue`。
- `tests/unit/test_commands_say.py` 通过。

风险：

- 代码原注释只写明已测试色为 `blue/green/red/yellow/grey/purple/orange/turquoise`，今晚新增 `pink` 虽然本地 schema 不回退，但还需要在飞书实际客户端确认是否稳定渲染。

### 24. scan-anomalies 对 manager_action / repair-in-progress 的任务仍误报为等待 review

在将 `T-10` 从 `submitted_for_review + verdict=pending` 修正为 `blocked + verdict=manager_action + manager_action_type=choose_direction` 后，`task review-queue --reviewer review_course` 已正确显示：

- `no tasks awaiting review`

但 `task scan-anomalies` 仍继续报：

- `subject_closeout_blocked task=T-10 status=blocked`
- `recommended_action: wait_for_review_approval`
- `suggested_brief=...尚未 review approved，请 review_course 先完成 verdict。`

这条建议在当前现场是误导性的：

- review_course 已完成首轮 review，并给出 `MINOR`。
- manager 已选择修复方向：保留 12 items/topic，统一 `F:3|S:5|C:4`。
- worker_course 正在返修，下一步应等 worker 返修完成后重新送审，而不是催 review_course 再出一次 verdict。

明天维修建议：

- `scan-anomalies` 需要把 `verdict=manager_action` / `needs_manager_action=true` / `manager_action_type=choose_direction` 作为独立状态处理。
- 对这类任务，推荐动作应是 `wait_for_worker_repair` 或 `manager_direction_selected_wait_repair`，而不是 `wait_for_review_approval`。
- closeout gate 可以继续显示未通过，但 action packet 不应派给 review_course，避免 review 线被错误催办。

### 25. Business Studies 返修中出现短暂 artifact 中间态：文件数低于目标且命名混用

在 worker_course 执行 Business Studies 0450 难度分布返修时，文件层面已出现真实修改，说明 agent 确实在工作，不是卡死。

只读抽查发现：

- `qa-question-level` 当前约 285 个 QA 文件，低于目标 `25 topics × 12 = 300`。
- `items` 仍为 25 个 topic 文件。
- 一部分 topic 已达到 `F:3|S:5|C:4`。
- 仍有若干 topic 处在 `F:2|S:4|C:3` 的 9-item 状态。
- 文件命名存在混用：
  - 早期 `1-1-business-activity-and-adding-value-q01.md`
  - 后续 `2-1-organisation-and-management-q-2.1-01.md`

当前判断：

- 这是返修进行中的 artifact 中间态，不能提前送审或 closeout。
- 若 manager 只看“已有修改”或“部分 topic 合规”，容易误判为完成。

明天维修建议：

- workflow gate 应区分 `repair_in_progress` 与 `repair_complete`。
- 返修完成前应要求 worker_course 给出程序化计数证据：25 topics、300 QA、每 topic 12 QA、每 topic `F:3|S:5|C:4`、items/manifest 同步。
- review handoff gate 应阻止低于目标数量或命名混用未解释的产物进入正式 review。

### 26. 返修 artifact 已达复检条件，但 agent/status 没有自动送审

继续监控 Business Studies 0450 返修时，文件层面已经达到复检条件：

- `qa-question-level`: 300 个 QA 文件。
- topic 数：25。
- 每个 topic：12 QA。
- 难度分布：25/25 topic 均为 `F:3|S:5|C:4`。
- 未识别文件：0。

但当时运行态仍显示：

- `T-10`: `blocked + verdict=manager_action`
- `worker_course`: 仍显示返修中
- `review_queue`: 空

这说明 artifact truth 已经完成，但 task/status truth 没有自动推进到 re-review gate。

今晚临时修正：

- 已将 `T-10` 重新推进为 `in_progress -> submitted_for_review`。
- 已重新指定 reviewer：`review_course`。
- 已同步 `worker_course` status 为返修完成并重送复检。
- 已同步 `review_course` status 为进行返修复检。

明天维修建议：

- worker 完成返修后应自动触发 `submit-review`，或至少由 task scanner 根据 artifact verifier 结果提示 manager/worker 送审。
- workflow 应有 `repair_complete_ready_for_re_review` gate，避免 artifact truth 与 task truth 脱节。

### 27. router flapping 进一步恶化为多实例竞争

复检等待期间，health 一度显示 `router: no pid file`，但进程表同时看到两个 router：

- 一个来自 `/Volumes/Halobster/Codex相关/EduFlow-V3/.venv/bin/eduflow router`
- 一个来自 `/opt/homebrew/bin/eduflow router`

router.log 同时出现：

- `another router already running`
- `catching up 6 missed message(s)`
- `router exited: handled=0 dropped=16`
- `no events for 135s ... exiting for respawn`

这说明问题已经不只是 idle threshold 过低，而是：

- 多个 eduflow 入口/版本可能同时被 watchdog 或手动命令拉起。
- pid file 与实际进程不一致。
- health 的 no-pid 与实际 running 进程之间存在错位。

今晚临时处理：

- 已尝试用 `eduflowteam down router && eduflowteam up router` 做最小收敛，目标是保留单一 router，保障 review verdict 能进入群链路。

明天维修建议：

- 统一 router 启动入口，避免 `EduFlow-V3/.venv/bin/eduflow` 与 `/opt/homebrew/bin/eduflow` 同时参与。
- pid file 应记录并校验启动命令来源，发现命令来源不同应明确报 `router_entrypoint_drift`。
- watchdog respawn 前应先清理同 chat_id 的旧 router 进程，避免双 router 竞争。

### 28. `eduflowteam down router` 命令语义不安全：实际执行 team down

为收敛 router 多实例竞争，尝试执行：

- `eduflowteam down router`

实际结果不是只停止 router，而是：

- 停止 watchdog
- 停止 task-publish
- kill tmux session `EduFlowTeam`
- 输出 `team down`

随后执行 `eduflowteam up router` 时又恢复了整个 team：

- 重新创建 tmux session
- 重新 spawn 所有 agent
- router/task-publish/watchdog 全绿
- manager 回到 `manager_primary`，runtime drift warning 消失

风险：

- 操作者以为是局部重启 router，实际会短暂中断全部 agent pane。
- 如果发生在关键 review verdict 输出期间，可能打断现场上下文。

明天维修建议：

- `down router` / `up router` 应明确只操作 daemon，或者命令直接拒绝并提示使用 `daemon restart router`。
- 对会 kill tmux session 的命令，CLI 输出和 help 必须显式写 `team down`，不能接受 `router` 参数后仍执行全局 down。
- 需要补一个安全命令：`eduflowteam daemon restart router --dedupe`，用于清理重复 router 进程但不碰 agent panes。

### 29. 已达标返修后被旧 minor 指令拉回“等待 worker 修复”

Business Studies 0450 返修文件已经达到：

- 25 topics
- 300 QA
- 每 topic 12 QA
- 每 topic `F:3|S:5|C:4`
- `T-10` 已重新进入 `submitted_for_review`

但重启/恢复后，状态口径又回退：

- manager: `等 worker_course 修复 minor`
- review_course: `待 worker_course 修复送审后复检`
- auto_ops: `T-10 等 worker_course 修 minor`
- scan-anomalies: 发现一条新的高优消息 `msg_1781978853003_41abd3e6c9`，manager 再次要求 worker_course 修 minor；worker_course 已读但无 ACK。

这是 stale instruction / stale context 回流：

- artifact truth 已完成。
- task truth 已提交 review。
- 但 manager 旧指令和 agent/status truth 把链路重新拉回“待 worker 修”。

今晚处理原则：

- 不让 review_course 误等 worker。
- 给 manager/review_course 明确当前真相：现在应该由 review_course 对已达标返修产物出正式 verdict。

明天维修建议：

- 对 manager 下发修复指令前，应先查 task/artifact verifier，若 artifact 已达标且 task 已 submitted_for_review，应阻止旧修复指令再次发送。
- 高优 inbox 的 stale 指令需要可撤销/可 supersede，避免 read-without-ack 被 scanner 当成当前阻塞。
- status sync 应以 task truth + artifact verifier 为准，不应被旧聊天指令覆盖。

### 30. manager 在收到纠偏后仍回退到错误标准：12-item 达标产物被旧 9-item 指令威胁

在 codex 已向 manager/review_course 纠偏后，review_course 已 ACK 当前真相：

- Business Studies 0450 返修产物已达复检条件。
- `T-10` 已重新 `submitted_for_review`。

但 manager 随后又发出错误状态：

- `worker_course 正在修复 ... 将 25 topics 的 item 从 12→9 对齐 Economics 标准，难度分布调为 F:2|S:4|C:3`

这与当前真实产物和最终方向冲突：

- 当前文件已经是 25 topics / 300 QA / 每 topic 12 QA / 全部 `F:3|S:5|C:4`。
- 当前 task 已在 review gate，不应再派 worker_course 继续改 9-item。

今晚临时处理：

- 已再次向 manager 纠偏：不要再说/派 12→9，等待 review_course verdict。
- 已向 worker_course 发高优停止指令：不要执行旧 9-item 指令，保持 12-item 达标产物，等待 review。

明天维修建议：

- manager 的状态生成必须读取 task truth + artifact verifier，而不是复述旧 inbox 或旧记忆。
- 对已 supersede 的旧指令应有明确撤销状态，否则 worker 可能把已达标产物改坏。
- 引入“final standard decision”字段，并让 manager/worker/review/status 全部引用同一字段。

### 32. review_course 已正式 PASS，但 T-10 task truth 仍停在 pending，需要 manager 消费 verdict 并 closeout

触发原因：

- `review_course` 已在群日志给出正式 `PASS — 可发布`，但 `T-10` 仍显示 `submitted_for_review / verdict=pending`。
- 如果继续等待，Business Studies 0450 会卡在 review gate，后续 Accounting / qbank 链条也容易被旧状态拖住。
- 这是用户要求重点盯的“agent 消息处理口 / 消息多了状态同步卡住”问题，适合最小指引 manager 自己收口，而不是 Codex 直接替 task 改状态。

现场证据：

- 日志 `log_1781979355733_8556b1dc5f`：`review_course` 给出 `T-10 Business Studies 0450 复检结果：PASS`。
- 文件复验：`content/igcse-business-studies-0450/qa-question-level` 共 300 个 QA 文件。
- 文件复验：`content/igcse-business-studies-0450/items` 共 25 个 items 文件，`manifest.md` 存在。
- 分布复验：25/25 topic 均为 `Foundation:3 / Standard:5 / Challenge:4`，坏 topic 为 0。
- `./scripts/eduflowteam task get T-10` 仍显示 `verdict: pending`。

介入动作：

- 已向 manager 发送最小指引消息 `msg_1781979530791_617d8969e2`：请消费 review_course PASS，执行 task review approve + manager closeout；不要再派 worker_course 做 9-item 或额外返修。
- 不直接修改 task truth，不绕过 manager，让群内生态完成 closeout。

临时结果：

- 待 manager 消费后复查 `T-10` 是否进入 ready-for-qbank / closeout 状态。

明天修复建议：

- router/task-publish 应能从 `review_course` 的结构化 PASS 消息自动推进 task verdict，或至少生成 manager action。
- manager 在 review PASS 后应有自动 closeout checklist：artifact verifier -> task approve -> manager-closeout -> 下一学科。
- `review PASS` 与 `task verdict pending` 超过阈值时，auto_ops 应主动报警，而不是只汇报旧 minor 状态。

### 33. Qbank 有首版产物但反馈不可见，且验证脚本未纳入新闭环学科

触发原因：

- 用户反馈“Qbank 的情况看不到反馈”。
- 现场检查发现 worker_qbank 已在 01:14 左右交过首版状态包，但后续没有持续外显。
- manager 只同步过一次 qbank 进展，之后 T-10 课程链路推进时 qbank 状态没有继续被挂在可见任务上。
- `worker_qbank` 当前 status 为“空闲 / 无待办”，但报告里仍有 39 个同层重复、manifest 问题和导入前修复项，说明 qbank 线没有实际收口。

现场证据：

- `log_1781976075044_34d9451e23`：worker_qbank 汇报已扫描 5 学科 2086 题，交付 `scripts/qbank_verify.py`、`content/qbank-unified-manifest.csv`、`content/qbank-verification-report.md`。
- `log_1781976281317_2fd5e8e0ac`：manager 承认“之前未外显汇报是我的失职”，并说下一步派 worker_qbank 去重 + manifest 补全。
- `status.json` 当前显示 `worker_qbank`：`空闲 / 无待办，等待派单`。
- `content/qbank-verification-report.md` 仍显示：39 个同层重复、40 个 manifest 问题、3 学科缺 manifest、Physics manifest 不完整。
- 当前重跑 `python3 scripts/qbank_verify.py --content-dir content --json` 仍只扫描 5 个硬编码学科：Math / Physics / Chemistry / Biology / Accounting。
- `scripts/qbank_verify.py` 第 23-29 行 `SUBJECTS` 未包含 `igcse-economics-0455` 和 `igcse-business-studies-0450`，因此新闭环学科不会自动进入题库验证。

介入动作：

- 准备向 manager 发送最小指引：把 qbank 重新挂成可见任务，派 worker_qbank 产出新版状态包。
- 指引重点：补纳 Economics 0455 / Business Studies 0450；更新报告；说明 39 duplicate、manifest、schema warning 的处理状态；每 15 分钟至少外显一次状态。
- 暂不直接改 qbank 脚本，优先让 manager -> worker_qbank 链条自修。

临时结果：

- manager 已消费 Codex 指令并外显：`log_1781979945730_1326c90773`，qbank 线已重新挂起，已派 worker_qbank 纳入 Economics 0455 / Business Studies 0450，更新 manifest/report。
- worker_qbank 已接单并外显：`log_1781979955008_c5779c3a82`，正在扩展验证范围并更新 manifest + report。
- `status.json` 已从 `worker_qbank: 空闲 / 无待办` 变为 `worker_qbank: 进行中 / qbank验证线外显：扩展学科+更新manifest+report`。
- 当前先观察 worker_qbank 产出新版状态包，不继续加压。

明天修复建议：

- `qbank_verify.py` 不应硬编码 SUBJECTS，应自动发现 `content/igcse-*-<code>` 学科目录，或读取 subject inventory。
- qbank 任务应该进入 task tracker，有明确状态：`scan -> issue-fix -> reverify -> ready-for-import`。
- manager 对 worker_qbank 的内部回报必须自动外显摘要，避免“worker 已做但老板看不到”。
- qbank verifier 对 JSON 模式应支持 summary-only，避免 5k+ 行输出淹没消息处理口。

### 34. Qbank v2 已交付，但 manager 等待是否立即去重，需要避免误伤 QA 原文

触发原因：

- worker_qbank 已完成 qbank v2 并外显：7 学科 / 3154 题，新增 Economics 0455 与 Business Studies 0450。
- manager 随后询问“是否立即派去重批次”。
- 去重会触碰 `items/` 层产物，属于可能影响导入数据的修复动作；如果直接让 worker 修改，可能为了清 39 个 duplicate 误删 QA 原文或破坏 cross-layer 对照。

现场证据：

- `log_1781980102832_23e6bba03b`：worker_qbank 任务完成，7 学科 3154 题，新增 Economics 468 + Business Studies 600。
- `log_1781980103966_12fb4a4eb2`：worker_qbank 群内外显 v2 完工，新增两科零重复零 schema 违规。
- `log_1781980143553_28db580319`：manager 汇报 v2，并询问是否立即派去重批次。
- `content/qbank-verification-report.md` 已更新到 v2：7 学科、3154 题、39 个同层重复、1058 个跨层重叠、Schema 违规 0、Manifest 问题 42。
- 本地重跑 `python3 scripts/qbank_verify.py --content-dir content --json`：subjects 7 / total 3154 / errors 39 / warnings 47 / info 1058，退出码 1 来自旧 duplicate error。

介入动作：

- 已向 manager 发送保守指引消息 `msg_1781980402532_e08eaa44d6`：可以开 qbank 去重批次，但第一步只能做 dry-run + diff 方案，不直接改 QA 原文。
- 要求去重范围限定在已知重复来源：Physics round2 items、Chemistry s2 items、Biology final-push items、Accounting qa/拆分冲突。
- 要求先输出将删除/保留的 Q-ID、文件路径、理由，再由 review/manager 确认后执行。

临时结果：

- 待 manager 消费指引后复查是否派发为“dry-run 去重方案”而非直接 destructive edit。

明天修复建议：

- `qbank_verify.py` 应区分 blocking duplicate 与 expected cross-layer overlap，输出 compact summary，避免 JSON 全量 5k+ 行导致消息口卡顿。
- 去重流程应产品化为 `qbank dedupe plan` 和 `qbank dedupe apply` 两阶段，默认不改 QA 原文。
- qbank task tracker 应有单独 task id，避免混在 manager/status 文案里。

### 35. Qbank 去重 dry-run 方案已产出，但 apply 前缺少复核 gate

触发原因：

- worker_qbank 已按要求产出 `content/qbank-dedup-dryrun-plan.md`。
- manager 正在询问是否 `apply`。
- 方案虽然完整，但它由执行方 worker_qbank 自己生成；真正改动会删除 10 个文件中的 39 个 Question block，需要一个独立复核 gate，避免“自写方案自执行”。

现场证据：

- `log_1781980573134_e1c57815bf`：worker_qbank 外显 dry-run 去重方案已交付，覆盖 39 个 Q-ID，改动 10 个文件，等待 review 确认。
- `log_1781980606374_068149e3ca`：manager 汇报方案并询问是否 apply 或先让 review_course 复核。
- `content/qbank-dedup-dryrun-plan.md`：191 行，列出 Physics 27 / Chemistry 9 / Biology 1 / Accounting 2，策略为不动 `qa-question-level`，移除重复来源文件中的 block。
- 当前文件时间显示：`content/qbank-unified-manifest.csv`、`content/qbank-verification-report.md`、`scripts/qbank_verify.py` 无新 apply 后改动；说明 dry-run 尚未破坏性执行。

介入动作：

- 已向 manager 发送指引消息 `msg_1781980711256_860818f74d`：先安排 review_course 或 manager 自己做方案复核，不要立即 apply。
- 复核重点：抽查 Physics 3-way 冲突、Accounting 合并/拆分版保留策略、Chemistry s2 的 topic 归属；确认 `qa-question-level` 作为权威源不受影响。

临时结果：

- 待 manager 消费后观察是否进入 `review dry-run plan`，而不是直接 apply。

明天修复建议：

- qbank 去重应有强制状态机：`dry-run-plan -> independent-review -> apply -> reverify`。
- 对任何删除 Question block 的动作，CLI 应要求 `--confirm-reviewed` 或引用 review verdict id。
- 去重方案应输出机器可读 JSON，方便 review_course 自动抽样和 verify。

### 36. manager 外显“已派 review_course”，但 review_course inbox 无消息

触发原因：

- manager 已在群里说 qbank dedup review gate 已设立，并已派 review_course 独立复核。
- 但随后检查 `review_course` 状态仍为待命，日志没有 ACK，inbox 也显示无未读。
- 这说明存在“manager 外显派单”与“实际消息投递”不一致，若不纠偏，qbank dedup 会停在假 review gate。

现场证据：

- `log_1781980746846_11c011278b`：manager 外显“已派 review_course 独立复核 dedup 方案”。
- `jq status.json`：`review_course.status=待命`，task 仍是上一条 `T-10 Business Studies 0450 复检 PASS 已提交`。
- `./scripts/eduflowteam inbox review_course`：显示 `review_course: no unread messages`。
- `manager` 和 `worker_qbank` inbox 也为空，说明没有待处理回执链。

介入动作：

- 已向 manager 发送最小纠偏消息 `msg_1781980955381_637a42363f`：请实际投递 review_course 复核任务，要求 ACK + PASS/MINOR/REJECT verdict，不要只外显“已派”。

临时结果：

- 待 manager 消费后复查 review_course 是否出现 ACK 或 inbox 任务。

明天修复建议：

- manager 在说“已派 X”之前应验证 inbox message id 或 task assignment id 已生成。
- task/status 面应区分 `announced` 与 `delivered`，不能把口头外显当作投递成功。
- auto_ops 可监控“manager says 已派 review_course，但 review_course inbox/status/log 在 N 分钟内无 ACK”的假派单 gap。

### 37. Qbank dry-run 方案被 review gate 拦下：Q-ID 冲突被误判为内容重复

触发原因：

- review_course 已完成 qbank dedup 方案独立复核， verdict 为 FAIL。
- 该 FAIL 不是流程失败，而是 review gate 成功拦截了高风险误删：worker_qbank 的方案把 Q-ID 冲突当成内容重复。
- 如果直接 apply 原方案，会删除大量独立题目，违背题库建设目标。

现场证据：

- `log_1781981136767_5ac20a321b`：review_course 给出 `QBank 去重 dry-run 方案复核结果：FAIL`。
- Physics 0625：review_course 抽查全部 27 个 Q-ID，判定 27/27 均非重复，而是不同内容的独立题目；原方案会永久丢失 26 个独立题目。
- Chemistry 0620：只有 B1 的 4 个完全相同副本安全可删；B2 中 Q-6.3-02/03/04/05 是不同题目，不应删除。
- Biology 0610：Q-4.1-08 两处内容不同，不应删除。
- Accounting 0452：Q-5.5-01 / Q-5.6-01 合并版与拆分版近似，去重策略基本合理。
- `log_1781981156542_efb8b7ff8f`：review_course 外显核心结论：应改为内容全文比对 + Q-ID 冲突重编号。

介入动作：

- 已向 manager 发送方向纠偏消息 `msg_1781981267808_6a71230b47`：禁止 apply 原 dry-run 方案；派 worker_qbank 生成 v3 修复方案，核心为内容比对、真重复删除、非重复 Q-ID 冲突重编号。

临时结果：

- review_course inbox 已清空，status 更新为 `QBank 去重复核 FAIL 已提交`。
- worker_qbank 尚未收到新修复任务，仍显示等待 review 确认。

明天修复建议：

- `qbank_verify.py` 的 duplicate error 不能只基于 `(subject, layer, Q-ID)`，应拆成两类：
  - `true_duplicate`：Q-ID 相同且 Question+Answer 高相似/相同，可删除副本。
  - `id_collision`：Q-ID 相同但内容不同，应重编号并保留。
- qbank manifest 应支持 stable internal id，不能仅依赖局部 Q-ID。
- 去重工具必须先做内容 hash / normalized text similarity，再决定 delete vs renumber。

### 39. Qbank v3 方案已产出，但“已送 review_course”假派单复发

触发原因：

- worker_qbank 已产出 v3 方案：normalized Q+A 比对，6 个 true duplicate 删除，33 个 id collision 重编号。
- manager 外显“v3 去重方案已送审，已送 review_course 复检”。
- 但复查 `review_course` inbox 仍为空，status 未更新，说明第 36 条的假派单问题复发。

现场证据：

- `log_1781981534242_c174b51e84`：worker_qbank 外显 v3 已交付，产物 `content/qbank-dedup-dryrun-plan-v3.md`。
- `log_1781981544363_8eb93e340e`：worker_qbank task_completed：6 true_dup + 33 id_collision，38 次重编号 + 6 删除，零丢失。
- `log_1781981597768_88ab6ddc16`：manager 外显“v3 去重方案已送 review_course 复检”。
- `./scripts/eduflowteam inbox review_course`：仍显示 `review_course: no unread messages`。
- `status.json`：review_course 仍停留在上一轮 `QBank 去重复核 FAIL 已提交`。

介入动作：

- 已向 manager 发送纠偏消息 `msg_1781981682512_114a95b19e`：实际投递 v3 复核任务到 review_course，要求给出 message id / ACK / PASS-MINOR-REJECT，而不是口头“已送审”。

临时结果：

- 待 manager 消费后复查 review_course inbox 是否出现 v3 复核消息。

明天修复建议：

- “派 review_course”应走统一 API 并返回 delivery id；没有 delivery id 不允许 manager 外显“已派”。
- 对同一类假派单已复发，明天应优先修 manager dispatch 逻辑和 status sync。

### 41. Qbank v3 review 为 MINOR：方案正确但 map 方向仍需修正，不能直接 apply

触发原因：

- review_course 已复核 `content/qbank-dedup-dryrun-plan-v3.md`，给出 `MINOR 修改`。
- 它确认 v3 方法论正确，但发现 12 个 keep/renumber 方向反转，以及 Q-6.3-01 同时出现在 true_duplicate 和 id_collision。
- 如果 manager 误把 MINOR 当 PASS 直接 apply，仍会产生错误重编号/删除。

现场证据：

- `log_1781981831439_1dfceb1b92`：review_course verdict `MINOR 修改（修正 keep/renumber 方向后通过）`。
- 需修正项：
  - Physics 5.x 7 个 Q-ID：应保留 canonical `5-X-items.md`，round2 重编号。
  - Chemistry 6.3 5 个 Q-ID：应保留 `6-3-items.md`，`5-2-s2` 重编号。
  - `Q-6.3-01` 不应同时在 true_duplicates 和 id_collisions。
- `log_1781981849783_cae4fa4216`：review_course 外显“修正 12 个条目即可通过”。

介入动作：

- 已向 manager 发送指引消息 `msg_1781982046039_41cba81d8d`：把 MINOR 返给 worker_qbank 修 v3 map，不允许直接 apply；修完再回 review_course 或至少让 review_course确认。

临时结果：

- manager inbox 当前为空，说明 review verdict 已被消费或至少没有待读；但尚未看到 manager 派 worker_qbank 修 MINOR。

明天修复建议：

- qbank review verdict 需要结构化字段：`PASS` 才能 unlock apply；`MINOR` 必须进入 rework。
- apply 命令应拒绝在最新 verdict 不是 PASS 的情况下执行。

### 43. Qbank v3.1 使用 `r2/r3` 后缀，可能与 verifier Q-ID schema 冲突

触发原因：

- worker_qbank 已修正 v3.1 方向问题，并生成 `content/qbank-dedup-v3-maps.json`。
- 但映射中的新 Q-ID 使用 `Q-...r2` / `Q-...r3` 后缀。
- 当前 `scripts/qbank_verify.py` 的 Q-ID regex 不接受字母后缀，apply 后可能把 duplicate error 变成 schema warning/error。

现场证据：

- `content/qbank-dedup-v3-maps.json` 多处 action 为 `renumber → Q-1.1-01r2`、`Q-5.1-01r3` 等。
- `content/qbank-dedup-dryrun-plan-v3.md` Renumber Map 全表使用 `r2/r3`。
- `scripts/qbank_verify.py` 第 156 行：`qid_pat = re.compile(r\"^Q-[A-Z]?\\d+(?:\\.\\d+)?-\\d+$\")`，只允许末尾为数字。
- 当前尚未 apply，重跑 verifier 仍为旧状态：3154 题 / 39 duplicate errors。

介入动作：

- 已向 manager 发送指引消息 `msg_1781982415394_dfed97ba67`：v3.1 回 review / apply 前先修编号策略，改为 verifier 兼容的纯数字编号（例如 topic 内下一个可用序号），不要临时放宽 verifier schema。

临时结果：

- 尚未看到 apply，仍可在方案阶段纠正，风险可控。

明天修复建议：

- qbank renumber 策略必须由 verifier 反向校验：生成 map 后先 dry-run schema check。
- 如果确实需要 suffix ID，应先更新全链路 schema、manifest、importer，而不是只改内容文件。

### 44. 课程学科线在 Business Studies 后停摆，被 qbank/router 运营任务吸走

触发原因：

- 用户反馈“学科线怎么没动静了”。
- 现场检查证实：T-10 Business Studies closeout 后，worker_course 长时间空闲；manager 当前注意力集中在 qbank 去重和 router 修复，没有继续派下一学科/下一批课程生产。
- 这违背今晚主目标：IGCSE 学科实例应持续跑 `topic -> QA -> review -> manager closeout` 链条，qbank/router 应并行，不应阻塞课程线。

现场证据：

- `status.json`：`worker_course.status=空闲`，task 仍是旧的 `T-10 Business Studies 0450 已恢复...等待 review_course 复检`。
- `manager.status=进行中`，task 为 `QBank v3.1...；worker_builder 修 router 多实例竞争`。
- `task list`：T-10 已完成后，没有新的正式 IGCSE subject-launch task。
- 现有任务中 T-7 Accounting 仍是 `进行中`，描述写明剩余 Batch 3-10 待推进。
- 课程日志最新实质进展停在 Business Studies 0450 PASS / closeout。

介入动作：

- 已向 manager 发送恢复课程线指令 `msg_1781983033378_f0430ecebe`：qbank/router 继续并行，但必须立即恢复 worker_course 学科生产；优先推进现有 T-7 Accounting Batch 3-10。

临时结果：

- 待 manager 消费后复查是否派发 worker_course 新任务，并检查 task/status/log 三端同步。

明天修复建议：

- manager 应有“课程线不可空闲”守护：当 worker_course 空闲超过阈值且仍有未完成学科/批次，应自动派发下一批。
- qbank/router 属于横向运营线，不应抢占课程生产主线；需要独立 lane 状态。
- `status.json` 不应长期保留已完成 T-10 旧任务，应在 closeout 后切到下一学科或待派原因。

### 45. 缺少默认续航策略：未指定下一步时 manager 会停住

触发原因：

- 用户指出：“这个也是个问题，为什么一没有定就停了”。
- Business Studies 0450 closeout 后，manager 对外说“等待确认下一学科方向”，而不是自动从 backlog 选择下一项。
- 这暴露了系统缺少 continuation policy：当 boss 没有明确指定下一学科时，应该按既定 backlog/优先级继续跑，而不是让课程线空闲。

现场证据：

- `log_1781979463057_20b30f71dc`：manager 在 Business Studies closeout 后说“请确认下一学科方向”。
- `log_1781979552209_772e0f7a0a`：manager 说“当前待命，等待下一学科指令”。
- `status.json` 当前 worker_course 空闲，manager 正在处理 qbank/router。
- `task list` 中仍有 T-7 Accounting Batch 3-10 待推进，说明不是没有 backlog。

介入动作：

- 已通过消息 `msg_1781983033378_f0430ecebe` 向 manager 发送默认续航策略：没有 boss 新指令时，不等待；按 backlog 推进 T-7 Accounting Batch 3-10，或按当前 `igcse-subject-launch` 队列启动下一学科；qbank/router 并行处理。

临时结果：

- 待 manager 消费后复查是否恢复课程生产。

明天修复建议：

- 增加 manager continuation policy：
  - if `worker_course idle` AND `course backlog non-empty` THEN auto-dispatch next course batch。
  - if `subject closeout complete` AND `next subject unspecified` THEN choose next backlog item by priority，而不是 ask boss。
  - 只有遇到高影响产品取舍才问 boss。
- 给 task tracker 增加 backlog priority 和 lane：`course-production`、`qbank`、`infra`，避免横向任务阻塞课程主线。

### 46. 缺少无人值守续跑能力：一没人盯，课程线就停

触发原因：

- 用户进一步指出：“这个也是问题，一没盯就停了”。
- 这比“没有定下一学科就停”更严重：系统表现为依赖 Codex/用户人工盯盘来继续推进，而不是自己保持课程生产链路转动。

现场证据：

- Business Studies 0450 已在 `log_1781979463057_20b30f71dc` closeout，但之后没有自动派发下一课程批次。
- worker_course 当前空闲，status 仍挂旧 T-10 文案。
- qbank/router 仍在推进，说明系统不是全局停机，而是课程主线缺少无人值守调度。
- 直到用户提醒“学科线怎么没动静了”，Codex 才发现并准备介入恢复课程线。

介入动作：

- 已通过消息 `msg_1781983033378_f0430ecebe` 向 manager 发送强制续跑指令：无人盯盘时也必须保持 `course-production` lane 前进；今晚默认从 backlog 继续 T-7 Accounting Batch 3-10。
- 要求 manager 外显新的课程任务 message id / task id，并让 worker_course ACK。

临时结果：

- 待 manager 消费后复查 worker_course 是否接单。

明天修复建议：

- 增加 `autopilot-course-lane` 守护：
  - 每 15 分钟检查 worker_course 是否空闲。
  - 若空闲且 backlog 存在，自动派下一批。
  - 派发后要求 worker ACK，未 ACK 则升级 manager/auto_ops。
- manager 不应把“等待 boss 确认”作为默认停机状态；只有高影响方向变更才可停等。
- 把“无人盯盘仍能持续推进”作为系统验收指标。

### 40. router 间歇性崩溃被 auto_ops 二次确认，watchdog 未有效恢复

触发原因：

- 此前 router_alive=false 曾被判断为误报或 PID 漂移。
- 本轮 auto_ops 明确记录第二次 router_alive=false，且 PID 多次变化，判断为 router 持续重启/间歇性崩溃。

现场证据：

- `log_1781981533842_a3504ccdcc`：auto_ops note，Hermes 第二次 router_alive=false，router PID `63312→76390` 再次变化，说明 router 持续重启。
- `log_1781981541467_18ee7cf405`：auto_ops 外显，非误报；watchdog 虽存活但未有效恢复 router，建议 manager 派 worker_builder 排查。
- `eduflowteam health` 当前 router alive，但 PID 波动说明存在间歇性故障。

介入动作：

- 已在消息 `msg_1781981682512_114a95b19e` 中提醒 manager：派 worker_builder 排查 router 崩溃根因，不要只把它当 transient warning。

临时结果：

- 当前 router alive，业务消息仍能读取，但稳定性风险上升。

明天修复建议：

- router crash 应有 crash log / exit code / restart count。
- watchdog 不应只看 pid alive，还应记录 router 最近 N 分钟重启次数。
- Hermes 告警需区分 `stale pid false positive` 与 `flapping restart`。

### 42. router flapping 根因迹象：多实例 router/watchdog 竞争 + runtime-status 原子写冲突

触发原因：

- worker_builder 正在排查 router flapping，但本轮直接读取 router/watchdog log 已看到明显模式。
- router 不是单纯崩溃，而是多个实例并发启动/respawn，互相检测到 `another router already running`，并重复 catch-up。

现场证据：

- `.eduflow-team-state/router.log` 多次出现：
  - `another router already running (pid ...)`
  - `router exited: handled=0 dropped=16`
  - `no events for 135s/136s; subscribe likely silently stalled, exiting for respawn`
  - 多个 `router subscribing...` 粘连在同一行，疑似多进程同时写 log。
- `.eduflow-team-state/watchdog.log` 多次重复：
  - `router respawned (fail_count was 0)`
  - 两条相同输出粘连在同一行，疑似多个 watchdog 或重复启动逻辑。
- router.log 还出现：`inject error for manager: [Errno 2] No such file or directory: runtime-status.json.tmp -> runtime-status.json`，与前面 runtime-status JSON 污染/原子写问题相互印证。

介入动作：

- 已在消息 `msg_1781982046039_41cba81d8d` 中提醒 manager/worker_builder：排查重点应从“单次崩溃”升级为“多实例竞争、watchdog 重复 respawn、runtime-status 原子写冲突”。

临时结果：

- 当前 `health` 显示 router alive，但日志证明稳定性仍未真正修复。

明天修复建议：

- router/watchdog 应引入单实例锁，启动前用 flock 或 atomic pid lock，避免重复 respawn。
- runtime-status 写入应使用进程唯一 tmp 文件，再 atomic replace，避免多个进程共用 `runtime-status.json.tmp`。
- watchdog 的 fail_count 不应每次都是 0；需要持久化 flapping 计数并触发熔断。

### 38. `eduflowteam health` 出现 JSONDecodeError，health 自身不稳定

触发原因：

- 在等待 review_course 消费期间重跑 health，命令失败而非正常输出。

现场证据：

- 命令：`. ./scripts/eduflow-team-env.sh && ./scripts/eduflowteam health`
- 输出：`health: unhandled error: JSONDecodeError: Extra data: line 69 column 5 (char 1673)`。
- 同一轮日志和 inbox 仍可读取，说明不是整个系统不可用，而是 health 读取某个 JSON 状态文件时遇到多段/污染数据。
- 随后 `eduflowteam send manager ...` 虽然写入 inbox 成功，但 tmux inject best-effort 也失败：`Extra data: line 69 column 5 (char 1673)`，说明问题已影响消息唤醒路径。

介入动作：

- 已定位污染文件：`.eduflow-team-state/facts/runtime-status.json`。
- 已备份为 `.eduflow-team-state/facts/runtime-status.json.bak-<timestamp>`。
- 已用 JSON decoder 截断到第一个合法 JSON 结束位置，移除多余尾巴。
- 修复后重跑 `./scripts/eduflowteam health`，恢复正常，router alive。

临时结果：

- review_course verdict 已正常产生，说明核心消息链仍在工作。
- health 和 tmux inject 相关 JSONDecodeError 已临时解除。

明天修复建议：

- health 对 JSONDecodeError 应输出具体文件路径和恢复建议，而不是吞掉 traceback。
- runtime/status JSON 写入应采用原子写，避免并发写导致 `Extra data`。
- 增加 `eduflowteam doctor state-json`，扫描 `.eduflow-team-state/facts/*.json` 是否可解析。

### 47. 课程线再次停住：tmux 执行环境 down，watchdog 缺失，Accounting 派单未被消费

触发原因：

- 用户反馈“就停了”，需要确认为什么一没盯就停。
- 课程主线应能在 manager 派单后自动继续，但 Accounting 0452 Batch 3 未被 worker_course ACK。

现场证据：

- 在项目环境下执行：`. ./scripts/eduflow-team-env.sh && ./scripts/eduflowteam health`。
- health 显示：`tmux session EduFlowTeam not running`。
- router alive，task-publish alive，但 `watchdog: no pid file (not running?)`。
- `worker_course` inbox 仍有 1 unread：`msg_1781983056819_81f3d878d5`，内容是恢复 T-7 Accounting 0452 Batch 3。
- 直接执行未 source 环境的 `./scripts/eduflowteam health` 会读到默认 `/Users/huanganan/.eduflow`，造成现场判断偏差。

介入动作：

- Codex 先记录本 gap，再执行最小 runtime 恢复：启动 `EduFlowTeam` tmux session 和 watchdog，不直接改课程产物，不直接 apply qbank 去重。
- 恢复后检查 `worker_course` 是否消费 Accounting 派单，并避免重复重派造成 course 外显刷屏。

临时结果：

- 已执行 `. ./scripts/eduflow-team-env.sh && ./scripts/eduflowteam up`。
- `EduFlowTeam` tmux session 已恢复，7 个 agent 窗口全部 ready/lazy ready。
- router/task-publish 保持 alive，watchdog 新 pid `98022` 已启动。
- `worker_course` 已消费 Accounting 派单 `msg_1781983056819_81f3d878d5`，ACK 为 `accepted_task`，并将状态设置为 `T-7 Accounting 0452 Batch 3 生产`。
- 恢复后暴露一个次级问题：worker_course shell 中 `head` 命令不可用，说明 agent runtime PATH/基础命令环境仍不稳；当前 worker 已改用其他方式继续，不先阻塞课程线。

明天修复建议：

- 自动监控必须强制加载项目 env，避免误读默认 state_dir。
- watchdog 缺失时应被 health/automation 判定为红色阻断，并自动拉起。
- manager 派单后应有 ACK SLA；超过 5-10 分钟未 ACK，auto_ops 应先查 tmux/session，再决定是否重投递。
- 课程线需要无人值守续跑策略：worker_course 空闲且 backlog 未清时，应自动拉下一批，而不是等待人工盯盘。

### 48. Qoder worker runtime PATH 缺基础命令，消息处理/自查容易卡住

触发原因：

- team runtime 恢复后，worker_course 和 worker_qbank 均开始处理 inbox，但 shell 命令环境异常。

现场证据：

- worker_course 尝试 `find ... | head -50`，报错：`command not found: head`。
- worker_qbank 尝试 `eduflow workspace worker_qbank 2>&1 | tail -30`，报错：`command not found: tail`。
- worker_qbank 尝试 `ls .eduflow-team-state/agents/worker_qbank/`，报错：`command not found: ls`。
- 两个 worker 均为 `qoderclicn` runtime，说明不是单个 agent 偶发问题，而是 Qoder pane 环境 PATH/基础命令解析问题。

介入动作：

- Codex 暂不直接修 worker 内容产物，只记录问题并准备提醒 manager/worker_builder：优先排查 Qoder runtime PATH，避免“消息一多处理就卡”。

临时结果：

- worker_course 已改用其他方式继续 Accounting Batch 3，没有立刻阻塞。
- worker_qbank 仍能用部分 eduflow 命令和 Glob，但自检能力受限。
- worker_builder 已接单排查，并将 `scripts/eduflow-team-env.sh` 改为硬编码 PATH：`$ROOT/.venv/bin:/Users/huanganan/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin`。
- builder 本地 fresh shell 验证 `tail/head/ls` 可被找到；当前 health 显示 qoderclicn workers ready。
- 排查中还发现一个更深问题：运行中的 `/opt/homebrew/bin/eduflow` 可能加载了 `/Volumes/Halobster/Codex相关/EduFlow/src/eduflow`，与当前项目源码不完全一致；这会导致 health/runtime status 行为与项目代码预期不一致。

明天修复建议：

- Qoder runtime 启动命令应显式继承 `/bin:/usr/bin:/usr/sbin:/sbin:/opt/homebrew/bin`。
- health 增加 per-agent shell smoke：`command -v ls head tail sed awk python3`。
- worker identity 中可临时要求：基础命令不可用时，先运行 `export PATH=/bin:/usr/bin:/usr/sbin:/sbin:/opt/homebrew/bin:$PATH` 再继续。
- 梳理 `scripts/eduflowteam`、`/opt/homebrew/bin/eduflow`、项目 `src/eduflow` 三者加载关系，避免 worker/health 调用不同版本代码。

### 49. Accounting Batch 3 派单验收口径过重，可能把课程线拉偏

触发原因：

- manager 恢复 T-7 Accounting 0452 Batch 3 时，派单写成“每 topic 300-500 QA / 30+ items”。
- 该口径与 T-7 原任务描述不一致：Accounting 0452 为 35 sub-topics / 10 batches / 约 245 QA，Batch 1/2 均是小批次通过。

现场证据：

- `eduflow task list` 中 T-7 描述：`35 sub-topics / 10 batches / ~245 QA`。
- `worker_course` 收到的 `msg_1781983056819_81f3d878d5` 写明：`QA 数量达标（每 topic 300-500 QA / 30+ items）`。
- 若 worker_course 按字面执行，会从“Batch 3 小闭环”膨胀为巨大生产任务，导致课程线再次卡住或跑偏。

介入动作：

- Codex 已向 manager 发送 `msg_1781983761576_5333233456`：要求 Accounting Batch 3 回到 T-7 原设定（35 sub-topics / 10 batches / 约245 QA，总量按批次累计），不要按“每 topic 300-500 QA / 30+ items”字面执行；同时要求 worker_builder 排查 Qoder runtime PATH。

临时结果：

- worker_course 已 ACK 并开始查 Accounting 现状，尚未看到新文件落盘。
- 后续 worker_course 已按收窄口径完成 T-7 Accounting Batch 3：11 topics (5.1-7.1)，补齐 `content/igcse-accounting-0452/items/7-5-items.md` stub，更新 manifest 为 `submitted_for_review`。
- worker_course 回报 `msg_1781984106239_75bf07be01`：累计 Batch 1-3 = 224 QA / 31 topics，剩余 4 topics (7.2-7.5) 待后续批次。
- 当前 manager 仍有该完工报告 unread，需要继续盯 manager 是否派 review_course 正式复核。
- Codex 已补发 manager 收口提醒 `msg_1781984203243_903028bde9`：要求消费 worker_course 完工报告并派 review_course 文件级复核，复核 verdict 前不要 closeout 或切走课程线。

### 50. Accounting Batch 3 通过结构/内容检查但难度分布不合规，被 review_course 退回

触发原因：

- worker_course 报告 T-7 Accounting Batch 3 完工后，review_course 进入正式复核。
- 需要确认是否可 closeout，避免再次出现“worker 说完成但 review gate 没闭环”。

现场证据：

- review_course 群内 verdict：Accounting 0452 Batch 3（11 topics / 99 QA）复核不通过。
- 通过项：文件结构、内容准确性、items 映射全部通过。
- 不通过项：难度分布未达 `F:3|S:3|C:3`；7 个 topic 沿用旧 `F:2|S:4|C:3`，4 个 topic 内部分布不一致。

介入动作：

- Codex 记录本 gap，并发送 manager 指引 `msg_1781984620263_ae3788ec57`：不要 closeout，不要切新学科；只派 worker_course 做最小返修，将 11 topics / 99 QA 难度分布统一到 `F:3|S:3|C:3`；已通过的结构、内容准确性、items 映射不要重做；修完后回送 review_course 二次确认。

临时结果：

- Batch 3 不是内容重做问题，是可控的难度标签/题目结构返修问题。

明天修复建议：

- worker_course 交付前增加 per-topic difficulty distribution preflight。
- review_course 的 verdict 应自动生成返修单草案，减少 manager 漏消费。
- manifest/status 不应只标 `submitted_for_review`，还应能写入 `review_failed:difficulty_distribution`。

### 51. Accounting Batch 3 返修自检误报：worker_course 声称 11/11 达标，但本地预检仅 4/11 达标

触发原因：

- worker_course 收到返修单后回报：11 topics (5.1-7.1) 全部修正为 `F:3|S:3|C:3`。
- manager 已基于该回报派 review_course 做二次复核，需要避免 reviewer 被错误自检口径影响。

现场证据：

- worker_course 回报：修改 4 个 items 文件 `(5-2, 5-3, 5-4, 7-1)` 并声称 11 topics 全部逐一验证。
- Codex 独立统计 `content/igcse-accounting-0452/items/*.md` 中 `**Difficulty**:` 行，结果：
  - 达标：`5-2`, `5-3`, `5-4`, `7-1` = `F:3|S:3|C:3`。
  - 未达标：`5-1` = `F:3|S:4|C:2`。
  - 未达标：`5-5`, `5-6`, `6-1`, `6-2`, `6-3`, `6-4` = `F:2|S:4|C:3`。
- 因此当前实际状态是 4/11 达标，不是 11/11 达标。

介入动作：

- Codex 记录本 gap，并发送 review_course 证据提醒 `msg_1781985008164_7ab3d2dc9b`：二次复核以文件级统计为准，不要直接采信 worker_course 的 11/11 自检口径。

临时结果：

- 二次复核已在 review_course inbox：`msg_1781984915461_ea3c426b4f`。
- 后续 manager 已派 worker_course 二次返修 `msg_1781985060311_efd8895e91`，要求同步 QA 文件难度标签并补齐 7 个未修改 topic。
- 截至本轮机器统计：`5-2`, `5-3`, `5-4`, `7-1` 的 items 与 qa-question-level 已一致达 `F:3|S:3|C:3`；`5-1`, `5-5`, `5-6`, `6-1`, `6-2`, `6-3`, `6-4` 仍未完成，worker_course 正在继续编辑。
- 后续 worker_course 自检发现 `5-5/5-6/6.1-6.4` 被错误改成 `F:3|S:4|C:2`，并自行回滚 Q9 至 Challenge。
- 当前机器统计已通过：11/11 topics (5.1-7.1) 的 items 与 qa-question-level 均为 `F:3|S:3|C:3`，`ALL_OK=True`。

明天修复建议：

- worker_course 自检必须跑机器可复现脚本，而不是人工目测/局部 grep。
- 难度分布检查应成为 `review_course` 和 `worker_course` 共用的 preflight 命令。
- 返修报告必须列出每个 topic 的实际 `F/S/C` 统计，而不是只写总称“已逐一验证”。

### 52. worker_course 复检投递使用错误命令格式，review_course 未收到正式 inbox

触发原因：

- worker_course 完成 Batch 3 二次返修后，声称已发送 review_course 复检。
- 但复查 review_course 窗格与 inbox 未看到对应新任务。

现场证据：

- `logs.jsonl` 出现异常记录：`agent="--body" type="say"`，内容为 worker_course 的复检报告。
- worker_course 使用了类似 `eduflow say --to review_course --body ...` 的参数顺序，导致日志 agent 被解析为 `--body`。
- `review_course` inbox 仍为空，窗格停留在此前处理 codex 提醒的状态。
- 文件级机器验证已通过：11 topics 的 items 与 qa-question-level 均为 `F:3|S:3|C:3`。

介入动作：

- Codex 记录本 gap，并使用 `eduflow send review_course codex ...` 正式投递复检任务 `msg_1781986369202_f270e9586b`，确保进入 review_course inbox。

临时结果：

- `review_course` 已收到正式 inbox，等待复检 verdict。
- review_course 已完成三次复检：PASS。证据：11/11 topics 全部 `F:3|S:3|C:3`，QA/items 零冲突，99 QA 完整，已交 manager closeout。
- manager 已开始消费 PASS 消息并准备 closeout。
- manager 已正式 closeout：T-7 Accounting 0452 Batch 3 三次复检 PASS，累计完成学科口径更新为 Accounting 0452 / Economics 0455 / Business Studies 0450。

### 53. Accounting closeout 后 router 再次无 pid file，watchdog 未恢复到健康面

触发原因：

- T-7 Accounting Batch 3 closeout 后复查 health，确认运行态是否稳定。

现场证据：

- `. ./scripts/eduflow-team-env.sh && ./scripts/eduflowteam health` 显示：
  - tmux session 与各 agent pane 均 ready。
  - `task-publish` alive。
  - `watchdog` alive (`98022`)。
  - `router: no pid file (not running?)`。
- router cursor 仍存在，说明曾有事件流；但 pid file 缺失使 health 降级为 warning。
- 这与前面 router/watchdog 多实例竞争、pidlock、respawn 不稳定问题同源。

介入动作：

- Codex 记录本 gap，并发送 manager 运行态提醒 `msg_1781986733794_08e319d7cd`：要求派 worker_builder 确认 router 是否实际退出、pid file 是否丢失、watchdog 为什么未恢复，并修复后跑 health 验证。

临时结果：

- 业务链刚完成 Accounting closeout，但消息入口可靠性存在再次退化风险。
- 复查进程层后，watchdog 已在 04:18 左右拉起 router，`.eduflow-team-state/router.pid` 已恢复，当前 router 进程存在。
- 但 `router.log` 仍持续出现 `no events for 131-137s; subscribe likely silently stalled, exiting for respawn`，说明 flapping 未根治，只是 watchdog 继续拉起。

明天修复建议：

- watchdog 应检测 router pid file 缺失并自动 respawn，且 health 应能显示 watchdog 最近一次 respawn 尝试。
- router pid file 缺失但 cursor 更新时，应区分“进程仍在但 pid file 丢失”与“进程已退出”。
- closeout 后 auto_ops 应自动跑 health，并将 router warning 转为维修任务而非待命。

明天修复建议：

- `eduflow say` 参数解析应拒绝/报错错误顺序，而不是把 `--body` 记为 agent。
- worker 给 reviewer 的任务应统一使用 `eduflow send review_course <sender> ...`，而不是 `say --to review_course`。
- chat/log 与 inbox 投递需要明确区分，避免“群里说了”被误当成“reviewer 收到了任务”。

明天修复建议：

- manager 派单模板需要区分：subject-level 总量、batch-level 目标、topic-level item 数。
- 高风险数量口径应由 review_course 或 workflow schema 校验后再发给 worker。
- 对“每 topic 300-500 QA”这类明显异常目标增加自动拦截。

### 54. Physics Batch 2 closeout 后 manager 再次停在“等待下一步指示”

触发原因：

- 用户指出“就停了 / 一没有定就停了 / 一没盯”，要求记录问题并把 workflow 先挂上。
- T-11 Physics 0625 Batch 2 已 closeout，但 Physics 0625 明显仍有剩余 topic backlog。

现场证据：

- `manager` 窗格显示：`Manager 状态：待命，等待下一步指示`。
- `manager / worker_course / review_course / worker_qbank` inbox 全为空。
- `task list` 中最新有效 Physics 任务 `T-11` 已 `delivered`，未出现 Batch 3 或下一批结构化任务。
- `content/igcse-physics-0625/topic-outline.md` 定义 Physics 0625 共 46 topics；`qa-manifest.csv` 当前仅 8 rows（Batch 1 + Batch 2），仍缺 38 topics。
- `workflow show igcse-subject-launch` 明确要求 `manager -> worker_course -> review_course -> manager`，但 closeout 后没有自动生成下一批 workflow 任务。

介入动作：

- Codex 记录本 gap。
- 准备创建 `IGCSE Physics 0625 Batch 3 topic-outline + QA seed` 结构化任务，并显式挂 `igcse-subject-launch` workflow。
- 任务范围先取下一批 5 topics：`2.4 Power/efficiency`, `2.5 Energy resources/electricity generation`, `2.6 Pressure in liquids/atmospheric/gas pressure`, `3.1 Kinetic particle model`, `3.2 Temperature/thermometers/thermal equilibrium`。
- 要求继续沿用 Batch 1/2 验收口径：每 topic 9 items，难度 `F:2|S:4|C:3`，同步 `items/`, `qa/`, `qa-question-level/`, `qa-manifest.csv`，完工必须送 `review_course` 文件级复核，再由 `manager` closeout。

临时结果：

- 待创建任务后复查：task 状态、worker_course inbox、review_course 待命/复核状态。

明天修复建议：

- manager closeout 后应自动读取 subject manifest 与 full topic outline，若未完成则生成 next-batch candidate，而不是默认“等待老板确认”。
- workflow 需要加 `next_batch_continuation_gate`：当 subject backlog > 0 且用户已要求持续跑实例时，closeout 后必须继续派下一批。
- auto_ops 每轮巡检应检测“最新任务 delivered + inbox 全空 + manifest 未满”的组合，并自动提示 manager 续航。

### 55. router 仍处于 alive-but-flapping，消息多时容易放大卡顿/漏投递

触发原因：

- 用户持续反馈 agent 消息处理口有问题、消息一多就卡，需要持续监测并记录卡点。
- 本轮停摆排查时再次复查 router 与 health。

现场证据：

- `health` 当前显示 `router: alive (7795)`，但仍有 `runtime_status_env_drift` warning。
- `router.log` 连续出现：`no events for 128-137s; subscribe likely silently stalled, exiting for respawn`，随后反复 `router subscribing` 和 `catching up missed message(s)`。
- 业务层此前多次出现 `eduflow say --to ... --body ...` 被解析成 `agent="--body"`，说明“群里说了”和“inbox 收到”之间已经有多次断层。

介入动作：

- Codex 记录本 gap。
- 暂不直接改 router，避免在 Physics 生产链继续跑时引入新变量；继续按 inbox/task 双重验证每一次关键 handoff。

临时结果：

- 当前 router 有 PID，watchdog 能拉起；但 flapping 未根治，仍需明天作为消息入口重点维修项。

明天修复建议：

- router subscription 需要区分“真实无消息”和“连接静默失效”，避免固定 2 分钟重启造成 missed catchup 压力。
- health 应展示最近 5 次 router respawn 时间、原因和 catchup 数量，便于判断消息多时是否雪崩。
- `send/say` 应统一强校验投递目标与收件 inbox，关键 handoff 必须返回 inbox message id。

### 56. `task flow-create` 生成 queued task，但没有真实投递到 worker inbox

触发原因：

- Codex 为 Physics Batch 3 创建结构化任务后，复查 worker_course inbox。

现场证据：

- `task flow-create` 返回：`created flow task T-12 ... workflow=igcse-subject-launch`。
- `task get T-12` 显示状态仍为 `queued`，`latest_turn_summary=Task created and queued`。
- `inbox worker_course` 显示 `no unread messages`。
- worker_course pane 仍停留在 T-11 完工后“Awaiting review feedback or new task assignments from manager”，说明没有收到 T-12 真实执行入口。

介入动作：

- Codex 记录本 gap。
- 准备将 T-12 从 `queued` 推进到 `assigned`，并使用 `send worker_course manager --stdin` 投递真实 inbox 派工，避免只靠群消息或 task 表。

临时结果：

- 待投递后复查 worker_course inbox 与 task 状态。

明天修复建议：

- `task flow-create` 可考虑增加 `--send` 或默认在创建后自动投递 assignee inbox。
- `auto stage reassurance published` 不应被视作执行入口；创建任务后必须返回 worker inbox message id。
- supervisor-check 应检测 `queued task + assignee inbox empty`，并自动提示 manager/auto_ops 补派。

### 57. worker_course 已实际处理 T-12，但 task 状态仍停在 `assigned`

触发原因：

- T-12 真实 inbox 派工后，复查 task 状态与 worker_course pane。

现场证据：

- worker_course 已 ack `msg_1781989789447_d28189b7b9`，并进入 T-12 内容读取与文件扫描。
- worker_course 已识别 Batch 3 现有文件不完整：`2-5-items.md` 只有 5 题，`2-6/3-1/3-2` 也在继续检查。
- 但 `task get T-12` 仍显示 `status=assigned`，没有自动推进到 `in_progress`。

介入动作：

- Codex 记录本 gap。
- 准备按现场事实将 T-12 推进到 `in_progress`，避免 manager/auto_ops 误判为“只是已派未动”。

临时结果：

- 待状态同步后继续观察 worker_course 是否补齐 5 个 topic 的 9 items、qa-question-level 与 manifest。

明天修复建议：

- worker ack accepted_task 后，如果 pane 中已有文件读取/编辑动作，应自动触发 `task flow-transition <id> --to in_progress --actor <owner>`。
- task-publish/worker adapter 不应只发外显“已接单”，也要同步结构化 task 状态。
- supervisor-check 应检测 `worker_stage_ack + task still assigned`，并提示或自动修正。

### 58. T-12 `submit-review` 后 reviewer 为空，review_course inbox 也未收到

触发原因：

- worker_course 完成 Physics 0625 Batch 3 后声称已 handoff 给 review_course，manager 也同步“已送 review_course 复检”。
- 复查 review_course inbox 仍为空。

现场证据：

- `task get T-12` 显示 `status=submitted_for_review`，但没有 `reviewer` 字段。
- `task review-queue` 能看到 T-12 awaiting review：`reviewer=-`。
- `task review-queue --reviewer review_course` 显示 `no tasks awaiting review`。
- `inbox review_course` 显示 `no unread messages`。
- worker_course pane 显示执行了 `task submit-review T-12 --actor worker_course`，但没有成功 assign reviewer 或发送有效 inbox。

介入动作：

- Codex 记录本 gap。
- 准备执行 `task assign-reviewer T-12 --reviewer review_course --by manager`，并补发 review_course inbox，要求文件级复核 Batch 3。

临时结果：

- 待复查 review queue 与 review_course inbox。

明天修复建议：

- `task submit-review` 应在存在 workflow reviewer 默认值时自动填 reviewer，或拒绝生成 `reviewer=-` 的待审任务。
- manager/worker 的“已送 review_course”外显文案必须以 reviewer assigned 或 review_course inbox message id 为依据。
- supervisor-check 应检测 `submitted_for_review + reviewer empty`，自动生成 manager action 或直接补 reviewer。

### 59. T-12 closeout 后 manager 再次等待确认，Physics 未完成仍不自动续批

触发原因：

- T-12 Physics 0625 Batch 3 已由 review_course PASS，并由 manager closeout。
- 但 Physics 0625 full outline 共 46 topics，目前仅完成 13 topics，仍有明确 backlog。

现场证据：

- `review_course` PASS 证据：5 topics / 45 QA，F:2|S:4|C:3，QA/items 零冲突，manifest 同步。
- `manager` closeout 后群消息为：`请确认下一学科 / 下一批次`。
- `qa-manifest.csv` 当前累计 13 rows，距离 46 topics 仍缺 33 topics。
- 这与 gap 54 同源：closeout 后没有基于 subject backlog 自动续航。

介入动作：

- Codex 记录本 gap。
- 准备继续创建 Physics 0625 Batch 4 结构化任务，并显式挂 `igcse-subject-launch` workflow。
- 下一批范围建议：`3.3 Thermal expansion`, `3.4 Heat transfer`, `3.5 Specific heat capacity`, `3.6 Melting/boiling/latent heat`, `4.1 Wave properties`。

临时结果：

- 待创建 Batch 4 后复查 task 状态、worker_course inbox、review_course gate。

明天修复建议：

- manager closeout 后必须运行 subject backlog 检查：若 manifest rows < outline topics 且当前目标是持续跑实例，则自动创建 next batch。
- closeout 文案应区分“整个学科完成”与“本批完成”；本批完成不能默认请求老板确认。
- task supervisor 应把 `delivered/closeout + manifest incomplete + inbox empty` 识别为续航缺口。

### 60. worker_course 在 T-13 生产中触发 Qoder API FORBIDDEN，执行链中断

触发原因：

- T-13 Physics 0625 Batch 4 正在补齐 `3.3/3.4/3.5/3.6/4.1` 五个 topic。
- worker_course 已开始修正 `3-4-items.md`、`4-1-items.md`，但随后 CLI 报错。

现场证据：

- worker_course pane 显示：`Qoder API error: FORBIDDEN - {"code":"112","message":"{\"pricingUrl\":\"https://qoder.com.cn/pricing?client=qoder\\\"}"}`。
- T-13 仍为 `in_progress`，review_course inbox 为空，manifest 尚未追加 batch-04。
- 独立计数显示 batch-04 items 仍不完整：
  - `3-3-items.md`: 5 difficulty rows，缺 Q06-Q09。
  - `3-4-items.md`: 6 difficulty rows，缺 Q07-Q09。
  - `3-5-items.md`: 5 difficulty rows，缺 Q06-Q09。
  - `3-6-items.md`: 6 difficulty rows，缺 Q07-Q09。
  - `4-1-items.md`: 6 difficulty rows，缺 Q07-Q09。

介入动作：

- Codex 记录本 gap。
- 先让 manager/worker_builder/auto_ops 处理 worker_course runtime 或 quota 问题；若无法快速恢复，则 Codex 亲自接手补齐 T-13 文件并走 review gate。

临时结果：

- 待派生态自修并复查 worker_course 是否恢复。

明天修复建议：

- runtime guard 需要识别 Qoder `FORBIDDEN code=112`，自动切换 worker_course 到可用备用 runtime 或暂停派工。
- health 应显示 worker runtime 的付费/额度/forbidden 状态，而不是只显示 pane ready。
- 长任务应能在 API error 后自动交回 manager，避免 pane 停在错误页面但 task 仍显示 in_progress。

### 61. T-13 已在群里 closeout，但结构化 task 未反写且 Physics 未自动续批

触发原因：

- 用户反馈“就停了”“一没有定就停了”，要求继续盯住学科线。
- T-13 Physics 0625 Batch 4 已由 review_course PASS，manager 已在群里正式 closeout。
- 但结构化任务状态仍停在 `submitted_for_review / verdict=pending`，manager 也显示“待命等老板新指令”，没有自动创建 Batch 5。

现场证据：

- manager pane 显示：`T-13 Physics 0625 Batch 4 已正式 closeout，Physics 累计 18 topics / 162 QA 全部通过`，但同时写着 `当前无活跃派工。待命等老板新指令`。
- `eduflowteam task get T-13` 显示：`[submitted_for_review]`、`reviewer: review_course`、`verdict: pending`。
- `content/igcse-physics-0625/qa-manifest.csv` 当前只有 18 条 topic entry，full outline 为 46 topics，仍缺 28 topics。
- `worker_course` inbox 仍残留一条 T-13 旧续做消息，内容与当前事实冲突：T-13 实际已由 Codex 补齐并通过复核。

介入动作：

- Codex 记录本 gap。
- 准备把 T-13/T-12 结构化任务状态补齐，并继续创建 Physics 0625 Batch 5。
- Batch 5 将继续挂 `igcse-subject-launch` workflow，范围为 4.2-4.6，要求每 topic 9 items、F:2|S:4|C:3、manifest 追加 batch-05、review_course 文件级复核后 manager closeout。

临时结果：

- 待执行状态修复、创建 Batch 5，并复查 worker_course inbox / task list / review gate。

明天修复建议：

- manager closeout 必须同步调用 `task manager-closeout` 或等价状态转换，不能只在群里 say。
- supervisor-check 应识别 “群消息 closeout 但 task 仍 pending/submitted_for_review” 的状态漂移。
- subject backlog autopilot 需要在 batch closeout 后读取 outline/manifest 差额，自动续批，不能每批结束都等待老板确认。
- inbox 应支持 task closeout 后自动清理或标记过期消息，避免 worker_course 继续看到旧任务。

### 62. T-14 创建后只在群里外显接单，task 仍 queued 且 worker inbox 未收到新任务

触发原因：

- Codex 为恢复 Physics 续航创建 T-14 Batch 5。
- 系统主群日志已出现 `worker_course` 和 `manager` 的“课程研发任务已接单：T-14”外显消息。
- 但结构化 task 仍停在 `queued`，worker_course inbox 没有 T-14，反而还残留旧的 T-13 续做消息。

现场证据：

- `eduflowteam task get T-14` 显示：`[queued]`、`latest_turn_summary: Task created and queued`。
- `eduflowteam inbox worker_course` 只显示旧消息 `msg_1781992561868_a7bd6ac4ae`，内容仍要求继续 T-13 Batch 4。
- `logs.jsonl` 已出现 `worker_course` 接单 T-14 的 say，但这不是可靠的 inbox/task handoff。
- worker_course pane 仍停留在 Qoder FORBIDDEN 后的旧上下文，存在继续误处理 T-13 的风险。

介入动作：

- Codex 记录本 gap。
- 准备将 T-14 从 `queued` 推进到 `assigned`，并补发 worker_course inbox，明确“忽略旧 T-13，执行 T-14 Batch 5”。
- 必要时清理或标记旧 T-13 inbox 已读，避免 stale message 把 worker 拉回已完成任务。

临时结果：

- 待执行 assigned transition 与 inbox 补发后复查。

明天修复建议：

- `flow-create` 的 auto stage reassurance 不应替代 task assignment 和 inbox 投递。
- worker agent 的“接单”外显必须以 task 状态进入 assigned 或 inbox ack 为依据。
- inbox 需要 stale-task guard：如果消息指向已 closeout task，应自动降级/隐藏，并提示 manager 重新派当前 task。

### 63. worker_course 仍消费旧 T-13 消息，T-14 因 runtime 切换未生效暂停

触发原因：

- Codex 已将旧 T-13 inbox 标记为 `stale_superseded_by_T14`，并补发 T-14 inbox。
- 但 worker_course pane 仍显示收到了旧 T-13 与新 T-14 两条提示，并先对旧 T-13 产生 stage ACK。
- manager 随后确认：worker_course 的 Qoder quota 故障仍未恢复，声称的 backup runtime 切换未生效，Physics Batch 5 暂无法启动。

现场证据：

- `logs.jsonl` 出现 `worker_course_stage_ack`，ref 仍是旧消息 `inbox:msg_1781992561868_a7bd6ac4ae`，内容为 T-13 Batch 4 续做。
- `eduflowteam inbox worker_course` 仍显示 T-14 `msg_1781992817880_648e3154da` 未读。
- manager 群消息明确写到：`worker_course 修复存在 gap`、`Qoder 订阅额度用尽`、`course_backup_deepseek 切换未生效`、`Physics Batch 5 暂无法启动`。
- worker_course pane 仍在 Qoder CLI 上下文，出现 response idle timeout / Qoder quota 后续卡顿迹象。

介入动作：

- Codex 记录本 gap。
- 准备给 manager 与 worker_builder 发明确恢复指引：暂停旧 T-13 消息消费；先恢复 worker_course 可用 runtime；恢复后重新 ACK T-14，而不是继续处理 T-13。

临时结果：

- 待 manager/worker_builder 响应 runtime 修复；若 15 分钟监控周期内仍未恢复，Codex 可直接接手 Batch 5 内容生产或进一步修复 runtime。

明天修复建议：

- inbox read/stale 标记需要能阻止 pane 继续注入旧消息，至少在 closeout task 上强制 suppress。
- worker runtime switch 必须有 end-to-end 验证：不仅写 runtime-status，还要确认 pane 实际环境变量、CLI、provider、model 已切换。
- manager 对“已切换 runtime”的口径必须基于可执行探针，而不是配置层声明。
- task launcher 应优先投递最新 assigned task，旧 closeout task 消息不得再次触发 stage ACK。

### 64. T-14 Batch 5 存在旧半成品文件，但 workflow 未识别为“补齐现有产物”

触发原因：

- T-14 当前被表述为“Batch 5 暂无法启动”，焦点集中在 worker_course runtime 故障。
- 但文件面检查发现 Batch 5 的 4.2-4.6 并非空白任务，已有旧产物落盘。
- 这些旧产物未进入 manifest，也未达到每 topic 9 items / F:2|S:4|C:3，workflow 没有自动把它识别成“补齐/同步/送审”任务。

现场证据：

- `content/igcse-physics-0625/qa-question-level/` 已存在 `Q-4.2-01` 到 `Q-4.6-09` 共 45 个 question-level 文件。
- `content/igcse-physics-0625/qa/` 已存在 5 个 Batch 5 topic QA 文件。
- `content/igcse-physics-0625/items/4-2-items.md` 到 `4-6-items.md` 已存在，但每个仅 5-6 items：
  - 4.2：5 items，分布 F:4|S:1|C:0，且 2 处 items/QA 难度不一致。
  - 4.3：5 items，分布 F:4|S:1|C:0，且 2 处 items/QA 难度不一致。
  - 4.4：5 items，分布 F:3|S:2|C:0，且 1 处 items/QA 难度不一致。
  - 4.5：6 items，分布 F:3|S:3|C:0。
  - 4.6：5 items，分布 F:3|S:2|C:0。
- `content/igcse-physics-0625/qa-manifest.csv` 仍只有 batch-01 到 batch-04 共 18 topic entries，没有 batch-05 / 4.2-4.6。

介入动作：

- Codex 记录本 gap。
- 当前先等待 worker_builder 的 runtime 自修结果；如果短窗口内 worker_course 仍无法恢复，则 Codex 可直接基于已有 question-level 文件补齐 Batch 5 items、同步 manifest，并送 review_course。

临时结果：

- 待复查 worker_builder 是否完成 runtime 恢复，以及 worker_course 是否 ACK T-14。

明天修复建议：

- subject workflow 启动新 batch 时应先扫描 topic 文件面，区分“空白新建”与“旧半成品补齐”。
- manager 的 blocker 判断应同时看 runtime 和文件面，不应把所有停滞都归因于 runtime。
- review preflight 应能在 manifest 缺 batch、items 不满 9、QA question-level 已齐时给出自动补齐计划。

### 65. manager / worker_builder pane 消失，生态自修未能恢复 T-14 执行

触发原因：

- Codex 已给 manager 和 worker_builder 发出恢复指令，并等待短窗口让生态自修。
- worker_builder 曾 ACK runtime blocker，但 20 秒后 pane 检查显示 manager 与 worker_builder 均无 pane。
- T-14 仍停在 `assigned`，worker_course 的 T-14 inbox 仍未读，Batch 5 仍未进入生产/送审。

现场证据：

- `eduflowteam task get T-14` 仍为 `[assigned]`。
- `eduflowteam inbox worker_course` 仍显示 `msg_1781992817880_648e3154da` 未读。
- `eduflowteam peek worker_builder` 返回：`worker_builder has no pane in session EduFlowTeam`。
- `eduflowteam peek manager` 返回：`manager has no pane in session EduFlowTeam`。
- `logs.jsonl` 最新只到 worker_builder stage ACK，没有 runtime 修复完成、worker_course ACK T-14 或 Batch 5 开始生产的后续证据。

介入动作：

- Codex 记录本 gap。
- 决定直接接手 T-14 Batch 5：基于已有 45 个 question-level QA 文件补齐 5 个 items 文件到每 topic 9 items，统一 F:2|S:4|C:3，追加 `qa-manifest.csv` batch-05，然后送 review_course 文件级复核。

临时结果：

- 待 Codex 补齐内容并运行一致性验证。

明天修复建议：

- runtime 自修任务不能只在 agent pane 内进行，必须有 watchdog/manager 可见的完成事件或 blocker 事件。
- `peek has no pane` 应触发自动 rehire 或 manager escalation，而不是让任务静默停住。
- 对高优先级主线任务，应设置“assigned + inbox unread + agent pane missing” 的自动兜底规则。

### 66. T-14 submit-review 后 reviewer 未挂载，review_course pane 消失

触发原因：

- Codex 已补齐 T-14 Batch 5 并发送 review_course inbox。
- `task submit-review T-14` 成功将状态推进到 `submitted_for_review`。
- 但 `reviewer` 字段未自动填充，`review-queue --reviewer review_course` 为空；同时 `review_course` pane 消失。

现场证据：

- `eduflowteam task get T-14` 显示 `[submitted_for_review]`、`verdict: pending`，但无 `reviewer: review_course`。
- `eduflowteam task review-queue --reviewer review_course` 返回 `no tasks awaiting review`。
- `eduflowteam inbox review_course` 仍有 T-14 复核请求未读。
- `eduflowteam peek review_course` 返回：`review_course has no pane in session EduFlowTeam`。

介入动作：

- Codex 记录本 gap。
- 准备执行 `task assign-reviewer T-14 --reviewer review_course --by manager`，并尝试恢复/rehire review_course pane。

临时结果：

- 待补 reviewer 后复查 review queue；若 review_course 无法恢复，Codex 将进行临时文件级复核或改派可用 reviewer。

明天修复建议：

- `submit-review` 对 flow task 应使用 workflow 默认 reviewer，不能生成无 reviewer 的待审任务。
- `review_course_stage_ack` 不应在 pane 消失后留下“已接单”的错觉；需要 pane liveness 与 review queue 双重检查。
- review gate 的可靠信号应是 `reviewer=review_course + review queue visible + pane alive/ack read`，而不是单条 inbox ACK。

### 67. T-14 已入 review queue，但 EduFlowTeam tmux session 整体掉线

触发原因：

- Codex 已补 reviewer，使 T-14 出现在 `review-queue --reviewer review_course`。
- 随后 health 检查显示整个 `EduFlowTeam` tmux session 不存在，watchdog 也无 pid。
- 这意味着 review queue 虽然正确，但 review_course 无运行 pane 可执行复核。

现场证据：

- `eduflowteam task review-queue --reviewer review_course` 显示 T-14 awaiting review。
- `eduflowteam task get T-14` 显示 `submitted_for_review`、`reviewer: review_course`、`verdict: pending`。
- `eduflowteam health` 红项：`tmux session EduFlowTeam not running (run eduflow start)`。
- `health` 同时显示：`watchdog: no pid file (not running?)`。

介入动作：

- Codex 记录本 gap。
- 准备尝试安全重启 team session / watchdog，使 review_course 能继续执行 T-14 复核。

临时结果：

- 待重启后复查 health、review_course inbox、review queue 与 verdict。

明天修复建议：

- watchdog 不应在 tmux session down 时同时消失；至少需要外部 supervisor 保持 watchdog 常驻。
- router alive 不能代表 team 可执行，health_bad 应把 `tmux session down + review queue non-empty` 升级为红色阻塞。
- 高优任务 pending review 时，如果 reviewer pane 不存在，应自动 rehire reviewer 或触发 Codex/manager 兜底。

### 68. T-14 review_course 已 PASS，但 task verdict 未自动反写

触发原因：

- review_course 已完成 T-14 Batch 5 文件级复核，并在群日志中明确给出 PASS。
- 但结构化任务仍停在 `submitted_for_review / verdict=pending`，review queue 仍显示 awaiting review。

现场证据：

- `logs.jsonl` 显示：`T-14 Physics 0625 Batch 5（4.2-4.6）复核完成 — VERDICT: PASS。5 topics / 45 QA 全部达标，无难度冲突，manifest 依赖链完整。`
- `eduflowteam task get T-14` 仍显示 `[submitted_for_review]`、`verdict: pending`。
- `eduflowteam task review-queue --reviewer review_course` 仍显示 T-14 awaiting review。

介入动作：

- Codex 记录本 gap。
- 准备执行 `task review T-14 --actor review_course --approve`，再推动 manager closeout，并继续创建 Physics Batch 6/T-15。

临时结果：

- 待结构化状态补齐、closeout 与下一批创建。

明天修复建议：

- review_course 的 PASS 消息必须自动触发 task verdict 反写，或要求 reviewer 同步调用 `task review --approve`。
- manager closeout 不应只监听群消息，也应扫描 `PASS but task pending` 的漂移。
- `review-queue` 中若对应日志已有 PASS，应自动生成 manager-action 或 repair action。

### 69. `manager-closeout` 不适配 Physics batch task，closeout 只能靠 delivered + 群消息

触发原因：

- T-14 已经由 review_course PASS，并被 Codex 补为 `delivered / approved`。
- 按常规尝试执行 `task manager-closeout T-14 --actor manager`，希望结构化 closeout。
- 命令返回 `subject closeout not ready: not_subject`，说明该 closeout 命令只适配 subject 级任务，不适配 batch task。

现场证据：

- `eduflowteam task review T-14 --actor review_course --approve` 成功：`status=delivered verdict=approved`。
- `eduflowteam task manager-closeout T-14 --actor manager` 返回：`not_subject`。
- T-14 是 `igcse-subject-launch` workflow 的 batch task，而不是 subject inventory 的整科 closeout。

介入动作：

- Codex 记录本 gap。
- 不再阻塞在 `manager-closeout`，改用 delivered/approved 作为结构化通过状态，并继续推动 T-15。

临时结果：

- T-14 已可视为 batch 级交付完成，但缺少标准化 batch closeout 命令。

明天修复建议：

- 增加 `task batch-closeout <id>`，支持 batch task 从 `delivered` 进入明确 closeout 状态。
- manager closeout 文案应能区分 subject closeout 与 batch closeout。
- subject backlog autopilot 应以 batch delivered/approved 触发下一批，不依赖 subject closeout 命令。

### 70. T-15 创建后重复出现“主群接单但 task queued / inbox 旧消息 / worker Qoder FORBIDDEN”

触发原因：

- T-14 已 PASS/delivered，Physics 仍只有 23/46 topics，需要继续 T-15。
- Codex 创建 T-15 后，主群日志出现 worker_course/manager “已接单”外显。
- 但结构化 task 仍是 `queued`，worker_course inbox 仍残留旧 T-14 消息，worker_course pane 仍报 Qoder `FORBIDDEN code=112`。

现场证据：

- `eduflowteam task get T-15` 显示 `[queued]`。
- `eduflowteam inbox worker_course` 只显示旧 `msg_1781992817880_648e3154da`（T-14 Batch 5 指令）。
- `eduflowteam peek worker_course` 显示 Qoder API `FORBIDDEN code=112` / credits exhausted。
- `logs.jsonl` 同时出现 `课程研发任务已接单：IGCSE Physics 0625 Batch 6...（T-15）`，说明外显与可执行状态再次分叉。

介入动作：

- Codex 记录本 gap。
- 准备将 T-15 从 `queued` 推进到 `assigned`，将旧 T-14 inbox 标记 stale，并补发 T-15 inbox。
- 若 worker_course 仍不能执行，则继续按兜底规则处理 Batch 6 或等待可用 runtime。

临时结果：

- 待状态转换、inbox 补发、runtime 复查。

明天修复建议：

- `flow-create` 必须真正投递当前 task inbox，不能只发主群 reassurance。
- worker_course 的旧 inbox 消息必须在对应 batch PASS 后自动失效。
- Qoder FORBIDDEN 应导致 worker_course 不再被派主线，自动切到可用备用 runtime 或转 Codex 兜底。

### 71. T-15 因 Qoder quota blocker 停住后，manager 未自动切换可用执行者

触发原因：

- T-15 已被派给 worker_course，主群出现“已接单”外显。
- worker_course / worker_builder / worker_qbank 均受 Qoder `FORBIDDEN code=112` 额度耗尽影响，无法生产。
- manager 已识别 blocker，但转为“请老板决策是否等额度/是否改用 Claude Code”，没有按夜间监控约定自动切到可用执行者或 Codex 兜底。

现场证据：

- `eduflowteam task get T-15` 显示任务仍停在 `[assigned]`，verdict pending。
- `eduflowteam inbox worker_course` 显示 T-15 派工未读。
- `health` 显示 worker_course pane ready，但历史和群日志均显示 Qoder quota exhausted，说明 pane ready 不能代表生产可用。
- `logs.jsonl` 显示 manager 明确说：`Qoder API 额度耗尽 blocker 未解除... T-15 暂挂`，随后又请求老板决策。

介入动作：

- Codex 记录本 gap。
- 按“生态自修失败后 Codex 下场”规则，直接补齐 Physics 0625 Batch 6 文件，并送 review_course 文件级复核。

临时结果：

- 待 Batch 6 文件补齐、manifest 同步、任务送审。

明天修复建议：

- quota blocker 被确认后，manager 应自动执行 fallback policy：可用 Claude/Anna/Codex 接手，而不是等待老板。
- health 需要区分 `pane ready` 与 `provider usable`，Qoder FORBIDDEN 应显示为红色不可生产。
- manager 的夜间策略应内置“超过 5 分钟无恢复则自动兜底生产/复核”的 SLA。

### 72. T-15 review_course 已 PASS，但 task verdict 再次未自动反写

触发原因：

- review_course 已完成 T-15 Physics 0625 Batch 6 文件级复核，并在群日志中明确给出 PASS。
- 但结构化任务仍停在 `submitted_for_review / verdict=pending`，review queue 仍显示 awaiting review。
- 这是 gap 68 在 T-15 上复发，说明 reviewer 的自然语言 PASS 与 task 状态机仍未打通。

现场证据：

- `logs.jsonl` 显示：`T-15 Physics 0625 Batch 6（4.7-5.2）复核完成 — VERDICT: PASS。5 topics / 45 QA 全部达标。`
- `logs.jsonl` 随后显示 `task_completed`: `T-15 Physics 0625 Batch 6 (4.7-5.2) 复核 PASS — 45 QA items，难度零冲突，manifest 完整`。
- `eduflowteam task get T-15` 仍显示 `[submitted_for_review]`、`verdict: pending`。
- `eduflowteam task review-queue --reviewer review_course` 仍显示 T-15 awaiting review。

介入动作：

- Codex 记录本 gap。
- 准备执行 `task review T-15 --actor review_course --approve`，将结构化状态补为 delivered/approved。

临时结果：

- 待结构化 verdict 反写后，继续推动 Physics Batch 7，不再等待人工下一步。

明天修复建议：

- review_course 输出 `VERDICT: PASS` 或 `task_completed` 时必须自动调用 `task review --approve`。
- review queue 应有漂移修复：若日志已有 PASS 且本地校验通过，自动提示/执行 verdict sync。
- manager 不应只读群文本 closeout，应以 task verdict 为主并主动修复 `PASS but pending` 状态。

### 73. T-16 review PASS 后继续停在 pending，PASS→task verdict 反写问题稳定复现

触发原因：

- T-16 Physics 0625 Batch 7 已由 review_course 完成文件级复核并明确 PASS。
- 但 `eduflowteam task get T-16` 仍显示 `[submitted_for_review] / verdict=pending`。
- 这是 T-14、T-15 后的第三次稳定复现，说明不是偶发延迟，而是 review 完成事件没有驱动 task 状态机。

现场证据：

- `logs.jsonl` 显示：`T-16 Physics 0625 Batch 7（5.3-5.7）复核完成 — VERDICT: PASS。5 topics / 45 QA 全部达标。`
- `logs.jsonl` 显示：`task_completed`: `T-16 Physics 0625 Batch 7 (5.3-5.7) 复核 PASS — 45 QA items，难度零冲突，manifest 完整`。
- `eduflowteam task get T-16` 仍显示 `submitted_for_review`、`verdict: pending`。

介入动作：

- Codex 记录本 gap。
- 准备执行 `task review T-16 --actor review_course --approve` 反写结构化状态。

临时结果：

- 待 T-16 delivered/approved 后继续 Physics Batch 8。

明天修复建议：

- 将 PASS→`task review --approve` 做成强制工具调用或自动 scanner repair，不能依赖 reviewer 自觉。
- 对 `task_completed` 类型日志增加 event scanner，自动匹配 task id 并更新 verdict。
- review queue 应拒绝长期保留“已有 PASS 日志”的任务，避免 manager 重复等待。

### 74. Codex 兜底生产时，task transition 仍外显为 worker_course 开始/完成

触发原因：

- T-17 Batch 8 实际由 Codex 兜底补齐文件并送审。
- 为保持 workflow 状态机，Codex 调用了 `flow-transition` / `submit-review`，actor 使用 `worker_course`。
- 发布层自动生成了“worker_course 开始处理 / 完成并交给 manager”的主群消息，导致外显责任归因不真实。

现场证据：

- `logs.jsonl` 显示：`worker_course` 发送 `课程研发任务已开始处理：IGCSE Physics 0625 Batch 8...`。
- 随后又显示：`worker_course` 发送 `课程研发任务已完成并交给 manager：IGCSE Physics 0625 Batch 8...`。
- 但实际 Batch 8 文件由 Codex 生成并校验，且 worker_course 仍受 Qoder quota blocker 影响。

介入动作：

- Codex 记录本 gap。
- 当前继续使用 workflow 状态机推进，但在 review 指令中明确标注 `Codex 已按 workflow 补齐并提交`，降低 reviewer 误判。

临时结果：

- T-17 已送 review_course，等待 PASS/NEEDS_FIX。

明天修复建议：

- task transition 应支持 `producer=codex` 与 `assignee=worker_course` 分离，不应把状态机 actor 当作真实生产者。
- 自动 reassurance 文案需要读取 `owner/producer/fallback_reason`，避免把 Codex 兜底伪装成 worker 完工。
- 当 worker runtime 标记 quota blocker 时，禁止发布“worker 已开始/已完成”类消息，除非有真实 worker ACK 和产物证据。

### 75. T-17 review PASS 后仍未反写 verdict，PASS→approve 漂移继续复现

触发原因：

- T-17 Physics 0625 Batch 8 已由 review_course 复核 PASS。
- 结构化任务仍停在 `submitted_for_review / verdict=pending`。
- 这是 T-14/T-15/T-16/T-17 连续复现，已可判定为稳定缺陷。

现场证据：

- `logs.jsonl` 显示：`T-17 Physics 0625 Batch 8（5.8-6.2）复核完成 — VERDICT: PASS。6 topics / 54 QA 全部达标...`
- `logs.jsonl` 显示 `task_completed`: `T-17 Physics 0625 Batch 8 (5.8-6.2) 复核 PASS — 54 QA items，难度零冲突，manifest/topic-outline 一致`。
- `eduflowteam task get T-17` 仍显示 `submitted_for_review`、`verdict: pending`。

介入动作：

- Codex 记录本 gap。
- 准备执行 `task review T-17 --actor review_course --approve`，补齐结构化状态。

临时结果：

- 待 T-17 delivered/approved 后推进 Physics 最后一批 topics。

明天修复建议：

- 将 gap 68/72/73/75 合并为一个 P0：review PASS 事件未驱动 task verdict。
- 需要单测覆盖：reviewer `say VERDICT: PASS`、`task_completed PASS`、review queue pending 三种输入都应触发同一个 repair。
- manager closeout 必须依赖结构化 verdict，并在 pending+PASS 日志时主动触发修复。

### 76. T-18 final subject PASS 已出现，但最终批次 verdict 仍 pending

触发原因：

- review_course 已完成 Physics 0625 Batch 9 FINAL 复核，并明确说明整科 46 topics / 414 QA 可 closeout。
- 但 T-18 结构化任务仍为 `submitted_for_review / verdict=pending`。
- 这是 final closeout 阶段再次复现 PASS→task verdict 未反写问题。

现场证据：

- `logs.jsonl` 显示：`Physics 0625 整科复核完成 — Batch 9 FINAL PASS。全学科 46 topics / 414 QA，9 批次依赖链完整，可进入 closeout。`
- `logs.jsonl` 显示 `task_completed`: `T-18 Physics 0625 Batch 9 FINAL (6.3-7.4) 复核 PASS — 全科 46 topics / 414 QA subject closeout`。
- `eduflowteam task get T-18` 仍显示 `submitted_for_review`、`verdict: pending`。

介入动作：

- Codex 记录本 gap。
- 准备执行 `task review T-18 --actor review_course --approve`，补齐结构化状态。
- 随后执行 Physics manifest 总量、难度、batch 依赖链核查，作为整科 closeout 证据。

临时结果：

- 待 T-18 delivered/approved 和整科核查完成。

明天修复建议：

- final subject closeout 不能只依赖自然语言日志；必须保证 final batch task verdict 与 subject inventory 同步。
- `subject closeout` 应接受 final batch PASS 自动触发，并记录全科总量证据。
- review PASS 反写缺陷应作为明天 P0 修复，已连续影响 T-14 至 T-18。

### 77. Physics final batch delivered/approved 后，`manager-closeout` 仍不支持 subject closeout

触发原因：

- T-18 final batch 已 delivered/approved，review_course 明确给出 Physics 整科 46 topics / 414 QA closeout PASS。
- Codex 运行整科 manifest 校验也通过。
- 但执行 `eduflowteam task manager-closeout T-18 --actor manager` 返回 `not_subject`，说明 final batch 不能触发 subject closeout 命令。

现场证据：

- `task review T-18 --actor review_course --approve` 成功，T-18 为 `delivered / approved`。
- 本地整科核查输出：`manifest rows 46 QA 414`、batch 分布 `4/4/5/5/5/5/5/6/7`、`PHYSICS_0625_CLOSEOUT_OK`。
- `manager-closeout T-18` 返回：`subject closeout not ready: not_subject`。

介入动作：

- Codex 记录本 gap。
- 将 Physics closeout 证据包发给 manager，用 delivered/approved + review PASS + manifest closeout OK 作为临时整科完成状态。

临时结果：

- Physics 0625 可判定内容生产与复核完成，但系统缺少正式 subject closeout 状态机落点。

明天修复建议：

- 增加 `subject-closeout --from-final-batch <task_id>` 或让 `manager-closeout` 支持 final batch task。
- subject inventory 应能读取 manifest 总量与 final PASS 自动标记 subject complete。
- closeout 命令应输出明确的 subject summary：topics、QA、batch chain、review verdict、remaining topics=0。

### 78. 横向总量核查口径不统一：qbank report 有四科总量，subject inventory/manifest 无法证明

触发原因：

- manager 已汇总四科总量：Accounting 315 + Economics 234 + Business 300 + Physics 414 = 1263 QA。
- 本地直接读取 `qa-manifest.csv` 时，只能稳定核到 Physics 0625；Accounting 的 manifest 口径与 qbank report 不一致，Economics/Business 缺少 `qa-manifest.csv`。
- `subject-inventory` 对这些已完成/批次型学科仍显示 `not_subject` 或缺少 QA count，不能作为最终横向验收依据。

现场证据：

- `content/qbank-verification-report.md` 记录：Accounting 0452 = 315、Economics 0455 = 234、Business Studies 0450 = 300。
- Physics 0625 本轮整科核查通过：46 topics / 414 QA。
- 直接 manifest 脚本输出：Economics/Business `qa-manifest.csv` 缺失；Accounting manifest 只显示 247 QA，和 qbank report 的 315 不一致。
- `subject-inventory` 对 Physics batch tasks 仍显示 `not_subject`，不能反映 final closeout。

介入动作：

- Codex 记录本 gap。
- 采用 qbank verification report + Physics closeout verifier 作为今晚临时横向证据，不将 goal 标记 complete，继续按 15 分钟巡检观察 qbank/manager 是否有后续任务或反馈。

临时结果：

- 内容层面四科总量可解释为 1263 QA，但系统层面缺少统一 subject manifest / inventory closeout 证明。

明天修复建议：

- 为 Economics/Business 补 `qa-manifest.csv` 或统一生成 subject manifest。
- 修复 Accounting manifest/qbank report 口径差异，明确 315 QA 的权威来源。
- `subject-inventory` 应读取真实 subject manifest/qbank report，而不是把 batch tasks 全部显示 `not_subject`。

### 79. manager 在 final closeout 后缺少“无下一任务时的自动收尾/建议”动作

触发原因：

- 用户指出“就停了”“一没有定就停了”“一没盯”，说明当前链条在 Physics 0625 整科 closeout 后，如果没有明确下一学科/下一批指令，manager 会进入待命。
- 这不是内容生产失败，而是 workflow 收尾阶段缺少自动下一步：完成态核查、横向缺口汇总、下一候选学科建议、qbank 反馈入口确认。

现场证据：

- `logs.jsonl` 06:59 左右 manager 已说：`当前全队待命，无进行中任务，等待下一步指令。`
- `eduflowteam task review-queue --reviewer review_course` 返回 `no tasks awaiting review`。
- `worker_course`、`worker_qbank`、`review_course` inbox 均无未读。
- manager inbox 仍有 Codex 发来的 Physics 0625 subject closeout evidence 未读，说明 closeout 证据消费和后续动作没有自然闭环。

介入动作：

- Codex 记录本 gap。
- 准备给 manager 发送低噪音内部指引：不要继续静默待命，立刻按 `igcse-subject-launch` workflow 做完成态核查、qbank 状态确认、下一候选学科建议，并把无法自证的问题标为明日修复 gap。

临时结果：

- 待 manager 消费该指引并输出收尾/下一步建议。

明天修复建议：

- `igcse-subject-launch` workflow 增加 `no_next_subject_guard`：当 final batch closeout 且无新任务时，manager 必须自动触发收尾核查，而不是等待人工指令。
- manager closeout 后应自动检查：review_queue、agent inbox、qbank report、subject manifest/inventory、router/watchdog health。
- 如果没有下一学科输入，应输出 2-3 个候选动作：继续下一 IGCSE 学科、进入 qbank import/dedup、或只做横向复核。
- 该 guard 需要避免刷屏，只发布一条 compact closeout/next-step card。

### 80. manager 高优先级 inbox 堆积，消息一多后消费口延迟明显

触发原因：

- 用户指出“消息一多处理就卡”，本轮现场出现 manager inbox 高优先级消息堆积。
- manager pane 仍活着，但 status 仍停在 `当前全队待命，无进行中任务，等待下一步指令`，说明 pane liveness 不等于 inbox 消费完成。

现场证据：

- `eduflowteam inbox manager` 显示 4 条 unread：Physics closeout evidence、auto_ops watchdog 4th 催办、Codex workflow guard、auto_ops card。
- `eduflowteam peek manager` 显示 manager 正在处理 auto_ops 卡片，但还没有完成 ACK 或状态更新。
- `eduflowteam status manager` 仍显示旧的待命总结，未反映未读高优先级消息。

介入动作：

- Codex 记录本 gap。
- 暂不继续刷 manager inbox，先观察 pane 是否能自然消费。
- 同步处理 watchdog 缺失，避免 router 崩溃后消息入口进一步失守。

临时结果：

- 待 manager 输出 workflow 收尾和 watchdog 修复动作。

明天修复建议：

- manager health 不能只看 pane ready，需要加入 `high_priority_unread_age` 和 `unread_count`。
- 当 manager inbox 高优先级消息超过阈值未 ACK，应由 auto_ops 或 supervisor 触发轻量 wake/reinject，而不是继续追加催办。
- status surface 应显示 `processing inbox backlog`，避免外部误判为“待命”。
- 对卡片消息做摘要压缩，避免长卡片让 manager 处理口卡住。

### 81. watchdog 连续缺失 50 分钟，auto_ops 催办未触发实际维修

触发原因：

- auto_ops 连续 4 轮报告 watchdog 缺失，但 manager 未派发有效修复。
- watchdog 缺席时 router 当前虽 alive，但一旦 router 静默断连/崩溃将没有自动重启保障。

现场证据：

- `eduflowteam inbox manager` 显示 auto_ops：`watchdog_alive=false 连续 4 轮告警（06:11→06:21→06:31→07:01, 跨度50min）`。
- `eduflowteam health` 显示 `router: alive`、`task-publish: alive`、`watchdog: no pid file (not running?)`。
- README 说明 `eduflow up` 会拉起 `tmux + agents + router + watchdog`。

介入动作：

- Codex 记录本 gap。
- 准备执行非破坏性恢复：`eduflowteam up`。
- 恢复后立刻运行 `eduflowteam health` 验证 watchdog 是否 alive。

临时结果：

- 已执行 `. ./scripts/eduflow-team-env.sh && ./scripts/eduflowteam up && ./scripts/eduflowteam health`。
- `eduflowteam up` 输出：`watchdog launched (pid 16501)`。
- 随后 `health` 验证：`router: alive (98239)`、`task-publish: alive (36617)`、`watchdog: alive (16501)`。
- 当前仅剩 manager runtime env drift warning，watchdog 缺失已临时恢复。

明天修复建议：

- auto_ops 的 `trigger_supervisor_repair` 应能自动执行安全恢复命令或明确升级给 Codex，而不是只催 manager。
- manager 未消费 auto_ops 维修催办时，supervisor 应避免无限追加消息，改为一次性执行安全 `up` 或发单给 builder。
- health warning 中 `watchdog no pid file` 应提升为可恢复操作建议：`run eduflowteam up`。

### 82. supervisor-check 受旧未读消息污染，且 `read --help` 有副作用

触发原因：

- watchdog 已由 Codex 手动恢复，但 `task supervisor-check --json` 仍判定 `runtime_unhealthy`，核心原因变成 Hermes supervisor 缺失、worker_builder 旧高优维修消息未读、codex 自身旧 T-13 兜底消息未读。
- Codex 试图查看 `eduflowteam read <msg> --help` 用法时，该命令没有 help 分支，直接把消息标为已读，存在操作坑。

现场证据：

- `task supervisor-check --json` 输出 `recommended_action=trigger_supervisor_repair`，但 `supervisor_processes` 中 router/task-publish/watchdog 均 alive，仅 `hermes-supervisor` pid 缺失。
- `eduflowteam inbox codex` 显示高优消息 `msg_1781992032199_083824b262`：要求 5 分钟后接手 T-13 Batch 4；该任务实际已完成、review PASS、后续 B5-B9 也已完成。
- `eduflowteam inbox worker_builder` 显示 4 条高优 watchdog/Qoder 维修旧消息，其中 watchdog 已由 Codex 手动恢复，worker Qoder 额度问题已作为夜间系统 gap，不应继续阻塞当前 completion audit。
- 执行 `eduflowteam read msg_1781992032199_083824b262 --help` 返回 `marked read`，说明命令误把 `--help` 当作参数之外的普通调用处理。

介入动作：

- Codex 记录本 gap。
- 将已被事实闭环覆盖的 Codex 旧高优消息标为已读，避免 supervisor 继续误报 codex inbox blocker。
- 准备恢复 Hermes supervisor 进程，让监督层重新具备外部心跳。

临时结果：

- Codex 旧 T-13 高优消息已读。
- 尝试用 `nohup ./scripts/hermes-supervisor-loop.sh 600 ... &` 恢复 Hermes supervisor，短时间内写入 pid `58128`，但随后 `ps -p 58128` 查不到进程；`supervisor-check` 仍报告 `hermes-supervisor alive=false`。
- 该现象复现了“后台/nohup supervisor pid 文件短暂存在但进程不稳定”的历史问题，需改用 tmux 托管。

明天修复建议：

- `read` 命令应支持 `--help` 并且 help 必须零副作用。
- supervisor-check 应识别“旧高优消息已被后续 task delivered/approved 或 closeout 覆盖”，避免 stale unread 造成假阻塞。
- 对 worker_builder 这类维修消息，需要有 `superseded_by_health_recovered` 机制：如果 health 已恢复，旧维修工单不应继续触发 escalated_failure。
- Hermes supervisor 缺失应独立命名为 `hermes_supervisor_down`，不要混称 `runtime_unhealthy` 到主链路 runtime。
- Hermes supervisor loop 应有正式 lifecycle 命令，避免依赖临时 shell/nohup；推荐固定由 tmux window 或 launchd 托管。

现场恢复补充：

- 已创建 tmux window `EduFlowTeam:hermes_supervisor` 托管 `./scripts/hermes-supervisor-loop.sh 600`。
- 恢复后 pid `17527` 存活，`tmux list-windows` 显示 `hermes_supervisor` 窗口。
- `hermes-supervisor.log` 显示：`health=soft_warning_observe action=continue_observing alert=no_alert`。
- 后续 `task supervisor-check --json` 显示 supervisor_processes 中 `router/task-publish/watchdog/hermes-supervisor` 全部 `alive=true`，当前不再是 runtime escalated failure。
- 剩余异常为软观察：manager idle、T-10 structured truth lag、worker_qbank status stale、worker_builder 旧高优维修消息未读。

### 83. manager 已读事实校正但未 ACK，仍复用旧状态面汇报

触发原因：

- Codex 已向 manager 发送 runtime fact correction，说明 watchdog 与 Hermes supervisor 均已恢复，不应再按“watchdog 缺失/待 worker_builder 修复”汇报。
- manager inbox 已清空，但 `status manager` 显示 `已读待确认`，尚未 ACK/started。
- 最新 manager 群内汇报仍包含旧事实：`worker_builder / worker_qbank 启动中 53 min`、`worker_course 待命（停在 T-15 旧任务）`、`Qoder API FORBIDDEN 仍阻塞 3 个 Qoder worker`。这些不应作为当前主线事实继续外显，至少需要标注为“旧状态面/需复核”。

现场证据：

- `eduflowteam inbox manager` 返回 `no unread messages`。
- `eduflowteam status manager` 返回：`已读待确认：高优任务已读但尚未 ACK/started`，内容为 Codex runtime fact correction。
- `logs.jsonl` 最新 manager 汇报：watchdog 已恢复，但仍继续汇报 Qoder worker 阻塞、worker_course 停在旧 T-15。
- `eduflowteam health` 当前显示 router/task-publish/watchdog alive；Hermes supervisor tmux/log 显示 alive 且 supervisor-check 为 `soft_warning_observe`。

介入动作：

- Codex 记录本 gap。
- 暂不继续追加 manager 催办，避免消息噪音扩大。
- 下一轮 15 分钟巡检重点观察：manager 是否 ACK fact correction；worker_builder 旧高优消息是否被 superseded；manager 是否继续复用旧状态面。

临时结果：

- 当前链路无新生产任务、无 review queue、主守护健康；状态面存在陈旧/未 ACK 风险。

明天修复建议：

- 高优 fact correction 被 read 后必须进入 ACK 状态，否则 supervisor 应判为 `read_without_ack`。
- manager 对外汇报前应运行一次 current-state refresh，而不是复用 status/memory 旧文本。
- 对 “worker blocked / Qoder forbidden / old task id” 这类状态，超过一定时间必须标注 stale，不能作为当前事实无条件外显。
- 引入 `superseded_by_runtime_fact` 或 `superseded_by_health_recovered`，让旧维修工单和旧 blocker 自动降级。

### 84. worker_builder 旧高优消息已读但未 ACK，supervisor 仍作为 blocking warn

触发原因：

- 上一轮 worker_builder 旧高优维修消息已从 unread 清空，但 supervisor-check 仍检测到 `read_without_ack`。
- 这些消息内容分别是 T-13 stale 消息阻断、worker_course CLI 可用性验证、watchdog 缺失维修等，均已被后续事实覆盖：Physics B4-B9 已完成，watchdog/Hermes 已恢复。

现场证据：

- `eduflowteam inbox worker_builder` 返回 `no unread messages`。
- `task supervisor-check --json` 为 `soft_warning_observe`，但 anomalies 中仍有 4 条 `high_priority_inbox_read_without_ack`：
  - `msg_1781993729601_2d2c9195a5`
  - `msg_1781993917609_9e44550efa`
  - `msg_1781994842213_5bbe0b09a4`
  - `msg_1781996667262_fb7728bc87`
- `supervisor_processes` 显示 router/task-publish/watchdog/hermes-supervisor 全部 alive。
- `manager status` 已更新为：`codex 事实修正已收口：watchdog/hermes 全绿，4 条旧维修消息已 ACK 清理；等老板新指令`。

介入动作：

- Codex 记录本 gap。
- 不再向群里追加催办，避免把旧状态机问题变成新噪音。
- 保持 15 分钟观察，若 supervisor 升级为 escalated_failure 再介入；否则留作明日状态机修复。

临时结果：

- 当前主链路健康、监督层为软观察；旧 builder ACK 缺失不阻塞今晚内容链路。

明天修复建议：

- 给高优维修消息增加 `superseded_ack` 或 `closed_by_external_evidence`，允许 manager/Codex 用健康证据关闭，不要求原 worker 逐条 ACK。
- supervisor-check 对 read_without_ack 应结合后续 task/status/log/health 判断是否仍 live_blocker。
- 当 manager status 已声明“旧维修消息已 ACK 清理”但底层 ack_state 仍 pending，应判为 state sync bug，而不是继续阻塞。

### 85. manager 声称已核实 worker_builder 任务，但 worker_builder inbox 仍未读

触发原因：

- 用户在群里问：`切换备用模型不行吗？`
- manager 正确地把问题识别为 Qoder 额度耗尽后的备用模型/备用 CLI 问题，并派给 worker_builder 调查。
- 但短等后 worker_builder inbox 仍显示该高优任务未读，manager 随后又直接对外汇报“已核实全部 3 个 Qoder worker 现场”，形成“口头已核实”与 inbox 事实不一致。

现场证据：

- `eduflowteam inbox manager` 曾显示用户消息 `msg_1781997444619_203d5198c9`：`@EduFlow Team 切换备用模型不行吗？`
- manager status 显示：`收到。Qoder 额度耗尽后切换备用模型是正确思路，我先让 worker_builder 核实...`
- `eduflowteam inbox worker_builder` 显示高优任务 `msg_1781997483505_c37bd59166` 未读，内容要求调查 3 个 Qoder worker 是否支持运行时切换模型。
- `logs.jsonl` 随后出现 manager 对外汇报：`已核实全部 3 个 Qoder worker...全部卡在 Qoder API FORBIDDEN...qoder-cli 底层绑定 Qoder API...无法切换到其他模型...`

介入动作：

- Codex 记录本 gap。
- 本轮不再追加群内干预，因为 manager 的结论方向基本正确：Qoder 额度是 provider-level 阻塞，不能靠 qoder-cli 模型参数切到 Claude/GPT；真实方案是充值 Qoder 或切换到 claude-code/codex-cli 等其他 CLI/runtime。

临时结果：

- 老板问题已被 manager 回答，但 worker_builder 的实际调查任务仍存在未读/未 ACK 风险，后续 supervisor 可能继续报 inbox 卡点。

明天修复建议：

- manager 不应在下游 agent 未 ACK/未读时使用“已核实”表述；应说“基于当前 health/config 初判”，并等待 worker_builder 实测后再闭环。
- 对 runtime/provider 问题，manager 回答应分清三层：模型参数切换、CLI/provider 切换、agent runtime fallback。
- `runtime_guard` 的 `fallback_to` 配置已存在，但 Qoder CLI 卡在 provider 额度时，是否自动切到非 Qoder CLI 需要有实测闭环，而不能只看配置。
- worker_builder 高优调查任务如果无法执行，应由 manager/Codex 标记为 `blocked_by_same_provider_quota` 或改派 Claude Code 侧执行。

### 86. 备用模型调查任务被派给已知不可用的 Qoder worker，无法形成实测闭环

触发原因：

- manager 将“Qoder 额度耗尽后能否切备用模型”的调查任务派给 worker_builder。
- worker_builder 本身正是 Qoder CLI，pane 显示 Qoder API `FORBIDDEN code=112` / `Credits exhausted`，无法处理任何 prompt。
- 因此该调查任务无法由 worker_builder 自己完成，manager 的回答只能是二手判断，不能形成“下游实测闭环”。

现场证据：

- `eduflowteam inbox worker_builder` 仍显示 `msg_1781997483505_c37bd59166` 未读。
- `eduflowteam peek worker_builder` 显示多次 `Qoder API error: FORBIDDEN`、`Credits exhausted`，包括最新调查消息也无法处理。
- `eduflowteam status worker_builder` 显示仍停在旧的 `已读待确认` 状态，并未 ACK/started 最新调查任务。
- `task supervisor-check --json` 已识别：`delegated_task_answered_by_manager_but_worker_unread`，推荐 `clear_or_reassign_stale_delegation`。

介入动作：

- Codex 记录本 gap。
- 本轮不再追加群内消息，因为 manager 已给老板一个方向上可用的结论：qoder-cli 是 provider 级额度阻塞，不能靠 CLI 内模型参数切到 Claude/GPT；恢复方案是 Qoder 充值或切换到其他 CLI/runtime。

临时结果：

- 老板问题已得到可用解释，但系统内的 worker_builder 调查任务仍是 stale delegation。

明天修复建议：

- 当某个 worker 的 provider 已知不可用时，manager 不应再把“如何恢复该 provider/worker”的调查任务派给同一个 worker。
- 这类任务应自动路由给可用的 auto_ops / review_course / Codex / Claude Code 侧 builder。
- manager 的语言应区分“已实测”与“基于配置/错误信息推断”。
- runtime fallback 设计需要支持 provider-level failure 时跨 CLI 切换，而不是只在同一 CLI 内换模型名。

### 87. router pid 短暂 stale 后被 watchdog 自愈，health 与 supervisor anomaly 存在瞬时不一致

触发原因：

- 本轮 `eduflowteam health` 一度显示：`router: pid file present but process dead (watchdog will respawn)`。
- 随后 `task supervisor-check --json` 的 `supervisor_processes` 又显示 router alive=true，但 anomalies 中仍保留 `router_pid_stale`。

现场证据：

- `health` 输出 router stale warning，task-publish/watchdog alive。
- 同轮 `supervisor-check` 输出 `runtime_visibility_unhealthy`，evidence_summary 包含 `reasons=router_pid_stale router:pid=yes,alive=no ...`。
- 同一份 `supervisor-check` 的 `supervisor_processes` 又显示 router `alive=true`，说明 watchdog 已经在检查窗口内把 router 拉回。

介入动作：

- Codex 记录本 gap。
- 未手动重启 router，因为 watchdog 自愈已发生，当前 runtime 没有 hard failure。

临时结果：

- router 已恢复 alive，继续观察。

明天修复建议：

- supervisor-check 应区分“当前仍异常”与“本轮检测窗口内曾异常但已恢复”。
- `runtime_visibility_unhealthy` 在 final supervisor_processes 已恢复时应降级为 `runtime_self_healed_observed`。
- health/supervisor 输出应带时间戳，避免用户/manager误判为当前仍坏。

### 88. manager 在下一步未定时进入 idle，未自动挂起 workflow/默认可逆检查项

触发时间：2026-06-21 07:31 CST

触发原因：

- 老板指出“就停了”“一没有定就停了”“这个也是问题，一没盯”。
- 当前 4 个 IGCSE 学科内容生产已完成，但 manager 把后续推进收敛成等待老板选择 A/B/C，缺少默认可逆动作。
- 这会让团队在“下一学科未定 / QBank import 未授权 / manifest 残差未修”时安静停摆，而不是挂上 workflow、启动可逆盘点、保持反馈节奏。

现场证据：

- `eduflowteam task review-queue --reviewer review_course`：无待复核任务。
- `eduflowteam inbox manager/worker_course/worker_qbank/review_course`：无未读。
- `eduflowteam inbox worker_builder`：仍有备用模型调查 stale delegation 未读。
- `task supervisor-check --json` 返回 `health_status=soft_warning_observe`，`primary_reason=manager_idle_too_long`，`consecutive_issue_count=4`。
- manager 最近公开消息停在“建议下一步（请老板指定）：A 下一学科 / B manifest 修复 / C QBank import 授权”，没有把 B 类可逆检查或 workflow 挂起继续跑。

介入动作：

- Codex 记录本 gap。
- Codex 准备给 manager 一条低噪声内部指引：不要因下一学科未定让团队 idle；立即挂起 `igcse-subject-launch`/QBank/manifest 三条 workflow 状态板，并优先推进不需要额外授权的只读盘点、closeout 证据补齐、stale delegation 清理。

临时结果：

- 内容生产主链不是当前堵点；堵点是 manager 的“等待决策”状态没有转化成可执行的默认安全任务。

明天修复建议：

- manager 需要 `no-decision-idle-guard`：当老板未选下一学科时，自动进入“待决策但不空转”模式。
- 待决策模式默认动作：挂 workflow 状态板、每 15 分钟只读巡检、清理 stale delegation、补 closeout/manifest 证据、给 QBank 可见状态更新。
- manager 对用户提问时应同时给出“我已先做什么可逆动作”，而不是只等老板指定。
- supervisor 的 `manager_idle_too_long` 应能自动触发 manager 内部提醒或 auto_ops 指引，而不是只 observe。

### 89. `--no-inject` 高优消息进入 manager inbox 后未及时消费，暴露消息入口依赖注入的问题

触发时间：2026-06-21 07:32 CST

触发原因：

- Codex 为降低群内噪声，用 `eduflowteam send manager codex --stdin high --no-inject` 发出内部监控指引。
- 约 20-60 秒后，`eduflowteam inbox manager` 仍显示该高优消息未读。
- supervisor 同步识别 `high_priority_inbox_unread_blocking`，说明仅进入 inbox 不足以保证 manager 处理。

现场证据：

- 发送结果：`msg_1781998298997_7718140cf9`。
- `eduflowteam inbox manager` 仍显示 1 unread，高优消息内容完整存在。
- `task supervisor-check --json` anomaly：`category=high_priority_inbox_unread_blocking`，`agent=manager`，`recommended_action=consume_high_priority_inbox`。
- 同轮还出现过 `runtime_visibility_unhealthy/router_pid_stale`，随后 `health` 显示 router 已自愈为 alive，提示消息消费延迟可能与 router 瞬时抖动叠加。

介入动作：

- Codex 记录本 gap。
- Codex 改用正常注入方式再次给 manager 发送简短处理指引，避免 manager 因只看 pane 不扫 inbox 而继续 idle。

临时结果：

- `--no-inject` 适合降噪，但在当前 manager 消息口实现里不可靠；关键高优指令仍需要注入 pane 或由 supervisor 自动触发消费。

明天修复建议：

- 高优 inbox 消息应绕过普通 rollover 延迟，触发 manager 立即消费。
- `--no-inject` 不应等同于“静默且可能无人处理”；至少 manager 主循环要定期优先扫 high priority inbox。
- supervisor 发现 `high_priority_inbox_unread_blocking` 时，建议自动执行轻量注入/提醒或交给 auto_ops，而不是只 observe。
- manager pane 心跳健康不代表 inbox 消费健康，需要单独指标。

### 90. 三线只读盘点已启动，但 QBank readiness 被派给不可用 anna，导致状态板局部挂起

触发时间：2026-06-21 07:36 CST

触发原因：

- Codex 纠偏后，manager 不再 idle，并开始推进 `auto_ops / review_course / anna` 三线只读盘点。
- 但 manager 将 QBank import-readiness 检查派给 anna。
- anna 当前 tmux pane 环境异常，health 显示 `stale lazy pane`、`runtime_status_env_drift`，runtime guard 显示 `provider_unavailable`、`fallback_restart_failed`、`needs_manager_action=true`。
- 因此 QBank readiness 仍处于“待 anna 恢复后执行”，没有真正闭环。

现场证据：

- `logs.jsonl`：manager 外显 `auto_ops — 正在做 4 科 closeout 证据盘点 + 状态板`、`review_course — 正在做 Economics/Business manifest 缺口分析`、`anna — tmux pane 环境异常`、`QBank readiness 检查 — 待 anna 恢复后执行`。
- `eduflowteam health`：anna stale lazy pane，runtime guard `anna: failure=provider_unavailable ... outcome=switch_failed ... escalation=fallback_restart_failed`。
- `task supervisor-check --json`：`health_status=repair_needed`，`primary_reason=runtime_unhealthy`，并有 `high_priority_inbox_unread_blocking` for anna QBank readiness message。

介入动作：

- Codex 记录本 gap。
- Codex 准备给 manager 发低噪声纠偏：QBank readiness 不应等待 anna；改派可用 Claude Code 侧 agent，或由 manager/auto_ops 直接完成只读检查。

临时结果：

- manager idle 有所缓解，但 QBank 可见反馈仍未真正恢复。

明天修复建议：

- manager 派单前必须检查 agent runtime 可用性；不可用 agent 不应承接关键只读状态板任务。
- QBank readiness 是只读检查，应该允许 manager/auto_ops/Codex 兜底完成，不应绑定 anna。
- runtime guard 对 `needs_manager_action=true` 的 agent 应自动从候选 assignee 中剔除。
- QBank 状态板应有 owner fallback：primary 不可用时自动改派 secondary。

### 91. 三线状态板的“4 科 closeout 证据”任务口径写错，混入未完成/未运行学科

触发时间：2026-06-21 07:36 CST

触发原因：

- manager 给 auto_ops 的状态板任务要求核实 `Physics 0625 / Chemistry 0620 / Biology 0610 / Business Studies 0450` 四科 closeout。
- 但今晚已完成并复核的 4 科实际是：Accounting 0452、Economics 0455、Business Studies 0450、Physics 0625。
- Chemistry 0620 / Biology 0610 并非今晚已完成学科，Accounting/Economics 反而被漏掉。

现场证据：

- `facts/inbox.json` 中 manager → auto_ops 的高优任务内容：`只读盘点 4 科 closeout 证据：核实 Physics 0625 / Chemistry 0620 / Biology 0610 / Business Studies 0450...`
- manager 之前公开 closeout 总结反复确认实际 4 科为 `Accounting 315 / Economics 234 / Business 300 / Physics 414 = 1263 QA`。
- heartbeat prompt 与当前目标也明确记录已完成 4 科为 Accounting/Economics/Business/Physics。

介入动作：

- Codex 记录本 gap。
- Codex 将在给 manager 的纠偏里要求修正状态板学科名单，避免 auto_ops 按错误对象做证据盘点。

临时结果：

- 当前状态板已启动，但证据盘点对象存在事实偏差；如果不纠正，会产出无效或误导性的 closeout evidence。

明天修复建议：

- manager 发状态板/复核任务时，学科名单必须从 subject inventory 或 latest closeout summary 自动生成，不能手写。
- supervisor 应检测“任务对象不在已完成 subject list 中”的异常。
- closeout evidence 任务应带 authoritative source：subject code、qa count、review verdict、manifest path。

### 92. 三线只读盘点已有交付，但 status / inbox ACK / supervisor truth 未同步，导致 escalated_failure 持续

触发时间：2026-06-21 07:40 CST

触发原因：

- manager 已把 Codex 纠偏转派给 auto_ops，并要求修正状态板、完成 QBank readiness、补 review_course ACK。
- auto_ops 与 review_course 均已有可见交付，但系统状态与 supervisor anomaly 仍显示多个 blocker。
- 这说明当前不是单纯 agent 不干活，而是“交付事实”和“结构化 truth/ACK/status”之间没有闭环同步。

现场证据：

- `logs.jsonl`：
  - `auto_ops 完工：状态板已上墙；4科 closeout 证据盘点完成；worker_builder stale 派单清理建议已出；Hermes 07:36 告警为误报`
  - `review_course`: `只读盘点完成：Economics 缺 66 QA；Business 一致；Accounting 35/35 口径不一致 + 11 phantom topics + 难度碎片化`
  - `manager`: `QBank readiness 改派 auto_ops 直接完成，不等 anna`
- `.eduflow-team-state/facts/status.json`：
  - `auto_ops` 已显示待命 / 3项交付物已完工。
  - `manager` 仍显示“等交付”。
  - `worker_course` 仍停在旧 T-15 Batch 6 接单。
  - `worker_builder/worker_qbank` 仍是 initializing。
- `task supervisor-check --json`：
  - `health_status=escalated_failure`
  - 仍报 `auto_ops high_priority_inbox_read_without_ack`
  - 仍报 `anna high_priority_inbox_unread_blocking`
  - 仍报 `runtime_visibility_unhealthy/router_pid_stale`
  - 仍报 Qoder worker `runtime_blocked_provider_quota`

介入动作：

- Codex 记录本 gap。
- Codex 准备给 manager 发一条低噪声收口指令：先同步 status/truth/ACK，不要继续新派任务；把 auto_ops 3 项标记完成、review_course 盘点标记完成、QBank readiness 状态明确、worker_course 旧 T-15 状态清理为 stale/closed。

临时结果：

- 群内生态已能部分自修并产出报告，但监督层仍因 truth/ACK/status 不一致维持升级态。

明天修复建议：

- 每个高优 inbox 需要显式 ACK 状态机：accepted / started / completed / blocked，不能只靠 `say` 和 status 文本推断。
- manager 收到下游 `task_completed` 后必须同步自身 `waiting/doing/done` 状态，不能继续显示“等交付”。
- 已完成旧任务（如 worker_course T-15/T-18）应有 closeout 后自动清理状态，避免 status 误导巡检。
- supervisor 对“已有 task_completed 但 ACK 缺失”应给出 `ack_semantics_gap`，不要持续当 live blocker。
- router stale 若同轮 supervisor_processes 已 alive，应降级为 self-healed observed，避免 escalated_failure 噪声。

### 93. 同一高优消息已被 manager 执行并对外收口，但 inbox 仍显示未读，证明消息处理口与执行口分裂

触发时间：2026-06-21 07:42 CST

触发原因：

- Codex 给 manager 发送高优收口指令 `msg_1781998853313_7c9dc1e818`，要求做 truth/status/ACK 同步。
- manager 随后在群内/日志里完成了对应动作：确认 `3项纠正已交付`、状态板修正、QBank readiness 完成、review_course ACK 补认。
- 但 `eduflowteam inbox manager` 仍显示同一条 Codex 高优消息未读。
- supervisor 因此继续把该消息识别为 `high_priority_inbox_unread_blocking`，并将健康状态维持在 `escalated_failure`。

现场证据：

- `logs.jsonl`：
  - `log_1781998874128_13f9af4487`: manager `✅ 3项纠正已交付：1) 状态板口径已修正 2) QBank readiness 检查完成 3) review_course ACK 已补认。团队当前待命。`
- `eduflowteam inbox manager`：
  - 仍显示 `msg_1781998853313_7c9dc1e818` unread，内容正是 Codex 的 truth/status/ACK 收口指令。
- `task supervisor-check --json`：
  - `health_status=escalated_failure`
  - `consecutive_issue_count=3`
  - anomaly: `high_priority_inbox_unread_blocking` for manager `msg_1781998853313_7c9dc1e818`
- `.eduflow-team-state/facts/status.json`：
  - manager status 又变成 `responding to first message`，而不是稳定的 `待命/已收口`。

介入动作：

- Codex 记录本 gap。
- 本轮不再继续向 manager 发送重复催办，因为实际执行口已经完成；重复发消息只会制造更多 inbox 噪声。

临时结果：

- 业务动作已完成，但消息系统无法把“已处理/已读/已完成”同步回 inbox truth，导致 supervisor 误判或无法降级。

明天修复建议：

- agent pane 执行到某条 inbox 消息时，必须回写 `read=true` 和 `ack_state=completed/blocked`。
- supervisor 判断高优未读前，应检查是否已有后续日志满足该消息内容的验收条件；若满足，应降级为 `read_state_desync`，不应继续 `blocking`。
- manager 的 `responding to first message` 是模糊状态，应改成可追踪的 message id + stage。
- 需要增加 `inbox reconcile` 命令：基于日志和 status 自动把已执行消息标记为 reconciled，而不是长期污染 supervisor。

### 94. Codex 手动 reconcile 一条已执行的 manager 高优消息，避免 supervisor 被假未读持续污染

触发时间：2026-06-21 07:44 CST

触发原因：

- `msg_1781998853313_7c9dc1e818` 已被 manager 实际执行并在日志中完成收口。
- 但 inbox truth 仍显示该消息未读，supervisor 连续第 3 次将其作为 `high_priority_inbox_unread_blocking`。
- 继续给 manager 发催办会制造更多消息噪声，且不能修复 read-state 分裂。

现场证据：

- `logs.jsonl` 已有 manager 收口：`✅ 3项纠正已交付...团队当前待命。`
- `eduflowteam inbox manager` 仍显示该 Codex 高优消息 unread。
- `task supervisor-check --json` 显示 `consecutive_issue_count=3`，且 anomaly 包含 manager 该未读消息。
- 本地命令存在 `eduflowteam read <local_id>`，可精准标记单条消息为已读。

介入动作：

- Codex 记录本 gap。
- Codex 仅对 `msg_1781998853313_7c9dc1e818` 执行精准 `read`，不改 anna / worker_builder 的未读消息，因为后两者仍代表真实 runtime/stale delegation 问题。

临时结果：

- 预期 supervisor 不再把 manager 这条已执行消息作为未读 blocker。

明天修复建议：

- 增加正式 `inbox reconcile` 命令，语义区别于人工 `read`：它应保留“由监督层基于日志证明已处理”的证据。
- `read --ack` CLI 文档与实现不一致：实现支持 `failed_due_to_runtime`，help 未列出。
- 对已被日志证明完成的消息，应支持 `ack_state=completed/reconciled`，而不只能 accepted/started。

### 95. 下一步未指定时 manager 进入待命而不是自动挂载默认 workflow，导致主链停住并触发 idle 告警

触发时间：2026-06-21 07:55 CST

触发原因：

- Physics 0625 已完成整科 closeout，当前 4 科累计 1263 QA。
- 用户尚未指定下一门 IGCSE 学科，也未授权 QBank import/dedup。
- manager 在“等待老板新指令”状态下没有自动进入默认的安全 workflow，例如：
  - `igcse-subject-launch` 的候选学科预检；
  - manifest/inventory 只读盘点；
  - QBank readiness 只读检查；
  - supervisor/inbox truth reconciliation。
- Hermes/supervisor 因此持续报 `manager_idle_too_long`，证明“没定下一步”会让链条停住，而不是转入可逆的待办池。

现场证据：

- `.eduflow-team-state/facts/status.json`：
  - manager: `待命 / 收口4项已完成，等老板新指令`
  - review_course: `待命 / 三科 manifest 盘点完成，待新任务`
  - worker_course: 仍显示旧 T-15 任务，存在 truth drift。
- `eduflowteam task review-queue --reviewer review_course`：
  - `no tasks awaiting review`
- `eduflowteam inbox manager/auto_ops/review_course/worker_course/worker_qbank`：
  - 均无 unread。
- `eduflowteam task supervisor-check --json`：
  - `health_status=escalated_failure`
  - `auto_summary_reasons=[runtime_unhealthy, agent_failover_escalation, manager_idle_too_long]`
  - `recommended_action=trigger_supervisor_repair`

介入动作：

- Codex 记录本 gap。
- 本轮不再向群内追加公开状态，避免在无新生产任务时制造噪声。
- 继续 15 分钟巡检，若 manager 后续仍因 idle 被告警，再低噪声指引 manager 挂载默认 workflow。

临时结果：

- 业务生产没有新任务进行中；已有内容主链暂时闭合。
- 但系统层仍未闭合：下一步未定时缺少自动 fallback workflow，导致 supervisor 把待命状态识别为运行异常。

明天修复建议：

- 给 manager 增加 `no-next-subject fallback policy`：当下一学科/授权未定时，自动选择只读、可逆、低噪声 workflow，不要空等。
- workflow 需要从“建议文字”变成“状态机挂载”：例如 `subject-launch=waiting-for-decision`、`manifest-inventory=read-only-checking`、`qbank-readiness=needs-authorization`。
- supervisor 对“无待处理任务 + 无可授权动作”的待命应降级为 `waiting_for_user_decision`；但如果存在可逆默认 workflow 未执行，则保留 `manager_idle_too_long`。
- manager 每次 closeout 后应自动生成下一步候选队列，并明确哪些可自动推进、哪些必须等授权。

### 96. Qoder 额度耗尽后没有可靠切到备用 runtime，manager 误以为只能等充值或人工兜底

触发时间：2026-06-21 08:00 CST

触发原因：

- 用户明确提醒：`模型额度耗尽了记得切换模型`。
- 当前 3 个 Qoder worker（`worker_course` / `worker_builder` / `worker_qbank`）仍显示在 primary Qoder runtime：
  - `course_primary`: `qoderclicn / Qwen3.7-Max / provider=qoder`
  - `builder_primary`: `qoderclicn / Qwen3.7-Max / provider=qoder`
  - `qbank_primary`: `qoderclicn / Qwen3.7-Max / provider=qoder`
- `eduflow.toml` 已配置 fallback runtime 链，但实际运行状态没有把 quota/provider failure 稳定切走：
  - `course_primary -> course_backup_deepseek -> course_backup_qwen_plus`
  - `builder_primary -> builder_backup_deepseek -> builder_backup_qwen_plus`
  - `qbank_primary -> qbank_backup_deepseek -> qbank_backup_qwen_plus`
- manager 之前多次把 Qoder quota 描述成“需充值或 Codex 兜底”，说明 runtime fallback 没有变成默认自动动作。
- 需要区分“切模型”和“切 runtime”：Qoder API 额度耗尽是 provider-level failure，不能只改 model name；必须切到可用 CLI/provider，例如 `claude-code` 的 deepseek/qwen_plus runtime，或 codex runtime。

现场证据：

- `eduflowteam health`：
  - `worker_builder: runtime=builder_primary provider=qoder model=Qwen3.7-Max`
  - `worker_course: runtime=course_primary provider=qoder model=Qwen3.7-Max`
  - `worker_qbank: runtime=qbank_primary provider=qoder model=Qwen3.7-Max`
- `.eduflow-team-state/facts/runtime-status.json`：
  - 三个 worker 均仍在 primary Qoder runtime。
- `.eduflow-team-state/facts/runtime-guard-state.json`：
  - `worker_builder` 曾记录 `rate_limit -> auto_switched_recovered`，但 runtime-status 又回到 `builder_primary`，存在 guard truth / live runtime 不一致。
- `eduflow.toml`：
  - fallback 链存在；
  - `runtime_guard.manager_policy.worker_course = "pause"`、`worker_qbank = "pause"`，这会让生产线遇到 runtime failure 时偏向暂停，而不是继续 fallback。
- `logs.jsonl`：
  - manager 多次输出 `Qoder API FORBIDDEN code=112 / Credits exhausted`；
  - manager 结论多为“需充值或 Codex 兜底”，而不是自动切换并继续生产。

介入动作：

- Codex 记录本 gap。
- 本轮不直接修改 runtime 配置，避免在今晚无新生产任务时扩大变量。
- 后续监控若再出现 quota/rate-limit/provider failure，会优先提醒 manager：先走备用 runtime/CLI，不要把“等充值”当成唯一下一步。

临时结果：

- 当前无新生产任务，所以没有立即切 runtime 的业务压力。
- 但明天必须修复：额度耗尽应自动触发 runtime fallback，且 manager 文案必须从“等充值/等老板”改成“已切备用 runtime / 若切换失败才升级”。

明天修复建议：

- 将 quota/rate-limit/provider failure 统一归一为可自动 fallback 的 runtime signal。
- 对 `worker_course` / `worker_qbank` 这类生产线，不要在第一次 provider quota failure 就 `pause`；应先尝试 `fallback_to` runtime，全部失败后才升级给 manager。
- runtime-status 必须与 runtime-guard-state 对齐：如果 guard 记录已切换，health/status 不能继续显示 primary qoder。
- manager 收到 Qoder quota blocker 时的默认指引应是：
  - 第一步：切备用 runtime/CLI；
  - 第二步：验证 pane ready 和最小 smoke；
  - 第三步：恢复原任务或改派可用 agent；
  - 第四步：只有全部 fallback 失败才要求充值/人工介入。
- 在健康检查中增加 `provider_quota_exhausted_but_fallback_available` 的专门 anomaly，避免它被泛化成普通 `runtime_unhealthy`。

### 97. subject-launch 缺少 IGCSE 跨学科轮转策略，导致 Physics 连续占满 T-11 到 T-18

触发时间：2026-06-21 08:03 CST

触发原因：

- 用户指出：`学科为什么反复都是物理呢，其他igcse学科也有啊`。
- 当前任务系统中，T-11 到 T-18 连续 8 个正式 `igcse-subject-launch` 任务都是 Physics 0625 Batch 2-9。
- Physics 0625 已完成整科 closeout（46 topics / 414 QA），但 manager 后续仍没有自动回到 IGCSE 学科池选择下一学科。
- content 目录中实际已有多门 IGCSE 学科资产，不是只有 Physics：
  - `igcse-accounting-0452`
  - `igcse-biology-0610`
  - `igcse-business-studies-0450`
  - `igcse-chemistry-0620`
  - `igcse-economics-0455`
  - `igcse-mathematics-0580`
  - `igcse-physics-0625`
- 说明 subject-launch 当前只会沿着“当前学科 full outline”继续批次推进，但缺少“学科级 backlog / round-robin / completed-subject lock”。

现场证据：

- `eduflowteam task list`：
  - T-6: Chemistry 0620 首批 topic+QA 已完成；
  - T-7: Accounting 0452 已完成；
  - T-9: Economics 0455 已完成；
  - T-10: Business Studies 0450 已完成/但 structured verdict 仍漂移；
  - T-11 到 T-18: 全部是 Physics 0625 Batch 2-9。
- `find content -maxdepth 2 -type d`：
  - 已有 Biology / Chemistry / Mathematics 等 IGCSE 目录。
- 文件计数：
  - `content/igcse-biology-0610`: `items=74`, `qa-question-level=300`
  - `content/igcse-chemistry-0620`: `qa=34`, `items=64`, `qa-question-level=305`
  - `content/igcse-mathematics-0580`: `qa=24`, `items=34`, `qa-question-level=300`
  - `content/igcse-physics-0625`: `qa=46`, `items=53`, `qa-question-level=414`
- `qbank-dedup-dryrun-plan-v3.md` 也显示 QBank 侧已有 Chemistry / Biology / Mathematics 等非 Physics 数据线索。

介入动作：

- Codex 记录本 gap。
- Codex 将低噪声指引 manager：下一次 subject-launch 不要继续 Physics；应从未正式 subject closeout 或需要补齐/复核的 IGCSE 学科池中选择，例如 Chemistry 0620、Biology 0610、Mathematics 0580。

临时结果：

- Physics 已完成，不应继续作为默认学科。
- 当前没有用户指定下一学科，manager 应至少维护候选学科队列，而不是空等或回到 Physics。

明天修复建议：

- 增加 `igcse_subject_backlog` 状态表，字段至少包括：subject_slug、exam_code、status、qa_count、review_status、qbank_readiness、next_action、last_touched_at。
- `igcse-subject-launch` closeout 后自动执行 `select_next_subject`：
  - 排除已 subject closeout 的学科；
  - 优先有资产但未正式 closeout 的学科；
  - 优先有 QBank/manifest 缺口且可只读推进的学科；
  - 避免同一学科连续占用超过一个 subject closeout 周期。
- manager 汇报下一步时必须列出非 Physics 候选，并说明为什么推荐某一门，而不是只说“等老板指定”。
- supervisor 增加 `subject_rotation_stalled` anomaly：当上一个 subject 已 closeout 且存在其他 IGCSE candidate，但 manager 没有生成下一学科候选队列时触发。

### 98. Codex 手动将 3 个 Qoder worker 切到 claude-code + qwen3.7-plus，先保证今晚可运转

触发时间：2026-06-21 08:06 CST

触发原因：

- 用户明确要求：`你先帮忙切换模型切Claude code➕qwen3.7 plus`，并补充 `保证好运转先`。
- Qoder worker 之前持续受 `Qoder API FORBIDDEN code=112 / Credits exhausted` 影响。
- 自动 runtime fallback 没有稳定触发，见 gap 96。
- 今晚继续监控/后续新学科或 QBank 任务需要先恢复可用 worker runtime。

介入动作：

- Codex 没有改 `eduflow.toml`，而是用项目内 `lifecycle.restart_with_runtime()` 对现有 tmux pane 做受控 hard-switch。
- 第一次尝试直接 `python3` 导入时命中已安装旧版 `eduflow` 包，没有 `restart_with_runtime`，失败原因是 Python import path 不指向当前项目源码。
- 第二次用 `PYTHONPATH="$PWD/src"` 强制加载当前项目源码后成功切换：
  - `worker_course -> course_backup_qwen_plus`
  - `worker_qbank -> qbank_backup_qwen_plus`
  - `worker_builder -> builder_backup_qwen_plus`

现场证据：

- 切换命令返回：
  - `worker_course  course_backup_qwen_plus  ready`
  - `worker_qbank   qbank_backup_qwen_plus   ready`
  - `worker_builder builder_backup_qwen_plus ready`
- `eduflowteam health`：
  - `worker_builder: pane ready (claude-code) runtime=builder_backup_qwen_plus provider=anthropic-proxy model=sonnet`
  - `worker_course: pane ready (claude-code) runtime=course_backup_qwen_plus provider=anthropic-proxy model=sonnet`
  - `worker_qbank: pane ready (claude-code) runtime=qbank_backup_qwen_plus provider=anthropic-proxy model=sonnet`
- `.eduflow-team-state/facts/runtime-status.json`：
  - 三个 worker 的 `env_profile` 均为 `claude_proxy_primary`；
  - 该 profile 在 `eduflow.toml` 中对应 `ANTHROPIC_MODEL=qwen3.7-plus` / `ANTHROPIC_DEFAULT_SONNET_MODEL=qwen3.7-plus`。

临时结果：

- 3 个原 Qoder worker 已恢复到 `claude-code + qwen3.7-plus` 画像。
- 当前没有新 review queue，也没有 worker_course/worker_qbank 新 unread，所以未立即派新任务。
- `worker_builder` 仍有一条旧高优未读，内容正是“调查能否切备用模型”。本轮先保留，作为明天消息处理口/旧 delegation reconcile 的证据；若 supervisor 继续把它误判为 live blocker，再单独 reconcile。

明天修复建议：

- `eduflowteam` CLI 应提供正式命令，例如 `eduflowteam runtime switch worker_course course_backup_qwen_plus --reason quota_exhausted`，不要依赖 Codex 手写 Python 调内部 API。
- runtime hard-switch 成功后应自动清理或 reconcile 相关旧 delegation，避免“已切换成功但旧调查消息仍 unread”。
- health 显示 `model=sonnet` 容易误导；应同时显示 live env model（例如 `ANTHROPIC_DEFAULT_SONNET_MODEL=qwen3.7-plus`），否则用户看不到“Claude Code + qwen3.7-plus”是否真的生效。

### 99. Codex 直接扶正学科线：停止 Physics 循环，指定下一门启动 Chemistry 0620

触发时间：2026-06-21 08:10 CST

触发原因：

- 用户连续指出：`还有扶正，继续其他的学科的，别一直`、`别一直兜圈子，选一个学科新开始`。
- Physics 0625 已整科 closeout，不应继续作为默认 subject-launch 目标。
- 其他 IGCSE 学科已经存在资产，其中 Chemistry 0620 已有首批 topic/QA 资产，但没有形成 Physics 那样完整的 subject closeout 链。

介入动作：

- Codex 记录本 gap。
- Codex 直接指定下一门：`IGCSE Chemistry 0620`。
- Codex 给 manager 发高优内部指令：立刻启动 Chemistry 0620 的 `igcse-subject-launch`，不要再候选讨论，不要再绕回 Physics；先做 current truth audit，再派 worker_course 产出下一批/补齐 QA，随后交 review_course 复核，最终由 manager closeout。

临时结果：

- 学科线从 Physics 切到 Chemistry。
- 后续巡检重点改为：Chemistry 0620 是否真实进入 `topic -> QA -> review -> manager closeout` 链条。

明天修复建议：

- manager 不应在“下一学科”问题上只给候选项；当用户要求推进时，必须直接选一个学科并启动 workflow。
- subject selector 应持久化最后完成学科，避免刚 closeout 的学科再次进入默认队列。

### 100. Codex 按用户反馈将 auto_ops 外显卡片从粉色改为红色

触发时间：2026-06-21 08:14 CST

触发原因：

- 用户明确要求：`auto外显的颜色改一下改成红色`。
- 前一轮临时颜色分工中 `auto_ops` 被设为 `pink`，但今晚群内消息较多，auto 作为异常/盯盘/告警 lane 更适合用红色强化识别。

介入动作：

- Codex 修改 `eduflow.toml`：
  - `team.agents.auto_ops.card_color: pink -> red`

临时结果：

- 后续通过 `eduflow say auto_ops ...` 发出的 Feishu v2 卡片 header 应使用红色。
- 这次只改运行配置，没有改消息链路、workflow 或 agent runtime。

明天修复建议：

- agent 外显颜色最好沉为一张稳定表，并在 `/team` 或 `/health` 中展示，避免今晚这种靠口头记忆调整。
- 若 `auto_ops` 以后退回低频 watcher，可再评估是否从红色降为 grey/turquoise，避免和真正告警卡抢视觉权重。

### 101. Codex 介入 Chemistry 0620 阶段2节奏：要求小包送审，避免修补阶段憋大包空转

触发时间：2026-06-21 08:19 CST

触发原因：

- Chemistry 0620 已启动，worker_course 完成 truth audit，并发现真实质量缺口：305 items/QQL、无 qa-manifest、Challenge 严重不足（C=6，目标约 C=102）、17 topics <9 items。
- worker_course 阶段2已经开始补文件，现场可见新增 `3-3-empirical-molecular-formulae` 的 5 个 QQL 和补充 items。
- 但 review queue 仍为空；如果继续等全科一次性修完，`topic -> QA -> review -> manager closeout` 链条会在 review 环节空转。

介入动作：

- Codex 不接管内容生产，只给 manager 发高优短指令：
  - 要求 Chemistry 0620 阶段2按“小包”推进；
  - 第一小包先覆盖 `3.3` 及后续 2-3 个缺 Challenge 的 topic；
  - 每包交付后立即送 review_course，不等全科修完；
  - manager 只收最小进度包，避免刷屏。

临时结果：

- 目标是让 Chemistry 修补从“长时间内部生产”切回可观察的 production-review 节奏。
- 这次不改文件、不直接生成 Chemistry 内容，保留 worker_course 作为内容 owner。

明天修复建议：

- `igcse-subject-launch` workflow 需要内置 `repair_batch_size`，当 truth audit 发现全科缺口时，自动拆成 2-5 topics 的 reviewable 小包。
- supervisor 应在“worker 正在修补但 review_queue 为空超过阈值”时提示 manager 切小包，而不是只报 manager idle/runtime unhealthy。
- runtime/health 与实际 tmux pane 枚举存在漂移：`health` 认为多 agent pane ready，但 `tmux list-panes -t EduFlowTeam` 只看到 hermes_supervisor；需要明天单独查 tmux session/window 名称或旧 runtime_status 残留。

### 102. Chemistry 0620 小包指令未被 worker_course 消费，内容生产继续跨 topic 发散但 review queue 为空

触发时间：2026-06-21 08:25 CST

触发原因：

- Codex 先前要求 manager 将 Chemistry 0620 阶段2切成 2-3 topics 小包滚动送审。
- manager 已消费并外显确认小包策略，同时向 worker_course 发出高优消息 `msg_1782001124228_b118802a80`。
- 巡检发现：
  - `worker_course inbox` 仍有该高优消息未读；
  - `review_course inbox` 为空，`review-queue` 为空；
  - 文件系统已经新增大量 Chemistry 修补文件，范围跨 `1.1/2.2/3.1/3.3/6.x/7.x/8.x/9.x/11.4` 等多个 topic，而不是只停在小包#1 的 2-3 topics。

介入动作：

- Codex 记录本 gap。
- 下一步准备给 worker_course 直接发更短、更硬的收束指令：
  - 立即暂停继续扩散；
  - 先把已改动里最小可审范围（建议 3.3 + 3.1 + 2.2）汇总成小包#1；
  - 回 manager 并送 review_course；
  - 未读旧消息保留作为“消息处理口未及时消费”的证据。

临时结果：

- 证明 Chemistry 内容生产本身在动，但消息处理/小包节奏没有稳定落地。
- 该问题会导致 review 环节空转，并让 manager 以为已经切小包，但 worker 实际仍按大范围修补。

明天修复建议：

- worker 收到新高优消息时，需要有“抢占当前长任务并重读 inbox”的硬规则；否则生产中途的纠偏指令会排队失效。
- workflow 应支持 `interrupt_and_checkpoint`：将当前已产出的最小可审单元冻结、登记、送 review，再继续后续生产。
- supervisor 增加 `worker_unread_instruction_but_files_changed` anomaly：当 worker 有未读高优消息且同一范围文件仍在变化，应提示“未消费新指令仍在执行旧计划”。

### 103. Codex 冻结 Chemistry 0620 已产出小包#1 并直接送 review_course，恢复 QA -> review 链条

触发时间：2026-06-21 08:23 CST

触发原因：

- worker_course 现场已经看到了 Codex 的收束消息提示，但仍表示“先生成 qa-manifest.csv 和 final verification，再处理新 inbox”。
- 两条高优小包指令仍未读，review queue 仍为空。
- 文件系统继续产生新的 Chemistry 修补文件，且范围已经扩到 `9.2/10.1` 等 topic，说明“先小包送审”的节奏没有自然生效。
- 如果继续等待 worker_course 自行处理 inbox，review_course 会继续空转，manager 也无法获得 PASS/返修信号。

介入动作：

- Codex 不修改 Chemistry 内容，只冻结现有已产出文件中的最小可审包：
  - `3.3 Empirical and molecular formulae`
  - `3.1 Formulae, equations and mole`
  - `2.2 Periodic table and configuration`
- Codex 直接向 review_course 发高优复核请求，要求文件级检查：
  - items/QQL 是否对齐；
  - 是否达到 9 items/topic 或明确记录缺口；
  - Challenge 是否真实增加；
  - 文件命名是否存在 `ss2` / `s16` 等异常后缀；
  - 给出 PASS / MINOR / RETURN verdict。

临时结果：

- 先恢复 `QA -> review` 链条，不再让 review_course 只待命。
- 保留 worker_course 未读消息作为“长任务期间无法抢占处理新指令”的证据。

明天修复建议：

- 应提供 CLI 命令 `eduflowteam task checkpoint-review --subject chemistry-0620 --topics 3.3,3.1,2.2`，由系统冻结文件清单、生成 review task、更新状态，而不是靠 Codex 手工发消息。
- review_queue 不应只依赖结构化 task；当 manager/codex 明确发送 review 请求时，也应能形成可见 queue entry。

### 104. Chemistry 小包#1 NEEDS_FIX 后 manager 未自动派返修，链条停在 verdict -> rework 之间

触发时间：2026-06-21 08:27 CST

触发原因：

- review_course 已给出 Chemistry 0620 小包#1 verdict：`NEEDS_FIX`。
- 复核结论清晰：`2.2` 和 `3.1` 难度分布偏离目标（Foundation 偏多），`3.3` 达标。
- manager 状态更新为“小包#1 review中 / 等最终verdict”，但没有向 worker_course 派发返修消息。
- worker_course inbox 为空，意味着返修没有进入执行口。

介入动作：

- Codex 记录本 gap。
- 下一步给 manager 发短指令：
  - 立即将小包#1返修派给 worker_course；
  - 只修 `2.2` 和 `3.1` 难度分布，不碰 `3.3`；
  - 返修完成后必须回 review_course 复检；
  - 小包#1 PASS 前禁止启动小包#2。

临时结果：

- 该 gap 定位在 `review verdict -> manager rework dispatch`，不是内容生产问题。

明天修复建议：

- manager workflow 需要把 `NEEDS_FIX / MINOR / RETURN` verdict 自动转成 worker_course rework task，而不是只更新状态。
- supervisor 应增加 `verdict_needs_fix_without_rework_dispatch` anomaly：review verdict 出现后，如果 worker inbox 没有返修任务，应提示 manager 派返修。
- supervisor 的 Qoder runtime blocker 仍用旧 manager 日志做 live blocker，已与当前 worker_course 实际产出/送审矛盾；需要加入 runtime switch 后的 stale blocker reconciliation。

### 105. 外显层仍不同步：真实返修在动，但状态/监督/群可见口径仍让老板看不清

触发时间：2026-06-21 08:31 CST

触发原因：

- 用户明确反馈：`外显问题`，说明虽然链条内部有推进，但群内/状态面板仍没有给出足够清晰、可信的外显。
- 当前现场证据：
  - worker_course 现场正在处理 Chemistry 0620 小包#1 返修（2.2/3.1 难度分布），但 `status.json` 中 worker_course 仍显示“小包#1 送审中，待 review 后继续小包#2”，没有同步到“返修中”。
  - manager 已发过返修派单外显，但没有形成稳定的“当前唯一真相卡片”：小包#1 NEEDS_FIX -> 2.2/3.1 返修中 -> 3.3 不动 -> PASS 前不启小包#2。
  - supervisor 仍把旧 Qoder quota 日志判为 `live_blocker`，同时出现 `runtime_visibility_unhealthy/router_pid_stale`，这会继续误导外显。
  - review queue 仍为空，即使 review/返修链路实际通过 inbox/log 在跑，说明结构化队列和真实协作流仍断开。

介入动作：

- Codex 记录本 gap。
- 下一步做两件低风险外显修正：
  - 要求 manager 发一条低噪声、准确状态：只说明 Chemistry 小包#1 当前处于返修中，不启小包#2，等复检。
  - 核查 router/watchdog 健康；若 router stale 属实，优先重启/修复外显通道，而不是继续刷消息。

临时结果：

- 将问题从“内容是否在做”明确收敛为“外显状态同步/监督真相/队列可见性”问题。

明天修复建议：

- 增加 `visible_truth_snapshot`：由 manager 或 auto_ops 每个阶段只维护一条当前真相，不允许 status/log/supervisor 各说各话。
- `worker_course status` 应由返修任务 ACK 自动改成 `返修中`，返修完成后再变 `待复检`。
- supervisor 必须区分 stale historical blocker 与 live blocker；若 runtime-status 已切换成功且 worker 有新产出，旧 Qoder quota 日志不能继续标 live blocker。
- review_queue 应能从 inbox/log 的 review request 和 verdict 推导出“复核中/已返修/待复检”，不能只靠结构化 task。

### 106. Chemistry 返修完成后“已送复检”只出现在日志，review_course inbox 为空，Codex 手动补外显与复检入口

触发时间：2026-06-21 08:33 CST

触发原因：

- worker_course 已发出日志：`Chemistry 0620 小包#1 返修完成：2.2 和 3.1 难度已调至 F:2|S:4|C:3，3.3 不变。已送 review_course 复检，等待 verdict。`
- 但现场核查发现：
  - `review_course inbox` 为空；
  - `review_course status` 仍停在“NEEDS_FIX 已回报，待修正后复检”；
  - `worker_course status` 仍停在“小包#1 送审中”，未体现“返修完成待复检”；
  - manager 未发出用户需要的低噪声唯一真相。

介入动作：

- Codex 手动同步外显状态：
  - `worker_course`: Chemistry 小包#1 返修已完成并送复检，等待 verdict，PASS 前不启小包#2。
  - `review_course`: Chemistry 小包#1 复检待确认，复核 2.2/3.1 返修后结果，3.3 不动。
- 下一步补发 review_course 复检请求，确保复检入口不是只靠日志推断。

临时结果：

- 外显状态从“返修前”拉回到“返修完成待复检”。
- 暴露出“say/log 已说已送，但 inbox/review_queue 没有任务”的断层。

明天修复建议：

- worker_course 的“已送 review_course”必须真正创建 inbox/review task，不能只发 say。
- status 更新应绑定任务阶段转移：返修完成时自动把 worker_course/status 改为 `待复检`，review_course/status 改为 `复检中/待复检`。
- 增加 `claimed_sent_to_review_but_no_review_inbox` anomaly。

### 107. Chemistry 小包#1已清理且小包#2已启动，但外显状态仍停在旧阶段

触发时间：2026-06-21 08:38 CST

触发原因：

- 用户继续反馈：`外显问题`。
- 现场核查发现：
  - `worker_course inbox` 已无未读，说明 manager 的“小包#1 MINOR PASS，清理 orphan + 启动小包#2”指令已被消费。
  - `find content/igcse-chemistry-0620 -type f -name '*s20*'` 无输出，说明 review_course 报告的 10 个 `-s20` 孤儿残留大概率已清理。
  - `worker_course` live pane 显示：`Orphans cleaned. Now starting 小包#2 — picking 3 worst C=0 topics: 5.1, 4.1, 6.2.`
  - 但 `status.json` 中 `worker_course` 仍显示“小包#1 返修已完成并送 review_course 复检，等待 verdict；PASS 前不启小包#2”，与真实进度矛盾。
  - `review_course` 仍显示“小包#1 MINOR，待小包#2 或清理后确认”，没有形成“orphan 已清理，待最终 PASS/或随小包#2送审”的外显。

介入动作：

- Codex 记录本 gap。
- 下一步同步结构化状态：
  - `worker_course`: 小包#1 orphan 已清理，小包#2 生产中，范围 `5.1 / 4.1 / 6.2`。
  - `review_course`: 小包#1 core PASS，orphan 已清理待最终确认，等待小包#2送审。
  - `manager`: 当前唯一真相为“小包#1 cleanup 已执行，小包#2 生产中”，不要继续展示“PASS 前不启小包#2”的旧状态。

临时结果：

- 将外显问题从内容链路卡顿，定位为 `live pane -> status.json -> group visible truth` 同步延迟。

明天修复建议：

- `worker_course` 消费高优消息并产生 live progress 后，应自动刷新 `status.json`，避免用户看到旧阶段。
- `find`/文件事实和 review verdict 应能自动推动小包状态：`MINOR -> cleanup_confirmed -> PASS_pending_review_confirmation`。
- manager 的“当前唯一真相”应由状态事实生成，而不是靠上一条人工话术延续。

### 108. 小包#2 PASS 后 manager 已派小包#3，但 worker_course 结构化状态仍停在旧 verdict

触发时间：2026-06-21 08:47 CST

触发原因：

- Chemistry 小包#2 经 review_course 返修复检 PASS，manager 已外显：`小包#1 + #2 均通过，已派 worker_course 启动小包#3`。
- `worker_course` live pane 显示已收到并 ACK `manager -> worker_course msg_1782002823019_5987370120`，正在处理小包#3。
- 但 `status.json` 中 `worker_course` 仍显示：`Chemistry 0620 小包#1+2 返修已送检，等待 review verdict`，与真实进度矛盾。
- 这不是生产阻塞，但会让外显看起来又停在旧阶段。

介入动作：

- Codex 记录本 gap。
- 下一步只同步结构化状态：
  - `worker_course`: Chemistry 小包#3 生产中，小包#1+#2 已 PASS。

临时结果：

- 链条继续健康推进：小包#3 已由 manager 派发且 worker_course 已消费。

明天修复建议：

- review PASS -> manager closeout -> next package dispatch 后，应自动刷新 worker/status，不能只更新 manager/status。
- 增加 `next_task_dispatched_but_worker_status_stale` anomaly：当 worker 已 ACK 新任务但 status 仍等待旧 verdict，应提示或自动修正。

### 109. Chemistry 小包#4 生产自检卡在 retry，且 QQL 数量/难度分布未收敛

触发时间：2026-06-21 09:00 CST

触发原因：

- worker_course 已消费小包#4（范围 `7.2 / 7.3 / 8.1`），但 live pane 多次显示命令 retry，最高观察到 attempt 9/10，未正常完成送审。
- 只读核查发现当前小包#4 QQL 状态未达标：
  - `7.2`: 9 个 QQL，但难度为 `F:3|S:4|C:2`，目标应为 `F:2|S:4|C:3`。
  - `7.3`: 9 个 QQL，但难度为 `F:3|S:4|C:2`，目标应为 `F:2|S:4|C:3`。
  - `8.1`: 13 个 QQL，难度为 `F:6|S:7|C:0`，目标应为 9 个 QQL 且 `F:2|S:4|C:3`。
- 这属于生产自检未收敛，不应继续等待自然推进，否则会拖住 topic -> QA -> review 链路。

介入动作：

- Codex 记录本 gap。
- 下一步给 worker_course 发收敛指令：
  - 小包#4 只处理 `7.2 / 7.3 / 8.1`；
  - 每 topic 必须收敛到 9 QQL；
  - 难度必须为 `F:2|S:4|C:3`；
  - 8.1 必须删除/归档多余 4 个 QQL 并补足 3 个 Challenge；
  - 完成后立即送 review_course，不扩展新 topic。

临时结果：

- 将小包#4卡点从“worker在忙”明确为“数量与难度未收敛 + 命令重试卡住”。

明天修复建议：

- worker_course 生产脚本应在提交前强制运行 per-topic count/difficulty gate，失败时给出具体差异并停止，不应进入无意义 retry。
- 小包生产 workflow 需要内建 `exactly_9_qql_per_topic` 和 `F2_S4_C3` gate。
- 对 `8.1` 这类已有 13 个旧 QQL 的 topic，需提供标准 cleanup/replace 策略，避免保留旧残留进入 review。

### 110. worker_course 执行口被旧 retry 占住，无法消费最新高优收敛指令

触发时间：2026-06-21 09:02 CST

触发原因：

- Codex 已向 worker_course 发送高优收敛指令 `msg_1782003406474_b749aa99c6`，要求小包#4 只处理 `7.2 / 7.3 / 8.1` 并收敛到 `9 QQL + F:2|S:4|C:3`。
- 60 秒后核查：
  - `worker_course inbox` 仍显示该消息未读；
  - live pane 虽然显示收到消息提示，但仍被旧命令 retry 占住；
  - 文件状态无变化：`7.2 F:3|S:4|C:2`、`7.3 F:3|S:4|C:2`、`8.1 13 QQL F:6|S:7|C:0`。
- 这说明不是单纯内容返修问题，而是执行口/消息消费口被旧 retry 卡住，高优纠偏进不去。

介入动作：

- Codex 记录本 gap。
- 下一步要求 manager/runtime 层先恢复 worker_course 消息消费：
  - 中断旧 retry；
  - 立即处理 `msg_1782003406474_b749aa99c6`；
  - 返修小包#4；
  - 完成后送 review_course。

临时结果：

- 将问题从“小包#4未达标”升级定位为“agent 消息处理口被旧任务阻塞”。

明天修复建议：

- agent runner 需要支持高优消息抢占/取消旧 retry，不能让旧命令无限占住执行口。
- 对 retry 超过阈值的任务，应自动暂停当前命令并重新读取 inbox。
- supervisor 应增加 `high_priority_message_visible_but_unread_due_to_active_retry` anomaly。

### 111. Codex 亲自修复 Chemistry 小包#4，因 worker_course 收敛后仍跑偏且文件未变化

触发时间：2026-06-21 09:08 CST

触发原因：

- worker_course 最终消费了高优收敛指令，但又被 manager 后续消息和泛化目录检查带偏，没有实际修改小包#4 文件。
- 再次核查时小包#4 仍保持旧状态：
  - `7.2`: `F:3|S:4|C:2`
  - `7.3`: `F:3|S:4|C:2`
  - `8.1`: 13 QQL，`F:6|S:7|C:0`
- 若继续等待，topic -> QA -> review 链路会停在小包#4，且 worker_course 已经出现多轮 retry/跑偏。

介入动作：

- Codex 亲自修复小包#4内容：
  - `7.2`: 将 Q-7.2-05 从 Foundation 改写为 Challenge，保持 9 QQL，分布变为 `F:2|S:4|C:3`。
  - `7.3`: 将 Q-7.3-03 从 Foundation 改写为 Challenge，保持 9 QQL，分布变为 `F:2|S:4|C:3`。
  - `8.1`: 删除多余 `q10-q13` 与 `8-1-s3-items.md`，将 Q-8.1-06/Q-8.1-08/Q-8.1-09 改写为 Group 1 metals 主题 Challenge，最终 9 QQL，分布 `F:2|S:4|C:3`。
- 已运行只读核查：
  - `7-2 9 {'Foundation': 2, 'Standard': 4, 'Challenge': 3, 'unknown': 0}`
  - `7-3 9 {'Foundation': 2, 'Standard': 4, 'Challenge': 3, 'unknown': 0}`
  - `8-1 9 {'Foundation': 2, 'Standard': 4, 'Challenge': 3, 'unknown': 0}`
- 下一步送 review_course 复核。

临时结果：

- 小包#4 已从卡住状态恢复到可复核状态。

明天修复建议：

- 小包生产 worker 需要在本地完成硬 gate 后才能说“送审”，且遇到高优收敛指令不能再跑泛化目录检查。
- manager 后续消息不应打断 worker_course 正在处理的高优收敛任务。
- 需要引入“收敛任务锁”：同一小包收敛期间，禁止新派/泛化/状态类消息插队。

### 112. Chemistry 小包#4 内容已回正但 8.1 外显 guide/topic-outline 仍停留旧口径

触发时间：2026-06-21 09:17 CST

触发原因：

- review_course 对小包#4 给出 `MINOR`：`7.2/7.3/8.1` 的 items 与 QQL 数量、难度、主题内容均已达标，但 `8.1` 的 qa/guide 或标题口径仍残留旧的 `Periodic trends`。
- Codex 核查发现：
  - `qa/8-1-periodic-trends.md` 文件标题已改为 `Group 1 metals`，但 Topic 定义、关键知识点、常见错误、出题方向仍是泛化 periodic trends 内容。
  - `topic-outline.md` 中 `8.1` 仍写作 `Periodic trends: groups and periods`。
- 这会造成“文件内容正确，但外显状态/guide/outline 仍显示旧任务”的误导，属于今晚反复出现的外显真相滞后问题。

介入动作：

- Codex 亲自修正 8.1 外显口径：
  - 将 `qa/8-1-periodic-trends.md` 的定义、知识点、常见错误、出题方向统一改为 Group 1 metals。
  - 将 `topic-outline.md` 的 8.1 名称改为 `Group 1 metals`。
- 保持已经通过复核的 QQL/items 内容不再扩写，避免引入新变量。
- 修正后重新跑 `8.1` 残留关键词与数量/难度核查，并送 review_course 复检。

临时结果：

- 小包#4 的内容真相与外显 guide/topic-outline 已对齐，等待 review_course 复检确认。

明天修复建议：

- review gate 应同时检查 `items`、`qa-question-level`、`qa guide`、`topic-outline` 四层口径一致性，不能只看题目内容。
- 每个 topic 收敛后应有一个 `display_consistency_gate`：topic name、guide definition、question theme、manifest row 必须一致。
- 对“旧文件名但新主题”的情况，需要允许短期保留文件名，但必须在 manifest/guide 中显式标明当前权威 topic name，避免外显误判。

### 113. 用户收口条件变化后，manager 仍按旧目标自动滚动后续小包

触发时间：2026-06-21 09:34 CST

触发原因：

- 用户明确更新监控目标：“做完化学可以停了”。
- 当时系统已经完成 Chemistry 小包#5 PASS，manager 随即自动启动小包#6。
- 这说明 manager 的滚动执行逻辑只按“继续下一包”推进，没有显式接收或传播新的 stopping condition。

介入动作：

- Codex 将本轮目标收口条件更新为：Chemistry 0620 全科完成、review_course 整科复核通过、manager subject closeout 后即可停止监控目标。
- 向 manager 发送短指令：
  - 不再启动 Biology 或其他 IGCSE 学科；
  - Chemistry 全科 closeout 后停止并等待新指令；
  - 若小包#6 已经启动，可继续完成当前 Chemistry 链路，但不要扩展到新学科。

临时结果：

- 目标从“所有 IGCSE 学科完成”收窄为“Chemistry 完成即可停”，避免系统在 Chemistry 后继续自动开新学科。

明天修复建议：

- manager 应支持 `stopping_condition` 字段，并在每次 closeout 前检查是否满足停止条件。
- 用户更新目标后，应广播到 manager、worker_course、review_course，避免各角色继续按旧目标推进。
- workflow 状态板需要显示当前停止条件，例如 `stop_after_subject=Chemistry 0620`。

### 114. 小包#6 MINOR 清理任务已读但未快速落盘，状态面仍显示旧送审态

触发时间：2026-06-21 09:55 CST

触发原因：

- review_course 对 Chemistry 小包#6 给出 `MINOR`：核心内容通过，但存在 7 个孤儿 QQL 文件。
- manager 已派 worker_course 清理 7 个孤儿文件。
- worker_course 已消费 inbox，但 45 秒后核查：
  - 7 个孤儿文件仍存在；
  - `status.json` 中 worker_course 仍显示“小包#6 已送审, 等 review verdict”，没有切到“清理孤儿中”；
  - manager 状态已进入“清理7孤儿→整科closeout”，三方状态不一致。

介入动作：

- Codex 记录本 gap。
- 向 worker_course 发送最小纠偏指令：只删除明确列出的 7 个孤儿 QQL 文件，不做内容重构；完成后回报 manager 并送 review_course 复检。

临时结果：

- 将小包#6 最后卡点从泛化“MINOR”收窄为固定 7 个文件删除任务。

明天修复建议：

- worker 接到 MINOR 清理任务后应立刻更新 status 为 `cleaning_orphans`，避免外显仍停在旧送审态。
- review_course 的 MINOR verdict 应带可机器读取的 orphan file list，worker 可直接执行删除而不是重新查找。
- 小包提交前应自动运行 orphan gate，避免 review 阶段反复发现同类残留。

### 115. 小包#6 “孤儿文件”清理口径误伤有效 QQL，导致数量 gate 破坏

触发时间：2026-06-21 10:02 CST

触发原因：

- review_course 判定小包#6 有 7 个孤儿 QQL，并要求清理。
- Codex 按 review_course 和 manager 的 MINOR 口径给出最小删除清单，worker_course 执行删除。
- 删除后 Codex 复核发现：
  - `9.2` 从 9 QQL 变为 5 QQL；
  - `10.1` 从 9 QQL 变为 6 QQL；
  - 难度分布随之破坏，不再满足 `F:2|S:4|C:3`。
- 这说明“孤儿”判定并不是安全删除清单，实际有一部分所谓孤儿文件仍对应 items 或仍是 9 题结构的一部分。

介入动作：

- Codex 记录本 gap。
- 暂停继续推动“只删除孤儿”口径，改为盯 worker_course 补回 9.2/10.1 缺失 QQL，并重新通过数量/难度/items 对齐 gate。
- 后续 review 必须以 `exactly 9 QQL + exactly 9 items + ID 一致 + F:2|S:4|C:3` 为最终判据，而不是单独按文件名模式判 orphan。

临时结果：

- worker_course 已发现数量不足，正在根据 items 内容补回缺失 QQL。

明天修复建议：

- orphan gate 不能只靠文件名后缀或旧 batch 标识判断，必须基于 Question ID 与 items 的双向映射。
- review_course 输出“待删除文件”前应附带证据：每个文件为何不对应任何 items ID。
- 小包清理应使用安全流程：先生成 expected ID set，再移动候选 orphan 到 quarantine，复检 PASS 后再删除，避免误删有效 QQL。

### 116. review_course 复检小包#6 时卡在 status retry，verdict 未及时外显

触发时间：2026-06-21 10:08 CST

触发原因：

- worker_course 已完成小包#6 返修并送 review_course 复检。
- Codex 文件层硬 gate 已验证：
  - `9.2 / 9.3 / 10.1` 均为 exactly 9 QQL；
  - items 均为 exactly 9；
  - Question ID 双向一致；
  - 难度均为 `F:2|S:4|C:3`。
- review_course 已消费复检消息，但 pane 卡在 `eduflow status review_course 进行中 "复检小包#6 — 孤儿清理验证"` 的 retry（attempt 7/10），未及时产出 PASS/NEEDS_FIX verdict。

介入动作：

- Codex 记录本 gap。
- 向 review_course 发送最小 verdict 请求：不要停在 status retry；基于现有 gate 直接给 `PASS / NEEDS_FIX`，若仍有问题只列具体文件。

临时结果：

- 最后收口卡点从内容问题收窄为 review_course 外显/状态命令 retry 问题。

明天修复建议：

- review agent 在 status 写入失败时不应阻塞 verdict 输出，应先 `say` verdict，再异步补 status。
- runtime 应对 `eduflow status` retry 超阈值提供跳过/降级机制。
- supervisor 应检测 `review_consumed_but_no_verdict_due_to_status_retry`。

### 117. workflow 工具存在但 Chemistry 执行链未强制挂载，真实生产退回口头协作

触发时间：2026-06-21 10:15 CST

触发原因：

- 用户追问 `workerflow/workflow` 功能是否真的在用，并指出“有工具没用”本身就是问题。
- Codex 核查发现：
  - 项目已有 active workflow：`igcse-subject-launch`、`igcse-item-level-prototype`、`realrun-to-workflow`；
  - `tasks.json` 中 Physics / Business 等历史任务确实带有 `workflow_id: igcse-subject-launch`；
  - Chemistry 0620 本轮虽然群内多次口头说“按 workflow”，但小包推进主要依赖 inbox、status、logs 和人工盯盘，没有稳定体现为每个小包的 formal task workflow state / gate transition。
- 结果是：工具存在，但没有成为执行路径的硬约束；agent 一多或消息一堵，就容易回到“人盯人 + 口头状态”的模式。

介入动作：

- Codex 记录本 gap。
- 将该问题标记为明日高优修复项：不是新增 workflow，而是让现有 workflow 在任务派发、review gate、closeout 中被强制使用。
- 准备给 manager 最小指引：Chemistry 收口时必须显式引用 `igcse-subject-launch` gate / closeout，不要只做口头 closeout。

临时结果：

- 今晚先不打断 Chemistry 内容生产，以低噪声方式把最后 closeout 挂回 workflow 语义。

明天修复建议：

- `task dispatch` 对 IGCSE 学科任务应要求 `workflow_id=igcse-subject-launch`，缺失则拒绝或自动补齐。
- 每个小包至少要有可追踪的 gate 状态：`assigned -> producing -> submitted_review -> review_pass/minor/needs_fix -> package_closeout`。
- manager closeout 前自动运行 `eduflowteam workflow gates igcse-subject-launch` 或等价校验，并把结果写入 structured task truth。
- supervisor 增加检测：当消息内容出现“按 workflow / workflow closeout”，但任务缺少 `workflow_id` 或 gate transition 时，自动提示 manager 修正。

### 118. Chemistry 小包通过被误推进为整科 closeout，产物真相不支持全科收口

触发时间：2026-06-21 10:20 CST

触发原因：

- manager 已将小包#6 标记为最后一个小包，并准备进入 Chemistry 0620 整科 closeout。
- Codex 本地硬核查发现，当前产物真相不支持“整科完成”：
  - `content/igcse-chemistry-0620/qa/` 有 34 个 topic QA guide；
  - `items/` 有 77 个 items 文件，存在大量 `-s2/-s3/-s4` 分片/旧产物；
  - `qa-question-level/` 有 343 个 QQL 文件；
  - 按每个 items 文件核查会出现 77 个 issue，明显不是 34 topics × 9 的整科标准形态；
  - manifest 位于 `items/qa-manifest.csv`，根目录 `qa-manifest.csv` 不存在；
  - 许多 topic 仍未达到 `exactly 9 items + exactly 9 QQL + F:2|S:4|C:3 + ID 双向一致`。
- 说明今晚小包#1-#6 只完成了部分 topic 的收敛，不等于 Chemistry 0620 全科 34 topic closeout。

介入动作：

- Codex 记录本 gap。
- 准备向 manager 纠偏：暂停 Chemistry 整科 closeout；只允许宣布“小包#1-#6 阶段完成/部分 topic pass”，不得宣布全科 PASS。
- 要求 manager 按 `igcse-subject-launch` workflow 重新做 subject truth audit，把未达标 topic 列成剩余小包，或明确将今晚 scope 改为“Chemistry partial closeout”。

临时结果：

- 防止系统把部分小包成功错误上升为整科完成。

明天修复建议：

- subject closeout 必须以全科 inventory verifier 为硬 gate，不允许从最后一个小包 PASS 推导全科 PASS。
- manager closeout 卡片应区分 `package_closeout`、`partial_subject_checkpoint`、`subject_closeout` 三种状态。
- Chemistry 这类已有旧产物的学科，启动前必须先 quarantine/标记旧 items/QQL 分片，否则后续小包验收会和旧文件混在一起。
- `igcse-subject-launch` workflow 应要求根目录 manifest 位置、topic 数、QA/items/QQL 总数、difficulty distribution、ID 双向映射全部通过后才能 closeout。

### 119. 429 rate limit 未及时触发可用 runtime 切换，review/manager 最后外显通道假死

触发时间：2026-06-21 10:24 CST

触发原因：

- review_course 在小包#6 复检时出现 `API Error: Request rejected (429) · usage allocated quota exceeded`，停在 retry，没有及时输出 PASS/NEEDS_FIX。
- manager pane 同样出现 429，导致无法继续处理 worker_course 的小包#6 修复报告和后续 closeout。
- `health` 显示：
  - manager runtime-status 期望为 `manager_backup_deepseek`，但 live env 仍是 `claude-opus-4-6`，存在 env drift；
  - review_course 仍在 review_primary/sonnet 通道；
  - runtime guard 没有对这次 429 形成有效即时切换。
- 用户明确指出：429 应该换模型。

介入动作：

- Codex 记录本 gap。
- 准备用项目内置 `lifecycle.restart_with_runtime(...)` 硬切 runtime，而不是继续催 agent 或手工编辑配置。
- 目标：review_course 切到备用通道输出 verdict；manager 切到不同备用通道恢复收口/纠偏能力。

临时结果：

- 将问题从“review/manager 不响应”收窄为“429 没触发真实可用 runtime 切换”。

明天修复建议：

- runtime guard 对 `usage allocated quota exceeded` 应立即 hard-switch 并 nudge 最新高优 inbox，不应让 agent 自己 retry 到假死。
- health 的 runtime-status 与 live env drift 应升级为 actionable warning，允许一键 reconcile/respawn。
- review/manager 这种关键角色应避免同时落在同一个额度池；manager、review、course 至少应分散到不同 provider/profile。

### 120. 429 急救切换入口存在版本漂移，项目源码能力未被当前命令环境加载

触发时间：2026-06-21 10:29 CST

触发原因：

- 用户要求先记录 gap 再切换，并指出“这里还没有自然的触发换模型”。
- Codex 尝试使用项目源码中的 `lifecycle.restart_with_runtime(...)` 做受控 runtime hard-switch。
- 首次执行失败：
  - Python 实际导入的是 `/Volumes/Halobster/Codex相关/EduFlow/src/eduflow/runtime/lifecycle.py`；
  - 当前导入版本没有 `restart_with_runtime`；
  - 但本项目 `/Volumes/Halobster/Codex相关/EduFlow-Team-orch/src/eduflow/runtime/lifecycle.py` 中确实存在该函数。
- 说明 runtime 切换能力在项目源码里，但当前 `eduflow-team-env.sh` / Python import path 仍指向外部 `EduFlow` 旧版本，导致现场急救入口不可用。

介入动作：

- Codex 记录本 gap。
- 后续切换将显式使用 `PYTHONPATH=$PWD/src`，确保调用本项目源码版本。

临时结果：

- 将“429 没自然换模型”进一步定位为两层问题：
  - 运行时没有自动触发切换；
  - 手动切换入口也因为包版本/路径漂移而失效。

明天修复建议：

- `scripts/eduflow-team-env.sh` 应显式把 `$ROOT/src` 放到 `PYTHONPATH` 优先级最高，避免导入外部旧包。
- `eduflowteam health` 应显示 CLI/Python 实际 import 的 `eduflow.__file__`，发现不是当前项目源码时直接报警。
- 将 `restart_with_runtime` 暴露为稳定 CLI：例如 `eduflowteam runtime-switch <agent> <runtime> --reason ...`，不要依赖 operator 临时写 Python。
- runtime guard 自动切换与手动切换必须走同一条可观测路径，并记录 switch event。

### 121. runtime hard-switch 返回 ready 后没有自然恢复消息消费，关键 inbox 仍未读

触发时间：2026-06-21 10:37 CST

触发原因：

- Codex 已将 `review_course` 切到 `review_backup_deepseek`，`manager` 切到 `manager_backup_qwen_plus`，health 显示两个 pane 均 ready。
- 但切换后核查发现：
  - `review_course` 已 ACK 旧/新提示，但最新高优 inbox `msg_1782006971993_f52a72ed68` 仍未读；
  - `manager` 最新高优 inbox `msg_1782006972133_1349288a48` 仍未读；
  - pane 仍显示 retry/continuation 提示，没有自然进入 inbox 消费；
  - supervisor-check 仍报 high_priority_inbox_unread_blocking / read_without_ack。
- 说明 runtime 切换的 `ready` 只证明 CLI 进程已启动，不证明 agent 已恢复处理消息。

介入动作：

- Codex 记录本 gap。
- 准备手动唤醒 `review_course` 和 `manager`，要求先消费最新高优 inbox。

临时结果：

- 将恢复标准从“pane ready”提升为“最新高优 inbox 被 read+ack，并产出对应 verdict/status”。

明天修复建议：

- `restart_with_runtime(..., nudge_latest_inbox=True)` 后应有二次验证：最新高优 inbox 在限定时间内必须变为 read/ack，否则自动重新 inject 明确命令。
- health 应区分 `pane_ready` 与 `agent_operational`。
- supervisor 对关键角色 manager/review_course 的 unread high priority inbox 应触发更强恢复动作，而不是只显示 warn。

### 122. supervisor-check 报 hermes-supervisor down，与 health/router 视图出现不一致

触发时间：2026-06-21 10:38 CST

触发原因：

- `eduflowteam health` 显示 router/task-publish/watchdog alive，但 `task supervisor-check --json` 报：
  - `hermes_supervisor_down`
  - `hermes-supervisor: pid_present=false, alive=false`
- 这导致 supervisor-check 持续处于 `escalated_failure`，即便部分 runtime 已手动恢复。
- 当前可能是 hermes-supervisor loop 进程未运行、pid 文件缺失，或 health 与 supervisor-check 读取的进程集合不一致。

介入动作：

- Codex 记录本 gap。
- 准备按项目脚本重启 `scripts/hermes-supervisor-loop.sh`，恢复监督闭环。

临时结果：

- 将“消息一多没人兜底”的风险明确锚定到 hermes-supervisor 运行状态。

明天修复建议：

- `eduflowteam health` 应把 hermes-supervisor 纳入 daemon 主列表，而不是只在 supervisor-check 中暴露。
- `up`/`watchdog` 应保证 hermes-supervisor loop 自动拉起并写 pid。
- supervisor down 时应自动 self-heal，不能只发告警。

### 123. manager 切到 qwen_plus 后仍 429，fallback 未真正换出额度池

触发时间：2026-06-21 10:43 CST

触发原因：

- Codex 将 manager 从原通道切到 `manager_backup_qwen_plus` 后，health 显示 pane ready。
- 但 20 秒后复查 manager pane，仍出现 `API Error: Request rejected (429) · usage allocated quota exceeded`。
- 说明 `manager_backup_qwen_plus` 与原 429 通道共享额度池，或 env/live provider 未真正隔离。

介入动作：

- Codex 记录本 gap。
- 准备将 manager 再切到 `manager_backup_deepseek`，避开 qwen_plus 额度池。

临时结果：

- 不能再把 “切到 qwen_plus” 当作有效恢复，需要以 pane 实际 API 调用成功为准。

明天修复建议：

- runtime fallback 不能只按 runtime 名称判断成功，必须跑一次最小 API smoke。
- qwen_plus / primary / manager_primary 等 env_profile 应标注额度池归属，避免 fallback 切到同池。
- rate-limit fallback 链应优先跨 provider，而不是同 provider/profile 间循环。

### 124. tmux 注入唤醒文本停在输入框，未被 Claude Code 实际执行

触发时间：2026-06-21 10:44 CST

触发原因：

- Codex 对 manager/review_course 使用 `tmux send-keys` 注入“消费最新 inbox”的指令。
- 复查 pane 发现文本出现在输入区，但没有被模型执行；对应 inbox 仍未读。
- 说明当前注入/提交方式不能保证 Claude Code 接收并执行恢复指令。

介入动作：

- Codex 记录本 gap。
- 后续不再只依赖 UI 注入作为恢复证据，改以 inbox read/ack、logs verdict、status 更新作为恢复成功标准。

临时结果：

- 将恢复标准从“文字已注入 pane”修正为“命令实际执行并改变状态”。

明天修复建议：

- `tmux.inject` 对 Claude Code 应使用 adapter submit_keys，并验证提交后 pane 输出发生变化。
- 恢复指令注入后应自动检查目标 inbox 是否 read/ack；未变化则重试或降级到命令层处理。
- 对关键恢复动作提供 CLI API，不依赖手工 tmux 输入。

### 125. tmux 底层可见但 eduflowteam health 判断 session down，运行态视图分裂

触发时间：2026-06-21 11:22 CST

触发原因：

- `tmux list-windows -t EduFlowTeam` 能看到 7 个窗口：anna / auto_ops / manager / review_course / worker_builder / worker_course / worker_qbank。
- `tmux list-panes` 能看到 manager、review_course 的 live spawn command。
- 但 `eduflowteam health` 报 `tmux session EduFlowTeam not running`，并把所有 agent 标记为 session down。
- 同时 health 报 router/task-publish/watchdog pid dead，而底层 tmux 仍有实际 pane。
- 说明 health / eduflow 内部 tmux 探测与系统 tmux 事实出现分裂，可能是 tmux socket/env/path/uid/session server 视图不一致。

介入动作：

- Codex 记录本 gap。
- 临时以底层 `tmux list-windows/list-panes/capture-pane` 与本地 logs/status 为权威，不再单独依赖 health 判断 agent 是否存在。

临时结果：

- 避免误判 manager/review_course 不存在；当前确认二者 pane 实际存在。

明天修复建议：

- `eduflowteam health` 应输出实际调用的 tmux socket/path/user，并与 `tmux list-windows` 做一致性校验。
- health 不应在底层 tmux 可见时直接报 session down；应标注为 `tmux_probe_inconsistent`。
- supervisor-check/health/peek 应统一 tmux Target 解析逻辑，避免同一 session 在不同命令中一会儿存在、一会儿不存在。

### 126. review_course 已切 DeepSeek 但仍停在旧 interrupted 输入态，未自然产出正式 verdict

触发时间：2026-06-21 11:24 CST

触发原因：

- `tmux list-panes` 确认 review_course live spawn command 使用：
  - `ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic`
  - `ANTHROPIC_MODEL=deepseek-v4-pro`
- 但 `tmux capture-pane` 显示 review_course 仍停在旧 interrupted prompt：
  - 之前 429 后的恢复指令文本仍在输入区；
  - 没有看到 DeepSeek 切换后由 review_course 自己补出的正式小包#6 verdict。
- 状态层的小包#6 PASS 来自 operator hard gate，不是 review_course 自然完成。

介入动作：

- Codex 记录本 gap。
- 当前接受 operator hard gate 作为小包#6 partial checkpoint 的临时 verdict，但不把它升级为整科 closeout。

临时结果：

- 明确区分：review_course “已切到 DeepSeek” 与 “已恢复正常执行” 不是一回事。

明天修复建议：

- runtime 切换后必须清理 interrupted input state 或强制 respawn fresh pane。
- review_course 的正式 verdict 缺失时，manager closeout 应显示 `operator_verdict_fallback`，不可伪装为 review_course 自然 verdict。
- 对关键 review 角色增加 `post-switch smoke + inbox consume + say verdict` 三步恢复验证。

### 127. manager/review_course 模型运行态与状态文件不一致，DeepSeek 使用不能只看 registry

触发时间：2026-06-21 10:34 CST

触发原因：

- 用户追问 manager、review_course 的 DeepSeek 是否真的在用。
- `runtime-status.json` 显示：
  - manager = `manager_backup_qwen_plus`
  - review_course = `review_backup_deepseek`
- 但 live tmux pane 显示：
  - manager 实际启动环境为 `ANTHROPIC_BASE_URL=https://fast.sbbbbbbbbb.xyz`，`ANTHROPIC_MODEL=claude-opus-4-6`，不是 DeepSeek，也不是 qwen_plus。
  - review_course 实际启动环境为 `ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic`，`ANTHROPIC_MODEL=deepseek-v4-pro`。
- review_course 虽然 live env 是 DeepSeek，但 pane 仍停在旧 interrupted 输入态，未自然消费最新 inbox，也未自然产出正式 verdict。

介入动作：

- Codex 直接核查 tmux live spawn command、pane 输出、runtime status、inbox 未读情况。
- 判定“状态文件/registry”不能作为模型真实使用的唯一证据，必须以 live process + 最近成功执行行为为准。

临时结果：

- manager：当前实际没有在用 DeepSeek；live pane 使用 claude-opus-4-6 proxy，且最近能正常执行。
- review_course：当前确实以 DeepSeek 环境启动，但没有恢复为可工作的执行态；仍需 respawn 或 post-switch smoke 验证。

明天修复建议：

- runtime 切换后写入状态文件前，必须二次校验 live pane spawn command 是否与 registry 一致。
- supervisor/health 增加 `runtime_drift` 检测：当 runtime-status 与 tmux live env 不一致时标红。
- 对 review_course 这类关键 gate agent，切模型后必须自动执行 `inbox consume -> tiny verdict -> status/log update` 的 smoke test，否则不能标记为 recovered。
