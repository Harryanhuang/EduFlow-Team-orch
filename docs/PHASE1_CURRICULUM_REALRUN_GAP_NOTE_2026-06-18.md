本 note 基于 2026-06-18 在隔离状态目录 `/var/folders/gs/swrx39bn0q71knbn42fp90y80000gn/T/eduflow-phase1-realrun-xjzx_qsu` 的一轮课程线真实闭环试运行。试运行使用 repo-local CLI：`PYTHONPATH=src python3 -m eduflow.cli ...`，覆盖了 `approve` 路径（T-2）与 `reject -> resubmit -> manager_action` 路径（T-1），并观察了 `manager-overview`、`task get`、`task-events.jsonl`、`publish-scan`、`publish-check` 的表现。

## 任务模型还缺什么字段

- 缺少可直接写给 manager 的 `manager_action_type`。当前 `T-1` 只落成 `verdict=manager_action` 和 `blocking_reason=reviewer_requested_manager_action`，能知道要管，但不知道 reviewer 要 manager 做的是改范围、补信息、换 reviewer，还是直接决定是否对外发。
- 缺少 reviewer 结论的结构化说明字段。`reject` 和 `manager_action` 现在只有状态与 verdict，没有 `review_summary`、`review_reason`、`required_fix`、`decision_note` 这类可回放、可汇总的文本槽位，导致链路虽然不乱，但 manager 需要另找上下文才能判断下一步。
- 缺少“本轮产物指针”。任务模型里没有 `artifact_ref`、`draft_path`、`deliverable_id` 一类字段，真实课程线里 manager 很难只看任务态就知道当前稿件到底是哪一版。
- 缺少用户面风险字段。现在能表达 `blocked`，但不能表达“这个任务虽然 delivered，但是否适合对 user 讲”。后面 publish gate 若想稳，就需要类似 `publish_readiness`、`user_visible_summary`、`sensitive_flags` 这类面向对外表达的字段。
- 缺少更细的时间语义。`last_meaningful_update_at` 已经有价值，但还不够区分 `last_submitted_at`、`last_reviewed_at`、`last_manager_touched_at`。这会限制后续判断“谁卡住了”和“谁该被提醒”。

## manager 视角还缺什么查询/摘要

- `manager-overview` 已能把 `manager_action` 单列出来，这说明 Phase 1 方向是对的；但它还缺一行“为什么现在需要 manager”。当前只显示 `T-1 [curriculum] Draft Unit 1 outline owner=worker_course reviewer=reviewer_amy`，不显示 `blocking_reason` 或 reviewer 要求，manager 仍要再 `task get` 一次。
- `task get` 现在能看终态，但缺“最近一次关键转折摘要”。真实回放里，T-1 经历了 `submitted_for_review -> rejected -> submitted_for_review -> manager_action`，如果没有翻 `task-events.jsonl`，manager 很难一眼知道这条任务为什么停在这里。
- 缺少按 lane / reviewer / aging 的管理查询。课程线一多，manager 会需要“哪些 curriculum 任务超过 N 分钟没动”“哪些 reviewer 连续打回”“哪些任务反复 submit-review”这种摘要。
- 缺少针对“噪音”本身的 manager 摘要。`publish-scan --include-silent` 能看到大多数内部事件都被压成 `publish=false`，这说明群里已经明显安静了；但 manager 现在没有一个更高层的“本轮哪些事件被静默、只剩哪些会出群”的摘要视图，需要自己读一串 event decision。
- `publish-check` 的使用方式偏底层。单条检查必须显式给 `--sender` 才能工作，不适合 manager 在真实值班时快速判断“这个任务现在如果对 user 说，会说什么、为什么不能说”。

## publish/scanner 以后该怎么接（本轮不做）

- Phase 2 先做 publish gate 更合适。真实试运行里，`publish-scan --include-silent` 已经证明内部状态迁移大多可以安静压住，只有 `T-2 delivered` 被判定为 `publish=true reason=delivered_to_user`。这说明“静音基础”已有雏形，下一步最直接的业务价值是把“哪些事件允许对 user 发、发什么摘要”收紧成稳定规则。
- publish gate 的最小切口建议是：只处理 `delivered`、`manager_action`、以及少数必须升级的阻塞态，输出统一的 user-facing summary。这样 manager 的体感会先明显改善，因为对外表达从“每次临场判断”变成“先过 gate”。
- scanner 应该放在 publish gate 之后接。因为 scanner 要回答的是“谁卡住了、何时该提醒、提醒给谁”，但如果 publish 口径还没稳定，scanner 发现问题后也不知道该触发 manager 内部提示，还是对 user 发解释。
- scanner 的后续职责可以收成三件事：发现长时间无推进、发现反复 reject/resubmit、发现 manager_action 长时间未处理。它更像巡视和升级器，不应该先承担“解释任务真相”的主职责。
- 事件流回放已经足够支撑 scanner 的后续接入，因为 `task-events.jsonl` 现在已经有 `correlation_id`、`event_type`、`from_* / to_*`、`meaningful_changes`。但在接 scanner 之前，最好先补齐上面两节提到的 manager 语义字段和摘要接口，否则 scanner 只能发现卡点，不能解释卡点。
