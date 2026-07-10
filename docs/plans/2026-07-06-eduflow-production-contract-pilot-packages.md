# EduFlow Production Contract Pilot Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Turn the 2026-07-06 production-agent architecture discussion into a small, testable EduFlow pilot around the course/qbank review-repair chain.

**Architecture:** Keep `flow task` as the source of truth. Add small read-only/read-model surfaces first, then wire the stable summaries into manager-facing output. Do not build a new workflow engine, do not expand the agent roster, and do not make low-risk tasks heavy.

**Tech Stack:** Python stdlib, existing `eduflow.store.tasks`, existing `local_facts`, existing loop/evidence/read-model surfaces, pytest, markdown docs/templates.

---

## Operating Rule For All Packages

Use the repo shim:

```bash
./scripts/eduflowteam ...
```

Run focused tests after each package. Do not start by running the full suite unless the package touches shared task/render surfaces.

Do not add dependencies. Do not change runtime credentials. Do not touch `.eduflow-team-state` fixtures except through tests with isolated `EDUFLOW_STATE_DIR`.

The pilot scope is:

```text
workflow: course/qbank review-repair chain
primary objects: Loop Contract, Tool Risk Matrix, Evolution Packet
runtime checks: delivery ack, agent productivity, source manifest/source risk
```

## Master Prompt For Claude

Use this when starting a fresh Claude window:

```text
你在 /Volumes/Halobster/Codex相关/EduFlow-Team-orch 工作。

任务：执行 docs/plans/2026-07-06-eduflow-production-contract-pilot-packages.md 中指定的单个 Package。

规则：
1. 先读 .claude/skills/skill-orchestration-guide.md，再按当前 Package 读取对应技能文件。
2. 只做当前指定 Package，不顺手做后续包。
3. 先读 README.md、相关现有代码、该 Package 的 Files/Steps。
4. 启动 Claude workflow：Plan -> Implement -> Verify -> Report。先列最小执行计划，再按测试驱动实现。
5. 保持最小 diff，不新增依赖，不重构无关模块。
6. 任何影响 task 状态、消息投递、review verdict 的改动必须有测试。
7. 如需要并行，用 Claude 原生 Agent Team / subagents 做只读侦察；子 Agent 不改文件，最多 3 个，结果汇总后由主线程实现。
8. 执行中遵守 Code beats prose：真实代码和测试优先于文档猜测。
9. 完成后给出：改动文件、运行过的测试、剩余风险、下一包建议。

当前要执行的 Package 是：<填 Package 编号和标题>。
```

## Claude Native Workflow Routing

Use this routing before every package so Claude enters the repo's native workflow instead of treating the package as a generic TODO.

**Always read first:**

```text
.claude/skills/skill-orchestration-guide.md
```

**Package-specific skills:**

```text
Package 0 baseline audit:
- .claude/skills/skill-orchestration-guide.md
- Optional Agent Team read-only lanes:
  1. map task/loop/evidence command surfaces
  2. map local_facts delivery/ack surfaces
  3. map manager-panel tests and output paths

Package 1 templates:
- .claude/skills/skill-orchestration-guide.md
- .claude/skills/workflow-recovery-patterns.md

Package 2 loop contract:
- .claude/skills/skill-orchestration-guide.md
- .claude/skills/multi-agent-collaboration.md
- .claude/skills/workflow-recovery-patterns.md
- Optional Agent Team read-only lanes:
  1. inspect task loop/evidence fields
  2. inspect local_facts delivery/ack fields
  3. inspect CLI/test patterns for task subcommands

Package 3 tool risk:
- .claude/skills/skill-orchestration-guide.md
- .claude/skills/manager-role-red-lines.md
- .claude/skills/provider-failover-protocol.md

Package 4 evolution packet:
- .claude/skills/skill-orchestration-guide.md
- .claude/skills/workflow-recovery-patterns.md
- .claude/skills/review-verdict.md
- .claude/skills/review-course-file-evidence-playbook.md

Package 5 readiness check:
- .claude/skills/skill-orchestration-guide.md
- .claude/skills/daemon-health-check.md
- .claude/skills/workflow-recovery-patterns.md
- Optional Agent Team read-only lanes:
  1. inspect delivery/ack evidence
  2. inspect heartbeat/productivity state
  3. inspect source/evidence/manifest state

Package 6 manager panel:
- .claude/skills/skill-orchestration-guide.md
- .claude/skills/manager-role-red-lines.md
- .claude/skills/multi-agent-collaboration.md

Package 7 pilot runbook:
- .claude/skills/skill-orchestration-guide.md
- .claude/skills/multi-agent-collaboration.md
- .claude/skills/workflow-recovery-patterns.md
- .claude/skills/review-course-file-evidence-playbook.md
- .claude/skills/qbank-lifecycle-gates.md
- .claude/skills/qbank-validation-patterns.md

Package 8 flow-memory bridge:
- Keep paused unless user explicitly authorizes memory writes.
- If authorized later, first re-run Package 4 tests and produce a separate approval checklist.
```

**Agent Team rule:** Use Agent Team only for independent, read-only reconnaissance or review. Do not let child agents edit files, change state, run destructive commands, or recursively spawn more agents. The main Claude window owns implementation, tests, and final judgment.

**Reusable read-only subagent prompt:**

```text
你是当前 Package 的只读侦察 Agent。
范围：<填一个窄范围，例如 local_facts delivery/ack surfaces>。
必须先读 .claude/skills/skill-orchestration-guide.md；如果范围涉及 manager/review/qbank/runtime，再读主线程指定的相关 skill。
只允许读取文件、搜索代码、总结现有行为。不要改文件，不要运行会改变状态的命令，不要提出超出当前 Package 的实现。
请返回：
1. 相关文件和函数/命令入口
2. 现有测试入口
3. 当前行为摘要
4. 对主线程实现的最小建议
```

## Package 0: Baseline Audit Only

**Purpose:** Let Claude refresh the current code surface before changing anything.

**Files:**
- Read: `README.md`
- Read: `docs/plans/2026-07-06-eduflow-production-contract-pilot-packages.md`
- Read: `src/eduflow/commands/task.py`
- Read: `src/eduflow/store/tasks.py`
- Read: `src/eduflow/store/local_facts.py`
- Read: `src/eduflow/store/task_evidence_account.py`
- Read: `tests/unit/test_commands_task.py`
- Read: `tests/unit/test_commands_messaging.py`

**Steps:**

1. Run a read-only status check:

   ```bash
   git status --short
   rg -n "loop-status|evidence-explain|manager-panel|delivery_state|ack_state|heartbeat" src/eduflow tests/unit
   ```

2. Produce a short baseline note in the final answer:

   ```text
   current surfaces found:
   - loop/evidence:
   - delivery/ack:
   - manager panel:
   - likely safe edit points:
   ```

3. Do not edit files in this package.

**Claude Prompt:**

```text
执行 Package 0: Baseline Audit Only。
只读检查，不改文件。目标是确认 loop/evidence/delivery/manager-panel 当前代码入口，并给出后续包的安全编辑点。
先读 .claude/skills/skill-orchestration-guide.md。
建议使用 Claude Agent Team 做最多 3 个只读侦察：task/loop/evidence、local_facts delivery/ack、manager-panel tests。子 Agent 不改文件，只汇报文件路径、函数名、测试入口。
```

## Package 1: Contract Templates

**Purpose:** Add stable markdown templates before code uses them.

**Files:**
- Create: `docs/templates/LOOP_CONTRACT_TEMPLATE.md`
- Create: `docs/templates/TOOL_RISK_MATRIX.md`
- Create: `docs/templates/EVOLUTION_PACKET_TEMPLATE.md`
- Modify: `docs/README_zh.md` only if there is already a templates index section; otherwise skip.

**Steps:**

1. Create `docs/templates/LOOP_CONTRACT_TEMPLATE.md` with these required fields:

   ```text
   task_id
   workflow_id
   current_phase
   owner
   iteration
   delivery_state
   inbox_local_id
   ack_required
   ack_deadline
   passed_checks
   failed_checks
   allowed_actions
   forbidden_actions
   next_required_output
   evidence_refs
   ```

2. Create `docs/templates/TOOL_RISK_MATRIX.md` with these levels:

   ```text
   Low: read-only
   Medium: local write
   High: coordination/runtime write
   Critical: destructive/external production
   ```

   It must explicitly classify:

   ```text
   send
   say --to user
   task dispatch
   task review
   reidentify
   fire/hire/reset/down
   rm -rf / delete / external deploy
   ```

3. Create `docs/templates/EVOLUTION_PACKET_TEMPLATE.md` with these fields:

   ```text
   source_task_id
   source_event
   trigger_reason
   content
   scope
   kind
   evidence_refs
   reuse_reason
   confidence
   recommended_action
   ```

4. Run:

   ```bash
   test -s docs/templates/LOOP_CONTRACT_TEMPLATE.md
   test -s docs/templates/TOOL_RISK_MATRIX.md
   test -s docs/templates/EVOLUTION_PACKET_TEMPLATE.md
   ```

**Claude Prompt:**

```text
执行 Package 1: Contract Templates。
只新增 docs/templates 下三个模板：LOOP_CONTRACT_TEMPLATE.md、TOOL_RISK_MATRIX.md、EVOLUTION_PACKET_TEMPLATE.md。
不要写代码，不要改 CLI。模板必须能被后续 Package 直接引用。
先读 .claude/skills/skill-orchestration-guide.md 和 .claude/skills/workflow-recovery-patterns.md。
用 Claude workflow 做一个短 checklist：模板字段是否覆盖 handoff、review reject、repair loop、manager correction、runtime incident。这个包通常不需要 Agent Team。
```

## Package 2: Loop Contract Read Model

**Purpose:** Add a read-only `task loop-contract <task_id> [--json]` surface that renders one actionable handoff packet from existing task/evidence/loop/delivery state.

**Files:**
- Create: `src/eduflow/store/task_loop_contract.py`
- Modify: `src/eduflow/commands/task.py`
- Test: `tests/unit/test_task_loop_contract.py`

**Behavior:**

`./scripts/eduflowteam task loop-contract T-1 --json` returns:

```json
{
  "task_id": "T-1",
  "workflow_id": "igcse-subject-launch",
  "current_phase": "review_repair",
  "owner": "worker_course",
  "iteration": 1,
  "delivery": {
    "state": "acknowledged",
    "inbox_local_id": "msg_...",
    "ack_required": true,
    "ack_state": "accepted_task"
  },
  "passed_checks": [],
  "failed_checks": [],
  "allowed_actions": [],
  "forbidden_actions": [],
  "next_required_output": "",
  "evidence_refs": []
}
```

Use existing fields. If a value is unknown, return an empty string/list, not invented text.

**Implementation Notes:**

- Source task from `tasks.get(task_id)` or the existing equivalent in `src/eduflow/store/tasks.py`.
- Source delivery from `local_facts.list_all_messages()` filtered by `task_id` when available, otherwise leave delivery fields empty.
- Source loop fields from existing task keys: `loop_status`, `loop_cycle_count`, `loop_recommended_action`, `loop_evidence_ref`.
- Source failed checks conservatively from `required_fix`, `blocking_files`, `review_reason`, `loop_stop_reason`.
- Do not mutate task state.

**Test cases:**

1. A flow task with `required_fix` renders failed checks.
2. A task with a related inbox message and ack renders delivery state.
3. Missing optional fields render as empty values.
4. CLI text output includes `task_id`, `current_phase`, `failed_checks`, and `next_required_output`.

**Commands:**

```bash
pytest tests/unit/test_task_loop_contract.py -q
pytest tests/unit/test_commands_task.py -q
```

**Claude Prompt:**

```text
执行 Package 2: Loop Contract Read Model。
目标：新增只读命令 `task loop-contract <task_id> [--json]`，从现有 task/local_facts/evidence 字段渲染 Loop Contract。
不要修改 task 状态，不要新增依赖，不要做自动派工。
先写 tests/unit/test_task_loop_contract.py，再实现最小代码。
先读 .claude/skills/skill-orchestration-guide.md、.claude/skills/multi-agent-collaboration.md、.claude/skills/workflow-recovery-patterns.md。
建议用 Claude Agent Team 做最多 3 个只读侦察：task loop/evidence 字段、local_facts delivery/ack 字段、task CLI/test 写法。主线程根据侦察结果实现。
```

## Package 3: Tool Risk Read Model

**Purpose:** Add a deterministic classifier for EduFlow command/tool risk. This is read-only; it does not block commands yet.

**Files:**
- Create: `src/eduflow/store/tool_risk.py`
- Modify: `src/eduflow/commands/task.py`
- Test: `tests/unit/test_tool_risk.py`

**Behavior:**

Add:

```bash
./scripts/eduflowteam task tool-risk --command "eduflow send worker_course manager 'x' 高" --json
```

Return:

```json
{
  "risk_level": "High",
  "access_mode": "auto_review",
  "reason": "coordination write: send",
  "requires_preflight": false,
  "requires_human_confirm": false
}
```

Rules:

```text
Low: status/read/list/grep/search/get/evidence-explain/loop-status
Medium: local file creation or non-critical local write
High: send, say --to user, task dispatch, task review, reidentify, runtime switch
Critical: reset, down, fire, rm -rf, delete state, external deploy, production write
```

**Test cases:**

1. `task evidence-explain T-1 --json` => Low.
2. `send worker_course manager ...` => High.
3. `say manager "..." --to user` => High.
4. `reset` / `down` / `fire worker_course` => Critical.
5. `rm -rf .eduflow-team-state` => Critical.

**Commands:**

```bash
pytest tests/unit/test_tool_risk.py -q
pytest tests/unit/test_commands_task.py -q
```

**Claude Prompt:**

```text
执行 Package 3: Tool Risk Read Model。
目标：新增只读风险分类器和 `task tool-risk --command "..."`
不要真正拦截命令，不要改 send/say/fire/reset 行为。只返回风险等级、建议访问模式和原因。
先写测试，再实现。
先读 .claude/skills/skill-orchestration-guide.md、.claude/skills/manager-role-red-lines.md、.claude/skills/provider-failover-protocol.md。
实现前先列出风险分类表和测试矩阵，确认 Low/Medium/High/Critical 都有覆盖。这个包默认 solo 执行即可。
```

## Package 4: Evolution Packet Read Model

**Purpose:** Generate memory/workflow/skill candidate packets from existing task signals, without writing memory yet.

**Files:**
- Create: `src/eduflow/store/evolution_packet.py`
- Modify: `src/eduflow/commands/task.py`
- Test: `tests/unit/test_evolution_packet.py`

**Behavior:**

Add:

```bash
./scripts/eduflowteam task evolution-packet <task_id> --json
```

Return empty candidate when no trigger is present:

```json
{"candidates": []}
```

Return a candidate only for these triggers:

```text
review verdict rejected
manager correction / manager_action
runtime incident / failed task
loop repair_cycle >= 2
```

Candidate shape:

```json
{
  "source_task_id": "T-1",
  "source_event": "review_rejected",
  "trigger_reason": "review rejected with required_fix",
  "content": "...",
  "scope": "workflow:igcse-subject-launch",
  "kind": "workflow_rule",
  "evidence_refs": ["task:T-1"],
  "reuse_reason": "...",
  "confidence": "medium",
  "recommended_action": "remember"
}
```

**Implementation Notes:**

- Do not call flow-memory in this package.
- Do not promote/reject memory.
- Keep content short and evidence-backed.
- If no evidence_refs can be produced, return no candidate.

**Test cases:**

1. Approved clean task returns `[]`.
2. Rejected task with `required_fix` returns one candidate.
3. Loop cycle count >= 2 returns one candidate.
4. Candidate includes `evidence_refs`.

**Commands:**

```bash
pytest tests/unit/test_evolution_packet.py -q
pytest tests/unit/test_commands_task.py -q
```

**Claude Prompt:**

```text
执行 Package 4: Evolution Packet Read Model。
目标：新增只读 `task evolution-packet <task_id> [--json]`，只在 review reject、manager_action、failed/runtime incident、repair>=2 时生成候选。
不要写 memory，不接 flow-memory，不自动改 workflow/skill。
先写测试，再实现。
先读 .claude/skills/skill-orchestration-guide.md、.claude/skills/workflow-recovery-patterns.md、.claude/skills/review-verdict.md、.claude/skills/review-course-file-evidence-playbook.md。
用 Claude workflow 明确一条红线：本包只生成候选，不写入 memory、不更新 skill、不自动推广经验。
```

## Package 5: Operational Readiness Check

**Purpose:** Combine the T-118 runtime lessons into a small read-only check before the pilot workflow is trusted.

**Files:**
- Create: `src/eduflow/store/operational_readiness.py`
- Modify: `src/eduflow/commands/task.py`
- Test: `tests/unit/test_operational_readiness.py`

**Behavior:**

Add:

```bash
./scripts/eduflowteam task readiness-check <task_id> --json
```

Return:

```json
{
  "task_id": "T-1",
  "delivery": {"status": "pass|warn|fail", "reason": "..."},
  "productivity": {"status": "pass|warn|fail", "reason": "..."},
  "source": {"status": "pass|warn|fail", "reason": "..."},
  "overall": "pass|warn|fail"
}
```

Rules:

- Delivery pass: recent related inbox row is acknowledged or no handoff required.
- Delivery warn: message is delivered but ack pending.
- Delivery fail: delivery_state indicates blocked/inject_failed/requires_polling for high-priority handoff.
- Productivity pass: assignee has recent heartbeat plus recent ack/log/task progress.
- Productivity warn: heartbeat exists but no recent progress signal.
- Productivity fail: no heartbeat/status or known runtime guard block.
- Source pass: task has `source_manifest` or evidence/source refs.
- Source warn: source risk unknown for curriculum/qbank tasks.
- Source fail: task explicitly has missing source/material evidence.

Keep thresholds simple and documented in code constants.

**Test cases:**

1. Acked message + heartbeat + evidence => pass.
2. Pending high-priority message => delivery warn.
3. No heartbeat => productivity fail.
4. Curriculum task without source evidence => source warn.

**Commands:**

```bash
pytest tests/unit/test_operational_readiness.py -q
pytest tests/unit/test_commands_task.py -q
```

**Claude Prompt:**

```text
执行 Package 5: Operational Readiness Check。
目标：新增只读 `task readiness-check <task_id> [--json]`，检查 delivery ack、agent productivity、source manifest/source risk。
不要自动修复，不发送消息，不 archive，不动 runtime。
先写测试，再实现。
先读 .claude/skills/skill-orchestration-guide.md、.claude/skills/daemon-health-check.md、.claude/skills/workflow-recovery-patterns.md。
建议用 Claude Agent Team 做最多 3 个只读侦察：delivery/ack、heartbeat/productivity、source/evidence/manifest。主线程负责合并成 readiness read model。
```

## Package 6: Manager Panel Minimal Surface

**Purpose:** Show the pilot signals where manager already looks, without making manager-panel slow.

**Files:**
- Modify: `src/eduflow/commands/task.py`
- Test: `tests/unit/test_commands_task.py`

**Behavior:**

In `task manager-panel`, for active workflow tasks, show one compact line when available:

```text
contract: phase=<phase> failed=<n> delivery=<pass|warn|fail> productivity=<pass|warn|fail> source=<pass|warn|fail>
```

Rules:

- Do not print full packets.
- Do not call slow verifier scripts.
- Use the read-model functions from Packages 2 and 5.
- If read-model raises, panel must still render and include a short warning.

**Test cases:**

1. Manager panel includes compact contract line for a task with loop contract/readiness data.
2. Manager panel still renders if readiness data is missing.
3. Existing manager-panel tests still pass.

**Commands:**

```bash
pytest tests/unit/test_commands_task.py -q
```

**Claude Prompt:**

```text
执行 Package 6: Manager Panel Minimal Surface。
目标：把 Loop Contract / readiness 的极简摘要放进 `task manager-panel`，只显示一行，不阻塞、不跑重检查。
不要重写 manager-panel，不改变现有 closeout 决策。
先补现有 manager-panel 测试，再最小实现。
先读 .claude/skills/skill-orchestration-guide.md、.claude/skills/manager-role-red-lines.md、.claude/skills/multi-agent-collaboration.md。
实现时保持 manager 只看摘要、不承担 worker/review 细节；manager-panel 报错必须降级为 warning，不影响原有面板渲染。
```

## Package 7: Real Pilot Runbook

**Purpose:** Define how to run 5-10 real course/qbank review-repair tasks and decide whether to continue.

**Files:**
- Create: `docs/workflows/_candidates/production-contract-pilot/README.md`
- Create: `docs/workflows/_candidates/production-contract-pilot/handoff-template.md`
- Create: `docs/workflows/_candidates/production-contract-pilot/acceptance-log.md`

**Runbook must include:**

```text
1. Choose a course/qbank task with review-repair risk.
2. Run task readiness-check.
3. Run task loop-contract.
4. Send repair handoff using Loop Contract fields.
5. After review, run evolution-packet.
6. Record whether manager was faster / worker less off-track / review more specific / closeout easier.
```

**Commands to include:**

```bash
./scripts/eduflowteam task readiness-check <T-id> --json
./scripts/eduflowteam task loop-contract <T-id> --json
./scripts/eduflowteam task evidence-explain <T-id> --json
./scripts/eduflowteam task evolution-packet <T-id> --json
./scripts/eduflowteam task manager-panel
```

**Claude Prompt:**

```text
执行 Package 7: Real Pilot Runbook。
目标：新增 docs/workflows/_candidates/production-contract-pilot/ 下的试点运行手册，不写代码。
手册必须告诉 manager 如何用 readiness-check、loop-contract、evidence-explain、evolution-packet 跑 5-10 个真实任务，并记录是否值得扩大。
先读 .claude/skills/skill-orchestration-guide.md、.claude/skills/multi-agent-collaboration.md、.claude/skills/workflow-recovery-patterns.md、.claude/skills/review-course-file-evidence-playbook.md、.claude/skills/qbank-lifecycle-gates.md、.claude/skills/qbank-validation-patterns.md。
用 Claude workflow 把 runbook 写成“manager 可执行清单”：选任务、检查 readiness、生成 contract、派 repair、review 后提 evolution packet、记录成败。这个包不需要改代码。
```

## Package 8: Optional Flow-Memory Bridge

**Purpose:** Only after Package 4 works, optionally send approved evolution packets into flow-memory candidates.

**Files:**
- Modify only after user approval.

**Default:** Do not implement in the first pass.

**Claude Prompt:**

```text
Package 8 暂停。不要实现 flow-memory 写入，除非用户明确授权。
当前只允许使用 `task evolution-packet` 生成候选文本，由人工决定是否进入 flow-memory。
如果未来授权实现，先读 .claude/skills/skill-orchestration-guide.md，并重新跑 Package 4 的测试；再单独写一份 memory 写入审批 checklist，不要直接写入。
```

## Suggested Execution Order

```text
Day 1:
Package 0
Package 1

Day 2:
Package 2
Package 3

Day 3:
Package 4
Package 5

Day 4:
Package 6
Package 7

After 5-10 real tasks:
Decide whether to wire Package 8 or expand to hiring/source-manifest/state-budget work.
```

## Stop Conditions

Stop and ask manager/user before continuing if:

- Implementing a package requires changing task transition semantics.
- A package would block existing `send`, `read`, `say`, `task review`, or `manager-panel`.
- Tests require live Feishu/Lark credentials.
- The change needs automatic deletion/archive of state files.
- A package wants to promote memory automatically.
