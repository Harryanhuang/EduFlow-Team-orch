---
name: findclass-form-builder
description: Build and maintain Feishu Base forms for teacher information collection in the FindClass workflow. Use when creating new teacher forms, modifying form fields, or validating form structure.
---

# FindClass Form Builder

管理和维护 FindClass 老师信息采集的飞书表单。

## 什么时候用

- 用户说"创建新的老师信息采集表单"
- 用户说"修改飞书表单的字段结构"
- 用户要验证当前表单字段与 skill 约定的映射是否一致
- 用户要新增/删除表单题目

## 表单结构

### 核心字段（必填）

| 题目 | 类型 | 说明 |
|------|------|------|
| 老师姓名 | 单行文本 | 必填 |
| 手机号 | 手机号 | 必填，用于发布时查重 |
| 简版个人简介 | 多行文本 | 必填，服务器简介用 |
| 详细个人简介 | 多行文本 | 用于 Obsidian 本地展示 |

### 常用字段

| 题目 | 类型 | 说明 |
|------|------|------|
| 所在城市 | 单行文本 | 如"深圳福田" |
| 教学阶段 | 多选 | IGCSE / A-Level / IB / AP 等 |
| 擅长科目 | 多选/文本 | 如"数学" |
| 授课方式 | 多选 | 深圳线下 / 线上 |
| 授课语言 | 单选 | 中英双语 / 中文 / 英文 |
| 教学风格 | 多行文本 | 约 220 字 |
| 教学年限 | 数字 | 年 |
| 带过学生数 | 数字 | 人 |
| 教学时长（小时） | 数字 | 小时 |
| 头像 | 附件 | 老师头像照片 |
| 好评图/展示图 | 附件（可多张） | 展示图片 |
| 飞书记录状态 | 单选 | 待审核 / 已审核 |
| 备注 | 多行文本 | 可选 |

## 执行前必须做的事

- 确认 `lark-cli` 可用
- 确认 Base token 和 table id（见 findclass-teacher-feishu-sync/SKILL.md）
- 确认当前表单版本号

## 标准流程

### 1. 读取当前表单结构

```bash
lark-cli base +record-list \
  --base-token <base_token> \
  --table-id <table_id> \
  --as bot
```

### 2. 新建/修改字段

通过 `lark-cli base +table-update` 或飞书界面操作。
每次修改后验证字段映射表。

### 3. 验证字段映射

确认飞书字段 → Markdown 字段映射（参照 findclass-teacher-feishu-sync 的字段速查表）。

## 操作原则

- 每次只修改少量字段，改完验证后再继续
- 不要删除已有字段，除非确认没有人使用
- 修改字段名时要同步更新所有相关 skill 的映射表
- 新增字段后更新本 skill 的字段表格
