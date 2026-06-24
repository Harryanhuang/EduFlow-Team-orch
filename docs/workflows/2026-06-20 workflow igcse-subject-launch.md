# workflow: igcse-subject-launch

## 基础信息

- `workflow_id`: `igcse-subject-launch`
- `workflow_name`: IGCSE 新学科开线
- `status`: active
- `owner`: `worker_builder`
- `initiator`: `manager`
- `participants`: `manager`, `worker_course`, `review_course`; 必要时 `auto_ops` 观察异常
- `handoff_chain`: `manager -> worker_course -> review_course -> manager`

## when_to_use

用于 IGCSE 新学科从候选进入正式开线，或者一个学科完成后切到下一个学科。

典型场景：

- Accounting 0452 完成后切 Physics 0625。
- worker_course 提出下一学科候选和最小计划。
- manager 需要判断是否能正式进入 QA seed 或生产阶段。

## trigger_examples

```text
调用 workflow: igcse-subject-launch
对象: Physics 0625
范围: 下一学科候选 -> pre-QA gate
边界: 不允许 worker_course 直接对 manager 收口；必须经过 review_course verdict
```

```text
调用 workflow: igcse-subject-launch
对象: Accounting 0452 closeout -> next subject
范围: subject closure 后确认下一学科开线
边界: 未完成质量门禁前不得 rollover
```

## in_scope

- 新学科候选与最小计划。
- outline / topic manifest / QA seed 的 pre-QA gate。
- review_course 对开线条件的 verdict。
- minor fix 后的二次 / 三次确认。
- manager 的正式开线或正式拒绝。

## out_of_scope

- 完整题库规模生产。
- item-level 入库验证。
- Extended 范围扩张，除非 manager 明确把它纳入本轮。
- 由 worker_course 直接向 manager 宣布正式收口。

## required_inputs

- 学科名与 syllabus code，例如 `Physics 0625`。
- 当前候选理由和范围。
- 已有文件路径或预期产物路径。
- 是否存在 active quality gate。
- manager 对 batch mode 的明确允许或禁止。

## expected_outputs

worker_course 应交：

- 候选与最小计划。
- outline / QA seed / manifest 的文件级产物。
- 如被退回，按 review issue 做 minor fix。

review_course 应交：

- 明确 verdict：`pass`, `minor_required`, `reject`, `conditional_pass`。
- file-level evidence packet：
  - sampled files
  - item / topic mapping count
  - path convention check
  - concrete spot checks
  - blocking issue list

manager 应交：

- 正式开线、正式拒绝或正式要求返工。
- 是否进入下一阶段的拍板。

## acceptance_gates

- `dispatch_acceptance_gate`: 派工后必须看到接单信号、read 状态或首个有效 artifact delta。派工不等于接单。
- `review_handoff_gate`: worker_course 交 review 后，必须看到 review_course 开始复核或给出绑定范围的 verdict。交 review 不等于 review 开始。
- `file_evidence_gate`: 高质量阶段的 PASS 必须包含文件级证据，不能只有摘要级复述。
- `quality_gate`: active quality gate 未解除时，manager 不得 dispatch next topic / next subject。
- `artifact_standard_gate`: outline、QA seed、manifest、路径命名必须一致；旧 `qa/` 与新 `qa-question-level/` 不能混算。
- `repair_acceptance_contract`: minor fix 必须有 `accepted_revision`，包括 topic、files_to_edit、review_issue_ids、intended_fix。
- `stale_state_reconciliation`: verdict 或 artifact 已推进时，旧 unread / 旧 task 不能继续作为主阻塞源。

## forbidden_moves

- `worker_course -> manager` 直接收口。
- manager 在 `minor_required` 未复核前宣布进入下一阶段。
- 把“预产出待审”说成“正式通过”。
- review_course 只复述 worker 状态摘要，却给 file-level PASS。
- active quality gate 未消费时继续 rollover。
- manager 把单 topic 指令扩成 batch，除非 `batch_mode_allowed=true`。

## reassurance_policy

- worker_course 可低频外显接单和开工，但不直播过程。
- review_course 可低频外显 `review_started` 和 `review_completed_handed_to_manager`，但不抢 manager 的正式 verdict 表达。
- manager 仍独占正式结果、问题处理、阶段拍板。

## builder_followup

每次运行结束后，worker_builder 需要更新：

- 哪些 handoff 模板可复用。
- 哪些 forbidden moves 新出现。
- 哪些 review evidence 维度需要固定。
- 这次是否更新 registry 的 `last_validated_run`。

## done_definition

满足以下条件才算完成：

- worker_course 已提交候选 / outline / seed / manifest。
- review_course 给出绑定范围的 verdict。
- 所有 minor fix 已重新回到 review_course。
- manager 基于 review verdict 正式拍板。
- 群消息、team status、文件真相没有明显冲突。

## common_failure_modes

- worker_course 交给 manager 而不是 review_course。
- review_course unread backlog 和已有 verdict 并存，污染判断。
- manager 在质量门禁未处理时继续切下一 topic。
- repair 消息 read 了，但 worker_course 把返工误解成完成确认。
- shell 插值破坏金额、公式或路径。
- topic / manifest / QA 文件路径不一致。

