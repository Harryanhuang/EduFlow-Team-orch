# T-142 router 掉件诊断报告

**worker_builder → manager** ｜ 2026-07-11 02:56 (UTC+8)
**触发**：manager msg_1783709562367_c3d97d333f + 追加 msg_1783709769376_86d7c071dd
**边界遵守**：全程只读（ps / stat / grep / curl / lark-cli 只读）；未改 inbox.json / router.cursor / .pid / tmux pane

---

## 结论（TL;DR）

**症状比提示更深一层**：整个 daemon stack（**router + watchdog + task-publish**）从 ~07-10 19:39 起**全部死亡**，不是单纯的 router respawn loop。
Router.log 里看到的 7 次 respawn 是当天早些时候的真实活动；19:39 后 router.log / watchdog.log / task-publish.log 三者 mtime 全部冻死，距今 **~7 小时无活动**。
Watchdog 自己也死了，所以连"自动 respawn"这条路都断了。
因此 boss 18:28 之后发到群里的所有消息都在飞书服务器上躺着，本地无人 ingest。

**好消息**：tmux 内所有 agent pane 仍然活着（manager / worker_* 心跳 1-9h 内），团队没受影响，只是 inbound 管道断了；router 一旦重启会自动 catchup 18:28 之后未处理事件（CLAUDE.md R7），boss 不一定需要重发。

---

## 证据

### 1. 进程层（核心证据）

```
$ ps -ef | grep -E "eduflow|lark"  (排除 grep 自身)
→ 无任何 eduflow python 进程在运行

router.pid    = 64806  (mtime 07-10 19:39:23, 进程不存在)
watchdog.pid  = 37046  (mtime 07-10 17:23:37, 进程不存在)
task-publish.pid = 37045 (mtime 07-10 17:23:37, 进程不存在)
```

`eduflow health` 自检也明说：

```
daemons:
  ⚠️ router:       pid file present but process dead (watchdog will respawn)
  ⚠️ task-publish: pid file present but process dead (watchdog will respawn)
  ⚠️ watchdog:     pid file present but process dead (watchdog will respawn)
                   ↑ 这条自相矛盾：watchdog 死了没人来 respawn 任何东西
```

### 2. 文件 mtime（侧面确认）

| 文件 | 最后 mtime | 距今 |
|---|---|---|
| router.log | 07-10 19:39:28 | ~7h 冻死 |
| router.seen | 07-10 18:37:23 | ~8h 冻死 |
| watchdog.log | 07-10 19:39:53 | ~7h 冻死 |
| task-publish.log | 07-10 19:47:01 | ~7h 冻死 |

### 3. Router cursor（关键证据）

```
router.cursor = {
  "message_id": "om_x100b6a38dd9dd884b3740313622558f",
  "create_time": "2026-07-10 18:28"
}
```

最后成功 ingest 的飞书 message_id 是 07-10 18:28 那条。

### 4. Manager inbox 反向印证

**07-10 18:00 之后 0 条 user→manager 消息入库**（已 grep facts/inbox.json 全部 5693 条消息验证）：

- 18:37 Sophon "manager 接单" → 入库 ✓
- 19:49 worker_course "幻影 batch2" → 入库 ✓
- 但这两条都是**内部** `eduflow send` 写入，**不走 router**；它们的出现反而**反向证明** router 已死——如果 router 活着，这段窗口的 boss 消息也该入库

manager inbox 最后一条 user→manager 是 **07-10 14:42**（msg_1783665762819_e312baadc1 — 200G 对象存储费用问询）。该消息 14:42 → 14:42+ 已正常 ACK，时间远早于 router 死亡。

04:00 追加症状里 boss 提到的 `msg_1783709727823_51b03cc24b` 同样 0 入库，与 router 死亡窗口完全吻合。

### 5. 上游/网络层（排除外部因素）

```
$ curl -sv --max-time 10 https://open.feishu.cn/open-apis/im/v1/messages
→ TLS 握手正常，HTTP 200，返回 99991661 access-token 缺失（未鉴权正常响应）

$ lark-cli im +chat-list
→ ok: true, 返回 1 个群 (chat_id=oc_31f0f00378bea36dd5e8f69256cc7a5e，与 router 一致)
```

watchdog 之前报的"lark-cli TLS handshake timeout"是偶发瞬态，并非持续性网络故障。

### 6. tmux panes（团队层面）

`eduflow health` tmux section 全部 ✅，manager/worker_builder 等 12 个 pane 都在线，心跳 1-9h 不等。**团队 agent 没事，只是 inbound 断了。**

---

## 建议（按优先级）

### A. 先轻量重启 daemon stack（推荐先做，5 分钟内可恢复）

1. **手动 `eduflow up`**（watchdog 死了，所以自动 sup 路径不一定生效；建议直接 shell 跑）
2. **router 启动会自动 catchup** 18:28 之后所有未处理事件（CLAUDE.md R7 路由层 catchup-on-restart 已实现）
3. **60s 后跑 `eduflow health`** 验证 daemons 转绿 + `router.log` 开始写新行 + manager inbox 收到 catchup 来的 boss 消息
4. **不需要让老板重发**，除非 catchup 后某些消息仍未到

### B. 如果重启后又硬死，根因排查

router 当天有 7 次 respawn/failure（"no events for 1200s; subscribe likely silently stalled"），最终 19:39 那次是硬死（不是软退出）。可能诱因：

- **laptop sleep/wake**：07-10 18:28 之后到 19:39 区间，boss 有段时间没说话 + 可能合盖睡眠 → macOS 可能 SIGKILL 了 ws 长连接和 watchdog；router 软检测（1200s no-events）只退出一次，重启后又被 sleep 杀掉
- **OOM 或 watchodg 在重启 router 时 race**：router 在 catchup 阶段可能短时内存尖峰，被 watchdog 误杀
- **task-publish 与 router 共享资源**：task-publish log 持续 "📭 no publishable task events" — 看起来是空转，但可能某种 IPC/lock 资源泄漏拖垮 router

### C. 飞书事件缓冲窗口

飞书事件默认 7 天缓冲，07-10 18:28 → 现在 07-11 02:56 约 8 小时，**理论上 catchup 仍可拉到**。如果超过 7 天 boss 消息丢失，则需要走 `lark-cli im +messages-search --as user`（user-only 鉴权；目前 bot identity 不支持）手动拉取。

### D. 短期缓解（不等授权即可做）

- 把 `feishu/subscribe.py` 的 silent-stall 检测从 1200s 降到 600s（提早主动退出-重启循环，比硬死概率低）
- 让 watchdog 与 router 的 supervise 关系加一层 "watchdog 也被 watchdogd 守护"（macOS launchd 写一个 plist）

但 D 涉及代码改动，需要授权+回归测试。

---

## 需授权项

| 操作 | 风险 | 当前状态 | 建议 |
|---|---|---|---|
| 我跑 `eduflow up` 重启 daemon | 低（不删 inbox/cursor） | **未执行** | 建议 manager 批准后我执行，60s 内回报 health |
| 改 `feishu/subscribe.py` stall 阈值 | 中（代码改动） | **未执行** | 需 manager/老板批准；先看重启是否复发再决定 |
| 改 macOS launchd watchdog 配置 | 中 | **未执行** | 同上 |
| 让老板重发 18:28 后的消息 | 无（仅沟通） | — | **不需要**；catchup 大概率自动补；若 5min 后 manager inbox 仍缺再补 |

---

## 我已做的 vs 未做的

**已做（全部只读）**：
- `eduflow inbox` / `eduflow read`（manager 派单）
- `ps -ef` / `stat -f %Sm` / `tail -n` / `grep -c`
- `curl https://open.feishu.cn/...`（未鉴权探测）
- `lark-cli im +chat-list`（只读）
- python 脚本 grep `facts/inbox.json` 5693 条消息统计
- 写本报告 markdown（仅本机路径，未提交）

**未做（按边界要求）**：
- 没 `eduflow up` / 没改 router / 没改 watchdog / 没 kill 任何进程
- 没动 `inbox.json` / `router.cursor` / `router.pid` / `watchdog.pid`
- 没动任何 tmux pane / agent 状态
- 没改任何 eduflow 源码 / 配置