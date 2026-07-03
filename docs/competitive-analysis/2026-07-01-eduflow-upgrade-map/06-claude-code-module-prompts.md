---
title: EduFlow 状态可信层升级：Claude Code 模块执行提示词包
date: 2026-07-01
status: draft
tags:
  - EduFlow
  - Claude-Code
  - execution-prompts
  - module-plan
  - Feishu
---

# EduFlow 状态可信层升级：Claude Code 模块执行提示词包

## 使用方式

这份文档把当前目标拆成可交给 Claude Code 独立执行的模块。建议顺序：

```text
M0 只读基线审计
→ M0.5 Residency Phase1 分支审计（如果分支存在或尚未合并）
→ M1 Employee Read Model
→ M2 Ops Dashboard CLI
→ M3 Feishu Snapshot Cards
→ M4 Runtime/Task Drift Explainer Skill
→ M5 Harness Surface Audit Skill
→ M6 Evidence Account Explainer
→ M7 Asset Registry Doctor
→ M8 Workflow Recommend 扩展
→ M9 Card Protocol v2 Hardening / Adoption
→ M10 Workspace Policy Skeleton
```

优先执行 P0：

```text
M0, M0.5（如适用）, M1, M2, M3, M4, M5
```

P1/P2 后续执行：

```text
M6, M7, M8, M9, M10
```

2026-07-02 Git 基线补充：当前最新 HEAD `91f0a87 Clarify project entrypoint with visual README` 强化了 README 和 `docs/media/` 作为项目入口的地位。执行下面任一模块前，Claude Code 应先记录当前 HEAD；执行 M0/M3/M5 时必须读取 `README.md` 与 `docs/media/README.md`，并保持实现口径与 README 的产品叙事一致：EduFlow 是飞书可见的本地可审计 AI 团队操作系统，不是纯代码工具或聊天机器人 demo。

2026-07-02 residency 分支补充：本地发现 `feat/2026-07-01-residency-phase1`，包含 `cards_v2.py`、`runtime/residency.py`、`store/agent_residency.py`、`residency-sleep`、`residency-wake`、wake failure ALERT、主群体验收敛等实现。若该分支存在，后续模块必须先判断它是否已合并；M1/M2 要消费 residency 字段，M3/M9 要复用 `cards_v2.py`，不能另造平行协议。详见 `08-residency-phase1-branch-impact-2026-07-02.md`。

## 总执行原则

给 Claude Code 的每个模块都应遵守：

- 不要重造 runtime guard、workflow engine、verification gate。
- 优先复用现有 primitive：`team --json`、`health`、`runtime verify`、`runtime-guard`、`task auto-ops-context`、`task auto-ops-production`、`task supervisor-check --json`、`task manager-actions`、`task evidence-account`、`workflow validate --strict`。
- 不要改飞书真实配置、不要发送真实飞书消息，除非模块明确要求，并且默认只做本地单元测试。
- 不要改 `.eduflow-team-state/` 的真实运行数据作为测试 fixture；测试必须用 `isolated_env()`。
- 不要削弱现有测试来通过。
- 新增 CLI 必须支持 `--json` 或至少有稳定可测试文本输出。
- 新增聚合视图必须有 degraded mode：一个子检查失败不能拖死整个 dashboard。
- 新增 prompt/skill 必须写清角色边界：manager 只读/派发，auto_ops 监控，worker_builder 修系统，review_course 出 verdict。
- 如果 `src/eduflow/feishu/cards_v2.py` 存在，优先复用并加固它，不要新建第二套 Card Protocol v2。
- 如果 `src/eduflow/runtime/residency.py` 存在，把 `resident / warm / cold` 和 `常驻 / 温备` 作为状态可信层的一等信号。
- 不要在普通测试或 smoke 中执行 `residency-sleep --apply`；涉及 sleep/wake 的验证默认使用 dry-run、mock 或 `isolated_env()`。

---

# M0：只读基线审计与实施确认

## 适合先开一个 Claude Code 窗口执行

目标：让 Claude Code 先确认当前 repo 事实，输出一份短基线报告，避免它直接从规划文档臆造实现。

```text
你在 /Volumes/Halobster/Codex相关/EduFlow-Team-orch 工作。

任务：只读扫描当前 EduFlow 项目，为后续“状态可信层升级”建立基线报告。不要修改任何文件。

必须先读：
- README.md
- docs/media/README.md
- AGENTS.md 或 CLAUDE.md（如果存在）
- docs/competitive-analysis/2026-07-01-eduflow-upgrade-map/05-current-eduflow-planning-recalibration.md
- docs/competitive-analysis/2026-07-01-eduflow-upgrade-map/08-residency-phase1-branch-impact-2026-07-02.md 如果存在
- docs/plans/2026-07-01-ecc-to-eduflow-team-skill-upgrade-plan.md
- src/eduflow/cli.py
- src/eduflow/commands/team.py
- src/eduflow/commands/task.py
- src/eduflow/commands/health.py
- src/eduflow/feishu/cards.py
- src/eduflow/feishu/slash.py
- src/eduflow/store/local_facts.py
- src/eduflow/store/tasks.py
- 如果当前分支或 `feat/2026-07-01-residency-phase1` 中存在，也必须读：
  - docs/plans/2026-07-01-phase0-residency-audit.md
  - src/eduflow/feishu/cards_v2.py
  - src/eduflow/feishu/cards_v2_schema.py
  - src/eduflow/runtime/residency.py
  - src/eduflow/store/agent_residency.py
  - src/eduflow/commands/sleep_idle.py
  - src/eduflow/commands/residency_wake.py
  - src/eduflow/commands/wake_alert.py

必须运行这些只读命令：
- git show --stat --oneline --decorate --name-status HEAD
- git branch --list feat/2026-07-01-residency-phase1
- git log --oneline --reverse master..feat/2026-07-01-residency-phase1 如果该分支存在
- git diff --name-status master..feat/2026-07-01-residency-phase1 如果该分支存在
- ./scripts/eduflowteam workflow validate --strict
- ./scripts/eduflowteam team --json
- ./scripts/eduflowteam task list | head -80
- rg -n "manager-panel|auto-ops-context|auto-ops-production|supervisor-check|evidence-account|review-queue|residency|cards_v2" src/eduflow tests/unit

输出文件：
- docs/plans/YYYY-MM-DD-eduflow-status-trust-baseline.md

报告必须包含：
1. 当前 Git HEAD、最新 commit 摘要，以及 README/视觉入口变化是否影响 P0 顺序。
2. `feat/2026-07-01-residency-phase1` 是否存在、是否已合并、差异文件列表、是否需要先做 M0.5。
3. 当前已有 primitives 列表，按 runtime / task / Feishu / workflow / memory / residency 分类。
4. P0 模块建议顺序：M0.5（如适用）-> employee_read_model -> ops-dashboard -> Feishu cards -> drift explainer -> harness audit。
5. 对每个模块列出预计触碰文件。
6. 标记不能碰的范围：真实 .eduflow-team-state 数据、真实飞书发送、真实 runtime 切换、`residency-sleep --apply`。
7. 标记已有测试入口。

验收：
- 没有修改代码。
- 报告里必须出现上述命令输出摘要。
- 报告里必须明确说明：当前不是重造 orchestration，而是补 operator cognition layer。
```

---

# M0.5：Residency Phase1 分支审计

## 何时执行

如果 `feat/2026-07-01-residency-phase1` 存在但尚未合并，或者它刚刚合并但还没有经过主线回归，就先执行这个模块。目标是判断这条分支能否作为 M1/M2/M3 的新底座。

## 推荐提示词

```text
你在 /Volumes/Halobster/Codex相关/EduFlow-Team-orch 工作。

任务：只读审计 `feat/2026-07-01-residency-phase1` 对 EduFlow 状态可信层的影响。不要修改文件，不要合并分支，不要切换分支做写操作。输出一份分支影响和合并前检查报告。

必须先运行：
- git status --short
- git branch --show-current
- git log --oneline --reverse master..feat/2026-07-01-residency-phase1
- git diff --stat master..feat/2026-07-01-residency-phase1
- git diff --name-status master..feat/2026-07-01-residency-phase1

必须从该分支读取：
- docs/plans/2026-07-01-phase0-residency-audit.md
- src/eduflow/feishu/cards_v2.py
- src/eduflow/feishu/cards_v2_schema.py
- src/eduflow/runtime/residency.py
- src/eduflow/store/agent_residency.py
- src/eduflow/commands/team.py
- src/eduflow/commands/sleep_idle.py
- src/eduflow/commands/residency_wake.py
- src/eduflow/commands/wake_alert.py
- tests/unit/test_cards_v2.py
- tests/unit/test_residency.py
- tests/unit/test_residency_sleep.py
- tests/unit/test_residency_wake.py
- tests/unit/test_residency_convergence.py

报告输出：
- docs/plans/YYYY-MM-DD-residency-phase1-branch-review.md

报告必须回答：
1. 这条分支实际实现了哪些能力，按 cards_v2 / residency policy / sleep / wake / main-group convergence 分类。
2. 哪些能力已经覆盖原 M3/M9，哪些仍需 M1/M2 补上。
3. `team --json` 新增 `residency` 是否向后兼容。
4. `cards_v2` 的角色 allow-list 是否符合：manager 才能 CLOSEOUT，review_course 才能 REVIEW，auto_ops/manager 才能 ALERT。
5. `residency-sleep` 默认是否 dry-run；`--apply` 的副作用边界是什么。
6. wake failure ALERT 是否可能制造主群噪音，是否有 dedup 或降级策略。
7. 若要合并，M1/M2/M3/M4/M5/M9 各自需要怎样调整。
8. 是否发现必须先修的 blocker；如果没有，给出 merge readiness: ready | ready_with_followups | blocked。

可选验证命令（只在分支已 checkout 或测试文件存在于当前工作树时运行）：
- python -m pytest tests/unit/test_cards_v2.py tests/unit/test_residency.py tests/unit/test_residency_sleep.py tests/unit/test_residency_wake.py tests/unit/test_residency_convergence.py tests/unit/test_commands_messaging.py
- ./scripts/eduflowteam workflow validate --strict

不要做：
- 不要执行 git merge / cherry-pick / rebase。
- 不要执行 `residency-sleep --apply`。
- 不要改真实 `.eduflow-team-state/`。
- 不要把该分支未合并代码当成当前 HEAD 的事实，报告里必须区分 current HEAD 与 branch HEAD。

完成汇报必须包含：
- 分支 commit 列表。
- 关键文件清单。
- ready/blocker 判断。
- 后续模块要改的具体点。
```

---

# M1：Employee Read Model 核心层

## 模块目标

建立只读 `employee_read_model.py`，统一解释 agent 的真实外显状态。这个模块是 P0 核心，后续 dashboard 和 Feishu card 都依赖它。

## 推荐提示词

```text
你在 /Volumes/Halobster/Codex相关/EduFlow-Team-orch 工作。

任务：实现 EduFlow 的 Employee Read Model 最小版。它是只读聚合层，用来区分“真实卡住”和“外显陈旧但功能正常”。

背景目标：
EduFlow 当前已有 status、heartbeat、logs、inbox、runtime-status、task truth、workflow gate 等 primitive，但飞书里还不能稳定看懂每个员工真实状态。本模块不要重造 runtime guard，也不要发送飞书消息，只做可测试的 read model。

必须先读：
- docs/competitive-analysis/2026-07-01-eduflow-upgrade-map/05-current-eduflow-planning-recalibration.md
- docs/competitive-analysis/2026-07-01-eduflow-upgrade-map/08-residency-phase1-branch-impact-2026-07-02.md 如果存在
- src/eduflow/commands/team.py
- src/eduflow/commands/status.py
- src/eduflow/store/local_facts.py
- src/eduflow/store/tasks.py
- src/eduflow/runtime/paths.py
- 如果存在，也必须读：
  - src/eduflow/runtime/residency.py
  - src/eduflow/runtime/config.py 中 residency 相关函数
  - src/eduflow/store/agent_residency.py
  - src/eduflow/commands/sleep_idle.py
  - src/eduflow/commands/residency_wake.py
  - tests/unit/test_residency.py
  - tests/unit/test_residency_sleep.py
  - tests/unit/test_residency_wake.py
- tests/unit/test_commands_status_log.py
- tests/unit/test_local_facts.py
- tests/unit/test_store_tasks.py

实现范围：
1. 新增 `src/eduflow/store/employee_read_model.py`。
2. 提供只读函数，建议命名：
   - `build_employee_snapshot(agent: str) -> dict`
   - `build_team_snapshot() -> list[dict]`
   - `classify_display_verdict(snapshot: dict) -> str`
   - `summarize_next_action(snapshot: dict) -> str`
3. snapshot 至少包含：
   - `agent`
   - `declared_status`
   - `declared_task`
   - `blocker`
   - `status_updated_at_ms`
   - `heartbeat_ms`
   - `heartbeat_age_ms`
   - `latest_log_type`
   - `latest_log_content`
   - `latest_log_at_ms`
   - `unread_high_priority_count`
   - `current_task_id`
   - `current_task_title`
   - `current_task_status`
   - `workflow_id`
   - `workflow_gate`
   - `workflow_gate_status`
   - `workflow_next_action`
   - `residency_label`，例如 `常驻` / `温备` / `未配置`
   - `residency_mode`，例如 `resident` / `warm` / `cold`
   - `residency_policy_source`
   - `last_active_at`
   - `last_handoff_at`
   - `last_sleep_at`
   - `last_wake_at`
   - `sleep_decision` 或 `sleep_eligibility`
   - `wake_status`，如果已有 wake failure evidence
   - `display_verdict`
   - `staleness_reason`
   - `recommended_next_action`
4. `display_verdict` 第一版限定为：
   - `active`
   - `stale_display`
   - `waiting_inbox`
   - `blocked`
   - `idle`
   - `warm_idle`（如果 residency 分支存在）
   - `stopped`
   - `unknown`
5. 分类规则建议：
   - status 为 `已停止` -> `stopped`
   - residency label 为 `温备` 且无高优未读/active task -> `warm_idle`
   - wake failure evidence 存在 -> `blocked`，recommended_next_action 指向 worker_builder/manager 处理 wake
   - 有高优未读 -> `waiting_inbox`
   - 有 blocker 或 task/status 明确 blocked -> `blocked`
   - heartbeat 新鲜但 status/log 陈旧 -> `stale_display`
   - heartbeat/log/status 都新鲜且有进行中任务 -> `active`
   - status 表示待命/ready 且无未读 -> `idle`
   - 证据不足 -> `unknown`
6. 时间阈值不要写死太深，可先定义模块常量：
   - `STATUS_STALE_MS = 30 * 60 * 1000`
   - `HEARTBEAT_FRESH_MS = 10 * 60 * 1000`
   - `LOG_FRESH_MS = 20 * 60 * 1000`

测试要求：
新增 `tests/unit/test_employee_read_model.py`，至少覆盖：
1. heartbeat 新鲜但 status 陈旧 -> `stale_display`
2. 高优未读 -> `waiting_inbox`
3. status 已停止 -> `stopped`
4. blocker 存在 -> `blocked`
5. ready/待命 + 无未读 -> `idle`
6. workflow task 能带出 `workflow_id` / gate / next_action
7. residency 为 warm/温备且无未读/active task -> `warm_idle` 或 `idle` with `residency_label=温备`
8. wake failure evidence 能进入 `blocked` 或 top-level `wake_status`

必须使用现有测试 helper：
- `isolated_env()`
- `local_facts.upsert_status`
- `local_facts.touch_heartbeat`
- `local_facts.append_message`
- `tasks.create_flow_task` 或现有 task helper

不要做：
- 不要改真实 `.eduflow-team-state/`。
- 不要发送 Feishu。
- 不要改 runtime guard。
- 不要改 task 状态机语义。
- 不要引入新依赖。
- 不要把 `温备` 当成 `stopped`。温备是可唤醒的低成本待命态。
- 不要调用 `residency-sleep --apply`。read model 只能读事实和做纯分类。

验收命令：
- python -m pytest tests/unit/test_employee_read_model.py
- python -m pytest tests/unit/test_commands_status_log.py tests/unit/test_local_facts.py tests/unit/test_store_tasks.py
- 如果 residency 文件存在：python -m pytest tests/unit/test_residency.py tests/unit/test_residency_sleep.py tests/unit/test_residency_wake.py
- ./scripts/eduflowteam workflow validate --strict

完成汇报必须包含：
- 新增文件列表。
- display_verdict 分类表。
- residency 字段如何接入，以及温备和停止的区别。
- 哪些数据源已接入，哪些暂未接入。
- 测试结果。
```

---

# M2：Ops Dashboard CLI

## 模块目标

新增 `eduflow task ops-dashboard --json/--text`，用 M1 的 read model 聚合当前 operator 最需要看的信息。要求快、稳、可降级。

## 推荐提示词

```text
你在 /Volumes/Halobster/Codex相关/EduFlow-Team-orch 工作。

任务：新增 `eduflow task ops-dashboard [--json] [--text]`，作为 P0 operator dashboard。它聚合现有 primitives，让 manager/auto_ops 5 秒内看到 top actions 和状态可信度。

前置假设：
- M1 已经实现 `src/eduflow/store/employee_read_model.py`。
- 如果 M1 不存在，先停止并说明依赖缺失，不要临时复制一份 read model 到 task.py。

必须先读：
- src/eduflow/store/employee_read_model.py
- src/eduflow/commands/task.py
- src/eduflow/commands/team.py
- 如果存在，也必须读：
  - src/eduflow/runtime/residency.py
  - src/eduflow/store/agent_residency.py
  - src/eduflow/commands/sleep_idle.py
  - src/eduflow/commands/residency_wake.py
  - src/eduflow/commands/wake_alert.py
- src/eduflow/store/task_event_scanner.py
- src/eduflow/store/task_publish_gate.py
- src/eduflow/store/task_evidence_account.py
- tests/unit/test_commands_task.py
- docs/competitive-analysis/2026-07-01-eduflow-upgrade-map/05-current-eduflow-planning-recalibration.md

实现范围：
1. 在 `src/eduflow/commands/task.py` 增加子命令：
   - `ops-dashboard`
   - 支持 `--json`
   - 支持 `--text` 或默认文本输出
2. 输出 JSON 顶层建议结构：
```json
{
  "generated_at_ms": 0,
  "summary": {
    "agents_total": 0,
    "active": 0,
    "stale_display": 0,
    "waiting_inbox": 0,
    "blocked": 0,
    "warm_idle": 0,
    "idle": 0,
    "unknown": 0
  },
  "top_actions": [],
  "employees": [],
  "residency": {
    "resident": 0,
    "warm": 0,
    "cold": 0,
    "wake_failed": 0,
    "sleep_candidates": 0
  },
  "review_queue": [],
  "manager_actions": [],
  "degraded": [],
  "notes": []
}
```
3. `employees` 来自 `employee_read_model.build_team_snapshot()`。
4. `top_actions` 生成规则第一版：
   - 高优未读 > blocked > stale_display > manager_action > review_queue。
   - 每条 action 包含 `priority`, `agent`, `reason`, `recommended_next_action`。
   - residency 分支存在时，补充这些 action：
     - warm/温备 agent 有高优未读 -> `wake_or_route_inbox`
     - wake failure -> `repair_wake_path`
     - dry-run sleep candidate -> `sleep_candidate_review`
     - resident agent 被错误判为可 sleep -> `residency_policy_mismatch`
5. 需要接入但允许 degraded：
   - employee snapshot
   - review queue / manager actions
   - supervisor-check 摘要，如已有函数可复用就复用；不要 shell out 自己调用 `eduflow`。
   - residency summary，如果 residency 模块不存在则 degraded 里记录 `residency:not_available`，不要失败。
6. degraded mode：
   - 某个聚合失败时不要整个命令失败。
   - 在 `degraded` 里记录 `source`, `error_type`, `message`。
   - 文本输出里显示 `degraded_sources=N`。
7. 文本输出必须适合飞书粘贴，建议包含：
   - `ops dashboard`
   - `summary: agents=... active=... stale_display=... waiting_inbox=... blocked=...`
   - `top_actions:`
   - `employees:`
   - `degraded:`

测试要求：
在 `tests/unit/test_commands_task.py` 增加测试，至少覆盖：
1. `task ops-dashboard --json` 输出合法 JSON。
2. 员工 `stale_display` 会进入 summary 和 top_actions。
3. 高优未读会进入 top_actions 且优先级高于 stale_display。
4. 一个子聚合异常时命令仍 rc=0，并输出 degraded。
5. 文本模式包含 summary/top_actions/employees。
6. residency 分支存在时，`warm_idle` / `wake_failed` / `sleep_candidates` 至少覆盖一个测试。

不要做：
- 不要让 ops-dashboard 调真实飞书。
- 不要启动 runtime。
- 不要读取 tmux pane 大量内容。
- 不要把 `manager-panel` 整段阻塞调用塞进 dashboard。
- 不要破坏现有 `manager-panel` 行为。
- 不要在 dashboard 内部执行 `residency-sleep --apply` 或真实 wake；dashboard 只能读、汇总和建议。

验收命令：
- python -m pytest tests/unit/test_employee_read_model.py tests/unit/test_commands_task.py
- ./scripts/eduflowteam task ops-dashboard --json
- ./scripts/eduflowteam task ops-dashboard
- ./scripts/eduflowteam workflow validate --strict

完成汇报必须包含：
- 新增/修改的命令。
- JSON shape。
- top_actions 排序规则。
- residency summary 和相关 top_actions。
- degraded mode 如何触发和展示。
- 测试结果。
```

---

# M3：Feishu Employee / Team Snapshot Cards

## 模块目标

把 M1/M2 的结果接到 Feishu slash/control plane，先做只读卡片，不触发真实任务执行。

## 推荐提示词

```text
你在 /Volumes/Halobster/Codex相关/EduFlow-Team-orch 工作。

任务：新增飞书 employee/team snapshot 卡片，让老板和 manager 可以在飞书里看见可信团队状态。只做 slash/card 层，不发送真实消息，不改 router 外部配置。

前置假设：
- M1 `employee_read_model.py` 已存在。
- M2 `task ops-dashboard --json` 已存在。
- 如果缺失，先停止并说明依赖缺失。

必须先读：
- src/eduflow/feishu/cards.py
- src/eduflow/feishu/cards_v2.py 如果存在
- src/eduflow/feishu/cards_v2_schema.py 如果存在
- src/eduflow/feishu/slash.py
- src/eduflow/feishu/deliver.py
- src/eduflow/store/employee_read_model.py
- src/eduflow/commands/task.py
- tests/unit/test_feishu_cards.py
- tests/unit/test_feishu_slash.py

实现范围：
1. 如果 `src/eduflow/feishu/cards_v2.py` 已存在，优先在它之上做 thin adapter 或在 `cards.py` 中调用它；不要新建第二套 `card_protocol.py`。如果它不存在，才在 `cards.py` 新增纯函数：
   - `employee_snapshot_card(snapshot: dict, *, title_suffix: str = "") -> dict`
   - `team_snapshot_card(dashboard: dict, *, title_suffix: str = "") -> dict`
2. 卡片必须使用现有 v2 schema helpers / `cards_v2.validate_card` / `render_to_card_dict`，不要回退到 card v1。如果现有 `CardType` 还没有 `OPS_SNAPSHOT`，先用最小 adapter 输出 schema 2.0，并在 M9 hardening 中补类型。
3. employee card 至少显示：
   - agent
   - display_verdict
   - residency_label / residency_mode
   - declared_status
   - current_task
   - workflow_id / workflow_gate / workflow_next_action
   - staleness_reason
   - recommended_next_action
4. team card 至少显示：
   - summary counts
   - residency counts：常驻 / 温备 / wake_failed / sleep_candidates
   - top 3 actions
   - blocked/stale/waiting agents
   - degraded sources
5. 卡片信息架构必须贴近 README 的公开叙事：老板通过飞书看团队状态，manager 负责任务拆分、派发、回收、复盘和关口检查；第一屏优先回答“谁在做、卡在哪、下一步谁接、是否需要老板判断”，不要做成开发者日志墙。
6. 在 `src/eduflow/feishu/slash.py` 新增 slash：
   - `/employees`：返回 team snapshot card
   - `/employee <agent>`：返回单个 employee card
   - `/ops` 或 `/ops-dashboard`：返回 ops dashboard card
7. `/team` 现有行为不要破坏。可以不改 `/team`，让新命令先独立上线。
8. 对 unknown agent 返回清晰 warning card 或文本，复用 `_bad_agent`。
9. 如果 residency 分支已合并，飞书第一屏必须能区分：常驻、温备、已停止、外显陈旧但 heartbeat 新鲜。

测试要求：
1. `tests/unit/test_feishu_cards.py` 增加 card shape 测试：
   - schema == "2.0"
   - title/content 包含 agent/display_verdict/residency/top_actions
   - degraded 为空/非空都能渲染
2. `tests/unit/test_feishu_slash.py` 增加 slash dispatch 测试：
   - `/employees`
   - `/employee worker_course`
   - `/employee unknown_agent`
   - `/ops`
3. 测试不得真实发送飞书。

不要做：
- 不要修改真实 chat_id。
- 不要调用 LLM。
- 不要让 slash handler 执行长耗时命令。
- 不要让卡片依赖真实 tmux。
- 不要改变 `/team` 现有语义，除非测试覆盖完全。
- 不要绕过 `cards_v2` 的 role allow-list 去发 CLOSEOUT / REVIEW / ALERT。

验收命令：
- python -m pytest tests/unit/test_feishu_cards.py tests/unit/test_feishu_slash.py
- python -m pytest tests/unit/test_employee_read_model.py tests/unit/test_commands_task.py
- ./scripts/eduflowteam workflow validate --strict

完成汇报必须包含：
- 新增 slash 命令列表。
- 每张卡片字段说明。
- 是否复用了 `cards_v2.py`；如果没有，必须说明当前分支不存在或缺口。
- 是否修改 `/team`，如果没有，说明原因。
- 测试结果。
```

---

# M4：Runtime / Task Drift Explainer Skill

## 模块目标

创建一个给 `auto_ops` / `worker_builder` / `manager-lite` 使用的本地 Skill：它不新增守护进程，只规定如何组合现有命令解释 runtime/status/task drift。

## 推荐提示词

```text
你在 /Volumes/Halobster/Codex相关/EduFlow-Team-orch 工作。

任务：创建 `skills/eduflow-runtime-task-drift-explainer/SKILL.md`，用于把现有 runtime/task primitives 解释成 diagnosis + safe next action。这个 skill 是操作规程，不是新代码守护进程。

必须先读：
- docs/plans/2026-07-01-ecc-to-eduflow-team-skill-upgrade-plan.md
- docs/competitive-analysis/2026-07-01-eduflow-upgrade-map/05-current-eduflow-planning-recalibration.md
- docs/competitive-analysis/2026-07-01-eduflow-upgrade-map/08-residency-phase1-branch-impact-2026-07-02.md 如果存在
- src/eduflow/commands/health.py
- src/eduflow/commands/runtime_verify.py
- src/eduflow/commands/runtime_guard.py
- src/eduflow/commands/task.py
- src/eduflow/commands/team.py
- 如果存在，也必须读：
  - src/eduflow/runtime/residency.py
  - src/eduflow/store/agent_residency.py
  - src/eduflow/commands/sleep_idle.py
  - src/eduflow/commands/residency_wake.py
  - src/eduflow/commands/wake_alert.py
- skills/eduflow-team-monitor/references/context-patrol.md 如果存在
- skills/eduflow-team-monitor/references/production-patrol.md 如果存在

实现范围：
1. 新增目录和文件：
   - `skills/eduflow-runtime-task-drift-explainer/SKILL.md`
2. SKILL.md frontmatter 至少包含：
   - name: eduflow-runtime-task-drift-explainer
   - description: 说明用于 runtime/status/task drift 诊断
3. 正文必须包含：
   - When to use
   - Role boundary
   - Read-only first commands
   - Diagnosis taxonomy
   - Evidence template
   - Safe next action routing
   - Do not do
   - Output template
4. Diagnosis taxonomy 必须包含：
   - `runtime_dead`
   - `env_drift`
   - `fallback_cooldown`
   - `inbox_not_consumed`
   - `context_blocked`
   - `task_truth_drift`
   - `production_stale`
   - `status_lag`
   - `external_state_mismatch`
   - `warm_residency_expected`
   - `wake_failed`
   - `sleep_suppressed_active_task`
   - `sleep_suppressed_unread_inbox`
   - `residency_policy_mismatch`
5. Role boundary：
   - `auto_ops`: monitor only, report to manager
   - `worker_builder`: repair config/CLI/runtime only after manager dispatch
   - `manager`: reads lite report and dispatches, does not repair
   - `worker_course/review_course/worker_qbank`: not runtime repair owners
6. Command ladder 必须优先使用：
   - `./scripts/eduflowteam team --json`
   - `./scripts/eduflowteam task ops-dashboard --json` 如果存在
   - `./scripts/eduflowteam health`
   - `./scripts/eduflowteam runtime verify <agent>`
   - `./scripts/eduflowteam runtime-guard`
   - `./scripts/eduflowteam task auto-ops-context`
   - `./scripts/eduflowteam task auto-ops-production`
   - `./scripts/eduflowteam task supervisor-check --json`
   - `./scripts/eduflowteam inbox <agent>`
   - `./scripts/eduflowteam residency-sleep --agent <agent> --json` 只允许 dry-run
   - `./scripts/eduflowteam residency-wake <agent> --json` 只在明确需要预热或验证 wake 时使用；不要作为普通诊断第一步
7. Output template：
```markdown
## Runtime/Task Drift Explainer

- affected_agent:
- diagnosis:
- confidence:
- evidence_used:
- what_is_not_the_problem:
- safe_next_action:
- owner:
- user_visible_update_needed:
- do_not_do:
```

不要做：
- 不要新增 Python runtime logic。
- 不要修改 task 状态机。
- 不要修改飞书发送逻辑。
- 不要把 manager 写成 repair owner。

验收：
- 文件存在。
- Markdown 可读。
- 至少包含 3 个 example cases：
  1. 外显陈旧但 heartbeat 新鲜。
  2. inbox 高优未读未消费。
  3. runtime env drift。
  4. 温备是预期低成本待命，不是 stopped。
  5. wake failed 需要 worker_builder/manager 介入。
- rg 能搜到 diagnosis taxonomy 里的所有 key。

完成汇报必须包含：
- 新 skill 路径。
- 适配角色。
- 诊断分类表。
```

---

# M5：Harness Surface Audit Skill

## 模块目标

创建只读审计 skill，用来扫 EduFlow 的 prompt/identity/skill/workflow/runtime/memory/Feishu surface，找重复、漂移、过载。

## 推荐提示词

```text
你在 /Volumes/Halobster/Codex相关/EduFlow-Team-orch 工作。

任务：创建 `skills/eduflow-harness-surface-audit/SKILL.md`，作为 EduFlow 配置面/能力面只读审计 Skill。它用于 worker_builder/Hermes/Luke_recorder，不给内容 worker 使用。

必须先读：
- docs/plans/2026-07-01-ecc-to-eduflow-team-skill-upgrade-plan.md 的 Harness Surface Audit 部分
- docs/competitive-analysis/2026-07-01-eduflow-upgrade-map/05-current-eduflow-planning-recalibration.md
- docs/competitive-analysis/2026-07-01-eduflow-upgrade-map/08-residency-phase1-branch-impact-2026-07-02.md 如果存在
- README.md
- docs/media/README.md
- CLAUDE.md
- AGENTS.md 如果存在
- src/eduflow/cli.py
- src/eduflow/commands/workflow.py
- docs/workflows/README.md
- .claude/skills/skill-registry.md 如果存在

实现范围：
1. 新增：
   - `skills/eduflow-harness-surface-audit/SKILL.md`
2. SKILL.md 必须定义扫描面：
   - AGENTS.md / CLAUDE.md
   - README.md
   - eduflow.toml
   - src/eduflow/cli.py
   - src/eduflow/commands/
   - src/eduflow/runtime/
   - src/eduflow/runtime/residency.py
   - src/eduflow/store/agent_residency.py
   - src/eduflow/feishu/cards_v2.py
   - src/eduflow/feishu/cards_v2_schema.py
   - src/eduflow/commands/sleep_idle.py
   - src/eduflow/commands/residency_wake.py
   - src/eduflow/commands/wake_alert.py
   - src/eduflow/store/task_event_scanner.py
   - skills/
   - .claude/skills/
   - docs/workflows/
   - docs/media/README.md
   - docs/media/readme-runtime-map.svg
   - docs/media/readme-delivery-loop.svg
   - .eduflow-team-state/agents/*/identity.md
   - .eduflow-team-state/facts/runtime-status.json
   - .eduflow-team-state/facts/runtime-switch-events.jsonl
3. 必须输出审计模板：
```markdown
## EduFlow Harness Surface Audit

### Current surface
- Runtime:
- Task/workflow:
- Identity/skill:
- Memory:
- Feishu/control:

### Duplicate or drift risks
- ...

### README / visual narrative drift
- ...

### Context overhead risks
- ...

### Primitive-only gaps
- ...

### Recommended placement
| finding | should land in identity / workflow / skill / CLI / test / docs |

### Top next moves
1. ...
```
4. 必须写清晋升判断：
   - 单角色边界 -> identity
   - 多角色链路 -> workflow
   - 可机器判断 -> CLI/test/task_event_scanner
   - 操作员巡检 -> monitor skill/reference
   - 长期知识 -> Hermes/Obsidian/memory candidate
   - 一次性事故 -> case note
5. 必须写清禁止项：
   - 不改真实状态。
   - 不发送飞书。
   - 不把审计结果直接写入 identity/workflow，除非另有 manager closeout。

验收：
- 文件存在。
- rg 能搜到 `Duplicate or drift risks`, `Context overhead risks`, `Recommended placement`。
- rg 能搜到 `residency`, `cards_v2`, `wake failure`，除非当前 repo 确实没有这些文件，并在文档里说明缺失。
- 文档明确不装给 worker_course/review_course/worker_qbank。

完成汇报必须包含：
- 新 skill 路径。
- 扫描面列表。
- 角色安装建议。
```

---

# M6：Evidence Account Explainer

## 模块目标

把现有 evidence gate 翻译成角色可执行 verdict packet。这个模块可先做 skill，再做 CLI。

## 推荐提示词

```text
你在 /Volumes/Halobster/Codex相关/EduFlow-Team-orch 工作。

任务：实现 Evidence Account Explainer 第一版。优先创建 skill；如果时间允许，再新增 `eduflow task evidence-explain <task_id> [--json]` CLI。目标是把已有 evidence-account / subject verifier / review queue 转成 `PASS | NEEDS_FIX | BLOCKED | OBSERVE` packet。

必须先读：
- src/eduflow/store/task_evidence_account.py
- src/eduflow/store/subject_verifier.py
- src/eduflow/store/ap_subject_verifier.py
- src/eduflow/store/task_event_scanner.py
- src/eduflow/commands/task.py 中 evidence-account / subject-inventory / review-queue / manager-actions
- tests/unit/test_task_publish_gate.py
- tests/unit/test_subject_verifier.py
- tests/unit/test_ap_subject_verifier.py
- tests/unit/test_commands_task.py 中 evidence-account 相关测试

实现路径 A（必须做）：
1. 新增 `skills/eduflow-evidence-account-explainer/SKILL.md`。
2. 文档写清：
   - review_course full verdict
   - worker_course selfcheck
   - worker_qbank qbank slice
   - manager closeout-lite
3. 输出模板：
```markdown
## Evidence Account Verdict Packet

- task_id:
- workflow_id:
- verdict: PASS | NEEDS_FIX | BLOCKED | OBSERVE
- confidence:
- missing_evidence:
- conflicting_evidence:
- latest_authoritative_review:
- subject_verifier_status:
- qbank_readiness:
- manager_action_allowed:
- required_next_owner:
- safe_next_action:
- do_not_say_to_user_yet:
```

实现路径 B（可选，若实现则必须测）：
1. 在 `src/eduflow/commands/task.py` 新增：
   - `task evidence-explain <task_id> [--json]`
2. 复用 `task_evidence_account` 的现有结构，不要重算一套 gate。
3. JSON 输出必须包含上面 packet 字段。
4. 文本输出必须适合 manager 粘贴。

不要做：
- 不要修改 subject verifier 判定逻辑。
- 不要把 batch/package PASS 自动升级成 subject PASS。
- 不要让 manager 深审内容。
- 不要发送飞书。

验收命令：
- python -m pytest tests/unit/test_subject_verifier.py tests/unit/test_ap_subject_verifier.py tests/unit/test_commands_task.py
- 如果新增 CLI：./scripts/eduflowteam task evidence-explain <现有或测试任务ID> --json

完成汇报必须包含：
- 新 skill/CLI。
- verdict 分类规则。
- 是否实现 CLI；如果没有，说明下一步。
```

---

# M7：Asset Registry Doctor 初版

## 模块目标

先做 read-only 资产目录，不做安装系统。统一登记 skill/workflow/identity rule/patrol reference/memory candidate/CLI check。

## 推荐提示词

```text
你在 /Volumes/Halobster/Codex相关/EduFlow-Team-orch 工作。

任务：实现 EduFlow Asset Registry Doctor 初版。它是 read-only 资产发现与 drift-check，不是 capability installer。

必须先读：
- docs/competitive-analysis/2026-07-01-eduflow-upgrade-map/04-ecc-missing-capabilities-analysis.md
- docs/competitive-analysis/2026-07-01-eduflow-upgrade-map/05-current-eduflow-planning-recalibration.md
- docs/workflows/README.md
- src/eduflow/commands/workflow.py
- src/eduflow/cli.py
- .claude/skills/skill-registry.md 如果存在
- skills/ 目录结构

实现范围：
1. 新增 `src/eduflow/store/asset_registry.py`。
2. 新增 `src/eduflow/commands/asset.py`。
3. 在 `src/eduflow/cli.py` 注册 top-level command：
   - `eduflow asset ...`
4. 支持命令：
   - `eduflow asset list [--json]`
   - `eduflow asset recommend "<task text>" [--json]`
   - `eduflow asset validate [--json]`
   - `eduflow asset drift-check [--json]`
5. 第一版资产类型：
   - `workflow`
   - `skill`
   - `identity_rule`
   - `patrol_reference`
   - `memory_candidate`
   - `cli_check`
6. 资产字段建议：
```json
{
  "asset_id": "",
  "asset_type": "",
  "title": "",
  "path": "",
  "status": "active|candidate|draft|stale|unknown",
  "owner_role": "",
  "trigger_terms": [],
  "validation_command": "",
  "source_evidence": ""
}
```
7. `list` 第一版至少扫描：
   - `docs/workflows/*/README.md`
   - `docs/workflows/_candidates/*/README.md`
   - `skills/*/SKILL.md`
   - `.claude/skills/*.md`
   - `.eduflow-team-state/agents/*/identity.md` 只读存在性，不解析真实 secret
8. `recommend` 可以先用关键词打分，类似 workflow recommend，但必须输出 confidence。
9. `validate` 检查：
   - workflow 标准文件是否齐。
   - skill 是否有 name/description 或标题。
   - identity 文件是否存在且非空。
10. `drift-check` 检查：
   - 同名/近似重复 skill。
   - candidate 与 active workflow 同 id。
   - active workflow 缺标准文件。
   - identity 存在但对应 agent 不在 team config 中。

测试要求：
新增 `tests/unit/test_commands_asset.py`，覆盖：
1. `asset list --json` 能列出临时 workflow 和 skill。
2. `asset recommend` 对 workflow/skill 关键词返回候选。
3. `asset validate --json` 返回 ok/warnings/errors。
4. `asset drift-check --json` 能发现 duplicate 或 missing standard file。

不要做：
- 不要写 install-state。
- 不要复制/安装/删除 skill。
- 不要修改 identity。
- 不要发送飞书。
- 不要引入新依赖。

验收命令：
- python -m pytest tests/unit/test_commands_asset.py
- python -m pytest tests/unit/test_commands_workflow.py
- ./scripts/eduflowteam asset list --json
- ./scripts/eduflowteam asset validate --json
- ./scripts/eduflowteam workflow validate --strict

完成汇报必须包含：
- 新命令说明。
- 资产类型表。
- drift-check 当前能发现什么，不能发现什么。
```

---

# M8：Workflow Recommend 覆盖 Ops / Status Drift

## 模块目标

扩展现有 `workflow recommend`，让它能识别当前最典型的 ops/status-drift 类任务，并推荐正确入口。

## 推荐提示词

```text
你在 /Volumes/Halobster/Codex相关/EduFlow-Team-orch 工作。

任务：扩展 `eduflowteam workflow recommend`，覆盖 ops/status-drift 类问题。当前 `agent 外显陈旧但实际功能正常，想制定优化方案` 无 confident recommendation，需要修正。

必须先读：
- src/eduflow/commands/workflow.py
- docs/workflows/README.md
- docs/workflows/runtime-failover-hardening/README.md
- docs/workflows/realrun-to-workflow/README.md
- docs/competitive-analysis/2026-07-01-eduflow-upgrade-map/05-current-eduflow-planning-recalibration.md
- tests/unit/test_commands_workflow.py

实现范围：
1. 在 `_RECOMMEND_KEYWORDS` 或相邻机制中增加 ops/status drift 关键词。
2. 第一版推荐策略：
   - `外显陈旧`, `status_lag`, `stale display`, `heartbeat`, `实际功能正常` -> 推荐 `runtime-failover-hardening` 或输出新 next_step 指向 `task ops-dashboard` / drift explainer。
   - `task truth drift`, `manager panel`, `supervisor-check`, `状态不一致` -> 推荐 `realrun-to-workflow` + ops-dashboard next_step，或如果更贴切则推荐 `runtime-failover-hardening`。
   - `429`, `fallback`, `runtime`, `env drift`, `pane ready but inbox not consumed` -> 推荐 `runtime-failover-hardening`。
3. 如果没有 active workflow 能完全覆盖，输出要比现在更有帮助：
```text
no confident workflow recommendation
suggested_next_step: ./scripts/eduflowteam task ops-dashboard --json
candidate_skill: eduflow-runtime-task-drift-explainer
```
4. 不要让 candidate workflow 被当 active workflow 使用。

测试要求：
在 `tests/unit/test_commands_workflow.py` 增加：
1. `"agent 外显陈旧但实际功能正常，想制定优化方案"` 不再只输出空泛 list，至少有 suggested_next_step 或推荐 workflow。
2. `"429 fallback env drift"` 推荐 runtime-failover-hardening。
3. `"重复真实运行沉淀流程"` 仍推荐 realrun-to-workflow。
4. 旧推荐样例不回归。

不要做：
- 不要新增自动执行。
- 不要把 workflow recommend 变成 LLM 调用。
- 不要修改 workflow active/candidate 边界。

验收命令：
- python -m pytest tests/unit/test_commands_workflow.py
- ./scripts/eduflowteam workflow recommend "agent 外显陈旧但实际功能正常，想制定优化方案"
- ./scripts/eduflowteam workflow validate --strict

完成汇报必须包含：
- 新关键词和推荐规则。
- 对 status drift 的输出样例。
- 测试结果。
```

---

# M9：Card Protocol v2 Hardening / Adoption

## 模块目标

如果 `feat/2026-07-01-residency-phase1` 或当前 HEAD 已经包含 `src/eduflow/feishu/cards_v2.py`，本模块不是从零实现协议，而是审查、补缺口、接入 M3/M2，并形成迁移边界。只有在当前 repo 确实没有 `cards_v2.py` 时，才退回到最小实现。

## 推荐提示词

```text
你在 /Volumes/Halobster/Codex相关/EduFlow-Team-orch 工作。

任务：执行 Card Protocol v2 hardening/adoption。目标是复用并加固现有 `cards_v2.py`，让 Feishu card 具备稳定 `card_type`、角色 allow-list、必填字段、可测试渲染和后续 scanner 可依赖的结构化字段。不要重复造第二套协议。

必须先读：
- src/eduflow/feishu/cards.py
- src/eduflow/feishu/cards_v2.py 如果存在
- src/eduflow/feishu/cards_v2_schema.py 如果存在
- src/eduflow/feishu/slash.py
- src/eduflow/commands/say.py
- src/eduflow/commands/send.py
- src/eduflow/commands/wake_alert.py 如果存在
- src/eduflow/store/task_publish_gate.py
- src/eduflow/store/task_publish_render.py
- tests/unit/test_feishu_cards.py
- tests/unit/test_cards_v2.py 如果存在
- tests/unit/test_commands_messaging.py 如果存在
- tests/unit/test_task_publish_render.py
- docs/competitive-analysis/2026-07-01-eduflow-upgrade-map/08-residency-phase1-branch-impact-2026-07-02.md 如果存在

实现范围：
1. 如果 `cards_v2.py` 已存在：
   - 不要新建 `card_protocol.py`。
   - 审查 `CardType`、`REQUIRED_FIELDS`、`agent_role_allowed`、`validate_card`、`render_to_card_dict`。
   - 缺什么补什么，优先补测试。
2. 如果 `cards_v2.py` 不存在：
   - 才新增最小结构化协议模块，文件名优先 `src/eduflow/feishu/cards_v2.py`。
3. card types 第一版以现有分支为准：
   - `ACK`
   - `START`
   - `PROGRESS`
   - `HANDOFF`
   - `BLOCKED`
   - `REVIEW`
   - `CLOSEOUT`
   - `ALERT`
   - `RECORDED`
4. 如果 M3/M2 需要 `OPS_SNAPSHOT`，不要直接绕开协议；在 schema 里补 `OPS_SNAPSHOT` 或明确用 `PROGRESS`/`ALERT` 适配，并留下迁移说明。
5. payload / body 字段建议：
```json
{
  "card_type": "PROGRESS",
  "task_id": "",
  "workflow_id": "",
  "agent": "",
  "title": "",
  "summary": "",
  "verdict": "",
  "next_owner": "",
  "next_action": "",
  "evidence_refs": [],
  "allowed_sender_roles": [],
  "severity": "info|success|warning|critical"
}
```
6. severity 到颜色映射：
   - success -> green
   - info -> blue
   - warning -> yellow/orange
   - critical -> red
7. 把 M3 employee/team snapshot card 接入现有协议。如果当前 schema 未包含 `OPS_SNAPSHOT`，本模块负责补齐或写清为什么暂缓。
8. 不要求一次性改完 `say` / publish renderer，但要审查它们是否已经调用 `cards_v2`，并补测试防止 worker 越权 CLOSEOUT。

测试要求：
1. payload 缺字段时能 normalize。
2. 每个 card_type 能渲染 v2 schema。
3. severity color 映射稳定。
4. manager 才能 CLOSEOUT；review_course 才能 REVIEW；auto_ops/manager 才能 ALERT。
5. field/value 错误应该 degrade 或返回可审计错误；role violation 应 block。
6. 如果补 `OPS_SNAPSHOT`，必须支持 top_actions/evidence_refs/residency summary。

不要做：
- 不要改飞书 API 调用。
- 不要迁移所有旧 card。
- 不要破坏 simple_card/rich_card 现有测试。
- 不要依赖外部包。
- 不要把自然语言 marker 当作唯一判断依据。
- 不要让 worker_course/review_course 等内容 worker 越权发 CLOSEOUT。

验收命令：
- python -m pytest tests/unit/test_cards_v2.py tests/unit/test_feishu_cards.py tests/unit/test_task_publish_render.py
- 如果 messaging 已接入：python -m pytest tests/unit/test_commands_messaging.py

完成汇报必须包含：
- card_type 枚举。
- payload schema。
- role allow-list。
- 当前 M3/M2 是否已接入。
- 迁移建议：哪些旧卡片后续可以接协议，哪些暂缓。
```

---

# M10：Task Workspace / Worktree Policy Skeleton

## 模块目标

为 P2 的隔离执行做最小 metadata，不立即深接 container-use。先让 task 能记录 workspace policy 和 evidence。

## 推荐提示词

```text
你在 /Volumes/Halobster/Codex相关/EduFlow-Team-orch 工作。

任务：实现 Task Workspace Policy Skeleton。只做 metadata 和最小 worktree policy，不接 container-use 深集成。

必须先读：
- docs/competitive-analysis/2026-07-01-eduflow-upgrade-map/01-claude-squad-agent-orchestrator-container-use-gap-report.md
- docs/competitive-analysis/2026-07-01-eduflow-upgrade-map/05-current-eduflow-planning-recalibration.md
- src/eduflow/store/tasks.py
- src/eduflow/commands/task.py
- tests/unit/test_store_tasks.py
- tests/unit/test_commands_task.py

实现范围：
1. 给 flow task 增加可选字段：
   - `workspace_mode`: `shared | worktree | container | external_artifact`
   - `workspace_path`
   - `workspace_branch`
   - `workspace_base_commit`
   - `workspace_evidence_ref`
2. `task dispatch` 支持可选参数：
   - `--workspace-mode <shared|worktree|container|external_artifact>`
   - `--workspace-path <path>`
   - `--workspace-branch <branch>`
   - `--workspace-base-commit <sha>`
3. 默认不改变现有行为：
   - 未传参数时 `workspace_mode` 可为空或 `shared`，但必须兼容旧任务。
4. `task get` / `task list` / `manager-panel` 里显示 workspace 信息的最小摘要。
5. 只做 metadata，不自动创建 git worktree。
6. 为未来 adapter 留函数或文档注释，但不要调用 destructive git 命令。

测试要求：
1. 创建/dispatch 任务时能保存 workspace fields。
2. 旧任务无 workspace fields 不报错。
3. 非法 workspace_mode 被拒绝。
4. `task get` 输出 workspace_mode。

不要做：
- 不要执行 `git worktree add`。
- 不要接 container-use。
- 不要改真实工作区。
- 不要把 shared 默认任务强制迁移。

验收命令：
- python -m pytest tests/unit/test_store_tasks.py tests/unit/test_commands_task.py
- ./scripts/eduflowteam workflow validate --strict

完成汇报必须包含：
- 新字段。
- CLI 参数。
- 兼容旧任务的策略。
- 后续接 worktree/container-use 的建议。
```

---

# 推荐并行方式

## 可以并行

```text
M4 Runtime/Task Drift Explainer Skill
M5 Harness Surface Audit Skill
M8 Workflow Recommend 扩展
```

这三个模块主要是文档/轻逻辑，冲突少。

## 最好串行

```text
M0.5 Residency Phase1 分支审计（如果分支存在且未合并）
→ merge / adapt decision
→
M1 Employee Read Model
→ M2 Ops Dashboard CLI
→ M3 Feishu Snapshot Cards
```

M2 依赖 M1，M3 依赖 M1/M2；如果 residency 分支存在，M1/M2/M3 又依赖 M0.5 的结论。

## 条件执行

```text
M9 Card Protocol v2 Hardening / Adoption
M10 Workspace Policy Skeleton
```

M9 只有在 `cards_v2.py` 缺字段、缺 `OPS_SNAPSHOT`、缺 role gate 测试，或 M3 接入需要补洞时才执行。M10 仍然暂缓，等 P0 状态可信层和 residency 合并稳定后再做。

---

# 给 Claude Code 的总控提示词

如果你想先让 Claude Code 自己拆分并执行，可以给它这个总控提示词：

```text
你在 /Volumes/Halobster/Codex相关/EduFlow-Team-orch 工作。

目标：按 docs/competitive-analysis/2026-07-01-eduflow-upgrade-map/06-claude-code-module-prompts.md 的模块顺序，先完成 P0 状态可信层升级。

执行顺序：
1. 先执行 M0，只读输出基线报告。
2. 如果存在 `feat/2026-07-01-residency-phase1` 且尚未合并，先执行 M0.5，只读审计该分支，不要合并。
3. 然后执行 M1 Employee Read Model，并把 residency 作为一等状态字段。
4. 再执行 M2 Ops Dashboard CLI，top_actions 必须包含 residency/wake/sleep 相关项。
5. 再执行 M3 Feishu Snapshot Cards，优先复用 `cards_v2.py`。
6. M4/M5 可以在 M1-M3 后执行，也可以并行独立执行。
7. M9 只在 `cards_v2.py` 需要补洞或 M3 接入缺协议字段时执行；不要从零实现第二套协议。

硬性约束：
- 不要重造 runtime guard、workflow engine、verification gate。
- 不要修改真实 `.eduflow-team-state/` 运行数据。
- 不要发送真实飞书消息。
- 不要引入新依赖。
- 不要削弱或跳过测试。
- 所有代码改动必须有单元测试。
- 不要执行 `residency-sleep --apply`，除非任务明确要求真实 sleep；普通模块只能 dry-run/mock/isolated_env。
- 如果 `cards_v2.py` 存在，不要新建 `card_protocol.py` 或重复协议。
- 每个模块完成后运行该模块列出的验收命令。
- 如果遇到依赖模块不存在，停止当前模块并说明缺失依赖，不要临时复制实现。

Done when：
1. M0 已确认当前 HEAD 和 residency 分支状态；如分支存在，M0.5 已输出 ready/blocker 判断。
2. M1/M2/M3 至少完成并通过测试。
3. `./scripts/eduflowteam task ops-dashboard --json` 能返回稳定 JSON，并包含 residency summary 或 degraded reason。
4. Feishu slash/card 单元测试能覆盖 `/employees`、`/employee <agent>`、`/ops`。
5. `./scripts/eduflowteam workflow validate --strict` 仍通过。
6. 最终汇报列出 changed files、测试命令、未完成模块和风险。
```
