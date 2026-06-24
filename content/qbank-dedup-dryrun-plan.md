# QBank 同层重复 Dry-Run 去重方案

**日期**: 2026-06-21
**执行者**: worker_qbank
**状态**: DRY-RUN（仅分析，未改动任何文件）

## 总览

| 组 | 学科 | 重复数 | 策略 | 预计移除行数 |
|----|------|--------|------|-------------|
| A | Physics 0625 | 27 | 保留原始 items，从 round2 文件中移除 | ~27 个 Question block |
| B | Chemistry 0620 | 9 | 保留 canonical topic items，从 s2 文件中移除 | ~9 个 Question block |
| C | Biology 0610 | 1 | 保留 round2，从 final-push 中移除 | ~1 个 Question block |
| D | Accounting 0452 | 2 | 保留拆分版，从原合并版中移除 | ~2 个 Question block |
| **合计** | | **39** | | **39 个 Question block** |

---

## 组 A: Physics 0625 — round2 与原始 items 冲突 (27 个)

**根因**: round2 批次生产时使用了与原始 items 相同的 Q-ID，导致同一题目在两个文件中出现。

**策略**: 保留原始 `*-items.md` 中的版本（与 `qa-question-level/` 权威源对齐），从 `*-round2-items.md` 中移除重复 Question block。

**理由**: 原始 items 文件是首次生产的规范文件，round2 是后续补充批次，不应覆盖已有 Q-ID。`qa-question-level/` 单题文件也与原始 items 对齐。

### A1: round1 组 (8 个) — `1-round2-items.md` vs `1-*-items.md`

| Q-ID | 冲突文件 | 保留 | 移除 | 理由 | 内容差异 |
|------|---------|------|------|------|---------|
| Q-1.1-01 | 1-1-items.md (438c) vs 1-round2-items.md (295c) | 1-1-items.md | 1-round2-items.md | 原始版本更完整 | 原始长 143c |
| Q-1.1-02 | 1-1-items.md (333c) vs 1-round2-items.md (444c) | 1-1-items.md | 1-round2-items.md | 保持文件一致性，以原始 items 为准 | round2 长 111c |
| Q-1.2-01 | 1-2-items.md (426c) vs 1-round2-items.md (446c) | 1-2-items.md | 1-round2-items.md | 原始 items 为规范源 | round2 长 20c |
| Q-1.3-01 | 1-3-items.md (337c) vs 1-round2-items.md (406c) | 1-3-items.md | 1-round2-items.md | 同上 | round2 长 69c |
| Q-1.3-02 | 1-3-items.md (336c) vs 1-round2-items.md (384c) | 1-3-items.md | 1-round2-items.md | 同上 | round2 长 48c |
| Q-1.4-01 | 1-4-items.md (287c) vs 1-round2-items.md (395c) | 1-4-items.md | 1-round2-items.md | 同上 | round2 长 108c |
| Q-1.5-01 | 1-5-items.md (349c) vs 1-round2-items.md (260c) | 1-5-items.md | 1-round2-items.md | 同上 | 原始长 89c |
| Q-1.5-02 | 1-5-items.md (275c) vs 1-round2-items.md (407c) | 1-5-items.md | 1-round2-items.md | 同上 | round2 长 132c |

### A2: round2 组 (6 个) — `2-round2-items.md` vs `3-*-items.md`

| Q-ID | 冲突文件 | 保留 | 移除 | 理由 | 内容差异 |
|------|---------|------|------|------|---------|
| Q-3.1-01 | 3-1-items.md (426c) vs 2-round2-items.md (476c) | 3-1-items.md | 2-round2-items.md | 原始 items 为规范源 | round2 长 50c |
| Q-3.2-01 | 3-2-items.md (323c) vs 2-round2-items.md (505c) | 3-2-items.md | 2-round2-items.md | 同上 | round2 长 182c |
| Q-3.3-01 | 3-3-items.md (525c) vs 2-round2-items.md (445c) | 3-3-items.md | 2-round2-items.md | 同上 | 原始长 80c |
| Q-3.4-01 | 3-4-items.md (515c) vs 2-round2-items.md (339c) | 3-4-items.md | 2-round2-items.md | 同上 | 原始长 176c |
| Q-3.5-01 | 3-5-items.md (402c) vs 2-round2-items.md (463c) | 3-5-items.md | 2-round2-items.md | 同上 | round2 长 61c |
| Q-3.6-01 | 3-6-items.md (432c) vs 2-round2-items.md (574c) | 3-6-items.md | 2-round2-items.md | 同上 | round2 长 142c |

### A3: round3 组 (6 个) — `3-round2-items.md` vs `4-*-items.md`

| Q-ID | 冲突文件 | 保留 | 移除 | 理由 | 内容差异 |
|------|---------|------|------|------|---------|
| Q-4.1-01 | 4-1-items.md (285c) vs 3-round2-items.md (346c) | 4-1-items.md | 3-round2-items.md | 原始 items 为规范源 | round2 长 61c |
| Q-4.2-01 | 4-2-items.md (510c) vs 3-round2-items.md (544c) | 4-2-items.md | 3-round2-items.md | 同上 | round2 长 34c |
| Q-4.3-01 | 4-3-items.md (361c) vs 3-round2-items.md (361c) | 4-3-items.md | 3-round2-items.md | 同上，长度一致 | 等长 |
| Q-4.4-01 | 4-4-items.md (420c) vs 3-round2-items.md (321c) | 4-4-items.md | 3-round2-items.md | 同上 | 原始长 99c |
| Q-4.5-01 | 4-5-items.md (400c) vs 3-round2-items.md (527c) | 4-5-items.md | 3-round2-items.md | 同上 | round2 长 127c |
| Q-4.6-01 | 4-6-items.md (372c) vs 3-round2-items.md (500c) | 4-6-items.md | 3-round2-items.md | 同上 | round2 长 128c |

### A4: round4 组 (1 个) — `4-round2-items.md` vs `5-2-items.md`

| Q-ID | 冲突文件 | 保留 | 移除 | 理由 | 内容差异 |
|------|---------|------|------|------|---------|
| Q-5.2-01 | 5-2-items.md (304c) vs 4-round2-items.md (337c) | 5-2-items.md | 4-round2-items.md | 原始 items 为规范源 | round2 长 33c |

### A5: round5 组 (6 个) — `4-round2-items.md` / `5-round2-items.md` vs `5-*-items.md`

> 注意: 部分 Q-ID 同时出现在 3 个文件中（原始 items + 4-round2 + 5-round2），需从两个 round2 文件中都移除。

| Q-ID | 冲突文件 | 保留 | 移除 | 理由 | 内容差异 |
|------|---------|------|------|------|---------|
| Q-5.1-01 | 5-1-items.md (288c) vs 4-round2-items.md (318c) vs 5-round2-items.md (452c) | 5-1-items.md | 4-round2-items.md + 5-round2-items.md | 原始 items 为规范源 | 3-way 冲突 |
| Q-5.3-01 | 5-3-items.md (294c) vs 4-round2-items.md (318c) vs 5-round2-items.md (570c) | 5-3-items.md | 4-round2-items.md + 5-round2-items.md | 同上 | 3-way 冲突 |
| Q-5.4-01 | 5-4-items.md (303c) vs 4-round2-items.md (488c) vs 5-round2-items.md (401c) | 5-4-items.md | 4-round2-items.md + 5-round2-items.md | 同上 | 3-way 冲突 |
| Q-5.5-01 | 5-5-items.md (406c) vs 4-round2-items.md (431c) vs 5-round2-items.md (378c) | 5-5-items.md | 4-round2-items.md + 5-round2-items.md | 同上 | 3-way 冲突 |
| Q-5.6-01 | 5-6-items.md (323c) vs 4-round2-items.md (430c) | 5-6-items.md | 4-round2-items.md | 同上 | round2 长 107c |
| Q-5.7-01 | 5-7-items.md (301c) vs 4-round2-items.md (459c) vs 5-round2-items.md (453c) | 5-7-items.md | 4-round2-items.md + 5-round2-items.md | 同上 | 3-way 冲突 |

### Physics 预计 diff 摘要

- **改动文件**: 5 个 round2 文件 (`1-round2-items.md`, `2-round2-items.md`, `3-round2-items.md`, `4-round2-items.md`, `5-round2-items.md`)
- **移除**: 27 个 Question block（含 4 个 3-way 冲突中的额外移除）
- **不动**: 所有 `*-items.md` 原始文件、`qa-question-level/`、`qa/`

---

## 组 B: Chemistry 0620 — s2 文件与 canonical topic 冲突 (9 个)

**根因**: `5-1-s2-items.md` 和 `5-2-s2-items.md` 是 section-2 补充批次，但错误地使用了 6.1/6.3 topic 的 Q-ID 编号。

**策略**: 保留 `6-1-items.md` 和 `6-3-items.md`（canonical topic 文件），从 `5-1-s2-items.md` 和 `5-2-s2-items.md` 中移除重复 Question block。

**理由**: Q-ID `Q-6.1-*` 和 `Q-6.3-*` 属于 topic 6.1 和 6.3，不应出现在 topic 5.1/5.2 的补充文件中。

### B1: s2-5.1 vs 6.1 (4 个)

| Q-ID | 冲突文件 | 保留 | 移除 | 理由 | 内容差异 |
|------|---------|------|------|------|---------|
| Q-6.1-01 | 6-1-items.md (463c) vs 5-1-s2-items.md (463c) | 6-1-items.md | 5-1-s2-items.md | canonical topic 文件 | **完全一致 (等长)** |
| Q-6.1-02 | 6-1-items.md (558c) vs 5-1-s2-items.md (558c) | 6-1-items.md | 5-1-s2-items.md | 同上 | **完全一致 (等长)** |
| Q-6.1-03 | 6-1-items.md (650c) vs 5-1-s2-items.md (650c) | 6-1-items.md | 5-1-s2-items.md | 同上 | **完全一致 (等长)** |
| Q-6.1-04 | 6-1-items.md (485c) vs 5-1-s2-items.md (485c) | 6-1-items.md | 5-1-s2-items.md | 同上 | **完全一致 (等长)** |

> 4 个均为完全相同的副本，零风险移除。

### B2: s2-5.2 vs 6.3 (5 个)

| Q-ID | 冲突文件 | 保留 | 移除 | 理由 | 内容差异 |
|------|---------|------|------|------|---------|
| Q-6.3-01 | 6-3-items.md (510c) vs 5-2-s2-items.md (421c) | 6-3-items.md | 5-2-s2-items.md | canonical topic 文件 | canonical 长 89c |
| Q-6.3-02 | 6-3-items.md (488c) vs 5-2-s2-items.md (445c) | 6-3-items.md | 5-2-s2-items.md | 同上 | canonical 长 43c |
| Q-6.3-03 | 6-3-items.md (491c) vs 5-2-s2-items.md (492c) | 6-3-items.md | 5-2-s2-items.md | 同上 | 近乎等长 |
| Q-6.3-04 | 6-3-items.md (547c) vs 5-2-s2-items.md (278c) | 6-3-items.md | 5-2-s2-items.md | 同上 | canonical 长 269c |
| Q-6.3-05 | 6-3-items.md (566c) vs 5-2-s2-items.md (348c) | 6-3-items.md | 5-2-s2-items.md | 同上 | canonical 长 218c |

### Chemistry 预计 diff 摘要

- **改动文件**: 2 个 s2 文件 (`5-1-s2-items.md`, `5-2-s2-items.md`)
- **移除**: 9 个 Question block
- **不动**: 所有 canonical `6-*-items.md`、`qa-question-level/`、`qa/`

---

## 组 C: Biology 0610 — final-push 与 round2 冲突 (1 个)

**根因**: `final-push-items.md` 是最后补充批次，重新生成了已存在于 `4-round2-items.md` 中的 `Q-4.1-08`。

**策略**: 保留 `4-round2-items.md` 中的版本，从 `final-push-items.md` 中移除。

**理由**: round2 是较早的规范补充批次，final-push 是末批，不应覆盖已有 Q-ID。

| Q-ID | 冲突文件 | 保留 | 移除 | 理由 | 内容差异 |
|------|---------|------|------|------|---------|
| Q-4.1-08 | 4-round2-items.md (585c) vs final-push-items.md (666c) | 4-round2-items.md | final-push-items.md | 较早的规范批次 | final-push 长 81c |

### Biology 预计 diff 摘要

- **改动文件**: 1 个 (`final-push-items.md`)
- **移除**: 1 个 Question block
- **不动**: `4-round2-items.md`、`qa-question-level/`

---

## 组 D: Accounting 0452 — qa/ 拆分版与原合并版冲突 (2 个)

**根因**: `5-5-partnership-accounts.md` 和 `5-6-limited-companies.md` 是原始合并版文件（包含多 topic），拆分后产生了 `5-5-partnership-accounts-appropriation.md` 和 `5-6-limited-companies-financial-statements.md`，两者共存于 `qa/` 目录。

**策略**: 保留拆分版（更细粒度、与 `qa-question-level/` 结构对齐），从原合并版中移除重复的 Question block。

**理由**: 拆分版是后续精细化产物，与单题文件结构一致。合并版中其他 topic 的 Question 不受影响。

| Q-ID | 冲突文件 | 保留 | 移除 | 理由 | 内容差异 |
|------|---------|------|------|------|---------|
| Q-5.5-01 | 5-5-partnership-accounts.md (251c) vs 5-5-partnership-accounts-appropriation.md (253c) | appropriation.md (拆分版) | partnership-accounts.md (合并版) | 拆分版与 qql 对齐 | 近乎等长 |
| Q-5.6-01 | 5-6-limited-companies.md (243c) vs 5-6-limited-companies-financial-statements.md (233c) | financial-statements.md (拆分版) | limited-companies.md (合并版) | 同上 | 近乎等长 |

### Accounting 预计 diff 摘要

- **改动文件**: 2 个 qa/ 合并版文件 (`5-5-partnership-accounts.md`, `5-6-limited-companies.md`)
- **移除**: 2 个 Question block
- **不动**: 拆分版文件、`qa-question-level/`、`items/`

---

## 全局汇总

| 组 | 改动文件 | 移除 Q-block | 不动 |
|----|---------|-------------|------|
| A (Physics) | 5 round2 files | 27 | 原始 items, qql, qa |
| B (Chemistry) | 2 s2 files | 9 | canonical items, qql, qa |
| C (Biology) | 1 final-push file | 1 | round2, qql |
| D (Accounting) | 2 qa/ 合并版 | 2 | 拆分版, qql, items |
| **合计** | **10 个文件** | **39** | |

## 风险评估

- **数据丢失风险**: 低。所有保留版本均与 `qa-question-level/` 权威源对齐
- **Chemistry B1 组**: 4 个完全相同的副本，零风险
- **Physics 3-way 冲突**: 4 个 Q-ID 在 3 个文件中出现，需从 2 个 round2 文件中都移除
- **内容差异**: 部分 round2 版本内容更长，但保留原始 items 的策略确保了与 qql 权威源的一致性

## 执行建议

确认后，建议用 Python 脚本批量执行：
1. 读取每个待改动文件
2. 用 `QUESTION_ENTITY_RE` 定位重复 block
3. 移除指定 Q-ID 的 `### Question ...` 到下一个 `### Question` 之间的文本
4. 写回文件
5. 重跑 `qbank_verify.py` 验证 39 → 0
