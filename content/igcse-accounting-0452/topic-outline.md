# IGCSE Accounting (0452) Topic Outline

基于 Cambridge IGCSE Accounting (0452) 现行 syllabus。
覆盖 Core + Supplement 全部知识领域。

## 知识领域概览

| 编号 | 领域 | Topic 数量 |
|------|------|------------|
| 1 | The fundamentals of accounting | 5 |
| 2 | Sources and recording of data | 6 |
| 3 | Verification of accounting records | 4 |
| 4 | Accounting procedures | 5 |
| 5 | Preparation of financial statements | 6 |
| 6 | Analysis and interpretation | 4 |
| 7 | Accounting principles and policies | 5 |
| **总计** | | **35** |

## Topic 列表

### 1 — The fundamentals of accounting

| ID | Topic | Core/Supplement | 前置 |
|----|-------|-----------------|------|
| 1.1 | The purpose of accounting | Core | 无 |
| 1.2 | Users of accounting information | Core | 无 |
| 1.3 | Assets, liabilities and capital | Core | 无 |
| 1.4 | The accounting equation | Core | 1.3 |
| 1.5 | Capital and revenue items | Core+Supplement | 1.1 |

### 2 — Sources and recording of data

| ID | Topic | Core/Supplement | 前置 |
|----|-------|-----------------|------|
| 2.1 | Source documents | Core | 1.1 |
| 2.2 | Double entry rules | Core | 1.3, 1.4 |
| 2.3 | Books of original entry | Core | 2.2 |
| 2.4 | The ledger | Core | 2.2 |
| 2.5 | The cash book | Core+Supplement | 2.2 |
| 2.6 | The petty cash book | Core+Supplement | 2.5 |

### 3 — Verification of accounting records

| ID | Topic | Core/Supplement | 前置 |
|----|-------|-----------------|------|
| 3.1 | The trial balance | Core | 2.4 |
| 3.2 | Types of errors | Core | 3.1 |
| 3.3 | Correction of errors | Core+Supplement | 3.2 |
| 3.4 | Bank reconciliation | Core+Supplement | 2.5 |

### 4 — Accounting procedures

| ID | Topic | Core/Supplement | 前置 |
|----|-------|-----------------|------|
| 4.1 | Depreciation: straight line method | Core | 1.3 |
| 4.2 | Depreciation: reducing balance method | Core+Supplement | 4.1 |
| 4.3 | Disposal of non-current assets | Core+Supplement | 4.1, 4.2 |
| 4.4 | Irrecoverable debts and allowances for receivables | Core+Supplement | 2.4 |
| 4.5 | Accruals, prepayments and inventory valuation | Core+Supplement | 2.4 |

### 5 — Preparation of financial statements

| ID | Topic | Core/Supplement | 前置 |
|----|-------|-----------------|------|
| 5.1 | Income statement: trading section | Core | 2.2 |
| 5.2 | Income statement with adjustments | Core+Supplement | 5.1, 4.5 |
| 5.3 | Statement of financial position | Core+Supplement | 5.2 |
| 5.4 | Capital adjustments | Core+Supplement | 5.3 |
| 5.5 | Partnership accounts appropriation | Supplement | 5.4 |
| 5.6 | Limited companies financial statements | Supplement | 5.4 |

### 6 — Analysis and interpretation

| ID | Topic | Core/Supplement | 前置 |
|----|-------|-----------------|------|
| 6.1 | Liquidity ratios | Supplement | 5.3 |
| 6.2 | Profitability ratios | Supplement | 5.3 |
| 6.3 | Efficiency ratios | Supplement | 5.3 |
| 6.4 | Ratio interpretation and limitations | Supplement | 6.1, 6.2, 6.3 |

### 7 — Accounting principles and policies

| ID | Topic | Core/Supplement | 前置 |
|----|-------|-----------------|------|
| 7.1 | Accounting concepts application | Core+Supplement | 1.1 |
| 7.2 | Capital vs revenue expenditure | Core+Supplement | 1.5 |
| 7.3 | Accounting policy changes | Supplement | 7.1 |
| 7.4 | Information quality characteristics | Core | 1.1 |
| 7.5 | Comprehensive scenario | Core+Supplement | 5.3, 7.1 |

## 字段规范

- ID: 采用章节式 `1.1`, `2.1` 等
- Topic: 使用 syllabus 官方表述
- Core/Supplement: 按 syllabus 实际层级标注
- 前置: 仅填真实依赖

## 产出约束

- topic-outline 只定义范围、层级、先修、覆盖关系
- 不在 outline 中写长篇教学解释
- 每个 outline 条目都必须能一一映射到一个 QA 文件

## QA 配套

每个 topic 对应一份 QA 文件，详见 `qa/` 目录。
题库总索引见 `qa-manifest.csv`。
