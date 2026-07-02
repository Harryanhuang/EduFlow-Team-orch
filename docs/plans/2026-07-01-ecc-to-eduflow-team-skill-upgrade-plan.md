# ECC 可借鉴能力到 EduFlow Team 的提升方案

> 日期: 2026-07-01
> 目标项目: `EduFlow-Team-orch`
> 参考项目: `affaan-m/ECC`
> 本版基线: 已扫描当前 `rebuild/minimal` 分支的 `src/eduflow/`, `eduflow.toml`, `docs/workflows/`, `skills/eduflow-team-monitor`, `.eduflow-team-state/agents/*/identity.md`, 以及 ECC 的相关 skills / agents / commands。

## 一、修正后的判断

ECC 对 EduFlow Team 的价值不是"拿来安装一套 skills"。

EduFlow 当前已经不是一个缺少治理层的多 agent demo。它已经有:

- `runtime_registry` + 多 provider fallback chain
- `runtime verify / runtime guard / runtime events / runtime switch`
- `health` 对 live env、pane、router、watchdog、context pressure 的检测
- `task` 子命令下的 manager panel、supervisor check、evidence account、publish scan、review queue、subject inventory
- `subject_verifier` / `ap_subject_verifier` / `task_evidence_account`
- `task_event_scanner` 中的大量 anomaly、closeout gate、manager boundary、context guard、review truth lag、qbank readiness 检查
- `docs/workflows/` 的 workflow registry、candidate、promotion、gap-map 机制
- `skills/eduflow-team-monitor` 的 production patrol / context patrol / intervention ladder
- 角色 identity: `manager`, `auto_ops`, `worker_builder`, `worker_course`, `review_course`, `worker_qbank`, `Hermes`, `Luke_recorder`

因此 ECC 里值得借鉴的东西,应该翻译成 **EduFlow 已有能力的解释层、审计层、基准测试层和规则沉淀层**。不要重复造 runtime guard、verification gate 或 workflow engine。

## 二、当前 EduFlow 能力盘点

### 2.1 Runtime / provider 韧性已经很强

当前已有实现面:

| EduFlow 面 | 位置 | 已有能力 |
| --- | --- | --- |
| runtime 注册表 | `eduflow.toml` `[runtime_registry.*]` | 每个 lane 有 primary / backup / fallback_to / switch_on |
| provider env profile | `eduflow.toml` `[env_profiles.*]` | 多 provider secret 引用、pool_id、provider_family |
| runtime 状态 | `.eduflow-team-state/facts/runtime-status.json` | 记录当前 runtime / env_profile / verified_at 等 |
| runtime 事件 | `.eduflow-team-state/facts/runtime-switch-events.jsonl` | 切换审计 |
| runtime verify | `src/eduflow/commands/runtime_verify.py` | env drift、API smoke、pane marker、inbox consumption verdict |
| runtime guard | `src/eduflow/commands/runtime_guard.py` | cooldown、recent switch、fallback health score |
| fallback loop | `src/eduflow/runtime/failover.py` | cross-pool fallback 选择与执行 |
| lifecycle | `src/eduflow/runtime/lifecycle.py` | restart_with_runtime、proved-ready gate、runtime status 写入 |

结论: ECC 的 `agent-introspection-debugging` 不能作为新 runtime 系统来装,更适合做成 **runtime 诊断报告模板**,把上述现有命令的输出解释给 manager / auto_ops / worker_builder。

### 2.2 Production / review gate 已经不是空白

当前已有实现面:

| EduFlow 面 | 位置 | 已有能力 |
| --- | --- | --- |
| subject verifier | `src/eduflow/store/subject_verifier.py` | subject/package scope、manifest、QA/QQL/items consistency、orphan/legacy fragments |
| AP verifier | `src/eduflow/store/ap_subject_verifier.py` | AP item/frontmatter/manifest/self-check |
| evidence account | `src/eduflow/store/task_evidence_account.py` | closeout readiness、missing/conflicting evidence、latest verdict、qbank readiness |
| closeout gate | `src/eduflow/store/subject_verifier.py:subject_closeout_gate` | verifier scope/status、task verdict/status hard blocks |
| task scanner | `src/eduflow/store/task_event_scanner.py` | review truth lag、manager anomalies、evidence packet incomplete、subject qbank readiness 等 |
| task CLI | `src/eduflow/commands/task.py` | manager-closeout、subject-inventory、evidence-account、manager-actions、supervisor-check |

结论: ECC 的 `verification-loop` 不应照搬成"build/type/lint/test/security"通用流程。EduFlow 更需要的是 **evidence account explainer**: 把已有 gate 的结果用不同角色能执行的语言解释清楚。

### 2.3 Context patrol 已经落地一半

当前已有实现面:

| EduFlow 面 | 位置 | 已有能力 |
| --- | --- | --- |
| context parser | `src/eduflow/runtime/context_monitor.py` | 识别 `warning / compact_recommended / exhausted` |
| auto_ops context | `eduflow task auto-ops-context --send-manager` | 全员 context snapshot, 输出 allow_continue_original_task |
| compact 命令 | `src/eduflow/commands/compact.py` | 向目标 pane 注入真实 `/compact` |
| monitor skill | `skills/eduflow-team-monitor/references/context-patrol.md` | context decision matrix |
| manager identity | `.eduflow-team-state/agents/manager/identity.md` | 90%+ 必须真实 compact, 禁止文字提醒替代 |

结论: ECC 的 `context-budget` / `strategic-compact` 不适合直接装 hook。EduFlow 更需要的是 **context overhead audit**,扫描 identity / skill / workflow / MCP / prompt 体积,避免 prompt 规则越来越胖。

### 2.4 Workflow registry 已有候选/晋升机制

当前已有实现面:

| EduFlow 面 | 位置 | 已有能力 |
| --- | --- | --- |
| active workflows | `docs/workflows/*/README.md` | `igcse-subject-launch`, `runtime-failover-hardening`, `realrun-to-workflow` 等 |
| candidate pool | `docs/workflows/_candidates/` | draft/backlog/promotion_ready/case_note_only |
| workflow CLI | `src/eduflow/commands/workflow.py` | recommend、validate、gap-map、promote-plan、promote |
| monitor gap notes | `skills/eduflow-team-monitor` | real run → gap note → workflow 修复建议 |

结论: ECC 的 `rules-distill` 很适合,但落点不是新 rules 目录,而是 **workflow gap-map + identity/skill/workflow 的差异化晋升机制**。

## 三、ECC 中真正值得借鉴的 6 个方向

### 方向 A: Workspace Surface Audit → EduFlow Harness Surface Audit

ECC 来源:

- `skills/workspace-surface-audit`
- `skills/context-budget`
- `agents/harness-optimizer`

适配后的 EduFlow 目标:

> 定期回答: 当前 EduFlow 这台机器/这个 repo 实际启用了哪些 harness surface? 哪些能力已经有 primitive,但缺 operator workflow? 哪些规则重复或过载?

为什么适合:

EduFlow 当前已经有很多层: `CLAUDE.md`, `AGENTS.md`, `.claude/skills`, repo `skills`, `docs/workflows`, `.eduflow-team-state/agents/*/identity.md`, Flow Memory, runtime registry, Feishu slash, task scanner。真正风险是 **能力重复、规则冲突、上下文膨胀、旧身份文件与当前代码 drift**。

建议新增 skill:

```text
skills/eduflow-harness-surface-audit/SKILL.md
```

主装角色:

| 角色 | 理由 |
| --- | --- |
| `worker_builder` | 负责系统建设/维修,最适合做配置面审计 |
| `Hermes` | 知识库与长期记忆 steward,适合审文档/知识漂移 |
| `Luke_recorder` | 记录老板纠偏和重复要求,可提供审计输入 |

不要装给:

- `worker_course`
- `review_course`
- `worker_qbank`

建议扫描面:

```text
CLAUDE.md
README.md
eduflow.toml
src/eduflow/cli.py
src/eduflow/commands/
src/eduflow/runtime/
src/eduflow/store/task_event_scanner.py
skills/
.claude/skills/
docs/workflows/
.eduflow-team-state/agents/*/identity.md
.eduflow-team-state/facts/runtime-status.json
.eduflow-team-state/facts/runtime-switch-events.jsonl
```

输出:

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

### Primitive-only gaps
- ...

### Top next moves
1. ...
```

优先级: **P0**。这是之前方案漏掉的关键。

### 方向 B: Agent Introspection Debugging → Runtime/Task Drift Explainer

ECC 来源:

- `skills/agent-introspection-debugging`
- `agents/silent-failure-hunter`
- `agents/loop-operator`

适配后的 EduFlow 目标:

> 不是新增 runtime recovery,而是把 `health + runtime verify + runtime guard + task scanner + production/context patrol` 组合成一个"故障解释器"。

当前已有 primitive:

```text
./scripts/eduflowteam health
./scripts/eduflowteam runtime verify <agent>
./scripts/eduflowteam runtime events --last N
./scripts/eduflowteam runtime-guard
./scripts/eduflowteam task auto-ops-context --send-manager
./scripts/eduflowteam task auto-ops-production --send-manager
./scripts/eduflowteam task supervisor-check --json
./scripts/eduflowteam inbox <agent>
./scripts/eduflowteam team --json
```

建议新增 skill:

```text
skills/eduflow-runtime-task-drift-explainer/SKILL.md
```

主装角色:

| 角色 | 版本 | 职责 |
| --- | --- | --- |
| `auto_ops` | monitor | 先跑只读诊断,把结果回流 manager |
| `worker_builder` | repair | 需要改 runtime/config/CLI 时接手 |
| `manager` | lite | 只读报告,决定派谁,不亲自修 |

替代上一版里的错误命名:

```text
旧: worker_repair
新: worker_builder
```

诊断分类:

| 类别 | 证据面 |
| --- | --- |
| `runtime_dead` | health/tmux/router/watchdog |
| `env_drift` | runtime verify env mismatches |
| `fallback_cooldown` | runtime-guard health/cooldown |
| `inbox_not_consumed` | runtime verify + inbox |
| `context_blocked` | auto-ops-context allow_continue_original_task=false |
| `task_truth_drift` | supervisor-check / task scanner |
| `production_stale` | auto-ops-production stale/blocked |
| `status_lag` | newer logs/heartbeat contradict status |

输出:

```markdown
## Runtime/Task Drift Explainer

- Affected agent:
- Diagnosis:
- Existing primitive used:
- Evidence:
- Safe next action:
- Owner:
- Do not do:
```

优先级: **P0**。但它是解释器,不是新守护进程。

### 方向 C: Verification Loop → Evidence Account Explainer

ECC 来源:

- `skills/verification-loop`
- `agents/pr-test-analyzer`
- `agents/code-reviewer`

适配后的 EduFlow 目标:

> 把 `task evidence-account`, `subject_verifier`, `manager-actions`, `manager-panel` 的结果翻译成 worker/review/manager/Anna 都能执行的 verdict packet。

当前已有 primitive:

```text
./scripts/eduflowteam task evidence-account <task_id>
./scripts/eduflowteam task subject-inventory
./scripts/eduflowteam task manager-actions
./scripts/eduflowteam task manager-panel
./scripts/eduflowteam task supervisor-check --json
./scripts/eduflowteam task review-queue --reviewer review_course
```

建议新增 skill:

```text
skills/eduflow-evidence-account-explainer/SKILL.md
```

主装角色:

| 角色 | 版本 | 职责 |
| --- | --- | --- |
| `review_course` | full | 把 evidence account 转成 PASS/NEEDS_FIX/BLOCKED |
| `worker_course` | selfcheck | 交付前自查 missing/conflicting evidence |
| `worker_qbank` | qbank | 只看 qbank_readiness / mapping / item readiness |
| `manager` | closeout-lite | 只读 verdict packet,不深审 |
| `anna` 如启用 | final-readonly | 老板汇总前核对 closeout 是否真成立 |

注意:

EduFlow 当前配置没有 `anna` 作为 active agent,只有 `.eduflow-team-state/agents/anna` 的历史 home/identity。若要用 Anna 角色,必须先在 `eduflow.toml` 加回 team agent;否则方案里只应写成 optional。

输出:

```markdown
## Evidence Account Verdict Packet

- Task:
- Verdict: PASS | NEEDS_FIX | BLOCKED | OBSERVE
- Missing evidence:
- Conflicting evidence:
- Latest authoritative review:
- Subject verifier status:
- Qbank readiness:
- Manager action allowed:
- Required next owner:
```

优先级: **P1**。不是新增 gate,而是让已有 gate 更容易被角色消费。

### 方向 D: Rules Distill → EduFlow Workflow/Identity Distill

ECC 来源:

- `skills/rules-distill`
- `skills/agent-introspection-debugging` 的 preventive change
- `commands/learn`

适配后的 EduFlow 目标:

> 把真实运行 gap note、boss 纠偏、manager 失误、auto_ops 巡检结果,定期蒸馏到正确位置: workflow gate、identity 红线、skill、CLI check、test scenario,而不是只堆在聊天记录里。

当前已有 primitive:

```text
skills/eduflow-team-monitor
docs/workflows/realrun-to-workflow/
docs/workflows/_candidates/
eduflowteam workflow gap-map
eduflowteam workflow maintainer <workflow_id>
eduflowteam workflow validate --strict
Luke_recorder identity: 记录老板/manager 对话与可复用教训
Hermes identity: Obsidian / memory candidate / conflict report
```

建议新增 skill:

```text
skills/eduflow-workflow-identity-distill/SKILL.md
```

主装角色:

| 角色 | 职责 |
| --- | --- |
| `Luke_recorder` | 从老板纠偏和 manager 暴露问题里提取 Trigger/Move/Failure mode |
| `Hermes` | 写入 Obsidian 白名单目录和 memory candidate backlog |
| `worker_builder` | 把规则落实成 workflow gate、identity patch、CLI check 或 test |
| `manager` | 决定是否晋升为团队 contract |
| `auto_ops` | 提供真实运行 gap note 输入 |

规则晋升路径:

| 重复模式 | 应该落到 |
| --- | --- |
| 单角色行为边界 | `.eduflow-team-state/agents/<role>/identity.md` 或 `eduflow.toml notes` |
| 多角色链路 | `docs/workflows/<workflow_id>/checklist.md` / `roles.md` / `forbidden moves` |
| 可机器判断 | `task_event_scanner.py` / `subject_verifier.py` / CLI check |
| 操作员巡检 | `skills/eduflow-team-monitor/references/*.md` |
| 长期知识 | Hermes Obsidian proposal / memory candidate |
| 一次性事故 | gap note / case_note_only candidate |

优先级: **P0/P1**。这比直接装 ECC rules 更贴合 EduFlow。

### 方向 E: Agent Eval → Runtime/Model Lane Benchmark

ECC 来源:

- `skills/agent-eval`
- `benchmark-methodology`

适配后的 EduFlow 目标:

> 用真实 EduFlow 任务评估不同 runtime/provider/agent lane,不要只凭体感决定 `course_primary`, `review_primary`, `builder_primary`, `qbank_primary` 用哪个模型池。

当前 EduFlow 的天然评估对象:

```text
course_primary / course_backup_minimax / course_backup_mimo / course_backup_kimi
manager_primary / manager_backup_*
review_primary / review_backup_*
builder_primary / builder_backup_*
qbank_primary / qbank_backup_*
Hermes primary/backup
```

建议新增:

```text
docs/evals/eduflow-agent-eval/
skills/eduflow-runtime-lane-eval/SKILL.md
```

先不要引入外部依赖。第一版可用 git worktree + `scripts/eduflowteam` + deterministic judge:

| Lane | 代表任务 | Judge |
| --- | --- | --- |
| `worker_course` | 生成一个 topic outline / QA seed | manifest + format + review sample |
| `review_course` | 对旧 T-91/T-99 review report 做 verdict | 是否抓到已知 blocker |
| `worker_builder` | 修一个小 CLI/test fixture | `python3 tests/run.py` 或目标 unit test |
| `worker_qbank` | qbank readiness 判定 | qbank verifier / manifest consistency |
| `manager` | 从 inbox/task 状态选择下一步 | manager_action packet 是否正确 |

输出指标:

```text
pass_rate
time_to_first_ack
time_to_verdict
context_pressure_delta
runtime_switch_count
manager_intervention_count
cost/proxy pool if available
```

优先级: **P2**。等 P0/P1 稳定后做,但长远价值很高。

### 方向 F: Agent Architecture Audit → Prompt/Memory/Transport Layer Audit

ECC 来源:

- `skills/agent-architecture-audit`
- `agents/harness-optimizer`

适配后的 EduFlow 目标:

> 审计 EduFlow 的 12 层 agent stack: system prompt、identity、memory injection、workflow hints、task scanner、Feishu card transport、hidden fallback、runtime status persistence。

为什么需要:

当前 EduFlow 有多层可能互相影响:

```text
AGENTS.md / CLAUDE.md
eduflow.toml notes
identity.render()
memory injection
workflow hints
task_event_scanner anomalies
Feishu router/deliver/say
tmux pane state
runtime-status / local facts
```

如果 agent 表现"越来越怪",不要只调 prompt,要查是哪一层污染或覆盖。

建议落地:

```text
skills/eduflow-agent-architecture-audit/SKILL.md
```

主装:

- `worker_builder`
- `Hermes`

优先级: **P1/P2**。

## 四、重新排序后的推荐落地

### P0: 先做两个"解释/审计 skill"

1. `eduflow-harness-surface-audit`
2. `eduflow-runtime-task-drift-explainer`

理由:

- 它们不会和现有代码冲突。
- 它们能马上降低 operator 误判。
- 它们能修正"已有 primitive 很多,但不知道该看哪一个"的问题。

### P1: 再做两个"沉淀/消费 skill"

3. `eduflow-evidence-account-explainer`
4. `eduflow-workflow-identity-distill`

理由:

- Evidence account 已经存在,缺的是角色可读 verdict packet。
- Workflow registry 已经存在,缺的是从 gap note / boss 纠偏到 identity/workflow/CLI/test 的固定蒸馏路线。

### P2: 最后做 benchmark/audit 深水区

5. `eduflow-runtime-lane-eval`
6. `eduflow-agent-architecture-audit`

理由:

- lane eval 需要稳定 judge 和可重复任务,不能急。
- architecture audit 会触及 prompt/memory/transport 层,适合在 P0/P1 有稳定证据后做。

## 五、角色安装矩阵

| 角色 | 建议安装 | 不建议安装 |
| --- | --- | --- |
| `manager` | `runtime-task-drift-explainer` lite, `workflow-identity-distill` governance, `evidence-account-explainer` closeout-lite | full audit / full repair / full verifier |
| `auto_ops` | `runtime-task-drift-explainer` monitor, `workflow-identity-distill` gap-input | full production repair |
| `worker_builder` | `harness-surface-audit`, `runtime-task-drift-explainer` repair, `workflow-identity-distill` implementer, `agent-architecture-audit` | course/qbank content verifier |
| `worker_course` | `evidence-account-explainer` selfcheck | runtime repair / rules governance |
| `review_course` | `evidence-account-explainer` full | runtime repair / manager closeout |
| `worker_qbank` | `evidence-account-explainer` qbank slice | course full verifier / runtime repair |
| `Hermes` | `harness-surface-audit` knowledge slice, `workflow-identity-distill` knowledge proposal, `agent-architecture-audit` memory slice | runtime repair |
| `Luke_recorder` | `workflow-identity-distill` observation/input | CLI repair / production verification |
| `worker_syllabus` | only selfcheck slice if needed | all governance/runtime skills |

## 六、不要借鉴或暂缓借鉴的 ECC 部分

| ECC 部分 | 建议 | 原因 |
| --- | --- | --- |
| 全局 `.cursor/.kiro/.opencode/.claude` hooks | 不装 | 会和 EduFlow 的 CLI/runtime/identity 体系叠加冲突 |
| `delivery-gate` stop hook | 暂缓,只借鉴理念 | EduFlow 的 closeout 已经通过 task gates;机械 Stop hook 容易误伤长跑监控 |
| 通用 language rules 全集 | 不装 | 与 EduFlow 当前 Python/runtime/education workflow 主线关系弱 |
| 原版 `verification-loop` | 不照搬 | EduFlow 的 verification 不是 npm build,而是 task/evidence/subject gate |
| 原版 `team-agent-orchestration` | 只借鉴术语 | EduFlow 已经有 team/workflow/task/inbox/Feishu 控制面 |
| 营销/投资/社媒类 skills | 不装 | 非 EduFlow Team 核心 |

## 七、可执行的第一周计划

### Day 1: 产出 harness surface audit 初版

文件:

```text
skills/eduflow-harness-surface-audit/SKILL.md
docs/plans/YYYY-MM-DD-eduflow-harness-surface-audit-report.md
```

验收:

- 能列出当前 runtime/task/workflow/identity/skill/memory/control-plane surface。
- 能指出重复规则和 drift 风险。
- 能给出 Top 3 next moves。

### Day 2: 产出 runtime/task drift explainer 初版

文件:

```text
skills/eduflow-runtime-task-drift-explainer/SKILL.md
```

验收:

- 明确先跑哪些现有命令。
- 把结果分类为 `runtime_dead / env_drift / fallback_cooldown / inbox_not_consumed / context_blocked / task_truth_drift / production_stale / status_lag`。
- 输出 owner 和 safe next action。

### Day 3: Evidence account explainer

文件:

```text
skills/eduflow-evidence-account-explainer/SKILL.md
```

验收:

- 读取 `task evidence-account` / `subject-inventory` / `review-queue`。
- 生成 `PASS | NEEDS_FIX | BLOCKED | OBSERVE` packet。
- 明确 manager 只读,review_course 出 verdict,worker_course 做 selfcheck。

### Day 4: Workflow/identity distill

文件:

```text
skills/eduflow-workflow-identity-distill/SKILL.md
```

验收:

- 能把一个 gap note 映射到 identity / workflow / skill / CLI check / test scenario。
- 能区别一次性事故和可晋升 workflow。
- 能对接 `eduflowteam workflow gap-map` / `maintainer` / `validate --strict`。

### Day 5: 选一个历史事故回放验证

建议用 4 类真实事故各回放一次:

1. runtime env drift / fallback cooldown
2. worker self-PASS 但 review_course 打回
3. subject closeout evidence incomplete
4. context 90%+ 但 manager 继续派长任务

验收:

- 新 skill 能找到正确已有 primitive。
- 不要求 agent 记忆历史细节也能定位证据面。
- 不越权: manager 只派发/closeout, worker_builder 修系统, review_course 出 verdict。

## 八、成功标准

这次从 ECC 借鉴的成功标准不是"新增了几个 skill",而是:

1. 新增 skill 不重复已有 runtime guard / task scanner / subject verifier。
2. 任一 runtime/task 漂移事故能在 3-5 分钟内定位应看的现有命令。
3. manager 不再被迫读一堆 JSON/日志,而是拿到 owner + next action。
4. review_course 能把 evidence account 转成可执行 verdict。
5. worker_builder 能定期审计 identity/skill/workflow/prompt 的 drift 和重叠。
6. gap note 能进入 workflow/identity/CLI/test 的晋升通道。
7. 普通内容 worker 不获得 runtime repair / governance 权限。

## 九、一句话版本

ECC 对 EduFlow 最值得借鉴的,不是它的全套配置仓库,而是 6 个方法:

```text
surface audit
drift introspection
evidence explainer
rules/workflow distill
runtime lane eval
agent architecture audit
```

其中 P0 应先做:

```text
eduflow-harness-surface-audit
eduflow-runtime-task-drift-explainer
```

它们最贴近当前 EduFlow 的真实缺口:已有能力多,但缺少一层面向角色和 operator 的"该看什么、怎么解释、谁来接手"。

## 十、GitHub 同类项目扫描补充

> 扫描时间: 2026-07-01
> 口径: GitHub stars + repo 描述 + 与 EduFlow 的结构相似度。排除原始 ClaudeTeam 线。

### 10.1 纯 stars / 影响力榜

这张榜表示社区影响力,不等于和 EduFlow 最像。

| 排名 | 项目 | Stars | 与 EduFlow 的关系 |
| --- | --- | ---: | --- |
| 1 | [anthropics/claude-code](https://github.com/anthropics/claude-code) | 135,249 | 底层 CLI 工具,不是编排器 |
| 2 | [All-Hands-AI/OpenHands](https://github.com/OpenHands/OpenHands) | 78,936 | AI 软件开发平台,偏云/沙箱/任务执行 |
| 3 | [FoundationAgents/MetaGPT](https://github.com/FoundationAgents/MetaGPT) | 69,134 | 通用多智能体软件公司范式 |
| 4 | [ruvnet/ruflo](https://github.com/ruvnet/ruflo) | 62,304 | agent meta-harness / swarm / memory / workflow |
| 5 | [microsoft/autogen](https://github.com/microsoft/autogen) | 59,394 | 通用 agentic AI 编程框架 |
| 6 | [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | 54,678 | role-playing agent orchestration 框架 |
| 7 | [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) | 47,687 | Claude Code 生态索引,不是运行系统 |
| 8 | [wshobson/agents](https://github.com/wshobson/agents) | 37,388 | 多 harness agent/plugin marketplace |
| 9 | [Yeachan-Heo/oh-my-claudecode](https://github.com/Yeachan-Heo/oh-my-claudecode) | 37,245 | Claude Code teams-first multi-agent orchestration |
| 10 | [OpenBMB/ChatDev](https://github.com/OpenBMB/ChatDev) | 33,621 | LLM 多智能体协作开发范式 |

### 10.2 与 EduFlow 最像的相似度加权榜

这张榜更重要。相似度判断维度:

- 是否管理多个 terminal/CLI coding agents
- 是否支持 Claude Code / Codex / OpenCode / Gemini 等多 harness
- 是否有并行 session / worktree / tmux / pane 维度
- 是否有 coordinator / manager / review / CI / merge gate
- 是否有 memory / workflow / skill / hook / plugin 生态

| 推荐级别 | 项目 | Stars | 为什么值得看 |
| --- | --- | ---: | --- |
| S | [Yeachan-Heo/oh-my-claudecode](https://github.com/Yeachan-Heo/oh-my-claudecode) | 37,245 | 标注为 teams-first multi-agent orchestration for Claude Code,最像 EduFlow 的 team/role/harness 方向 |
| S | [smtg-ai/claude-squad](https://github.com/smtg-ai/claude-squad) | 7,982 | 管理多个 AI terminal agents,覆盖 Claude Code / Codex / OpenCode / Amp,与 EduFlow 的多 CLI pane 很接近 |
| S- | [AgentWrapper/agent-orchestrator](https://github.com/AgentWrapper/agent-orchestrator) | 7,839 | 并行 coding agents、计划任务、spawn agents、CI 修复、merge conflict/code review,适合借鉴任务队列和 merge gate |
| A | [stravu/crystal](https://github.com/stravu/crystal) | 3,097 | 多 Codex / Claude Code session + git worktrees + desktop comparison,适合借鉴 worktree isolation 和方案对比 |
| A | [dagger/container-use](https://github.com/dagger/container-use) | 3,897 | 为 coding agents 提供安全独立开发环境,适合补 EduFlow 的隔离执行层 |
| A | [ruvnet/ruflo](https://github.com/ruvnet/ruflo) | 62,304 | 影响力大,meta-harness/swarm/memory/workflow 思路可借鉴,但比 EduFlow 泛化很多 |
| B+ | [wshobson/agents](https://github.com/wshobson/agents) | 37,388 | 更像 agent/skill/plugin marketplace,适合借鉴技能货架与跨 harness 打包,不是 runtime 主体 |
| B | [Dicklesworthstone/claude_code_agent_farm](https://github.com/Dicklesworthstone/claude_code_agent_farm) | 851 | 20+ Claude Code agents + tmux monitoring + lock coordination,规模小但 tmux farm 思路贴近 |
| B | [baryhuang/claude-code-by-agents](https://github.com/baryhuang/claude-code-by-agents) | 885 | 桌面 app + API + @mentions 协调 local/remote agents,适合借鉴交互体验 |

### 10.3 从这些项目反推 EduFlow 的提升方向

#### 提升 1: 从 `tmux pane` 升级到 `task workspace / worktree isolation`

参考:

- `stravu/crystal`
- `dagger/container-use`
- `AgentWrapper/agent-orchestrator`

当前 EduFlow 已有:

- 每个 agent 独立 pane
- inbox/status/task/facts
- runtime fallback

缺口:

- agent 之间共享同一个工作区,并行写文件时容易冲突
- 没有把任务天然绑定到 branch/worktree/container
- review/merge gate 主要靠 task/evidence,不是 workspace isolation

建议:

```text
P1: 新增 task workspace policy
- task dispatch 可选 --workspace-mode shared|worktree|container
- worker_builder 先实现 worktree 模式
- task evidence 记录 workspace_path / branch / base_commit
- manager-panel 展示 workspace isolation 状态
```

#### 提升 2: 把 `task scanner` 输出产品化成 operator dashboard

参考:

- `claude-squad`
- `agent-orchestrator`
- `claude-code-by-agents`

当前 EduFlow 已有:

- `task manager-panel`
- `task supervisor-check --json`
- `task auto-ops-production`
- `task auto-ops-context`

缺口:

- 功能很强,但结果散在多个 CLI 输出里
- manager/auto_ops/老板需要的是一个稳定 dashboard,不是 N 个命令

建议:

```text
P0: 新增 eduflow task ops-dashboard --json/--text
聚合:
- team status
- runtime verify summary
- runtime guard
- context patrol
- production patrol
- manager actions
- review queue
- high-priority unread
输出:
- top_3_actions
- blocked_agents
- unsafe_to_continue_agents
- closeout_candidates
- stale_or_drift_cases
```

这比再增加一个 agent 更有价值。

#### 提升 3: Skill / workflow marketplace 化,但只对 EduFlow 原生资产

参考:

- `wshobson/agents`
- `ruvnet/ruflo`
- ECC

当前 EduFlow 已有:

- `.claude/skills`
- repo `skills/`
- `docs/workflows/`
- workflow candidate / promotion
- Hermes / Luke_recorder / worker_builder 的沉淀角色

缺口:

- skill、workflow、identity、memory candidate 的关系不够统一
- manager 不一定知道该调用哪个 skill/workflow
- 重复经验可能散落在 `.claude/skills`, repo `skills`, workflow docs, identity notes

建议:

```text
P0/P1: 新增 eduflow asset registry
资产类型:
- skill
- workflow
- identity rule
- patrol reference
- memory candidate
字段:
- trigger
- owner role
- status: draft|active|stale|candidate|deprecated
- source evidence
- install targets
- validation command
```

并提供:

```bash
eduflow asset list
eduflow asset recommend "<task text>"
eduflow asset validate
eduflow asset drift-check
```

#### 提升 4: agent lane benchmark,用真实任务选择 runtime

参考:

- ECC `agent-eval`
- `AgentWrapper/agent-orchestrator`
- `OpenHands` / `MetaGPT` 的 benchmark 文化

当前 EduFlow 已有:

- runtime_registry 多 provider
- runtime switch events
- task events
- tests/scenarios

缺口:

- 现在 runtime 选择多半依赖经验和故障后 fallback
- 缺少定期比较 `course/review/builder/qbank/manager` lane 哪个 provider 真有效

建议:

```text
P2: eduflow eval lane
样例任务:
- manager: 从 inbox/task 状态选 top next action
- worker_course: 生成/修复小 topic package
- review_course: 复核已知带 blocker 的样例
- worker_builder: 修一个小 CLI fixture 并跑测试
- worker_qbank: qbank readiness 判断
指标:
- pass_rate
- time_to_ack
- time_to_verdict
- runtime_switch_count
- context_pressure_delta
- manager_intervention_count
```

#### 提升 5: 把 Feishu 外显从"字符串 marker"升级到结构化 card protocol

参考:

- `claude-code-by-agents`
- `claude-squad`
- EduFlow 自己的 2026-07-01 residency audit

当前 EduFlow 已有:

- `eduflow say --card`
- card color
- publish filter
- worker reason override marker

缺口:

- 仍有不少逻辑靠自然语言 marker
- CLOSEOUT / HANDOFF / REVIEW / BLOCKER / ALERT 没有统一结构化字段

建议:

```text
P1: card protocol v2
card_type:
- ACK
- STARTED
- PROGRESS
- HANDOFF
- REVIEW_VERDICT
- BLOCKER
- ALERT
- CLOSEOUT
字段:
- task_id
- workflow_id
- evidence_refs
- next_owner
- verdict
- allowed_sender_roles
```

这会让 task scanner 少依赖中文字符串匹配。

#### 提升 6: 把 manager 从"提示词约束"进一步变成"可执行边界"

参考:

- `AgentWrapper/agent-orchestrator` 的任务/CI/merge gate
- ECC 的 harness construction / action space design

当前 EduFlow 已有:

- manager identity 红线
- manager boundary findings
- task scanner anomaly

缺口:

- manager 仍可能手动执行超过 1 分钟动作
- "manager 不亲自干活"主要靠 prompt,机器边界不够硬

建议:

```text
P1: manager command policy
对 manager pane:
- 允许 read-only status/team/inbox/task-manager-actions
- 限制长命令/文件写入/测试/grep 大范围扫描
- 发现越权命令写入 task_event_scanner manager_boundary anomaly
```

先做 audit-only,不要一上来 block。

### 10.4 推荐路线图

#### 0-2 周: 补 dashboard 和解释层

1. `eduflow task ops-dashboard`
2. `skills/eduflow-harness-surface-audit`
3. `skills/eduflow-runtime-task-drift-explainer`
4. `skills/eduflow-evidence-account-explainer`

目标: 让已有强能力更容易被 manager / auto_ops / worker_builder 消费。

#### 2-4 周: 补隔离和结构化外显

1. task workspace/worktree policy
2. card protocol v2
3. asset registry 初版
4. manager command policy audit-only

目标: 降低并行编辑冲突、减少字符串 marker、把 skill/workflow/identity 资产管起来。

#### 1-2 个月: 补 benchmark 和 agent architecture audit

1. lane eval fixtures
2. runtime provider scorecard
3. prompt/memory/transport architecture audit
4. stale identity/workflow drift CI

目标: 从"经验调度"升级到"数据化选择 runtime / workflow / role prompt"。
