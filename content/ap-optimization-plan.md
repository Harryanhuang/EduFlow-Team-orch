# AP 学科知识点优化计划

> 扫描日期：2026-06-22
> 扫描人：worker_course
> 范围：content/ 目录下所有 AP 相关学科

---

## 1. 扫描结果：AP 学科现状

| 指标 | 结果 |
|------|------|
| 仓库中 AP 学科数 | **0** |
| AP 相关 content 目录 | **无** |
| AP 相关 manifest 条目 | **无** |
| AP 相关 QQL / items / outline | **无** |

**结论：AP 学科为完全 greenfield，所有内容需从零启动。**

---

## 2. AP 课程体系分析与优先级建议

基于 College Board 官方 AP 课程目录和国内市场需求，建议按以下优先级启动：

### Tier 1 — 高需求（首波启动）

| 学科 | College Board 代码 | 预估 Topics | 预估 Items | 优先级理由 |
|------|-------------------|------------|-----------|-----------|
| **AP Calculus AB** | MAT-101 | ~24 | ~400 | 报考人数最多，中国学生刚需 |
| **AP Calculus BC** | MAT-102 | ~32 | ~550 | AB 的超集，额外 Topics 10 项 |
| **AP Physics 1** | PHY-101 | ~28 | ~500 | 新考纲（2024-25），需求强劲 |
| **AP Chemistry** | CHE-101 | ~30 | ~550 | 与 IGCSE 0620 有衔接基础 |
| **AP Computer Science A** | CS-101 | ~20 | ~350 | 已有 0478 基础，可快速复用 |
| **AP Statistics** | STA-101 | ~26 | ~450 | 报考人数 Top 5，跨学科需求 |

### Tier 2 — 中需求（第二波）

| 学科 | College Board 代码 | 预估 Topics | 预估 Items | 优先级理由 |
|------|-------------------|------------|-----------|-----------|
| **AP Biology** | BIO-101 | ~30 | ~550 | 与 IGCSE 0610 有衔接基础 |
| **AP Macroeconomics** | ECO-101 | ~22 | ~400 | 文科类热门 |
| **AP Microeconomics** | ECO-102 | ~22 | ~400 | 与 Macro 共享基础概念 |
| **AP English Language** | ENG-101 | ~18 | ~300 | 写作类 AP，需求稳定 |

### Tier 3 — 低需求/长尾（后续按需）

| 学科 | College Board 代码 | 预估 Topics | 预估 Items | 备注 |
|------|-------------------|------------|-----------|------|
| AP Physics 2 | PHY-102 | ~24 | ~450 | 依赖 Physics 1 基础 |
| AP Physics C: Mechanics | PHY-103 | ~16 | ~300 | 需 Calculus 前置 |
| AP Physics C: E&M | PHY-104 | ~18 | ~350 | 需 Calculus + Physics C: Mech 前置 |
| AP Environmental Science | ENV-101 | ~20 | ~350 | 跨学科综合 |
| AP Psychology | PSY-101 | ~24 | ~400 | 文科类稳定需求 |
| AP US History | HIS-101 | ~30 | ~500 | 中国市场需求有限 |
| AP World History | HIS-102 | ~28 | ~450 | 中国市场需求有限 |

---

## 3. 每学科扩产目标与标准

参考 IGCSE 0478 冲刺经验（28 topics × 18 items = 504），AP 学科建议标准：

| 参数 | IGCSE 标准 | AP 标准 |
|------|-----------|--------|
| Topics 覆盖 | 8 groups, 28 subtopics | 6-10 units, 20-32 topics |
| Items per topic | 18 (F:6\|S:6\|C:6) | **15-20** (F:5\|S:7\|C:5~8) |
| QQL per topic | 9 questions (3F\|3S\|3C) | **9-12 questions** (3F\|3-5S\|3-4C) |
| 难度分布 | F:2\|S:4\|C:3 | **F:2\|S:4\|C:4** (AP 更重 Challenge) |
| topic outline | ✅ required | ✅ required (College Board CED format) |
| qa-manifest.csv | ✅ required | ✅ required |

### AP 难度说明
- **F (Foundation)**: 概念识别、定义回忆、基础计算
- **S (Standard)**: 标准题型、多步骤计算、概念应用
- **C (Challenge)**: FRQ 级别、综合分析、跨知识点整合

---

## 4. Workflow 规划

### 阶段 1 — 基础建设（每学科）

```
1. 创建 content/ap-<subject-code>/ 目录结构
   ├── topic-outline.md (College Board CED format)
   ├── qa-manifest.csv
   ├── items/
   ├── qa-question-level/
   └── qa/ (syllabus-level topic descriptions)

2. 编写 topic-outline.md
   - 按 College Board Course and Exam Description (CED) 的 Units/TTopics 结构
   - 标注每个 Topic 的 Exam Weighting
   - 标注 Core/Extension（如有）

3. 初始化 qa-manifest.csv
   - 参照 IGCSE 格式：topic_id, topic_title, unit, question_count, difficulty_mix, status
```

### 阶段 2 — 批量生产（每学科）

```
4. 按 Topic 批次生产 items + QQL
   - 每批 4-6 topics（与 IGCSE 冲刺节奏一致）
   - 每 topic: 15-20 items + 9-12 QQLs
   - 难度分布 F:2|S:4|C:4

5. 每批完成送 review_course 复核
   - QQL → items 对齐检查
   - 难度分布验证
   - Tone 检查（无 self-correction 语言）
```

### 阶段 3 — 质量闭环

```
6. 全学科完成后 truth audit
   - 全 topics 难度一致性
   - items 与 QQL 对应关系
   - syllabus coverage 完整性

7. 跨学科关联检查
   - AP Calc BC vs AP Calc AB 重叠 Topics
   - AP Physics 1 vs AP Physics C 重叠 Topics
   - 知识迁移路径
```

---

## 5. 首批启动建议（Phase 0 Sprint）

建议先启动 **3 个学科** 作为 Phase 0 验证 workflow：

| 学科 | 目录名 | Topics | Items | 启动理由 |
|------|--------|--------|-------|---------|
| **AP Calculus AB** | `content/ap-calculus-ab` | 24 | ~400 | 报考人数最多，workflow 验证最佳候选 |
| **AP Computer Science A** | `content/ap-csa` | 20 | ~350 | 已有 IGCSE 0478 基础，可快速启动 |
| **AP Chemistry** | `content/ap-chemistry` | 30 | ~550 | 已有 IGCSE 0620 基础，可复用部分概念 |

### 预计工作量

| 学科 | Topics | Items (15-20/Topic) | QQLs (9-12/Topic) | 预估工时 |
|------|--------|---------------------|-------------------|---------|
| AP Calculus AB | 24 | ~400 | ~240 | 2-3 days |
| AP CSA | 20 | ~350 | ~200 | 2 days |
| AP Chemistry | 30 | ~550 | ~300 | 3-4 days |
| **Phase 0 合计** | **74** | **~1300** | **~740** | **7-9 days** |

---

## 6. 与 IGCSE 内容的衔接关系

```
IGCSE 0620 (Chemistry)  ──→  AP Chemistry (部分知识点复用)
IGCSE 0610 (Biology)    ──→  AP Biology (部分知识点复用)
IGCSE 0580 (Math)       ──→  AP Calculus AB/BC (代数基础)
IGCSE 0478 (Comp Sci)   ──→  AP CSA (编程基础)
IGCSE 0625 (Physics)    ──→  AP Physics 1 (物理基础)
IGCSE 0452 (Accounting) ──→  AP Microeconomics (商业基础)
IGCSE 0455 (Economics)  ──→  AP Macro/Micro (经济基础)
```

衔接策略：已有 IGCSE items 中的基础概念（如二进制、化学方程式、物理公式）可在 AP 中适当引用或复用，减少重复生产。

---

## 7. 目录结构规划

```
content/
├── ap-calculus-ab/          # AP Calculus AB
│   ├── topic-outline.md     # College Board CED format
│   ├── qa-manifest.csv
│   ├── items/
│   │   ├── topic_1.1.md     # Unit 1: Limits and Continuity
│   │   ├── topic_1.2.md
│   │   └── ...
│   ├── qa-question-level/
│   │   ├── topic_1.1.md
│   │   └── ...
│   └── qa/                  # Syllabus-level topic descriptions
├── ap-csa/                  # AP Computer Science A
├── ap-chemistry/            # AP Chemistry
├── ap-physics-1/            # AP Physics 1 (Phase 1)
├── ap-statistics/           # AP Statistics (Phase 1)
├── ap-calculus-bc/          # AP Calculus BC (Phase 1)
└── ...                      # Phase 2+ subjects
```

---

## 8. 风险与依赖

| 风险 | 缓解措施 |
|------|---------|
| AP 考纲更新（College Board 每年微调） | 使用最新 CED（2024-25），定期比对更新 |
| 难度分布不当（AP 比 IGCSE 更难） | C 类比例从 3→4，增加综合分析题 |
| FRQ 格式适配 | AP 有 Free Response Questions，需要特殊 item 格式 |
| 跨学科依赖 | Calculus BC 依赖 AB；Physics C 依赖 Calculus |

---

## 9. 下一步行动

1. **确认首批 3 学科**（Calculus AB / CSA / Chemistry）
2. **启动 Calculus AB 的 topic-outline.md**（按 College Board CED）
3. **建立 AP 专属 items 模板**（增加 FRQ 标记字段）
4. **开始 Phase 0 批量生产**

---

*本计划由 worker_course 产出，基于 IGCSE 0478 冲刺经验（28 topics × 18 items = 504）和 College Board 官方课程框架。*
