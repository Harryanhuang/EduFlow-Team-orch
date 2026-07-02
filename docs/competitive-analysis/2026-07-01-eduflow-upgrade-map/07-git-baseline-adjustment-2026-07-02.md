---
title: EduFlow 新 Git 基线后的规划微调
date: 2026-07-02
status: draft
tags:
  - EduFlow
  - git-baseline
  - README
  - Feishu
  - execution-prompts
---

# EduFlow 新 Git 基线后的规划微调

## 当前 Git 基线

当前最新 HEAD：

```text
91f0a87 Clarify project entrypoint with visual README
```

该 commit 主要变化：

```text
M README.md
A docs/media/README.md
A docs/media/eduflow-team-orch-hero.png
A docs/media/eduflow-team-orch-hero.svg
A docs/media/runtime-architecture.png
A docs/media/runtime-architecture.svg
A docs/media/workflow-guided-delivery.png
A docs/media/workflow-guided-delivery.svg
```

## 对原规划的影响

结论：**P0 执行顺序不需要推翻，只需要略改 M0/M3/M5 的提示词重点。**

原因：

- 新 commit 强化了 README 作为项目入口的定位。
- 新增 visual README / runtime architecture / workflow-guided-delivery 图，说明 EduFlow 的公开叙事已经更清晰：多 CLI agent、Feishu 控制面、tmux runtime、本地任务台账、workflow registry。
- 这些内容不会改变“先补状态可信层”的判断。
- 但它要求后续 Claude Code 执行时，必须把 README 和 `docs/media/` 当成当前产品叙事基线，而不是只读旧 docs/plans。

## 需要微调的模块

### M0：只读基线审计

应补充：

- 读取 `docs/media/README.md`。
- 运行 `git show --stat --oneline --decorate --name-status HEAD`。
- 在基线报告中记录当前 HEAD 和 README 入口变化。
- 检查 README 中的产品定位是否与 `05-current-eduflow-planning-recalibration.md` 一致。

### M3：Feishu Snapshot Cards

应补充：

- 卡片语言要贴近 README 的公开叙事：老板通过飞书看团队状态，manager 负责任务拆分、派发、回收、复盘和关口检查。
- 不要把 Feishu card 做成开发者日志墙。
- `employee/team snapshot` 第一屏优先显示：谁在做、卡在哪、下一步谁接、是否需要老板判断。

### M5：Harness Surface Audit

应补充：

- 扫描 `docs/media/README.md` 和 README 引用的三张图。
- 把 README/视觉叙事也纳入 surface drift 检查：如果代码能力、文档叙事、飞书外显三者不一致，需要标记 drift。

## 不需要改的部分

### P0 顺序不变

```text
M0 -> M1 -> M2 -> M3 -> M4/M5
```

原因：新 commit 只是强化项目入口和视觉表达，没有改变当前真实瓶颈。当前真实瓶颈仍然是：

```text
已有 primitive 很多，但飞书里还不能稳定地 30 秒看懂：
谁在做、卡在哪、证据够不够、下一步谁接、是否可收口。
```

### 不提前做 container-use

README 新增架构图不代表要立刻做 container-use。container-use 仍然属于 P2，高风险 builder 任务和批量迁移场景再接。

### 不提前做 selective install

ECC 的能力供应链仍然是中长期方向。当前仍应先做 read-only asset registry / drift-check，再演进到 capability pack / selective install。

## 给 Claude Code 的额外提醒

后续执行 `06-claude-code-module-prompts.md` 时，应在总控提示词前加一句：

```text
开始前先记录当前 Git HEAD，并读取 README.md 与 docs/media/README.md。当前 HEAD 若包含 README/视觉入口更新，后续状态可信层实现必须保持与 README 的产品叙事一致：EduFlow 是飞书可见的本地可审计 AI 团队操作系统，不是纯代码工具或聊天机器人 demo。
```

## 最终判断

这次 Git 更新让 EduFlow 的“对外入口”更清楚了，所以规划文档只需要小修：

- M0 更重视 README / media / HEAD。
- M3 更贴近飞书第一屏产品叙事。
- M5 把文档视觉叙事也纳入 drift audit。

但实施主线不变：

```text
先统一状态可信度
→ 再解释现有 gate
→ 再治理资产漂移
→ 再做隔离 workspace
→ 再做 capability pack / selective install
```
