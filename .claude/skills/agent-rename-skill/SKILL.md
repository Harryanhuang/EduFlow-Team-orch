---
name: agent-rename
description: Use when an agent needs to rename (保留功能/职责/记忆, 只改名字). 触发场景: 老板拍板「X 改名为 Y」、agent rename 但功能不变、agent-home 迁移、纯名字改名复用。
metadata:
  type: procedure
  generated_by: worker_builder
  date: 2026-07-07
  version: "1.1"
  source_task: T-149
  source_example: T-146 auto_ops → Sophon
when_to_use: 老板说"X 改名为 Y, 旧名退役"；agent rename 但功能不变；保持记忆/职责/数据完整继承；未来改名 (如 Monika → Monica) 可完全复用此 SOP。
---

# Agent Rename Skill — 改名不换功能 SOP

基于 T-146 (auto_ops → Sophon, 2026-07-07) 11 步全清单沉淀。

## 前置确认 (4 件)

- [ ] 老板明确拍板: 旧名退役 + 新名启用 (不要凭"我猜老板想改"自作主张)
- [ ] 拍板是否继承功能/职责/记忆 (如"继承全部" = cp -a agent-home/ + facts/ + log/)
- [ ] 拍板 CLI adapter (claude-code / codex-cli / ...)
- [ ] 拍板 runtime (minimax / mimo / kimi / ...) + fallback chain

## 7 步改名流程

### 1. 备份原 toml
```bash
cp eduflow.toml eduflow.toml.bak-$(date +%Y-%m-%d)-T<id>
```

### 2. toml 改段 (5 处)

```toml
# (a) 旧段改名为新段
[team.agents.<new>]
runtime = "<new>_backup_<model>"
role  = "<原 role 复制, 前加 T-<id> YYYY-MM-DD 由 <old> 改名为 <new> 标注>"
notes = "<原 notes 复制, 注明 T-<id> 改名前叫 <old>, 职责+记忆完整继承>"

# (b) 旧段新建为 archived (不删, 留 audit)
[team.agents.<old>]
archived = "YYYY-MM-DD 改名为 <new>, 历史 audit 保留"
enabled_for_dispatch = false
card_color = "<原 color>"
# 注: 不再设 runtime/role/specialty/tone/notes — 这些属性已迁到 <new> 段

# (c) 新 runtime_registry 段 (claude-code + <model>)
[runtime_registry.<new>_backup_<model>]
cli = "claude-code"
model = "sonnet"
provider = "anthropic-proxy"
env_profile = "claude_proxy_<model>_backup"
fallback_to = "<new>_backup_<model2>"
switch_on = ["spawn_failed", "ready_timeout", "rate_limit", ...]

# (d) 旧 runtime_registry 段保留作为 alias (4 段全留, 防止 runtime-switch-events.jsonl 引用失效)
[runtime_registry.<old>_backup_<model>]
# 内容不变, 旧 runtime-switch 记录仍能 resolve

# (e) 3 处别名同步更新
[team.residency]
resident_agents = ["manager", "<new>", "Luke_recorder"]  # <old> → <new>

[runtime_guard.manager_policy]
<new> = "pause"  # <old> = "pause" → <new> = "pause"
```

### 3. agent-home 迁移
```bash
cp -a .eduflow-team-state/agent-home/<old>/ .eduflow-team-state/agent-home/<new>/
rm -rf .eduflow-team-state/agent-home/<old>
# 注: cp -a 保留 .claude + .claude.json + identity.md + 所有历史 (记忆完整继承)
```

### 4. kill 旧 pane
```bash
tmux kill-window -t EduFlowTeam:<old>
```

### 5. hire 新 pane
```bash
eduflow hire <new>
# 期望: ✅ hired: <new> (claude-code) → EduFlowTeam:<new>
```

### 6. 验证 (5 项)
```bash
# (a) status 确认 initializing
eduflow status <new>   # → 进行中 | initializing

# (b) tmux pane alive
tmux list-windows -t EduFlowTeam | grep <new>

# (c) toml 解析无错
python3 -c "from eduflow.runtime import config; print(config.agent_config('<new>').get('role','')[:60])"

# (d) 旧段识别为 archived
python3 -c "from eduflow.runtime import config; print(config.agent_config('<old>').get('archived'))"

# (e) 全套 unit tests 绿
python3 tests/run.py
```

### 7. memory 继承确认
- `facts/<old>/*.jsonl` 内容与 `facts/<new>/*.jsonl` 一致 (cp -a 已保证)
- recall / log 数据完整继承
- 旧 agent-home 备份建议留档 7 天 (防止新名有 BUG 时回滚)

### 7.5 (必跑, rename 后强制) — Store 残留清理 checklist

rename 改完 toml + agent-home + pane 后, **必须** 清理 3 处 store 残留, 否则 team 面板会继续显示旧名 live status (T-150 实证 bug):

1. **`status.json`**: 删 `agents.<old>` 段 (`python -c "import json; d=json.load(open(...)); del d['agents']['<old>']; json.dump(d, open(...,'w'))"`)
2. **`facts/<old>/`**: 整个目录 `mv .eduflow-team-state/facts/<old>/ .eduflow-team-state/.archived-YYYY-MM-DD-T<id>/<old>/` (含 memory.jsonl + .memory.lock + recall/log)
3. **`agents/<old>/`**: 整个目录 `mv .eduflow-team-state/agents/<old>/ .eduflow-team-state/.archived-YYYY-MM-DD-T<id>/agents_<old>/` (含 identity.md)

验证:
```bash
eduflow team | grep -i <old>      # 应空 (无 live status 行)
eduflow team | grep -i <new>      # 应显示 <new> 行
ls facts/<old>/ agents/<old>/      # 应 No such file or directory
python -c "import json; json.load(open('.eduflow-team-state/facts/status.json'))"  # 解析 OK
python3 tests/run.py               # 无 regression
```

**红线**: 不删任何旧数据, 全 mv 到 archive 目录。

**真实案例**: T-146 auto_ops → Sophon 后 T-150 清理 store 残留 (3 处 mv 到 `.archived-2026-07-07-T150/`)。漏掉这步会导致 team 面板持续显示 `auto_ops · ✅ 已交付 · 运行态简报: auto_ops 盯盘中` 假状态行 (T-150 修复前实测)。

## 红线 checklist (必走)

- [ ] 旧名 toml 段保留为 archived, **不删** (历史 audit 留档)
- [ ] 旧名 agent-home 目录 cp 后 rm (不直接 rm, 先 cp 兜底)
- [ ] 旧 pane kill 前确认 logs.jsonl 已 sync
- [ ] 新 pane hire 后 verify status
- [ ] `[team.residency] resident_agents` / `[runtime_guard.manager_policy]` / `[runtime_registry.<old>_*]` 三处别名同步更新
- [ ] toml 备份文件保留 (不要删 `.bak`)
- [ ] 跑 tests 全套确认无 regression (通常 +1 个新 test test_commands_task, 因 agent_names() 多一个 entry)
- [ ] manager 同步派 Hermes 改 `wiki/04-团队/<new>.md`
- [ ] **rename 后必跑 store 清理 checklist** (step 7.5: status.json / facts/<old>/ / agents/<old>/) — 不清 team 面板会假显示旧名 live status (T-150 实证 bug)

## 失败回滚

| 失败 | 回滚步骤 |
|------|---------|
| hire 失败 | `cp eduflow.toml.bak-... eduflow.toml` + `mv agent-home/<new>/ agent-home/<old>/` + `tmux respawn-window` |
| tests regression | 先看 toml 段冲突 (旧段没 archived 标注), 再看 agent-home 数据缺失 |
| router 找不到 <new> | 检查 `[team.agents]` 列表 + `[runtime_registry.<new>_*]` 段 |

## 真实案例 (T-146 auto_ops → Sophon, 2026-07-07)

11 步全清单执行 + 182 tests pass + 自动 Sophon pane @2 + auto_ops 段保留为 archived 标识:
- 旧名段改: `[team.agents.auto_ops]` → `[team.agents.Sophon]`
- 旧名段 archived 重建: `archived = "2026-07-07 改名为 Sophon"`
- 新 runtime: `sophon_backup_minimax` (claude-code + minimax M3)
- agent-home: `cp -a agent-home/auto_ops/ agent-home/sophon/; rm -rf agent-home/auto_ops`
- 旧 pane: `tmux kill-window -t EduFlowTeam:auto_ops`
- 新 pane: `eduflow hire Sophon` → ✅ hired: Sophon (claude-code) → EduFlowTeam:Sophon
- 状态: `eduflow status Sophon` → 进行中 | initializing
- 验证: toml 解析 OK + 182 tests pass + agent-home 11 个目录 (auto_ops 不在, sophon 在)

## 关联

- 引用: T-139 (review_course → worker_review 模式) — 但 T-139 **没** 同步更新 cards_v2_schema.py 角色表 (T-144 BUG 根因), 改名时除了 toml/runtime_registry/agent-home/tmux 4 处, **还要** 检查 `src/eduflow/feishu/cards_v2_schema.py:_ROLE_ALLOWED_TYPES` (review_course → worker_review 同款)
- 上游 dispatch 模板: T-128 #5 docs+skills 重叠矩阵 提到 "agent 改名迁移" 是高频 SOP
- 未来触发: Monika → Monica 之类纯名字迁移可完全复用 (无 functional change, 走 7 步流程 + 红线 checklist 即可)
