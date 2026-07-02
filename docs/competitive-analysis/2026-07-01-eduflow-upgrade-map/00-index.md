---
title: EduFlow 竞品与参考项目升级地图索引
date: 2026-07-01
status: draft
tags:
  - EduFlow
  - competitive-analysis
  - agent-workforce
  - workflow
  - Feishu
---

# EduFlow 竞品与参考项目升级地图索引

这个文件夹把 2026-07-01 这一轮外部参考项目分析集中到一起，目标不是做竞品列表，而是沉淀 EduFlow 下一阶段的升级方向。

## 文件

| 文件 | 内容 |
| --- | --- |
| `01-claude-squad-agent-orchestrator-container-use-gap-report.md` | claude-squad、agent-orchestrator、container-use 对 EduFlow 的差距报告 |
| `02-qoder-eduflow-vs-oh-my-claudecode-analysis.md` | Qoder 对 oh-my-claudecode 与 EduFlow 的对比分析 |
| `03-synthesis-upgrade-roadmap.md` | 综合五类参考项目后的 EduFlow 升级总纲 |
| `04-ecc-missing-capabilities-analysis.md` | ECC 对 EduFlow 缺失的能力目录、选择安装、skill 治理、安全审计和持续学习能力补全 |
| `05-current-eduflow-planning-recalibration.md` | 结合当前 EduFlow 代码与运行态，对整体规划合理性和优先级做二次校准 |
| `06-claude-code-module-prompts.md` | 面向 Claude Code 执行的模块化提示词包，覆盖 P0/P1/P2 分层实施 |
| `07-git-baseline-adjustment-2026-07-02.md` | 新 Git 基线 `91f0a87` 后，对 README/视觉入口与执行提示词的轻量调整 |
| `08-residency-phase1-branch-impact-2026-07-02.md` | 新分支 `feat/2026-07-01-residency-phase1` 对 cards_v2、温备驻留、主群外显和执行提示词的结构性影响 |

## 参考项目定位

| 项目 | 借鉴层 |
| --- | --- |
| `claude-squad` | 多 agent session 操盘、worktree 隔离、终端操作密度 |
| `agent-orchestrator` | durable facts、外部反馈回流、IDE 级状态闭环 |
| `container-use` | container + branch 的隔离执行现场、command log、merge/apply/discard |
| `oh-my-claudecode` | 阶段化编排、模型分层、验证循环、HUD、skillify、handoff、critic |
| `affaan-m/ECC` | 能力目录、选择安装、rules/skills/agents 治理、跨 CLI 分发、doctor/repair、安全扫描、持续学习 |

## 总结一句话

EduFlow 不应该追随任何一个项目的外形。它应该吸收它们各自最强的局部能力，升级成：

**飞书可见的公司 AI 员工操作系统：员工有岗位身份、CLI/模型能力画像、可选择安装的能力包、workflow 快速通道、隔离执行现场、证据验证闭环、外部反馈回流和持续沉淀机制。**
