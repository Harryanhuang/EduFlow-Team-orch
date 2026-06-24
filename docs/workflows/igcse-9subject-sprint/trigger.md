# trigger: igcse-9subject-sprint

## Standard Manager Call

```text
调用 workflow: igcse-9subject-sprint
对象: <subject_name> (<syllabus_code>)
范围: sprint Node 1 → Node 2 → batch dispatch
需要的 artifact: topic-outline.md / qa-manifest.csv / sprint-brief
```

## Batch Dispatch Template (per subject)

```text
调用 workflow: igcse-subject-launch
对象: <subject_name> (<syllabus_code>)
范围: sprint Node 1 → Node 2
需要的 artifact: topic-outline.md / qa-manifest.csv / sprint-brief
```

## 9-Subject Sprint Dispatch Order

Recommended batch sequence (from most to least ready):
  1. Physics 0625     (Batch 9/9 final, needs closeout)
  2. Biology 0610     (3/?? topics, QA exists, partial)
  3. Accounting 0452   (outline complete, 38 QA, partial)
  4. Chemistry 0620  (3/?? topics, QA exists, partial)
  5. Economics 0455   (outline only, QA empty)
  6. Mathematics 0580 (3/?? topics, QA partial)
  7. AddMath 0606     (NOT STARTED)
  8. Combined 0653    (NOT STARTED)
  9. CompSci 0478     (NOT STARTED)

## Sprint Status Report Trigger

```text
调用 workflow: igcse-9subject-sprint
命令: status_summary
需要的 artifact: 9-subject sprint status table
```

## Use When

- Sprint start: dispatch all 9 subjects with current-state awareness
- Sprint mid-point: progress review every 30 minutes
- Sprint end: final closeout summary for all 9 subjects

## Do Not Use When

- Runtime is unhealthy or agents are blocked
- review_course has a backlog of unreviewed items
- A single subject has more than 3 open minor repairs
