# QBank 验证报告

**日期**: 2026-06-21
**执行者**: worker_qbank
**工具**: `scripts/qbank_verify.py`

## 1. 执行摘要

对 **7 个**已闭环学科的全部产出进行了扫描、解析、Schema 校验、去重和一致性检查。

| 指标 | 结果 |
|------|------|
| 扫描学科数 | 7 |
| 解析 Question 总数 | 3154 |
| 同层内重复 (error) | 39 |
| 跨层重叠 (info, 预期) | 1058 |
| Schema 违规 | 0 |
| Manifest 问题 | 42 |

**结论**: 题库内容可导入。新增 Economics 0455 (468 题) 和 Business Studies 0450 (600 题) 均无重复、无 Schema 违规。原有 5 学科的 39 个同层重复和 manifest 缺失问题不变，待后续去重/补齐批次处理。

## 2. 学科清单

| 学科 | code | Topics | qa/ 文件 | qa-question-level/ 文件 | items/ 文件 | 解析 Q 数 | Manifest |
|------|------|--------|----------|------------------------|-------------|-----------|----------|
| Mathematics 0580 | 0580 | 27 | 24 | 300 | 34 | 600 | MISSING |
| Physics 0625 | 0625 | 41 | 46 | 315 | 53 | 322 | yes (4 rows) |
| Chemistry 0620 | 0620 | 18 | 34 | 305 | 64 | 305 | MISSING |
| Biology 0610 | 0610 | 26 | 0 | 300 | 74 | 300 | MISSING |
| Accounting 0452 | 0452 | 24 | 37 | 315 | 35 | 559 | yes (35 rows) |
| **Economics 0455** | **0455** | **13** | **0** | **234** | **26** | **468** | **MISSING** |
| **Business Studies 0450** | **0450** | **13** | **0** | **300** | **25** | **600** | **MISSING** |

> 加行为本次新增纳入验证的学科。

## 3. 难度分布

| 学科 | Foundation | Standard | Challenge | 总计 |
|------|-----------|----------|-----------|------|
| Mathematics 0580 | 106 (17.7%) | 398 (66.3%) | 96 (16.0%) | 600 |
| Physics 0625 | 181 (56.2%) | 114 (35.4%) | 27 (8.4%) | 322 |
| Chemistry 0620 | 142 (46.6%) | 157 (51.5%) | 6 (2.0%) | 305 |
| Biology 0610 | 41 (13.7%) | 240 (80.0%) | 19 (6.3%) | 300 |
| Accounting 0452 | 217 (38.8%) | 221 (39.5%) | 121 (21.6%) | 559 |
| Economics 0455 | 104 (22.2%) | 208 (44.4%) | 156 (33.3%) | 468 |
| Business Studies 0450 | 150 (25.0%) | 250 (41.7%) | 200 (33.3%) | 600 |

### 难度分布异常

- **Chemistry 0620**: Challenge 仅 6 题 (2.0%)，远低于其他学科，建议补题
- **Biology 0610**: Foundation 仅 41 题 (13.7%)，Standard 占 80%，分布偏科
- **Physics 0625**: Challenge 仅 27 题 (8.4%)，同样偏低
- **Economics 0455 / Business Studies 0450**: 难度分布均衡，Challenge 占比 33%，无需补题

## 4. 发现的问题

### 4.1 同层内重复 (39 个, ERROR)

与上一轮验证结果一致，新增的 Economics 和 Business Studies **无任何重复**。39 个重复全部集中在原有 5 学科：

**Physics 0625 (27 个):**
- `*-round2-items.md` 文件中包含与原始 `*-items.md` 重复的 Q-ID
- `4-round2-items.md` 中包含跨 topic 的 Q-ID，与 `5-*-items.md` 冲突
- **根因**: round2 批次生产时未去重

**Chemistry 0620 (9 个):**
- `5-1-s2-items.md` / `5-2-s2-items.md` 中 Q-ID 与 `6-1-items.md` / `6-3-items.md` 冲突
- **根因**: section-2 补充文件使用了与后续 topic 相同的 Q-ID 编号

**Biology 0610 (1 个):**
- `Q-4.1-08` 同时出现在 `4-round2-items.md` 和 `final-push-items.md`

**Accounting 0452 (2 个):**
- `Q-5.5-01` / `Q-5.6-01` 在原 QA 文件与拆分版文件中均出现
- **根因**: 拆分版与原文件共存于 `qa/` 目录

### 4.2 跨层重叠 (1058 个, INFO)

同一 Q-ID 在不同内容层（如 `items/` 和 `qa-question-level/`）中出现的预期重叠。导入时以 `qa-question-level/` 为权威来源。

### 4.3 Manifest 问题 (42 个, WARNING)

- **5 个学科缺失 manifest**: Mathematics, Chemistry, Biology, Economics, Business Studies
- **Physics manifest 不完整**: 仅 4 行 (batch-01 topics 1.1-2.2)，缺少其余 42 个 topic
- **Accounting manifest 行数不匹配**: qa/ 层 topic 文件的 manifest 声明 `question_count` 与实际 Question entity 数不一致（qa/ 文件已拆分为单题文件，每个文件仅 1 个 Question entity）

### 4.4 Schema 校验

全部 3154 个 Question 通过 Schema 校验：
- Difficulty 枚举值正确 (Foundation / Standard / Challenge)
- Question ID 格式符合 `Q-<topic-id>-<nn>` 规范
- 所有必填字段 (Question, Answer) 均存在

## 5. 已产出

| 产出 | 路径 | 说明 |
|------|------|------|
| 验证工具 | `scripts/qbank_verify.py` | 覆盖 7 学科，可重复执行 |
| 统一 manifest | `content/qbank-unified-manifest.csv` | 覆盖全部 7 学科 3154 题 |
| 本报告 | `content/qbank-verification-report.md` | 验证方案与发现汇总 |

## 6. 导入前去重建议

### 必须处理 (ERROR)

1. **Physics round2 去重**: 对 `*-round2-items.md` 文件，仅保留不与原始 `*-items.md` 冲突的 Q-ID
2. **Chemistry s2 去重**: 从 `5-1-s2-items.md` 和 `5-2-s2-items.md` 中移除与 `6-1/6-3-items.md` 重复的 Q-ID
3. **Biology final-push 去重**: 从 `final-push-items.md` 中移除 `Q-4.1-08`
4. **Accounting qa/ 去重**: 移除拆分版中与原文件重复的 Q-ID，或将拆分版设为权威

### 建议处理 (WARNING)

5. **补齐 manifest**: 为 Mathematics、Chemistry、Biology、Economics、Business Studies 生成 `qa-manifest.csv`
6. **更新 Physics manifest**: 扩展至全部 46 个 topic
7. **补题**: Chemistry Challenge 题 (当前仅 6 题) 和 Biology Foundation 题 (当前仅 41 题)

## 7. 本次变更摘要 (v2)

| 变更项 | v1 (5 学科) | v2 (7 学科) | 差异 |
|--------|------------|------------|------|
| 学科数 | 5 | 7 | +2 (Economics, Business Studies) |
| Question 总数 | 2086 | 3154 | +1068 |
| 同层重复 | 39 | 39 | 无变化 (新学科无重复) |
| 跨层重叠 | 524 | 1058 | +534 (新学科跨层) |
| Manifest 问题 | 40 | 42 | +2 (新学科各缺 1 个 manifest) |
| Schema 违规 | 0 | 0 | 无变化 |

## 8. 验证方案总结

```
qbank_verify.py 执行流程:

  content/<subject>/
    ├── topic-outline.md    → 解析 topic 列表 (ID + name)
    ├── qa/*.md             → 解析 topic 级 QA (含 Question entities)
    ├── qa-question-level/  → 解析单题 QA 文件
    └── items/*.md          → 解析批量 items 文件

  校验步骤:
    1. Schema 校验: Difficulty enum, Q-ID 格式, 必填字段
    2. 同层去重: (subject, layer, Q-ID) 唯一性
    3. 跨层重叠标记: 预期行为, info 级别
    4. Manifest 一致性: 文件存在性, question_count 匹配
    5. 难度分布统计: 检测偏科

  输出:
    - 文本报告 (stdout)
    - JSON 报告 (--json)
    - 统一 manifest CSV (--manifest-out)
```

## 9. 后续建议

1. **全局 Q-ID 唯一化**: 当前 Q-ID 不含 subject_slug，跨学科存在碰撞。建议导入时统一前缀为 `Q-<subject>-<topic>-<nn>`
2. **导入管道**: 建议以 `qa-question-level/` 层为权威数据源，`items/` 层作为生产日志保留
3. **CI 集成**: 将 `qbank_verify.py` 加入 CI pipeline，每次内容变更自动验证
4. **去重批次**: 39 个同层重复为已知问题，建议单独开 task 处理（不改动 QA 内容文件本身，仅在 items 层做去重）
