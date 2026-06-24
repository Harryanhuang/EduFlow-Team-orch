# IGCSE New Subject Launch Flow

基于 Physics 0625 首批链路沉淀：下一学科候选 -> 可开线复核 -> outline minor fix -> 二次/三次确认 -> QA seed 质检通过。

## 适用范围

用于 IGCSE 新学科从候选进入首批生产前后的流程复用。  
目标不是替代课程内容 review，而是把开线 gate、minor 修复、复核确认的节奏固定下来。

## 标准链路

1. `worker_course` 提交下一学科候选与最小计划
2. `review_course` 做可开线性复核
3. `manager` 基于 review verdict 决定是否正式开线
4. `worker_course` 产出首批 outline / seed 文件
5. `review_course` 做 outline + QA seed 质量审校
6. 若 verdict 为 minor required，`worker_course` 修 minor
7. `review_course` 做二次确认；若仍有缺口，进入三次确认
8. `manager` 只在 review 明确通过后收口 pre-QA gate
9. `worker_course` 将首批 QA seed 归档为正式产出

## 阶段验收点

### 1. 下一学科候选

验收点：

- 学科 code 明确，例如 `igcse-physics-0625`
- 候选理由明确：课程组合补齐、已有资产可参考、生产风险可控
- 最小计划明确：首批 topic 范围、预计 QA seed 数量、review 节点

不得直接把候选计划当作可开线结论。

### 2. 可开线性复核

验收点：

- `review_course` 明确给出 `accept / reject / conditional`
- 若为 `conditional`，必须列出阻断项或 minor 项
- manager 只消费 review verdict，不跳过 review gate

### 3. 首批 outline

验收点：

- `topic-outline.md` 存在
- 首批 topic ID、topic 名称、Core/Extended 范围、前置关系清晰
- 知识领域概览与 topic 列表一致
- outline 能一一映射到 QA seed 文件

### 4. QA seed

验收点：

- QA seed 文件存在且命名符合规范
- 每个 seed 文件含 Topic 名称、定义、关键知识点、前置、常见错误、可出题方向、难度提示、适合题型
- `qa-manifest.csv` 存在并登记 topic、文件、题量、batch
- outline 中的关键概念已同步进入对应 QA seed

### 5. 二次 / 三次确认

验收点：

- 每次 minor 修复后必须回到 `review_course`
- review verdict 必须明确写出是否通过
- manager 不在二次/三次 verdict 前宣布正式进入下一阶段

### 6. QA seed 质检通过

验收点：

- `review_course` 明确首批通过
- manager 明确 pre-QA gate 已收口
- worker 将 QA seed 标记为正式产出，而不是“预产出待审”

## 常见 minor 类型

Physics 0625 现场暴露出的典型 minor：

- outline 与知识领域概览不一致
  - 例如概览表分成 `2 + 2`，但实际应合并为 `General physics | 4`
- outline 已补概念，但 QA 未同步
  - 例如 `terminal velocity` 进入 outline 后，QA 1.2 仍缺对应知识点、常见错误、出题方向
- syllabus 关键概念遗漏
  - 例如 `scalars vs vectors`
  - 例如 `W = mg`
  - 例如 `mass vs weight`
- manifest 缺失
  - 首批 QA seed 文件存在，但缺 `qa-manifest.csv`
- 状态表述过早
  - 把“预产出待审”说成“正式下一阶段已开始”
- verdict 语义误读
  - 把 `minor required / pass after fix` 误收成 `direct pass`

## 二次确认触发条件

任一条件满足，必须触发二次确认：

- review verdict 不是直接通过，而是 `minor required`
- outline 内容有调整，且 QA seed 需要同步
- QA seed 已预产出，但 review 尚未明确通过
- manifest、topic ID、文件名、题量登记有任何补改
- manager 或 status 摘要与最新 review verdict 不一致

## 三次确认触发条件

任一条件满足，必须触发三次确认：

- 二次确认明确指出仍有未完成项
- 文件面显示已修，但 review/status 仍停在旧 verdict
- 修复项影响多个文件，例如 outline + QA + manifest
- reviewer 指出的唯一阻断项已补，需要最终确认收口

## Manager 收口规则

manager 收口前必须同时满足：

- `review_course` 最新 verdict 为通过
- 文件面存在 outline、QA seed、manifest
- worker 状态不再是“待审预产出”
- 群消息、team status、文件真相三者没有明显冲突

禁止：

- 跳过 `review_course` 直接开线
- 把 conditional pass 当 direct pass
- 在二次/三次确认前宣布正式切下一阶段

## 可复用口径

最小派工模板：

```text
请按 IGCSE 新学科开线链路处理：先提交候选与最小计划 -> review_course 做可开线复核 -> manager 基于 verdict 决定开线 -> 产出首批 outline/QA seed -> review_course 质检 -> minor 修复后二次/三次确认 -> 通过后再收口进入正式 QA。
```

最小 review 请求模板：

```text
请 review_course 复核 <subject-slug> 是否可开线，并检查首批 outline/QA seed 是否满足 pre-QA gate。若为 minor required，请列出必须二次确认的具体项。
```
