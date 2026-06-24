# handoff-template: igcse-item-level-prototype

## Manager -> worker_qbank

```text
调用 workflow: igcse-item-level-prototype
对象: <subject + topic/files>
范围: 1-2 个 topic 或文件
边界:
- 不扩新 topic
- 不做完整题库规模
- 产出 item-level prototype 后交 review_course
- 不对 user 做正式结论
请低频外显接单/开工，并提交最小 item 实体。
```

## worker_qbank -> review_course

```text
请按 igcse-item-level-prototype 复核 item prototype。
范围: <item files / topic ids>
请检查:
- solvability
- answer correctness
- explanation usefulness
- topic mapping
- difficulty/type metadata
请给 bounded verdict，不做完整题库结论。
```

## review_course -> worker_builder

```text
item prototype review result:
Verdict: <pass / minor_required / reject>
Reusable pattern: <what can become template>
Issues: <blocking / minor>
请 worker_builder 沉淀 item template、handoff template、review checklist。
```

## worker_builder -> manager

```text
igcse-item-level-prototype asset update:
Template asset: <path / summary>
Checklist update: <summary>
Forbidden moves added: <summary>
Recommendation: <expand / repair / stop>
```

