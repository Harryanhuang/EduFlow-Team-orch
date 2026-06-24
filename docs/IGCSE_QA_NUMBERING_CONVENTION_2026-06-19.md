# IGCSE QA Numbering Convention

适用场景：每个学科累计 `200-300` 题，且一个 topic 下可能有多道题。

## 1. 编号层级

推荐使用三级编号：

- `Topic ID`
- `Question ordinal within topic`
- `Difficulty tag`

推荐展示格式：

- `Q-<topic-id>-<nn>`

示例：

- `Q-1.1-01`
- `Q-1.1-02`
- `Q-2.3-07`
- `Q-N6-04`

在文件系统或机器处理时可用 normalized 版本：

- `Q-1-1-01`
- `Q-2-3-07`
- `Q-N6-04`

## 2. 单题块建议结构

```md
### Question Q-1.1-01
**Difficulty**: Foundation
**Question**: ...
**Answer**: ...
**Explanation**: ...
**Tags**: ledger, purpose-of-accounting
```

## 3. 难度枚举

统一三档：

- `Foundation`
- `Standard`
- `Challenge`

不要在同一题库里混用：

- `easy/medium/hard`
- `basic/intermediate/advanced`
- `L1/L2/L3`

## 4. 编号规则

- 同一 topic 内从 `01` 开始递增
- 编号一旦进入 review，不随意重排
- 删除题目时，该编号留空或标记 retired，不立即回填
- 新增题目在尾部追加，避免影响 reviewer 引用

## 5. 与文件结构的关系

- 一个 QA 文件可包含该 topic 的多道题
- 文件名仍是 topic 级，不是题级
- 题级可定位靠 `Q-<topic-id>-<nn>`

## 6. 禁止项

- 不要每次改稿都重排题号
- 不要按批次重置同一 topic 的题号
- 不要把难度写进题号主体，难度是元数据，不是主键
