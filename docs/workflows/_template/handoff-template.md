# handoff-template: <workflow_id>

## Manager -> worker_builder

```text
调用 workflow: realrun-to-workflow
对象: <new workflow candidate>
范围: <real-run evidence / gap note / repeated pattern>
边界:
- 先按 docs/workflows/_template 起草
- 不直接标记 active
- 不自动派单、不发飞书、不写 task
- 必须保留 manager closeout 和 worker reassurance 边界
请输出 draft workflow assets，并说明建议动作：
update_trigger_examples / update_forbidden_moves / update_acceptance_gates / mark_stale_candidate / split_new_workflow_candidate
```

## Manager -> first_assignee

```text
调用 workflow: <workflow_id>
对象: <subject/task/topic>
范围: <scope>
边界:
- 按角色边界执行
- 必要 review 不可跳过
- worker 只做低频 reassurance，不抢 manager 正式结论
需要的 verdict / artifact: <expected output>
```

## Worker -> review_or_next_assignee

```text
workflow: <workflow_id>
handoff target: <review_or_next_assignee>
scope: <files / artifacts / decision>
evidence: <file-level evidence if required>
open issues: <none / list>
```

## Review / Builder -> manager

```text
workflow: <workflow_id>
verdict: <pass / minor_required / reject / manager_action>
scope reviewed: <scope>
evidence: <files / checks / artifacts>
recommended manager action: <closeout / repair / stale / split>
```
