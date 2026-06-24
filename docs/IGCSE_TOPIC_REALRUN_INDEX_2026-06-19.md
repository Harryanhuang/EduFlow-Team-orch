# IGCSE Topic Real-Run Index

这页是 IGCSE topic 多智能体真实运行的导航入口。

目标不是把某一轮任务跑得最顺，而是持续用真实 IGCSE 学科任务去撞 EduFlow Team，暴露并记录 manager / worker_course / review_course / auto_ops 的真实问题。

## 先看什么

### 1. 执行 brief

如果你要知道这一轮任务整体怎么跑，看这里：

- [IGCSE Topic Multi-Agent Execution Brief](/Volumes/Halobster/Codex相关/EduFlow-Team-orch/docs/plans/2026-06-19-igcse-topic-multiagent-execution-brief.md)

用途：

- 任务边界
- 角色分工
- 学科推进方式
- topic / QA 的基本要求

### 2. operator checklist

如果你要知道“怎么观察系统露馅”，看这里：

- [IGCSE Topic Real-Run Operator Checklist](/Volumes/Halobster/Codex相关/EduFlow-Team-orch/docs/IGCSE_TOPIC_REALRUN_OPERATOR_CHECKLIST_2026-06-19.md)

用途：

- 真实触发后先看什么
- 发现偏航时怎么做最小纠偏
- 每轮必须记录什么 gap

### 3. preflight

如果你要开始一轮新的真实运行，先看这里：

- [IGCSE Topic Real-Run Preflight](/Volumes/Halobster/Codex相关/EduFlow-Team-orch/docs/IGCSE_TOPIC_REALRUN_PREFLIGHT_2026-06-19.md)

用途：

- 确认 state_dir
- 看旧任务池是否污染新观察
- 决定本轮是保留旧任务，还是新 run 隔离

## 本轮已经发现了什么

本轮真实偏航结论在这里：

- [IGCSE Topic Real-Run Gap Note](/Volumes/Halobster/Codex相关/EduFlow-Team-orch/docs/IGCSE_TOPIC_REALRUN_GAP_NOTE_2026-06-19.md)

当前已经比较明确的结论：

1. manager 会被旧验证任务语境吸走
2. 新 user 目标压不过旧任务上下文
3. worker / review / auto_ops 的 user-facing 可见性还没真正立住
4. `worker_to_user = false` 让 user 侧仍然主要只看到 manager 在说话
5. auto_ops 理论上应在场，但真实运行里其存在感并不稳定

## 推荐使用顺序

### 如果你要开一轮新的 IGCSE 学科测试

1. 先看 preflight
2. 再看 operator checklist
3. 然后用 brief 里的模糊真实触发词启动
4. 最后把这一轮结果写回新的 gap note

### 如果你要继续修系统

先优先处理这些问题：

1. manager 主线切换能力不足
2. worker / review / auto_ops 低频在岗外显不足
3. operator 对 state_dir / session 状态的误判风险

## 不建议做什么

- 不建议一上来继续写更精准的 manager 提示词
- 不建议先把正确 batch / reviewer / 收口方式全喂进去
- 不建议为了看起来顺利而跳过真实偏航

因为这会遮住 EduFlow Team 的真实问题。
