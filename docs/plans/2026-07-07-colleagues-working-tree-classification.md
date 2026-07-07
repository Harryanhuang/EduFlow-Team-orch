# 同事 Working Tree 改动分类清单（2026-07-07 17:30）

> 本次 pilot commit (`ac618b88`) 之后留在 working tree 的所有改动。
> 这些**不是**本次会话做的，**不在 `ac618b88` commit 里**，但因为同分支 working tree 出现，
> 你后续可能想 commit 它们或单独建分支。

## 一、Modified Files（16 个，1382 +/103 -）

按主题分 5 组：

### 1. Runtime Failover / Watchdog 强化（最大组）

| 文件 | +N / -N | 主题 |
|------|---------|------|
| `src/eduflow/commands/watchdog.py` | +278 / -22 | watchdog 命令增强 |
| `src/eduflow/runtime/watchdog.py` | +15 / -2 | runtime watchdog 核心 |
| `tests/unit/test_commands_watchdog.py` | +160 / -0 | 新测试 |
| `src/eduflow/commands/router.py` | +75 / -6 | router 命令 |
| `src/eduflow/commands/health.py` | +24 / -0 | health 命令 |
| `src/eduflow/cli.py` | +3 / -0 | CLI dispatch |
| `src/eduflow/commands/runtime.py` | +3 / -0 | runtime 入口 |

**推测目的**：基于最近 `c1a53206 Stabilize EduFlow runtime failover routing` commit 后续工作，可能是
`T-118` 反思后对 runtime failover 的进一步加固。

### 2. Feishu / Cards（卡片层）

| 文件 | +N / -N | 主题 |
|------|---------|------|
| `src/eduflow/feishu/cards_v2_schema.py` | +11 / -0 | **T-144**: 加 `worker_review` 卡片权限（rename 后跟进） |
| `src/eduflow/feishu/catchup.py` | +118 / -12 | 消息 catchup 增强 |
| `src/eduflow/feishu/slash.py` | +75 / -0 | slash 命令 |
| `src/eduflow/commands/say.py` | +28 / -6 | say 命令（feishu 适配） |
| `tests/unit/test_feishu_catchup.py` | +58 / -7 | 测试 |
| `tests/unit/test_feishu_slash.py` | +72 / -0 | 测试 |

**推测目的**：feishu 卡片权限表跟进 T-139 rename；catchup 逻辑增强。

### 3. Tasks Store（>30 处 review_course hard-coded）

| 文件 | +N / -N | 主题 |
|------|---------|------|
| `src/eduflow/store/tasks.py` | +138 / -6 | tasks store 大改 |

**推测目的**：可能包括全局 `review_course → worker_review` rename，或者
T-118 反思后的任务存储调整。**变更量大，建议单独看 diff 再评估**。

### 4. 配置

| 文件 | +N / -N | 主题 |
|------|---------|------|
| `eduflow.toml` | +144 / -6 | toml 配置（runtime registry / 容灾链等） |

**推测目的**：和 runtime failover 配套，或新的容灾链。

### 5. Skill 文档

| 文件 | +N / -N | 主题 |
|------|---------|------|
| `.claude/skills/agent-hiring-checklist.md` | +180 / -36 | agent 招聘 checklist |

## 二、Untracked Files（16 个）

| 文件 | 推测 |
|------|------|
| `.bak-stash-2026-07-06-T128/` | 历史 stash 备份目录，**应删除或归档** |
| `.claude/skills/review-syllabus-skill/SKILL.md.bak` | 备份文件，**应删除** |
| `T-118-4-questions-summary-2026-07-06.md` | T-118 反思的 4 问 summary（**注意**：这是我昨天反思的源头之一） |
| `content/igcse-addmath-0606/topic-outlines/T1.md` | pilot T-122 的真实产物（worker course 在 pilot 时写的） |
| `docs/competitive-analysis/2026-07-07-eduflow-vs-claudeteam-product-feature-comparison.md` | 竞品分析，**与本次 pilot 无关** |
| `docs/plans/2026-07-06-eduflow-production-contract-pilot-packages.md` | **Obsidian vault 里的 plan**（一直是 untracked，不应 commit） |
| `docs/plans/2026-07-07-claudeteam-upstream-borrowing-plan.md` | 同事的另一个 plan |
| `scripts/dispatch_weekly_report.sh` | 新脚本 |
| `skills/eduflow-manager-troubleshoot/` | 新 skill（之前 message 里见到过） |
| `src/eduflow/commands/agent.py` | 新命令 |
| `src/eduflow/commands/daemon.py` | 新命令 |
| `src/eduflow/commands/runtime_env_clean.py` | 新命令 |
| `tests/unit/test_commands_agent.py` | 测试 |
| `tests/unit/test_commands_daemon.py` | 测试 |
| `tests/unit/test_task_archive.py` | 测试 |

## 三、建议

### 立刻清理
```bash
rm -rf .bak-stash-2026-07-06-T128/
rm .claude/skills/review-syllabus-skill/SKILL.md.bak
```

### 单独建分支
对 runtime failover / feishu / tasks.py 的改动，单独建分支递交：
```bash
git checkout -b chore/2026-07-07-runtime-failover-followup
git add src/eduflow/commands/watchdog.py src/eduflow/runtime/watchdog.py \
        tests/unit/test_commands_watchdog.py src/eduflow/commands/router.py \
        src/eduflow/commands/health.py src/eduflow/cli.py \
        src/eduflow/commands/runtime.py
git commit -m "chore: runtime failover watchdog followup"
```

对 `store/tasks.py` 的大改动（138 行），**先看 diff 再决定**：
```bash
git diff src/eduflow/store/tasks.py | head -100
```

### 不 commit
- Obsidian vault 文档（`docs/plans/...` 中由 Obsidian 管理的）
- 临时 stash 备份