# handoff-template: realrun-to-workflow

## Manager -> worker_builder

```text
调用 workflow: realrun-to-workflow
对象: <real run / gap note / case>
范围: <pattern to convert>
边界:
- 不写普通总结
- 必须产出可调用 workflow 资产或 registry 更新建议
- 必须引用真实运行证据
请判断这是 existing_sample / variation / backlog_candidate / active_candidate / case_note_only。
```

## worker_builder -> manager

```text
realrun-to-workflow result:
Candidate: <workflow_id or existing workflow>
Decision recommended: <active / backlog / stale / variation / case_note_only>
Evidence: <real run / gap note references>
Assets updated: <files or proposed files>
Gates added: <list>
Forbidden moves added: <list>
Next manager action: <approve / reject / request revision>
```

