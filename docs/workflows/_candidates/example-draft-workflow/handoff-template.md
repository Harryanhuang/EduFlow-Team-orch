# handoff-template: example-draft-workflow

## Manager -> worker_builder

```text
调用 candidate workflow: example-draft-workflow
对象: <real-run evidence / gap note>
范围: candidate draft only
边界:
- 不当作 active workflow
- 不用于 task dispatch --workflow
- 不自动派单、不发飞书、不写 task
- promotion 必须经过 manager closeout
请给出 candidate files 和 builder recommendation。
```

## worker_builder -> manager

```text
candidate workflow: example-draft-workflow
status: draft
owner: worker_builder
recommendation: <promotion_ready / backlog / stale_candidate / rejected / case_note_only>
evidence: <real-run / gap note>
manager closeout needed: yes
```
