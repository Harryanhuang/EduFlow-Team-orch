# trigger: realrun-to-workflow

## Standard Manager Call

```text
调用 workflow: realrun-to-workflow
对象: <real run / gap note / case>
范围: <what pattern or failure should be converted>
边界: 不写普通总结；必须产出 trigger、handoff、gates、forbidden moves、done definition
需要的 verdict / artifact: workflow asset + registry update recommendation
```

## Use When

- A chain has run successfully more than once.
- The same failure mode keeps appearing.
- Manager keeps needing the same instruction.
- Builder has enough real evidence to write a reusable asset.

## Do Not Use When

- There is only a vague idea and no real run.
- The issue is a one-off bug with no collaboration pattern.
- The task requires code changes before any process asset can be useful.

