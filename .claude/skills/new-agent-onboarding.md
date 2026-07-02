---
name: new-agent-onboarding
description: "新员工入职 skill：覆盖记忆系统、Workflow 派工链路、任务对接、身份文件、通讯规范、团队经验教训六大系统。新 agent 加入团队后按此流程走一遍即可完成全部系统对接。"
metadata:
  type: reference
  generated_by: worker_builder
  date: 2026-06-26
  version: "1.0"
---

# 新员工入职 Skill — EduFlow Team 系统对接指南

## 适用对象

所有新加入团队的 agent（worker_course / review_course / worker_qbank / worker_builder / auto_ops / Hermes / Luke_recorder / manager 备份）。manager 本体不需此 skill。

## 使用方法

新 agent 首次启动后，在 pane 中加载此 skill，按顺序走完以下 6 个模块，每模块末尾有「自检命令」，确认掌握后再进入下一模块。

---

## 模块一：记忆系统（Durable Memory）

### 1.1 记忆是什么

`eduflow remember` 写入的记忆是**跨 /clear 和 tmux pane 重启仍然保留**的持久信息。它不是日志（`eduflow log`）——日志是每步操作的审计流水， verbose；记忆是你希望「睡一觉醒来还记得」的关键信息。

### 1.2 写入命令

```bash
eduflow remember <your-name> <kind> "<内容>" [--ref <引用>]
```

例：
```bash
eduflow remember worker_course learning "AP Physics C E&M 的 items 路径在 02-题库/items/E&M/，不是 Unit N"
eduflow remember worker_course blocker "worker_qbank 的 env_drift 是因为 PROXY_MANAGED 哨兵值被当成 mismatch" --ref T-68
eduflow remember worker_course decision "AP Physics C E&M 和 Mechanics 共用题库根，slug 用 ap-physics-c-em"
eduflow remember worker_course task_completed "T-52 verifier E&M slug/path 修复完工"
eduflow remember worker_course note "boss 偏好 AP 真题先用 PyMuPDF 抽文本，抽不到再走 pdfplumber"
```

### 1.3 kind 分类（`KNOWN_KINDS`）

| kind | 用途 | 什么时候用 |
|------|------|-----------|
| `learning` | 关键经验教训 | 发现坑后立刻写，防止下次重踩 |
| `blocker` | 阻塞点 | 任务卡住、等别人时 |
| `decision` | 重要决策 | 方案选择后的记录，带 **Why** |
| `task_completed` | 完工确认 | 每个任务完成时 |
| `task_assigned` | 接单记录 | 被派活时（通常自动） |
| `note` | 一般备注 | 不属于以上但值得记的 |

**未知 kind 不会被拒绝**（只打 warning），但请用上面的标准分类。

### 1.4 读取与删除

```bash
# 读最近 20 条
eduflow recall <your-name>

# 读最近 N 条 + 过滤 kind
eduflow recall <your-name> --limit 10 --kind learning

# 删除全部（需 --yes 确认）
eduflow forget <your-name> --yes

# 只删某 kind
eduflow forget <your-name> --kind blocker --yes
```

### 1.5 自动注入

每次 pane 启动、CLI 被唤醒时，最近 20 条记忆会**自动注入到 identity.md 的 init prompt 里**。所以记忆写好后不需要手动 "告诉" 自己——下次醒来自然在 prompt 里看到。

### 1.6 上限与淘汰

每人最多 **200 条**，超出后**最老的自动淘汰**。如果某条记忆很重要、不应该被刷掉，定期 `remember` 一次（更新时间戳）可以把它推到最新位置。

### 1.7 存储位置

```
$EDUFLOW_STATE_DIR/facts/<agent>/memory.jsonl
```

每行一条 JSON 记录。**不要直接编辑这个文件**，用 CLI 操作。

### 模块一自检

```bash
# 1. 写一条 learning 记忆：你刚刚知道了什么
eduflow remember <your-name> learning "我刚刚完成了入职记忆系统模块的学习"

# 2. 确认能读出来
eduflow recall <your-name> --kind learning --limit 3

# 3. 记住：以后每踩一个坑，第一件事就是 remember
```

---

## 模块二：Workflow 体系（多智能体派工链路）

### 2.1 整体架构

```
Feishu 群聊消息
    │
    ▼
feishu/router.py  ← 纯函数分类：DROP / ROUTE / SLASH / BROADCAST
    │
    ▼  Decision.ROUTE → manager（默认）
    │
manager 收件箱（inbox.json）
    │
    ▼  manager 决策 + 派工
    │
eduflow send <worker> manager "<任务描述>"
    │
    ▼  worker 收件箱
    │
worker 执行 → eduflow say 回报结果
    │
    ▼  （可选）eduflow send manager worker "完工"
    │
manager 汇总 → 回复 boss（群聊）
```

### 2.2 路由器（router）分类规则

路由器是 `feishu/router.py` 中的 `classify_event()` 纯函数，按顺序匹配：

| 条件 | 动作 | 说明 |
|------|------|------|
| 无 message_id | DROP | 忽略 |
| 已见过 msg_id | DROP | 去重 |
| chat_id 不匹配 | DROP | 跨团队消息 |
| 机器人自发卡片 | DROP | 防止无限循环 |
| 以 `/` 开头 | SLASH | 零 LLM 命令分发 |
| 人类发送 | ROUTE → manager | **所有人类消息默认给 manager** |

**重要**：`@worker_cc`、`@team`、`@all` **不会在 router 层扇出**。它们只是文本内容，manager 读到后手动 dispatch。旧版的 router 扇出已移除。

### 2.3 派工链路（manager → worker）

manager 通过 `eduflow send` 派活：

```bash
eduflow send worker_course manager "请生产 AP Calculus AB Unit 1 的 10 个知识点结构化内容"
```

这条命令做了两件事：
1. 写入 worker_course 的 `inbox.json`
2. 向 worker_course 的 tmux pane 注入提示文本

### 2.4 角色路由表

| 角色 | 负责什么 | 不应该做什么 |
|------|----------|-------------|
| `manager` | 决策 + 派工 + 跟踪 + 验收 + 汇总 | 不应该直接执行 >1min 的工作 |
| `worker_course` | 课程内容生产（知识点结构化、QA 生成） | 不应该改代码、不应该做 review |
| `review_course` | 质量检查、verdict | 不应该生产内容、不应该改代码 |
| `worker_qbank` | 题库生产、导入导出 | 不应该做课程研发 |
| `worker_builder` | 系统建设、工具链、故障维修 | 不应该做课程内容 |
| `auto_ops` | 监控、巡检、健康检查 | 不应该做业务逻辑 |
| `Hermes` | 知识库维护、召回、蒸馏 | 不应该做课程研发 |
| `Luke_recorder` | 团队记录、经验教训总结 | 不应该做课程研发 |

### 2.5 Workflow 命中判断

当 boss（老板）在群聊发消息时：

1. 消息 → router → manager inbox
2. manager 判断是否需要派工：
   - 如果是闲聊/问答 → manager 直接回复
   - 如果是具体任务 → `eduflow send <worker> manager "<任务>"`
   - 如果是集合指令（`@team` / `@all` / `全体X`）→ manager **逐个** `eduflow send` 给每个相关 worker
3. worker 接单 → 执行 → say/send 回报
4. manager 汇总 → say to boss

### 模块二自检

```bash
# 确认你理解了：如果 boss 在群里 @你，消息会怎么到你手里？
# 答案：boss → router → manager inbox → manager send 你 → 你的 inbox
# 你不会直接收到 boss 的消息（除非 manager 转发）
```

---

## 模块三：任务对接（inbox / send / say / read / status）

### 3.1 接单流程（每次 `eduflow inbox` 后）

```bash
# 1. 查看未读
eduflow inbox <your-name>

# 2. 对每条未读消息，执行以下：

#   2a. ACK（标记已读 + 确认接单）
eduflow read <local_id> --ack accepted_task
#   如果是返修/重做任务：
eduflow read <local_id> --ack accepted_revision

#   2b. 对老板说（一句话 ACK）
eduflow say <your-name> "任务已接单：<一句话描述>" --to user

#   2c. 对 manager 说（内部进度）
eduflow send manager <your-name> "已接单，开始处理"

#   2d. 更新自己的状态
eduflow status <your-name> 进行中 "<当前任务>"

# 3. 真正开始执行时
eduflow read <local_id> --ack started_task
eduflow say <your-name> "任务已开始处理：<第一步>" --to user
```

### 3.2 `send` 参数顺序（**极容易搞错**）

```bash
✅ eduflow send <recipient> <sender> "<message>" [priority]
#     你 = sender，第一个参数是你发给谁
# 例：eduflow send manager worker_course "步骤 1 完成" 中

❌ eduflow send <sender> <recipient> "..."   ← 反了！
```

助记：**"发给谁" 在前，"谁发的" 在后**。和微信发消息一样——你先选联系人，再输入内容。

### 3.3 `say` 参数顺序 + `--to`（**必须带 --to**）

```bash
✅ eduflow say <your-name> "<消息>" --to user
✅ eduflow say <your-name> "<消息>" --to manager

❌ eduflow say "<消息>"                          ← 缺 agent 名
❌ eduflow say <your-name> "<消息>"               ← 缺 --to（会 fallback 但不靠谱）
```

**`--to` 的作用**：`chat.publish` 过滤器用它判断这条消息该发给谁。

| --to 值 | 含义 | 过滤规则 |
|---------|------|---------|
| `user` | 对老板说 | 受 `worker_to_user` 配置控制（默认 false） |
| `manager` | 对 manager 说 | 受 `worker_to_manager` 配置控制（默认 true） |

**⚠️ 大坑**：`worker_to_user` 默认是 `false`——worker 的 `--to user` 消息默认**不会出现在群聊里**。manager 可以在 `eduflow.toml` 的 `[chat.publish]` 或 `[team.agents.<name>.publish_overrides]` 里覆盖。所以 worker 发 `--to user` 不代表 boss 一定能看到——这是设计如此，不是 bug。

### 3.4 `read` 的 ack 值

| ack 值 | 什么时候用 |
|--------|-----------|
| `accepted_task` | 首次接单 |
| `accepted_revision` | 返修/重做 |
| `started_task` | 真正开始执行（执行完 3.1 的步骤后） |

### 3.5 `status` 更新

```bash
# 开始任务
eduflow status <your-name> 进行中 "<任务描述>"

# 完成
eduflow status <your-name> 已交付 "<完成了什么>"

# 待命
eduflow status <your-name> 待命 "<等待新任务>"
```

### 3.6 在岗外显协议（Visible Presence）

接单后不要长时间静默。老板和 manager 需要知道你还活着：

| 时机 | 说什么 | --to |
|------|--------|------|
| 接单后 | "任务已接单：XXX" | user |
| 开始执行 | "任务已开始处理：第一步 XXX" | user |
| 每 10 分钟 / 完成一个阶段 | "阶段进度：已做 A，正在 B，下一步 C" | user |
| 暂无新结果 | "阶段进度：暂无新结果，仍在 XXX" | user |
| 卡住 | "当前卡在：XXX，已回报 manager" | user |
| 卡住时同步告诉 manager | 详细的阻塞点信息 | manager（用 send） |
| 交接 | "已交接：XXX，等待 review/manager" | user |

**群聊消息要短**：不要贴日志、secret、stack trace、长报告。

### 模块三自检

```bash
# 确认你记住了：
# send 的参数顺序是：recipient, sender, message
# say 的参数顺序是：agent_name, message, --to
```

---

## 模块四：身份文件（identity.md）

### 4.1 位置与结构

每个 agent 有一个身份文件：

```
.eduflow-team-state/agents/<agent_name>/identity.md
```

**这个文件决定了你每次醒来知道自己是谁。**

### 4.2 标准结构

```markdown
# <agent_name> — <一句话角色描述>

You are **<agent_name>**, a team worker. Your role is **<角色描述>**
running on **<cli>** (model: `<model>`).

## Your job
- 核心职责列表
- 接单 / ACK / 汇报 流程
- 通讯规范（命令示例）

## Argument-order contract
send / say 的参数顺序说明

## Working directory rule
不要 cd 到哪里、runtime_config.json 在哪

## Quick reference
常用命令速查

## Memory usage
怎么用 memory 系统
```

### 4.2.1 model 字段自动填充

identity.md 第一行的 `model` 字段由系统自动填充，不需要手动写：

- 来源：`eduflow.toml` → `[runtime_registry.<name>].model` → 团队 `default_model` 回退
- 解析函数：`src/eduflow/runtime/config.py::resolved_agent_config()` 四级联查
  1. runtime chain 的 selected model
  2. agent 自身 `model` 字段
  3. `$EDUFLOW_DEFAULT_MODEL` 环境变量
  4. `eduflow.toml` 的 `default_model`（默认 `opus`）
- 渲染入口：`src/eduflow/agents/identity.py` → `render()` → `_WORKER_BODY` 模板第 279 行
- 新 agent 雇佣时：`lifecycle.provision_pane()` 自动调用 `identity.write()`，model 已传入

**自检**：确认自己的 identity.md 第一行包含 `model: <xxx>`，如果不为空说明已正确注入。

### 4.3 必读规则

1. **你 = 文件名里的那个 agent**。如果你是 `worker_course`，你的所有 `eduflow say` / `eduflow send` / `eduflow status` 里出现的 agent 名都应该是 `worker_course`。
2. **不要改自己的 identity.md**。如果 identity.md 需要更新，report 给 manager，由 worker_builder 或 manager 来改。
3. **每次 pane 启动会自动重读 identity.md**。所以改完后需要 `eduflow reidentify <your-name>` 才能生效。
4. **identity.md 会包含记忆注入内容**。在 init prompt 里，identity.md 后面会追加 `eduflow remember` 写入的最近 20 条记忆。

### 4.4 红线区（⚠️）

每个 agent 的 identity.md 开头都有红线区——**这些是绝对不能违反的规则**。不同 agent 的红线不同：

- **manager**：不直接执行 >1min 的工作、集合指令必须逐个 dispatch、5 分钟巡视
- **worker**：接单后必须 ACK、不要长时间静默、say 必须带 --to
- **auto_ops**：不修改业务数据、只读监控

**新 agent 第一件事：读自己的 identity.md，把红线区记住。**

### 4.5 修改 identity.md 的流程

```bash
# 如果你需要更新自己的身份文件：
eduflow send manager <your-name> "请求更新 identity.md：<原因>"

# 或者由 worker_builder 统一维护：
eduflow reidentify <your-name>          # 重新注入
eduflow reidentify --all                # 全员重新注入
```

### 模块四自检

```bash
# 1. 读自己的 identity.md
cat .eduflow-team-state/agents/<your-name>/identity.md

# 2. 确认红线区是什么
# 3. 确认你的 Working directory rule 是什么（不要 cd）
```

---

## 模块五：通讯规范

### 5.1 红线汇总（所有 agent 通用）

| 红线 | 违反后果 |
|------|---------|
| 不要 `cd` 到其他目录再跑 `eduflow` 命令 | `runtime_config.json` 找不到，命令失败 |
| `say` 必须带 `--to` | 过滤器分不清意图，消息可能到不了该到的人 |
| `send` 参数顺序不能反 | 消息发给错误的人 |
| 不要改其他 agent 的 identity.md | 身份混乱 |
| 不要直接编辑 `memory.jsonl` / `inbox.json` | 数据损坏 |
| 不要在生产环境暴露 token / secret | 安全风险 |

### 5.2 角色边界

| 原则 | 说明 |
|------|------|
| 谁的地盘谁管 | 课程研发 → worker_course，review → review_course，系统维修 → worker_builder |
| 不要越权 | review_course 不应该改代码，worker_course 不应该做系统配置 |
| 遇到模糊地带 → 回报 manager | manager 决定派给谁 |

### 5.3 5 分钟 Cadence（manager 专用，其他 agent 了解即可）

manager 在派活后必须每 5 分钟用 `eduflow peek <worker>` 检查进度。这是 manager 的红线，其他 agent 不需要主动触发。

### 5.4 派活格式（manager → worker）

manager 派活时应包含：
- **目标（goal）**：要达成什么
- **验收标准（acceptance criteria）**：怎么算做完了
- **边界（boundary）**：不应该改什么

不应该包含详细的 "怎么做"（How），除非 worker 主动问。

### 5.5 完工回报格式（worker → manager）

```bash
eduflow send manager <your-name> "T-XX 完工：<完成了什么>，产出路径：<路径>，验证结果：<pass/fail + 简述>"
```

如果需要老板看到：
```bash
eduflow say <your-name> "T-XX 完工 ✅ <一句话结果>" --to user
```

### 5.6 常用命令速查

```bash
# 收件箱
eduflow inbox <your-name>

# 标记已读 + ACK
eduflow read <local_id> --ack accepted_task

# 发送消息给其他 agent
eduflow send <recipient> <sender> "<msg>" [高|中|低]

# 群聊发消息
eduflow say <your-name> "<msg>" --to user|manager

# 更新状态
eduflow status <your-name> 进行中|已交付|待命 "<描述>"

# 写记忆
eduflow remember <your-name> <kind> "<内容>"

# 读记忆
eduflow recall <your-name> [--limit N] [--kind K]

# 快速看自己 pane
eduflow peek <your-name>

# 健康检查
eduflow health

# 任务完成
eduflow task done <T-id>
```

### 模块五自检

```bash
# 确认你能回答：
# 1. 如果你的任务做完了，要发几条消息？分别发给谁？
#    答：至少 2 条 — eduflow send manager（内部完工） + eduflow say --to user（对外完工）
# 2. 如果你卡住了，第一件事是什么？
#    答：eduflow say --to user "当前卡在 XXX" + eduflow send manager 详细阻塞信息
```

---

## 模块六：团队现有经验与教训

### 6.1 已知坑位（按时间倒序）

| 日期 | 坑 | 教训 |
|------|-----|------|
| 2026-06-26 | `worker_to_user=false` 导致 worker 的 say 不显示在群聊 | 这是设计：worker 不直发 user，全部走 manager→user 通道。不是 bug，不要试图修改 chat.publish 配置 |
| 2026-06-25 | AP Physics C E&M vs Mechanics 共用题库根但路径布局不同 | E&M 路径在 `02-题库/items/E&M/unit-N/`（无 U 前缀），Mechanics 在 `Unit N/`。verifier 需要区分 |
| 2026-06-23 | `PROXY_MANAGED` 哨兵值被 env_drift 检测当成 mismatch | `ANTHROPIC_AUTH_TOKEN=PROXY_MANAGED` 是合法哨兵，env 比对时应该 skip |
| 2026-06-23 | `git worktree` 父仓库 `.git` 会间歇性消失 | 本仓库是 git worktree，parent 消失时 git 命令会 fatal。`git stash` 有丢改动风险——优先用 Edit 工具直接改 |
| 2026-06-21 | tmux pane 初始 shell 的 `$PATH` 未展开 | `PATH=...:$PATH` 可能导致字面 `$PATH` 残留。应硬编码完整 PATH |
| 2026-06-21 | `ps -o command=` 默认截断长路径 | 用 `ps -ww -o command=` 防止截断 |
| 2026-06-21 | pid 文件被外部 unlink 导致 health 误报 | watchdog 已加 pidlock.repair_pid_file() 自愈逻辑 |
| 2026-06-21 | lark-cli 通过 npx 启动时 73s 延迟 | npx 的 package-lookup 开销极大。已改为 `feishu/lark._resolve_cli_prefix` 绕过 npx |

### 6.2 团队约定

1. **测试伴随代码**：新模块必须同 commit 带 unit test
2. **Operator playbook**：新命令必须带 `tests/scenarios/*.md` Given/When/Then
3. **Two-use rule**：抽象/基类只在第三次使用时才提取
4. **Dead code = delete**：`grep` 找不到调用就删掉
5. **单文件上限 ~300 LOC**：超过就考虑拆分
6. **No compatibility shims**：未发布的代码直接改，不要留 wrapper

### 6.3 文件结构速览

```
.eduflow-team-state/
├── agents/
│   ├── manager/identity.md
│   ├── worker_course/identity.md
│   ├── review_course/identity.md
│   ├── worker_builder/identity.md
│   ├── worker_qbank/identity.md
│   ├── auto_ops/identity.md
│   ├── Hermes/identity.md
│   └── Luke_recorder/identity.md
├── inbox/           # 各 agent 收件箱
├── facts/           # 各 agent 记忆
│   ├── <agent>/memory.jsonl
└── status/          # 各 agent 状态

src/eduflow/
├── cli.py           # 命令入口 + 注册表
├── commands/        # 每个子命令一个模块
├── store/           # 文件本地状态
├── runtime/         # 配置 / 路径 / tmux / watchdog
├── feishu/          # lark-cli 封装 + router
└── agents/          # CliAdapter 基类 + 各 adapter

.claude/skills/      # 已有 42 个 skill 文件
```

### 6.4 工具链

- **PDF 抽取**：PyMuPDF 1.27 + pdfplumber 0.11（T-68 已安装）
- **CLI 运行时**：claude-code / qwen-code / gemini-cli / kimi-code 均有 adapter
- **飞书**：lark-cli 事件订阅（+subscribe），NDJSON 格式

### 6.5 常见问题 FAQ

**Q: 我收不到消息怎么办？**
A: 检查 `eduflow inbox <your-name>`。如果 inbox 为空但你应该收到，可能是 manager 还没 dispatch，或者 router 配置有问题。找 manager 或 auto_ops。

**Q: 我的 pane 重启后记忆还在吗？**
A: 在。`eduflow remember` 写入的是磁盘文件（`facts/<agent>/memory.jsonl`），pane 重启后 init prompt 会自动注入最近 20 条。

**Q: 我该用什么 model？**
A: 看 `eduflow.toml` 里你的 `[team.agents.<name>]` 段，`runtime` 字段指定了你的主备运行时。不需要自己指定 model。

**Q: 我可以帮另一个 agent 干活吗？**
A: 不可以。每个 agent 有自己的职责边界。如果你觉得某事该做，report 给 manager，让 manager dispatch 给负责的 agent。

**Q: 测试失败了怎么办？**
A: 报告失败，不要静默跳过。`python3 tests/run.py` 的输出应该如实反映。如果是 pre-existing failure（已知的不相关失败），注明 "pre-existing"。

### 模块六自检

```bash
# 确认你读了以下文件：
# 1. eduflow.toml — 看你的 runtime 配置
# 2. .eduflow-team-state/agents/<your-name>/identity.md — 你的身份
# 3. 上面的已知坑位表 — 避免重踩
```

---

## 入职完成检查清单

走完以上 6 个模块后，新 agent 应该能独立完成以下操作：

- [ ] 读自己的 identity.md 并记住红线
- [ ] 查看 inbox、ACK 消息、开始执行任务
- [ ] 用 `send` 给 manager 发消息（参数顺序正确）
- [ ] 用 `say` 给群聊发消息（带 `--to`）
- [ ] 用 `remember` 写入一条 learning 记忆
- [ ] 用 `recall` 读回自己写的记忆
- [ ] 更新自己的 status
- [ ] 说出至少 3 个已知坑位
- [ ] 知道遇到问题时该找谁（manager）

**全部勾选后，按顺序执行报到流程：**

```bash
# 第一步：确认 identity.md model 字段已注入
cat .eduflow-team-state/agents/<your-name>/identity.md | head -1
# 确认输出包含 model: <xxx>

# 第二步：向 manager 报到（正式上岗信号）
eduflow send manager <your-name> "新员工 <your-name> 报到：identity.md 已读（model: <xxx>），红线已记，inbox 已清空，所有系统对接确认完毕，正式上岗待命中。"

# 第三步：向群里发一句外显
eduflow say <your-name> "<your-name> 正式上岗 ✅" --to user

# 第四步：写入完成记忆
eduflow remember <your-name> task_completed "新员工入职 skill 学习完毕，所有模块自检通过，已报到上岗"
```
