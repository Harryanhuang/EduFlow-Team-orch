# IGCSE Review Preflight Checklist

提交给 `review_course` 前逐项自查：

## 1. 结构完整性

- [ ] `content/<subject-slug>/topic-outline.md` 已存在
- [ ] `content/<subject-slug>/qa/` 已存在
- [ ] outline 中每个 topic 都有唯一 QA 文件
- [ ] 没有孤立 QA 文件找不到对应 topic

## 2. 命名一致性

- [ ] 课程目录名符合 `igcse-<subject>-<code>`
- [ ] QA 文件名符合 `<normalized-topic-id>-<topic-slug>.md`
- [ ] topic ID 在 outline、文件名、QA 标题中一致

## 3. 内容字段完整性

- [ ] 每个 QA 文件都包含：Topic 名称、定义、关键知识点、前置知识、常见错误、可出题方向、难度提示、适合题型
- [ ] outline 每行都有 ID、Topic、层级标签、前置
- [ ] Core / Extended 标签未混乱

## 4. 事实与边界

- [ ] 内容未超出该 syllabus 范围
- [ ] 未改写已确认的课程事实
- [ ] 前置关系基本合理，没有明显逆序依赖

## 5. review 友好性

- [ ] 当前批次文件数可控，适合一次 review
- [ ] 批次说明写清 topic 范围和关注点
- [ ] 若存在争议点，已单独备注而不是埋在正文里

## 6. 可复用性

- [ ] 新文件遵守通用模板，没有临时私有字段
- [ ] 同一学科内部风格一致
- [ ] reviewer 反馈可沉淀回模板或规范文件

## 7. 大规模题库附加项（200-300 QA 适用）

- [ ] 已建立 `qa-manifest.csv` 或等价总索引
- [ ] 每个 topic 的题量预算已登记
- [ ] 题级编号符合 `Q-<topic-id>-<nn>` 规则
- [ ] 已定义每批依赖关系和 freeze 状态
- [ ] 删除/改稿未导致已 review 题号漂移
