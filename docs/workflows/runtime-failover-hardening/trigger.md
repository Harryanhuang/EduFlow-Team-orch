# Trigger

当以下任一条件出现时，启动 runtime-failover-hardening：

- 昨晚 gap note 中 runtime 相关条目 ≥ 3 个（60/63/65/66/67/71/86/96/98/119/120/121/123/124/125/126/127）
- manager 或任意 critical agent 出现 runtime-status 与 live env 漂移
- 同额度池 fallback 循环导致 429 不恢复
- 切换后高优 inbox 60s 内未消费
- 全局 eduflow 二进制 import 路径不在本项目 src/ 内
