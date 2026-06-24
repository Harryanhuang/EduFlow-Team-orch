# Trigger

当以下任一条件出现时，启动 runtime-failover-hardening：

- 昨晚 gap note 中 runtime 相关条目 ≥ 3 个（60/63/65/66/67/71/86/96/98/119/120/121/123/124/125/126/127）
- manager 或任意 critical agent 出现 runtime-status 与 live env 漂移
- 同额度池 fallback 循环导致 429 不恢复
- 切换后高优 inbox 60s 内未消费
- 全局 eduflow 二进制 import 路径不在本项目 src/ 内

## Standard Manager Call

```text
调用 workflow: runtime-failover-hardening
对象: <agent / pool / runtime switch case>
范围: detect failure → cross-pool switch → env verify → API smoke → inbox recovery
边界:
- 实施位 = worker_builder；smoke = auto_ops；复核 = review_course
- 必须保留 17 条 gap case → 代码路径映射证据
- manager 拥有最终 closeout 与 follow-up 拍板
需要的 verdict / artifact:
- runtime verify 输出 proved_ready / ready_unproven / env_drift 等口径
- health 显示 import path matches EDUFLOW_ROOT
- runtime events JSON 含 ts/agent/from_runtime/to_runtime/reason/outcome/trigger/cross_pool/env_ok/smoke_ok
```
