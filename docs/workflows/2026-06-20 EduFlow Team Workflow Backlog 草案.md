# 2026-06-20 EduFlow Team Workflow Backlog 草案

## 定位

这里收两条已经被 gap note 证明有价值，但暂时不抢第一阶段主线的 workflow 候选。

它们现在不是 active workflow，原因是：还需要更多真实运行验证和更细的执行边界。

## backlog: runtime-recovery-and-resume

### 用途

用于处理运行态失败后的真实恢复，而不是只切模型或只看 status 文件。

典型触发：

- manager / review_course / worker_course 遇到 429。
- fallback 显示成功，但 live process env 没有切到备用 provider。
- pane ready，但最新 high-priority inbox 没有被消费。
- runtime-status.json 与真实 tmux pane / process env 不一致。
- agent 进程活着，但没有 meaningful action。

### candidate_chain

```text
Auto/Hermes -> manager -> worker_builder -> manager
```

说明：

- Hermes / auto_ops 可以报警。
- manager 负责正式处理和派工。
- worker_builder 负责沉淀恢复 checklist 与后续流程资产。

### 最小 acceptance gates

- `runtime_reality`: 必须看 live env / actual CLI / latest inbox consumed / meaningful action。
- `dispatch_acceptance_gate`: 恢复指令必须被 agent ACK，不只投递到 inbox。
- `stale_state_reconciliation`: 恢复后旧 task / 旧 unread 不得继续污染当前判断。

### forbidden_moves

- 只看 runtime-status.json 就宣布恢复。
- pane ready 但不确认 inbox consumed。
- 切模型后不确认实际进程 env。
- runtime 修复成功后，让 agent 继续旧线程而不处理最新高优指令。

### active 前需要补的内容

- 哪些命令算 live env 证据。
- 哪些信号算 meaningful action。
- 多久未 ACK 触发升级。
- Hermes 问题反馈群和 EduFlow Team 主群的边界。

## backlog: quality-gate-intervention

### 用途

用于高优质量门禁打断正常 topic rollover，避免问题继续扩散到下一批生产。

典型触发：

- review_course PASS 缺 file-level evidence。
- 用户指出质量问题，但 manager 尚未消费。
- manifest 与真实文件不一致。
- artifact path 漂移。
- worker_course 在质量门禁未解除时继续生产下一 topic。

### candidate_chain

```text
observer -> auto_ops -> manager -> review_course -> manager
```

说明：

- observer 可以是 user、Hermes、auto_ops 或现场 operator。
- auto_ops 只做 anomaly lane，不是 owner。
- manager 必须把 gate 转成正式流程指令。
- review_course 负责文件级验证。

### 最小 acceptance gates

- `quality_gate`: active gate 未解除前，不得 dispatch next topic。
- `file_evidence_gate`: review verdict 必须包含 sampled files / concrete checks / path convention check。
- `review_handoff_gate`: review_course 必须明确接到当前 gate 范围。
- `stale_state_reconciliation`: 旧 PASS 不能覆盖新 gate。

### forbidden_moves

- 把 quality gate 当普通 inbox 消息。
- manager 未消费高优 gate 就继续 rollover。
- review_course 只做摘要级 PASS。
- worker_course 在 gate 未解除时扩大生产。

### active 前需要补的内容

- quality gate 优先级定义。
- manager panel 如何显示 blocking gate。
- review evidence packet 的最小格式。
- gate 解除条件。

