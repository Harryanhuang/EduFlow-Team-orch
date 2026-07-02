---
name: findclass-teacher-image-to-md
description: Use when converting a teacher profile image into a completed Obsidian teacher Markdown file for FindClass/Obsidian teacher vault workflows, including field normalization, class_style expansion/compression, and case整理, while keeping output aligned with upload-side field mappings.
---

# FindClass Teacher Image to Markdown

把老师信息图补成可用的 Obsidian Markdown。

## 什么时候用

这些场景直接用：

- 用户给老师信息图，要补全老师 Markdown
- 用户要把图片里的老师简介、教学风格、案例整理进现有文件
- 用户要让 `good_subject` / `good_field` 先对齐系统取值，再写入 Markdown

这些场景不要硬套：

- 直接上传服务器
- 批量改库
- 没有图片来源的纯猜写

## 核心规则

### 1. 先看图，再看现有 Markdown

先抽取图片里能确认的事实，再对照现有文件补字段，不要反过来猜。

### 2. `good_subject`

优先使用小程序系统里的真实取值。

- 只保留后续能一一对应的值
- 图片里更细的说法，若系统没有对应值，就归并到系统值
- 如果老师本身就是双学科或多学科老师，要把多个学科都保留下来，不要压成单学科
- 正文展示时也要同步体现双学科，不要只在字段里写出来

### 3. `good_field`

优先按系统里的课程体系名归并，不展开学校体系别名。

- `CIE`、`爱德思`、`AQA` 等按系统实际可映射的体系处理
- 不把体系内子标签拆成多个独立取值

### 4. `personal_intro`

只保留短简介。

- 保留学历背景、关键身份标签和一句总括
- 不塞 `class_style`、案例、课程清单

### 5. `class_style`

以约 220 字为参考长度，优先自然表达，不硬凑字数。

- 少于参考长度时，可以适度补足
- 超过参考长度时，删减到更紧凑的版本
- 重点写学科熟悉度、考纲把握、授课方式、个性化提分能力
- 不写学历背景、案例结果、课程清单
- 不为了凑字数加入空话或重复句

### 6. `经典个案`

- 只写图片里能确认的内容
- 模糊字样先保守处理，不脑补
- 统一整理成可读的短句

## 执行顺序

1. 读图抽取信息
2. 对齐 `good_subject` / `good_field`
3. 更新 frontmatter
4. 更新 `个人简介`、`教学特色`、`授课范围`
5. 更新 `class_style`
6. 整理 `经典个案`
7. 检查“缺失字段”是否和已补内容冲突
