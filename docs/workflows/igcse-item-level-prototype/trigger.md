# trigger: igcse-item-level-prototype

## Standard Manager Call

```text
调用 workflow: igcse-item-level-prototype
对象: <subject + topic/files>
范围: 1-2 个 topic 或文件的 item-level prototype
边界: 不扩新 topic；不做完整题库规模；qbank 不直接对 user 做正式结论
需要的 verdict / artifact: item prototype + review_course item-level verdict + builder template asset
```

## Use When

- Topic-level QA has passed enough to test qbank readiness.
- Manager needs to know whether QA can become item-level assets.
- Builder should extract a reusable item template after prototype review.

## Do Not Use When

- Subject launch is not yet approved.
- The team is still fixing topic-level QA quality.
- The requested task is full-scale item production.

