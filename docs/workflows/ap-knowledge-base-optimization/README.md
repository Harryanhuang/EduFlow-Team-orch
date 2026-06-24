# workflow: ap-knowledge-base-optimization

## Metadata

- workflow_id: `ap-knowledge-base-optimization`
- workflow_name: AP 知识库题库优化
- status: `promotion_ready`
- owner: `worker_builder`

## When To Use

用于 AP（Advanced Placement）学科知识库从框架到题库 items 的优化生产。典型场景：

- 老板指定当晚优化 4-5 个 AP 学科，需要可复现的派工、review、closeout 链路。
- 需要把“学科框架 → Unit items → QA/review → qbank-agent ready”拆成可验证阶段。
- 防止 Unit/package PASS 被误报为 full subject complete。

## Trigger Examples

```text
调用 workflow: ap-knowledge-base-optimization
对象: AP Computer Science A
范围: Unit 1 题库 items 生产
边界: 只做 Unit 1；每 subtopic 输出 F/S/C 三道 MCQ；产物必须进入 Obsidian /AP Computer Science A/02-题库/items/Unit 1/
需要的 verdict / artifact: review_course schema + content PASS；qa-manifest.csv 与 QA-自检.md 同步
```

```text
调用 workflow: ap-knowledge-base-optimization
对象: AP Calculus AB
范围: Subject 1 golden path（先完成完整学科样板，再进入下一学科）
边界: 当前学科未 subject_sample_ready 前，不启动下一学科 full production
需要的 verdict / artifact: full_subject approved + qbank_agent_ready
```

## Initiator

- manager

## Participants

- manager
- worker_course
- review_course
- worker_builder（仅维护 tool/template/schema/validator/workflow/runtime，不参与 actual MCQ 内容生产）
- auto_ops

## Primary Chain

```text
manager -> worker_course -> review_course -> manager
```

## Handoff Chain

```text
manager -> worker_course
worker_course -> review_course
review_course -> manager
manager -> user (final summary)
```

## In Scope

- AP 学科框架文件与 Unit 级 item 文件生产。
- 每道 item 必须满足 AP qbank schema（unit/topic/subtopic + knowledge_point/core_concept/exam_pattern/question_type/common_mistake/explanation_context）。
- `qa-manifest.csv` 与 `QA-自检.md` 的同步与脚本校验。
- review_course 对 schema PASS 与 content quality PASS 的分别 verdict。
- 四档 readiness tier 的晋级：unit_seed_ready / unit_package_ready / subject_sample_ready / qbank_agent_ready。

## Out Of Scope

- Automatic workflow execution。
- Automatic task dispatch（manager 必须显式 flow-create/dispatch）。
- Feishu sending。
- Flow-task state-machine changes（state machine 由 task store 维护）。
- worker_builder 直接生产 actual MCQ item 内容。
- 跨学科并行批量生产，除非 manager 明确允许并设置 `batch_mode_allowed=true`。

## Required Inputs

- 学科名（如 AP Computer Science A）与今晚处理范围（Unit / Topic）。
- 目标 Obsidian 交付路径。
- workflow_id、owner、reviewer、stage。
- 是否允许进入下一学科/单元的明确信号。

## Expected Outputs

worker_course 应交：

- 学科框架文件（如 `<学科>_题库优化版_知识点框架.md`）。
- Unit item 文件（命名 `U<unit>.<topic>.<subtopic>-<F|S|C>.md`）。
- `qa-manifest.csv`（subtopic 行 + topic/unit SUMMARY 行）。
- `QA-自检.md`（7 项 checklist）。

review_course 应交：

- 明确 verdict：`pass` / `minor_required` / `reject` / `manager_action`。
- file-level evidence packet：sampled files、schema 检查结果、item/topic 数量、路径检查、blocking issue list。
- 区分 `schema_pass` 与 `content_quality_pass`。

manager 应交：

- 正式拍板当前 tier（unit_seed_ready / unit_package_ready / subject_sample_ready / qbank_agent_ready）。
- 决定是否进入下一 Unit/学科。

## Core Gates

- `subject_sample_first_gate`
- `ap_qbank_schema_gate`
- `content_quality_gate`
- `role_boundary_gate`
- `review_verdict_authority_gate`
- `retro_before_next_subject_gate`
- `manager_closeout_gate`

## Acceptance Gates

- `subject_sample_first_gate`: 必须先完成完整学科样板（subject sample），才能进入下一学科 full production。Unit package PASS 不等于 subject sample PASS。
- `ap_qbank_schema_gate`: 每道 item 文件必须包含 YAML frontmatter 要求的全部 qbank-agent 字段（unit/topic/subtopic + knowledge_point/core_concept/exam_pattern/question_type/common_mistake/explanation_context），且正文包含 ## Options / ## Answer / ## Explanation。schema PASS 不等于内容质量 PASS。
- `content_quality_gate`: review_course 必须单独给出 `content_quality_pass` verdict，与 schema_pass 独立；不能把 schema 通过冒充内容质量通过。
- `role_boundary_gate`: worker_builder 只维护 tool/template/schema/validator/runtime，不得接单或生产 actual MCQ / 课程内容 / item generation。review/operator fallback 不能冒充 manager closeout。
- `review_verdict_authority_gate`: 只有 manager 能拍板正式 tier 和 closeout；review_course verdict 是 manager 决策依据，不是最终结果；worker/review/qbank 不得抢 manager 正式结论文言。
- `retro_before_next_subject_gate`: 第一学科完成后，必须先完成 retro（复盘、lesson learned、forbidden moves 更新），才能进入下一学科。
- `manager_closeout_gate`: closeout 必须同时有 manifest/QA 自检/文件证据/review verdict，不允许没有证据就 closeout。

## Forbidden Moves

- `worker_course -> manager` 直接收口。
- `worker_builder` 接单或生产 actual MCQ / 课程内容 / item generation。
- manager 在 `minor_required` 未复核前宣布进入下一阶段或下一学科。
- 把”预产出待审”说成”正式通过”。
- review_course 只复述 worker 状态摘要，却给 file-level PASS。
- active quality gate 未消费时继续 rollover。
- manager 把单 Unit 指令扩成 batch，除非 `batch_mode_allowed=true`。
- 用 `package` 或 `unit` 级 approved 冒充 `subject_sample_ready` 或 `qbank_agent_ready`。
- 把 Unit package 冒充 full subject sample；Unit 1 的 approved 不等于整个学科的 subject_sample_ready。
- 未完成第一个 subject sample 就启动下一科 full production。
- review/operator fallback 冒充 manager closeout；manager_closeout 只能由 manager 触发。
- schema PASS 冒充内容质量 PASS；schema_pass 与 content_quality_pass 必须分别声明。
- 没有 manifest/QA 自检/文件证据就 closeout；closeout 必须附 evidence packet。

## Reassurance Policy

- worker_course 可低频外显接单和开工，但不直播过程。
- review_course 可低频外显 `review_started` 和 `review_completed_handed_to_manager`，但不抢 manager 的正式 verdict 表达。
- worker_builder 只能报告 tool/template/schema/validator/runtime 修复进度，不得报告课程内容完工。
- manager 仍独占正式结果、问题处理、阶段拍板。

## Builder Followup

每次运行结束后，worker_builder 需要更新：

- 哪些 handoff 模板可复用。
- 哪些 forbidden moves 新出现。
- 哪些 review evidence 维度需要固定。
- AP item schema 是否需要新增字段。
- 这次是否更新 registry 的 `last_validated_run`。

## Done Definition

满足以下条件才算完成：

- worker_course 已提交学科框架、Unit items、manifest、QA 自检。
- review_course 给出绑定范围的 verdict，且区分 schema PASS 与 content quality PASS。
- 所有 minor fix 已重新回到 review_course。
- manager 基于 review verdict 正式拍板 tier。
- 群消息、team status、文件真相没有明显冲突。

## Common Failure Modes

- worker_course 交给 manager 而不是 review_course。
- review_course unread backlog 和已有 verdict 并存，污染判断。
- manager 在质量门禁未处理时继续切下一 topic / 下一学科。
- repair 消息 read 了，但 worker_course 把返工误解成完成确认。
- shell 插值破坏路径、公式或学科名。
- topic / manifest / QA 文件路径不一致。
- 把 Unit 1 的 approved 当成整个学科的 subject_sample_ready。

## Manager Closeout

manager 是 workflow caller 和正式决策 owner。closeout 时必须显式声明 tier：

- `unit_seed_ready`: 仅有框架或少量 seed items，不足以构成 package。
- `unit_package_ready`: 单个/多个 Unit 的 items 完整通过 review，但未覆盖完整学科 sample。
- `subject_sample_ready`: 完整学科 sample 通过 review，但 qbank-agent 消费链路尚未验证。
- `qbank_agent_ready`: qbank-agent 能成功消费 items 并生成题目/解析。
- `closeout_completed`: manager 正式签名，任务完结。

## Lifecycle Notes

- Start as `draft`。
- Move to `promotion_ready` after at least one real AP subject pilot。
- Move to active only after manager closeout and strict validation。
- Mark stale when repeated real runs show the gates no longer match reality。

## Boundary

This workflow is a reusable coordination asset. It is not an automatic execution engine, scheduler, Feishu sender, or task writer.

When active, manager dispatches via `eduflow task flow-create --workflow ap-knowledge-base-optimization` or `eduflow task dispatch --workflow ap-knowledge-base-optimization`.
