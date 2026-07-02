---
name: subject-knowledge-base-structure
description: 学科知识库标准目录结构、内容规范与工作流程（跨课程体系：A-Level/IGCSE/IB/AP/DSE）。worker_course 生产知识页、review_course 验收时必须遵循此标准。
---

## 工作流程（大段任务模式）

```
manager 派单
    ↓
worker_course 独立完成全部内容 → 汇报 manager
    ↓
manager 开启 review_course 复核
    ↓
review_course 发现问题 → 反馈 manager → manager 派 worker_course 修复
    ↓（循环直到标准达成）
review_course 确认达标 → 收尾声明 + 建议下一个学科 + 提出 skill 沉淀意见
    ↓
manager 分发下一步任务执行
```

**各角色职责**：
- **worker_course**：接单后独立完成，不等 review 介入，完成后一次性汇报 manager
- **review_course**：manager 主动触发才介入，给出具体问题清单，确认达标后负责收尾+下一科建议+skill意见
- **manager**：调度者，不直接修改内容，负责派单/触发review/分发修复/执行skill沉淀

# 学科知识库结构标准

## 七层通用框架

所有课程体系、所有学科，统一使用以下七层框架：

```
<体系>/<考试局或Level>/<学科(代码)>/
├── 01-索引与总览/
├── 02-课本与考纲/
│   ├── 课本/          ← PDF 源文件，README 记录版本/适用年份
│   ├── 考纲/          ← PDF 源文件（每年一份），README 记录生效年份/主要变化
│   └── 命题分析/      ← 题型分布、评分规律
├── 03-Topic知识点/    ← 核心 RAG 原料层
├── 04-专项资源/
├── 05-知识点分类真题库/
├── 06-知识点分类模拟题库/
└── 99-归档层/
```

## 各体系差异结构

### A-Level — 按考试局分支

```
A-Level/
├── CAIE/Physics (9702)/
│   └── 03-Topic知识点/ → AS/、A2/
└── Edexcel/Physics (IAL)/
    └── 03-Topic知识点/ → Unit 1-6/
```

### IGCSE — 按考试局分支

```
IGCSE/
├── CAIE/Physics (0625)/
│   └── 03-Topic知识点/ → Core Topics/、Extended Topics/
└── Edexcel/Physics (4PH1)/
    └── 03-Topic知识点/ → Core/、Extended/
```

### IB IBDP — 按 SL/HL 分支

```
IB IBDP/Physics/
├── SL/ → 03-Topic知识点/ → Topics A-D（5个核心Topic，字母编号）
└── HL/ → 03-Topic知识点/ → Topics A-D + HL扩展 E-I
```

### AP — 按科目分支

```
AP/Physics/
├── Physics 1/ → 03-Topic知识点/ → Units 1-10/
├── Physics 2/ → 03-Topic知识点/ → Units 1-7/
└── Physics C/
    ├── Mechanics/        → Units 1-7/
    └── Electricity & Magnetism/ → Units 1-5/
```

### DSE — 单一体系

```
DSE/Physics/
└── 03-Topic知识点/ → 必修部分/、选修部分/（M1/M2）
```

## 语言规范（CRITICAL）

### 标题层（Headings）

| 课程体系 | 标题层规范 | 示例 |
|---|---|---|
| AP / A-Level / IGCSE / IB / OSSD / SAT | **中英双语** | `# Kinematics / 运动学` |
| DSE | **繁体中文 + 英文** | `# 運動學 / Kinematics` |

**标题层包括**：
- 文件一级标题（`# Topic Name`）
- 章节标题（`## 1. Definition`、`## 2. Formulae`）
- 子章节标题（`### 1.1 Velocity`）

### 内容层（Body Content）

| 课程体系 | 内容层规范 |
|---|---|
| AP / A-Level / IGCSE / IB / OSSD / SAT | **纯英文** |
| DSE | **繁体中文** |

**内容层包括**：
- 段落正文
- 公式说明
- 例题步骤
- Common Mistakes 说明

**示例（A-Level）**：
```markdown
# Kinematics / 运动学

## 1. Definition / 定义

**Displacement** is the straight-line distance from the starting point to the final position, in a specified direction. It is a vector quantity.

## 2. Formulae / 公式

For constant acceleration:
$$v = u + at$$
where $v$ is final velocity (m/s), $u$ is initial velocity (m/s), ...
```

**示例（DSE）**：
```markdown
# 運動學 / Kinematics

## 1. 定義 / Definition

**位移** 是由起點到終點的直線距離，並具有特定方向。它是向量。

## 2. 公式 / Formulae

對於等加速度運動：
$$v = u + at$$
其中 $v$ 是最終速度 (m/s)，$u$ 是初速度 (m/s)，...
```

---

## Topic 知识页标准（03-Topic知识点 层每个 .md 文件）

### YAML Frontmatter（7个必填字段）

```yaml
---
curriculum: A-Level          # 课程体系
exam_board: CAIE             # 考试局
subject: Physics
subject_code: "9702"
level: A2                    # AS / A2 / SL / HL / Core / Extended 等
topic_number: "26"
stage: A2                    # 与 level 呼应，便于 RAG 过滤
---
```

推荐字段（4个）：`paper_mapping`、`language`、`status`、`tags`

### 正文必须区块

1. **Topic Basics** — exam_board/subject_code/topic_number/level/stage/paper_mapping/status/language
2. **定义** — 使用官方考试局用语（CAIE/IB/College Board wording）
3. **公式** — LaTeX 格式，标注推导条件
4. **Worked Example** — 含完整解题步骤
5. **Common Mistakes** — 独立章节，列高频失分点
6. **Topic Connections** — wiki links，≥5个关联知识点链接

推荐区块：Exam Patterns、实验技能（A-Level P3/P5、IB IA）、Revision Checklist

## Review 验收门控（review_course 必查）

- [ ] YAML frontmatter 7个必填字段全部存在
- [ ] 定义使用官方 exam board 原文（非改写）
- [ ] 公式含 LaTeX，推导条件标注
- [ ] Worked Example 含数字验证
- [ ] Common Mistakes 独立成章节（非混入正文）
- [ ] Topic Connections wiki links ≥5个
- [ ] 文件命名规范：`T{nn}-{Topic-Name}.md`（如 T01-Physical-Quantities.md）

## 各体系差异对照表

| 体系 | 分支维度 | Topic层子目录 | 特殊资源 |
|---|---|---|---|
| A-Level | 考试局 (CAIE/Edexcel) | AS/ A2/ | 实验 P3/P5 |
| IGCSE | 考试局 (CAIE/Edexcel) | Core/ Extended/ | Extended专项 |
| IB | Level (SL/HL) | 字母编号 A-I | IA实验/TOK |
| AP | 科目 (1/2/C-Mech/C-EM) | 数字编号 Units/ | FRQ专项 |
| DSE | 单一 | 必修/ 选修M1/M2/ | SBA校本评核 |
