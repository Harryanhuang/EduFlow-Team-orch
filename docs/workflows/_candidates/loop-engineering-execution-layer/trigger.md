# trigger: loop-engineering-execution-layer

## Standard Manager Call

```text
调用 candidate workflow: loop-engineering-execution-layer
对象: <task id / builder repair / workflow-backed task>
范围: loop evidence and repair coordination only
边界: loop pass 不等于 delivery / review verdict / manager closeout；不自动派单；不自动执行 workflow
需要的 verdict / artifact: loop-status summary + evidence ref + optional Builder handoff
```

## Use When

- Builder work needs deterministic verification before manager closeout.
- A workflow-backed task has review/repair cycles that need a visible next owner.
- Repeated failure cycles may need memory/workflow crystallization after closeout.

## Do Not Use When

- The task has no formal task id.
- The need is a subjective content verdict that belongs to `review_course`.
- Manager is asking for final user-facing closeout.
