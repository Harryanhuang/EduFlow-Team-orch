# handoff-template: ap-knowledge-base-optimization

## Manager -> worker_course

```text
调用 workflow: ap-knowledge-base-optimization
对象: <AP Subject>
范围: <Unit / Topic / full subject sample>
边界:
- 只做指定范围，不自动扩 Unit/学科
- 产物必须进入 Obsidian /AP <Subject>/02-题库/items/
- 每 subtopic 输出 F/S/C 三道 MCQ，命名 U<unit>.<topic>.<subtopic>-<F|S|C>.md
- item 文件必须包含完整 qbank-agent schema 字段
- worker_builder 不参与 actual MCQ 内容生产
需要的 verdict / artifact:
- 学科框架文件
- Unit item 文件
- qa-manifest.csv（subtopic 行 + topic/unit SUMMARY 行）
- QA-自检.md（7 项 checklist）
```

## worker_course -> review_course

```text
workflow: ap-knowledge-base-optimization
handoff target: review_course
scope: <Unit / Topic / subject sample>
evidence:
- sampled item files: <list>
- schema check result: <PASS / FAIL with fields>
- item count by unit/topic: <counts>
- manifest rows vs files: <drift / match>
- QA-自检 result: <PASS / FAIL>
open issues: <none / list>
```

## review_course -> manager

```text
workflow: ap-knowledge-base-optimization
verdict: <pass / minor_required / reject / manager_action>
scope reviewed: <Unit / Topic / subject sample>
schema_pass: <true / false>
content_quality_pass: <true / false>
evidence:
- sampled files: <list>
- schema violations: <list>
- content issues: <list>
- counts: items= X, manifest_rows= Y, QA passed= Z
recommended manager action: <tier_promote / repair / stale / split / closeout_completed>
recommended tier: <unit_seed_ready / unit_package_ready / subject_sample_ready / qbank_agent_ready>
```

## manager -> user

```text
AP <Subject> <Scope> 已推进至 <tier>。
- 完成内容：<summary>
- 下步动作：<next unit / next subject / qbank-agent validation / repair>
- 注意：当前为 <tier>，不等同于完整学科 closeout。
```
