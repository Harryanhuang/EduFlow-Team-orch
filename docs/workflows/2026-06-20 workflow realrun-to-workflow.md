# workflow: realrun-to-workflow

## 基础信息

- `workflow_id`: `realrun-to-workflow`
- `workflow_name`: 真实运行经验沉淀为 workflow
- `status`: active
- `owner`: `worker_builder`
- `initiator`: `manager`
- `participants`: `manager`, `worker_builder`; 必要时 `review_course`, `worker_qbank`, `auto_ops` 提供证据
- `handoff_chain`: `manager -> worker_builder -> manager`

## when_to_use

用于真实运行中某条链路已经跑出稳定经验，或者反复暴露同类问题，需要从 case note / gap note 升级成可复用 workflow 资产。

这条 workflow 的核心判断是：

> 不是每个事故都要变成 workflow，但反复出现、会影响协作边界、能被 manager 调用的链路，必须沉淀。

## trigger_examples

```text
调用 workflow: realrun-to-workflow
对象: Accounting 0452 final review + Physics 0625 launch
范围: 把真实运行经验沉成 workflow registry v1
边界: 不写成普通总结，必须产出可调用字段、门禁、禁止动作和维护规则
```

## in_scope

- 从真实运行样本提取稳定链路。
- 从 gap note 提取门禁和异常分支。
- 把经验写成 manager 可调用 workflow。
- 给 builder 后续维护动作。
- 更新 registry 的 status / last_validated_run / next_builder_action。

## out_of_scope

- 不重写 agent 身份。
- 不做自动执行引擎。
- 不把一次偶发事件强行升级成 workflow。
- 不把所有 gap 都写成 active workflow。
- 不替代代码层 bugfix。

## required_inputs

- 真实运行样本或 gap note。
- 当前 workflow registry。
- 相关产物路径或消息证据。
- manager 希望复用的场景。

## expected_outputs

worker_builder 应交：

- workflow 说明书。
- manager trigger examples。
- handoff chain。
- acceptance gates。
- forbidden moves。
- reassurance policy。
- done definition。
- common failure modes。
- registry 更新建议。

manager 应交：

- 是否接纳为 active workflow。
- 是否放入 backlog。
- 是否只保留为 case note。

## acceptance_gates

- `dispatch_acceptance_gate`: builder 必须明确接到沉淀任务。
- `file_evidence_gate`: workflow 必须引用真实样本、产物或 gap，不接受纯抽象设想。
- `quality_gate`: 如果 workflow 解决的是质量门禁，必须写出阻断条件。
- `runtime_reality`: 如果涉及运行态恢复，必须写明不能只看 runtime status。
- `stale_state_reconciliation`: 必须说明旧消息、旧 task、旧 verdict 如何不污染新流程。

## forbidden_moves

- 只写“经验总结”，没有 workflow_id / trigger / gates / done definition。
- 把 manager 的一次临场话术当成 workflow。
- 忽略失败样本，只沉淀看起来顺的链路。
- 让 auto_ops 成为 workflow owner。
- 把 workflow 写成 Claude Code 内部 subagent 编排。

## reassurance_policy

- worker_builder 可以外显“开始沉淀 workflow”和“已交 manager 审阅”。
- worker_builder 不替 manager 宣布 workflow 正式 active。
- manager 才能正式宣布纳入 registry。

## builder_followup

builder 在每次沉淀后必须判断：

- 这条 workflow 是否已被真实运行验证。
- 是否要更新 lifecycle status。
- 是否要新增 intake rule。
- 是否要把固定动作反哺给 agent identity / skill / template。

## done_definition

满足以下条件才算完成：

- workflow spec 已完成。
- registry 已给出 status 和 owner。
- manager 能用统一调用口径触发它。
- 至少一个真实案例能回测。
- 已明确哪些问题仍留在 backlog。

## common_failure_modes

- builder 只写“复盘”，不写可调用协议。
- manager 不知道什么时候调用。
- workflow 没有 gate，跑起来还是靠人工盯。
- workflow 写得过细，变成一次性 prompt。
- workflow 没有 lifecycle，过几天就过期。

