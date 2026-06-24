# IGCSE Batch Delivery Spec

目的：让 `review_course` 可以按批次复核，避免一次性提交过大造成返工。

## 推荐批次切分

按知识领域或自然章节分批，不按随意文件数量分批。

推荐批次顺序：

1. `topic-outline.md` 先单独提交一次
2. 每批 4-8 个 QA 文件，且尽量属于同一领域
3. 难度或依赖强的 topic 放在后批，先过基础块
4. 最后一批补遗漏、交叉检查、统一命名

## 每批交付内容

每一批至少包含：

- 本批 QA 文件路径列表
- 对应 topic ID 范围
- 是否覆盖 Core / Extended
- 是否存在待 reviewer 特别关注的边界点

## 给 review_course 的消息模板

`Batch <n> ready: <subject-slug> topics <id-range>, files <count>. Focus: <domain>. Notes: <edge cases or none>.`

## 交付顺序约束

- 先有 outline，后有 QA
- 同一 topic 不跨两批拆开
- 若发现 outline 需调整，先回修 outline，再继续后续批次

## 回退策略

- 某批被指出结构性问题时，暂停后续批次
- 先修正模板级问题，再批量套回未 review 文件
- 把 reviewer 指出的问题写回命名规范或检查清单，避免重复犯错
