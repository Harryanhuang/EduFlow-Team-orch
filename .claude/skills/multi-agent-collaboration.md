---
name: multi-agent-collaboration
description: 多智能体协同模式。用于 worker_course + review_course + worker_qbank 协同生产时参考。
metadata:
  type: workflow
  generated_by: Hermes
  date: 2026-06-24
---

# 多智能体协同模式

## 角色定义

| Agent | 职责 | 输入 | 输出 |
|-------|------|------|------|
| worker_course | 课程内容生产 | task description | course content |
| review_course | 评审质量检查 | course content | verdict |
| worker_qbank | 题库生产 | course content | QBank items |

## 协同流程

```
manager dispatch
    ↓
worker_course → produce content
    ↓
review_course → quality check
    ↓ (approved)
worker_qbank → generate QBank
    ↓
review_course → QBank check
    ↓ (approved)
deliver → user
```

## 协同规则

### 1. 信息传递
- worker_course 产出必须写入 `content/{subject}/` 目录
- review_course 从磁盘读取，不依赖内存
- worker_qbank 从 `content/{subject}/` 读取

### 2. 状态同步
- 每阶段完成后更新 task status
- 使用 `correlation_id` 关联父子 task
- 失败时保留中间产物供修复

### 3. 错误处理
- review_course 返回 `quality_not_met` → 回退 worker_course
- worker_qbank 失败 → 可单独重跑，无需重跑 worker_course
- review_course 卡住 → manager 介入判定

### 4. 并行限制
- 同一 subject 禁止并行 worker_course（文件冲突）
- worker_qbank 可与 review_course 并行（只读）
- manager 调度时检查任务分配：`eduflow task list --assignee worker_course` shows what's currently active per agent; if any active task already targets the same subject, do NOT dispatch a new one for that subject

## 常见协同问题

### 1. 文件覆盖冲突
- **表现**：并行 worker_course 覆盖彼此文件
- **解决**：manager 按 subject 串行调度

### 2. 中间状态丢失
- **表现**：worker_course 崩溃，review_course 无可评内容
- **解决**：每阶段产物必须落盘

### 3. review_course 判定过严
- **表现**：频繁返修，拖慢整体进度
- **解决**：使用 review-criteria skill 统一标准

### 4. QBank 质量不匹配
- **表现**：QBank 难度与课程内容不匹配
- **解决**：worker_qbank 必须引用 worker_course 的 topics

## 调度命令参考

```bash
# 查看当前 subject 锁
eduflow task review-queue --stage curriculum | grep -v done

# 串行调度（按 subject）
# manager 按顺序 dispatch，避免并行

# 并行检测
ps aux | grep worker_course | wc -l
```

## 使用场景

- manager 调度多智能体任务时参考
- worker_course/review_course/worker_qbank 理解上下游关系
- 故障排查时定位协同断点