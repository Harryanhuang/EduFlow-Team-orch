# trigger: example-draft-workflow

## Standard Manager Call

```text
调用 candidate workflow: example-draft-workflow
对象: <real-run evidence / gap note>
范围: draft candidate only
边界: 不当作 active workflow；不自动派单；不发飞书；promotion 必须 manager closeout
需要的 verdict / artifact: candidate workflow draft + builder recommendation
```

## Use When

- A repeated gap may deserve its own workflow.
- `worker_builder` needs a concrete draft candidate to maintain.

## Do Not Use When

- An active workflow already covers the scenario.
- The pattern is one-off and should remain case note only.
