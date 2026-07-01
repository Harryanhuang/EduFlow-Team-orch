# Phase 0 现状审计 — 群聊外显与温备驻留

> 对应方案: `留学公司知识库/11-Eduflow Team 多智能体项目/2026-07-01 EduFlow 群聊外显与温备驻留方案 v0.1.md`
> 范围: 仅审计现状、列出能力、指出最小改动点;**不修改任何行为**。
> 审计基线: 2026-07-01 仓库状态(`rebuild/minimal` 分支,~8K LOC src+tests)

## 一、关键文件位置

| 用途 | 文件 | 行数级别 |
| --- | --- | --- |
| 发消息 + tmux 注入 + lazy wake 入口 | `src/eduflow/commands/send.py` | 170 |
| 运行时 wake / is_ready / is_rate_limited | `src/eduflow/runtime/wake.py` | 230 |
| 面板创建 / spawn / identity init | `src/eduflow/runtime/lifecycle.py` | 820 |
| 单 agent 入队 / 启 pane | `src/eduflow/commands/hire.py` | 60 |
| 杀 pane(粗暴) | `src/eduflow/commands/fire.py` | 40 |
| 本地事实 / inbox / status / heartbeat / log | `src/eduflow/store/local_facts.py` | 1600 |
| 任务事件 → 群聊 publish 决策 | `src/eduflow/store/task_publish_gate.py` | 575 |
| 任务发布守护循环 | `src/eduflow/commands/task_publish.py` | 80 |
| `eduflow say` 群聊发送 / publish filter | `src/eduflow/commands/say.py` | 405 |
| team 配置 + 运行时注册表 + env_profile | `src/eduflow/runtime/config.py` | 510 |
| `/team` 面板输出 | `src/eduflow/commands/team.py` | 85 |
| 主配置 `eduflow.toml` | `eduflow.toml` | 675 |
| 死 pane 自动 respawn | `src/eduflow/runtime/agent_reaper.py` | 290 |
| 守护进程存活 | `src/eduflow/runtime/watchdog.py` | 360 |

## 二、已有能力盘点

### 2.1 启动 / 唤醒 / 存活

| 能力 | 实现 | 备注 |
| --- | --- | --- |
| `eduflow up` 起 pane + spawn CLI | `lifecycle.provision_pane` 走 5 状态分支:LAZY/READY/READY_NO_INIT/SPAWN_FAILED/CONFIG_ERROR | ✅ 完整 |
| Lazy wake 首次消息触发 spawn | `send.py:146-160` 在 `cfg.lazy and not is_ready` 时调用 `wake_if_dormant` | ✅ 完整 |
| `is_ready` / `is_rate_limited` 探测 | `wake.py:38-50` 通过 capture-pane 找 adapter.ready_markers | ✅ 完整 |
| 死 pane 自动 respawn | `agent_reaper.py:probe` — DEAD pane 走 `tmux.spawn_agent` 复活 | ✅ 完整(但是 spawn,不是 sleep) |
| Runtime 切换 / 容灾链 | `lifecycle.restart_with_runtime` + `config.fallback_runtime` | ✅ 完整(2026-06-30 P0+P1+P2 已上线) |
| 守护进程 respawn / 冷却 | `watchdog.py` 走 `cooldown_secs=600` | ✅ 完整 |

### 2.2 群聊外显

| 能力 | 实现 | 备注 |
| --- | --- | --- |
| `eduflow say <agent> <msg>` 发卡片 | `commands/say.py:main` → `feishu_chat.send_card(simple_card(title, body, color))` | ✅ 完整 |
| 发送方按 agent 着色 | `_AGENT_COLOR_MAP` + `_WORKER_PALETTE` | ✅ 完整(manager 蓝,worker 按名映射) |
| Publish 过滤 | `_publish_allowed()` 查 `[chat.publish.<sender>_to_<receiver>]` + agent `publish_overrides` | ✅ 完整 |
| Worker 允许的"短 ACK"白名单 | `_worker_reason_override()` 列了 50+ 字符串 marker(任务已接单 / 阶段进度 / 暂无新结果 / 巡检正常 等) | ⚠️ **基于字符串 marker,不是结构化卡片** |
| 任务事件 publish 决策 | `task_publish_gate.decide_task_event_publish` 决定 worker_accepted / delivered / worker_started 等是否上群 | ✅ 完整 |
| Dedup 90 秒窗口 | `DedupCache` 90s;P0 anomaly 永不 dedup | ✅ 完整 |
| `CLOSEOUT` / `REVIEW` / `HANDOFF` 结构化卡片类型 | ❌ **不存在** | 现有 worker "已交接" 是自然语言字符串 |
| role → allowed message types 规则 | ❌ **不存在** | worker/manager 都能发任何 marker 字符串 |
| "CLOSEOUT 只能 manager 发" 系统级校验 | ❌ **不存在** | 当前靠 agent identity `notes` prompt 提示 |
| 阶段卡片证据字段强制 | ❌ **不存在** | worker say 不带结构化 evidence 字段 |

### 2.3 任务状态

| 能力 | 实现 | 备注 |
| --- | --- | --- |
| 状态字段 | `待命 / 已接单 / 进行中 / 已交付 / 已读待确认 / 待接单 / 受阻 / 已对账 / 已完成 / 空闲 / 已停止` | ✅ 11 个,字典序中文 |
| 状态投影 | `_project_status_row` 35+ 规则:运行受阻、watchdog 恢复、worker visibility、stale 等 | ✅ 完整 |
| Heartbeat | `touch_heartbeat` / `get_heartbeat` / `all_heartbeats` | ✅ 完整 |
| Inbox 显式 ACK | `record_message_ack(kind, ...)` — accepted_task / started_task / completed / reconciled | ✅ 完整 |
| 显式 ACK 同步到 status | `_sync_explicit_ack_visibility` | ✅ 完整 |
| `温备` 状态字面量 | ❌ **不存在** | 当前只有 `待命`(等价"lazy 但还没接单")和 `已停止`(被 fire) |
| Residency 字段 | ❌ **不存在** | status.json 当前只有 `agent / status / task / blocker / updated_at` |

### 2.4 配置

| 能力 | 实现 | 备注 |
| --- | --- | --- |
| `eduflow.toml` 团队配置 | `[team]`, `[team.agents.<name>]`, `[runtime_registry]`, `[env_profiles]`, `[chat.publish]` | ✅ 完整 |
| 单 agent 字段 | `cli/model/runtime/role/specialty/tone/notes/card_color/lazy/publish_overrides/category` | ✅ 完整 |
| `[team.residency]` | ❌ **不存在** | 没有 residency/mode/idle_timeout 等配置 |
| `[team.agents.<name>.residency]` | ❌ **不存在** | 没有 per-agent residency override |

### 2.5 自动调度

| 能力 | 实现 | 备注 |
| --- | --- | --- |
| `eduflow task-publish` 守护循环 | `commands/task_publish.py` 默认 15s 一轮 | ✅ 完整 |
| `eduflow auto-ops` / watchdog 周期检查 | `watchdog.py:_guard_agent_runtimes` 走 fallback chain | ✅ 完整 |
| 调用 `sleep_if_idle(agent)` 回收 warm agent CLI | ❌ **不存在** | watchdog 只管 daemon,不管 pane 内的 CLI |
| HANDOFF / CLOSEOUT 后登记 sleep candidate | ❌ **不存在** | task_publish 不触发 pane sleep |

## 三、明确"自动回温备"缺失的证据

方案 Phase 0 要求 "明确写出当前缺少'自动回温备'的证据"。逐项核对:

1. **没有 `sleep_if_idle(agent)` 实现**: `grep -rEn "sleep_if_idle|graceful.*exit|exit_cli" src/` 无任何匹配。
2. **没有 idle / handoff_buffer 超时字段**: 配置层无 residency block;store 层无 per-agent `last_active_at` / `handoff_at`。
3. **没有"自动回温备"的触发器**: 
   - `watchdog.py` 走 `cooldown_secs=600` 是 daemon 维度,非 agent pane 维度。
   - `agent_reaper.py:probe` 探测 DEAD pane 时调用 `tmux.spawn_agent` **起一个 CLI**(`lifecycle.provision_pane`),而不是退出 CLI。
   - `task_publish.py` 默认每 15s 调一次 `task_cmd publish-run --to <target>`,不涉及 pane 资源。
4. **`fire.py` 是粗暴 kill**:`tmux.send_keys C-c` + `tmux.kill_window`。`fire` 整窗杀掉,不是 graceful sleep。Phase 3 需要的"保 pane、退 CLI"在 `fire` 上没有等价物。
5. **状态字段无 `温备`**: `_IDLE_STATUSES = {"待命", "空闲", "ready", "idle"}` 缺 `温备`;`_WEAK_STATUS_TASKS` 也不含。
6. **resident 配置缺位**:`[team.residency]` / `[team.agents.<name>.residency]` 在 toml 中无 schema 入口。

结论: v1 落地"idle → warm"必须新增 `runtime/residency.py` 模块 + 配置块 + 触发器,**没有现成代码可复用**。

## 四、最小改动点

按"v1 不破坏 lazy wake、不新增依赖"原则,Phase 2-3 的最小改动点:

### 4.1 新增模块(~350 LOC,分散 ≤ 200 LOC/文件)

| 文件 | 作用 | 估计 LOC |
| --- | --- | --- |
| `src/eduflow/runtime/residency.py` | `ResidencyPolicy` dataclass / `load_residency_policy(agent)` / `is_idle(agent)` / `sleep_if_idle(agent)` / `wake(agent)` | 180 |
| `src/eduflow/store/agent_residency.py` | 持久化 per-agent `mode / last_sleep_at / last_wake_at / last_active_at` 到 `agent_residency.json` | 60 |
| `src/eduflow/feishu/cards_v2.py` | `CardType` 枚举 / `build_card(type, fields)` / `validate_card(card, sender)` | 130 |

### 4.2 现有文件扩展(最小侵入,符合 CLAUDE.md "Match the canonical command" 原则)

| 文件 | 改动 | 估计 LOC |
| --- | --- | --- |
| `runtime/config.py` | 增加 `load_residency_default()` / `load_agent_residency_override(agent)` 读 `[team.residency]` / `[team.agents.<name>.residency]` | +40 |
| `store/local_facts.py` | `upsert_status` 增加 `residency` 字段(默认不破坏);`_project_status_row` 增加 residency 投影;`温备` 加入 `_IDLE_STATUSES`;新增 `touch_residency_event(agent, event)` 写 last_active_at / last_sleep_at / last_wake_at | +60 |
| `commands/team.py` | `_emit_text` / `_emit_json` 加 residency 列(`常驻 / 温备 / 唤醒中 / 进行中`) | +30 |
| `commands/say.py` | 接受 `--card <type>` 路由到 `cards_v2.build_card` + `validate_card`;无 `--card` 时回退 simple_card 保持向后兼容 | +50 |
| `commands/send.py` | `cfg.lazy` 之外增加 `residency_policy.mode == "warm" and is_warm_status` 时也走 `wake_if_dormant` | +20 |
| `commands/task_publish.py` 或 `commands/auto_ops_loop`(若不存在则新建 ~50 LOC)| 周期调 `runtime.residency.sweep_idle_agents()`,把 idle warm agent 走 `sleep_if_idle` | +30 |
| `commands/watchdog.py` | 周期调 `runtime.residency.sweep_idle_agents()`(备选触发点,与 task_publish 二选一) | +20 |
| `commands/down.py` 或 `commands/team.py` | 提供 `eduflow team/wake <agent>` 手动预热命令 | +20 |
| `eduflow.toml` | 在 `[team]` 旁增加 `[team.residency]` 块,把 manager/auto_ops/Luke_recorder 标 `resident`,worker_* 标 `warm`,worker_syllabus 用 300s 自定义 idle_timeout | +30 |

### 4.3 测试 + 场景(CLAUDE.md 强约束)

| 文件 | 用途 | 估计 LOC |
| --- | --- | --- |
| `tests/unit/test_residency.py` | 覆盖 `ResidencyPolicy` / `is_idle` / `sleep_if_idle` / `wake` 的纯函数 + 注入式副作用 | 200 |
| `tests/unit/test_cards_v2.py` | 覆盖 `validate_card`(CLOSEOUT 只能 manager,worker 不发正式成功,evidence 字段) | 150 |
| `tests/scenarios/2026-07-01-residency-and-card-protocol.md` | operator 端到端回归剧本:起 team → 派单 → sleep → 唤醒 → card 渲染 | 80 |
| `tests/scenarios/2026-07-01-main-group-card-matrix.md` | 9 种 card 类型 × 多角色组合的群聊外显矩阵 | 60 |

## 五、与方案 v0.1 设计点的对应检查

| 方案点 | 当前是否支持 | 落地方式 |
| --- | --- | --- |
| `resident` 始终在线 | 部分:`cfg.lazy=false` 决定 spawn,但 spawn 后一直占 CLI 不退 | Phase 2 加 residency config + 禁止 resident auto-sleep |
| `warm` 退 CLI 保 pane | ❌ 缺 | Phase 3 新增 `sleep_if_dormant_for_warm(agent)` |
| `cold` 不在场 | ❌ 缺 | **v1 不实现**,按方案非目标保留 |
| 卡片类型协议(9 种) | ❌ 缺 | Phase 1 `feishu/cards_v2.py` |
| `CLOSEOUT` 只能 manager | ❌ 缺 | Phase 1 `validate_card` 强制 |
| Worker 不发正式成功 | ❌ 缺 | Phase 1 `validate_card` 强制 + Phase 5 把 worker `notes` 里的"已交付"语义改成"已交接,等待 manager 收口" |
| `/team` 显示 4 态 | 部分:只看 status | Phase 2 `team.py` 加 residency 列 |
| 长任务 `HANDOFF` 带 `运行状态变化: active -> warm` | ❌ 缺 | Phase 1 卡片字段 + Phase 3 sleep 触发时把状态变化写进 HANDOFF 卡的 `运行状态变化` 字段 |
| Wake 失败 `ALERT` | ❌ 缺 | Phase 4 在 `wake_if_dormant` 失败路径发 `ALERT` 卡片(走 `say` 通道) |
| 阶段驱动陪跑(无定时刷存在感) | 部分:目前 auto_ops 30 分钟必说一次 | Phase 5 把 `auto_ops notes` 里的"约每 30 分钟在主群说一次"降级为:有阶段变化才说,无变化进入 `/team` 面板 |

## 六、未覆盖风险

1. **跨 session 状态**:多 session 部署时 `local_facts` 是 state-dir 维度的,residency 持久化必须按 `$EDUFLOW_STATE_DIR` 重读(参考 `runtime/paths.state_dir()` 已有的 no-cache 约定)。
2. **预热时机**:Phase 4 的"manager 预热高频 worker"在 `commands/say.py` 收 card 决策时如何抢先 wake?需要新增 `runtime/residency.preheat(agent)` 接口。
3. **Runtime 切换期间的 sleep**: 当 agent 正在 `restart_with_runtime` 走 fallback chain 时,`is_idle` 必须为 False,否则会把正在重启的 agent 误 sleep。需要在 `cooldown` / `fallback` flag 期间拒绝 sleep。
4. **`/team` 输出脚本兼容性**: 如果有外部 CI 解析 `eduflow team --json`,新增 residency 字段必须向后兼容(用 default value 兼容老 schema)。`team.py:_emit_json` 需要在每条记录加 `"residency": "常驻|温备|唤醒中|进行中|..."`。
5. **dedup cache 与 card 协议**: `task_publish_gate.DedupCache` 是基于 `(task_id, stage, content_hash)`,跟 card type 协议是平行的两套。Phase 1 不动 dedup,Phase 5 再考虑是否让 `CardType` 进入 dedup key。
6. **CLAUDE.md 强约束**: 新模块必须自带 unit test + scenario(在同 commit);单文件 ≤ 300 LOC;无兼容性 shim;two-use rule。这要求 `runtime/residency.py` 的 dataclass / 函数按需拆分,不能一锅端。
7. **Flow Memory 依赖**: 当前测试基线缺 `flow_memory` 模块(`ModuleNotFoundError`),不在本次审计修复范围,但 Phase 1 起的 unit test 编写必须用 `tests/helpers.py:isolated_env()` 隔离,避开 `eduflow.memory.*` 的 import 链。

## 七、Phase 0 验收(自检)

- [x] 列出 8 个核心模块的现状与能力。
- [x] 明确写出"自动回温备"在源码中无任何实现(grep 0 命中)。
- [x] 明确指出最小改动点(3 个新模块 + 7 处扩展 + 4 份测试/场景)。
- [x] 与方案 v0.1 设计点逐项对应,标出"✅ / 部分 / ❌"。
- [x] 未覆盖风险列出 6 项。
- [x] **未修改任何源代码 / 配置文件 / 文档正文**。

---

Phase 0 结论:**方案 v0.1 可执行,所有需要落地的点都有明确的最小改动面**。建议老板在 Phase 1 进入实现前先看本审计,确认改动面与方案假设一致。

进入 Phase 1 的前置条件:
1. 老板确认 4.1 三个新模块的文件位置(本审计建议 `runtime/residency.py`、`store/agent_residency.py`、`feishu/cards_v2.py`,与现有命名规范一致)。
2. 老板确认 4.2 各处扩展的边界(尤其 `say.py` 的 `--card` 路由和 `local_facts.upsert_status` 的 `residency` 字段是否可写)。
3. 老板确认 Phase 1 之后是否同步 `agents/<name>/identity.md` 的 `notes` 字段(把"已交付"改成"已交接,等待 manager 收口")。

任何一条不确认,都应先回到方案 v0.1 讨论,而不是直接进 Phase 1。
