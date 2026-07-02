---
name: findclass-teacher-feishu-sync
description: Use when syncing reviewed teacher records from Feishu Base into the FindClass Obsidian teacher vault, especially for reading a specific teacher record, downloading avatar and gallery attachments, generating Markdown from the local teacher template, and placing files into the correct Obsidian folders.
---

# FindClass Teacher Feishu Sync

把飞书老师表单中的“已审核”老师资料，稳定同步到 Obsidian 老师资料库。

这个 skill 只负责：

1. 从飞书 Base 读取老师记录
2. 下载头像和展示图到正确目录
3. 按模板生成 Obsidian Markdown
4. 把老师资料落到指定知识库路径

它不负责：

- 把老师资料发布回 FindClass 服务器
- 自动修改旧飞书表单题目
- 批量全量导入所有老师

## 什么时候用

这些场景直接用：

- 用户说“把这条飞书老师记录同步到 Obsidian”
- 用户说“把已审核通过的老师资料落到知识库”
- 用户说“把飞书里的老师信息和图片下载到老师资料文件夹”
- 用户要重复执行同一套“飞书 -> Obsidian 老师资料”流程

这些场景不要硬套：

- 用户要处理的是题库 PDF，不是老师资料
- 用户要发布老师到服务器
- 用户只有表单截图，没有实际 Base 记录

## 路径配置

本流程的路径支持通过环境变量覆盖，缺省使用下面的默认值：

| 变量 | 缺省值 |
|------|--------|
| `$FINDCLASS_OBSIDIAN_ROOT` | `/Volumes/Halobster/Obsidian Edu/留学公司知识库` |
| `$FINDCLASS_TEACHER_TEMPLATE` | `$FINDCLASS_OBSIDIAN_ROOT/10-老师信息资料文件夹/_模板/老师资料模板.md` |
| `$FINDCLASS_TEACHER_TEXT_DIR` | `$FINDCLASS_OBSIDIAN_ROOT/10-老师信息资料文件夹/老师基本资料（文字）/老师资料` |
| `$FINDCLASS_TEACHER_AVATAR_DIR` | `$FINDCLASS_OBSIDIAN_ROOT/10-老师信息资料文件夹/老师头像（图片）` |
| `$FINDCLASS_TEACHER_GALLERY_DIR` | `$FINDCLASS_OBSIDIAN_ROOT/10-老师信息资料文件夹/老师好评图片及展示（图片）` |

使用时在脚本/命令中优先引用环境变量，未设置时以上述缺省值回退。

当前缺省路径（即上述变量未设置时）：

- Obsidian 根目录：`/Volumes/Halobster/Obsidian Edu/留学公司知识库`
- 模板：`/Volumes/Halobster/Obsidian Edu/留学公司知识库/10-老师信息资料文件夹/_模板/老师资料模板.md`
- 老师文字资料目录：`/Volumes/Halobster/Obsidian Edu/留学公司知识库/10-老师信息资料文件夹/老师基本资料（文字）/老师资料`
- 老师头像目录：`/Volumes/Halobster/Obsidian Edu/留学公司知识库/10-老师信息资料文件夹/老师头像（图片）`
- 老师展示图目录：`/Volumes/Halobster/Obsidian Edu/留学公司知识库/10-老师信息资料文件夹/老师好评图片及展示（图片）`

## 当前飞书 Base 约定

当前已验证可用的 Base：

- base token：`TZwnb0QT8aXD4OsZVwkcYZpAnUd`
- table id：`tblG3S7C9nOaxbd2`
- 主表名：`老师资料采集表`

当前字段顺序已经验证过，核心字段如下：

- `老师姓名`
- `手机号`
- `所在城市`
- `教学阶段`
- `擅长科目`
- `授课方式`
- `授课语言`
- `简版个人简介`
- `详细个人简介`
- `教学风格`
- `教学年限`
- `带过学生数`
- `教学时长（小时）`
- `头像`
- `好评图 / 展示图`
- `飞书记录状态`
- `备注`

## 执行前必须做的事

先读取这些 skill / reference：

1. `../lark-shared/SKILL.md`
2. `../lark-base/SKILL.md`
3. `../lark-base/references/lark-base-record-read-sop.md`
4. `../lark-base/references/lark-base-record-get.md`
5. `../lark-base/references/lark-base-record-download-attachment.md`

如果是第一次进入这个流程，还要顺手确认：

- `lark-cli` 可用
- 当前可用 `--as bot`
- Base token 和 table id 没变

## 标准流程

### 1. 先定位记录

优先用下面两种方式之一：

- 已知 `record_id`：直接 `+record-get`
- 不知道 `record_id`：先 `+record-list` 或 `+record-search`

如果用户明确说“同步刚刚提交的那条”，通常先读最近几条记录，再人工判断目标。

### 2. 确认记录是否适合同步

至少检查：

- `老师姓名` 不为空
- `手机号` 不为空
- `简版个人简介` 不为空
- `详细个人简介` 不为空，或者至少有可用的替代正文
- `飞书记录状态` 最好是 `已审核`

如果状态还是 `待审核`，默认不要当成正式样本落库；除非用户明确要求继续。

### 3. 解析字段映射

飞书字段到 Markdown frontmatter 的映射：

| 飞书字段 | Markdown 字段 |
|---|---|
| 老师姓名 | `name` |
| 手机号 | `phone` |
| 所在城市 | `city` |
| 教学阶段 | `grade` |
| 擅长科目 | `good_subject` |
| 授课方式 | `class_type` |
| 授课语言 | `language` |
| 简版个人简介 | `personal_intro` |
| 教学风格 | `class_style` |
| 教学年限 | `work_year` |
| 带过学生数 | `take_student` |
| 教学时长（小时） | `teach_time` |
| 飞书记录状态 | 不直接写字段，只作为导入判断依据 |

补充约定：

- `source` 固定写 `feishu`
- `source_record_id` 写飞书 `record_id`
- `sync_id` 先写 `null`
- `publish_status` 默认写 `draft`
- `import_status` 写 `imported`
- `avatar` 只指向头像目录文件
- `gallery` 只放展示图目录文件
- 后续如果发布到服务器，`tb_user_info.info` 默认只使用 `personal_intro`
- 不要把整篇 Markdown 正文直接写入服务器简介字段

### 3.1 字段速查表

后续手工排查或补字段时，优先按这张表核对：

| 飞书字段 | Markdown 字段 | 常见值示例 |
|---|---|---|
| 老师姓名 | `name` | `黄老师Harry（测试）` |
| 手机号 | `phone` | `13970730859` |
| 所在城市 | `city` | `深圳福田` |
| 教学阶段 | `grade` | `IGCSE;A-Level` |
| 擅长科目 | `good_subject` | `数学` |
| 授课方式 | `class_type` | `深圳线下;线上` |
| 授课语言 | `language` | `中英双语` |
| 简版个人简介 | `personal_intro` | `北京大学数学系本科；哈佛大学计算机科学硕士；曾担任深国交计算机老师。` |
| 详细个人简介 | 正文 `## 个人简介` 素材 | 多行正文，仅本地展示使用 |
| 教学风格 | `class_style` | 一整段描述 |
| 教学年限 | `work_year` | `10` |
| 带过学生数 | `take_student` | `200` |
| 教学时长（小时） | `teach_time` | `8000` |
| 头像 | `avatar` | `[[老师姓名-头像.jpg]]` |
| 好评图 / 展示图 | `gallery` | `[[老师姓名-展示1.png]]` |

### 4. 下载附件

不要优先用 `lark-cli docs +media-download`。

Base 附件下载，优先使用：

```bash
lark-cli base +record-download-attachment
```

原因：

- 这个命令已经验证可用
- 支持直接按 `record_id + file_token` 下载
- 更适合 Base 附件

下载规则：

- 头像字段：下载到 `老师头像（图片）`
- 好评图 / 展示图字段：下载到 `老师好评图片及展示（图片）`
- 文件名统一改成：
  - `老师姓名-头像.<ext>`
  - `老师姓名-展示1.<ext>`
  - `老师姓名-展示2.<ext>`

如果没有展示图：

- `gallery: []`
- 正文里明确写“展示图：暂缺”

### 5. 生成 Markdown 文件

文件名规则：

```text
{老师姓名}__feishu_{record_id}.md
```

示例：

```text
黄老师Harry（测试）__feishu_rec27BNSceUxUo.md
```

最终落库目录固定为：

```text
/Volumes/Halobster/Obsidian Edu/留学公司知识库/10-老师信息资料文件夹/老师基本资料（文字）/老师资料
```

不要放到：

- `老师基本资料（文字）` 根目录
- 其他临时目录
- skill 工作目录

除非用户明确要求改目录，否则一律写到上面这个固定文件夹。

frontmatter 至少要包含：

- `title`
- `created`
- `updated`
- `tags`
- `name`
- `source`
- `source_record_id`
- `sync_id`
- `phone`
- `city`
- `grade`
- `good_subject`
- `class_type`
- `language`
- `work_year`
- `take_student`
- `teach_time`
- `class_style`
- `personal_intro`
- `avatar`
- `gallery`
- `import_status`
- `publish_status`

### 5.1 标准 frontmatter 示例

后续生成老师资料时，优先贴近这个结构：

```yaml
---
title: "黄老师Harry（测试）"
created: 2026-06-16
updated: 2026-06-16
tags: [teacher, feishu, reviewed]

name: "黄老师Harry（测试）"
source: "feishu"
source_record_id: "rec27BNSceUxUo"
sync_id: null

phone: "13970730859"
email: ""
province: ""
city: "深圳福田"
grade: "IGCSE;A-Level"
good_subject: "数学"

good_field: ""
class_type: "深圳线下;线上"
language: "中英双语"
price: null
star: 5.0
work_year: 10
take_student: 200
teach_time: 8000
class_style: "这里放教学风格整段文字"
personal_intro: "这里放 1 到 2 句简版简介"

avatar: "[[黄老师Harry（测试）-头像.jpg]]"
gallery:
  - "[[黄老师Harry（测试）-展示1.png]]"
files: []

import_status: "imported"
import_time: 2026-06-16

publish_status: "draft"
publish_time: null
content_hash: null
last_error: null
---
```

注意：

- `grade`、`class_type` 如果飞书里是多选，统一用分号拼接
- `price`、`sync_id` 没有就先保留 `null`
- `gallery` 没有图时写空数组 `[]`
- `personal_intro` 保持短，正文里的“个人简介”再放完整版本
- 如果后续执行 `Obsidian -> 服务器` 发布，服务器简介字段优先取 `personal_intro`

### 6. 正文结构

正文优先沿用当前老师资料模板，不要临时造新结构。

建议至少保留：

- `## 个人简介`
- `## 教学特色`
- `## 授课范围`
- `## 适合的学生类型`
- `## 当前从飞书拿到的真实字段`
- `## 附件清单`
- `## 录入完成前自查`

如果飞书里没有“适合的学生类型”，可以根据详细简介和教学风格提炼 3 到 4 条，但不要编造夸张结果。

### 7. 校验

落库后至少检查：

1. Markdown 文件已创建
2. `source_record_id` 正确
3. `personal_intro` 不为空
4. 头像文件确实在头像目录
5. 展示图文件确实在展示图目录
6. Markdown 里的图片链接文件名和本地文件一致

## 关键命令模式

### 读取记录

```bash
lark-cli base +record-get \
  --base-token TZwnb0QT8aXD4OsZVwkcYZpAnUd \
  --table-id tblG3S7C9nOaxbd2 \
  --record-id <record_id> \
  --as bot
```

### 下载头像

```bash
lark-cli base +record-download-attachment \
  --base-token TZwnb0QT8aXD4OsZVwkcYZpAnUd \
  --table-id tblG3S7C9nOaxbd2 \
  --record-id <record_id> \
  --file-token <avatar_file_token> \
  --output "./老师姓名-头像.jpg" \
  --overwrite \
  --as bot
```

### 下载展示图

```bash
lark-cli base +record-download-attachment \
  --base-token TZwnb0QT8aXD4OsZVwkcYZpAnUd \
  --table-id tblG3S7C9nOaxbd2 \
  --record-id <record_id> \
  --file-token <gallery_file_token> \
  --output "./老师姓名-展示1.png" \
  --overwrite \
  --as bot
```

## 已验证样本

这条样本已完整跑通过：

- 记录 ID：`rec27BNSceUxUo`
- 老师：`黄老师Harry（测试）`
- Markdown：
  `/Volumes/Halobster/Obsidian Edu/留学公司知识库/10-老师信息资料文件夹/老师基本资料（文字）/老师资料/黄老师Harry（测试）__feishu_rec27BNSceUxUo.md`
- 头像：
  `/Volumes/Halobster/Obsidian Edu/留学公司知识库/10-老师信息资料文件夹/老师头像（图片）/黄老师Harry（测试）-头像.jpg`
- 展示图：
  `/Volumes/Halobster/Obsidian Edu/留学公司知识库/10-老师信息资料文件夹/老师好评图片及展示（图片）/黄老师Harry（测试）-展示1.png`

## 操作原则

- 一次只同步 1 位老师
- 不全量扫飞书整表
- 不覆盖已经人工深度修改过的 Obsidian 文件，除非用户明确要求
- 头像只进头像目录
- 展示图只进展示图目录
- 没有把握的字段宁可留空，也不要编造
- 如果图片下载失败，先落文字版，并明确记录失败原因

## 建议输出

完成后对用户至少交代：

1. Markdown 放在哪里
2. 头像放在哪里
3. 展示图放在哪里
4. 有没有缺字段
5. 有没有附件还没下成功
