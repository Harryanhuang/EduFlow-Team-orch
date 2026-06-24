# IGCSE Subject Production Assets

基于本轮 `content/igcse-chemistry-0620/` 与现有 `igcse-mathematics-0580`、`igcse_physics` 产物沉淀的最小复用资产。

## 现有产物观察

- 课程主目录模式：`content/<subject-slug>/`
- topic 总纲文件：`content/<subject-slug>/topic-outline.md`
- QA 目录：`content/<subject-slug>/qa/`
- Chemistry QA 命名：`<chapter>-<topic>-<slug>.md`，例如 `1-1-kinetic-particle-states.md`
- Mathematics QA 命名：`<domain><index>-<slug>.md`，例如 `N1-number-types-sequences.md`
- 共同结构：
  - 先有 `topic-outline.md` 统一定义 topic 列表、先修关系、Core/Extended 范围
  - 再按 topic 拆分 QA 文件
  - QA 文件字段稳定，便于 review 和后续批量生产

## 本轮新增可复用资产

- `docs/templates/IGCSE_TOPIC_OUTLINE_TEMPLATE.md`
- `docs/templates/IGCSE_QA_TEMPLATE.md`
- `docs/IGCSE_NAMING_CONVENTION_2026-06-19.md`
- `docs/IGCSE_BATCH_DELIVERY_SPEC_2026-06-19.md`
- `docs/IGCSE_REVIEW_PREFLIGHT_CHECKLIST_2026-06-19.md`

## 建议放置路径

- 通用模板放 `docs/templates/`
- 通用流程规范放 `docs/`
- 新学科产物仍落在 `content/<subject-slug>/`

## 复用方式

1. 复制 `docs/templates/IGCSE_TOPIC_OUTLINE_TEMPLATE.md` 生成新学科 `content/<subject-slug>/topic-outline.md`
2. 按命名规范确定 topic ID 和 QA 文件名
3. 复制 `docs/templates/IGCSE_QA_TEMPLATE.md` 批量生成 `qa/*.md`
4. 按 `docs/IGCSE_BATCH_DELIVERY_SPEC_2026-06-19.md` 分批提交 review
5. 提交前执行 `docs/IGCSE_REVIEW_PREFLIGHT_CHECKLIST_2026-06-19.md`
