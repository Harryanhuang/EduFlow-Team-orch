# 2026-06-20 EduFlow Team Workflow 生命周期与维护规则

## 目标

这份规则解决 workflow “常用常新”的问题。

EduFlow Team 的 workflow 不是写完就封存的说明书。它必须随着真实运行不断更新，但更新不能随意漂移。第一版采用轻量生命周期，不做数据库或自动引擎。

## 生命周期状态

### `draft`

含义：

- 有明确场景，但还没有充分真实运行验证。
- 可以试用，但 manager 不应把它当稳定流程。

进入条件：

- 新需求出现。
- builder 能写出初版 trigger / participants / expected outputs。
- 至少能说明为什么不是已有 workflow 的小变体。

### `validated`

含义：

- 已被一次真实运行验证。
- 仍需要观察更多边界。

进入条件：

- 至少有一个真实案例能回测。
- 关键 handoff chain 跑通过。
- 至少一个 acceptance gate 被实际触发或验证。

### `active`

含义：

- manager 可以正式调用。
- builder 负责维护。

进入条件：

- 至少一次真实运行闭环通过。
- forbidden moves 清楚。
- done definition 清楚。
- 出现异常时知道停在哪个 gate。

### `stale`

含义：

- workflow 仍有历史价值，但已不适合直接调用。

进入条件：

- agent 命名、runtime、产物路径或业务边界变化后未更新。
- 最近真实运行反复绕开这条 workflow。
- workflow 与 gap note 新事实冲突。

## 更新触发

任一情况出现，worker_builder 必须检查 workflow 是否要更新：

- manager 临场反复补同一种流程说明。
- worker / review / qbank 多次卡在同一 handoff。
- review verdict 与文件真相不一致。
- 高优质量门禁未阻断正常推进。
- runtime 恢复状态与 live pane 不一致。
- user 需要通过现场提醒才能发现 agent 没外显。
- 产物路径、命名、manifest 发生漂移。

## 维护职责

### manager

- 负责调用 workflow。
- 负责确认 workflow 是否纳入 registry。
- 负责正式拍板 active / backlog / stale。

### worker_builder

- 负责维护 workflow 文档。
- 负责把真实运行样本升级成 workflow 资产。
- 负责提出 registry 更新建议。
- 负责把固定动作反哺为 skill / template / identity 建议。

### review_course / worker_qbank / worker_course

- 负责反馈自己在 workflow 中的 handoff 缺口。
- 负责让自己的 verdict / artifact 能被 workflow gate 检查。

### auto_ops

- 只负责 watcher / anomaly lane。
- 可以提出某条 workflow 需要更新。
- 不作为 workflow owner。

## 版本更新最小记录

每次更新 workflow，至少记录：

- 更新日期。
- 触发样本。
- 更新了哪个 gate / forbidden move / done definition。
- 是否改变 status。
- 下一次需要观察什么。

## 不做什么

- 不为 lifecycle 建数据库。
- 不做自动 schema 校验。
- 不把 workflow 更新变成每次都要大评审。
- 不允许没有真实样本的抽象扩写污染 active workflow。

