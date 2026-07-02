---
name: findclass-batch-publish
description: Publish multiple reviewed teacher Markdown files from Obsidian to the FindClass server in batch. Use when the user wants to go-live with several teachers at once.
---

# FindClass Batch Publish

批量发布已审核的老师资料到 FindClass 服务器。

## 什么时候用

- 用户说"把这批老师都上传到服务器"
- 用户有多个已整理好的老师 Markdown 需要统一发布
- 用户要查看批量发布进度

## 与单条发布的关系

本 skill 是 `findclass-teacher-publish` 的批量扩展版本。单条发布规则（图片压缩、webp 转换、查重、回写等）同样适用于批量场景。

## 核心路径

使用环境变量（与 findclass-teacher-publish 一致）：
```
$FINDCLASS_TEACHER_TEXT_DIR
```
缺省值：
```
/Volumes/Halobster/Obsidian Edu/留学公司知识库/10-老师信息资料文件夹/老师基本资料（文字）/老师资料
```

## 标准流程

### 1. 扫描待发布老师

```bash
# 找出 publish_status 为 draft 或待发布的老师
grep -l "publish_status.*draft" *.md
```

### 2. 预检

对每个待发布老师执行（参照 findclass-teacher-publish 干跑规则）：
- Markdown 可解析
- name, phone, personal_intro, avatar 不为空
- 图片文件存在
- 手机号/姓名无数据库重复（首次新增）

### 3. 逐条发布

按顺序对每个老师执行 findclass-teacher-publish 的发布脚本。
每条发布后立刻记录结果。

### 4. 生成批量报告

发布结束后输出：
- 成功数量 / 失败数量 / 跳过数量
- 成功清单（含 sync_id）
- 失败清单（含原因）
- 需要人工干预的异常

## 操作原则

- 批量发布 ≠ 全量发布。仍然逐条执行，保证每条都走完整流程
- 一条失败不阻塞后续，记录后继续下一条
- 发布前必须预检，不要把明显有问题的老师推出去
- 每条发布后立刻回写本地状态（sync_id / publish_status / publish_time）
