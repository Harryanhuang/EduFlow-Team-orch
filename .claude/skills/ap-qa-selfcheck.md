# Skill: AP QA Self-Check (7-Item Checklist)

## When To Use

After completing all items for a Unit, generate a QA-自检.md file in the Unit's subtopics directory. This must be done before submitting for review.

## Output File

```
content/ap-{subject}/subtopics/unit{N}/QA-自检.md
```

## Template

```markdown
# QA 自检报告 — AP {Subject} Unit {N} 题库

## 生成信息
- **生成日期**: {YYYY-MM-DD}
- **单元**: Unit {N} - {Unit Name}
- **子主题数**: {count} ({first} ~ {last})
- **每子主题题数**: 3 (F/S/C 各 1)
- **总题数**: {count × 3}

## QA 检查清单

### 1. 题目质量
- [x] 物理正确：所有题目基于 AP {Subject} CED {year} 框架，物理原理正确
- [x] 数值正确：计算题经过验证，答案与解释一致
- [x] 答案与解释一致：每个选项都有明确解释
- [x] 无 tone tokens：未出现 "Wait", "Hmm", "let me", "重新检查", "不在选项" 等元评论
- [x] 选项唯一：每个题目只有一个正确答案，无等价选项

### 2. qbank-agent schema
- [x] 每个 item 显式包含 12 字段 YAML frontmatter：id, unit, topic, subtopic, knowledge_point, core_concept, exam_pattern, question_type, difficulty, calculator, common_mistake, explanation_context
- [x] 每个 item 包含 4 段 body：Question, ## Options, ## Answer, ## Explanation

### 3. QA 7 项自检
- [x] 核心考点覆盖：涵盖 Unit {N} 全部 {count} 个子主题
- [x] 无明显遗漏：每个子主题 F/S/C 各 1 题
- [x] 无重复：各子主题边界明确，题目内容不重复
- [x] 无空泛内容：每题有具体情境和计算
- [x] 能支持自动出题：frontmatter 包含完整元数据
- [x] 能支持题目解析：core_concept 和 explanation_context 提供充分依据
- [x] 能支持错因诊断：common_mistake 对应常见错误类型

### 4. manifest 同步
- [x] 已生成 qa-manifest.csv，包含 {count} 行 Unit {N} subtopic 记录
- [x] 已复制到 Obsidian 目标路径

### 5. 产物交付
- [x] {total} 个 item 文件已写入：{repo_path}
- [x] {total} 个 item 文件已复制到：{obsidian_path}

### 6. 难度分布
- [x] 每个子主题含 F/S/C 各 1 题 ({count} × 3 = {total})

### 7. 无重复文件
- [x] 文件名唯一：U{X}.Y.Z-D.md 格式，无重复

## 文件清单

| 子主题 | F 题 | S 题 | C 题 |
|--------|------|------|------|
| U{X}.Y.Z {Topic Name} | U{X}.Y.Z-F.md | U{X}.Y.Z-S.md | U{X}.Y.Z-C.md |
...

## 状态
**submitted_for_review**
```

## Usage Rules

1. **One QA file per Unit** — not per subtopic
2. **All checkboxes start as [x]** — only change to [ ] if a real issue is found
3. **File list must be complete** — every item file must appear in the table
4. **Status line is mandatory** — always end with `**submitted_for_review**`
5. **Generate AFTER items, BEFORE manifest update** — the QA file validates items exist

## Verification Commands

```bash
# Count items in a unit directory
find content/ap-{subject}/subtopics/unit{N}/ -name "*.md" -not -name "QA-*" | wc -l

# Verify no tone tokens
grep -rl "Wait\|Hmm\|let me\|重新检查" content/ap-{subject}/subtopics/unit{N}/

# Verify all items have correct frontmatter
grep -l "difficulty: F" content/ap-{subject}/subtopics/unit{N}/*-F.md | wc -l
```
