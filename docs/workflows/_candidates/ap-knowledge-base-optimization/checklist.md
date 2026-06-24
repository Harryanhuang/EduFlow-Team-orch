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

## Promotion Checklist

- [ ] `eduflowteam workflow validate` passes。
- [ ] `eduflowteam workflow validate --strict` passes。
- [ ] manager confirms active status。
- [ ] README documents lifecycle_notes、manager_closeout 与四档 tier。
- [ ] 至少一个 AP subject pilot 已跑通。
