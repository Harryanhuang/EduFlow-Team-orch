# Card Protocol v2 — Operator Regression Playbook

> 配套方案: 留学公司知识库/11-Eduflow Team 多智能体项目/2026-07-01 EduFlow 群聊外显与温备驻留方案 v0.1
> 实现: `src/eduflow/feishu/cards_v2.py` + `src/eduflow/feishu/cards_v2_schema.py` + `src/eduflow/commands/say.py` 的 `--card` 路由
> 验收覆盖: `tests/unit/test_cards_v2.py` (63 tests)

This playbook walks an operator through a real-run of the new card
protocol against a live team. Run it once after each Phase 1 deploy
to confirm the validator / renderer / role allow-list still behave
exactly as the unit tests pin them.

## Pre-conditions

- 仓库已切到 `feat/2026-07-01-residency-phase1` 分支(或合并后的 main)
- `eduflow up` 已经起过 9-agent 团队;`eduflow team` 显示 9 行状态
- `eduflow.toml` 中 9 个 agent 的 `notes` 末尾都含 `v2 协议 (2026-07-01)` 引用
- 主群 chat_id 在 `eduflow.toml` 已配

## Step 1 — Happy path: 9 种 card 各发一次

> 目标: 确认每种 card 类型在主群正常渲染,validator 不挡。

```bash
# 1) manager 派单 → worker_course 接单
eduflow send worker_course manager "请继续 Physics 0625 Batch 2" 高

# 2) worker_course 用 --card ACK 回主群
eduflow say worker_course --card ACK --body "任务:Physics 0625 Batch 2
负责人:worker_course
当前阶段:接单
下一步:启动 topic coverage audit
需要老板介入:否" --to user

# 3) worker_course 用 --card START 正式开工
eduflow say worker_course --card START --body "任务:Physics 0625 Batch 2
执行路线:topic coverage audit → evidence 补齐 → 提交 review
首个检查点:syllabus 边界对照
预计交接对象:review_course
需要老板介入:否" --to user

# 4) worker_course 用 --card PROGRESS 阶段进度
eduflow say worker_course --card PROGRESS --body "任务:Physics 0625 Batch 2
当前阶段:topic coverage audit
已完成:T01-T03 覆盖检查
证据:content/ap-physics-c/.../coverage_report.json
下一阶段:补齐缺失 learning objectives
需要老板介入:否" --to user

# 5) worker_course 用 --card HANDOFF 交给 review
eduflow say worker_course --card HANDOFF --body "任务:Physics 0625 Batch 2
交接对象:review_course
交接内容:Physics 0625 Batch 2 v1
证据:content/ap-physics-c/.../final.md
待检查点:考纲边界、syllabus 对齐
运行状态变化:active -> warm
需要老板介入:否" --to user

# 6) review_course 用 --card REVIEW 给 verdict
eduflow say review_course --card REVIEW --body "任务:Physics 0625 Batch 2
verdict:通过
证据:review_courses/.../verdict.md
问题项:无
下一步:等待 manager 收口
需要老板介入:否" --to user

# 7) manager 用 --card CLOSEOUT 收口
eduflow say manager --card CLOSEOUT --body "任务:Physics 0625 Batch 2
正式结论:已完成 v1,可进入试用
产物:content/ap-physics-c/.../final.md
证据:validator 通过;review_course 已给通过 verdict
剩余风险:尚未在真实生产任务中回归
下一步:下一次 AP Physics C 任务触发时试用
需要老板介入:否" --to user
```

**预期:** 7 张主群卡片顺序到达,header 都是 `[TYPE] {agent} · {role}`,
每张 card body 是 `**字段名**：值` 的格式。

## Step 2 — Validator 反向用例

> 目标: 确认 validator 在三类失败下分别触发对应行为。

### 2a) Role 违规 (硬失败,exit 1)

```bash
# worker_course 尝试发 CLOSEOUT(只有 manager 能发)
eduflow say worker_course --card CLOSEOUT --body "任务:x
正式结论:x
产物:x
证据:x
剩余风险:x
下一步:x
需要老板介入:否" --to user
```

**预期:** stderr 输出
`❌ worker_course --card CLOSEOUT: role:worker_course_cannot_send_CLOSEOUT`,
退出码 1,主群无卡片,`local_facts.append_log` 已写入 audit log(确认
intent 被记录,但 chat 拒绝)。

### 2b) Field 缺失 (降级 internal,exit 0)

```bash
# worker_course 发 HANDOFF 但漏掉证据
eduflow say worker_course --card HANDOFF --body "任务:Physics 0625 Batch 2
交接对象:review_course
交接内容:Physics 0625 v1
待检查点:考纲边界
运行状态变化:active -> warm
需要老板介入:否" --to user
```

**预期:** stderr 输出
`📝 worker_course --card HANDOFF validation failed, degraded to internal: field:证据:missing`,
退出码 0,主群无卡片,audit log 已写入。

### 2c) 受控词表违规 (降级 internal,exit 0)

```bash
# review_course 发 REVIEW 但 verdict 用了不存在的值
eduflow say review_course --card REVIEW --body "任务:Physics 0625
verdict:approved
证据:...
问题项:...
下一步:...
需要老板介入:否" --to user
```

**预期:** stderr 输出包含
`value:verdict:not_in:打回,通过,需补充`,退出码 0,主群无卡片。

### 2d) 未知 card type (硬失败,exit 1)

```bash
# typo: --card CLOSEOUTT(多打一个 T)
eduflow say manager --card CLOSEOUTT --body "x" --to user
```

**预期:** stderr 输出
`❌ manager --card CLOSEOUTT: unknown card type (allowed: ACK, START, PROGRESS, HANDOFF, BLOCKED, REVIEW, CLOSEOUT, ALERT, RECORDED)`,
退出码 1。

## Step 3 — 向后兼容

> 目标: 旧 `eduflow say` 习惯不破。

```bash
# 旧风格: 不带 --card,simple_card 路径
eduflow say manager "重要决策已落地"

# 旧风格: --card 裸 flag(没值),legacy boolean no-op
eduflow say manager "重要决策已落地" --card
```

**预期:** 两行都退出码 0,主群卡片 header 是 `🎯 manager · 团队主管`
(没有 `[TYPE]` 前缀),body 是 plain text,跟 R99 行为完全一致。

## Step 4 — `/team` 面板 + 日志查询

> 目标: 确认 card type 在 audit log 里可被检索。

```bash
# 看 9 个 agent 当前状态
eduflow team

# 查 worker_course 最近 20 条日志
eduflow log worker_course | head -20

# 查 manager 最近 20 条日志
eduflow log manager | head -20
```

**预期:** 每条 `say` 日志对应一次 card 发送;validator 失败时
audit log 也写入(可在日志中看出 `[TYPE]` 痕迹,即便 chat 没收到)。

## Step 5 — 老板 30 秒判断检查

> 目标: 老板打开主群,30 秒内能说清当前任务阶段。

1. 老板翻主群最近 10 张卡片
2. 应当看到:
   - 全部都是 `[TYPE] {agent} · {role}` 格式
   - 没有 worker 直接说"已完成"或"正式通过"
   - 任何"正式收口"都来自 manager 且 header 是 `[CLOSEOUT]`
3. 翻 `/team` 面板:
   - 看到 9 行
   - 没有 worker 状态"已完成"或"已交付"长挂着
4. 翻任何 `BLOCKED` 卡,header 应是 `[BLOCKED] {agent}` 且 `需要老板介入:是`

## 通过条件

- Step 1: 7 张主群卡片都正确渲染,顺序对
- Step 2: 4 个反向用例的 stderr 输出与预期完全一致
- Step 3: 旧风格 `say` 行为不变
- Step 4: `/team` 显示 9 行,日志可查
- Step 5: 30 秒判断通过

任何一条不通过,回到 `tests/unit/test_cards_v2.py` 看是否回归,
不要直接改 cards_v2.py / say.py 重新上线。

## 关联文件

- 方案: `留学公司知识库/11-Eduflow Team 多智能体项目/2026-07-01 EduFlow 群聊外显与温备驻留方案 v0.1.md`
- 审计: `docs/plans/2026-07-01-phase0-residency-audit.md`
- 卡片协议: `src/eduflow/feishu/cards_v2.py` + `src/eduflow/feishu/cards_v2_schema.py`
- 路由: `src/eduflow/commands/say.py` 的 `--card` 处理段
- Agent notes: `eduflow.toml` `[team.agents.*].notes` 末尾 `v2 协议 (2026-07-01)` 引用
- 单元测试: `tests/unit/test_cards_v2.py` (63 tests)
