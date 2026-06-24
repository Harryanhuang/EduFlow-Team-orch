# IGCSE QA Bank Scaling Spec

适用场景：单学科扩展到 `200-300` 题级别的 QA 题库化生产，例如 IGCSE Accounting。

## 结论

现有最小资产可以支撑“小规模 topic 级 QA 文件生产”，但不足以支撑 `200-300` 题级别的稳定批量编排。  
缺的不是 topic 模板本身，而是“大规模追踪与批量治理层”。

## 现有资产是否够用

### 已够用

- `docs/templates/IGCSE_TOPIC_OUTLINE_TEMPLATE.md`
  - 仍适合作为 topic 范围与依赖骨架
- `docs/templates/IGCSE_QA_TEMPLATE.md`
  - 仍适合作为单 topic QA 文件骨架
- `docs/IGCSE_NAMING_CONVENTION_2026-06-19.md`
  - 目录、topic、文件命名规则仍成立
- `docs/IGCSE_BATCH_DELIVERY_SPEC_2026-06-19.md`
  - 批次思路仍成立，但需要在大规模场景下加 manifest 与批次依赖
- `docs/IGCSE_REVIEW_PREFLIGHT_CHECKLIST_2026-06-19.md`
  - 仍可用，但需要补题量级自查项

### 不够用的部分

当 QA 从“每 topic 一份说明型文件”升级到“200-300 题题库化”时，现有资产缺 3 类关键控制面：

1. 题级编号规范
2. 全量 QA 索引 manifest
3. 批次间依赖与冻结规则

## 新增资产

- `docs/IGCSE_QA_BANK_SCALING_SPEC_2026-06-19.md`
- `docs/IGCSE_QA_NUMBERING_CONVENTION_2026-06-19.md`
- `docs/IGCSE_BATCH_DEPENDENCY_SPEC_2026-06-19.md`
- `docs/templates/IGCSE_QA_MANIFEST_TEMPLATE.csv`

## 推荐数据组织方式

仍保留：

- `content/<subject-slug>/topic-outline.md`
- `content/<subject-slug>/qa/*.md`

大规模时新增：

- `content/<subject-slug>/qa-manifest.csv`

作用：

- 作为题库总索引
- 追踪每个 topic 的题量
- 追踪批次、依赖、review 状态、责任人

## 生产建议

1. 先定 `topic-outline.md`
2. 再定 `qa-manifest.csv` 初稿，给出 topic -> 题量预算 -> 批次分配
3. 再批量生成 QA 文件
4. 每次交付 review 时，以 manifest 为准更新状态

## 对 Accounting 200-300 QA 的直接建议

- 不建议只靠文件名和目录人工追踪
- 必须上 manifest
- 必须固定题级编号规则
- 必须定义 batch freeze 规则，避免前批改 ID 后批全部漂移
