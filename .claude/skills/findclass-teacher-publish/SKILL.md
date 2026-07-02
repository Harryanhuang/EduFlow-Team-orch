---
name: findclass-teacher-publish
description: Use when publishing one reviewed teacher Markdown file from the Obsidian teacher vault into the FindClass teacher database, especially for uploading avatar and gallery images, inserting or updating tb_user and tb_user_info, and writing sync_id and publish status back into the Markdown file.
---

# FindClass Teacher Publish

把 Obsidian 里的单个老师资料发布到 FindClass 服务器。

当前这个 skill 是基于已经跑通的真实链路整理出来的，适合重复执行同一类动作：

1. 读取老师 Markdown
2. 解析 frontmatter
3. 生成上传版 `webp` 压缩图
4. 上传头像和展示图
5. 写入或更新 `tb_user` 和 `tb_user_info`
6. 回写本地 `sync_id`、`publish_status`、`publish_time`

## 什么时候用

这些场景直接用：

- 用户说“把这位老师上传到服务器”
- 用户说“测试一下 Obsidian 老师资料能不能发布到 FindClass”
- 用户说“把已整理好的老师资料正式上线”
- 用户说“把这位已经有 `sync_id` 的老师重新更新到服务器”

这些场景不要硬套：

- 用户要从飞书同步到 Obsidian
- 用户要批量全量上传很多老师

## 当前能力边界

这个 skill 现在支持两种模式：

- **首次新增上线**
- **已有 `sync_id` 的单条更新发布**

当前还**没有**封装好的部分：

- 批量发布
- 自动回滚已上传但未入库的图片

## 路径配置

本 skill 的路径支持通过环境变量覆盖，缺省使用下面的默认值：

| 变量 | 缺省值 |
|------|--------|
| `$FINDCLASS_OBSIDIAN_ROOT` | `/Volumes/Halobster/Obsidian Edu/留学公司知识库` |
| `$FINDCLASS_TEACHER_TEXT_DIR` | `$FINDCLASS_OBSIDIAN_ROOT/10-老师信息资料文件夹/老师基本资料（文字）/老师资料` |
| `$FINDCLASS_TEACHER_AVATAR_DIR` | `$FINDCLASS_OBSIDIAN_ROOT/10-老师信息资料文件夹/老师头像（图片）` |
| `$FINDCLASS_TEACHER_GALLERY_DIR` | `$FINDCLASS_OBSIDIAN_ROOT/10-老师信息资料文件夹/老师好评图片及展示（图片）` |
| `$FINDCLASS_TEACHER_WEBP_DIR` | `$FINDCLASS_OBSIDIAN_ROOT/10-老师信息资料文件夹/_上传压缩图（webp）` |

使用时优先引用环境变量，未设置时以上述缺省值回退。

默认老师 Markdown 目录：

`/Volumes/Halobster/Obsidian Edu/留学公司知识库/10-老师信息资料文件夹/老师基本资料（文字）/老师资料`

默认图片目录：

- 头像：`/Volumes/Halobster/Obsidian Edu/留学公司知识库/10-老师信息资料文件夹/老师头像（图片）`
- 展示图：`/Volumes/Halobster/Obsidian Edu/留学公司知识库/10-老师信息资料文件夹/老师好评图片及展示（图片）`

上传前自动生成的压缩图目录：

- `/Volumes/Halobster/Obsidian Edu/留学公司知识库/10-老师信息资料文件夹/_上传压缩图（webp）`

当前发布脚本：

`/Volumes/Halobster/Codex相关/tools/findclass_teacher_publish.py`

## 执行前必须读

先读这些内容：

1. `../findclass-teacher-feishu-sync/SKILL.md`
2. `/Volumes/Halobster/Obsidian Edu/留学公司知识库/09-公司AI赋能通用知识/07-findclass老师资料上传方案/00-完整方案.md`
3. 当前要发布的老师 Markdown 文件

## 发布规则

### 1. 只处理单个老师

一次只发布 1 位老师，不做全量。

### 2. 只发布已整理好的 Markdown

至少确认这些字段不为空：

- `name`
- `phone`
- `personal_intro`
- `avatar`

如果图片文件找不到，不要继续发。

### 3. `tb_user.images` 的组成

由下面两部分按顺序组装：

1. 头像 URL
2. 展示图 URL 列表

也就是：

```text
images = [avatar_url] + gallery_urls
```

### 4. 图片上传前先转 `webp`

这是当前默认规则。

- Obsidian 里保留原图
- 发布脚本自动生成上传版 `webp`
- 真正上传到服务器的是压缩后的 `webp`

当前压缩规则：

- 头像：最长边不超过 `1200px`
- 展示图：最长边不超过 `1600px`
- 压缩图会按老师 Markdown 文件名单独落目录，避免互相覆盖

这样做的好处是：

- 本地原始素材不丢
- 服务器图片更轻
- 后面重发时可以继续自动覆盖更新上传版

### 5. 服务器简介字段只用 `personal_intro`

这是当前最重要的规则之一。

发布时：

- `tb_user_info.info` 默认只写 `personal_intro`
- 不要把整篇 Markdown 正文塞进 `info`

例如：

```text
北京大学数学系本科
哈佛大学计算机科学硕士
曾担任深国交计算机老师
```

这种短简介才是当前服务器简介字段应该存的内容。

### 6. 发布成功后的本地回写

无论是首次新增还是更新，成功后本地文件至少要保持这些状态：

1. `sync_id` 变成新生成的数字
2. `publish_status` 变成 `synced`
3. `publish_time` 写入当天日期

### 7. 首次新增的查重原则

首次发布前，先用：

- `phone`
- `name`

做数据库查重。

如果库里已经有同手机号或同姓名记录，默认停止，不直接继续新增。

### 8. 更新模式的处理原则

如果 Markdown 已经有 `sync_id`：

- 不再按姓名 / 手机号做新增查重
- 而是先确认服务器里这个 `sync_id` 真实存在
- 然后覆盖更新这位老师的主信息和扩展信息
- 图片也会重新上传，并重写 `images`

当前更新时会覆盖的重点字段包括：

- `tb_user`
  - `name`
  - `phone`
  - `email`
  - `province`
  - `city`
  - `grade`
  - `good_subject`
  - `images`
  - `status`
- `tb_user_info`
  - `price`
  - `star`
  - `info`
  - `work_year`
  - `take_student`
  - `teach_time`
  - `class_type`
  - `good_field`
  - `class_style`
  - `language`

其中：

- `tb_user_info.info` 依然只用 `personal_intro`
- `详细个人简介` 只保留在 Obsidian 本地正文中

## 当前脚本用法

### 干跑

```bash
python3 /Volumes/Halobster/Codex相关/tools/findclass_teacher_publish.py \
  --markdown "/绝对路径/老师文件.md" \
  --dry-run
```

作用：

- 检查 Markdown 能否解析
- 检查头像和展示图能否找到
- 检查上传版 `webp` 能否成功生成
- 预判当前会走 `insert` 还是 `update`
- 不写服务器

### 正式发布

```bash
python3 /Volumes/Halobster/Codex相关/tools/findclass_teacher_publish.py \
  --markdown "/绝对路径/老师文件.md"
```

## 当前脚本真实验证样本

已验证样本：

- Markdown：
  `/Volumes/Halobster/Obsidian Edu/留学公司知识库/10-老师信息资料文件夹/老师基本资料（文字）/老师资料/黄老师Harry（测试）__feishu_rec27BNSceUxUo.md`
- 新生成 `sync_id`：
  `150`

说明当前这条链路已经至少跑通一次：

- 读 Markdown
- 生成上传版 `webp`
- 上传头像
- 上传展示图
- 新增 `tb_user`
- 新增 `tb_user_info`
- 回写本地状态

后续如果再次对这份 Markdown 执行脚本：

- 会自动走 `update` 模式
- 不会再报“已有 sync_id 无法发布”

## 操作原则

- 先干跑，再正式发布
- 不要跳过查重
- `sync_id` 已存在时，确认这是你要更新的那位老师
- 图片上传成功但数据库失败时，要明确告诉用户
- 回写失败时，也要明确告诉用户

## 完成后要向用户汇报什么

至少说清：

1. 是否发布成功
2. 这次走的是 `insert` 还是 `update`
3. `sync_id`
4. 本地文件是否已回写
5. 图片是否已上传
6. 服务器简介是否按 `personal_intro` 写入
