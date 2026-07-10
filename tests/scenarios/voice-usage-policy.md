# Voice / TTS 使用方案 v1（manager-only 范围，T-140）

> 配套方案：eduflow.tts.say (T-158 / 2026-07-09 落地) + `eduflow.toml [tts.voice]` 12-agent 映射
> 实现：`src/eduflow/commands/tts.py`（MiniMax t2a_v2 HTTP）+ `lark-cli im +messages-send --msg-type file`（opus 上传）
> 任务：T-159 → T-140 范围调整（老板 msg_1783593289429_72b74cb8e6：目前只要 manager 用语音汇报）

## 目的

约束 manager 单独使用 `/voice` / `eduflow tts say`：
- 避免群刷屏（Opus 比文字吃注意力 ≈5x）
- 限定真正"语音比文字强"的场景
- 失败可观察、可回退、不影响主流程
- **其他 11 agent voice 用法冻结**（pending 老板后续 enable）— 见 §E 扩展 checklist

## 适用范围

- 类型：host-live（飞书群 + tmux + MiniMax API + lark-cli 真链路）
- 当前仅 manager 有 voice 权限；其他 agent 走 frozen 通道
- 凭证：`MINIMAX_AUTH_TOKEN` 在 agent-home env 文件已配
- 不在范围：voice clone（老板说之后再做）/ voice 映射修改（已 freeze 2026-07-09）

## 前置条件

- `eduflow up` 已起，12 agent pane 全绿（`eduflow health` 12 heartbeat ok）
- `eduflow.toml [tts.voice]` 12-agent 映射已 freeze
- `MINIMAX_AUTH_TOKEN` export
- `lark-cli im +messages-send --msg-type file` 在部署机已验证可用

## 3 条硬边界（manager 适用）

| 边界 | 规则 | 备注 |
|---|---|---|
| **频率** | ≤5 次 / manager / 24h | 超过会触发聊天气泡 + token 预算告警；超出需 manager 自检 |
| **场景** | 仅以下 5-7 类（见 §A.2） | 其他场景应回到 `eduflow say` 文字 |
| **单条时长** | ≤15s（≈75 字） | 长内容拆多段（每段独立 TTS call），或彻底改用文字 |
| **失败必报** | 任何 TTS/上传失败 → 自动回退文字 say + DM manager | TTS 503 / ffmpeg 缺失 / token 过期 / lark-cli 报错 |

---

## A. Manager Given/When/Then 8-12 Case（operator playbook）

> 每一条对应一条 operator 可手动跑、跑完可断言 pass/fail 的剧本。

### A.1 通用前置（所有 case 共享）

**Given** manager pane alive，`eduflow health manager` ok，[tts.voice.manager] 映射已生效（male-qn-daxuesheng / pitch 3 / speed 1.25 = "海绵宝宝·大学生调高音"）
**And** `MINIMAX_AUTH_TOKEN` 在 manager agent-home env 已 export

### A.2 5-7 类 Manager 适用场景（正文 Given/When/Then 覆盖以下）

1. **派工指令**（manager 向 worker 派单）
2. **巡视汇报**（manager 5min cadence 巡检总结）
3. **收口 ack**（manager 收到 worker 完工后发 "任务已闭环" 类回复）
4. **告警升压**（router 失联 / 全员温备 / runtime 异常）
5. **老板点名**（老板在群里 `@manager 用语音回我`）
6. **阶段里程碑**（Sprint 完工 / OKR 阶段达成）
7. **追责定性**（critical bug 责任判定）

### A.3 Case 列表

#### Case 1 — Happy path 派工指令

**Given** 老板刚发 `worker_qbank 接 T-103 cross-system contamination`
**When** manager 执行 `eduflow tts say "worker_qbank 接 T-103 cross-system contamination" --agent manager --to <main_chat_id>`
**Then** 主群收到 1 条 opus 文件消息（≈6s，海绵宝宝·大学生调高音）；worker_qbank inbox 收到对应 send（route 走 task 分配）；`tts/last.mp3` 落盘可重听

#### Case 2 — Happy path 巡视汇报（5min cadence）

**Given** manager 刚跑完 `eduflow peek worker_course worker_qbank ...` 巡视
**When** manager `eduflow tts say "巡视发现 worker_qbank 卡 T-103，worker_course 正常推进" --agent manager --to <main_chat_id>`
**Then** 主群收到 1 条 opus，时长 ≤10s；老板能 5s 内听懂关键点

#### Case 3 — Happy path 收口 ack

**Given** worker_qbank send manager "T-103 完工"
**When** manager `eduflow tts say "T-103 已闭环 ✅" --agent manager --to <main_chat_id>`
**Then** 主群收到 1 条 opus，时长 ≤3s；满足"对话收尾"语义

#### Case 4 — Happy path 告警升压

**Given** router 失联 5min，watchdog 已 cooldown 1 个 worker
**When** manager `eduflow tts say "⚠️ router 失联，全员温备，已告警老板" --agent manager --to <main_chat_id>`
**Then** 主群收到 1 条 opus，语气重（速度 1.25 + 升调 → 紧迫感）；老板立即 follow-up

#### Case 5 — Happy path 老板点名

**Given** 老板在群里 `@manager 用语音回我关于 T-158 的进展`
**When** manager `eduflow tts say "T-158 opus 上传通道已通，12 声线映射完成，下一步 T-159 出政策" --agent manager --to <main_chat_id>`
**Then** 主群收到 1 条 opus；频率限额当次豁免（boss_nudge=true 进 metadata）；后续 24h 计数正常

#### Case 6 — Happy path 阶段里程碑

**Given** Sprint 完工，所有 worker 完工报告已收入
**When** manager `eduflow tts say "Sprint 12 完工，12/12 agent 已报" --agent manager --to <main_chat_id>`
**Then** 主群收到 1 条 opus，时长 ≤8s；老板听一次即知完工面

#### Case 7 — 反例：低优先级闲聊触发 voice

**Given** manager 在群回 "好的" 后无业务动作
**When** manager 错误 `eduflow tts say "好的" --agent manager`
**Then** 路由层应拒绝（policy gate 拦截闲聊字符串长度 ≤ 4 字）；若硬发出，operator 事后 review 把这条作为培训素材

#### Case 8 — 反例：超 15s 长内容

**Given** manager 刚写了一篇 200 字的技术复盘
**When** `eduflow tts say "<200 字>" --agent manager --to <main_chat_id>`
**Then** TTS 命令应 warning + auto-truncate 到 75 字 / 或切成多段（v1 默认 auto-truncate）

#### Case 9 — 反例：超频率（>5 次 / manager / 24h）

**Given** manager 24h 内已发 5 次 voice，今需第 6 次报完工
**When** `eduflow tts say "完工" --agent manager --to <main_chat_id>`
**Then** 路由拒绝（reason=rate_limit），自动 fallback 到 say 文字 + DM manager 自报

#### Case 10 — 失败：TTS API 503

**Given** MiniMax API 临时返回 503
**When** `eduflow tts say "T-103 已闭环 ✅" --agent manager --to <main_chat_id>`
**Then** 主群收到 1 条**文字 say**（"⚠️ TTS 失败已回退：T-103 已闭环 ✅"，自动 fallback）；manager inbox 同时收到 1 条 DM（"manager TTS fail: 503 ..." 高优先级）

#### Case 11 — 失败：MINIMAX_AUTH_TOKEN 缺失

**Given** agent-home env 文件里 `MINIMAX_AUTH_TOKEN=` 未设
**When** `eduflow tts say "完工" --agent manager --to <main_chat_id>`
**Then** 命令立即返回 exit 1 + `❌ TTS failed: MINIMAX_AUTH_TOKEN (or MINIMAX_API_KEY) not set; check agent-home env files`；**不**发群（早返回）

#### Case 12 — 失败：opus 上传到 lark-cli 失败

**Given** MiniMax TTS 成功（mp3 bytes 落盘），但 `lark-cli im +messages-send --msg-type file` 退出非 0
**When** `eduflow tts say "T-103 已闭环 ✅" --agent manager --to <main_chat_id>`
**Then** 命令返回 `❌ TTS saved to /…/tts/last.mp3 but Feishu send failed: <err>`；manager 应 catch 后 `eduflow say manager "..." --to user` 文字回退 + DM manager 自报

---

## B. Per-Agent 使用建议（manager-only 详细；其他 11 agent 占位）

> 老板 T-140 范围调整：目前只要 manager 用语音汇报。其他 11 agent 的详尽建议冻结，pending 老板后续 enable（见 §E 扩展 checklist）。

### B.0 — manager（详细）

**声线**：海绵宝宝·大学生调高音（male-qn-daxuesheng / pitch 3 / speed 1.25）

**本质约束**：
- 速度快 + 升调 → 海绵宝宝风格的"轻快"本质
- 与"严肃追责" / "低声安抚" / "长篇技术"语义冲突 → 这些场景不该用 voice
- 是 manager "身份标识音"，应被保护作为品牌 → 频繁误用会贬值

#### 适合场景（5-7 类，对应 A.2）

| # | 场景 | 典型句式 | 时长 |
|---|---|---|---|
| 1 | **派工指令** | "worker_qbank 接 T-103 cross-system contamination" | ≤8s |
| 2 | **巡视汇报**（5min cadence） | "巡视发现 worker_qbank 卡 T-103，worker_course 正常" | ≤10s |
| 3 | **收口 ack** | "T-103 已闭环 ✅" | ≤3s |
| 4 | **告警升压** | "⚠️ router 失联，全员温备，已告警老板" | ≤6s |
| 5 | **老板点名**（boss_nudge=true） | "<回应老板点名内容>" | ≤10s |
| 6 | **阶段里程碑** | "Sprint 12 完工，12/12 agent 已报" | ≤8s |
| 7 | **追责定性**（critical bug） | "T-103 责任在 worker_qbank 校验未做，半年内二次发生" | ≤10s |

#### 不适合场景（声线与语义冲突，避免）

| 场景 | 为什么不合适 |
|---|---|
| 长篇技术报告（>75 字） | 速度 1.25 → 听者疲劳；超 15s 强拆段 |
| 严肃追责详细 | 海绵宝宝升调与"严肃"冲突；如需追责用 voice，写极简结论 + 文字详细 |
| 低声安抚（如 worker 失误道歉） | 升调与"安抚"语义相悖 → 改用 say 文字 |
| 开会讨论 / 多人对话 | 多人并发各自 voice 会刷屏 → 应有 voice 防抖（v2 才做） |
| raw 数据 / UUID 列表 / stack trace | 听感完全无意义（C-1 反模式） |
| emoji 反应 / 闲聊 | 信息密度太低（C-4 反模式） |
| 个别 worker 私有反馈 | 应走 `eduflow send worker_x manager` 文字通道，voice 不该侵入个人对话 |

#### manager 海绵宝宝风格具体限制

- ⚠️ **禁止**"派工细节"长篇配音（如 5 个 worker 的具体步骤）→ 走文字 say + 卡片
- ⚠️ **禁止**"代码 review 全文"配音 → 走文字 + 飞书文档链接
- ✅ **鼓励**"短句 ≤ 8s"的快节奏指令 / 收口 / 告警
- ✅ **鼓励**用 voice 把"语气"传达出来：紧迫、升压、轻快收口

#### 频率上限（同边界）

- ≤5 次 / manager / 24h
- 老板点名场景**单次豁免**（不计入 24h 计数）
- 超额 → 自动回退 say 文字 + DM manager 自报

---

### B.1 — B.12 其他 11 agent（**frozen pending boss approval**）

> ⚠️ **本段为占位 / frozen 段**。详细建议待老板显式 enable 后再展开。
> 启用流程见 §E 扩展 checklist。
> 当前建议：worker_* / Hermes / Sophon / Monica / Luke_recorder / anna 等 agent 一律**不发** `/voice`。

每个 agent 的声线配置已在 `eduflow.toml [tts.voice]` 中 freeze，但**未授权使用**：

| Agent | 声线 (frozen) | label | 当前状态 |
|---|---|---|---|
| Monica | female-shaonv / pitch 1 / speed 1.0 | 朱茵·紫霞 | frozen — fallback 期间独立判定 |
| Sophon | presenter_male / pitch -1 / speed 1.0 | 刘德华·无间道 | frozen — 监控员默不发 |
| Hermes | calm_female / pitch 1 / speed 1.0 | 知识库学术女 | frozen |
| Luke_recorder | female-shaonv / pitch 1 / speed 1.10 | 记录员嘴快活泼女 | frozen |
| worker_builder | male-qn-jingying / pitch -1 / speed 1.0 | 黄渤·草根工程师 | frozen |
| worker_course | calm_female / pitch 0 / speed 1.0 | 林青霞·东方不败 | frozen |
| worker_qbank | female-yujie / pitch 0 / speed 1.0 | 题库严谨女学者 | frozen |
| worker_school | calm_female / pitch 0 / speed 1.0 | 招生亲和女 | frozen |
| worker_syllabus | presenter_male / pitch -1 / speed 1.0 | 陈道明·康熙 | frozen |
| worker_teacher | calm_female / pitch 1 / speed 1.0 | 巩俐·归来 | frozen |
| worker_review | cantonese_male / pitch -2 / speed 1.0 | 张涵予·集结号 | frozen |

> 任何 agent 接到 voice 命令 → 路由层应**显式拒绝**（reason=policy_frozen）→ 自动 fallback 到 say 文字，并 DM manager 报 "agent_x voice attempt blocked by T-140 freeze"。

---

## C. 反模式清单（≥5）

> 这些场景**绝对不要**触发 `/voice`。列出来是为了：当有人误触发时，能在事后 manual review 里指出正确做法。

### C-1 — 不发 raw 数据
- **反模式**：`eduflow tts say "<100 个 UUID>"` / `<JSON dump>` / `<stack trace>`
- **为啥坏**：语音是时间序列，听者无法 skip；raw 数据听感极差且无意义
- **正确做法**：raw 数据 → 文字 say + 附件；voice 只说"已写入 status.json"

### C-2 — 不发长对话 / 长报告
- **反模式**：把 1000 字的 review 全文塞进 tts say
- **为啥坏**：>15s（≈75 字）听者注意力断崖下降
- **正确做法**：拆多段（每段独立 tts call），或彻底改用文字 say + 链接

### C-3 — 不替代 say 文字
- **反模式**：本该 `eduflow say manager "..." --to user` 写的群消息，被偷换成 tts
- **为啥坏**：voice 不能被复制粘贴 / 全文搜索 / 截图引用；丢失 audit trail
- **正确做法**：永远同时发文字（say）+ 可选 voice 附件；voice 不替代文字，必须共存

### C-4 — 不发低优先级闲聊 / emoji 反应
- **反模式**："好的，收到" / "嗯" / "在的" / emoji 反应 等用 voice
- **为啥坏**：5x 注意力消耗 vs 极低信息量；触发频率限额的概率变大
- **正确做法**：闲聊一律文字 + emoji；只有当内容 ≥ 1 句话且需要传达语气时再考虑 voice

### C-5 — 不发开会录音 / 会议纪要转 voice
- **反模式**：把多人会议录音 → TTS 转录 → 当一条 voice 发群
- **为啥坏**：会议录音本就杂音多，TTS 转出来更乱；时长必爆 15s
- **正确做法**：会议纪要写成结构化 markdown，发文字 + 飞书文档链接

### C-6 — 不发重复内容（与文字完全一样的复述）
- **反模式**：刚已文字 say "完工 ✅"，又触发 voice "完工 ✅"
- **为啥坏**：完全冗余，唯一差异是 band-width 占用 5x
- **正确做法**：要么纯文字、要么纯 voice；并存时 voice 必须补充文字无法传达的"语气/紧迫度"

### C-7 — 多人同时高并发 voice 无防抖（v1 不解决）
- **反模式**：5 个 agent 同时间向主群发 voice
- **为啥坏**：5x 同时段群刷屏，老板无法分清角色
- **正确做法**：v1 仅 manager 用 voice，无并发问题；v2 应加 5s 防抖

### C-8（删除：原 'manager 派工用语音' 已被 T-140 收回 → 现已允许）

> ~~C-8：manager 派工不应用 voice~~ → **已删除**
> 老板 T-140 明确："目前只要 manager 用语音汇报" → manager 派工是用 voice 的核心场景之一。

---

## D. Fallback 策略

### D.1 — 何时触发回退

| 失败模式 | 触发条件 | 用户可见行为 |
|---|---|---|
| TTS API 503 / 4xx / 5xx | `urllib.error.URLError` 或 HTTP 非 200 | 群内发文字 say：`<msg>` + "⚠️ TTS 失败已回退" |
| TTS 业务级错误 | `base_resp.status_code != 0`（MiniMax 返回 200 但报错） | 同上 |
| 音频 payload 空 | `data.audio == ""`（极少见，但发生过） | 同上 |
| lark-cli 上传失败 | `+messages-send --msg-type file` rc != 0 或 ok=false | 同上 + DM manager |
| `MINIMAX_AUTH_TOKEN` 缺失 | env 文件没有 export | 命令 exit 1，早返回，**不**发任何群消息 |
| `--to chat_id` 缺失 + toml 也没配 | 命令级错误 | 命令 exit 1 |
| 频率超额（>5/24h） | 边界 1 触顶 | 路由拒绝 → fallback say 文字 + DM 自报 |
| 其他 agent 触发（T-140 freeze） | policy gate | 路由拒绝 + DM manager 报 "agent_x voice attempt blocked by T-140 freeze" |
| 长内容 ≥15s | 边界 3 触顶 | auto-truncate 到 75 字 + warning |

### D.2 — 回退实现（policy 层）

```bash
# 标准回退模板（manager 应该这么写）
eduflow tts say "<msg>" --agent manager --to <chat_id> || {
  # T-140 v1 policy：失败即用文字 say 替代
  eduflow say manager "<msg>" --to user
  # 主动 DM manager 自报（避免静默回退）
  eduflow send manager manager "<msg truncated to 50 字> TTS fallback: <err>" 高
}
```

### D.3 — DM manager 内容规范

每次 fallback 必须发一条 DM 给 manager（或自报），**最少包含**：
- 哪个 agent（manager 自报时 = "manager"）
- 哪条 tts call 触发（msg truncated 到 50 字）
- 失败 err 摘要（不要 stack trace）
- 是否已用 say 文字替代
- 当前 24h 频率计数

格式：
```
[manager] TTS fallback — <text truncated to 50 字>
err: <one-line summary>
fallback: yes（已 say 文字）/ no（早返回未发群）
rate: <manager 当前 24h 频率计数>
```

### D.4 — Manager 海绵宝宝风格 fallback 特殊规则

- manager fallback 时**必须**立刻在原 opus 位置发**一条文字消息**说明："⚠️ TTS 失败，海绵宝宝这次没声音：" + 实际应发的文字内容
- 这是因为老板预期听到 manager 的"声线品牌"，突然缺失会造成认知断点 → 必须立即补足

### D.5 — 已知盲点（v1 不覆盖）

- opus / mp3 文件大小无显式校验（< 1MB 应该合理）
- 飞书 audio 消息在某些客户端不自动播放，需手动点
- 多人同时高并发发 voice（不强制串行；v2 应加 5s 防抖）

---

## E. 扩展 checklist：何时把 voice 启用扩展到其他 agent

> 老板 T-140 暂时只允许 manager。下列 checklist 是判断"可不可以扩展到 agent_x"的判定流程。

### E.1 硬性条件（全部满足）

- [ ] **群消息频率稳定** — agent_x 24h 文字 say 频率 ≤ 10 次（避免 voice 后变 5x 注意力）
- [ ] **TTS 配额富余** — MiniMax 24h token 配额使用率 < 60%（在 manager 5/天基线之上还有余量）
- [ ] **老板显式 enable** — `eduflow agent unlock <name> --voice` 命令已跑（解锁后从 frozen → active）
- [ ] **声线适用性已评估** — agent_x 的声线与人设匹配（参考 B.0 manager 的"适合/不适合"评估范式）
- [ ] **2 周监控期完成** — agent_x 跑过 ≥2 周 frozen 状态，期间无误触发 / 无投诉 / 无频率超额

### E.2 软性条件（至少满足 3 条）

- [ ] agent_x 的"语义快变量"任务占多数（巡视 / 收口 / 告警，非 raw 数据 / 长对话）
- [ ] agent_x 的声线辨识度有助于老板"听音识人"
- [ ] agent_x 当前已派工密度高（≥1 派单/天），voice 可减少文字开销
- [ ] 同类 agent 已 enable（如 worker_* 全员扩展，但要按 agent 一个个 enable）
- [ ] 团队节奏已稳定（无 router 失联 / 无 watchdog cooldown）超过 1 周

### E.3 扩展流程

1. manager 提议（PROGRESS 卡：建议 enable agent_x voice；列满足 E.1 + 软性 ≥3 条）
2. 老板拍板（`eduflow agent unlock <name> --voice`）
3. B.1 占位段更新为正式建议（仿 B.0 模板）
4. tests/scenarios/voice-usage-policy.md v2 发布（含 agent_x full Given/When/Then cases）

### E.4 反向 checklist（何时撤回 voice 权限）

- [ ] agent_x 单日 voice > 5 次（频率超额 ≥ 2 次）
- [ ] agent_x voice 触发 ≥ 1 次 C-1 / C-2 / C-3 / C-4 反模式
- [ ] 老板点名撤回（`eduflow agent relock <name> --voice`）

触发任一 → 自动回退 frozen 状态，需重新走 E.1+E.2 才能再 enable。

---

## F. 失败排查

| 现象 | 大概率原因 | 排查点 |
|---|---|---|
| TTS 命令 exit 1 但无 err 信息 | token 文件权限 / 网络 | `cat agent-home/env` 看 MINIMAX_AUTH_TOKEN；`curl` 试 t2a_v2 |
| opus 上传成功但群内看不到 | chat_id 错 / lark-cli profile 不匹配 | `eduflow team` 看 chat_id；手动跑 `lark-cli im +messages-send` |
| 频率超限但路由未拦 | routing rule 未上 | `grep "voice_rate" src/eduflow/feishu/router.py` |
| fallback 后 manager 未收到 DM | `eduflow send` 出错 | 看 manager pane 是否 alive |
| 声线与 agent 不匹配 | `[tts.voice]` 段没拉到 | `eduflow tts say "test" --agent <name> --no-send` 看 json 中的 voice 字段 |

## G. 不在范围

- voice clone（10s 极短录音生成专属声线；老板已说之后再说）
- `[tts.voice]` 段修改（已 freeze 2026-07-09；改前需解冻流程）
- 国际化声线（中文声线为主，英文/粤语暂不支持）
- multi-lingual TTS（多语言一句话暂不支持混合发音）
- 自动播放（客户端层，不归 policy 控）
- **其他 11 agent voice 启用**（T-140 范围调整，需走 §E 扩展 checklist）

## 版本

- v1（2026-07-09，T-159 → T-140 范围调整）
- 下次 review trigger：
  - 频率超额报警 ≥3 次
  - 老板点名改边界
  - TTS 模型升级
  - 老板 enable 第 2 个 agent 走通扩展（v2）
