# Eduflow ↔ oh-my-claudecode 对比与借鉴分析

> 生成日期：2026-07-01
> 对比对象：[oh-my-claudecode (OMC)](https://github.com/Yeachan-Heo/oh-my-claudecode) v4.15 vs EduFlow-Team-orch

---

## 一、两个项目的定位差异

理解差异之前，先看清两者的本质定位，这决定了哪些东西能借鉴、哪些不能硬搬。

OMC 是一个 **Claude Code 原生的多智能体编排插件**。它的核心命题是"让 Claude Code 自己变成一个团队"——所有 agent 都是 Claude Code 内的 subagent，通过 hooks 注入行为、skills 定义编排模式、agents 定义角色契约，state 跟踪跨上下文进度。它不关心外部聊天平台，用户直接在 Claude Code 会话里操作。

Eduflow 是一个 **本地可审计的 AI 团队操作系统**。它的核心命题是"把多个不同的 CLI agent 放进 tmux，通过飞书群远程操控"——agent 是真实的外部 CLI 进程（Claude Code / Codex / Gemini / Kimi / Qwen / Qoder），manager 调度，飞书群做控制面，本地文件+SQLite 做状态。用户可以在手机飞书群里下指令。

这意味着：OMC 的很多"会话内编排"设计可以直接借鉴到 Eduflow 的 manager 角色和 worker 协作协议里；但 OMC 的 Claude Code 插件分发、hooks 注册等基础设施层面的事情，对 Eduflow（Python + tmux + 飞书）不直接适用。

---

## 二、Eduflow 已经比 OMC 强的地方（不要丢掉）

在说借鉴之前，先确认 Eduflow 的独有优势——这些是 OMC 完全没有的：

**飞书群控制面**。OMC 没有任何外部聊天平台集成，用户只能在 Claude Code 终端里操作。Eduflow 的飞书 slash command、卡片回报、健康检查报警、手机端遥控，是真正的差异化能力。这是 Eduflow 不需要向 OMC 学习、反而 OMC 可以向 Eduflow 学习的部分。

**多 CLI 异构编排**。OMC 本质是 Claude Code 单引擎，虽然 v4.4 加了 Codex/Gemini/Antigravity 的 tmux CLI worker，但它们都是"一次性 spawn、完成即死"的临时 worker。Eduflow 的 7 个 adapter（claude_code / codex_cli / gemini_cli / kimi_code / qwen_code / qoder_cli_cn / hermes_agent）是持久身份的独立 agent，有自己的 identity、记忆、任务队列。这种异构持久编排能力比 OMC 更成熟。

**教育领域工作流**。Eduflow 的 IGCSE/A-Level/AP 学科生产线、题库验证、knowledge base 工作流 registry，是 OMC 完全不具备的领域纵深。

**崩溃恢复韧性**。Eduflow 的 cross-pool failover、stale-event 120s 检测、lark-cli 锁竞争处理、flap-guard、watchdog orphan-reap，这些在生产环境里打磨出来的运行时韧性，OMC 的 worktree 隔离和 state 持久化并不能替代。

**Flow Memory 插件**。Eduflow 的记忆系统已经抽取成独立 package，有 SQLite/Postgres/Markdown 三种 backend、LanceDB 向量存储、23 个 MCP 工具、514 个测试。OMC 的三层记忆（notepad / project-memory / plan-notepad）在架构上反而更简单。

---

## 三、Eduflow 可以借鉴的核心提升点

以下是按影响力和可行性排序的借鉴方向。每条都标注了：OMC 怎么做的、Eduflow 现状、怎么迁移。

### 1. 分阶段编排管线（最高优先级）

**OMC 的做法**：Team 模式是一条 5 阶段管线——`team-plan → team-prd → team-exec → team-verify → team-fix (loop)`。每个阶段用不同的 agent 角色：plan 阶段用 explore(haiku)+planner(opus)，prd 阶段用 analyst(opus)，exec 阶段用 executor(sonnet)，verify 阶段用 verifier(se sonnet)+security-reviewer，fix 阶段回到 executor。verify/fix 循环直到验证通过或超过最大修复轮次（默认 3 轮）。阶段之间写 handoff 文档（Decided/Rejected/Risks/Files/Remaining），即使取消也能恢复。

**Eduflow 现状**：manager 收到目标后直接拆任务、派发给 worker，worker 完成后 say 回报。没有显式的"计划→PRD→执行→验证→修复"管线。workflow registry 提供执行契约，但"真正派发仍由 manager 或操作者显式完成"，没有自动化的 verify/fix 循环。

**怎么迁移**：不需要照搬 OMC 的 19 个 agent 角色，但可以在 Eduflow 的 manager identity 和 workflow 契约里引入阶段化协议。具体做法是在 workflow registry 的每个 workflow 定义里增加 `stages` 字段（plan / exec / verify / fix），manager 按阶段推进，verify 阶段调用独立的 verifier 角色（可以是 hermes 或新建一个 review 角色），fix 阶段把验证发现的问题回派给原 worker。stage handoff 可以落成 `.eduflow-team-state/handoffs/<workflow>/<stage>.md`。这和 Eduflow 现有的 task_publish_gate 和 task_evidence_account 天然契合——publish gate 就是 verify 阶段的关口。

### 2. 分层模型路由用于成本优化（高优先级）

**OMC 的做法**：三层模型分级——LOW(haiku，快速查询/简单任务)、MEDIUM(sonnet，代码实现/调试)、HIGH(opus，架构/审查)。每个 agent 定义里写死 model tier。还有"委派类别"自动检测：从任务描述自动判断是 visual-engineering(HIGH, temp 0.7) / ultrabrain(HIGH, temp 0.3) / artistry(MEDIUM, temp 0.9) / quick(LOW, temp 0.1) / writing(MEDIUM, temp 0.5)，自动决定 model + temperature + thinking budget。核心洞察："规划和审查用贵模型，实现用便宜模型，Sisyphus(实现)从 Opus→Sonnet/DeepSeek 是最大的成本杠杆"。

**Eduflow 现状**：有 multi-provider fallback 链（Qwen/M3/mimo/GLM/Kimi），但这是**故障转移**用的——主 provider 挂了才切备用。没有"按任务复杂度主动选择不同价位模型"的能力。manager 和所有 worker 默认用各自配置的同一个 model。

**怎么迁移**：在 eduflow.toml 的 agent 定义里增加 `model_tier` 字段（budget / balanced / premium），或者更灵活地增加 `task_model_map`——简单查询用 Qwen-Flash，代码实现用 Sonnet/DeepSeek，架构审查用 Opus。manager 派发任务时可以根据任务类型（在 workflow 的 stage 定义里标注）自动选择对应 tier 的 worker 或覆盖 worker 的 model。这对 Eduflow 尤其有价值，因为你有 7 个 CLI adapter，可以在不同价位模型间灵活切换，成本优化空间比 OMC 更大。

### 3. 基于证据的验证循环（高优先级）

**OMC 的做法**：verifier agent 有严格的证据要求——没有 5 分钟内的新鲜测试输出就不批准，拒绝"should/probably/seems"这类语言，必须独立运行验证命令。Ralph 模式在所有 user story 通过后，还要跑一轮强制 deslop（ai-slop-cleaner）+ 回归再验证，防止清理引入新问题。验证协议要求 BUILD / TEST / LINT / FUNCTIONALITY / ARCHITECT / TODO / ERROR_FREE 全部有实际命令输出。

**Eduflow 现状**：有 `task_publish_gate` 和 `task_evidence_account`，有 subject_verifier（ap_subject_verifier / subject_verifier），说明已经有验证和证据收集的雏形。但没有"新鲜证据"要求（验证必须在完成后的时间窗口内），没有 deslop + 回归再验证的强制循环，验证更多是"publish 前过 gate"而不是"verify→fix→re-verify 循环到通过"。

**怎么迁移**：强化 task_publish_gate 的验证逻辑——增加 `evidence_freshness` 检查（验证命令的输出时间戳必须在任务完成后的 N 分钟内），增加 `verify_fix_loop` 机制（验证不通过时自动生成 fix task 回派给 worker，最多 N 轮）。对于教育内容生产，可以增加 deslop 步骤——用独立的 review agent 检查 AI 味道、格式一致性、知识准确性，通过后再回归验证一遍。

### 4. 深度访谈/歧义度量（中优先级）

**OMC 的做法**：deep-interview skill 在写任何代码之前，用苏格拉底式提问量化需求清晰度。跨加权维度（Goal / Constraints / Criteria / Context）打分，每轮针对最低分维度提问。有 Round 0 拓扑枚举门（锁定顶层组件列表后再深入），有歧义阈值（默认 20%，低于阈值才允许进入执行）。还有 brownfield awareness——先用 explore agent 搜集代码库事实，引用 repo 证据而不是让用户重新发现。

**Eduflow 现状**：manager 收到 boss 的目标后直接拆解派发。对于"帮我检查当前任务台账，给出下一步派发建议"这种清晰指令没问题，但对于"帮我做一个 AP 化学知识库"这种模糊目标，缺少需求澄清环节。workflow registry 虽然提供了执行契约，但选择哪个 workflow 本身可能就需要澄清。

**怎么迁移**：在 manager identity 里增加"模糊目标检测→澄清提问"协议。当 boss 的目标包含 ambiguity markers（如"帮我弄一个"/"优化一下"但没有具体标准）时，manager 先进入澄清模式，用结构化提问量化清晰度，低于阈值时拒绝派发并继续提问。对于教育场景，澄清维度可以是：学科范围 / 学段 / 目标产出物 / 质量标准 / 截止时间 / 参考素材。这可以直接落成一个新的 workflow：`requirement-clarification`。

### 5. 实时可观测性：HUD + Agent 观测台（中优先级）

**OMC 的做法**：两层 statusline——HUD 每 300ms 更新，显示 repo/branch、ralph 迭代/最大值、PRD story ID、活跃模式、上下文窗口百分比、运行中 agent 数、后台任务槽位、todo 完成度、调用计数、会话健康度。有三种预设（minimal/focused/full）。颜色编码：绿=健康，黄=警告(ctx>70%, ralph>7)，红=危险(ctx>85%)。还有 Agent Observatory——每个 agent 的实时 tool 调用数、token 用量、估算成本、修改文件数、瓶颈检测（如"Grep 2.3s avg"），5 分钟无活动判定为 stale。

**Eduflow 现状**：有 `eduflow health`（聚合检查）、`eduflow peek`（快速巡视 pane）、`eduflow status`、`eduflow runtime`。但这些是"主动查询"模式，不是"持续可见"模式。没有实时 statusline，没有 per-agent token/cost 追踪，没有瓶颈检测。

**怎么迁移**：Eduflow 的 tmux 环境天然适合做 statusline——tmux status bar 可以显示每个 pane 的状态。可以做一个 `eduflow hud` 命令，输出一行紧凑状态（类似 `[EduFlow] manager:busy ctx:67% | worker_cc:idle | worker_codex:exec 2/5 tasks | watchdog:ok | memory:234 items`），设置成 tmux status bar 或飞书群定时播报。per-agent 的 token/cost 追踪可以利用 `eduflow usage`（已有 ccusage wrapper）扩展，在 health 命令里增加 per-agent 成本摘要。

### 6. 从执行经验自动提取 Skill（中优先级）

**OMC 的做法**：skillify skill 从会话中提取可复用模式，有严格的三问质量门——"5 分钟能 Google 到吗？否"、"是这个代码库/项目/工作流特有的吗？是"、"花了真实的调试/设计/运营 effort 吗？是"——三问全过才生成 skill 文件。生成的 skill 自动注入到后续会话上下文（trigger 匹配时），不需要手动 recall。还有 self-improve——自主代码改进引擎，用 git worktree 做隔离实验分支，锦标赛选择，只合并赢家。

**Eduflow 现状**：有 `docs/workflows/` 的 workflow registry 和 `realrun-to-workflow` 机制，但这是"人工把一次执行沉淀成 workflow 契约"。skills/ 目录有预装的 skill 包，但没有"从一次真实执行中自动提取可复用流程"的能力。

**怎么迁移**：Eduflow 的 workflow registry 已经有"候选→验证→晋升"机制（`workflow recommend` / `workflow use` / `workflow validate`），这比 OMC 的 skillify 更结构化。可以增强的是"自动候选"——当一次 task 完成且 evidence_account 显示结果良好时，manager 自动建议"这次执行的模式可以提取成 workflow 候选"，生成 draft workflow 定义供人审。这比 OMC 的全自动 skillify 更适合 Eduflow 的"可审计"哲学——自动候选、人工晋升。

### 7. 阶段交接文档（中优先级）

**OMC 的做法**：team 的每个阶段完成后写 handoff 文档到 `.omc/handoffs/<stage>.md`，包含 Decided / Rejected / Risks / Files / Remaining 字段。这些文档在上下文压缩或取消后仍然存在，新会话可以读取恢复。

**Eduflow 现状**：有 inbox（消息）、task store（任务状态）、memory（持久记忆），但没有"阶段交接"的专门文档。一个 worker 完成任务后，下一个接手的人（或 manager 自己在上下文被压缩后）需要从 inbox 日志和 task 状态里拼凑上下文。

**怎么迁移**：在 task 完成时，让 worker（或 manager）自动生成一份 handoff note 到 `.eduflow-team-state/handoffs/<task_id>.md`，包含：已决定的事项 / 已拒绝的方案 / 风险 / 涉及文件 / 剩余工作。这和 Eduflow 现有的 task_evidence_account 可以合并——evidence_account 记录"做了什么"，handoff note 记录"为什么这么做、还剩什么"。

### 8. 对抗式审查 + 预判（中优先级）

**OMC 的做法**：critic agent 在审查前先"预判 3-5 个可能的问题区域"（Pre-commitment），这激活了主动搜索而非被动阅读。然后做多视角审查（安全/新人/运维视角），显式 gap 分析（"缺了什么"而非"什么错了"），pre-mortem（"假设这个方案执行后失败了，生成 5-7 个失败场景"），最后自我审计（低置信度的发现移到 Open Questions）。核心原则："虚假批准的代价是虚假拒绝的 10-100 倍"。

**Eduflow 现状**：有 hermes（外部监督/steward 角色）和 review 类 workflow gate，但没有结构化的"预判→多视角→gap 分析→pre-mortem"审查协议。

**怎么迁移**：把这套审查协议写进 hermes 的 identity.md 或新建一个 `reviewer` agent 角色。在 workflow 的 verify 阶段，让 reviewer 先预判问题再审查，输出结构化的 review report（Decided / Rejected / Risks / Open Questions / Pre-mortem scenarios）。对于教育内容，预判维度可以是：知识准确性 / 题目完整性 / 答案正确性 / 格式规范 / 难度匹配。

### 9. 并行 Worker 的 Worktree 隔离（低-中优先级）

**OMC 的做法**：team worker 在独立的 git worktree 里工作（`<repo>/.omc/team/<team-name>/worktrees/<worker-name>`），coordination state 留在主目录。dirty worktree 不会被强制清理，而是作为 warning 上报。有 `OMC_STATE_DIR` 支持集中式 state，survive worktree 删除。

**Eduflow 现状**：所有 worker 在同一个 tmux session 的不同 pane 里工作，共享同一个 repo 工作目录。多个 worker 同时改文件可能冲突。

**怎么迁移**：对于多 worker 并行改代码的场景，可以给每个 coding worker 创建 git worktree（`.eduflow-team-state/worktrees/<agent>/`），worker 在自己的 worktree 里工作，完成后 merge 回主分支。但这对 Eduflow 的教育内容生产场景（worker 主要是生成内容而非改代码）可能不是刚需，优先级取决于是否有"多 worker 并行改同一个 repo"的真实场景。

### 10. 自然语言触发词（低优先级）

**OMC 的做法**：magic keywords——输入 `autopilot`/`build me`/`I want a` 自动触发 autopilot 模式，`ralph`/`don't stop`/`must complete` 触发 ralph，`ulw`/`ultrawork` 触发并行模式。不需要记 slash command。

**Eduflow 现状**：飞书群里用 slash command（`/health` `/team` `/send`）和 `@manager` 自然语言。已经有自然语言路由能力（router 的 classify_event），但触发词是固定的 slash command。

**怎么迁移**：在 router 的 classify 逻辑里增加 magic keyword 检测——boss 说"帮我全自动跑完"自动关联到 autopilot-like workflow，说"必须做完不要停"关联到 ralph-like 持久循环。这个改动很小，在 router.py 里加几个关键词映射即可。

---

## 四、不建议借鉴的部分

**Claude Code 插件分发模型**。OMC 的 `.claude-plugin/plugin.json` + npm 包 + marketplace 是 Claude Code 生态特有的，Eduflow 是 Python + tmux + 飞书，不适用。

**hooks 注册到 Claude Code 生命周期**。OMC 的 11 个 lifecycle hooks（PreToolUse / PostToolUse / PreCompact 等）是 Claude Code 的机制。Eduflow 的等价物是 router pipeline + watchdog + lifecycle.py，已经有自己的事件处理架构。

**delegation enforcer（自动注入 model 参数到 Task 调用）**。这是 OMC 解决"Claude Code 不会自动从 agent 配置读 model 参数"的 workaround。Eduflow 的 agent model 是在 eduflow.toml 里配置的，不存在这个问题。

**branded path types（ReadPath / WritePath）**。这是 TypeScript 编译时类型安全的技巧。Eduflow 是 Python，可以用更 Pythonic 的方式（如 pathlib 的 Path 子类或 pydantic 模型）达到类似效果，不需要照搬。

---

## 五、总结：优先级矩阵

| 借鉴方向 | 影响力 | 迁移难度 | 建议优先级 |
|---|---|---|---|
| 分阶段编排管线 (plan→exec→verify→fix) | 高 | 中 | 第一批 |
| 分层模型路由用于成本优化 | 高 | 低 | 第一批 |
| 基于证据的验证循环 | 高 | 中 | 第一批 |
| 深度访谈/歧义度量 | 中 | 低 | 第二批 |
| 实时可观测性 (HUD + Agent 观测台) | 中 | 中 | 第二批 |
| 从执行经验自动提取 workflow 候选 | 中 | 中 | 第二批 |
| 阶段交接文档 | 中 | 低 | 第二批 |
| 对抗式审查 + 预判 | 中 | 低 | 第二批 |
| 并行 Worker 的 worktree 隔离 | 低-中 | 中 | 按需 |
| 自然语言触发词 | 低 | 低 | 随手做 |

第一批的三项（分阶段管线、成本路由、验证循环）是组合起来能显著提升 Eduflow 执行质量和成本效率的核心提升。它们恰好填补了 Eduflow 当前"manager 派发→worker 执行→say 回报"这条链路中缺失的"验证闭环"和"成本意识"两个环节。第二批更多是体验和成熟度的提升。
