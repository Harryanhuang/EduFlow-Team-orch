# unit5 题目 QA 自检报告

## 基本信息
- **单元**: unit5
- **子主题数**: 3
- **题目总数**: 9
- **难度分布**: F:3 | S:3 | C:3（每 subtopic F/S/C 各 1）
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

- U5.1.1 (中值定理 (MVT))
- U5.1.2 (极值定理 (EVT))
- U5.2.1 (增减性与一阶导数检验)

## 路径
- 代码库: `content/ap-calculus-bc/subtopics/unit5/`
- Manifest: `content/ap-calculus-bc/qa-manifest.csv`

## 状态标记

**状态：已完成 (complete)** — 7 项自检全部通过，共 9 题（3 subtopics × 3），manifest 行数已对齐 subtopics。
