# 2026-06-20 EduFlow Team Workflow Registry v1

## 定位

这份文档是 `manager` 的 workflow 调用目录，也是 `worker_builder` 维护 workflow 资产的入口。

它不是案例集，也不是自动执行引擎。第一版只解决一个问题：

> manager 面对真实任务时，先知道该调用哪条协作协议，而不是每次临场重新组织。

## 当前可调用 workflow

| workflow_id | workflow_name | status | owner | when_to_use | primary_chain | current_scope | acceptance_gates | forbidden_moves | last_validated_run | next_builder_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `igcse-subject-launch` | IGCSE 新学科开线 | active | `worker_builder` | 新学科从候选进入正式开线，或从上一学科切到下一学科 | `manager -> worker_course -> review_course -> manager` | IGCSE 学科候选、outline、QA seed、pre-QA gate | `dispatch_acceptance_gate`, `review_handoff_gate`, `file_evidence_gate`, `quality_gate`, `artifact_standard_gate`, `repair_acceptance_contract`, `stale_state_reconciliation` | `worker_course -> manager` 直接收口；minor 未复核就开线；预产出待审和正式通过混说 | Physics 0625 pre-QA gate；Accounting 0452 subject closeout | 把 Physics / Accounting 现场样本继续压缩成 handoff 模板 |
| `igcse-item-level-prototype` | IGCSE item-level 原型验证 | active | `worker_builder` | topic-level QA 已有，但 qbank 判断还不能直接入库，需要最小 item 原型 | `manager -> worker_qbank -> review_course -> worker_builder -> manager` | 1-2 个 topic 或文件的 item-level prototype | `dispatch_acceptance_gate`, `review_handoff_gate`, `file_evidence_gate`, `quality_gate`, `artifact_standard_gate`, `runtime_reality`, `stale_state_reconciliation` | 扩成完整题库；跳过 review；qbank 直接对 user 做正式结论；拿 topic-level QA 当 item-level 资产 | Physics 0625 item-level prototype 提案 | 沉淀 item 模板、review 维度、manager 收口口径 |
| `realrun-to-workflow` | 真实运行经验沉淀为 workflow | active | `worker_builder` | 某条链路已经跑出稳定经验，需要升级为可复用调用资产 | `manager -> worker_builder -> manager` | 真实运行样本、gap note、case note、workflow spec | `dispatch_acceptance_gate`, `file_evidence_gate`, `quality_gate`, `runtime_reality`, `stale_state_reconciliation` | 只写总结不写调用协议；把单次 case 当 workflow；忽略失败样本 | Accounting / Physics 真实运行复盘；Workflow Registry v1 建设 | 建立 workflow 更新节奏与 intake 规则 |
| `ap-knowledge-base-optimization` | AP 知识库题库优化 | active | `worker_builder` | AP 学科从框架到题库 items 的优化生产；需区分 Unit/package 与 subject/qbank-agent ready | `manager -> worker_course -> review_course -> manager` | AP 学科框架、Unit items、manifest、QA 自检 | `dispatch_acceptance_gate`, `review_handoff_gate`, `ap_item_schema_gate`, `file_evidence_gate`, `manifest_qa_script_gate`, `tier_promotion_gate`, `stale_state_reconciliation` | worker_builder 生产 actual MCQ；Unit/package approved 冒充 subject_sample_ready；worker_course 直接收口；未复核 minor 就 rollover | AP Computer Science A Unit 1 生产与复核（T-42） | 沉淀 AP item schema、manifest/QA 校验脚本、四档 tier 口径 |

## Backlog workflow

| workflow_id | workflow_name | status | owner | when_to_use | candidate_chain | first_builder_action |
| --- | --- | --- | --- | --- | --- | --- |
| `runtime-recovery-and-resume` | 运行态恢复与继续执行 | backlog | `worker_builder` + `auto_ops` | 429、备用模型半恢复、pane ready 但未消费 inbox、env drift、bare CLI command stall | `Auto/Hermes -> manager -> worker_builder -> manager` | 把 `runtime_reality` 验证收成最小 checklist |
| `quality-gate-intervention` | 高优质量门禁介入 | backlog | `worker_builder` + `review_course` | 用户、Auto 或 Hermes 发现质量门禁，必须打断 topic rollover | `observer -> auto_ops -> manager -> review_course -> manager` | 把 `quality_gate_active` 与 file-level evidence 要求写成可执行协议 |

## Manager 调用口径

manager 调用 workflow 时，使用统一口径：

```text
调用 workflow: <workflow_id>
对象: <subject/task/topic>
范围: <scope>
边界: <constraints>
需要的 verdict / artifact: <expected output>
```

示例：

```text
调用 workflow: igcse-subject-launch
对象: Physics 0625
范围: pre-QA gate + 首批 seed
边界: worker_course 不得直接收口；minor 必须回 review_course；manager 只在 verdict 通过后正式开线
需要的 verdict / artifact: review_course 的 file-level verdict + outline/seed/manifest 一致性确认
```

## Builder 维护口径

`worker_builder` 不是事后总结员，而是 workflow maintainer。每次真实运行结束后，builder 至少判断：

- 这次是已有 workflow 的普通样本，还是暴露了新分支？
- 有没有新增 forbidden move？
- 有没有新增 acceptance gate？
- 有没有 agent 固定动作需要回写到 identity / skill / template？
- registry 中的 `last_validated_run` 和 `next_builder_action` 是否需要更新？

## 当前不做

- 不做自动执行引擎。
- 不做 YAML / JSON DSL。
- 不把 workflow 写成 Claude Code 式 subagent workflow。
- 不让 auto_ops 成为 workflow owner。
- 不把 gap note 的问题删掉或弱化成“已解决”。

