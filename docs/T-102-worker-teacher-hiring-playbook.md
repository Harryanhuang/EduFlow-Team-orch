---
name: worker-teacher-hiring-playbook
description: "T-102 worker_teacher 雇佣上线全流程复盘：雇佣步骤、skill 安装、问题发现、改进建议。后续雇佣新 agent 时可参考。"
metadata:
  type: reference
  generated_by: Luke_recorder
  date: 2026-06-26
  task_ref: T-102.b
---

# T-102 worker_teacher 雇佣上线 — 流程复盘与 skill 沉淀

## 一、背景

FindClass 小程序需要上架老师信息，涉及三个环节：飞书表单收集 → Obsidian 编辑整理 → 上传服务器。老板决定雇佣一个新 agent `worker_teacher` 专职负责。

## 二、完整时间线

| 时间 | 事件 | 角色 |
|------|------|------|
| ~11:03 | manager 派发 T-102 给 worker_builder：雇佣 FindClass 老师资料整理员 | manager → worker_builder |
| ~11:03 | worker_builder 接单，开始搭建框架 | worker_builder |
| ~11:14 | worker_builder 报完工：新 agent worker_teacher 已雇佣，正在初始化中 | worker_builder → chat |
| ~11:16 | 老板追补指令：去电脑上的 codex 找相关 skill 安装给 worker_teacher，涉及飞书表单/Obsidian/上传三个环节 | boss → team |
| ~11:16 | manager 派补充指令给 worker_builder | manager → worker_builder |
| ~11:16 | worker_builder 接单，搜索 codex 目录 | worker_builder |
| ~11:17 | worker_builder 找到 4 个 FindClass 系列 skill 并安装 | worker_builder |
| ~11:17 | manager 派 T-102.b 给 Luke_recorder：沉淀雇佣流程 skill，分析改进空间 | manager → Luke_recorder |

## 三、雇佣流程拆解（worker_builder 实际执行的动作）

### 3.1 第一阶段：创建新 agent

1. **读取现有 agent 模板** — 参照已有 worker_* 的身份文件结构和 identity.md 格式
2. **生成 worker_teacher/identity.md** — 角色描述：FindClass 老师资料整理员，负责飞书表单收集、Obsidian 编辑整理、上传服务器
3. **配置 tmux window** — 分配 window 8，设置 pane 和 CLI adapter
4. **初始化 runtime** — tea chain 配置、inbox、workspace、记忆系统就绪
5. **报完工** — worker_builder `say` 到群：「新 agent worker_teacher 已雇佣，正在初始化中」

### 3.2 第二阶段：技能安装（老板追补指令）

worker_builder 搜索 codex 目录（~/.codex/），找到并安装了 4 个 skill：

| Skill 名称 | 用途 | 来源 |
|-----------|------|------|
| `findclass-importer` | 本地试卷 PDF 导入 FindClass 题库（扫描、可恢复上传、审计、异常清单） | codex |
| `findclass-teacher-feishu-sync` | 飞书 Base → Obsidian 老师资料同步（读表、下载头像/展示图、生成 Markdown） | codex |
| `findclass-teacher-image-to-md` | 老师信息图 → Obsidian Markdown（字段归一化、class_style 展开/压缩） | codex |
| `findclass-teacher-publish` | Obsidian 老师资料 → FindClass 服务器发布（上传图、写 tb_user/tb_user_info、回写 sync_id） | codex |

此外，worker_builder 还产出了 **`new-agent-onboarding.md`**（20KB，六大模块全覆盖）：记忆系统、Workflow 派工链路、任务对接、身份文件、通讯规范、团队经验教训。

## 四、可复用的经验 / skill 沉淀

### 4.1 已产出的 skill 文件

| 文件 | 内容概要 | 可复用性 |
|------|---------|---------|
| `.claude/skills/new-agent-onboarding.md` | 新员工入职全流程指南（6 大模块，含自检命令） | 高 — 任何新 agent 可用 |
| `.claude/skills/findclass-importer/` | FindClass 题库导入流程 | 中 — 特定业务域 |
| `.claude/skills/findclass-teacher-feishu-sync/` | 飞书 → Obsidian 老师同步 | 中 — 特定业务域 |
| `.claude/skills/findclass-teacher-image-to-md/` | 老师图片 → Markdown | 中 — 特定业务域 |
| `.claude/skills/findclass-teacher-publish/` | Obsidian → 服务器发布 | 中 — 特定业务域 |

### 4.2 雇佣流程通用步骤（可沉淀为 `agent-hiring-checklist`）

```
1. 明确角色定义（名称、职责、运行 CLI）
2. worker_builder 执行：创建 identity.md + tmux window + runtime 配置
3. 安装通用 skill：new-agent-onboarding.md（六大模块）
4. 安装业务 skill：根据职责域搜索和安装对应 skill
5. 验证：eduflow status <agent> 确认初始化完成
6. 记忆系统就绪：eduflow recall <agent> 确认空或已有初始记忆
7. 派第一个测试任务验证通讯链路
```

## 五、正式操作中的提升空间分析

### 5.1 流程效率

| 问题 | 描述 | 严重度 | 改进建议 |
|------|------|--------|---------|
| 追补指令 | 雇佣完工后老板追加了 skill 安装指令，导致第二轮 dispatch | 低 | 在 T-102 初次派发时就包含「雇佣 + 安装对应 skill」的完整要求，避免追补 |
| skill 搜索手动化 | worker_builder 需要手动搜索 ~/.codex/ 找相关 skill，没有自动发现机制 | 中 | 建立 skill 注册表（registry），新 agent 创建时自动匹配职责域对应的 skill |
| 无预检 | 没有在安装前验证 skill 的兼容性和依赖 | 低 | 增加 skill 安装前的 validate 步骤 |

### 5.2 skill 覆盖率

| 缺口 | 描述 | 建议 |
|------|------|------|
| 飞书表单修改 skill | 当前只有「读取已审核表单」的 sync skill，没有「修改表单字段/结构」的 skill | 补充 findclass-form-builder skill |
| 批量处理 skill | findclass-teacher-publish 明确不支持批量发布 | 补充 findclass-batch-publish skill |
| 错误回滚 skill | 发布失败后的图片清理/回滚没有封装 | 补充 findclass-publish-rollback skill |
| 质量检查 skill | 老师 Markdown 生成后没有自动校验 skill（如字段完整性、class_style 长度） | 补充 findclass-teacher-quality-check skill |

### 5.3 配置准确性

| 问题 | 描述 | 建议 |
|------|------|------|
| model 字段为空 | worker_teacher identity.md 中 `model: \`\`` 为空 | worker_builder 创建时应自动填充当前会话的默认模型 |
| 无职责域声明 | worker_teacher 的 identity 没有明确声明 `domain: findclass-teacher`，无法用于自动 skill 匹配 | 在 identity.md 中增加 `## Domain` 段 |
| 路径硬编码 | 多个 FindClass skill 中路径硬编码为 `/Volumes/Halobster/Obsidian Edu/...` | 提取为环境变量或配置文件，避免换机器就失效 |

### 5.4 协作流程

| 问题 | 描述 | 建议 |
|------|------|------|
| manager 没有验收环节 | worker_builder 报完工后，manager 直接派下一个任务，没有验证 worker_teacher 是否真的可用 | 增加验收步骤：派一个最小测试任务（如 `eduflow status worker_teacher`）确认通讯 |
| 新员工没有自我介绍 | worker_teacher 初始化后没有向群内报到 | 在 onboarding skill 中增加「向群内报到」步骤 |

## 六、改进建议汇总

### 立即执行（P0）
1. 补齐 worker_teacher identity.md 中的 model 字段
2. 在 new-agent-onboarding.md 中增加「新员工群内报到」步骤
3. manager 派单后增加最小验证步骤

### 短期（P1）
4. 建立 skill registry 机制：按 domain 自动匹配 skill
5. 补充 4 个缺失的 skill（form-builder、batch-publish、rollback、quality-check）
6. 将 FindClass skill 中的硬编码路径提取为配置

### 中期（P2）
7. 编写 `agent-hiring-checklist.md` skill，将通用步骤标准化
8. 实现「雇佣 + 技能安装」一次性派发，避免追补指令
