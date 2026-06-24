# handoff-template: igcse-subject-launch

## Manager -> worker_course

```text
调用 workflow: igcse-subject-launch
对象: <course + code>
范围: <candidate / outline / QA seed / manifest>
边界:
- 先交 review_course，不直接向 manager 收口
- 如 review_course 给 minor_required，先做 accepted_revision，再修复
- 未通过 review 前不得说成正式开线
请先低频外显接单与开工，然后提交 artifacts 给 review_course。
```

## worker_course -> review_course

```text
请按 igcse-subject-launch 复核 <subject + code>。
范围:
- <files / outline / seed / manifest>
需要 verdict:
- pass / minor_required / reject / conditional_pass
如为 pass，请给 file-level evidence packet。
如为 minor_required，请列出 issue id、文件、必须修复项。
```

## review_course -> manager

```text
igcse-subject-launch verdict for <course + code>:
Verdict: <pass / minor_required / reject / conditional_pass>
Scope reviewed: <files / artifacts>
Evidence: <sampled files, mapping count, spot checks, path convention check>
Blocking issues: <none / list>
Manager action needed: <launch / reject / send minor repair>
```

## Closeout Split

```text
如果本次 verdict 只覆盖 Batch / package / QA seed，不要说成 subject closeout。
Batch/package PASS -> manager 用 task batch-closeout。
只有整科 inventory + evidence + QA standard 全满足时，manager 才能用 task manager-closeout。
```
