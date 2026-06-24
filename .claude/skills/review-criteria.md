---
name: review-criteria
description: Review Course 评审判定标准和常见返修原因。用于 review_course 执行评审或 manager 抽检时参考。
metadata:
  type: workflow
  generated_by: Hermes
  date: 2026-06-24
---

# Review Course 评审标准

## 评审阶段

1. **格式检查** — 文件结构、命名、JSON schema
2. **内容检查** — 知识点覆盖、难度梯度
3. **质量检查** — 错误率、重复率、完整性
4. **教学可用性** — 是否有实际教学价值

## 判定结果

| verdict | 含义 | 下一步 |
|---------|------|--------|
| approved | 通过 | deliver → user |
| quality_not_met | 需返修 | return → worker_course |
| blocked | 阻塞 | report → manager |

## 常见返修原因

### 1. 知识点覆盖不足
- **表现**：遗漏 syllabus 要求的 topic
- **阈值**：覆盖率 < 90% 需返修
- **修复**：补充缺失 topic

### 2. 难度梯度异常
- **表现**：AS 阶段出现 A-Level 难度题
- **阈值**：难度与 stage 不匹配
- **修复**：调整题目难度

### 3. 错误率超标
- **表现**：数学错误、概念错误、物理单位错误
- **阈值**：错误率 > 5%
- **修复**：逐题修正

### 4. 内容重复
- **表现**：相同或高度相似题目
- **阈值**：重复率 > 10%
- **修复**：去重或改编

### 5. 格式不规范
- **表现**：JSON 缺少必填字段、命名不一致
- **阈值**：任一必填字段缺失
- **修复**：补全字段

## 评审检查清单

```bash
# 格式检查
python3 -c "
import json, os
for root, dirs, files in os.walk('content/'):
    for f in files:
        if f.endswith('.json'):
            path = os.path.join(root, f)
            try:
                with open(path) as fp:
                    json.load(fp)
            except json.JSONDecodeError as e:
                print(f'JSON ERROR: {path} -> {e}')
"

# 覆盖检查
python3 -c "
import json
with open('content/{subject}/topics/index.json') as f:
    topics = json.load(f)['topics']
covered = set()
for root, dirs, files in os.walk('content/{subject}/'):
    for f in files:
        if f.endswith('.json'):
            # 提取 topic id
            pass
coverage = len(covered) / len(topics)
print(f'Coverage: {coverage:.1%}')
"

# 错误率检查（抽样）
python3 -c "
import random, json
with open('items/questions.json') as f:
    items = json.load(f)['items']
sample = random.sample(items, min(50, len(items)))
errors = 0
for q in sample:
    # 人工检查或调用 API 校验
    pass
error_rate = errors / len(sample)
print(f'Error rate: {error_rate:.1%}')
"
```

## 使用场景

- review_course 执行评审时调用
- manager 抽检前自检
- worker_course 完成后自检（避免返修）