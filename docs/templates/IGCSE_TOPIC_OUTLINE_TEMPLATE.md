# IGCSE <Subject Name> (<Code>) Topic Outline

基于 Cambridge IGCSE `<Subject Name>` (`<Code>`) 现行 syllabus。  
覆盖 `<Core + Supplement / Core + Extended / syllabus-appropriate scope>`。

## 知识领域概览

| 编号 | 领域 | Topic 数量 |
|------|------|------------|
| `<Domain1>` | `<Domain Name>` | `<count>` |
| `<Domain2>` | `<Domain Name>` | `<count>` |
| **总计** | | `<<total>>` |

## Topic 列表

### `<Domain1>` — `<Domain Name>`

| ID | Topic | Core/Extended | 前置 |
|----|-------|---------------|------|
| `<1.1 / N1 / P1>` | `<Topic Name>` | `<Core / Extended / Core+Extended>` | `<无 / prereq ids>` |
| `<1.2 / N2 / P2>` | `<Topic Name>` | `<Core / Extended / Core+Extended>` | `<prereq ids>` |

### `<Domain2>` — `<Domain Name>`

| ID | Topic | Core/Extended | 前置 |
|----|-------|---------------|------|
| `<ID>` | `<Topic Name>` | `<tier>` | `<prereq ids>` |

## 字段规范

- `ID`:
  - 自然科学优先用章节式：`1.1`, `1.2`, `2.1`
  - 数学等字母域学科可用：`N1`, `A2`, `G4`
- `Topic`: 英文官方或接近官方表述，必要时可在 QA 中补中文
- `Core/Extended`: 用该学科 syllabus 实际层级命名；不要混写非官方标签
- `前置`: 仅填真实依赖；没有则写 `无`

## 产出约束

- topic-outline 只定义范围、层级、先修、覆盖关系
- 不在 outline 中写长篇教学解释
- 每个 outline 条目都必须能一一映射到一个 QA 文件

## QA 配套

每个 topic 对应一份 QA 文件，详见 `qa/` 目录。
