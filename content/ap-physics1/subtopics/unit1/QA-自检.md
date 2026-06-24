# QA 自检报告 — AP Physics 1 Unit 1 题库

## 生成信息
- **生成日期**: 2026-06-23
- **单元**: Unit 1 - Kinematics
- **子主题数**: 15 (U1.1.1 ~ U1.5.4)
- **每子主题题数**: 3 (F/S/C 各 1)
- **总题数**: 45

## QA 检查清单

### 1. 题目质量
- [x] 物理正确：所有题目基于 AP Physics 1 CED 2025-2026 框架，物理原理正确
- [x] 数值正确：计算题经过验证，答案与解释一致
- [x] 答案与解释一致：每个选项都有明确解释
- [x] 无 tone tokens：未出现 "Wait", "Hmm", "let me", "重新检查", "不在选项" 等元评论
- [x] 选项唯一：每个题目只有一个正确答案，无等价选项

### 2. qbank-agent schema
- [x] 每个 item 显式包含：unit, topic, subtopic, knowledge_point, core_concept, exam_pattern, question_type, common_mistake, difficulty, explanation_context

### 3. QA 7 项自检
- [x] 核心考点覆盖：涵盖 Unit 1 全部 15 个子主题
- [x] 无明显遗漏：每个子主题 F/S/C 各 1 题
- [x] 无重复：各子主题边界明确，题目内容不重复
- [x] 无空泛内容：每题有具体物理情境和计算
- [x] 能支持自动出题：frontmatter 包含完整元数据
- [x] 能支持题目解析：core_concept 和 explanation_context 提供充分依据
- [x] 能支持错因诊断：common_mistake 对应常见错误类型

### 4. manifest 同步
- [x] 已生成 qa-manifest.csv，包含 15 行 Unit 1 subtopic 记录
- [x] 已复制到 Obsidian 目标路径

### 5. 产物交付
- [x] 45 个 item 文件已写入：/Volumes/Halobster/Codex相关/EduFlow-Team-orch/content/ap-physics1/subtopics/unit1/
- [x] 45 个 item 文件已复制到：/Volumes/Halobster/Obsidian Edu/留学公司知识库/01-留学课程通用知识/03-AP知识库/03-学科知识/AP Physics 1/02-题库/items/Unit 1/

### 6. 难度分布
- [x] 每个子主题含 F/S/C 各 1 题 (15 × 3 = 45)

### 7. 无重复文件
- [x] 文件名唯一：U1.X.Y-D.md 格式，无重复

## 文件清单

| 子主题 | F 题 | S 题 | C 题 |
|--------|------|------|------|
| U1.1.1 标量与矢量 | U1.1.1-F.md | U1.1.1-S.md | U1.1.1-C.md |
| U1.1.2 位置-时间关系 | U1.1.2-F.md | U1.1.2-S.md | U1.1.2-C.md |
| U1.1.3 符号约定与参考系 | U1.1.3-F.md | U1.1.3-S.md | U1.1.3-C.md |
| U1.2.1 矢量分解与合成 | U1.2.1-F.md | U1.2.1-S.md | U1.2.1-C.md |
| U1.2.2 二维位移与速度 | U1.2.2-F.md | U1.2.2-S.md | U1.2.2-C.md |
| U1.2.3 相对速度 | U1.2.3-F.md | U1.2.3-S.md | U1.2.3-C.md |
| U1.3.1 抛体运动基本假设 | U1.3.1-F.md | U1.3.1-S.md | U1.3.1-C.md |
| U1.3.2 飞行时间/最大高度/射程 | U1.3.2-F.md | U1.3.2-S.md | U1.3.2-C.md |
| U1.3.3 平抛与斜抛速度分析 | U1.3.3-F.md | U1.3.3-S.md | U1.3.3-C.md |
| U1.4.1 惯性参考系 | U1.4.1-F.md | U1.4.1-S.md | U1.4.1-C.md |
| U1.4.2 伽利略变换 | U1.4.2-F.md | U1.4.2-S.md | U1.4.2-C.md |
| U1.5.1 x-t 图像 | U1.5.1-F.md | U1.5.1-S.md | U1.5.1-C.md |
| U1.5.2 v-t 图像 | U1.5.2-F.md | U1.5.2-S.md | U1.5.2-C.md |
| U1.5.3 a-t 图像与互转 | U1.5.3-F.md | U1.5.3-S.md | U1.5.3-C.md |
| U1.5.4 线性化与实验数据 | U1.5.4-F.md | U1.5.4-S.md | U1.5.4-C.md |

## 状态
**submitted_for_review**
