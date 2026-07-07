---
name: agent-hiring-checklist
description: Complete checklist for hiring a new agent in the EduFlow team. Covers hire-vs-start decision, team config, runtime_registry backfill, identity auto-render, tmux provisioning, skill installation, and live-smoke verification.
metadata:
  type: reference
  owner: worker_builder
  version: "2.0"
  changelog: "v2 (2026-07-06, T-100): +hire-vs-start decision matrix, corrected identity auto-render path (was misleading operators to hand-write agent-home), +runtime_pool KeyError backfill flow. Derived from the T-99 worker_teacher re-hire run."
---

# Agent Hiring Checklist (v2)

新 agent 雇佣完整流程检查清单。用于 worker_builder 或 manager 雇佣新 agent 时逐项确认。

> **v2 升级依据（T-99 worker_teacher 实跑暴露的 3 处短板）**
> 1. `hire` 与 `start` 未区分 → 派单误用 `start`，实际须 `hire`。见 §0。
> 2. identity.md 被误导为手写到 `agent-home/`，实际由 lifecycle 从 config 渲染到 `agents/<name>/`。见 §阶段二。
> 3. 关联 runtime_pool 缺 `[runtime_registry]` 条目 → `hire` KeyError 中止，旧 skill 未教补建。见 §阶段一·补。

---

## §0 决策矩阵：hire vs start vs up/down（**先读这张表**）

| 命令 | 作用 | 前置条件 | 何时用 |
|------|------|----------|--------|
| `eduflow hire <name>` | 往**运行中**的 session 注册并拉起**单个** agent 的 pane | `[team.agents.<name>]` 已在 toml 配好；session 正在跑（`tmux has-session`） | **完全新增** agent（toml 之前没有它）后，把它加进已在运行的团队 |
| `eduflow start` | 拉起**整个 team**：建 session + 每个已注册 agent 一个 pane | session **尚未**运行（已在跑则拒绝：`⚠️ session already running; refusing to start over`） | 冷启动整支团队；**不是**给运行中团队加人 |
| `eduflow up` / `down` | 整 team 生命周期（含 router / watchdog 等 daemon） | — | 整体起停团队运行体系 |

> **注意**：`eduflow start` 无 `<name>` 语义 —— 它忽略 agent 参数、拉起整队，且 session 已在跑会直接拒绝。
> 想给**运行中**的团队加一个新 agent，唯一正路是 `eduflow hire <name>`。

### 决策流

```
要上线一个 agent？
├── 它是全新 agent（toml 里没有 [team.agents.<name>]）？
│     → 先 §阶段一 配 toml + §阶段一·补 确保 runtime_pool 存在
│     → session 在跑：eduflow hire <name>
│     → session 没跑：eduflow start（会把它和全队一起拉起）
│
└── 它是既有 agent，只是 pane 挂了要重启？
      → session 在跑：kill 旧 window → eduflow hire <name>（见 §阶段三 的 rehire 教训）
      → 整队都没跑：eduflow start
```

---

## 阶段一：基础配置

- [ ] 确定 agent 名称（按团队命名规范：`worker_<domain>` / `review_<domain>`）
- [ ] 确定 runtime 配置（复用或**补建** `runtime_registry` 条目 —— 见 §阶段一·补）
- [ ] 在 `eduflow.toml` 写 `[team.agents.<name>]` 段
  - [ ] `runtime` 字段（必填，指向一个存在于 `[runtime_registry]` 的池名）
  - [ ] `role` 字段（必填，一句话角色描述 —— 会成为 identity.md 首行）
  - [ ] `specialty` 字段（推荐，技能标签列表 —— 会渲染进 identity + manager 派工视图）
  - [ ] `tone` 字段（推荐，LLM 输出风格）
  - [ ] `notes` 字段（推荐，外显规则 + v2 协议 + 红线 —— 会渲染进 identity 的「备注」章节）
  - [ ] `card_color` 字段（推荐，飞书卡片颜色，避免与既有 agent 撞色）
  - [ ] `lazy` 字段（可选，默认 false）
- [ ] 配完立刻验证 config 能解析（不要等到 hire 才炸）：

```bash
python3 - <<'PY'
import sys; sys.path.insert(0,"src")
from eduflow.runtime import config
config.agent_config("<name>")            # KeyError ⇒ toml 段没写对
config.resolve_runtime_chain("<name>")   # KeyError: runtime <x> not in runtime_registry ⇒ 去 §阶段一·补
print(config.resolved_agent_config("<name>"))  # 看 cli/selected_runtime/model/env_profile 是否符合预期
PY
```

---

## 阶段一·补：runtime_pool 缺条目 → `hire` KeyError 补建流程（**T-99 新增**）

`hire` / `start` 解析 runtime 时走 `config.resolve_runtime_chain()`，它对 `[team.agents.<name>].runtime` 指向的池名调用 `runtime_config(name)`；**池名不在 `[runtime_registry]` 会 `raise KeyError(f"runtime {name!r} not in runtime_registry")`**，进而 `provision_pane` 返回 `CONFIG_ERROR`，`hire` 中止。

历史坑：`facts/runtime-status.json` 里可能**记着**某 agent 的 runtime（如 `teacher_backup_mimo`），但 `[runtime_registry]` 里那个块**早被删/从未建** —— skill 若不教补建，operator 会摸黑。

### 补建步骤

1. **hire 前先查池子是否存在**：

```bash
# (a) 看该 agent 历史关联的 runtime 池 + 应有的 cli/model/env_profile
python3 -c "import json;d=json.load(open('.eduflow-team-state/facts/runtime-status.json'))['agents'];import sys;print(d.get('<name>','<none>'))"
# (b) 看这个池名在不在 registry
grep -n "runtime_registry.<pool>" eduflow.toml || echo "MISSING → 需要补建"
```

2. **补建 `[runtime_registry.<pool>]`**，四字段必须齐全，且 **`env_profile` 从现有池复用（严禁新建 provider 凭据）**：

```toml
[runtime_registry.<pool>]           # 名字 = runtime-status.json 里记的池名
cli = "claude-code"                 # 从 runtime-status.json 抄
model = "sonnet"                    # 抄；实际模型由 env_profile 的 ANTHROPIC_DEFAULT_*_MODEL 映射
provider = "anthropic-proxy"        # 抄
env_profile = "claude_proxy_mimo_backup"   # ← 必须复用已存在的 env_profile（grep 确认它已在 [env_profiles]）
fallback_to = ""                    # 无同族备份池就留空
switch_on = ["spawn_failed", "ready_timeout", "rate_limit", "auth_failure", "provider_unavailable", "conversation_history_corrupt"]
```

> 复用 `env_profile` 的意义：token/base_url 全在 env_profile 里，复用现有池 = 不碰凭据、不新增泄露面。
> 例：`claude_proxy_mimo_backup` 的 `ANTHROPIC_DEFAULT_SONNET_MODEL = "mimo-v2.5-pro"`，所以 `model="sonnet"` 实跑即 mimo-v2.5-pro。

3. **补建后立刻验证解析**（`resolve_runtime_chain` 不再 KeyError）：

```bash
python3 -c "import sys;sys.path.insert(0,'src');from eduflow.runtime import config;print(config.resolve_runtime_chain('<name>'))"
```

4. **hire 后跑 live-smoke 验证真的能起**：

```bash
eduflow runtime verify <name> --live-smoke     # 期望 proved_ready
```

> **红线**：补建只加**该 agent 自己的** runtime 池，复用既有 env_profile；**不改其他 agent 的 runtime 配置**，不新建 provider 凭据。

---

## 阶段二：身份文件 identity.md（**自动渲染，勿手写 —— T-99 修正**）

**identity.md 由系统从 config 自动渲染，operator 不手写。**

- 路径：`.eduflow-team-state/agents/<name>/identity.md`（**注意是 `agents/`，不是 `agent-home/`**）
- 渲染来源：`[team.agents.<name>]` 的 `role` / `specialty` / `tone` / `notes` 四个字段
- 渲染入口：`lifecycle.provision_pane()` → `agents/identity.py::render()`（manager 视角还有 `render_for_prompt`），在 hire/start 时自动调用并写盘

### ❌ 常见错误 vs ✅ 正确做法

| ❌ 错误 | ✅ 正确 |
|--------|--------|
| 手写 identity 到 `agent-home/<name>/identity.md` | 内容写进 `[team.agents.<name>]` config 字段 |
| 手改 `agents/<name>/identity.md` 正文 | 改 toml 的 role/specialty/notes → `eduflow reidentify <name>` 重渲染 |
| 以为改了文件就生效 | provision/reidentify 会**覆盖**手改；toml 才是唯一真源 |

> 手写到 `agent-home/` 不会被 CLI 读作身份，且下次 provision 无效；手改 `agents/<name>/identity.md` 会在 reidentify 时被 config 渲染结果覆盖。

### lifecycle.provision_pane 流程顺序（记住这条链）

```
validate config (agent 在 team.json?)
  → resolve runtime chain（若 runtime_pool 缺 → CONFIG_ERROR，回 §阶段一·补）
  → render + persist identity.md  (agents/<name>/identity.md)
  → lazy? 是则设 待命 返回 LAZY
  → spawn CLI in pane（带 env_profile 前缀）
  → wait ready marker（≤20s）
  → inject identity init prompt（让 agent 读 identity.md 并报到）
  → set status 进行中
```

- [ ] 改动 role/specialty/notes 后用 `eduflow reidentify <name>` 而非手改文件
- [ ] hire 后确认 `agents/<name>/identity.md` 已生成且首行角色正确

---

## 阶段三：Tmux 与启动

- [ ] `eduflow hire <name>` 创建 tmux window + 渲染 identity + spawn CLI + 注入 init（session 须在跑）
- [ ] `eduflow peek <name>` 确认 CLI 已醒（prompt `❯` 出现、非持续 "initializing"）
- [ ] `eduflow team` 确认 heartbeat 在最近 1 分钟内

> **⚠️ 关键教训（2026-06-28）**：如果中途修改了 runtime 配置（如从错误 runtime 改为正确的），
> **必须 kill 旧 pane + rehire** 才能生效。`reidentify` 只注入文本，不重启 tmux pane，
> 旧 env_vars（含 API token）会持久化在 pane 中，导致 401 认证失败。
> 正确流程：`tmux kill-window -t <session>:<agent>` → `eduflow hire <agent>`。

---

## 阶段四：Skill 安装

- [ ] 扫描与 agent 核心职责相关的 skill
- [ ] 从 codex 目录（`/Volumes/Halobster/Codex相关/skills/`）复制到项目 `.claude/skills/`
- [ ] `eduflow reidentify <name>` 确保 agent 识别到新 skill
- [ ] 更新 `.claude/skills/skill-registry.md`（**只加你这个 agent 的条目，不动别人的编号/owner**）

---

## 阶段五：验证与验收

- [ ] `eduflow runtime verify <name> --live-smoke` → 期望 `proved_ready`
- [ ] `eduflow health` → 该 agent 显示 `proved_ready (runtime=<pool>, pool=<...>)`
- [ ] 发一条测试任务：`eduflow send <name> worker_builder "测试任务：回复收到"`
- [ ] 确认 agent ACK（`eduflow read <local_id>` 查 ACK 状态）
- [ ] 确认 agent 用 `say`/`send` 回复（视 chat.publish 配置）
- [ ] 确认 `eduflow peek <name>` 显示已处理

---

## 阶段六：Onboarding 指引

- [ ] 确认新 agent 能访问 `new-agent-onboarding.md`（面向**新 agent 自身**的六大系统对接指南）
- [ ] agent 首次启动后应自动走 onboarding 流程并向 manager 报到

> **交叉引用**：本 skill 是**operator（worker_builder/manager）的雇佣 runbook**；
> `new-agent-onboarding.md` 是**新 agent 自己**读的系统对接指南（记忆/派工/通讯/身份文件等）。
> 两者受众不同、互补不冲突：identity.md 的路径与自动渲染，两边保持一致（`agents/<name>/identity.md`）。
> 若未来两文件出现矛盾，以本 skill 的 §阶段二 + §阶段一·补（贴近 lifecycle 实现）为准。

---

## 验收完成

全部勾选后，向 manager 发送雇佣完成报告：

```bash
eduflow send manager worker_builder "T-<id> 完工：新 agent <name> 已雇佣。
配置 ✅ | runtime_pool ✅ | identity 渲染 ✅ | hire ✅ | live-smoke proved_ready ✅ | 验证 ✅
Agent: <name> | Runtime: <pool> | CLI: <cli> + <实际模型>
已装 Skill: <列表>
验证: runtime verify --live-smoke = proved_ready；测试任务已 ACK" 高
```
