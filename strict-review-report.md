# T-95 Strict Review Report — Boss Format

**reviewer**: review_course
**date**: 2026-07-02
**scope**: 113 skill packages (full sweep)
**method**: review_strict_v2.py — 5-axis independent check (no reuse of prior verdict)

## 总体结论

- **113 总数**: 0 pass / 67 warn / 46 fail
- **P0 阻塞**: 46 个 skill (40.7%)
- **P1 系统性问题**: 67 个 skill (59.3%)
- **最严重类别**: C axis (EK 真实性) 38 个 P0 — 几乎全部 AP 38 skill + 部分 AQA
- **致命 P0**: A axis (源 PDF 错放) 8 个 skill — Biology 9700 包实际指向 Marine Science 9693 PDF

## Top 10 Worst

| # | Skill | Overall | 偏差数 | 主要 P0 |
|---|-------|---------|--------|---------|
| 1 | ap-african-american-studies | fail | 1 | C: PDF 971 LO/EK but 0 real EK |
| 2 | ap-biology | fail | 1 | C: 325 mentions but 0 EK |
| 3 | ap-calculus-ab | fail | 1 | C: 277 mentions but 0 EK |
| 4 | ap-chemistry | fail | 1 | C: 258 mentions but 0 EK |
| 5 | ap-chinese-language-and-culture | fail | 1 | C: 73 mentions but 0 EK |
| 6 | ap-comparative-government-and-politics | fail | 1 | C: 173 mentions but 0 EK |
| 7 | ap-computer-science-a | fail | 1 | C: 177 mentions but 0 EK |
| 8 | ap-english-language-and-composition | fail | 1 | C: 58 mentions but 0 EK |
| 9 | ap-english-literature-and-composition | fail | 1 | C: 67 mentions but 0 EK |
| 10 | ap-environmental-science | fail | 1 | C: 279 mentions but 0 EK |

## 5 维度偏差统计

| Axis | P0 fail | 描述 |
|------|---------|------|
| A. PDF 身份 | 8 | source PDF 放错或 cover subject 不匹配 metadata.subject |
| B. topic/unit 吻合 | 0 (warn 16) | "Why choose this syllabus?" 等通用占位 topic 混入 |
| C. essential_knowledge 真实性 | 38 | 所有 unit 缺 essential_knowledge，PDF 大量 LO/EK 未抽取 |
| D. assessment 结构 | 0 (warn 33) | mcq_count/frq_count/duration_hours 字段缺失 |
| E. 模板污染 | 0 | 无跨体系混淆，但 internal consistency 待查 |

## P0 详情

### P0-A 源 PDF 错放（8 个，必立即修）

| Skill | 实际 PDF | 期望 PDF |
|-------|----------|----------|
| caie-alevel-biology-9700 | Marine Science 9693 | Biology 9700 |
| caie-alevel-computer-science-9618 | ? | Computer Science 9618 |
| caie-alevel-geography-9696 | ? | Geography 9696 |
| caie-igcse-combinedsci-0653 | ? | Combined Science 0653 |
| caie-igcse-compsci-0478 | ? | Computer Science 0478 |
| aqa-ial-computer-science-9645 | ? | AQA CS 9645 |
| aqa-ial-sociology-9690 | ? | AQA Sociology 9690 |
| edexcel-ial-computer-science | ? | Edexcel CS |

修复：每个 skill 重新核对 `metadata.source_provenance[0].local_archive_ref` 指向正确 syllabus PDF。

### P0-C EK 真实性（38 个）

全部 38 个 AP skill + aqa-ial-chemistry-7405 + aqa-ial-economics-9640。修复：每个 unit topic 加 `essential_knowledge: [...]` 数组，从 PDF EK tables 抽取。

## P1 详情

### B axis warn（16 个 CAIE 系）

`topics.json` 含 `1. Why choose this syllabus?` `2. Syllabus overview` `What else you need to know` 等占位 topic。修复：topic tree 只保留 PDF 真正的 content topic，删除 admin/syllabus-overview 段。

### D axis warn（33 个）

`assessment.json` 缺 mcq_count/frq_count/duration_hours 字段。修复：从 PDF Exam Information section 提取。

## 每包详细（sample - 4 worst + 4 high-risk）

### ap-african-american-studies (P0-C)
- field_completeness: {metadata:true, topics:true, assessment:true, skill_md:true, examples:true}
- content_accuracy: fail
- A: pass
- B: pass (no generic topics)
- C: **FAIL** — PDF 971 LO/EK mentions but 0 real EK (empty_ek=13)
- D: pass
- E: pass
- 修复: 抽 971 个 EK from PDF per topic

### caie-alevel-biology-9700 (P0-A + B + C)
- field_completeness: {metadata:true, topics:true, assessment:true, skill_md:true, examples:true}
- content_accuracy: fail
- A: **FAIL** — PDF cover mentions 'marine science' but metadata.subject='biology' (SOURCE MIS-ATTRIBUTED)
- B: warn — generic placeholder topics '1. Why choose this syllabus?' '2. Syllabus overview'
- C: warn — 0 real EK
- D: pass
- E: pass
- 修复: (1) 改 local_archive_ref 指向真 Biology 9700 PDF (found at `/Volumes/Halobster/Obsidian Edu/留学公司知识库/07-公司管理流程通用知识/06-教师培训/参考资料或对应网站/01-CAIE官方考纲与考务/9700 Biology 2025-2027 syllabus.pdf`); (2) 删除 1./2. generic topics; (3) 抽 EK

### caie-alevel-physics-9702 (B + C)
- A: pass
- B: warn — generic placeholder topics
- C: warn — empty_ek=13
- D: pass
- E: pass
- 修复: 删 generic topics + 抽 EK

### aqa-ial-biology-7402 (C)
- A: pass
- B: pass
- C: warn — empty_ek=3 but PDF 37 LO/EK mentions
- D: pass
- E: pass
- 修复: 抽 EK from AQA Biology PDF

## 修复建议

### P0 立即修（46 个）
1. **8 个 PDF 错放**: 重新核对 local_archive_ref → 对应正确 syllabus PDF
2. **38 个 EK 缺失**: worker_syllabus 跑批量抽取脚本，从每个 PDF 的 EK tables 抽 essential_knowledge
3. 复测: review_strict_v2.py 跑过 → 0 P0 才能进 P1 修复阶段

### P1 系统修（67 个）
1. **16 个 CAIE generic topics**: 删 "Why choose this syllabus?" / "Syllabus overview" 等 admin 段
2. **33 个 assessment 字段**: 从 PDF 抽 mcq/frq/duration 填 assessment.json
3. **67 个 EK 抽取**: 同 P0-2

### 优先级
1. 先修 8 个 P0-A（source 错放）— 阻塞整个 review
2. 再修 38 个 P0-C（EK 缺失）— 影响所有 routing
3. 然后修 67 个 P1 一次性批量

## 下一步

- T-95 完成。等 worker_syllabus 修复后用 review_strict_v2.py 复测
- 报告文件: `/Volumes/Halobster/Codex相关/EduFlow-Team-orch/strict-review-report.md`
- JSON 详细: `strict-review-summary.json`
- 脚本: `.claude/skills/review-syllabus-skill/scripts/{review_strict_v2.py,strict_batch_dir.py}`