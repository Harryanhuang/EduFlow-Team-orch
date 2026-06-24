# trigger: <workflow_id>

## Standard Manager Call

```text
调用 workflow: <workflow_id>
对象: <subject/task/topic>
范围: <scope>
边界: <constraints>
需要的 verdict / artifact: <expected output>
```

## Use When

- The request matches a repeated real-run pattern.
- manager needs a stable collaboration chain rather than an ad hoc prompt.
- The required participants and closeout gate are known.

## Do Not Use When

- This is a one-off case note.
- An existing active workflow already covers the scenario.
- The problem is runtime recovery, unless this workflow explicitly owns runtime recovery.
- The request requires automatic dispatch or Feishu sending.

## Boundary

manager calls the workflow and owns formal closeout. Workers may provide low-frequency reassurance, but they must not抢 manager formal verdict or final user-facing result.
