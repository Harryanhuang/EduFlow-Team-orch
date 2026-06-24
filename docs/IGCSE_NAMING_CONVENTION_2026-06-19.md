# IGCSE Naming Convention

## 1. 课程目录命名

- 统一格式：`content/<exam>-<subject>-<code>/`
- 推荐示例：
  - `content/igcse-chemistry-0620/`
  - `content/igcse-mathematics-0580/`
  - `content/igcse-physics-0625/`

说明：
- 全部小写
- 单词之间用连字符 `-`
- 末尾带 syllabus code，避免不同版本或近似学科冲突

## 2. topic-outline 命名

- 固定为：`topic-outline.md`

## 3. QA 目录命名

- 固定目录：`qa/`

## 4. Topic ID 规则

- 章节型学科：
  - 用 `1.1`, `1.2`, `2.1` 这种层级 ID
  - QA 文件名中把 `.` 转为 `-`
  - 例如 `1.1` -> `1-1`
- 域字母型学科：
  - 用 `N1`, `A4`, `G3` 这种紧凑 ID

## 5. QA 文件命名

- 通用格式：`<normalized-topic-id>-<topic-slug>.md`
- 示例：
  - `1-1-kinetic-particle-states.md`
  - `7-3-ion-gas-identification.md`
  - `N6-money-finance-indices-surd.md`

规则：
- slug 全小写
- 空格转连字符
- 去掉逗号、冒号、括号等标点
- 保留足够语义，避免过短缩写
- 一个 QA 文件只对应一个 topic

## 6. 批次文件 / 报告命名

- review 或交付说明建议格式：
  - `docs/<date>-<subject-slug>-batch-<nn>-review-note.md`
  - `docs/<date>-<subject-slug>-handoff.md`

## 7. 禁止项

- 不要混用下划线和连字符
- 不要省略 syllabus code
- 不要在同一学科里同时使用 `1.1` 和 `T1` 两套不兼容 ID 体系
- 不要让 QA 文件名与 outline 中 topic ID 对不上
