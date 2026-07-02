# unit1 题目 QA 自检报告

## 基本信息
- **单元**: unit1
- **子主题数**: 6
- **题目总数**: 18
- **难度分布**: F:6 | S:6 | C:6（每 subtopic F/S/C 各 1）
- **生成日期**: 2026-06-25
- **状态**: 已完成 (complete)

## QA 七项自检

- [x] 1. 题目质量：数学正确、答案与解释一致、无 tone tokens、选项唯一
- [x] 2. schema 字段完整：每个 item 含 id/difficulty/calculator/type frontmatter 及 Options/Answer/Explanation
- [x] 3. 题目与知识点对应：每题明确 targeting 对应 subtopic
- [x] 4. 难度分布：每个 subtopic 恰好含 F/S/C 各 1 题
- [x] 5. manifest 同步：qa-manifest.csv 行数 = subtopics 数，按 subtopics/ 层索引
- [x] 6. 选项设计：每题 4 选项 MCQ，有且仅有 1 个正确选项
- [x] 7. 无元评论：题目文本不含 Wait/Hmm 等 meta commentary，无 SUMMARY 行，无重复文件

## 子主题清单

- U1.1.1 (Converting between moles and particles using Avogadro's number)
- U1.3.1 (Calculate percent composition from molecular formula)
- U1.4.1 (Calculate mass of an element in a mixture component)
- U1.5.1 (Write ground-state electron configuration for neutral atoms)
- U1.6.1 (Relate PES peak position to binding energy and peak height to number of electrons)
- U1.7.1 (Predict relative atomic radius based on periodic position)

## 路径
- 代码库: `content/ap-chemistry/subtopics/unit1/`
- Manifest: `content/ap-chemistry/qa-manifest.csv`

## 状态标记

**状态：已完成 (complete)** — 7 项自检全部通过，共 18 题（6 subtopics × 3），manifest 行数已对齐 subtopics。
