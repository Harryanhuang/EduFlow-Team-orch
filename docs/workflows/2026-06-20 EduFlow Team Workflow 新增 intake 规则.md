# 2026-06-20 EduFlow Team Workflow 新增 intake 规则

## 目标

这份规则解决工作过程中不断出现新需求时，workflow 库如何增长的问题。

第一原则：

> 不是什么都要新建 workflow。只有能被 manager 反复调用、能约束多 agent 协作、能沉淀 gate 的链路，才值得进入 registry。

## intake 判断

manager 或 worker_builder 发现新流程需求时，按下面顺序判断。

### 1. 是已有 workflow 的普通样本吗？

如果只是同一 workflow 下的新学科、新 topic、新文件，不新增 workflow。

处理方式：

- 更新 `last_validated_run`。
- 记录新的 common failure mode。
- 必要时补 trigger example。

### 2. 是已有 workflow 的变体吗？

如果 handoff chain 相同，但 gate 或 forbidden move 有变化，优先作为变体处理。

处理方式：

- 不新增 workflow_id。
- 在原 workflow 中补 variation note。
- 观察是否连续出现。

### 3. 是新的 workflow 候选吗？

满足以下条件，才进入 backlog：

- manager 可以用一句 `调用 workflow: <id>` 触发。
- 至少涉及两个 agent 的协作边界。
- 有明确 done definition。
- 有至少一个真实样本或强烈待验证样本。
- 不能被现有 workflow 合理覆盖。

### 4. 什么时候升为 active？

满足以下条件，才能从 backlog / draft 升为 active：

- 真实运行至少跑通一次。
- 关键 gates 被验证。
- forbidden moves 清楚。
- manager 调用口径清楚。
- builder 能维护它。

## 新 workflow 最小模板

新增 workflow 草案必须先写这些字段：

- `workflow_id`
- `workflow_name`
- `status`
- `owner`
- `when_to_use`
- `primary_chain`
- `required_inputs`
- `expected_outputs`
- `acceptance_gates`
- `forbidden_moves`
- `done_definition`
- `common_failure_modes`

## 命名规则

- 使用稳定英文 slug。
- 采用动词或场景组合。
- 不使用 agent 名字作为 workflow_id。
- 不使用一次性任务名。

推荐格式：

```text
<domain>-<stage>-<action>
```

例子：

- `igcse-subject-launch`
- `igcse-item-level-prototype`
- `runtime-recovery-and-resume`
- `quality-gate-intervention`

## 新增 workflow 的禁止动作

- 不因为一次临场 prompt 就新增 active workflow。
- 不把 case note 直接改名为 workflow。
- 不让 auto_ops 成为 owner。
- 不把 workflow 写成完整技术实现方案。
- 不绕开 manager 正式确认。

## builder intake 输出

worker_builder 每次处理 intake，应给 manager 一份短判断：

```text
候选 workflow: <id>
判断: existing_sample / variation / backlog_candidate / active_candidate
理由: <基于真实运行的证据>
建议动作: <更新现有 workflow / 进入 backlog / 升 active / 仅保留 case note>
```

