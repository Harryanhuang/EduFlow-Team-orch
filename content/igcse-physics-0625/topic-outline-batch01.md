# IGCSE Physics (0625) Topic Outline

基于 Cambridge IGCSE Physics (0625) 现行 syllabus。
首批仅覆盖 Core 段 4 个基础 topic，不扩展到 Extended。

## 知识领域概览

| 编号 | 领域 | Topic 数量 |
|------|------|------------|
| 1 | General physics | 4 |
| **总计** | | **4** |

## Topic 列表

### 1 — Measurement & motion

| ID | Topic | Core/Extended | 前置 |
|----|-------|---------------|------|
| 1.1 | Physical quantities, SI units, measuring length and time | Core | 无 |
| 1.2 | Speed, velocity, acceleration, distance-time and speed-time graphs（含 scalars vs vectors 区分、terminal velocity 概念） | Core | 1.1 |

### 2 — Forces & energy

| ID | Topic | Core/Extended | 前置 |
|----|-------|---------------|------|
| 2.1 | Mass, weight, density, force as push/pull, Hooke's law（含 W=mg 计算、mass vs weight 对比表） | Core | 1.1 |
| 2.2 | Work, energy, power, energy resources and conversion | Core | 1.2, 2.1 |

## 字段规范

- `ID`: 章节式 ID（`1.1`, `1.2`, `2.1`...），对应 QA 文件名中 `.` 转 `-`
- `Topic`: 英文官方或接近官方表述
- `Core/Extended`: Core 仅，后续批次可扩展 Supplement
- `前置`: 仅填真实依赖；没有则写 `无`

## 产出约束

- topic-outline 只定义范围、层级、先修、覆盖关系
- 不在 outline 中写长篇教学解释
- 每个 outline 条目都必须能一一映射到一个 QA 文件

## QA 配套

每个 topic 对应一份 QA 文件，详见 `qa/` 目录。
首批 4 个 topic 对应 QA 文件命名约定：
- `1-1-physical-quantities-measurement.md`
- `1-2-speed-velocity-acceleration-graphs.md`
- `2-1-mass-weight-density-force-hooke.md`
- `2-2-work-energy-power-resources.md`
