# IGCSE Batch Dependency Spec

适用场景：多批次并行生产、review_course 分批复核、总量达到 `200-300` 题。

## 为什么需要

小规模时，批次只需按章节切分。  
大规模时，如果没有依赖和冻结规则，会出现：

- 前批 topic ID 变动导致后批文件名漂移
- reviewer 引用失效
- manifest 与实际文件不一致
- 多人并行时重复出题或漏题

## 1. 批次定义

- `batch-01`, `batch-02`, `batch-03` ... 顺序编号
- 每批绑定：
  - topic 范围
  - 计划题量
  - 依赖批次
  - freeze 状态

## 2. 依赖规则

- 若 topic B 依赖 topic A 的术语或框架，B 所在批依赖 A 所在批
- 若前批涉及 outline / topic ID 可能调整，后批不得先冻结
- manifest 中用 `depends_on_batches` 显式记录

## 3. Freeze 规则

三种状态：

- `draft`：可调整 topic 名、题量、编号规划
- `review`：已交 reviewer，原则上不改主键
- `frozen`：review 通过，不改 topic ID、文件名、已发题号

## 4. 推荐流程

1. `batch-01` 先过 outline 对应基础 topic
2. `batch-02+` 只在前置批 topic ID 稳定后继续
3. 每批提交时同步更新 manifest
4. reviewer 反馈若涉及结构级变动，先回退到 draft，再统一修下一批

## 5. 最小 manifest 字段

- `subject_slug`
- `topic_id`
- `topic_name`
- `qa_file`
- `question_count`
- `difficulty_mix`
- `batch_id`
- `depends_on_batches`
- `status`
- `review_state`
- `owner`
- `notes`

## 6. manager / reviewer 报告口径

每批至少汇报：

- topic 范围
- 题量
- 依赖是否已满足
- 当前 freeze 状态
- 是否有 blocked topic
