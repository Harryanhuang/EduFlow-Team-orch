---
name: findclass-quality-check
description: Validate teacher Markdown files for data completeness and correctness before publishing to FindClass server. Use as a pre-publish gate or standalone quality audit.
---

# FindClass Quality Check

老师资料发布前的质量检查。

## 什么时候用

- 发布前确认资料完整可用
- 老板要求抽检老师资料质量
- 批量发布前的统一预检
- 用户说"检查一下这位老师的资料有没有问题"

## 检查项

### 必填字段（P0）

| 检查项 | 要求 | 失败处理 |
|--------|------|---------|
| name | 非空 | 阻塞发布 |
| phone | 非空，11 位手机号格式 | 阻塞发布 |
| personal_intro | 非空 | 阻塞发布 |
| avatar | frontmatter 不为空且对应文件存在 | 阻塞发布 |
| sync_id | 首次发布应为 null；已有 sync_id 走更新模式 | 仅记录 |

### 推荐字段（P1）

| 检查项 | 要求 | 失败处理 |
|--------|------|---------|
| city | 非空 | 警告 |
| good_subject | 非空 | 警告 |
| class_style | 非空 | 警告 |
| work_year | 非空 | 警告 |
| class_type | 非空 | 警告 |

### 文件完整性（P0）

| 检查项 | 要求 |
|--------|------|
| 头像文件 | 在 `$FINDCLASS_TEACHER_AVATAR_DIR` 目录下，文件名与 Markdown 引用一致 |
| 展示图文件 | 在 `$FINDCLASS_TEACHER_GALLERY_DIR` 目录下，文件名与 Markdown 引用一致 |
| Markdown 格式 | YAML frontmatter 可解析，无语法错误 |

### 一致性检查（P2）

| 检查项 | 说明 |
|--------|------|
| good_subject 取值 | 是否在小程序系统已知取值范围内 |
| class_style 长度 | 约 220 字参考长度，过短/过长需提示 |
| personal_intro 长度 | 保持短句，不应过长（>200 字需提示） |
| 手机号唯一性 | 服务器无重复记录（通过发布脚本的查重逻辑确认） |

## 执行流程

### 1. 读取 Markdown

解析 frontmatter，检查必填字段。

### 2. 检查文件

确认头像/展示图文件存在且路径匹配。

### 3. 一致性校验

对照系统取值表检查 good_subject 等字段。

### 4. 生成报告

输出结构化检查结果：

```
老师: <name>
- P0 检查: PASS / FAIL
  - name: ✅ 非空
  - phone: ✅ 13970730859
  - personal_intro: ✅ 非空
  - avatar: ✅ 文件存在
- P1 检查: PASS / WARN
  - city: ✅ 深圳福田
  - class_style: ⚠️ 过短（仅 50 字）
- P2 检查: PASS / INFO
  - good_subject: ✅ 数学（系统已知值）
```

## 操作原则

- P0 项任一失败 → 阻塞发布
- P1 项失败 → 发出警告但不阻塞，由操作者判断
- P2 项失败 → 仅记录 info，不阻塞
- 不要跳过检查直接发布
- 批量检查时逐条报告，汇总 PASS/FAIL 数量
