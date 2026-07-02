---
title: ECC 对 EduFlow 的缺失能力补全分析
date: 2026-07-01
status: draft
tags:
  - EduFlow
  - ECC
  - capability-registry
  - skill-governance
  - company-agent-workforce
---

# ECC 对 EduFlow 的缺失能力补全分析

## 一句话判断

`affaan-m/ECC` 不是单个 Skill，也不是普通 skill 集合。更准确地说，它是一个 **agent harness 能力操作系统**：把 rules、skills、agents、hooks、MCP、安装 profile、安装状态、doctor/repair、安全扫描、持续学习和跨 harness 分发，组织成一个可选择、可审计、可维护的能力面。

对 EduFlow 来说，ECC 最值得借鉴的不是“它有很多 skill”，而是它回答了一个 EduFlow 下一阶段一定会遇到的问题：

**公司 AI 员工的能力到底怎么装、怎么选、怎么升级、怎么审计、怎么避免越装越乱？**

## ECC 补的是哪一层

前面几个项目主要补的是：

| 项目 | 补 EduFlow 的哪一层 |
| --- | --- |
| `claude-squad` | 多 session 操盘与 worktree 现场 |
| `agent-orchestrator` | 外部反馈、durable facts、事件回流 |
| `container-use` | 隔离执行环境与 command log |
| `oh-my-claudecode` | 编排流程、verify/fix、模型分层、handoff |
| `ECC` | 能力目录、选择安装、规则/skill 治理、持续学习、安全审计、跨 CLI 分发 |

所以 ECC 应该补进 EduFlow 的“员工能力供应链”层，而不是当作另一个竞品 UI。

## EduFlow 当前缺口

### 1. 员工能力还缺少可安装单位

EduFlow 已经有员工角色、workflow、skill、飞书展示和 runtime 线索，但还缺一个更明确的能力单位：

```text
capability_unit:
  type: rule | skill | workflow | mcp | cli_script | employee_pack
  owner:
  target_cli:
  target_role:
  permissions:
  install_profile:
  version:
  evidence_contract:
  health_status:
```

没有这个单位，后续会出现三个问题：

- 不知道某个员工“装了什么能力”。
- 不知道某个 workflow 依赖哪些 skill/rule/MCP。
- 不知道升级、卸载、迁移时哪些文件是 EduFlow 管的，哪些是用户自己写的。

ECC 的 selective install 和 install-state 正好补这个契约。

### 2. 缺少选择安装和能力画像绑定

EduFlow 不应该让每个员工都装全量能力。公司智能体员工应该像岗位配权限一样安装能力：

| EduFlow 角色 | 应安装的能力 profile |
| --- | --- |
| `manager` | planning、routing、risk escalation、Feishu status、workflow promotion |
| `worker_builder` | code execution、test、container/worktree、artifact evidence、security scan |
| `worker_research` | source collection、citation、knowledge synthesis、claim verification |
| `worker_ops` | Feishu/Lark、CRM、approval、calendar、sheet、external feedback |
| `reviewer` | quality gate、rubric、regression check、evidence freshness |

ECC 的 `minimal/core/full` profile、`install-plan`、`doctor`、`repair` 说明：能力安装应该是一个可预览、可回滚、可修复的生命周期，而不是复制一堆 markdown 文件。

### 3. skill、workflow、rule 的边界需要更硬

ECC 的 capability surface selection 给 EduFlow 一个很有用的判断顺序：

| 能力形态 | EduFlow 里的含义 | 适合放什么 |
| --- | --- | --- |
| `rule` | 总是生效的岗位/路径/安全约束 | 飞书可见性、证据必填、权限底线、敏感信息禁止外发 |
| `skill` | 单员工按需加载的工作方法 | 题库清洗、文章生成、QA review、客户跟进 |
| `workflow` | 多员工固定协作链路 | realrun-to-workflow 后沉淀的重复工作高速通道 |
| `MCP` | 多 CLI/多员工复用的结构化工具接口 | 飞书、GitHub、CRM、知识库、审批 |
| `CLI/script` | 一次性或确定性本地动作 | 校验、转换、导入、状态扫描 |
| `employee_pack` | 岗位能力包 | 一个角色默认拥有的一组 rule/skill/workflow/MCP |

这能防止 EduFlow 把所有东西都塞进 skill，也能防止 workflow 变成超大 SOP 文档。

### 4. 缺少能力健康审计

EduFlow 需要类似 ECC 的 `doctor/repair/list-installed/security-scan` 思路：

```text
eduflow capability list
eduflow capability plan --role worker_builder --profile code-production
eduflow capability apply --dry-run
eduflow capability doctor
eduflow capability repair
eduflow capability uninstall --owned-only
eduflow security-scan --capabilities
```

这层的价值不是炫技，而是防止团队越来越大以后出现：

- 重复 skill。
- 旧 skill 仍被调用。
- 某员工缺关键工具权限。
- 某 workflow 依赖不存在。
- 某 MCP 或 hook 权限过大。
- 外部下载的 skill/rule 来源不可信。

### 5. 缺少持续学习到能力晋升的治理链

EduFlow 已经有 `realrun-to-workflow`，这非常接近 ECC 的 continuous learning 方向。但 EduFlow 现在还需要把“重复工作沉淀”拆成更清晰的晋升链：

```text
run evidence
→ case note
→ instinct / heuristic
→ skill candidate
→ skill
→ workflow candidate
→ workflow
→ employee_pack
```

其中：

- `case note` 保存一次性经验。
- `instinct` 保存高频判断规则，但还不直接自动执行。
- `skill candidate` 需要人工或 reviewer 审核。
- `workflow candidate` 需要跑过真实任务验证。
- `employee_pack` 是岗位级默认能力组合。

这能让 EduFlow 的 workflow 不只是“重复工作项目组”，而是公司 AI 员工的能力进化系统。

## 建议加入 EduFlow 的 ECC 借鉴模块

### A. Capability Registry

新增能力注册表，统一登记 rule、skill、workflow、MCP、script、employee pack。

建议路径：

```text
.eduflow-team-state/capabilities/
  registry.json
  install-state.json
  profiles/
  packs/
  audits/
```

最小字段：

```yaml
id:
type:
title:
owner:
version:
target_roles:
target_cli:
requires:
permissions:
source:
install_state:
health:
last_used_at:
```

### B. Employee Pack

把“给团队某个角色装什么”从口头建议变成可执行包：

```yaml
employee_pack: worker_builder.code-production
rules:
  - evidence-required
  - no-destructive-command-without-approval
skills:
  - repo-analysis
  - test-driven-development
  - workflow-candidate-capture
workflows:
  - realrun-to-workflow
mcp:
  - github
  - feishu-doc
environment_policy:
  default: git_worktree
  high_risk: container_use
```

### C. Capability Doctor

飞书里可以显示每个员工的能力健康：

```text
employee: worker_builder_01
capability_health: warning
missing:
  - security-scan
stale:
  - old-import-skill
overlap:
  - two similar article-writing skills
external_risk:
  - unverified third-party prompt pack
```

### D. Security / Supply Chain Scan

ECC 的 AgentShield 思路对 EduFlow 很重要，因为 EduFlow 未来会安装很多 skill、workflow、MCP 和外部连接。

EduFlow 至少应扫描：

- skill 里是否要求外发 secret。
- MCP 是否请求过大权限。
- hook 是否能静默执行危险命令。
- workflow 是否绕过 evidence gate。
- employee pack 是否给了超岗位权限。
- 外部来源是否记录 source/provenance。

### E. Consult / Recommend

ECC 有“我不确定该装哪个 profile 时先 consult”的思想。EduFlow 可以做成：

```text
eduflow recommend "每周自动汇总销售线索并发飞书"
```

输出：

```text
recommended_employee_pack: worker_ops.crm-weekly
recommended_workflow: weekly-lead-summary
required_mcp: lark-sheets, lark-im, crm
required_rules: pii-redaction, evidence-required
environment_policy: shared
reviewer: worker_reviewer_ops
```

这会让 EduFlow 从“会运行任务”升级成“能推荐公司应该调用哪条 AI 员工高速路”。

## 对现有四个 EduFlow 原生 skill 的修正

前面拆 4 个原生 skill 时，应该把 ECC 这一层补进去：

| 原生 skill | 装给谁 | ECC 补强点 |
| --- | --- | --- |
| `employee-status-to-feishu` | `manager`、`ops` | 展示员工能力 profile、安装健康、缺失权限 |
| `realrun-to-workflow` | `manager`、`worker_builder`、`reviewer` | 从 run evidence 晋升到 skill/workflow/pack 的治理链 |
| `workflow-route-jump` | `manager`、`ops` | 路由前先检查 capability dependency 是否满足 |
| `capability-pack-doctor` | `manager`、`worker_builder`、`reviewer` | 新增，负责 list/plan/doctor/repair/security-scan |

也就是说，原来第四个如果只是“某个业务 skill”，现在应调整成更底层的：

**`capability-pack-doctor`：公司 AI 员工能力包体检与修复 skill。**

## 落地优先级

### P0：先做文档契约

- 定义 `capability_unit` schema。
- 定义 `employee_pack` schema。
- 定义 skill / workflow / rule / MCP / script 的边界。
- 定义安装状态与 owned-only 卸载原则。

### P1：接到飞书展示

- 员工状态卡增加 `capability_profile`。
- 员工状态卡增加 `capability_health`。
- workflow 卡增加 `missing_dependencies`。
- manager 卡增加 `recommended_pack`。

### P2：接入 realrun-to-workflow

- 每次 workflow candidate 生成时，同时输出 capability dependencies。
- 晋升 workflow 前检查依赖是否可安装、可审计、可回滚。
- 成熟 workflow 可被打包进 employee pack。

### P3：能力治理命令

- `capability list`
- `capability plan`
- `capability apply --dry-run`
- `capability doctor`
- `capability repair`
- `capability security-scan`

## 最终结论

ECC 对 EduFlow 的最大启发是：

**AI 员工不是只要会执行任务，还要有一套可治理的能力供应链。**

EduFlow 现在已经有“飞书可见的员工”“workflow 快速通道”“多 CLI 底座”的产品方向。下一步如果吸收 ECC，就应该把这些能力变成：

- 可选择安装的 employee pack。
- 可审计的 capability registry。
- 可修复的 install-state。
- 可晋升的 continuous learning。
- 可控权限的 security scan。

这样 EduFlow 才能从“能跑任务的团队系统”，升级成“公司 AI 员工的能力操作系统”。
