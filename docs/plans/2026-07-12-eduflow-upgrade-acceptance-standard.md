# EduFlow 全面升级验收标准

**文档类型：** 实施前验收契约（Acceptance Contract）

**适用方案：** `2026-07-12-eduflow-governed-team-operating-system-master-plan.md`

**生效规则：** 本标准批准前，不进入生产代码实施；任一 Gate 未满足全部强制项，不得宣布完成，也不得进入依赖该 Gate 的下一阶段。

---

## 0. 契约治理与实施边界

### 0.1 文档优先级

本次升级出现冲突时，按以下顺序解释和执行：

1. 本验收标准；
2. `2026-07-12-eduflow-governed-team-operating-system-master-plan.md`；
3. 当前会话提供的顶层 `AGENTS.md` 合同与 Lore Commit Protocol；
4. 仓库 `CLAUDE.md` 中未被本次升级明确替代的工程约定。

不得用低优先级文档绕过高优先级 Gate、权限、数据完整性或审批要求。发现无法按此顺序消解的强制冲突时停止实施并升级给项目所有者。

### 0.2 本轮批准的工程例外

以下内容是本次升级对现有 `CLAUDE.md` 的受控、限域替代，不构成其他项目的通用例外：

- G4 可以引入 SQLite WAL 作为目标事务真相源，替代“no DB”现状；
- 可以创建总方案和每 Gate 验收包明确要求的 `docs/operations/`、`docs/architecture/`、`docs/governance/` 与 `acceptance/`；
- 可以创建只读、可独立运行且不承载业务写逻辑的 `scripts/audit_production_topology.py`；
- 可以保留总方案明确要求的有限期兼容 read model、alias 和迁移 shim，但必须登记 owner、usage metric、expiry 和 removal test；
- `CLAUDE.md` 中的分支名称仅视为历史描述，实施以实时 `git branch`、HEAD 和 worktree 事实为准。

### 0.3 跨仓库与生产 checkpoint

- 本轮默认只修改当前 EduFlow 仓库。对 sibling `flow-memory` 仓库的修改必须另行提交 scope checkpoint；当前仓库可以先完成接口、依赖、迁移设计与兼容验证。
- 外部消息发送、生产凭据轮换、Git 历史重写、生产数据库读写主源切换和不可逆生产数据迁移仍需在对应 Gate 单独获得项目所有者明确批准。
- 同批批准多个 Gate 只表示范围获批，不表示可以跨 Gate 实施；必须先获得前一 Gate 的正式 REVIEW PASS 或本标准允许的 CONDITIONAL PASS。

---

## 1. 验收原则

### 1.1 判定只允许三种结果

| 结果 | 含义 |
|---|---|
| `PASS` | 所有强制标准通过，证据完整，无未处理否决项 |
| `CONDITIONAL PASS` | 仅允许存在明确列出的非安全、非数据完整性 LOW 风险；有 owner、期限和回归测试 |
| `FAIL` | 任一强制项失败、证据缺失、测试未运行或存在否决项 |

以下表述不得作为验收结论：

- “看起来正常”；
- “应该没问题”；
- “测试大部分通过”；
- “代码已经写完”；
- “Agent 说完成了”；
- “群里已经发了 PASS”；
- “之前运行过”；
- “暂时没有发现报错”。

### 1.2 权限边界

- 实施 Agent 只能提交 `HANDOFF` 和自检证据，不能批准自己的工作。
- `worker_review` 负责正式 `REVIEW` 验收 verdict。
- `manager` 根据 REVIEW 和本标准决定是否正式 `CLOSEOUT`。
- 安全、凭据轮换、数据迁移和生产切换需要对应 owner 的专项签字。
- Agent Loop `passed` 不能替代 REVIEW；REVIEW 不能替代 manager CLOSEOUT。

### 1.3 证据优先级

从强到弱：

1. 自动化测试和机器可读输出；
2. 数据库/事件/审计记录；
3. 可复现的 CLI 运行结果；
4. 受控故障注入结果；
5. 人工检查记录；
6. 群聊或自然语言声明。

自然语言声明不能单独证明强制项通过。

---

## 2. 每个 Gate 必须提交的验收包

每个 Gate 结束时必须生成：

```text
acceptance/<gate-id>/
  summary.md
  changed-files.txt
  test-results.txt
  fault-injection-results.txt
  security-results.txt
  migration-results.txt
  rollback-proof.md
  known-risks.md
  review-verdict.md
```

不适用的文件仍需存在，并写明 `not_applicable` 和理由。

`summary.md` 必须包含：

```text
Gate:
Revision:
Config generation:
Environment:
Acceptance result:
Mandatory criteria passed/total:
Open Critical/High/Medium/Low:
Rollback tested:
Reviewer:
Manager closeout:
```

---

## 3. 全局基线标准

这些条件适用于每一个 Gate。

### AC-GLOBAL-01：工作区保护

**PASS：**

- 实施前记录 `git status --short`；
- 用户原有未提交改动被单独列出；
- 没有覆盖、重置、格式化或提交无关改动；
- changed-files 只包含审批范围。

**FAIL：** 任何用户改动丢失或被混入提交。

### AC-GLOBAL-02：回归测试

**PASS：**

```bash
python3 -m compileall -q src tests
python3 -m pytest
python3 -m pip check
git diff --check
```

全部返回 0。全量 pytest 不得少于实施前基线测试数，除非删除测试经过单独批准并有等价替代。

### AC-GLOBAL-03：新增行为测试

每个缺陷至少包含：

1. 修复前可失败的回归测试；
2. 最小实现；
3. 修复后通过；
4. 相邻边界负向测试。

### AC-GLOBAL-04：静态与供应链检查

目标 Gate 启用后必须通过：

- Ruff；
- Pyright 或 mypy 已纳入范围的模块；
- secret scan；
- `pip-audit`；
- Node 模块存在时运行 `npm audit`；
- 无新增未批准依赖。

### AC-GLOBAL-05：未解决风险

**PASS：**

- Critical：0；
- High：0；
- Medium：必须有 owner、期限、影响和缓解措施；
- Conditional Pass 只能包含 Low 或明确不影响当前 Gate 的 Medium。

### AC-GLOBAL-06：可回滚

**PASS：**

- 写明回滚命令和数据恢复步骤；
- 代码回滚已在测试环境验证；
- schema/config 变更有向前恢复方案；
- 凭据轮换不得以恢复旧凭据作为回滚。

### AC-GLOBAL-07：可观察

新增关键状态必须能通过 CLI/JSON 或审计事件查看，不能只存在于日志文本或 Prompt。

---

## 4. G-1 生产事实与治理基线验收

### AC-G-1-01：生产拓扑完整

**PASS：** 所有 EduFlow daemon、tmux pane 和主要 Agent 进程均能对应：

- PID；
- checkout 绝对路径；
- commit SHA；
- Python/CLI runtime；
-配置文件路径和 hash；
- state dir；
- Lark profile；
-启动入口。

抽查任意三个 live pane，记录值与系统进程事实一致。

### AC-G-1-02：数据真相清单完整

inbox、task、event、cursor、seen、runtime status、switch event、loop run、workflow asset、Skill asset、memory DB 均记录写入者、读取者、备份、权限和迁移要求。

### AC-G-1-03：旧计划完成度可追踪

每份旧计划标记 historical/active/superseded/observation-only；声称 DONE 的项目必须链接代码、commit 或测试证据。

### AC-G-1-04：信任模型获批

普通成员、operator、admin、manager、worker、reviewer、builder、runtime operator、recorder 的权限矩阵无空白项；每类凭据和工具都有最小权限说明。

### AC-G-1-05：SLO 和人工接管可执行

至少模拟一次：连续 runtime switch 失败或消息重试超限后进入 `human_takeover`，新自动动作停止，operator 能看到原因和恢复步骤。

### G-1 否决项

- 存在无法对应 checkout/revision 的生产进程；
- 不知道实际使用哪个 memory DB；
- control-plane owner 未指定；
- 凭据来源未知；
- 无人工接管路径。

---

## 5. G0 安全与可靠消息止血验收

### AC-G0-01：Slash RBAC

必须验证：

| 场景 | 期望 |
|---|---|
| 普通成员执行只读命令 | 按 allowlist 成功 |
| 普通成员执行 `/send` | 拒绝并审计 |
| 普通成员执行 `/stop`、`/clear` | 拒绝并审计 |
| sender_id 缺失 | 所有写命令 fail closed |
| operator 执行 `/send` | 成功，记录 actor |
| operator 执行 admin 命令 | 拒绝 |
| admin 执行受控命令 | 成功，记录 actor/target/result |
| allowlist 为空 | 写命令全部拒绝 |

**PASS：** 负向测试 100% 通过；不存在未登记的写命令 handler。

### AC-G0-02：消息 ACK

故障注入：

1. inbox 写权限错误；
2. 文件锁超时；
3. 飞书发送暂时失败；
4. 进程在 persist 后、ACK 前崩溃；
5. 重启后 replay 同一事件。

**PASS：**

- retryable failure 不推进 cursor/seen；
- 恢复后最终只产生一条 canonical inbox/message；
- terminal drop 正常推进；
- 超限进入 dead-letter；
- dead-letter 可查询、可重放、可审计。

### AC-G0-03：凭据

**代码准备 PASS：**

- repo 只保留无真实值的 example config；
- secret scan 无有效凭据；
- config 权限不安全时启动拒绝或强告警；
-日志、异常、卡片和证据包不出现 secret。

**生产轮换 PASS：** 所有进入过 Git、日志或 state 的 token/secret 已轮换，并验证旧值失效。生产轮换必须独立批准。

### AC-G0-04：加密 fail closed

**PASS：**

- 无 `cryptography` 时敏感存储拒绝启动/写入；
-不存在 XOR fallback；
-密文、nonce 或 tag 任意一项被修改时解密失败；
-错误不会回显 plaintext、key 或完整密文；
-现有数据迁移前有备份和可解性报告。

### AC-G0-05：Inbox supersession

**PASS：**

- 两条不同 task_id 的高优消息互不影响；
- 同一 task 的新 revision 只能显式 supersede 旧 revision；
- superseded 与 read/acknowledged 分开；
-不存在基于 agent 名、`batch 6` 等模糊文本的批量已读。

### G0 否决项

- 任意非授权成员能执行写命令；
- 任意 retryable delivery failure 被永久 ACK；
- 仍有有效 secret 被 Git 跟踪；
- 加密可静默降级；
- 无 task_id 的消息能自动吞掉其他任务。

---

## 6. G1 Runtime、敏感数据、身份权限与 Skills 验收

### AC-G1-R1：Runtime Truth

对每个支持的 runtime 验证：

```text
process_present
cli_ready
environment_match
provider_reachable
inbox_probe_consumed
```

**PASS：**

- `proved_ready` 只在 required stages 全部通过时出现；
- `skipped` 输出 `ready_unproven`；
- unread probe 不得标 consumed；
- cache 超过 TTL 失效；
- pane 中出现 auth/provider error 时不标 clean；
- JSON verdict 与 live pane 抽查一致。

### AC-G1-R2：Switch 串行化

同时触发 manual 和 watchdog switch 100 次并发测试。

**PASS：**

- 每个 Agent 同时最多一个 active switch；
- 无 JSONL 截断或覆盖；
- 每个 start 有唯一 completed/failed；
-旧 generation 不能覆盖新状态；
-最终 runtime status、event、live pane 一致。

### AC-G1-R3：Inbox reconciliation

旧 unread、旧 verdict 与新 task 状态冲突时进入 reconciliation queue；不得静默已读，不得长期作为 live blocker。reconcile 必须记录 actor、依据和前后状态。

### AC-G1-D1：DEK/KEK 生命周期

**PASS：**

- 100 条测试密文经密码变更后全部可解；
- recovery key 恢复后全部可解；
-旧密码失效；
- recovery key 只展示一次；
-安全问题恢复路径已删除或永久禁用；
-迁移中断后可以恢复旧数据，不出现部分不可解。

### AC-G1-D2：干净安装

在无其他 editable workspace 的全新环境执行：

```bash
python3 -m venv <temp>
pip install .
eduflow version
eduflow health --json
python3 -m pytest <clean-install-smoke>
docker build --no-cache .
```

**PASS：** 无隐式 `flow-memory` 路径依赖；CLI、memory 初始化和基础 router import 成功；依赖版本可追踪。

### AC-G1-I1：Identity/Role/Authority

**PASS：**

- 每个 Agent 有 identity version、role、authority profile、capability pack；
- worker 不能 CLOSEOUT；
- producer 不能正式 REVIEW 自己产物；
- runtime operator 不能改业务 verdict；
- recorder 不能派工；
- manager 不拥有生产 artifact write assignment；
-权限拒绝由代码产生，不依赖 Prompt 自觉。

### AC-G1-S1：Skills Capability Registry

**PASS：**

- production Skill 100% 登记 id/version/owner/status/risk/allowed_roles；
- reference Skill 不会作为执行 Skill 自动触发；
- deprecated Skill 有替代项和到期日；
-同名项目级/用户级 Skill 不会静默覆盖；
-每个 Role 有 required/optional/forbidden Skill Pack；
- Agent runtime status 可显示实际加载的 Skill 版本。

### G1 否决项

- cached/skip 仍能得到 proved-ready；
-并发切换造成状态与 pane 不一致；
-密码变更或恢复后旧密文不可解；
- clean install 依赖开发机其他 workspace；
-正式权限只存在于 Prompt；
- production Skill 未登记仍可使用。

---

## 7. G2 Agent Loop 验收

### AC-G2-01：生命周期

每个 Run 可查询 PID/runner/lease/heartbeat/start/end/exit code。必须验证 start、cancel、resume、进程崩溃、daemon 重启和 reconcile。

**PASS：** 不存在永久 `running` 的死进程；重复 start 不产生两个 active run。

### AC-G2-02：Stop Rules

场景必须覆盖：

- 失败测试从 20 降到 1；
-旧失败修好后暴露新失败；
-相同失败且无相关 diff 连续出现；
-已通过测试重新失败；
-flaky result；
-checker infrastructure failure。

**PASS：** 分别得到 progressing、newly_exposed、stalled、regression、flaky、infrastructure，而不是统一 `no_failure_reduction`。

### AC-G2-03：Cycle Evidence

每轮证据必须包含 spec version/hash、base/head commit、dirty hash、actor、duration、exit code、测试统计、真实 diff 和脱敏 checker output。

随机抽取一个 cycle，在同 revision/依赖环境可复现 checker 结果。

### AC-G2-04：预算

超过 max cycles/time/diff/concurrency 后进入 `human_review_required`，不继续自动运行。

### AC-G2-05：权限真相

Agent Loop passed 后 task 不得自动变 delivered/approved/closed；现有 truth-contract tests 必须保留。

---

## 8. G3 Workflow 团队 Loop 验收

### AC-G3-01：Definition 版本

每个 active Workflow 有 id/version/hash；实例创建后修改 Definition 不改变旧实例解释。新版本产生新 hash/version。

### AC-G3-02：Instance 生命周期

必须完整演示：

```text
start
-> role binding
-> dispatch
-> worker execution
-> handoff ACK
-> evidence submit
-> worker_review REVIEW reject
-> repair
-> REVIEW approve
-> manager CLOSEOUT
```

每一步都有事件、actor、timestamp、前置 Gate 和 next owner。

### AC-G3-03：职责分离

系统必须拒绝：

- producer 与 reviewer 同一 Agent；
- worker 发 CLOSEOUT；
- manager 无 REVIEW 证据直接 closeout；
- reviewer 修改产物后直接批准；
- runtime operator 被绑定为业务 reviewer。

### AC-G3-04：Handoff ACK

handoff 未持久化或未 ACK 时 Workflow 不得进入 started/completed；超时进入 escalation，不得假装继续。

### AC-G3-05：Gate

缺 required input/output/evidence 时 transition 被拒；拒绝结果包含缺失项、required next owner 和 safe next action。

### AC-G3-06：兼容视图

旧 task-level `team_loop_account` 与 Workflow Instance 不一致时必须显示 derived drift，不能覆盖实例真相。

### G3 否决项

- Workflow 仍只保存一个 `workflow_id`；
-没有 Instance/Step/Gate/event；
-通过群聊文字即可跨阶段；
- REVIEW/CLOSEOUT 权限可绕过；
-旧实例被新 Definition 静默改变。

---

## 9. G4 SQLite 双写、对账与切换验收

### AC-G4-01：迁移前备份

JSON/JSONL/SQLite/state dir 完整备份；记录 checksum；执行恢复演练并验证关键记录数。

### AC-G4-02：双写一致性

至少连续运行一个批准的稳定窗口。要求：

- idempotency key 一致；
- row/event count 一致；
-状态字段一致；
-零未解释差异；
-对账任务失败会阻止切换。

### AC-G4-03：故障注入

覆盖消息、task、workflow、loop、runtime 在事务中断时的恢复。重复 replay 不得产生重复业务事件。

### AC-G4-04：切换

切换前后使用同一验收数据集比较 read model，结果一致。切换后 JSON 只读，任何新写入测试必须失败或被明确拒绝。

### AC-G4-05：回滚窗口

在批准的回滚窗口内验证 SQLite 读取失败时可恢复服务；不得恢复到产生数据分叉的旧写路径。

### G4 否决项

- 双写差异不为零；
-缺少备份恢复演练；
-无幂等键；
-切换后仍存在两个可写真相源；
-迁移失败会丢失 REVIEW/CLOSEOUT 或 message ACK。

---

## 10. G5 Evolution Loop 验收

### AC-G5-01：Candidate 质量

每个 candidate 有 supporting runs、failure pattern、root cause class、repair outcome、scope、recommended surface、counterexample 和 expiry。

### AC-G5-02：人工 Gate

运行证据不能自动修改正式 Skill、Workflow、Role、Authority 或 Memory。promotion 必须有 reviewer/manager 审批事件。

### AC-G5-03：效果比较

选取至少一个更新，在后续 Workflow Instance 比较：review iteration、repair cycle、duration、failure rate、人工介入。没有基线或采用数据时不得声称改进有效。

### AC-G5-04：可撤销

更新造成回归时可以回退 Skill/Workflow/Spec 版本，旧 Instance 仍可按原版本解释。

---

## 11. G6 定时任务验收

### AC-G6-01：Workflow Instance 复用

每个定时 occurrence 必须创建或绑定一个版本化 Workflow Instance，并记录 schedule id、occurrence id、definition version/hash 和 correlation id。不得创建第二套业务状态机。

### AC-G6-02：Authority 与审批

定时触发不得绕过 task、RBAC、required Workflow Gate、manager approval、正式 REVIEW 或 CLOSEOUT。未知 actor、缺失 owner 或失效 Authority 必须 fail closed 并审计。

### AC-G6-03：时区与 DST

必须覆盖时区、夏令时跳变、重复本地时间和不存在的本地时间；每个逻辑 occurrence 最多执行一次，所有计算结果可通过 CLI/JSON 解释。

### AC-G6-04：幂等与重复触发

相同 schedule/occurrence 的重复事件、daemon replay 或手工 retry 必须复用同一幂等键，不得创建重复 Workflow Instance 或重复外部副作用。

### AC-G6-05：重叠与背压

每个 schedule 必须显式声明 overlap policy 与 backpressure budget。达到并发、队列长度或延迟预算时进入 queued、skipped-with-reason 或 human_review_required，不得无界派发。

### AC-G6-06：失败、取消与恢复

必须验证失败重试、cancel、daemon 崩溃和重启恢复。retryable failure 不得伪装为成功；恢复后不得丢失 occurrence、Workflow Instance 绑定或审计链。

### AC-G6-07：历史保留与可观察

历史记录必须包含 planned_at、fired_at、started_at、completed_at、result、attempts、actor 和关联 Workflow Instance，并具有明确 retention policy；当前和历史状态可由 CLI/JSON 查询。

### AC-G6-08：安全副作用

定时任务引发的外部发送、生产写入和高风险工具调用必须复用对应 Capability/Authority 检查及 checkpoint；凭据不得进入 schedule definition、日志或验收证据。

### G6 否决项

- 定时任务拥有独立于 Workflow Instance 的第二套业务状态机；
- 重复触发能产生重复正式副作用；
- scheduler 可以绕过 RBAC、REVIEW、CLOSEOUT 或生产 checkpoint；
- daemon 重启后 occurrence 丢失、重复执行或无法对账；
- overlap/backpressure 未定义或可以无界增长。

---

## 12. G7 清理与复杂度验收

### AC-G7-01：行为不变

拆分前有 characterization tests；拆分后公共 API、task/event schema 和用户可见输出保持一致，除非另有批准。

### AC-G7-02：单一实现

Memory/Cards 清理前完成调用矩阵和迁移；删除旧实现后全仓无生产引用，deprecated compatibility ledger 已关闭。

### AC-G7-03：巨石拆分质量

不是以文件行数下降作为唯一标准。拆分后必须：

-领域决策与 IO 分离；
-依赖方向单向；
-循环依赖为零；
-测试可独立覆盖；
-没有新增无意义抽象或依赖。

### AC-G7-04：冗余删除

删除项必须附引用扫描、运行测试和回滚说明；不能因“看起来没用”直接删除历史兼容或业务数据。

---

## 13. 最终系统验收

只有以下全部通过，整体升级才可最终 CLOSEOUT：

1. 任意正式动作可追踪到 Identity、Role、Authority、Assignment 和 actor。
2. 任意消息可从 Feishu event 追踪到 persist、ACK、task/workflow 和可见回复。
3. 未授权控制操作 100% 被拒绝并审计。
4. Runtime verdict 与 live pane/provider/inbox 事实一致。
5. Agent Loop 可观察、取消、恢复、对账，且不能越过 REVIEW/CLOSEOUT。
6. Workflow Instance 能完成真实 reject→repair→approve→closeout 团队 Loop。
7. SQLite 是唯一可写业务真相，旧存储处于只读或归档状态。
8. Skills、Workflow、Identity、Authority 和 Loop Spec 均有版本和 owner。
9. Evolution 更新具有采用记录和效果比较。
10. clean install、clean Docker build、全量测试、故障注入和安全扫描全部通过。
11. Critical/High 风险为零。
12. rollback、human takeover 和 disaster recovery 均完成演练。

---

## 14. 审批页

```text
Acceptance Standard Version: 1.0.0
Approved Scope: G-1, G0, G1, G2, G3, G4, G5, G6, G7; strictly dependency ordered
Excluded Scope: sibling flow-memory writes without a separate checkpoint; external sends; production credential rotation; Git history rewrite; production read-source switch; irreversible production migration without per-action approval
Required Gates: G-1 -> G0 -> G1 -> G2 -> G3 -> G4 -> G5 -> G6 -> G7
Conditional Pass Allowed: yes, only under section 1.1; never for security or data-integrity failures
Security Owner: Project Owner (user)
Control-plane Owner: Project Owner (user)
Workflow Reviewer: worker_review
Manager Approval: Project Owner approved contract-first execution in the Codex goal thread; manager remains the only system CLOSEOUT owner
Approved At: 2026-07-12 Asia/Shanghai
```

本页未填写前，本标准视为草案，实施计划不得进入执行状态。
