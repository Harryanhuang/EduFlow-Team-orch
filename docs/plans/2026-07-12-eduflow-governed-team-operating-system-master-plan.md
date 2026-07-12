# EduFlow Governed Team Operating System Master Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan package-by-package. Do not start a later gate until the preceding gate's acceptance evidence is recorded.

> **Mandatory prerequisite:** Before implementation, approve `docs/plans/2026-07-12-eduflow-upgrade-acceptance-standard.md`. If that document's approval page is blank, this implementation plan remains draft-only.

**Goal:** 将 EduFlow 从“以 Prompt、Markdown Workflow 和分散文件状态驱动的多 Agent 工具”升级为具备机器可执行身份权限、可靠消息投递、Agent Loop、Workflow 团队 Loop、事务化真相和可验证组织学习的公司级多智能体操作系统。

**Architecture:** 系统分为 Identity & Authority、Skills & Capability、Agent Loop、Workflow Loop、Evidence & Authority、Evolution Loop 六层。Workflow Definition 是版本化团队协议，Workflow Instance 是一次真实团队 Loop；Agent Loop 只负责单角色执行与自检，`worker_review` 负责正式 REVIEW，`manager` 仍是唯一 CLOSEOUT owner。所有跨层状态最终迁入事务化事件存储，Prompt 只作为已授权规则的渲染结果，不再作为权限真相源。

**Tech Stack:** Python 3.10+、SQLite WAL、tmux、Feishu/Lark、TOML/YAML/Markdown registry、pytest、Ruff、Pyright/mypy、TruffleHog/Gitleaks、pip-audit、现有 EduFlow CLI。

---

## 0. 文档定位

这是 2026-07-12 起的总入口计划。旧计划继续保留为历史证据，不删除、不覆盖；实施时以本计划的状态判断、依赖顺序和 Gate 为准。

实施顺序必须是：先批准验收标准，再批准实施范围，最后执行代码计划。不得先写代码、再根据结果补验收口径。

本计划整合：

- `2026-06-21 EduFlow Team overnight gap repair packages.md`
- `2026-06-23 AP overnight gap repair packages.md`
- `2026-07-01-claude-squad-agent-orchestrator-gap-report.md`
- `2026-07-01-ecc-to-eduflow-team-skill-upgrade-plan.md`
- `2026-07-01-phase0-residency-audit.md`
- `2026-07-02-eduflow-status-trust-baseline.md`
- `2026-07-04-loop-engineering-execution-layer.md`
- `2026-07-04-loop-engineering-observation-plan.md`
- `2026-07-07-claudeteam-upstream-borrowing-plan.md`
- `2026-07-11-scheduled-tasks-design.md`
- `2026-07-11-scheduled-tasks.md`
- 2026-07-12 全仓安全、架构、逻辑、冗余、Skills、Loop、Workflow、Identity 复盘结论。

### 状态词

| 状态 | 含义 |
|---|---|
| `DONE` | 当前代码和测试中已有可验证实现 |
| `PARTIAL` | 已有 primitives 或只读视图，但未形成完整闭环 |
| `PLANNED` | 有旧设计或候选文档，尚无生产实现 |
| `BLOCKED` | 前置真相、权限或迁移条件未满足，禁止实施 |
| `SUPERSEDED` | 旧方案的判断被本计划替代，但文档保留 |

---

## 1. 当前实现总账

### 1.1 已落地能力

| 能力 | 状态 | 当前证据 | 本计划处理 |
|---|---|---|---|
| Residency warm/active/sleep/wake | `DONE` | `runtime/residency.py`、residency tests | 保留，接入 Authority 与 Workflow workload |
| Feishu Cards v2 | `DONE` | `feishu/cards_v2.py`、schema 与 tests | 收敛旧 cards，卡片类型接入权限 |
| Flow task 与 REVIEW/CLOSEOUT 边界 | `DONE/PARTIAL` | task authority tests、truth-contract tests | 保留边界，转为机器授权 |
| Runtime verify/failover primitives | `PARTIAL` | verify、failover、watchdog | 修假阳性、并发切换和 live smoke |
| Workflow Registry | `DONE` | list/show/use/validate/candidates/promote | 升级为版本化 Definition Registry |
| Workflow Instance | `PLANNED` | 无实例存储和执行状态机 | 新建团队 Loop 核心 |
| Agent Loop checker/evidence | `PARTIAL` | loop runner、archive、task CLI | 补生命周期、进度判断、预算和真实证据 |
| Team Loop read model | `PARTIAL` | `team_loop_account.py` | 降为兼容视图，Workflow Instance 成为真相 |
| Evolution Packet | `PARTIAL` | read-only candidate generator | 接入采用、版本和效果回测 |
| Asset Registry | `PARTIAL` | Skill/Workflow 资产扫描 | 升级为 Capability Registry |
| Scheduled Tasks | `PLANNED` | 设计和分包文档 | 推迟到 Workflow Instance 稳定之后 |
| Memory 双实现收敛 | `BLOCKED` | 本地 `eduflow.memory` + 外部 `flow_memory` | 先统一 store 与依赖，再演进 |

### 1.2 当前验证基线

- 生产 Python 文件：145。
- 生产源码约 50,548 行。
- 2026-07-12 全量测试：`2768 passed in 240.21s`。
- `compileall`、`pip check`、`git diff --check` 通过。
- 当前工作区存在用户未提交改动；实施包不得覆盖或重置这些改动。

### 1.3 已确认的未解决风险

1. Feishu 高权限 Slash 缺统一 RBAC，且 `sender_id` 未完整传入 SlashContext。
2. DeliveryReport 未成为 ACK 条件，投递失败仍可能推进 seen/cursor。
3. `eduflow.toml` 被 Git 跟踪且历史中出现非空认证值。
4. sensitive storage 缺 `cryptography` 时退化为不安全 XOR。
5. runtime `proved_ready` 存在 timestamp、cache、skipped smoke 假阳性。
6. runtime switch 无 per-agent 串行化，事件补写会覆盖并发 append。
7. 高优 inbox 使用模糊 `mark_all_read(...keep_last=1)`，可能吞掉独立任务。
8. Identity、Role、Authority、Assignment、Skill、Workflow 规则混在长 Prompt/TOML notes 中。
9. 项目 Skill、用户 Skill、reference-only Skill 和 proposed Skill 缺统一治理。
10. Workflow 只有 Definition Registry，没有 Instance、Step、Gate、ACK 和运行事件。
11. Agent Loop background 无 PID/lease/heartbeat/cancel/reconcile；stop rule 只比较失败命令数量。
12. task snapshot/event、cursor/ACK、runtime status/event 缺跨文件事务。
13. memory 双实现、cards 双实现、旧角色 alias 与巨石模块仍在累积维护成本。

---

## 2. 不可破坏的系统原则

以下原则必须转化为代码、schema、测试和 CI Gate，不能只写在 Prompt：

1. 未知身份默认拒绝高权限操作。
2. 未持久化成功不得 ACK；retryable failure 不得推进 cursor/seen。
3. unread 不等于 consumed；`skipped` 不等于 verified。
4. Agent Loop passed 只代表 checker evidence，不代表 delivered、REVIEW 或 CLOSEOUT。
5. `worker_review` 是公司级正式 REVIEW owner；`review_course` 只作为有期限的历史 alias。
6. `manager` 是唯一 CLOSEOUT owner；manager 不生产业务/代码产物。
7. Producer 不得正式 REVIEW 自己的产物。
8. Runtime operator 不得修改业务 verdict；Recorder 不得派工或批准候选规则。
9. Workflow Definition 与 Workflow Instance 分离；实例绑定 definition version/hash。
10. 双写只能是有限期迁移手段，必须有对账、截止日期和单一切换点。
11. Evolution candidate 不得自动写入永久 Skill、Workflow 或 Memory。
12. 安全、身份、权限和数据迁移失败时 fail closed，不允许临时 fail-open。

### 2.1 2026-07-12 对话暴露出的系统性问题

本节不是一般风险清单，而是今天连续复盘中明确暴露、必须进入设计的认知纠偏。

#### 问题 A：代码中的 EduFlow 不等于实际运行中的 EduFlow

静态代码可以证明某条路径存在，但不能自动证明当前 daemon、tmux pane、checkout、配置、外部 editable dependency 和飞书群正在使用同一版本。此前 manager dead-pid、runtime switch 显示成功但 live pane 仍错误等事故已经证明：状态标签、缓存 verdict 和真实运行面可能分离。

**设计响应：** G-1 必须先生成生产拓扑；每个进程记录 commit/config hash；任何 runtime/identity/workflow verdict 都必须区分 declared、cached、live-proved。

#### 问题 B：EduFlow 已经是生产控制面，却仍按个人自动化脚本治理

系统已掌握任务派发、组织身份、模型凭据、本机命令、审核结论、记忆、故障恢复和用户外显，但许多边界仍依赖“群成员可信”“Agent 会遵守 Prompt”“本机装过依赖就算项目依赖”等假设。

**设计响应：** Identity/Authority、RBAC、职责分离、依赖锁、审计和人工接管必须成为平台能力，而不是补充说明。

#### 问题 C：最危险的失败是每一层都认为自己成功

可能同时出现：router 认为已处理、cursor 已推进、inbox 未落盘、Agent 未消费、task 未更新、群里却出现完成表述。局部成功会共同制造虚假闭环。

**设计响应：** 明确端到端成功链；任何上游 ACK 必须依赖下游 durable evidence；外显结论必须来自权威事件，不得由自由文本反推。

#### 问题 D：缺少信任模型和最大损害边界

当前没有正式回答普通群成员、operator、admin、manager、worker、reviewer、runtime operator、recorder 分别能控制什么；所有 Agent 默认高权限运行进一步扩大了 Prompt Injection 和误操作影响。

**设计响应：** G0/G1 建立 command RBAC、Role/Authority、Capability Pack、工具权限和最小化凭据范围；生产默认不以全局 YOLO 权限作为长期目标。

#### 问题 E：缺少服务目标、失败预算和自动化停止条件

当前 watchdog、retry、runtime failover、manager cadence 和 Loop 都有恢复动作，但没有统一定义消息延迟、最大重试、最大切换、最大循环时间和何时必须冻结自动化。

**设计响应：** 引入 SLO、budget 和 circuit breaker；自动恢复连续失败后进入 `attention_required/human_takeover`，不能无限重试。

#### 问题 F：临时兼容最可能在三个月内侵蚀本次修复

最可能的回归路径是：RBAC 影响业务后增加 fail-open、ACK 严格后把 retry 当成功、smoke 未实现后把 skipped 当 ready、task_id 缺失后恢复模糊文本匹配、SQLite 双写长期不退出、旧 alias 永久保留。

**设计响应：** 所有兼容行为必须有 owner、原因、指标、到期日和删除测试；无 expiry 的 compatibility 不得合并。

#### 问题 G：Skills 不是越多越好，当前缺少能力供应链

项目级 11 个 Skill 与约 200 个用户级 Skill 并存；available、installed、approved、assigned、reference、deprecated 没有统一语义，角色 notes 还在自然语言中硬编码 Skill 路由。

**设计响应：** G1 Capability Registry 与 Role Skill Pack 是前置治理，不是末尾清理。

#### 问题 H：Workflow 才是团队层级 Loop

旧双层 Loop 方案把 Team Loop 主要建成 task read model；今天确认这仍低了一层。Workflow Definition 应描述团队协议，Workflow Instance 才是一次真实团队 Loop；task/Agent Loop 是其中的执行单元。

**设计响应：** G3 建立 Workflow Instance、Step、Gate、Role Binding、Handoff ACK、REVIEW/Repair/CLOSEOUT；`team_loop_account` 降为兼容视图。

#### 问题 I：身份 Prompt 正在成为规则垃圾场

身份、岗位、权限、任务、Workflow、Skill、通信格式、历史事故纠偏被混入长 Prompt/TOML notes。继续增加“必须/不得/唯一”会扩大上下文、冲突和执行漂移。

**设计响应：** Prompt 只渲染当前 Agent 需要的精简结果；权限进入 Authority Policy，岗位进入 Role Catalog，临时职责进入 Workflow Assignment，操作方法进入 Skill。

#### 问题 J：缺少跨层最终 Owner

Runtime、message、task、workflow、review、memory、skills 各自局部正确时，仍可能产生整体失败。若没有一位平台 owner 对跨层契约负责，问题会在模块边界反复出现。

**设计响应：** 在 G-1 指定 EduFlow control-plane owner；任何跨层 schema、authority、成功语义和迁移必须由该 owner 审批，manager 仍只做业务派发与 CLOSEOUT，不承担代码实现。

### 2.2 今天确认的系统词汇

后续文档、代码和群内沟通统一使用：

| 术语 | 定义 |
|---|---|
| Agent Loop | 单角色围绕一个 task 的执行、自检、返修循环 |
| Workflow Loop | 多角色围绕一个业务目标的派发、交接、执行、REVIEW、返修、CLOSEOUT 循环 |
| Evolution Loop | 跨多个 Workflow Instance 的经验提炼、审批、版本更新和效果回测 |
| Identity | Agent 是谁，不包含当前任务 |
| Role | 岗位长期职责，不包含具体 Agent 名 |
| Authority | 系统允许执行的动作和范围 |
| Capability Pack | 允许使用的 Skills、工具和依赖 |
| Assignment | 某次 Workflow/Task 中的临时责任 |
| REVIEW | `worker_review` 的正式审核 verdict |
| CLOSEOUT | `manager` 的正式最终收口 |

---

## 3. 目标架构

```text
User / Feishu / CLI
        |
        v
Identity Resolution + Command RBAC
        |
        v
Reliable Message Ingress
received -> persisted -> delivered -> acknowledged -> completed/dead-letter
        |
        v
Workflow Instance (Team Loop)
Definition version -> role binding -> steps -> gates -> REVIEW -> CLOSEOUT
        |
        +-----------------------+
        |                       |
        v                       v
Agent Task / Agent Loop       Evidence & Authority
execute/check/repair          self-check/REVIEW/CLOSEOUT
        |                       |
        +-----------+-----------+
                    v
Transactional Event Store + Read Models
                    |
                    v
Evolution Loop
candidate -> human approval -> versioned update -> outcome comparison
```

### 3.1 六类对象必须分开

| 对象 | 回答的问题 | 真相源 |
|---|---|---|
| Agent Identity | 它是谁 | identity registry |
| Role Definition | 岗位长期负责什么 | role catalog |
| Authority Profile | 系统允许它做什么 | RBAC policy |
| Capability Pack | 它能使用哪些 Skill/工具 | capability registry |
| Workflow Assignment | 本次团队 Loop 扮演什么角色 | workflow instance |
| Task Assignment | 当前要交付什么 | task ledger |

---

## 4. 实施 Gate 总览

| Gate | 目标 | 预计周期 | 前置 | 发布条件 |
|---|---|---:|---|---|
| G-1 | 生产事实与资产基线 | 1–2 天 | 无 | 可回答实际运行版本、身份、配置、数据和资产来源 |
| G0 | 安全与可靠消息止血 | 3–5 天 | G-1 | Slash 权限、ACK、凭据、加密 P0 关闭 |
| G1 | Runtime 真相、敏感数据生命周期、Identity/Authority/Skills 治理 | 2 周 | G0 | runtime verdict 可信、安装可复现、权限由代码强制 |
| G2 | Agent Loop 生命周期 | 1 周 | G1 | run 可观察、取消、恢复、对账，stop rule 可解释 |
| G3 | Workflow Instance 团队 Loop | 2–3 周 | G1/G2 | 多 task/角色/step/gate/ACK/REVIEW/CLOSEOUT 可闭环 |
| G4 | 事务化状态存储 | 2–4 周 | G3 schema 稳定 | 消息、task、workflow、loop、runtime 具备事务真相 |
| G5 | Evolution Loop | 2 周 | G4 | 更新 Skill/Workflow/Spec 后能比较效果 |
| G6 | 定时任务与主动运营 | 2 周 | G3/G4 | scheduled occurrence 复用 Workflow Instance 和 RBAC |
| G7 | 降复杂度与清理 | 持续 | 各层稳定 | 单实现、无过期 alias、巨石模块按边界拆分 |

### 4.1 原 V0–V4 周计划映射

用户此前确认的周计划不删除，映射到新版 Gate 如下：

| 原周计划 | 新版位置 | 状态 |
|---|---|---|
| 第 1 周 V0：权限、消息 ACK、凭据、加密止血 | G-1 + G0.1–G0.5 | 完整保留；前置增加 1–2 天生产事实基线 |
| 第 2 周 V1：runtime 真相、switch 串行化、inbox 修复 | G0.5 + G1.R1–G1.R3 | 完整保留；inbox 先止血，runtime 随后修复 |
| 第 3 周 V2：敏感数据生命周期、干净安装 | G1.D1–G1.D3 | 完整保留；与身份治理同一 Gate、独立提交 |
| 第 4–6 周 V3：SQLite 双写、对账和切换 | G4.1–G4.3 | 完整保留；前置要求 Workflow Instance schema 稳定 |
| 第 7 周以后 V4：巨石拆分和冗余清理 | G7 | 完整保留；改为持续小 PR，不做大爆炸重写 |

新版并未取消原 V0–V4，而是在其前后补上 Identity/Skills/Workflow/Evolution 的必要治理，并调整依赖顺序。

---

## 5. G-1：生产事实、资产与变更基线

**目标：** 防止修错 checkout、误锁合法操作者、迁漏数据或把历史计划当成当前实现。

### Task G-1.1：生成生产拓扑清单

**Files:**
- Create: `docs/operations/eduflow-production-topology.md`
- Create: `scripts/audit_production_topology.py`
- Test: `tests/unit/test_audit_production_topology.py`

**步骤：**

1. 先写测试，固定输出必须包含进程、PID、checkout、commit SHA、配置路径、state dir、tmux session、daemon profile。
2. 运行测试并确认脚本缺失时失败。
3. 实现只读审计脚本，禁止输出 secret value。
4. 在当前机器生成基线文档。
5. 人工核对是否存在多 checkout、多 daemon 或旧命令入口。

**验收：** 每个运行进程都能追溯到代码 revision 和配置 generation。

### Task G-1.2：建立旧计划完成度索引

**Files:**
- Create: `docs/plans/PLAN_STATUS_INDEX.md`

**步骤：**

1. 为 `docs/plans` 每个文件标记 `historical / active / superseded / observation-only`。
2. 为 active 计划链接本总方案中的 Gate/Task。
3. 标记已执行内容的 commit/test evidence。
4. 标记未执行内容，禁止仅凭计划文档判断 feature 存在。

### Task G-1.3：建立数据与配置清单

**Files:**
- Create: `docs/operations/state-and-config-inventory.md`

清单至少包含 inbox、task、task events、runtime status、switch events、cursor、seen、loop runs、memory DB、workflow assets、Skill assets的写入者、读取者、权限、备份和迁移要求。

### Task G-1.4：定义信任模型、SLO 与人工接管

**Files:**
- Create: `docs/architecture/TRUST_MODEL.md`
- Create: `docs/operations/CONTROL_PLANE_SLO.md`
- Create: `docs/operations/HUMAN_TAKEOVER_RUNBOOK.md`

**信任模型至少回答：**

- 飞书普通成员、operator、admin 的命令权限；
- 每个 Role 的工具、凭据、文件和外部系统访问范围；
- Prompt Injection 后单个 Agent 的最大损害范围；
- 哪些动作必须双人/双角色确认；
- 哪些凭据不得进入 Agent pane 环境。

**首版 SLO 建议由 owner 审批后固化：**

| 指标 | 初始目标 |
|---|---|
| 高优消息 durable persist | 99.9%，10 秒内 |
| retryable delivery 最终成功或 dead-letter | 5 分钟内有明确结果 |
| runtime switch | 3 分钟内 proved 或 failed，不无限 pending |
| Workflow handoff ACK | 高优 5 分钟内，否则升级 |
| orphaned Loop/Workflow 检出 | 2 个巡检周期内 |
| unauthorized control action | 100% 拒绝并审计 |

**Circuit Breaker：** 同一 runtime 连续切换、同一消息连续 retry、同一 Loop 重复失败或同一 Workflow 连续 repair 超过预算时，进入 `human_takeover`，停止新自动动作。

### Task G-1.5：指定治理 Owner 与决策流程

**Files:**
- Create: `docs/governance/OWNERSHIP.md`
- Create: `docs/governance/DECISION_AND_EXCEPTION_PROCESS.md`

至少指定：control-plane owner、security owner、workflow definition maintainer、Skill registry maintainer、schema/migration owner、runtime operator、正式 REVIEW owner、CLOSEOUT owner。临时例外必须记录 expiry，不允许口头永久放宽。

**Gate G-1 验收命令：**

```bash
./scripts/eduflowteam health --json
./scripts/eduflowteam runtime list --json
./scripts/eduflowteam workflow validate --strict
python3 scripts/audit_production_topology.py --json
```

---

## 6. G0：安全与可靠消息止血

### Task G0.1：统一 Slash RBAC

**Files:**
- Modify: `src/eduflow/feishu/router.py`
- Modify: `src/eduflow/feishu/deliver.py`
- Modify: `src/eduflow/feishu/slash.py`
- Create: `src/eduflow/security/authorization.py`
- Test: `tests/unit/test_feishu_slash_authorization.py`
- Test: `tests/integration/test_control_plane_authorization.py`

**测试优先场景：**

1. 普通成员可以执行 allowlisted read-only 命令。
2. 未知/缺失 sender_id 调用写命令必须拒绝。
3. operator 可以 `/send`，不能 `/clear` 或 runtime switch。
4. admin 可以执行破坏性命令，并产生审计事件。
5. operator/admin 配置为空时，写命令 fail closed。
6. `decision.sender_id` 必须完整传入 `SlashContext`。

### Task G0.2：Delivery ACK 与 retry/dead-letter

**Files:**
- Modify: `src/eduflow/feishu/deliver.py`
- Modify: `src/eduflow/feishu/subscribe.py`
- Modify: `src/eduflow/feishu/catchup.py`
- Create: `src/eduflow/store/message_delivery.py`
- Test: `tests/unit/test_feishu_delivery_ack.py`
- Test: `tests/integration/test_message_retry_contract.py`

**DeliveryReport 最小契约：**

```python
durable_success: bool
retryable_failure: bool
terminal_failure: bool
failure_reason: str
```

只有 inbox 成功落盘或 Slash 回复成功发布，才能推进 cursor/seen。terminal drop 推进；retryable failure 不推进；超过上限进入 dead-letter。

### Task G0.3：凭据治理

**Files:**
- Create: `eduflow.example.toml`
- Modify: `.gitignore`
- Modify: config loader permission checks
- Create: `docs/operations/credential-rotation-runbook.md`

**特别 Gate：** token 轮换和 Git 历史清理必须由用户单独确认；代码准备与运维执行分开提交。

### Task G0.4：敏感存储 fail closed

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/eduflow/memory/sensitive.py`
- Test: sensitive storage tests

删除 XOR fallback；强制 AEAD；篡改 tag 必须失败；旧数据迁移前必须备份并逐条验证可解。

### Task G0.5：停止模糊自动已读

**Files:**
- Modify: `src/eduflow/commands/send.py`
- Modify: `src/eduflow/store/local_facts.py`
- Test: messaging and concurrent-task tests

删除基于 agent 名和模糊文本的 `mark_all_read(...keep_last=1)`。仅显式 `supersedes_message_id` 或同 `task_id + higher revision` 可以 supersede；旧消息标记 `superseded`，不得伪装为 `read`。

**G0 发布门：**

```bash
python3 -m pytest tests/unit/test_feishu_slash_authorization.py -q
python3 -m pytest tests/integration/test_message_retry_contract.py -q
python3 -m pytest
python3 -m compileall -q src tests
python3 -m pip check
git diff --check
```

---

## 7. G1：Runtime 真相、敏感数据生命周期、Identity、Authority 与 Skills Capability

### Task G1.R1：修复 Runtime Truth Verdict

**Files:**
- Modify: `src/eduflow/commands/runtime_verify.py`
- Modify: `src/eduflow/runtime/verify.py`
- Modify: `src/eduflow/runtime/lifecycle.py`
- Modify: runtime status/read model
- Test: `tests/unit/test_runtime_verify.py`
- Test: `tests/integration/test_runtime_truth_contract.py`

**测试优先场景：**

1. inbox 使用真实 `created_at`；仍 unread 的 probe 永远不能标为 consumed。
2. `skipped` live smoke 只能产生 `ready_unproven`，不得产生 `proved_ready`。
3. cached verdict 超过 TTL 自动失效。
4. pane 存在但出现 auth/provider/error marker 时不得标 clean。
5. runtime status 与 live pane/env 不一致时输出 drift，而不是信缓存。
6. `proved_ready` 必须分别证明 process、CLI、environment、provider 和 inbox consumption。

目标状态：

```text
declared
-> spawned
-> cli_ready
-> environment_verified
-> provider_verified
-> inbox_consumed
```

只有全部 required stages 通过才得到 `proved_ready`；缺少 live smoke 时为 `ready_unproven`。

### Task G1.R2：Runtime Switch 串行化与 Append-only 审计

**Files:**
- Modify: `src/eduflow/commands/runtime_switch.py`
- Modify: `src/eduflow/runtime/lifecycle.py`
- Modify: `src/eduflow/runtime/verify.py`
- Modify: watchdog/failover callers
- Test: `tests/integration/test_runtime_switch_concurrency.py`

**实现契约：**

- 每个 Agent 一个 switch lock。
- manual、watchdog、failover 共用唯一切换入口。
- 使用 `switch_id + generation/CAS`。
- 事件使用 `switch_started`、`switch_completed`、`switch_failed` 追加记录。
- 禁止读取整份 JSONL 后覆盖回写。
- 旧 generation 完成事件不得覆盖新 runtime status。

**验收：** manual/watchdog 并发时只有一个切换生效；最终 status、事件和 live tmux pane 三者一致。

### Task G1.R3：Inbox Reconciliation 与 Stale Truth

**Files:**
- Modify: inbox/read/local facts reconciliation paths
- Test: `tests/integration/test_inbox_reconciliation.py`

在 G0.5 停止模糊自动已读后，补齐显式 `delivered/acknowledged/started/completed/reconciled/superseded` 语义。旧 unread、旧 verdict 和新 task 状态冲突时进入 reconciliation queue，不得直接作为 live blocker 或被静默吞掉。

### Task G1.D1：敏感数据改为 DEK/KEK 生命周期

**Files:**
- Modify: `src/eduflow/memory/sensitive.py`
- Create: sensitive storage migration module
- Test: password change/recovery/migration/tamper tests

**目标模型：**

```text
random DEK -> encrypt sensitive records
password-derived KEK -> wrap DEK
recovery key -> independently wrap the same DEK
```

密码变更只重新包裹 DEK，不重写数据密钥；恢复密码不得使旧密文不可解。删除弱安全问题恢复，recovery key 只展示一次。迁移前备份，迁移后逐条解密比对，任一记录失败时保持旧数据不变。

### Task G1.D2：干净安装与 Flow Memory 依赖收口

**Files:**
- Modify: `pyproject.toml`
- Modify: `Dockerfile`
- Modify: installation docs
- Create: clean-install integration test/script

短期先声明并锁定当前实际硬依赖 `flow-memory`，或将其作为明确 optional feature 并保证 core import 不因缺包崩溃；不得继续依赖另一个 workspace 的 editable install。

**验收环境：**

1. 全新 venv，无其他 editable package。
2. `pip install` 后 CLI import/start 正常。
3. memory 初始化、router 启动和基础测试正常。
4. Docker `--no-cache` build 成功。
5. 输出依赖版本和代码 revision，不依赖用户交互 shell PATH。

### Task G1.D3：可复现依赖与供应链门禁

提交 Python constraints/lock 与 Node lockfile；启用 `pip-audit`、`npm audit`、hash/checksum、SBOM 和 clean-build CI。Bot Creator 不得继续忽略 lockfile 或依赖未固定的 postinstall 下载。

### Task G1.1：Role Catalog

**Files:**
- Create: `config/roles/*.yaml`
- Create: `src/eduflow/governance/roles.py`
- Test: `tests/unit/test_role_catalog.py`

首批角色：`manager`、`worker`、`reviewer`、`builder`、`runtime_operator`、`recorder`。Role 只描述长期职责和禁止职责，不绑定具体 Agent。

### Task G1.2：Authority Profiles

**Files:**
- Create: `config/authority/*.yaml`
- Create: `src/eduflow/governance/authority.py`
- Modify: task/review/closeout/runtime/skill-promotion write paths
- Test: `tests/integration/test_authority_enforcement.py`

必须由代码拒绝 producer 自审、worker CLOSEOUT、runtime operator 改业务 verdict、recorder 派工、builder 生产业务内容等越权操作。

### Task G1.3：Identity Registry 与版本

**Files:**
- Create: `config/identities.yaml`
- Modify: `src/eduflow/agents/identity.py`
- Modify: runtime status schema
- Test: `tests/unit/test_identity_render.py`
- Test: `tests/integration/test_identity_preflight.py`

记录 `identity_version`、`role_version`、`authority_version`、`capability_pack_version`、`config_hash`。`identity.md` 变为这些结构化事实的精简渲染，不再保存全部真相。

### Task G1.4：Capability Registry 与 Skill Pack

**Files:**
- Create: `skills/registry.yaml`
- Modify: `src/eduflow/store/asset_registry.py`
- Create: `src/eduflow/governance/capabilities.py`
- Test: `tests/unit/test_skill_registry.py`

Skill schema 至少包含：`id/version/status/type/owner/allowed_roles/risk/side_effects/triggers/requires/supersedes/deprecated_aliases/source_of_truth`。

状态统一为：`approved / experimental / reference / deprecated`。角色绑定 `required / optional / forbidden` Skill Pack，禁止默认向所有 Agent 暴露约 200 个用户级 Skill。

### Task G1.5：Alias EOL

将 `review_course` 定义为 `worker_review` 的有期限历史 alias；新增引用必须自动重写或拒绝。完成 docs、workflow、skill、tests 和 runtime config 的引用清理后删除兼容路径。

**G1 验收：**

- 任意正式动作可解释为 `agent -> role -> authority -> assignment`。
- Agent 启动失败时明确显示 `identity_invalid / authority_conflict / capability_missing`。
- Prompt 缩短，但代码级权限测试覆盖不下降。

---

## 8. G2：Agent Loop 运行生命周期

### Task G2.1：Loop Run Supervisor

**Files:**
- Modify: `src/eduflow/store/loop_runs.py`
- Create: `src/eduflow/runtime/loop_supervisor.py`
- Modify: `src/eduflow/commands/task.py`
- Test: `tests/unit/test_loop_supervisor.py`

Run 状态：`created/scheduled/running/checking/repair_wait/passed/stopped/failed/cancelled/orphaned`。记录 PID、runner_id、lease、heartbeat、started/ended、exit code。

新增：

```bash
task loop-cancel <loop_id>
task loop-resume <loop_id>
task loop-reconcile
```

### Task G2.2：修 Stop Rules

**Files:**
- Modify: `src/eduflow/runtime/loop_runner.py`
- Test: `tests/unit/test_runtime_loop_runner.py`

不再按 failed command 数量判断进度。比较失败测试集合、fingerprint 集合、相关 diff、失败数量和连续相同次数；区分 regression、residual、newly_exposed、flaky、infrastructure、policy failure。

### Task G2.3：版本化 Loop Spec

**Files:**
- Replace/extend: `src/eduflow/runtime/loop_specs.py`
- Create: `config/loop_specs/*.yaml`
- Test: `tests/unit/test_runtime_loop_specs.py`

Spec 强制 `allowed_roles/stages/checks/timeouts/budgets/forbidden/success`，不是只读元数据。第一阶段仍只维护 `code-repair`，不急于扩展业务 Spec。

### Task G2.4：不可变 Cycle Manifest

每轮保存 spec version/hash、base/head commit、dirty hash、环境指纹、actor、duration、exit code、测试统计、真实 diff ref。checker output 必须脱敏。

### Task G2.5：资源预算

加入 `max_cycles/max_wall_time/max_checker_time/max_parallel_runs/max_changed_files/max_diff_size`。达到预算进入 `human_review_required`，不得笼统假装 passed 或无限循环。

---

## 9. G3：Workflow Instance，团队层级 Loop

### Task G3.1：Workflow Definition Schema 与版本

**Files:**
- Create: `src/eduflow/workflow/schema.py`
- Modify: `src/eduflow/commands/workflow.py`
- Modify: `docs/workflows/_template/*`
- Test: workflow validation tests

Definition 需要 `workflow_id/version/status/roles/steps/dependencies/gates/timeouts/forbidden_moves/closeout_policy`。active Workflow 发布后内容 hash 固定；新变更产生新版本。

### Task G3.2：Workflow Instance Store

**Files:**
- Create: `src/eduflow/store/workflow_instances.py`
- Create: `tests/unit/test_workflow_instances.py`

实例记录 definition version/hash、goal、phase、role bindings、task ids、open/blocked gates、review iteration、current/next owner 和时间线。

### Task G3.3：Workflow 状态机

```text
draft -> intake_ready -> dispatching -> executing
-> evidence_pending -> review_pending -> reviewing
-> repair_required -> executing
-> closeout_ready -> closed
```

异常状态：`blocked/stalled/cancelled/failed/superseded`。所有 transition 必须校验 Authority、前置 Gate 和职责分离。

### Task G3.4：Role Binding 与冲突检测

Workflow 绑定抽象 role，不硬编码 agent 名。实例启动时解析 `reviewer -> worker_review`。拒绝 producer/reviewer 同人、manager 执行生产 step、runtime operator 担任业务 reviewer 等冲突。

### Task G3.5：Step、Handoff 与 ACK

每个 Step 定义 required inputs/outputs、entry/exit gates、owner、timeout、escalation。handoff 必须经历 `created -> persisted -> acknowledged -> started -> completed/superseded`。

### Task G3.6：REVIEW、Repair、CLOSEOUT

- Agent Loop passed 只满足 Step 的 self-check 条件。
- `worker_review` REVIEW 才能通过正式 review gate。
- reject 自动生成受控 repair assignment，不自动修改产物。
- 只有 manager 且所有 required gates 通过时才能 CLOSEOUT。

### Task G3.7：Workflow CLI

```bash
workflow start <workflow_id> --goal ... --by manager
workflow status <instance_id>
workflow bind-role <instance_id> <role> <agent>
workflow dispatch <instance_id> <step>
workflow submit <instance_id> <step> --task <task_id>
workflow review <instance_id> --verdict ... --by worker_review
workflow closeout <instance_id> --by manager
workflow cancel <instance_id>
```

第一版为半自动推进：系统计算 allowed transitions，人类/授权 Agent 显式执行；不做自动 REVIEW、自动 CLOSEOUT 或自动修复。

### Task G3.8：兼容 read model

现有 `team_loop_account.build(task_id)` 保留为兼容视图，但明确标记 derived。新 `workflow_account.build(instance_id)` 成为团队 Loop 主 read model。

---

## 10. G4：事务化状态真相

### Task G4.1：SQLite WAL Schema

首批表：

```text
messages
message_deliveries
message_attempts
tasks
task_events
workflow_instances
workflow_events
loop_runs
loop_cycles
runtime_instances
runtime_switches
control_audit
schema_migrations
```

### Task G4.2：有限期双写与自动对账

1. JSON 仍为读主源，SQLite 双写。
2. 每次写生成相同 idempotency key。
3. 自动对账必须为零差异。
4. 达到稳定窗口后 SQLite 切为读主源。
5. JSON 进入只读回滚窗口。
6. 截止日期后停止 JSON 写入。

不得无限期双写。

### Task G4.3：崩溃恢复测试

覆盖 inbox 写一半、task event 成功/snapshot 失败、cursor/ACK 半提交、workflow transition 半提交、runtime switch 中断、重复事件 replay。

---

## 11. G5：Evolution Loop

### Task G5.1：Experience Packet

从 Workflow Instance 和 Agent Loop 聚合：failure pattern、root cause class、repair move、repair outcome、recommended update surface、supporting runs、counterexamples、scope 和 expiry。

更新面固定为：

```text
loop_spec
skill
handoff_template
workflow_rule
role_authority
runtime_policy
memory_candidate
no_reuse
```

### Task G5.2：人工晋升 Gate

```text
candidate -> reviewer/manager audit -> promote/reject/archive
```

不得从 runtime trace 自动生成永久规则。

### Task G5.3：效果回测

每个正式更新关联 `change_id/version/first_adopted_instance`，比较更新前后的 review iteration、repair cycle、duration、failure rate 和人工介入次数。无改善或出现回归时撤销/修订。

### Task G5.4：Memory 前置卫生

在扩展候选来源前完成：单一 memory store、CLI/MCP 指向一致、placeholder candidate 清理、stale constraint 生命周期和固定 promote/reject 节奏。

---

## 12. G6：定时任务与主动运营

`2026-07-11-scheduled-tasks*.md` 保留为设计输入，但实现推迟到 Workflow Instance 和事务存储稳定后。

定时任务不应自建第二套 task/workflow 状态机。每个 occurrence 只负责：

```text
schedule fires
-> create/locate workflow instance
-> bind authorized roles
-> dispatch first allowed step
-> obey overlap/backpressure policy
```

定时规则不能直接绕过 manager approval、RBAC、Workflow Gate、REVIEW 或 CLOSEOUT。

---

## 13. G7：降复杂度与清理

### 13.1 Memory 单实现

先声明并锁定 `flow-memory` 依赖，建立 API/schema 等价矩阵、双写对账和数据迁移，再决定保留外部实现或本地实现。禁止直接删除 7,000+ 行本地 memory。

### 13.2 Cards 单实现

让 snapshot/card 调用统一 v2 schema，补视觉与结构契约测试，再删除 legacy helper。

### 13.3 巨石模块拆分

按解析、领域决策、持久化、呈现、外部副作用拆分：

- `store/task_event_scanner.py`
- `commands/task.py`
- `store/tasks.py`
- `commands/memory_cli.py`

每次只移动一个职责，先写 characterization tests，不在同一 PR 改业务语义。

### 13.4 文档与 alias 清理

统一 `worker_review`，清理 `review_course`；删除确认无引用的根目录无语义文件；将 observation/gap notes 与 active plans 分层索引；评估将大规模业务 content 迁至数据仓库。

---

## 14. CI、测试和发布门禁

### 14.1 每个包必跑

```bash
python3 -m compileall -q src tests
python3 -m pytest
python3 -m pip check
git diff --check
```

### 14.2 新增工程门禁

- Ruff。
- Pyright 或 mypy 渐进门禁。
- coverage baseline 与 changed-lines coverage。
- TruffleHog/Gitleaks。
- `pip-audit`、`npm audit`。
- Python/Node lockfile 与 SBOM。
- clean venv install。
- clean Docker build。
- per-test timeout。
- unit/integration/fault-injection 分层 CI。

### 14.3 必须保留的集成场景

1. 未授权 Slash 全部拒绝。
2. 投递失败不推进 cursor，恢复后只投递一次。
3. 两条不同 task_id 高优消息不能互相吞掉。
4. manual/watchdog runtime switch 并发只允许一个生效。
5. cached ready 在 pane/provider 失效后不能继续 `proved_ready`。
6. Agent Loop pass 不产生 REVIEW/CLOSEOUT。
7. producer 不能 REVIEW 自己产物。
8. Workflow repair 后必须重新经过 reviewer gate。
9. manager 只能在 closeout-ready 时 CLOSEOUT。
10. Workflow definition 升级不静默改变旧实例。
11. SQLite 双写差异不为零时禁止切换读主源。
12. Evolution 更新后必须有 outcome comparison。

---

## 15. 分支、提交与回滚

### 15.1 分支策略

每个 Gate 使用独立 `codex/` 前缀分支或独立 worktree。当前工作区有未提交改动，实施前必须先识别其 owner，不得 reset、checkout 或覆盖。

### 15.2 提交策略

一个提交只做一个可回滚决策，使用 Lore Commit Protocol。建议包序：

1. baseline inventory；
2. Slash RBAC；
3. Delivery ACK；
4. credential/config；
5. cryptography fail-closed；
6. Identity/Role/Authority；
7. Skill Registry；
8. Agent Loop lifecycle；
9. Workflow Definition version；
10. Workflow Instance；
11. Workflow Gate/authority；
12. SQLite dual-write；
13. read-source switch；
14. Evolution Loop；
15. cleanup。

### 15.3 回滚原则

- G0/G1 代码可单独 revert，但凭据不得回滚到旧值。
- schema migration 前必须备份和 dry-run。
- Workflow 新版本不能覆盖旧实例绑定。
- SQLite 切换保留有限期 JSON 只读回退。
- 不在同一发布中同时修改 schema、authority 和用户外显语义。

---

## 16. 暂不实施

在前置 Gate 未完成前，不做：

- 全自动 Workflow 执行；
- 自动 REVIEW 或 CLOSEOUT；
- 自动修复代码/业务内容；
- 自动把运行经验写成永久 Skill/Memory；
- 任意 DAG Workflow Engine；
- 大爆炸式 SQLite 迁移；
- 大爆炸式巨石模块重写；
- 在可靠 Run 生命周期前扩充大量业务 Loop Specs；
- 在 Workflow Instance 前实现 scheduled task 生产调度。

---

## 17. 三个月失效防线

最可能的失效方式是新功能绕开统一边界，或迁移期兼容永久化。因此建立以下架构测试：

1. 所有 Slash 写命令必须登记 Authority。
2. 所有 inbox/cursor 写必须通过 Message Delivery API。
3. 所有正式 verdict 必须通过 Review Authority API。
4. 所有 CLOSEOUT 必须通过 Manager Closeout Gate。
5. 所有 active Workflow 必须有 version/hash。
6. 所有 Workflow task 必须关联 instance/step。
7. 所有 production Skill 必须存在于 approved registry。
8. 所有 runtime switch 必须通过 per-agent lock/generation。
9. 双写必须有 expiry date 和 zero-diff metric。
10. deprecated alias 到期后 CI 直接失败。

### 17.1 Compatibility Debt Ledger

新增 `docs/governance/COMPATIBILITY_DEBT.md`，每条兼容项必须记录：

```text
compatibility_id
old_contract
new_contract
why_still_needed
owner
usage_metric
introduced_at
expires_at
removal_test
```

以下行为默认进入首批账本：`review_course` alias、legacy cards、JSON/SQLite 双写、旧 workflow alias、旧 memory import shim、任何 fail-open、任何 `skipped => ready` 兼容。

### 17.2 Architecture Boundary Tests

除功能测试外，增加仓库级边界测试，阻止新代码绕过：

- 直接写 cursor/seen；
- 直接写 task verdict/closeout；
- 未登记 Slash write handler；
- active Workflow 无 version/hash；
- production Skill 无 registry entry；
- Role/Authority 只存在于 Prompt、没有结构化定义；
- 新增 deprecated alias 无 expiry；
- 新增第二套状态存储无 migration decision。

---

## 18. 首批建议审批范围

不要一次批准整个路线实施。首批只审批：

```text
G-1 生产事实与资产基线
+
G0.1 Slash RBAC
+
G0.2 Delivery ACK/retry
+
G0.3 凭据代码准备（不含实际轮换）
+
G0.4 加密 fail-closed
+
G0.5 停止模糊自动已读
```

首批完成后提供：

- changed files；
-新增测试；
-全量验证；
-生产影响；
-回滚方法；
-剩余 P0/P1；
-是否允许进入 G1 的建议。

---

## 19. 完成定义

EduFlow 的本轮升级只有在以下条件同时满足时才算完成：

1. 系统可以证明每个 Agent 的 Identity、Role、Authority、Skill Pack 和当前 Workflow Assignment。
2. 消息从接收到消费有完整 ACK、retry、dead-letter 和 correlation chain。
3. Agent Loop 可启动、观察、取消、恢复和解释停止原因。
4. Workflow 是版本化团队协议，并有真实 Instance/Step/Gate/Role Binding。
5. `worker_review` REVIEW 与 `manager` CLOSEOUT 由代码强制。
6. 核心状态拥有事务化单一真相和崩溃恢复能力。
7. Skills、Workflow、Loop Spec 和 Identity 更新都能追踪版本与效果。
8. 定时任务复用 Workflow Instance，不另建旁路。
9. CI 可以阻止安全、权限、状态语义和 alias 回归。
10. 运维人员能够从一个 correlation id 追踪完整团队 Loop。
