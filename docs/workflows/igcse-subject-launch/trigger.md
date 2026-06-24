# trigger: igcse-subject-launch

## Standard Manager Call

```text
调用 workflow: igcse-subject-launch
对象: <subject name + syllabus code>
范围: candidate -> pre-QA gate
边界: worker_course 不得直接对 manager 收口；必须经过 review_course verdict；minor 必须回 review_course 二次确认
需要的 verdict / artifact: file-level review verdict + outline / seed / manifest 一致性确认
```

## Use When

- A previous subject is closing and the next subject needs formal launch.
- `worker_course` has proposed a candidate subject and minimum plan.
- There is a pre-QA gate with outline / seed / manifest artifacts.
- A minor repair must return to review before manager closeout.

## Do Not Use When

- The task is already in item-level qbank prototype.
- The task is full-scale production without a subject launch decision.
- The real issue is runtime recovery or high-priority quality intervention.

