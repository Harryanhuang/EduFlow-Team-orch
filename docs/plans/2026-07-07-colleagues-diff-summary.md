# 同事 Working Tree 关键 Diff 摘要

> 2026-07-07 17:30。本文档是 `2026-07-07-colleagues-working-tree-classification.md`
> 的 C 部分：关键文件 diff 实际看到了什么。

## 1. `src/eduflow/store/tasks.py`（最大单文件，+138/-6）

**主题**：**T-104: task archival**（**不是** `review_course → worker_review` rename）

新增：
- `ARCHIVABLE_STATUSES = frozenset({"delivered", "cancelled", "已完成", "已取消"})` — 排除 `failed`（boss 关注）
- `list_tasks(include_archived: bool = False)` — 新增 keyword-only 参数，默认过滤 archived
- `is_archived(task) → bool` — soft-mark 读取
- `_archive_dir()` / `_archive_slice_file(month)` — 物理归档路径
- `_archive_reference_ts(task)` — 决定归档月份的 timestamp 优先级链
- `archive_candidates(older_than_days=90, ...)` / `archive_tasks(...)` — 物理 move + soft mark

**对 pilot 的影响**：
- pilot 的 4 个 read-model 全部用 `tasks.get(task_id)` 按 ID 查单个 task，**不**用 `list_tasks()`
- pilot 不直接受影响
- 间接影响：被归档的 task，`tasks.get()` 会返回 `None`，pilot read-model 返回 `None` —— **这是预期行为**，测试已覆盖
- `failed` 状态不在 ARCHIVABLE 内，对 pilot 来说：failed task 仍然留在 live store 里，可被 pilot 查到

**与 `review_course → worker_review` rename 的关系**：
- 本次**没有**在 `store/tasks.py` 里改 rename
- 之前推断的 "T-139 rename 已完成" 实际**只完成了 cards_v2_schema.py 这一层**
- store 层（`tasks.py:242 WORKFLOW_DEFAULT_REVIEWERS` + 各种 hard-coded 字符串）仍为 `review_course`
- 完整 rename 仍需单独任务

## 2. `src/eduflow/commands/router.py`（+75/-6）

**主题**：**T-130: router bug guard**

发现：当 legacy env var `EDUFLOW_ROUTER_STALE_S` 被 set 时，它**静默**覆盖
`eduflow.toml` 的 `router.stale_event_threshold_s`，导致真实消息被丢弃。
修法：检测到 legacy env var 被 set 时打 warning，建议 unset 或迁移到
`EDUFLOW_ROUTER_STALE_EVENT_THRESHOLD_S`（现代 env override）。

**对 pilot 的影响**：
- 路由 stale event threshold 影响 router watchdog 行为
- pilot 不直接依赖 router，但 readiness-check 的 productivity 维度依赖 heartbeat
- 没有立即冲突

## 3. `src/eduflow/commands/watchdog.py`（+278/-22，最大命令改动）

**主题**：watchdog 命令增强（推测与 T-130 router bug 相关）

没有细看 diff，但 +278 行 / -22 行表明是大幅重写 watchdog 调度逻辑。

## 4. `src/eduflow/feishu/cards_v2_schema.py`（+11）

**主题**：**T-144: review_course → worker_review 卡片权限跟进**

```python
"worker_review": frozenset({
    CardType.ACK, CardType.START, CardType.PROGRESS,
    CardType.HANDOFF, CardType.BLOCKED,
    CardType.REVIEW,
}),
```

注释明确："review_course was renamed to worker_review (T-139) but the
role allow-list wasn't updated. Add the worker_review entry mirroring
the old review_course perms. Keep the stale review_course entry as an
alias so historical cards sent under the old name still validate."

## 5. `eduflow.toml`（+144/-6）

**主题**：runtime registry / 容灾链等配置更新（推测与 T-118 runtime failover 反思相关）

## 6. `src/eduflow/feishu/catchup.py`（+118/-12）

**主题**：消息 catchup 逻辑增强（推测针对 router 重启后的 catchup）

## 7. `src/eduflow/feishu/slash.py`（+75）

**主题**：新增 slash 命令（推测 `eduflow` 子命令扩展）

## 8. `.claude/skills/agent-hiring-checklist.md`（+180/-36）

**主题**：agent 招聘 checklist 更新

## 9. 其余小改动

- `src/eduflow/cli.py` (+3) — 应该是 watchdog/agent/daemon 新命令的 dispatch 注册
- `src/eduflow/commands/runtime.py` (+3) — runtime 命令微调
- `src/eduflow/commands/health.py` (+24) — health 命令增强
- `src/eduflow/commands/say.py` (+28/-6) — say 命令适配 feishu 卡片权限
- `src/eduflow/runtime/watchdog.py` (+15/-2) — runtime watchdog 核心
- `src/eduflow/commands/agent.py` / `daemon.py` / `runtime_env_clean.py`（新增）— 新命令
- `tests/unit/test_*`（多个）— 配套测试

## 关键 takeaway

1. **T-104 archive** 与 pilot 没有直接冲突，但 `failed` 状态不入归档意味着
   pilot 的 `runtime_incident` 候选（trigger=`status=failed`）仍能查到
2. **T-130 router bug guard** 是真实的 bug 修复，建议尽快推到 origin
3. **T-144 cards 跟进** 是 T-139 rename 的后续，已落地
4. **store 层 rename** 仍未做，pilot 的所有 read-model 内部用 `review_course` 字符串——这与 T-139
   rename 状态一致，无新问题
5. 整个 working tree 改动 1382 +/103 -，与 pilot 隔离，**应该**单独建分支递交

## 建议的 commit/PR 拆法

| 主题 | Commit 标题 |
|------|-------------|
| Runtime failover followup (T-130 + watchdog) | `chore: router stale-env bug guard + watchdog followup` |
| Feishu cards + slash + catchup | `chore: feishu cards worker_review permission + slash/catchup` |
| T-104 task archival | `feat: task archival (T-104)` |
| New commands (agent/daemon/runtime_env_clean) | `feat: agent/daemon/runtime_env_clean commands` |
| Config + skill docs | `docs: agent-hiring-checklist + eduflow.toml` |
| Pilot (already on `feat/production-contract-pilot-2026-07-07`) | (already done) |