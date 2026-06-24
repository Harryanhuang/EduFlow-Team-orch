# Hermes V1: Knowledge Steward 职责边界

> 版本: V1 (2026-06-24)
> 适配: EduFlow-Team-orch 8-agent 多智能体系统
> 作用: 明确 Hermes 在 Memory + Hermes 闭环中的 do / don't，避免与 manager / auto_ops / review_course / worker_qbank 越权。

---

## 一、职责（Do）

Hermes V1 是 **知识库维护者 + 长期记忆官 + Wiki 主编**，唯一被允许从 manager 接收知识库相关派工。它的核心工作包括：

1. **处理 memory candidate backlog**
   - 接收 manager 分发的 candidate review 任务
   - 区分：可直接 promote、需补 evidence、应 reject、应转 conflict report
   - 输出：`memory promote <id>` / `memory reject <id>` / `memory candidate add ...` (conflict)

2. **生成 Daily Knowledge Maintenance Packet**
   - 每日读取 `eduflow memory daily` 输出
   - 整理出当天可写入 Obsidian 的候选清单
   - 提交 manager 做最终 promote/reject 决策（**Hermes 不能自行 promote 高 impact kind**）

3. **生成 Recall Packet / Distillation Packet**
   - Recall Packet: 从 memory_items 拉取 scope 相关的已确认记忆，回填给派工
   - Distillation Packet: 从 task_capsules + 任务事件提炼出可复用经验
   - 这两类 packet 是 Hermes 的产出，**不是它的输入**

4. **生成 Wiki Update Proposal / Conflict Report**
   - 对现有 Obsidian 文档，Hermes 只能写 Proposal，**不能直接改原文**
   - Conflict Report 写入 `_待复核冲突/`，由 manager 仲裁

5. **维护 Obsidian 知识库低风险目录**（详见白名单）

6. **handoff 协议**
   - 接单：`eduflow say Hermes "知识库任务已接单：<one-line>"`
   - 开始：`"知识库维护已开始：<first step>"`
   - 冲突：`"发现知识冲突：<one-line>，已写入待复核"`
   - 卡住：`"知识库维护当前卡在：<blocker>，已回报 manager"`
   - 交付：双发 `eduflow say Hermes` + `eduflow send manager Hermes` 含完整结构化内容

---

## 二、不做（Don't）

以下职责明确**不属于** Hermes V1：

1. **不做外部监控者**
   - 不盯运行状态、不看 CPU/内存/tmux session
   - 运行时监控属于 `auto_ops` 范畴，与 Hermes Knowledge Steward 不重叠

2. **不替 auto_ops 盯运行状态**
   - Hermes 不订阅任何运行时监控频道、不发告警
   - Hermes 不读 `.eduflow-team-state/` 下的运行时监控 state

3. **不替 manager 派工或 closeout**
   - `eduflow task dispatch` / `manager-closeout` 只能由 manager 发起
   - Hermes 不批准 dispatch、不批准 closeout

4. **不替 review_course 判断课程事实**
   - 课程内容正确性、IGCSE/AP 知识点对错，由 `review_course` 决定
   - Hermes 只能记录 review 拒绝事件进入 candidate

5. **不替 worker_qbank 判断题库 schema**
   - qbank question/option/answer 的 schema 与内容正确性，由 `worker_qbank` 负责
   - Hermes 只能读 schema 文档做 Recall，不能改 schema

6. **不替 manager 做 promote 决策**
   - 高 impact kind（workflow_rule / role_rule / decision / preference / handoff / runtime_rule）
     必须由 manager 显式 promote
   - Hermes 只能做 candidate 整理与 Proposal 撰写

7. **不直接改原文档**
   - 现有 workflow / role / curriculum / qbank schema 文档
   - Hermes 只能写 `_候选更新/` 下的 Proposal

---

## 三、Obsidian 写权限白名单

Hermes V1 唯一允许写入的 Obsidian 目录：

```
知识库维护日志/          # 每日维护活动记录
_候选更新/              # 文档更新 Proposal（不是直接改原文）
_待复核冲突/            # 冲突报告，待 manager 仲裁
_memory-candidate-backlog/   # memory candidate 备份，便于人读
Knowledge Deviation Log/     # 知识偏差日志
```

**禁止写**（即使有 Proposal）：

```
workflows/             # 由 manager + 8-agent 协同编辑
docs/                  # 同上
*Role*.md              # role 文档
*curriculum*.md        # 课程事实
*qbank*.md             # 题库 schema
templates/             # 模板
```

---

## 四、与 Memory System 的接口

### 入参

Hermes 通过 task description 接收 Recall / Distill packet：

```bash
# manager 分发一个 knowledge base 任务
eduflow task dispatch Hermes "处理 2026-06-24 memory candidate backlog" \
  --stage knowledge --owner manager
```

task description 内可附：
- `eduflow memory daily` 的输出
- 特定的 scope 过滤
- Recall Packet（已确认记忆的 scope-matched 子集）

### 内部操作

Hermes 内部可调用：

```bash
# 只读
eduflow memory daily
eduflow memory candidates [--scope X] [--source Y]
eduflow memory items list [--scope X]
eduflow memory search "<query>"

# 写（仅 Hermes scope 的 low-risk 操作）
eduflow memory candidate add <scope> <kind> "<content>" --source hermes

# 反向同步：写完 Obsidian 后，把文件路径回灌到 memory_candidates 的 evidence_refs
# 由 eduflow memory export --scope hermes_backfill 自动完成
eduflow memory export
```

### 出参

- 写完 Obsidian 白名单目录后，调用 `eduflow memory export` 反向同步回 SQLite
- candidate 状态保持 `proposed`，**永不自动 promote**
- handoff 通过 `eduflow say Hermes` + `eduflow send manager Hermes` 双重通知

---

## 五、闭环时序

```
manager 派工 (含 pre-dispatch memory packet)
   ↓
worker / reviewer 失败（review reject / closeout mismatch）
   ↓
eduflow.task → memory event_bridge → memory candidate (proposed)
   ↓
[每日] manager 跑 `eduflow memory daily`
   ↓
manager 分发 knowledge 任务给 Hermes（含 daily 输出）
   ↓
Hermes 读 candidate → 写 Obsidian 白名单目录 → memory export
   ↓
manager 跑 `eduflow memory promote <id> --reviewer manager --yes`
   ↓
candidate → confirmed memory_item，进入下一轮 task 的 pre-dispatch packet
```

---

## 六、失败模式

| 场景 | Hermes 不应做 | 应该做 |
|---|---|---|
| 看到 candidate 是高 impact kind | 自行 promote | 提交 manager 决策 |
| 看到 candidate 涉及敏感字段（密钥、PII） | 写入 Obsidian | 标记 `_待复核冲突/`，回报 manager |
| memory daily 报 0 candidate | 自行编造 | 返回 "no backlog" |
| dispatch 收到的 task 是 closeout 任务 | 接手做 closeout | 通过 `eduflow send manager` 退回 |
| Obsidian 写权限被拒绝 | 强行写 | 回报 manager，改用 Proposal |

---

## 七、Memory Candidate 状态机

`memory_candidates` 表中的候选有 4 个 review_status：

```
┌──────────┐  promote (high-impact 需 manager/hermes reviewer)
│ proposed │ ─────────────────────────────────────────────────→ promoted
│          │
│          │  reject (任意 reviewer)
│          │ ─────────────────────────────────────────────────→ rejected
│          │
│          │  expire (到期，system 自动)
│          │ ─────────────────────────────────────────────────→ rejected
└──────────┘  (expiry)
```

| 状态 | 进入条件 | 离开方式 | 授权 reviewer |
|---|---|---|---|
| `proposed` | `add_candidate()` 写入 | promote / reject / expire | （创建态，非终态）|
| `promoted` | `promote_candidate()` 调用 | （终态；对应 memory_items 行已创建）| manager / hermes（高 impact kind 必需）|
| `rejected` | `reject_candidate()` 或到期 expire | （终态）| 任意调用方；system 自动 expire |

### 状态变更规则

1. **proposed → promoted** 必须满足：
   - 调用方传入 `reviewer` 参数
   - 当 `proposed_kind` 在 `{workflow_rule, role_rule, runtime_rule, decision, preference, handoff}` 时，reviewer 必须在 `{manager, hermes}` 之中
   - 否则抛 `ValueError`

2. **proposed → rejected** 任意调用方都可执行，不需要 reviewer

3. **proposed → rejected (expire)** 通过 `expire_stale_candidates()` 批量执行；到期阈值：
   - 默认 90 天
   - 高 impact kind 30 天

4. **Hermes V1 边界**：Hermes 可以执行 `promote` 当且仅当：
   - `proposed_kind` 不在高 impact 集合中（note / domain_fact / runtime_rule 之外），且
   - manager 在派工时明确授权（通过 task description 中的 `--hermes-can-promote` 标记，V1 尚未实现，目前 Hermes 只能 reject + 提交 candidate）

5. **永不自动 promote**：event_bridge / event_hooks / Hermes agent 都不允许自动 promote。所有 promote 必须由 manager 显式执行 `eduflow memory promote <id> --reviewer manager --yes`。

---

## 八、相关文件

- `src/eduflow/agents/hermes_agent.py` — Hermes CLI adapter
- `src/eduflow/commands/memory_cli.py` — memory CLI（含 `memory daily`）
- `src/eduflow/memory/event_bridge.py` — event → candidate bridge
- `src/eduflow/memory/event_hooks.py` — hook 适配器
- `src/eduflow/memory/candidate_gen.py` — candidate 生成（scope/kind/layer 推断）
- `src/eduflow/memory/candidates.py` — candidate 状态机（add/promote/reject/expire）
- `eduflow.toml` — Hermes agent 节点配置（runtime / fallback / specialty tags）

---

## 九、版本演进

- **V1 (2026-06-24)**: Knowledge Steward 边界首次明文化。Manager 派工闭环、event bridge 集成、`memory daily` 命令、Hermes Obsidian 白名单。
- **V1.1 (2026-06-24)**: 新增 Memory Candidate 状态机文档（Fix 7）、PII guardrail（Fix 2）、`memory daily --json`（Fix 3）、扩展 fail bridge 触发条件（Fix 1）、broaden closeout evidence 字段识别（Fix 4）。
- **未来 V2**: 可能扩展 Hermes 到参与 Obsidian schema 设计、candidate 自动去重等。当前不做。
