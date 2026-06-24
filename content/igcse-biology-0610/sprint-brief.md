# Sprint Brief: IGCSE Biology 0610
**Node:** 1 → 2 (Subject Intake & Gap Scan — revised)
**Date:** 2026-06-22
**Worker:** worker_course

## Outline Status
- **topic-outline.md:** ✅ 完整，44 topics（Core + Supplement），19 domains
- **QQL 文件：** 全部 44 topics × 9 QQL = 396 个文件 ✅ 数量完整

## QA Gap Analysis

### Topics 1.1–15.2 (34 topics) — COMPLETE ✅
- 每个 topic 9 QQL 文件，F:2|S:4|C:3 分布合理
- item 文件完整
- **无需操作**

### Topics 16.1–19.2 (10 topics) — DIFFICULTY IMBALANCE ⚠️
数量完整（各9个 QQL），但 difficulty label 严重失衡：

| Topic | 当前分布 | 目标 F:2/S:4/C:3 | 缺口 | 修正方式 |
|-------|---------|-----------------|------|---------|
| 16.1 | F:1 S:6 C:2 | F:2 S:4 C:3 | F+1, S+2, C+1 | label调整 |
| 16.2 | F:0 S:8 C:1 | F:2 S:4 C:3 | F+2, S+4 | label调整 |
| 16.3 | F:1 S:7 C:1 | F:2 S:4 C:3 | F+1, S+3, C+2 | label调整 |
| 17.1 | F:0 S:6 C:3 | F:2 S:4 C:3 | F+2, S+2 | label调整 |
| 17.2 | F:0 S:9 C:0 | F:2 S:4 C:3 | F+2, C+3, S-5 | label调整 |
| 17.3 | F:0 S:9 C:0 | F:2 S:4 C:3 | F+2, C+3, S-5 | label调整 |
| 18.1 | F:0 S:6 C:3 | F:2 S:4 C:3 | F+2, S+2 | label调整 |
| 18.2 | F:0 S:7 C:2 | F:2 S:4 C:3 | F+2, S+3, C+1 | label调整 |
| 19.1 | F:0 S:8 C:1 | F:2 S:4 C:3 | F+2, S+4, C+2 | label调整 |
| 19.2 | F:0 S:7 C:2 | F:2 S:4 C:3 | F+2, S+3, C+1 | label调整 |

**关键问题：** 10 个 topic 全缺 Foundation（应为 F:2 各），4 个 topic 全缺 Challenge

## Sprint Target
1. **Batch 1（6 topics）：** 16.1 / 16.2 / 16.3 / 17.1 / 17.2 / 17.3
2. **Batch 2（4 topics）：** 18.1 / 18.2 / 19.1 / 19.2
3. **操作：** 仅调整 QQL 文件中 `**Difficulty**: X` 标签，不改题目内容
4. **命名：** QQL 文件已存在，直接修改标签
5. **Manifest：** 更新 difficulty_mix 字段

## Next Node
→ Node 3: QA Generation（Label Fix）→ Node 4: review_course 审查
