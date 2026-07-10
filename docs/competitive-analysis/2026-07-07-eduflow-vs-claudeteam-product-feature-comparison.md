# EduFlow vs ClaudeTeam 产品功能对比表

日期：2026-07-07

对比快照：

- EduFlow：本地 checkout `ac618b88` 加当前工作树。
- ClaudeTeam 上游：`/tmp/ClaudeTeam-upstream` 的 `main`，commit `7bd130b`，已从 `zylMozart/ClaudeTeam` 刷新。

状态说明：

- 已有：当前检查到的产品面已经具备。
- 草稿：当前 EduFlow 工作树里已经出现，但还不能当作稳定产能，需要讨论和测试后再定。
- 部分：有能力，但分散、较弱，或缺少清晰的用户入口。
- 缺口：当前检查面没有。
- 拒绝：本轮不值得引入。

## 总体判断

| 维度 | EduFlow | ClaudeTeam | 产品判断 |
| --- | --- | --- | --- |
| 产品定位 | 教育生产操作系统：派工、workflow、复核、证据、runtime recovery、记忆 | 通用本地 AI 团队产品：一句话拉起团队，飞书控制，动态招工，多 CLI | EduFlow 在真实教育交付上更深；ClaudeTeam 在首次上手和老板可见性上更干净。 |
| 核心承诺 | 让长期课程、题库、复核、生产任务可恢复、可审计、可复用 | 让用户在飞书里遥控一支混编 AI 团队 | EduFlow 应借“操作清晰度”，不是替换自己的领域契约。 |
| 最强能力 | task/workflow/review/evidence/runtime/memory 全链路 | 飞书 setup、slash 命令、`/team`、`/task`、生命周期控制、adapter 广度 | EduFlow 需要更统一的 command center，不需要更多平行引擎。 |
| 最大产品风险 | 操作面分散：`task`、`workflow`、`runtime`、`manager-panel`、`ops-dashboard`、Feishu slash 都能回答一部分问题 | 通用 task 模型太浅，不足以承载 EduFlow 的 REVIEW/CLOSEOUT 和证据链 | 借只读窗口和状态分类；不要借第二套 task 生命周期。 |
| 升级方向 | 把 EduFlow 的深状态变成老板一眼能看懂的操作地图 | 把上游简单好用的操作路径当 pattern library | 第一优先级是：谁在做什么、哪里卡住、谁需要动作、什么能 close。 |

## 功能模块对比

| 功能区 | EduFlow 状态 | ClaudeTeam 状态 | 差异 | 借鉴决策 |
| --- | --- | --- | --- | --- |
| 目标场景 | 已有。面向教育内容生产、QA 复核、题库验证、workflow 证据、记忆、runtime 恢复。 | 已有。面向通用多智能体团队，覆盖软件、科研、营销、数据、内容运营模板。 | EduFlow 纵深更强；ClaudeTeam 通用包装更完整。 | 保留 EduFlow 领域模型，只借更好操作面。 |
| 团队结构 | 已有。manager、Sophon、recorder、worker_course、worker_review、builder、qbank、syllabus、Hermes，加 resident/warm 策略。 | 已有。manager + workers，可动态 hire/fire，有通用模板。 | EduFlow 角色边界更清楚，但新用户更难一眼理解。 | 做角色地图：owner、职责、当前任务、下一动作。 |
| manager 入口 | 已有。用户应先找 manager；manager 负责派工、升级、收口。 | 已有。群消息统一进 manager。 | 原则一致；EduFlow 对 closeout 更严格。 | 保持 manager-only closeout，把规则做成可见产品规则。 |
| worker 边界 | 已有。worker 做切片；reviewer 给证据 verdict；Sophon 看运行异常。 | 部分。通用 worker/manager loop，领域边界较弱。 | EduFlow 更强，但边界多藏在文档和身份 prompt 里。 | 在 `/employees` 或 `/team` 里产品化边界。 |
| REVIEW vs CLOSEOUT | 已有。`worker_review` 出 REVIEW verdict；`manager` 才能 CLOSEOUT。 | 缺口。上游是通用 approve/reject。 | 这是 EduFlow 核心优势，也是借上游 task 时最容易踩坏的边界。 | 绝不整套搬上游 approval 语义；此边界设为发布门禁。 |
| task 台账深度 | 已有。stage、owner、workflow_id、reviewer、verdict、evidence、publish gate、loop run、readiness、archive。 | 已有但简单。create/update/list/get/done/pause/approve/reject/void 加 intent anchor。 | EduFlow task 模型远深于上游；上游胜在简单可扫。 | 不替换 task store，只借轻量只读任务窗口。 |
| 飞书任务窗口 | 草稿。当前工作树已有 `/task [all]` 只读状态分组。 | 已有。`/task [all]` 看板，终态默认折叠。 | 上游先做出了好用的手机任务窗口；EduFlow 需要映射更复杂状态。 | P1。只读、终态折叠、needs-action 明确、不能改状态。 |
| manager panel | 已有。`task manager-panel`、`manager-overview`、manager actions、closeout 面。 | 缺口。上游主要靠简单 task/slash card。 | EduFlow 决策面更强，但有点分散。 | manager panel 继续做权威决策面；`/task` 只做摘要。 |
| review queue | 已有。`submit-review`、`assign-reviewer`、`review-queue`、`review`、`update-verdict`。 | 部分。approve/reject 是通用审批。 | EduFlow 有正式复核工作流；上游只是任务审批。 | 保留 EduFlow；只借显示方式，不借语义。 |
| evidence account | 已有。`evidence-account`、`evidence-explain`、evidence packet、verifier、readiness check。 | 缺口。 | EduFlow 有真正审计链。 | 保护为核心能力；在 closeout 视图里露出来。 |
| workflow registry | 已有。active/candidate workflow、gate、roles、checklist、handoff、promotion、strict validate。 | 部分。README 说 manager 可编排 loop/workflow，但没有同等 registry。 | EduFlow 明显更强，也更适合机构化交付。 | 保留；补 discoverability。 |
| workflow 执行方式 | 已有。是协调契约，不是自动引擎；`task dispatch --workflow` 只是挂载 workflow_id 和 hint。 | 部分。manager 根据任务选拓扑。 | EduFlow 正确避免了过度自动化。 | 不新增自动 workflow 引擎，除非重复痛点证明需要。 |
| 教育生产资产 | 已有。IGCSE/AP workflow、qbank schema、topic outline、review playbook、模板。 | 缺口。只有通用团队模板。 | EduFlow 的领域壁垒。 | 不需要从上游借。 |
| qbank 验证 | 已有。`qbank_verify.py`、AP verifier、manifest gate、schema check、review playbook。 | 缺口。 | EduFlow 专属能力。 | 保留投入，避免被通用 task 状态稀释。 |
| 持久记忆 | 已有。remember/recall/forget、candidate、packet、Obsidian export、sensitive memory、MCP、decay/storage。 | 已有。agent memory、team memory、skills、task 生命周期自动记忆。 | 两边都有；EduFlow 更治理化，上游 task anchor 更轻。 | 只有出现 stale-anchor 痛点时再借，不扩记忆功能。 |
| skills/playbooks | 已有。教育 skill、review playbook、workflow skill、troubleshoot skill。 | 已有。共享 skills 和通用 domain templates。 | 上游包装更适合新手；EduFlow 更适合生产。 | 若查找成本持续高，再做 skill map。 |
| 飞书 setup | 部分。有 docs 和 `scripts/feishu_bot_creator` 支持 Playwright/manual，但 CLI 没有顶层 `eduflow feishu connect`。 | 已有。`feishu connect --quick`、浏览器自动化、`--manual`，一条路径写 app/group/credentials/chat_id。 | ClaudeTeam 首次 setup 产品化明显更好。 | P2。先借 setup UX 和 checklist；不急着加命令。 |
| 飞书 slash 命令 | 已有/草稿。`/help`、`/team`、`/home`、`/sophon`、`/employees`、`/employee`、`/health`、`/usage`、`/tmux`、`/send`、`/dispatch`、`/submit`、`/assign-reviewer`、`/review-queue`、`/manager-overview`、`/task`、`/compact`、`/stop`、`/clear`。 | 已有。`/help`、`/team`、`/health`、`/usage`、`/tmux`、`/send`、`/compact`、`/stop`、`/clear`、`/task`、`/shutdown`、`/restart`、`/login`。 | EduFlow 领域命令更多；上游 lifecycle 控制更强。 | 先按用户问题重排 help；`/shutdown`、`/restart` 暂缓。 |
| 老板 command center | 部分。很多视图能回答问题，但用户要知道该看哪里。 | 部分偏强。命令少，README 的控制承诺清楚。 | EduFlow 最大遗漏可能是信息架构，不是功能缺失。 | P0/P1。先做一页 operator map。 |
| `/team` 实时状态 | 部分。EduFlow slash `/team` 仍用 TUI 文本解析；runtime 其他地方已有更强检查。 | 已有。上游 `pane_probe` 用前台进程 + pane 输出运动，且批量 probe。 | 上游分类原则更稳。 | P1 prototype。复用 EduFlow 本地 runtime probe，别复制第二套分类器。 |
| `/employees` / `/employee` | 已有。EduFlow 有 employee read model 和卡片。 | 缺口。 | EduFlow 这里可能比上游更接近“谁在干什么”。 | 保留并升级成主操作视图。 |
| ops dashboard | 已有。`task ops-dashboard`，slash `/home` 做老板首页，`/sophon` 做 Sophon 值守视图。 | 缺口/部分。上游靠 `/health`、`/team`、`/usage`。 | EduFlow 更强，但与 manager panel、task window 有重叠。 | 保留一个老板首页，减少重复解释。 |
| health | 已有。`health`、`runtime verify`、runtime events、live smoke、stale-status guardrail。 | 已有。强调 green health 只是 infra，pane 验证才是真 ready。 | EduFlow 技术更深；上游更会教育用户。 | 借文案和 checklist，让 health 说清“哪里未 ready”。 |
| runtime verify | 已有。`runtime verify/list/switch/events`，env drift、smoke、provider 证明。 | 部分。有 auth、metrics、watchdog、pane probe，但没有同等 runtime switch 面。 | EduFlow 生产恢复更强。 | 保留，不要埋进通用 health。 |
| runtime failover | 已有。runtime registry、fallback、switch event、guard/escalation。 | 部分。adapter auth 和 CLI readiness 为主。 | EduFlow 优势。 | 放进 operator map，让老板知道什么时候要介入。 |
| warm residency | 已有。resident/warm、`residency-sleep`、`residency-wake`、pending-task protection。 | 缺口/部分。有 always-on 和 lazy agent，但没有同等 warm 策略。 | EduFlow 更懂成本和会话释放。 | 保留；在老板视图里区分 warm idle 和 broken。 |
| watchdog/router recovery | 已有。watchdog、router silent restart、catchup、runtime guard。 | 已有。watchdog、subscribe quiet detection、restart 后 catchup。 | 两边都重要；上游 catchup 有值得借的细节。 | P1，但必须先做 replay/dedup 验证。 |
| catchup cursor | 草稿/部分。当前工作树有 catchup 草稿；EduFlow 还有 `recent_window_lines`，合并风险高。 | 已有。ms 时间戳、bounded lookback、backlog cap、same-minute ordering、warning。 | 上游可能更抗 Feishu 漏消息；EduFlow dedup 路径更复杂。 | 先 prototype 和测试。最大不确定性是 router merge/dedup 加 recent-window 的真实行为。 |
| chat shutdown/restart | 缺口。 | 已有。受 controls 守卫；`/shutdown` 保留 router/subscription/watchdog，`/restart` detached 执行。 | 远程运维有价值，但副作用高。 | 暂缓。以后必须 default-deny、确认、审计、shell fallback。 |
| chat login | 缺口。 | 已有。受 controls 守卫。 | 远程认证方便但 credential 隔离风险大。 | 暂缓或拒绝，除非认证痛点压倒其他问题。 |
| CLI adapter 广度 | 已有。Claude Code、Codex、Gemini、Kimi、Qwen、Qoder CN、Mimo、Hermes。 | 已有更广。MiniMax、opencode、CodeWhale、OpenClaw、Trae、Pi、OpenAI-compatible BYOK。 | ClaudeTeam 更广；EduFlow 当前够用。 | 本轮拒绝。瓶颈不是 adapter 数量。 |
| adapter auth | 已有。runtime profiles、env profiles、smoke、provider failover。 | 已有。`agent_auth`、token/login/env 优先级、BYOK adapter。 | EduFlow runtime 切换更强；上游通用说明更清楚。 | 可借文案，不做新 adapter。 |
| deployment UX | 部分。EduFlow docs 完整但更项目化、步骤较多。 | 已有。coding-agent deployment protocol、quick/no-@/manual、pane verification。 | ClaudeTeam 新手体验更好。 | P2。补 EduFlow readiness checklist，区分 infra green 和 team ready。 |
| multi-team isolation | 已有。独立 Feishu app/chat/state 指引。 | 已有。类似且文案清楚。 | 基本相当。 | 借更清晰的说明即可。 |
| 本地状态审计 | 已有。facts、inbox、status、logs、tasks、runtime events、memory、workflow registry。 | 已有。inbox/status/logs/tasks/memory。 | EduFlow 状态更多，更强也更难懂。 | 做 source-of-truth map，这是高价值低风险升级。 |
| 命令分组 | 已有。CLI 按 bootstrap/store/lifecycle/transport/supervision/task/asset/memory/operational 分组。 | 已有。类似但更小。 | EduFlow 命令已经大到仅分组不够。 | 增加“我想知道 X，该跑 Y”的任务型 help。 |
| 产品包装 | 部分。README 定位强、图也有；但 docs/plans/workflows/skills 分散。 | 已有。README 和 deployment 更像面向外部用户的产品。 | ClaudeTeam 顶层故事更顺；EduFlow 内部操作深度更强。 | 等方案确认后再更新 README/operator doc。 |
| 测试和场景 | 已有。EduFlow unit/integration/scenario 覆盖 task、runtime、memory、workflow、commands。 | 已有。上游覆盖 core runtime、adapter、slash、task。 | EduFlow 测试更广也更重。 | 借功能时只加最小 operator 行为测试；catchup 例外，需要 replay harness。 |
| 风险姿态 | 已有但分散。代码和文档里有很多 guardrail。 | 已有。default-deny controls 和低依赖故事更清晰。 | EduFlow 需要把风险边界产品化。 | 增加 read-only vs mutating release checklist。 |

## 用户路径对比

| 用户路径 | EduFlow 今天 | ClaudeTeam 今天 | EduFlow 应借什么 |
| --- | --- | --- | --- |
| 首次部署 | 安装、配置 `eduflow.toml`、按 docs/scripts 配飞书、启动、验证。能力强但步骤多。 | `init`、`feishu connect --quick` 或浏览器/manual、`install-hooks`、`up`、pane 验证。路径更顺。 | first-run checklist：先问 CLI、飞书模式、roster、验证门槛。 |
| 我团队活着吗？ | `health`、`runtime verify`、`team`、`/health`、`/team`、`/home`、`/employees`、`/sophon`。强但散。 | `/team`、`/health`、pane verification。简单。 | 一个老板首页：alive、working、blocked、waiting review、needs manager action。 |
| 谁负责当前任务？ | task ledger、manager panel、inbox、status、workflow_id、review queue。 | task list 和 manager routing。 | 用 EduFlow 数据，但一张卡显示 owner + next action。 |
| 什么需要我决策？ | manager actions、review queue、manager panel、operational readiness。 | pause/approve/reject 和 task kanban。 | 在轻量 task window 中做 needs boss/manager action lane。 |
| 我能信这个产出吗？ | evidence account、review verdict、verifier、workflow gate、manager closeout。 | 通用 approve/reject。 | 保留 EduFlow trust chain，在 closeout 视图显示证据 readiness。 |
| 我如何远程恢复？ | shell 命令和 runtime guard。chat slash 没有 shutdown/restart。 | `/shutdown`、`/restart` 带 controls。 | 等只读视图稳定后，再考虑 default-deny 的远程 lifecycle。 |
| 我如何增加模型/CLI 容量？ | runtime registry、env profiles、已有 adapters/failover。 | adapter 更多，BYOK 更通用。 | 当前不需要扩 adapter；更该说明现有 runtime chain。 |

## 借鉴优先级矩阵

| 优先级 | 功能 | 原因 | 范围 |
| --- | --- | --- | --- |
| P0 | Operator information architecture map | 最大缺口是用户不知道该看哪里，不是系统没有数据。 | 文档/只读。把用户问题映射到 source of truth、命令、owner。 |
| P1 | 轻量 task window | 老板手机上能快速扫任务，不改 task 状态。 | `/task [all]` 只读、终态折叠、needs-action lane。 |
| P1 | marker-free `/team` classifier | 减少 TUI 文本漂移导致的错误状态判断。 | 复用本地 runtime probe，避免第二套分类器。 |
| P1 | catchup replay harness | 飞书漏消息恢复很关键，也最容易引入重复派单。 | 先测试和回放，再改生产路径；必须证明 `recent_window_lines` dedup。 |
| P2 | deployment readiness checklist | 上游更会讲清 health green 不等于 team ready。 | 文档和命令文案。 |
| P2 | chat lifecycle controls | 远程运维有价值，但副作用高。 | default-deny、确认、审计；`/login` 先不做。 |
| 拒绝 | 新 CLI adapter | 不是 EduFlow 当前瓶颈，会增加认证和 TUI 漂移维护成本。 | 本轮不做。 |

## EduFlow 需要的一页 Source of Truth Map

| 操作者问题 | 当前事实源 | 当前入口 | 产品问题 | 建议形态 |
| --- | --- | --- | --- | --- |
| 团队里有哪些人？ | `eduflow.toml`、local facts、tmux panes | `team`、`/team`、`/employees` | 多个视图都能回答一部分，不清楚谁权威。 | `/employees` 做人类视图；`team` 做技术 pane 视图。 |
| 每个人在干什么？ | task ledger、status、inbox、facts | `task list`、`manager-panel`、`/task`、`/employee` | 太多入口都能部分回答。 | boss card 显示 active task、状态、blocker、next action。 |
| 什么需要复核？ | task reviewer/verdict 字段 | `review-queue`、`manager-panel`、slash review queue | 数据强，但 review 和 closeout 容易视觉混在一起。 | REVIEW lane 和 CLOSEOUT lane 分开。 |
| 什么可以收口？ | verdict、evidence packet、readiness、manager action | `manager-closeout`、`batch-closeout`、evidence commands | closeout readiness 很强但不直观。 | ready for manager closeout lane，带证据摘要。 |
| runtime 安全吗？ | runtime verify/events、health、watchdog | `health`、`runtime verify`、`runtime events`、`/sophon` | 运行健康和业务进度混在多个入口。 | Sophon panel 分 infra、provider、pane、inbox、task staleness。 |
| 飞书是否漏消息？ | catchup cursor、router logs、inbox rows、recent window | router/catchup logs | 人工很难判断；重复 replay 成本高。 | replay harness 加可见 catchup warning。 |

## 最终产品判断

EduFlow 不应该变成更宽泛的 ClaudeTeam clone。它在教育生产真正重要的维度上已经超过上游：workflow contract、review gate、evidence、runtime failover、memory。

高质量借鉴路径要更窄：

1. 先让 EduFlow 从老板/操作者视角更容易看懂。
2. 借来的界面默认只读，直到状态真相被证明。
3. 坚守 `worker_review` 的 REVIEW 和 `manager` 的 CLOSEOUT 边界。
4. 把 Feishu catchup 当可靠性子系统，不当 UI 小功能。
5. 本轮拒绝新 CLI adapter，瓶颈是操作清晰度，不是模型种类。

如果这份对比表进入升级 backlog，第一步应是 operator information architecture map 加轻量 task window 评审，而不是 chat restart 或 adapter 扩容。
