# trigger: ap-knowledge-base-optimization

## Standard Manager Call

```text
调用 workflow: ap-knowledge-base-optimization
对象: <AP Subject，如 AP Computer Science A>
范围: <Unit / Topic / full subject sample>
边界:
- 只做指定范围，不自动扩 Unit/学科
- 产物必须进入 Obsidian /AP <Subject>/02-题库/items/
- worker_builder 不参与 actual MCQ 内容生产
需要的 verdict / artifact: review_course schema + content PASS；qa-manifest.csv 与 QA-自检.md 同步；明确 tier 状态
```

## Use When

- 需要为 AP 学科生产或优化题库 items。
- manager 需要稳定的“派工 → 生产 → review → closeout”链路。
- 需要把 Unit/package approved 与 subject/qbank-agent ready 分开。

## Do Not Use When

- 一次性 case note，没有重复价值。
- 已有 active workflow 能覆盖该场景。
- 只需要 runtime 修复或 workflow 资产维护（应使用 `realrun-to-workflow` 或 runtime 流程）。
- 要求自动派单、自动发飞书或自动执行。

## Boundary

manager calls the workflow and owns formal closeout. Workers may provide low-frequency reassurance, but they must not抢 manager formal verdict or final user-facing result.
