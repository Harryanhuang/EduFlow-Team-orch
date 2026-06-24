# Unit 4 题目 QA 自检报告

## 基本信息
- **单元**: Unit 4 - Contextual Applications of Differentiation
- **子主题数**: 7 (4.1.1, 4.1.2, 4.1.3, 4.2.1, 4.2.2, 4.3.1, 4.3.2)
- **题目总数**: 21 (每个子主题 F/S/C 各 1 题)
- **生成日期**: 2026-06-23
- **状态**: submitted_for_review

## QA 检查清单

- [x] 1. 题目质量：数学正确、答案与解释一致、无 tone tokens、选项唯一
- [x] 2. qbank-agent schema：每个 item 显式包含 unit/topic/subtopic/knowledge_point/core_concept/exam_pattern/question_type/common_mistake/difficulty/explanation_context
- [x] 3. QA 7 项自检通过
- [x] 4. manifest 同步（7 行 Unit 4 subtopic）
- [x] 5. 产物已交付到 Obsidian 目标路径
- [x] 6. 每个 subtopic 含 F/S/C 各 1 题
- [x] 7. 无重复文件

## 详细检查

### 数学正确性验证

| 题号 | 子主题 | 难度 | 验证结果 |
|------|--------|------|----------|
| U4.1.1-F | 线性近似公式 | F | sqrt(17) ≈ 4 + 1/8 = 4.125 (实际 4.123)，正确 |
| U4.1.1-S | 线性近似公式 | S | e^0.1 ≈ 1 + 0.1 = 1.1，正确 |
| U4.1.1-C | 线性近似公式 | C | ln(1.05) ≈ 0.05，f''(x) < 0 凹向下，高估，正确 |
| U4.1.2-F | 高估与低估 | F | x^2 凹向上，低估，验证 1.2 < 1.21，正确 |
| U4.1.2-S | 高估与低估 | S | sin(x) 在 x=0 附近凹向下，高估，验证 0.1 > 0.0998，正确 |
| U4.1.2-C | 高估与低估 | C | f''(2) = 8 > 0 凹向上，低估，验证 3.5 < 3.541，正确 |
| U4.1.3-F | 微分与误差 | F | dy = 6 × 0.01 = 0.06，正确 |
| U4.1.3-S | 微分与误差 | S | dV = 300 × 0.1 = 30，正确 |
| U4.1.3-C | 微分与误差 | C | dS/S = 2π/100π = 2%，正确 |
| U4.2.1-F | 相关变化率 | F | dA/dt = 2×5×2 = 20，正确 |
| U4.2.1-S | 相关变化率 | S | dr/dt = 4/(36π) = 1/(9π)，正确 |
| U4.2.1-C | 相关变化率 | C | dx/dt=2 时，dD/dt = 18/√5，正确 |
| U4.2.2-F | 相似三角形 | F | r/h = 6/12 = 1/2，正确 |
| U4.2.2-S | 相似三角形 | S | dV/dt=2, h=4 时，dh/dt = 1/(2π)，正确 |
| U4.2.2-C | 相似三角形 | C | 人速 1.6 m/s，影子顶端速率 2.5 m/s，正确 |
| U4.3.1-F | 最优化 | F | x = 50, A = 1250 最大，正确 |
| U4.3.1-S | 最优化 | S | x = (25-√175)/3 ≈ 3.92，正确 |
| U4.3.1-C | 最优化 | C | a=4, b=2, S=4 最小，正确 |
| U4.3.2-F | 二阶检验 | F | f(0)=1, f(2)=-3, f(3)=1，最大值 1，正确 |
| U4.3.2-S | 二阶检验 | S | f(0)=1, f(1)=2, f(2)=1，最小值 1，正确 |
| U4.3.2-C | 二阶检验 | C | f(0)=2, f(1)=6, f(3)=2, f(4)=6，差值 4，正确 |

### 文件清单

**Repo 路径** (`/Volumes/Halobster/Obsidian Edu/留学公司知识库/11-Eduflow Team 多智能体项目/EduFlow-Team-orch/content/ap-calculus-ab/subtopics/unit4/`):
- U4.1.1-F.md, U4.1.1-S.md, U4.1.1-C.md
- U4.1.2-F.md, U4.1.2-S.md, U4.1.2-C.md
- U4.1.3-F.md, U4.1.3-S.md, U4.1.3-C.md
- U4.2.1-F.md, U4.2.1-S.md, U4.2.1-C.md
- U4.2.2-F.md, U4.2.2-S.md, U4.2.2-C.md
- U4.3.1-F.md, U4.3.1-S.md, U4.3.1-C.md
- U4.3.2-F.md, U4.3.2-S.md, U4.3.2-C.md

**Obsidian 路径** (`/Volumes/Halobster/Obsidian Edu/.../AP Calculus AB/02-题库/items/Unit 4/`):
- 同上 21 个文件已同步

### Manifest 更新

在 `qa-manifest.csv` 中追加 7 行：
- U4.1.1 ~ U4.3.2，每行 items_count=3, question_count=3, difficulty_mix=F:1|S:1|C:1

## 注意事项
- 所有题目均为 no-calc 难度
- 所有选项经代数等价性检查，无重复选项
- 无 meta commentary、scratch work 或 tone tokens
- 所有数学公式使用 LaTeX 格式
