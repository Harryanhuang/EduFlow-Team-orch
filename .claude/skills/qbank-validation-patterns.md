---
name: qbank-validation-patterns
description: QBank 校验流程和常见错误模式。用于 worker_qbank 自检或 review_course 评审前检查。
metadata:
  type: workflow
  generated_by: Hermes
  date: 2026-06-24
---

# QBank 校验流程与错误模式

## 校验流程

1. **答案一致性检查** — 同一题答案在 manifest 和实际 JSON 必须一致
2. **图片失效检查** — 所有图片路径必须可访问（404 检查）
3. **AO 映射检查** — 每题必须有明确的 AO（Assessment Objective）标签
4. **题目完整性** — 问题、答案、解析、难度等级缺一不可
5. **格式规范** — JSON 结构符合 unified_manifest schema

## 常见错误模式

### 1. 答案不一致
- **表现**：manifest 填 A，实际 JSON 选 B
- **修复**：遍历 manifest row 和 qa JSON，对比 answer 字段

### 2. 图片路径失效
- **表现**：图片引用 404 或路径错误
- **修复**：用 curl -I 逐个检查 images/ 目录

### 3. AO 缺失或错误
- **表现**：题目无 AO 标签或 AO 与难度不匹配
- **修复**：补充 AO 标签，按大纲校验合理性

### 4. 难度等级异常
- **表现**：AS Level 标记为 Easy
- **修复**：按 syllabus 难度曲线校验

## 自检清单

```bash
# 1. 检查答案一致性
python3 -c "
import json, csv
with open('unified_manifest.csv') as f:
    manifest = {r['id']: r['answer'] for r in csv.DictReader(f)}
with open('items/questions.json') as f:
    qbank = {q['id']: q['answer'] for q in json.load(f)['items']}
for k in manifest:
    if manifest[k] != qbank.get(k):
        print(f'ANSWER MISMATCH: {k}')
"

# 2. 检查图片可用性
find items -name "*.png" -o -name "*.jpg" | while read f; do
  curl -sI "$f" >/dev/null || echo "BROKEN: $f"
done

# 3. 统计 AO 分布
python3 -c "
import json
with open('items/questions.json') as f:
    items = json.load(f)['items']
from collections import Counter
aos = Counter(q.get('ao', 'MISSING') for q in items)
print(dict(aos))
"
```

## 使用场景

- worker_qbank 完成后自检
- review_course 评审前交叉检查
- manager 抽检发现问题的第一轮修复指引