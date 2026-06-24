# workflow: igcse-item-level-prototype

## 基础信息

- `workflow_id`: `igcse-item-level-prototype`
- `workflow_name`: IGCSE item-level 原型验证
- `status`: active
- `owner`: `worker_builder`
- `initiator`: `manager`
- `participants`: `manager`, `worker_qbank`, `review_course`, `worker_builder`; 必要时 `worker_course` 补充 topic 背景
- `handoff_chain`: `manager -> worker_qbank -> review_course -> worker_builder -> manager`

## when_to_use

用于 topic-level QA 已经存在，但还不能证明它能直接支撑题库入库，需要先做 1-2 个文件或 topic 的 item-level 原型验证。

这条 workflow 的目的不是扩生产量，而是回答：

> 现在的 QA 能不能变成可入库、可检索、可复核、可规模化的题目实体？

## trigger_examples

```text
调用 workflow: igcse-item-level-prototype
对象: Physics 0625
范围: 1-2 个已通过 topic 的 item-level prototype
边界: 不扩新 topic，不碰完整题库规模，不让 qbank 直接对 user 做正式结论
```

## in_scope

- 从已通过的 topic-level QA 中选 1-2 个最小样本。
- worker_qbank 产出 item-level 实体样本。
- review_course 复核 item 粒度、可解性、答案质量、元数据。
- worker_builder 沉淀 item 模板、handoff 模板、review checklist。
- manager 判断是否进入下一阶段。

## out_of_scope

- 不扩成完整题库规模。
- 不补新 topic。
- 不处理 Extended 范围，除非 manager 明确纳入。
- 不让 worker_qbank 做正式对外结论。
- 不把 topic-level QA 直接等同于 item-level 入库资产。

## required_inputs

- 已通过 review 的 topic-level QA 文件。
- topic / QA / manifest 路径。
- manager 指定的最小 prototype 范围。
- 题库入库最低要求：题干、答案、解析、知识点、难度、题型、来源 topic、可解性。

## expected_outputs

worker_qbank 应交：

- 1-2 个 topic 或文件的 item-level prototype。
- 每个 item 的题干、答案、解析、知识点、难度、题型、topic 映射。
- 不足以入库的缺口说明。

review_course 应交：

- item-level verdict。
- file-level evidence packet：
  - sampled item IDs
  - solvability check
  - answer / explanation check
  - topic mapping check
  - metadata completeness check

worker_builder 应交：

- item 模板资产。
- handoff 模板。
- forbidden moves。
- done definition。

manager 应交：

- 是否通过 item prototype。
- 是否允许扩大到下一批。
- 正式问题处理与阶段判断。

## acceptance_gates

- `dispatch_acceptance_gate`: worker_qbank 必须明确接单，不能只看消息投递。
- `review_handoff_gate`: qbank prototype 必须进入 review_course，不得直接 manager 收口。
- `file_evidence_gate`: review_course 必须抽查具体 item，不接受只看 summary。
- `quality_gate`: prototype 若暴露入库质量缺口，不得继续扩大生产。
- `artifact_standard_gate`: item 文件、topic 映射、manifest 或索引必须一致。
- `runtime_reality`: 若 qbank/review runtime 切换过，必须确认实际有 meaningful action，而不是只看 runtime status。
- `stale_state_reconciliation`: 旧 handoff / 旧 verdict 不得覆盖当前 prototype 范围。

## forbidden_moves

- worker_qbank 直接向 user 或 manager 宣布正式题库可用。
- prototype 第一拍扩成完整题库。
- 未经过 review_course 就让 builder 沉模板。
- review_course 用课程 topic 视角代替 item 粒度复核。
- manager 在 prototype 未通过时宣布题库阶段正式开启。

## reassurance_policy

- worker_qbank 可以低频外显“开始做 item 原型”与“已交 review”，但不公布正式质量结论。
- review_course 可以外显“开始复核 item 原型”和“verdict 已交 manager”。
- worker_builder 可以外显“开始沉淀模板资产”，但不替 manager 宣布阶段通过。

## builder_followup

worker_builder 必须把 prototype 经验沉成：

- item file template。
- qbank handoff template。
- review item checklist。
- manager closeout checklist。
- 是否需要新增 workflow 变体的判断。

## done_definition

满足以下条件才算完成：

- worker_qbank 已产出最小 item prototype。
- review_course 已给 item-level verdict 和证据。
- worker_builder 已沉淀模板资产。
- manager 已正式判断是否进入下一阶段。

## common_failure_modes

- qbank 没外显，user 无法判断是否在工作。
- qbank 只做可行性评论，没有交 item 实体。
- review_course 沿用 topic-level PASS，未检查 item 可解性。
- builder 只写总结，没有形成模板。
- manager 把 prototype 通过误说成完整题库可生产。

