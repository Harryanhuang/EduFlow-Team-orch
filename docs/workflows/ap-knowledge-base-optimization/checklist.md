# checklist: ap-knowledge-base-optimization

## Intake Checklist

- [ ] 存在真实 AP 生产场景或 gap note 作为来源。
- [ ] 这不是一次性 case note。
- [ ] 不是现有 workflow（如 igcse-subject-launch）的简单变体。
- [ ] manager 能按名称调用本 workflow。
- [ ] worker_builder 被指定为 workflow maintainer。
- [ ] Primary chain `manager -> worker_course -> review_course -> manager` 已明确。
- [ ] manager closeout 与四档 tier（unit_seed_ready / unit_package_ready / subject_sample_ready / qbank_agent_ready / closeout_completed）已明确。

## Before Manager Dispatch

- [ ] workflow_id 为稳定 slug：`ap-knowledge-base-optimization`。
- [ ] trigger examples 使用真实 AP 学科语言。
- [ ] participants、handoff chain、forbidden moves、reassurance policy 已明确。
- [ ] AP qbank item schema（YAML + 正文标题）已文档化。
- [ ] manifest/QA 脚本校验方式已确定（`scripts/ap_qbank_verify.py`）。

## Before Manager Closeout

- [ ] Required inputs 已 present（学科、范围、目标路径、workflow_id、reviewer）。
- [ ] Expected outputs 已 present（框架、items、manifest、QA 自检）。
- [ ] Core Gates 已检查。
- [ ] Acceptance Gates 已检查。
- [ ] File-level evidence 存在。
- [ ] `scripts/ap_qbank_verify.py` 返回 PASS。
- [ ] worker_builder 已记录下一次维护动作。

## Block Closeout If

- [ ] Required review 或 evidence 缺失。
- [ ] Artifact 路径、命名或 manifest truth 不清晰。
- [ ] Worker reassurance 被当作正式 manager 结果。
- [ ] auto_ops 越过 watcher 角色主导流程。
- [ ] Unit/package 级 approved 被用来冒充 subject_sample_ready 或 qbank_agent_ready。
- [ ] Workflow 需要被拆分或标记 stale 才能激活。
- [ ] `subject_sample_first_gate` 未通过：第一个学科 sample 未完成就启动下一科。
- [ ] `ap_qbank_schema_gate` 未通过：item YAML frontmatter 缺字段或正文缺 Options/Answer/Explanation。
- [ ] `content_quality_gate` 未通过：review_course 未单独给出 content_quality_pass，或 schema PASS 被当作内容质量 PASS。
- [ ] `role_boundary_gate` 未通过：worker_builder 参与 actual MCQ 内容生产，或 review/operator fallback 冒充 manager closeout。
- [ ] `review_verdict_authority_gate` 未通过：manager 未基于 review verdict 正式拍板。
- [ ] `retro_before_next_subject_gate` 未通过：第一学科完成后未做 retro 就进入下一学科。
- [ ] `manager_closeout_gate` 未通过：closeout 缺 manifest/QA 自检/文件证据/review verdict 中任一项。

## Promotion Checklist

- [ ] `eduflowteam workflow validate` passes。
- [ ] `eduflowteam workflow validate --strict` passes。
- [ ] manager confirms active status。
- [ ] README documents lifecycle_notes、manager_closeout 与四档 tier。
- [ ] 至少一个 AP subject pilot 已跑通。
