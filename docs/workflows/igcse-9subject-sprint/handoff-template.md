# handoff-template: igcse-9subject-sprint

## Manager -> worker_course: Subject Dispatch

```
请开始 sprint Node 1 → Node 3 推进 [SUBJECT] ([SYLLABUS_CODE])：

当前状态：[topic-outline 完整性] / [QA items 数量] / [item files 数量]
Sprint 目标：[目标 QA gap 填充]
Batch 范围：[topic IDs in this batch]
难度目标：F:2 | S:4 | C:3

请先完成 sprint brief（1段），再进入 QA 生成。
完成后发 review_course 复核，并汇报 manager 进度。
```

## Manager -> review_course: Batch Review Handoff

```
Batch [N] ready for review: [SUBJECT]
Topics: [topic-id-range]
Files: [count]
Focus: [domain notes or none]
请做文件级复核（不是总结级），verdict: PASS / minor revision / FAIL。
```

## worker_course / worker_qbank -> review_course: QA Batch Delivery

```
[SUBJECT] Batch [N] ready: topics [ID-range], [file-count] files.
Focus: [domain]. Notes: [edge cases or none].
```

## review_course -> manager: Verdict Handoff

```
review verdict for [SUBJECT] Batch [N]:
  verdict: [PASS / minor / FAIL]
  evidence: [file-level evidence summary]
  [if minor] revision produced by [agent]
  [if FAIL] root cause: [description]
```

## Sprint Status Report Template

```
=== 9-Subject Sprint Status [HH:MM] ===

Subject        | Outline | QA gap | Items | Status
-------------|--------|--------|-------|--------
0452 Accounting | [n/n]  | [n]   | [n]   | [status]
0606 AddMath   | [n/n]  | [n]   | [n]   | [status]
0610 Biology   | [n/n]  | [n]   | [n]   | [status]
0620 Chemistry | [n/n]  | [n]   | [n]   | [status]
0653 Combined  | [n/n]  | [n]   | [n]   | [status]
0478 CompSci  | [n/n]  | [n]   | [n]   | [status]
0455 Economics | [n/n]  | [n]   | [n]   | [status]
0580 Math      | [n/n]  | [n]   | [n]   | [status]
0625 Physics  | [n/n]  | [n]   | [n]   | [status]

Open issues: [count]
Next action: [highest priority]
```
