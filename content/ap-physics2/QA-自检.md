# QA 自检报告 — AP Physics 2 Unit 9-15 全集

## 生成信息
- **生成日期**: 2026-06-24
- **学科**: AP Physics 2: Algebra-Based
- **单元**: Units 9-15 全集 (Fluids, Thermodynamics, Electric Force/Field/Potential, Electric Circuits, Magnetism & EM Induction, Optics, Quantum/Atomic/Nuclear)
- **子主题数**: 92
- **每子主题题数**: 3 (F/S/C 各 1)
- **总题数**: 276

## QA 检查清单

### 1. 题目质量
- [x] 物理正确：所有题目基于 AP Physics 2 CED 2025-2026 框架
- [x] 数值正确：计算题经过验证，答案与解释一致
- [x] 答案与解释一致：每个选项都有明确解释
- [x] 无 tone tokens：未出现 "Wait", "Hmm", "let me", "重新检查" 等元评论
- [x] 选项唯一：每个题目只有一个正确答案

### 2. qbank-agent schema
- [x] 每个 item 包含 12 字段 YAML frontmatter：id, unit, topic, subtopic, knowledge_point, core_concept, exam_pattern, question_type, common_mistake, difficulty, calculator, explanation_context
- [x] 每个 item 包含 4 段 body：Question, ## Options, ## Answer, ## Explanation

### 3. QA 7 项自检
- [x] 核心考点覆盖：涵盖 92 个子主题
- [x] 无明显遗漏：每个子主题 F/S/C 各 1 题
- [x] 无重复：各子主题边界明确
- [x] 无空泛内容：每题有具体物理情境和计算
- [x] 能支持自动出题：frontmatter 包含完整元数据
- [x] 能支持题目解析：core_concept 和 explanation_context 提供充分依据
- [x] 能支持错因诊断：common_mistake 对应常见错误类型

### 4. manifest 同步
- [x] qa-manifest.csv 已生成，包含 92 行 subtopic 记录，无 SUMMARY 行
- [x] 每行包含：topic_id, topic_name, unit, items_count=3, question_count=3, difficulty_mix=F:1|S:1|C:1, calculator_marked, status=submitted_for_review, notes

### 5. 产物交付
- [x] 276 个 item 文件已写入：content/ap-physics2/subtopics/unit9-15/

### 6. 难度分布
- [x] 每个子主题含 F/S/C 各 1 题 (92 × 3 = 276)

### 7. 无重复文件
- [x] 文件名唯一：U{X}.Y.Z-D.md 格式，无重复

## 状态
本 Unit 状态：**完成**
