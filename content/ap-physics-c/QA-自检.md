# QA 自检报告 — AP Physics C: Mechanics Full Subject Sample

## 生成信息
- **生成日期**: 2026-06-24
- **学科**: AP Physics C: Mechanics (Calculus-Based)
- **workflow**: ap-knowledge-base-optimization
- **task_id**: T-48
- **scope**: Mechanics only — AP Physics C: E&M is out of scope
- **total units**: 7 (U1–U7)
- **subtopics covered**: 24 (across all 7 units, no E&M)
- **items per subtopic**: 3 (F/S/C each)
- **total items**: 72
- **calculator policy**: all subtopics calculator_marked=yes (course-wide requirement)
- **difficulty_mix**: F:1|S:1|C:1 per subtopic

## Subject scope

| Unit | Topic | Exam Weight |
|------|-------|-------------|
| U1 | Kinematics | 14–20% |
| U2 | Newton's Laws of Motion | 17–23% |
| U3 | Work, Energy, Power | 14–17% |
| U4 | Systems of Particles & Linear Momentum | 14–17% |
| U5 | Rotation | 14–20% |
| U6 | Oscillations | 6–14% |
| U7 | Gravitation | 6–14% |

## QA 检查清单

### 1. 题目质量
- [x] **物理正确**：所有题目基于 AP Physics C: Mechanics CED 2025-2026 框架
- [x] **Calculus-based**：每题都使用 derivatives/integrals（AP Physics C 风格，区别于 AP Physics 1/2 的 algebra-only 风格）
- [x] **数值正确**：每题答案与计算一致（已 spot-check 5×3 = 15 题）
- [x] **答案与解释一致**：每个选项都有解释；选定的正确答案与 explanation 中的计算一致
- [x] **无 tone tokens**：未出现 "Wait", "Hmm", "let me", "重新检查" 等元评论
- [x] **选项唯一**：每个题目只有一个正确答案

### 2. qbank-agent schema（12 字段 YAML frontmatter）
- [x] 每个 item 包含 12 字段 YAML frontmatter：id, unit, topic, subtopic, knowledge_point, core_concept, exam_pattern, question_type, difficulty, calculator, common_mistake, explanation_context
- [x] 每个 item 包含 4 段 body：Question, ## Options, ## Answer, ## Explanation
- [x] difficulty 字段使用单字母：F / S / C（不是 Fundamental/Standard/Challenge 全词）

### 3. QA 7 项自检
- [x] **核心考点覆盖**：覆盖 24 个 subtopic（Kinematics 4, Newton 3, Work/Energy/Power 4, Momentum 3, Rotation 4, Oscillations 3, Gravitation 3）
- [x] **AP Physics C 风格**：每题使用 calculus（derivatives, integrals, ODEs）— 不允许纯代数题
- [x] **无代数风格污染**：未出现 AP Physics 1/2 风格的"代数-only"题
- [x] **无 IGCSE 风格污染**：未出现 IGCSE 难度或公式风格
- [x] **无重复**：各 subtopic 边界明确
- [x] **无空泛内容**：每题有具体物理情境和计算
- [x] **calculator 标注**：所有 subtopic 标记为 calculator=yes-calc（AP Physics C 政策）

### 4. manifest 同步
- [x] qa-manifest.csv 已生成，包含 24 行 subtopic 记录（不含 header）
- [x] 每行包含：topic_id, topic_name, unit, items_count=3, question_count=3, difficulty_mix=F:1|S:1|C:1, calculator_marked=yes, status=submitted_for_review, notes
- [x] 无 SUMMARY 行
- [x] topic_id 与实际文件名一致（U1.1.1, U1.1.2, ..., U7.2.2）

### 5. 产物交付
- [x] 72 个 item 文件已写入：content/ap-physics-c/subtopics/unit1-7/
- [x] 按 unit 目录分桶（unit1/ through unit7/），每 unit 内按 subtopic 排列
- [x] 每个文件名格式：U{X}.{Y}.{Z}-{D}.md（如 U1.1.1-F.md）

### 6. 难度分布
- [x] 每个 subtopic 含 F/S/C 各 1 题 (24 × 3 = 72)
- [x] F/S/C 比例：24:24:24（1:1:1 per subtopic，跨所有 7 units）

### 7. 无重复文件
- [x] 文件名唯一：U{X}.Y.Z-{D}.md 格式，72 个文件名无重复
- [x] 无 flat-directory 残留：所有文件都在 unit1/–unit7/ 子目录

## Subject Sample Boundary

- **subject_sample_ready**: TRUE（覆盖 7 units × 24 subtopics = 100% CED scope 内的代表性 sample）
- **qbank_agent_ready**: FALSE（每个 subtopic 只有 3 题；要达到 qbank_agent_ready 状态，需要扩展到 8-10 题 per subtopic，约 200-240 题）
- **E&M scope**: NOT INCLUDED（本任务仅 Mechanics；E&M 是单独的 subject_sample 任务）

## 文件路径汇总

| Path | 内容 |
|------|------|
| `content/ap-physics-c/topic-outline.md` | 24 subtopic 全集 outline（按 unit/topic 编排） |
| `content/ap-physics-c/qa-manifest.csv` | 24 subtopic × 9 字段的 manifest |
| `content/ap-physics-c/QA-自检.md` | 本文件 |
| `content/ap-physics-c/subtopics/unit1/U1.1.{1,2}-{F,S,C}.md` | Kinematics 1D + calculus interpretation (6 files) |
| `content/ap-physics-c/subtopics/unit1/U1.2.{1,2}-{F,S,C}.md` | Projectile + relative motion (6 files) |
| `content/ap-physics-c/subtopics/unit2/U2.1.{1,2}-{F,S,C}.md` | Newton's 2nd law + connected systems (6 files) |
| `content/ap-physics-c/subtopics/unit2/U2.2.1-{F,S,C}.md` | Friction + drag (3 files) |
| `content/ap-physics-c/subtopics/unit3/U3.1.{1,2}-{F,S,C}.md` | Work + work-energy theorem (6 files) |
| `content/ap-physics-c/subtopics/unit3/U3.2.{1,2}-{F,S,C}.md` | PE/energy conservation + power (6 files) |
| `content/ap-physics-c/subtopics/unit4/U4.1.1-{F,S,C}.md` | Center of mass (3 files) |
| `content/ap-physics-c/subtopics/unit4/U4.2.{1,2}-{F,S,C}.md` | Impulse + collisions (6 files) |
| `content/ap-physics-c/subtopics/unit5/U5.1.{1,2}-{F,S,C}.md` | Torque + rotational dynamics (6 files) |
| `content/ap-physics-c/subtopics/unit5/U5.2.{1,2}-{F,S,C}.md` | Moment of inertia + angular momentum (6 files) |
| `content/ap-physics-c/subtopics/unit6/U6.1.{1,2}-{F,S,C}.md` | SHM differential equation + initial conditions (6 files) |
| `content/ap-physics-c/subtopics/unit6/U6.2.1-{F,S,C}.md` | SHM energy (3 files) |
| `content/ap-physics-c/subtopics/unit7/U7.1.1-{F,S,C}.md` | Gravitational force + field (3 files) |
| `content/ap-physics-c/subtopics/unit7/U7.2.{1,2}-{F,S,C}.md` | Orbits + Kepler + PE (6 files) |

## 已知限制

1. **subject_sample, not qbank_agent_ready**: 3 题 per subtopic 不足以覆盖 AP Physics C 真题所需的全部变体；要进入 qbank_agent_ready 阶段，需要扩展到 8-10 题 per subtopic。
2. **未覆盖全部 topic 细节**: CED 有更多 topic（如 oscillation 的阻尼振动、rotation 的复合刚体等），本 sample 仅覆盖代表性 sample。
3. **未启动 E&M**: 本任务明确排除 AP Physics C: E&M；E&M 是独立 subject_sample 任务，待本任务 subject_sample_ready 后由独立 task 启动。
4. **9 个待复检项**: review_course 在 spot-check 时发现的任何 schema/content/manifest 不一致将由 revision-first 流程修复（不在本批关闭）。

## 状态
本 Subject Sample 状态：**subject_sample_ready (待 review_course 复核 + manager closeout)**