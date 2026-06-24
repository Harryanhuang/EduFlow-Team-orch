# QBank 去重方案 v3.2 — Normalized Q+A 比对 + 纯数字 Renumber Map

**日期**: 2026-06-21
**执行者**: worker_qbank
**状态**: DRY-RUN v3.2（未改动任何 QA 文件）
**数据源**: `content/qbank-dedup-v3-maps.json` + `content/qbank-renumber-map-numeric.json`（SHA-256 normalized Q+A 哈希）

## 方法论

1. 提取每个 Question entity 的 `**Question**` + `**Answer**` 字段
2. 归一化空白字符（`re.sub(r'\s+', ' ', text.strip())`）
3. 计算 SHA-256 哈希，同一 Q-ID 在同一层内比较哈希值
4. **true_duplicate**: 哈希完全相同 → 删除副本
5. **id_collision**: 哈希不同（不同题目共享 Q-ID）→ 保留全部，重编号

## v3.1 修正记录 (review_course MINOR 反馈)

review_course 指出两类问题：

**1. 方向反转 (12 个 A4/A5 条目)**

JSON 数据中 A4/A5 组 `keep`/`renumber` 方向被脚本字母排序反转。修正: keep = `5-X-items.md` (canonical)，renumber = `4-round2` + `5-round2`。

**2. Q-6.3-01 分类冲突**

Q-6.3-01 的 Question 文本在两个文件中完全相同，但 Answer 变体不同（s2 版提 OIL RIG，canonical 版给化学方程式例子）。原归为 id_collision 需重编号，现重分类为 **near_duplicate → true_duplicate**：保留 canonical 版（更丰富），删除 s2 变体。

**修正结果**: true_duplicate 6→7, id_collision 33→32, renumber map 38→37 行。

**已修正**:
- `qbank-dedup-v3-maps.json`: 全部 action 字段校准 + Q-6.3-01 移入 true_duplicates
- 本计划文档: 总览表、删除表、重编号表、对比表均已同步

## 总览

| 学科 | 无冲突 Q-ID | 真实重复 (删除) | Q-ID 冲突 (重编号) |
|------|-----------|---------------|-------------------|
| Mathematics 0580 | 600 | 0 | 0 |
| Physics 0625 | 263 | 0 | 27 |
| Chemistry 0620 | 287 | **5** | **4** |
| Biology 0610 | 298 | 0 | 1 |
| Accounting 0452 | 555 | 2 | 0 |
| Economics 0455 | 468 | 0 | 0 |
| Business Studies 0450 | 600 | 0 | 0 |
| **合计** | **3071** | **7** | **32** |

> v1 误判 39 个全部为重复 → 将丢失 32 题。v3 仅删除 7 个真实副本（含 1 个 near-duplicate），重编号 32 个冲突，零丢失。

---

## (a) True Duplicate 列表 — 删除副本 (7 个)

### Chemistry: 4 个 (B1 组) + 1 个 near-duplicate (B1.5)

Q-6.1-01 至 Q-6.1-04 在 `5-1-s2-items.md` 和 `6-1-items.md` 中 Q+A 内容**完全相同**。

| Q-ID | 保留 | 删除 | Q+A 哈希 | 内容证据 |
|------|------|------|---------|---------|
| Q-6.1-01 | `6-1-items.md` | `5-1-s2-items.md` | `82d6919f08ebc1a1` | Q+A 完全一致 |
| Q-6.1-02 | `6-1-items.md` | `5-1-s2-items.md` | `d3a4a45c4f0b0204` | Q+A 完全一致 |
| Q-6.1-03 | `6-1-items.md` | `5-1-s2-items.md` | `fd441d369dfd7c9c` | Q+A 完全一致 |
| Q-6.1-04 | `6-1-items.md` | `5-1-s2-items.md` | `cd7db5ab16c207ab` | Q+A 完全一致 |

**操作**: 从 `5-1-s2-items.md` 中移除 4 个 Question block。

**Q-6.3-01 (near-duplicate)**: Question 文本完全相同（"Define oxidation and reduction in terms of oxygen transfer."），但 Answer 变体不同（s2 版引用 OIL RIG，canonical 版给出具体化学方程式例子）。归为 true_duplicate — 保留 canonical 版（更丰富的化学方程式示例），删除 s2 变体。

| Q-ID | 保留 | 删除 | 分类 | 理由 |
|------|------|------|------|------|
| Q-6.3-01 | `6-3-items.md` (含 CuO+H₂ 例子) | `5-2-s2-items.md` (OIL RIG 提及) | near_duplicate | 同 Q 不同 A 变体，canonical 版更优 |

### Accounting: 2 个 (qa/ 层拆分版)

Q-5.5-01 和 Q-5.6-01 在 qa/ 层的合并版与拆分版中 Q+A 内容**完全相同**（v2 误判为不同内容，因 markdown 格式差异；normalized Q+A 确认一致）。

| Q-ID | 保留 | 删除 | Q+A 哈希 | 说明 |
|------|------|------|---------|------|
| Q-5.5-01 | `5-5-partnership-accounts-appropriation.md` (拆分版) | `5-5-partnership-accounts.md` (合并版) | `0d30a42162ab18e5` | 拆分版与 qql 结构对齐 |
| Q-5.6-01 | `5-6-limited-companies-financial-statements.md` (拆分版) | `5-6-limited-companies.md` (合并版) | `0d30a42162ab18e5` | 同上 |

**操作**: 从合并版文件中移除重复的 Question block（合并版中其他 topic 的 Question 不受影响）。

> **保守处理说明**: 这 2 个 Accounting 条目 Q+A 哈希完全一致，归为 true_duplicate 而非 needs_human_review。如 review_course 仍要求人工确认，可将其降级为 "hold" 状态不执行删除。

---

## (b) ID Collision 列表 — 重编号映射 (32 个冲突, 37 行映射)

### Physics 0625: 27 个冲突

**规范文件优先级**: 原始 `*-items.md` > `*-round2-items.md`。原始 items 文件中的 Q-ID 保持不变，round2 文件中的版本重编号为该 topic 下一个可用的纯数字后缀（如 `Q-1.1-01` → `Q-1.1-10`）。

#### A1: round1 组 — `1-round2-items.md` (8 个冲突)

| 原 Q-ID | 规范文件 (keep) | round2 文件 (renumber) | 新 Q-ID | Question 预览 |
|---------|---------------|----------------------|---------|--------------|
| Q-1.1-01 | `1-1-items.md` | `1-round2-items.md` | Q-1.1-10 | keep: "metre rule to measure…" / new: "Convert 2.5 km to metres…" |
| Q-1.1-02 | `1-1-items.md` | `1-round2-items.md` | Q-1.1-11 | keep: "Convert 3.2 km into metres…" / new: "measures pencil five times…" |
| Q-1.2-01 | `1-2-items.md` | `1-round2-items.md` | Q-1.2-10 | keep: "car 10→25 m/s…" / new: "car 10→30 m/s uniformly…" |
| Q-1.3-01 | `1-3-items.md` | `1-round2-items.md` | Q-1.3-10 | keep: "dropped from rest, 3s…" / new: "mass vs weight?" |
| Q-1.3-02 | `1-3-items.md` | `1-round2-items.md` | Q-1.3-11 | keep: "stone from cliff, 4s…" / new: "spring constant 40 N/m…" |
| Q-1.4-01 | `1-4-items.md` | `1-round2-items.md` | Q-1.4-10 | keep: "mass 5 kg, weight?" / new: "500 kg car brakes…" |
| Q-1.5-01 | `1-5-items.md` | `1-round2-items.md` | Q-1.5-10 | keep: "block 240 g, 4 cm…" / new: "motor 6000 J in 30s…" |
| Q-1.5-02 | `1-5-items.md` | `1-round2-items.md` | Q-1.5-11 | keep: "2.7 g/cm³ → kg/m³" / new: "2 kg ball dropped 5 m…" |

#### A2: round2 组 — `2-round2-items.md` (6 个冲突)

| 原 Q-ID | 规范文件 (keep) | round2 文件 (renumber) | 新 Q-ID |
|---------|---------------|----------------------|---------|
| Q-3.1-01 | `3-1-items.md` | `2-round2-items.md` | Q-3.1-07 |
| Q-3.2-01 | `3-2-items.md` | `2-round2-items.md` | Q-3.2-07 |
| Q-3.3-01 | `3-3-items.md` | `2-round2-items.md` | Q-3.3-06 |
| Q-3.4-01 | `3-4-items.md` | `2-round2-items.md` | Q-3.4-07 |
| Q-3.5-01 | `3-5-items.md` | `2-round2-items.md` | Q-3.5-06 |
| Q-3.6-01 | `3-6-items.md` | `2-round2-items.md` | Q-3.6-07 |

#### A3: round3 组 — `3-round2-items.md` (6 个冲突)

| 原 Q-ID | 规范文件 (keep) | round2 文件 (renumber) | 新 Q-ID |
|---------|---------------|----------------------|---------|
| Q-4.1-01 | `4-1-items.md` | `3-round2-items.md` | Q-4.1-07 |
| Q-4.2-01 | `4-2-items.md` | `3-round2-items.md` | Q-4.2-06 |
| Q-4.3-01 | `4-3-items.md` | `3-round2-items.md` | Q-4.3-06 |
| Q-4.4-01 | `4-4-items.md` | `3-round2-items.md` | Q-4.4-06 |
| Q-4.5-01 | `4-5-items.md` | `3-round2-items.md` | Q-4.5-07 |
| Q-4.6-01 | `4-6-items.md` | `3-round2-items.md` | Q-4.6-06 |

#### A4/A5: round4+5 组 — `4-round2-items.md` / `5-round2-items.md` (7 个冲突, 含 5 个 3-way)

| 原 Q-ID | 规范文件 (keep) | round2 文件 1 → 新 ID | round2 文件 2 → 新 ID |
|---------|---------------|----------------------|----------------------|
| Q-5.1-01 | `5-1-items.md` | `4-round2-items.md` → Q-5.1-06 | `5-round2-items.md` → Q-5.1-07 |
| Q-5.2-01 | `5-2-items.md` | `4-round2-items.md` → Q-5.2-07 | — |
| Q-5.3-01 | `5-3-items.md` | `4-round2-items.md` → Q-5.3-07 | `5-round2-items.md` → Q-5.3-08 |
| Q-5.4-01 | `5-4-items.md` | `4-round2-items.md` → Q-5.4-07 | `5-round2-items.md` → Q-5.4-08 |
| Q-5.5-01 | `5-5-items.md` | `4-round2-items.md` → Q-5.5-06 | `5-round2-items.md` → Q-5.5-07 |
| Q-5.6-01 | `5-6-items.md` | `4-round2-items.md` → Q-5.6-05 | — |
| Q-5.7-01 | `5-7-items.md` | `4-round2-items.md` → Q-5.7-06 | `5-round2-items.md` → Q-5.7-07 |

### Chemistry 0620: 4 个冲突 (B2 组)

规范文件: `6-3-items.md`（canonical topic）。重编号 `5-2-s2-items.md` 中的版本。

| 原 Q-ID | 规范文件 (keep) | s2 文件 (renumber) | 新 Q-ID | Question 预览差异 |
|---------|---------------|-------------------|---------|------------------|
| Q-6.3-02 | `6-3-items.md` | `5-2-s2-items.md` | Q-6.3-06 | keep: "electro…" / new: "Fe₂O₃ + 3CO…" |
| Q-6.3-03 | `6-3-items.md` | `5-2-s2-items.md` | Q-6.3-07 | keep: "Fe₂O₃ + 3CO…" / new: "Zn + Cu²⁺…" |
| Q-6.3-04 | `6-3-items.md` | `5-2-s2-items.md` | Q-6.3-08 | keep: "oxidising agent?" / new: "OIL RIG?" |
| Q-6.3-05 | `6-3-items.md` | `5-2-s2-items.md` | Q-6.3-09 | keep: "Zn + Cu…" / new: "half-equation for reduction…" |

### Biology 0610: 1 个冲突 (C 组)

| 原 Q-ID | 规范文件 (keep) | 冲突文件 (renumber) | 新 Q-ID | Question 预览 |
|---------|---------------|-------------------|---------|--------------|
| Q-4.1-08 | `4-round2-items.md` | `final-push-items.md` | Q-4.1-10 | keep: "water as universal solvent…" / new: "magnesium ions in plant nutrition…" |

---

## (c) 无冲突保留列表

以下学科/文件无任何同层冲突，保持不变：

| 学科 | 无冲突 Q-ID 数 | 说明 |
|------|-------------|------|
| Mathematics 0580 | 600 | 全部 clean |
| Economics 0455 | 468 | 全部 clean |
| Business Studies 0450 | 600 | 全部 clean |
| Physics 0625 (clean) | 263 | 非冲突 Q-ID 保持不变 |
| Chemistry 0620 (clean) | 287 | 非冲突 Q-ID 保持不变 |
| Biology 0610 (clean) | 298 | 非冲突 Q-ID 保持不变 |
| Accounting 0452 (clean) | 555 | 非冲突 Q-ID 保持不变 |

---

## Renumber Map 完整映射表（纯数字后缀）

| # | Subject | 原 Q-ID | 新 Q-ID | 改动文件 |
|---|---------|---------|---------|---------|
| 1 | Physics | Q-1.1-01 | Q-1.1-10 | 1-round2-items.md |
| 2 | Physics | Q-1.1-02 | Q-1.1-11 | 1-round2-items.md |
| 3 | Physics | Q-1.2-01 | Q-1.2-10 | 1-round2-items.md |
| 4 | Physics | Q-1.3-01 | Q-1.3-10 | 1-round2-items.md |
| 5 | Physics | Q-1.3-02 | Q-1.3-11 | 1-round2-items.md |
| 6 | Physics | Q-1.4-01 | Q-1.4-10 | 1-round2-items.md |
| 7 | Physics | Q-1.5-01 | Q-1.5-10 | 1-round2-items.md |
| 8 | Physics | Q-1.5-02 | Q-1.5-11 | 1-round2-items.md |
| 9 | Physics | Q-3.1-01 | Q-3.1-07 | 2-round2-items.md |
| 10 | Physics | Q-3.2-01 | Q-3.2-07 | 2-round2-items.md |
| 11 | Physics | Q-3.3-01 | Q-3.3-06 | 2-round2-items.md |
| 12 | Physics | Q-3.4-01 | Q-3.4-07 | 2-round2-items.md |
| 13 | Physics | Q-3.5-01 | Q-3.5-06 | 2-round2-items.md |
| 14 | Physics | Q-3.6-01 | Q-3.6-07 | 2-round2-items.md |
| 15 | Physics | Q-4.1-01 | Q-4.1-07 | 3-round2-items.md |
| 16 | Physics | Q-4.2-01 | Q-4.2-06 | 3-round2-items.md |
| 17 | Physics | Q-4.3-01 | Q-4.3-06 | 3-round2-items.md |
| 18 | Physics | Q-4.4-01 | Q-4.4-06 | 3-round2-items.md |
| 19 | Physics | Q-4.5-01 | Q-4.5-07 | 3-round2-items.md |
| 20 | Physics | Q-4.6-01 | Q-4.6-06 | 3-round2-items.md |
| 21 | Physics | Q-5.1-01 | Q-5.1-06 | 4-round2-items.md |
| 22 | Physics | Q-5.1-01 | Q-5.1-07 | 5-round2-items.md |
| 23 | Physics | Q-5.2-01 | Q-5.2-07 | 4-round2-items.md |
| 24 | Physics | Q-5.3-01 | Q-5.3-07 | 4-round2-items.md |
| 25 | Physics | Q-5.3-01 | Q-5.3-08 | 5-round2-items.md |
| 26 | Physics | Q-5.4-01 | Q-5.4-07 | 4-round2-items.md |
| 27 | Physics | Q-5.4-01 | Q-5.4-08 | 5-round2-items.md |
| 28 | Physics | Q-5.5-01 | Q-5.5-06 | 4-round2-items.md |
| 29 | Physics | Q-5.5-01 | Q-5.5-07 | 5-round2-items.md |
| 30 | Physics | Q-5.6-01 | Q-5.6-05 | 4-round2-items.md |
| 31 | Physics | Q-5.7-01 | Q-5.7-06 | 4-round2-items.md |
| 32 | Physics | Q-5.7-01 | Q-5.7-07 | 5-round2-items.md |
| 33 | Chemistry | Q-6.3-02 | Q-6.3-06 | 5-2-s2-items.md |
| 34 | Chemistry | Q-6.3-03 | Q-6.3-07 | 5-2-s2-items.md |
| 35 | Chemistry | Q-6.3-04 | Q-6.3-08 | 5-2-s2-items.md |
| 36 | Chemistry | Q-6.3-05 | Q-6.3-09 | 5-2-s2-items.md |
| 37 | Biology | Q-4.1-08 | Q-4.1-10 | final-push-items.md |

> 共 37 行映射（32 个冲突 Q-ID，其中 5 个 3-way 产生额外 5 行映射）。所有新 Q-ID 均为纯数字后缀，通过 `qbank_verify.py` schema 校验。

## Delete Map 完整删除表

| # | Subject | Q-ID | 保留文件 | 删除文件 | 证据 |
|---|---------|------|---------|---------|------|
| 1 | Chemistry | Q-6.1-01 | 6-1-items.md | 5-1-s2-items.md | Q+A hash=82d6919f |
| 2 | Chemistry | Q-6.1-02 | 6-1-items.md | 5-1-s2-items.md | Q+A hash=d3a4a45c |
| 3 | Chemistry | Q-6.1-03 | 6-1-items.md | 5-1-s2-items.md | Q+A hash=fd441d36 |
| 4 | Chemistry | Q-6.1-04 | 6-1-items.md | 5-1-s2-items.md | Q+A hash=cd7db5ab |
| 5 | Chemistry | Q-6.3-01 | 6-3-items.md | 5-2-s2-items.md | near_dup: 同 Q 不同 A 变体 |
| 6 | Accounting | Q-5.5-01 | 5-5-…-appropriation.md | 5-5-partnership-accounts.md | Q+A hash=0d30a421 |
| 7 | Accounting | Q-5.6-01 | 5-6-…-financial-statements.md | 5-6-limited-companies.md | Q+A hash=0d30a421 |

## 预计 Diff 汇总

| 操作 | 数量 | 影响文件数 |
|------|------|----------|
| 删除 Question block | 7 | 4 (5-1-s2 + 5-2-s2 + 2 accounting qa/) |
| Q-ID 重编号 | 37 次 | 7 (5 physics round2 + 1 chem s2 + 1 bio final-push) |
| 改动文件总计 | | 10 (含 1 个文件同时有删除+重编号: 5-2-s2-items.md) |

## v1 → v2 → v3 → v3.2 对比

| | v1 | v2 | v3.1 | v3.2 |
|---|---|---|---|---|
| 比对方法 | Q-ID 匹配 | SHA-256 raw body | SHA-256 normalized Q+A | 同 v3.1 + 纯数字后缀 |
| 删除数 | 39 | 4 | 7 (含 1 near-dup) | 7 (同 v3.1) |
| 重编号数 | 0 | 39 | 37 | 37 (纯数字) |
| 丢失独立题目 | 32 | 0 | 0 | 0 |
| Accounting 处理 | 误删 | 误判为冲突 | 确认为 true dup (Q+A 一致) | 同 v3.1 |
| Q-6.3-01 | 误删 | 归为冲突 | near-dup → true_dup | 同 v3.1 |
| Q-ID 后缀格式 | N/A | N/A | r2/r3 (不通过 schema) | 纯数字 (通过 schema) |

## 执行后验证

执行后重跑 `qbank_verify.py`:
- 同层重复: 39 → 0 (7 删除 + 32 重编号)
- Question 总数: 3154 → 3147 (-7 true duplicates)
- 新增 Q-ID: 37 个纯数字后缀编号，全部通过 `^Q-[A-Z]?\d+(?:\.\d+)?-\d+$` schema 校验
- Schema dry-run: 0 Non-standard Q-ID, 0 与现有 Q-ID 碰撞
