# 2026-06-20 EduFlow Team Workflow Registry v1 回测说明

## 目标

用昨天真实运行案例反查 Workflow Registry v1 是否真的能约束现场问题。

结论先写在前面：

> Registry v1 不能替代代码修复，但能把“哪些动作不能继续靠临场提醒”固定成 manager 可调用、builder 可维护、review/course/qbank 可执行的协作协议。

## Accounting 0452 closeout

对应 workflow：

- `igcse-subject-launch`
- `quality-gate-intervention` backlog

覆盖的问题：

- review_course 后期发现 7.5 真实 minor defect。
- 7.5 repair message read 了，但 worker_course 最初误解。
- Accounting full-review pass 被延后。

workflow 约束：

- `repair_acceptance_contract` 要求 accepted_revision，read=true 不算真正接单。
- `file_evidence_gate` 要求 review PASS 有文件级证据。
- `quality_gate` 要求高优质量问题未解除前不得 subject closeout。

## Physics 0625 pre-QA gate

对应 workflow：

- `igcse-subject-launch`

覆盖的问题：

- worker_course 提交计划后，不应直接给 manager 收口。
- 正确链路应为 worker_course -> review_course -> manager。
- minor required 必须二次 / 三次确认。

workflow 约束：

- `review_handoff_gate` 强制 review_course 接手。
- forbidden moves 明确禁止 `worker_course -> manager` 直接收口。
- done definition 要求 manager 只能基于 review verdict 正式开线。

## Physics 0625 item-level prototype

对应 workflow：

- `igcse-item-level-prototype`

覆盖的问题：

- topic-level QA 不等于题库可入库资产。
- qbank 需要做最小验证。
- builder 需要把 qbank 经验沉成模板。

workflow 约束：

- worker_qbank 只交 prototype 和入库缺口，不做正式对外结论。
- review_course 按 item 粒度复核。
- worker_builder 必须沉 item 模板、handoff 模板、review checklist。

## 7.5 minor repair

对应 workflow：

- `igcse-subject-launch`
- 后续可能抽成 repair variation

覆盖的问题：

- repair 指令中金额被 shell expansion 破坏。
- worker_course read 了消息，但误解为完成确认。

workflow 约束：

- `repair_acceptance_contract` 要求 topic、files_to_edit、review_issue_ids、intended_fix。
- common failure modes 记录 shell 插值破坏金额、公式或路径。
- manager 不应只凭 read=true 判断返工开始。

## 429 / DeepSeek fallback 恢复

对应 workflow：

- `runtime-recovery-and-resume` backlog

覆盖的问题：

- runtime-status.json 显示 DeepSeek，但 live process env 没有生效。
- pane ready 不代表 inbox 已消费。
- manager runtime 恢复后仍可能处理旧线程而不是最新高优指令。

workflow 约束：

- `runtime_reality` 要求 live env / actual CLI / latest inbox consumed / meaningful action。
- backlog 明确下一阶段要把恢复 checklist 写成 workflow。

## review_course 文件级证据不足

对应 workflow：

- `igcse-subject-launch`
- `quality-gate-intervention` backlog

覆盖的问题：

- review_course PASS 有时像 summary-level pass。
- 用户看不到 review_course 是否真的开始复核。
- quality gate 提醒到达时，manager 已继续 topic rollover。

workflow 约束：

- `file_evidence_gate` 固定 evidence packet。
- reassurance_policy 允许 review_course 低频外显 started / handed_to_manager。
- `quality_gate` 要求 active gate 阻断 rollover。

## 当前仍未解决的事

- 这些文档还没有接入代码层 manager panel / scanner / publish。
- runtime 恢复还需要 repo 内 checklist 或命令级验证。
- quality gate 还需要产品层优先级和 panel 表达。
- review evidence packet 还需要后续变成模板或测试样例。
- worker/review/qbank 的外显策略还需要继续在真实运行中校准。

