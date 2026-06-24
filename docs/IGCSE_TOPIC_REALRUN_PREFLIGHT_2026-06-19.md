# IGCSE Topic Real-Run Preflight

这份 preflight 不是部署文档，而是每次开始一轮新的 IGCSE 学科真实运行前，用来减少“旧任务污染新观察”的操作清单。

## 为什么需要这份清单

本轮真实运行已经证明：

- 旧验证任务会污染 manager 对新 user 目标的判断
- 默认 `~/.eduflow` 与 repo-local `.eduflow-team-state` 容易混淆
- 没做隔离时，很难判断问题到底来自系统能力，还是来自旧状态残留

所以每次开始一轮新的 IGCSE 学科真实运行前，先做 preflight。

## 一、确认 state_dir

必须先确认当前用的是哪一个 state_dir。

推荐：

```bash
cd /Volumes/Halobster/Codex相关/EduFlow-Team-orch
. ./scripts/eduflow-team-env.sh
PYTHONPATH=src python3 -m eduflow.cli health
```

检查点：

- `state_dir` 是否指向 repo-local `.eduflow-team-state`
- 不要误用默认 `~/.eduflow`

## 二、看当前任务池里有没有旧任务

```bash
PYTHONPATH=src python3 -m eduflow.cli task list
PYTHONPATH=src python3 -m eduflow.cli task manager-overview
```

重点看：

- 有没有旧验证任务
- 有没有已经不属于当前 user 主线的历史任务
- 有没有未完成但其实不打算继续推进的老任务

如果有，就先记录，不要直接忽略。

## 三、区分“旧任务保留观察”还是“新 run 隔离”

每轮开始前先做判断：

### 方案 A：保留旧任务

适用场景：

- 你就是想观察“新 user 目标压过旧任务”这件事
- 你故意要看 manager 会不会被旧语境吸走

优点：

- 更真实
- 更容易暴露 manager 主线切换能力问题

缺点：

- 观测噪音更大
- 更难判断下游执行问题

### 方案 B：新 run 隔离

适用场景：

- 你已经确认 manager 主线切换问题存在
- 下一轮想测的是 worker / review / auto_ops 的执行链本身

优点：

- 观察更干净
- 更容易定位下游链路问题

缺点：

- 会少掉一层真实任务竞争压力

## 四、如果选择“新 run 隔离”

建议至少做到：

- 新建独立 state_dir
- 明确当前 run scope
- 不混用旧 task pool

例如：

```bash
export EDUFLOW_STATE_DIR=/tmp/eduflow-igcse-run-01
PYTHONPATH=src python3 -m eduflow.cli up
```

或者单独复制现有 env 脚本，再覆盖 `EDUFLOW_STATE_DIR`。

## 五、确认 tmux / agent 在不在场

```bash
PYTHONPATH=src python3 -m eduflow.cli health
PYTHONPATH=src python3 -m eduflow.cli team
```

重点看：

- manager 是否 ready
- worker_course 是否 ready
- review_course 是否 ready
- auto_ops 是否真的有 pane / 会话

因为这轮已经证明：

- 配置里有 agent
- 不等于它真的在场

## 六、确认本轮到底要测什么

不要一轮里同时测太多东西。

开始前先写清楚：

- 这轮是测 manager 主线切换？
- 还是测 worker/review/auto_ops 外显？
- 还是测 topic + QA 真实生产链？

如果不先定目标，很容易把所有问题混在一起。

## 七、推荐顺序

### 第一类轮次：主线切换测试

- 保留旧任务
- 给模糊真实 user 指令
- 看 manager 会不会被旧语境吸走

### 第二类轮次：执行链测试

- 用新 run 隔离
- 让 manager 重新接一条模糊任务
- 观察 worker / review / auto_ops 是否真的动起来并且可见

## 八、每轮开始前的最小记录

至少记录：

- 当前 state_dir
- 当前 task pool 概况
- 当前 tmux / agent 状态
- 当前 run 的测试目标

这样后面写 gap note 时，才能说清楚这轮问题到底是在什么前提下出现的。
