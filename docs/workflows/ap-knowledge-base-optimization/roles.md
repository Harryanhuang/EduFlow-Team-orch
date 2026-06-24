# roles: ap-knowledge-base-optimization

## manager

- Calls the workflow。
- 定义学科、范围、目标 Obsidian 路径、边界与允许进入的 tier。
- 拥有 formal dispatch、formal closeout 与 user-facing summary 的语言权。
- 必须区分 `unit_seed_ready` / `unit_package_ready` / `subject_sample_ready` / `qbank_agent_ready` / `closeout_completed`。

## worker_course

- 接受任务并发送低频 reassurance（接单 / 开工 / 交 review）。
- 生产学科框架文件、Unit item 文件、`qa-manifest.csv`、`QA-自检.md`。
- 所有产出必须落在指定的 Obsidian 目标路径下。
- 不绕过 review_course 直接对 manager 收口。
- 失败时必须沉淀 lesson learned 到下一轮 brief / template / validator。

## review_course

- 复核 worker_course 提交的 scope。
- 给出明确 verdict：`pass` / `minor_required` / `reject` / `manager_action`。
- 必须分别声明 `schema_pass` 与 `content_quality_pass`。
- 提供 file-level evidence：sampled files、schema 检查结果、数量统计、blocking issues。
- 通过 `eduflow task review` 将 verdict 写回 task truth，不能只留在群聊。

## worker_builder

- 维护 workflow 资产、tool、template、schema、validator、runtime 修复。
- 不得接单或生产 actual MCQ / 课程内容 / item generation。
- 在每次 real run 后选择维护动作：`update_trigger_examples`、`update_forbidden_moves`、`update_acceptance_gates`、`mark_stale_candidate`、`split_new_workflow_candidate`。
- 不抢 manager 正式 verdict。

## auto_ops

- 监视 stale handoff、unread backlog、runtime anomaly、gap signal。
- 不拥有 workflow，也不替代 manager 做阶段拍板。

## Boundary

Worker/review/qbank 角色各守其 lane。manager 是 caller 与正式决策 owner。本 workflow 不是自动执行引擎。
