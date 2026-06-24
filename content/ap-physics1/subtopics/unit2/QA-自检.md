# Unit 2 题目 QA 自检报告

## 基本信息
- **单元**: Unit 2 — Dynamics (Newton's Laws & Forces)
- **子主题数**: 19（原有 9 + Batch 1 gap-fill 10）
- **题目总数**: 57（原有 27 + Batch 1 gap-fill 30）
- **生成日期**: 2026-06-24
- **状态**: submitted_for_review

## QA 检查清单

- [x] 1. 题目质量：物理正确、答案与解释一致、无 tone tokens、选项唯一
- [x] 2. schema 字段完整：每个 item 含 unit/topic/subtopic/knowledge_point/core_concept/exam_pattern/question_type/common_mistake/explanation_context 以及 id/difficulty/calculator/type
- [x] 3. 难度分布：每个 subtopic F:1|S:1|C:1
- [x] 4. manifest 同步（qa-manifest.csv 已追加 19 行 U2 subtopic，无 SUMMARY 行）
- [x] 5. 无重复文件
- [x] 6. 两套编号共存：原有 U2.1.x-U2.3.x 不动，新增 U2.4.x 使用框架编号

## 原有子主题（已 review 通过，保持不动）
- U2.1.1 (Newton's First Law & Inertia) — CED 2.7.1
- U2.1.2 (Newton's Second Law F=ma) — CED 2.7.2
- U2.1.3 (Newton's Third Law) — CED 2.7.3
- U2.2.1 (Free Body Diagrams) — CED 2.6.1
- U2.2.2 (Tension & Connected Objects) — CED 2.6.2
- U2.2.3 (Inclined Plane Analysis) — CED 2.6/2.7
- U2.3.1 (Static Friction) — CED 2.4.1
- U2.3.2 (Kinetic Friction) — CED 2.4.2
- U2.3.3 (Friction on Inclined Planes) — CED 2.4.3

## Batch 1 gap-fill 新增子主题
- U2.4.1 (系统、内力与外力) — CED 2.1.1
- U2.4.2 (质量与重量) — CED 2.1.2
- U2.4.3 (力的分类与叠加) — CED 2.1.3
- U2.4.4 (地表重力与万有引力定律) — CED 2.2.1
- U2.4.5 (重力场与重力加速度) — CED 2.2.2
- U2.4.6 (支持力的本质与计算) — CED 2.3.1
- U2.4.7 (支持力与视重) — CED 2.3.2
- U2.4.8 (胡克定律与弹簧力) — CED 2.5.1
- U2.4.9 (弹簧的串联与并联) — CED 2.5.2
- U2.4.10 (连接体与阿特伍德机) — CED 2.7.4

## 路径
- 代码库: `content/ap-physics1/subtopics/unit2/`
- Manifest: `content/ap-physics1/qa-manifest.csv`
