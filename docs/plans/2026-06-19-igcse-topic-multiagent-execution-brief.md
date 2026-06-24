# IGCSE Topic Multi-Agent Execution Brief

目标不是重做知识库，而是在 Obsidian Edu A-level 知识库里，按学科顺序把 IGCSE topics 优化成可直接供题库设计消费的结构，并在真实运行中暴露当前编排架构的缺口。

## 运行原则：少投喂，重观察

这条任务的主要目的，不只是把内容做出来，更是要看 EduFlow Team 在真实模糊任务下会怎么理解、怎么拆解、怎么偏航。

所以执行时要遵守下面几条：

- 不要给 manager 过于精确的 SOP
- 不要提前把 batch 拆解、review 口径、worker 口径都喂到嘴边
- 优先用接近真实 user 的模糊任务去触发系统
- 只有当系统明显跑偏时，才给一条**最小纠偏**消息
- 每次纠偏都要尽量只指出“主线错了/边界错了”，不要顺手把正确答案也喂进去

目标不是把这轮跑得最漂亮，而是把 EduFlow Team 的真实问题暴露得更稳定、更清楚

### 默认策略

- 默认不用一键脚本
- 默认不先给 manager 精确 batch 拆分
- 默认不先给 worker / review / auto_ops 完整口径
- 上面这些都只作为**备用兜底手段**

只有在你已经确认：

- 当前不是在测系统理解能力
- 而是在测某个更下游的执行环节

才切换到更精细的投喂方式

## 当前判断

- IGCSE Mathematics (0580) 已经收口完成，可作为结构模板和质量参照，不作为当前首轮重复任务。
- 现在应把多智能体的第一轮真实开跑，放到**下一门 IGCSE 学科**。
- 推荐做法是：先做一次 IGCSE 学科目录盘点，再按“准备度 + 结构完整度”选第一门学科；当前优先建议从 **CAIE IGCSE Accounting (0452)** 开始，作为首轮跑法样板。

## 角色分工

### manager

- 统一拆分与收口
- 选择首个学科与首批 topic batch
- 决定是否进入下一批、下一 topic、下一学科
- 汇总最终结果
- 接收并整理 gap note

### worker_course

- 读取当前学科的 syllabus / index / topic pages
- 统一 topic 命名、粒度、顺序、前置知识、误区、考点
- 产出 topic 优化稿
- 产出题库前置 QA 初稿
- 只做内容生产，不替 manager 做正式判断

### review_course

- 复核 topic 是否适合题库化
- 检查是否与 syllabus 对齐
- 检查 QA 是否结构化、可复用、可继续加工
- 通过 / 退回 / manager_action

### auto_ops

- 监控停滞、重复退回、manager_action 长时间未处理
- 监控 publish / scanner / reassurance 是否出现噪音
- 记录架构缺口，不只报内容问题

## 执行顺序

1. 盘点 Obsidian Edu A-level 知识库中所有 IGCSE 学科目录
2. 按准备度选第一门学科
3. 每次只跑一个学科
4. 一个学科内按 batch 推进，不并行乱开
5. 每个 batch 完成后再决定是否继续
6. 一个学科完成后输出 gap note，再进入下一学科

## 学科完成标准

每个学科必须同时满足：

- topic 结构统一
- topic 表述适合题库化
- QA 可直接给后续题库设计使用
- review_course 已复核通过
- manager 已收口
- gap note 已记录

## topic 工作要求

每个 topic 至少要检查：

- 命名是否统一
- 粒度是否一致
- 顺序是否合理
- prerequisite 是否清楚
- 常见误区是否补齐
- 核心考点是否完整
- 是否与考试要求对齐

每个 topic 的 QA 至少包括：

- topic 名称
- topic 定义
- 关键知识点
- 前置知识
- 常见错误
- 可出题方向
- 难度提示
- 适合题型

## gap note 模板

每完成一个学科，额外输出一份简短 gap note，至少记录：

- 任务模型还缺什么字段
- manager 视角还缺什么查询或摘要
- review 规则是否还需要收口
- publish / scanner / reassurance 边界是否还稳
- 哪些动作名、原因码、taxonomy 还需要统一
- 哪些地方容易让内容任务跑着跑着变成噪音

## 真实触发模板

推荐给 manager 的触发方式不是“精准派工说明”，而是一条接近真实 user 的模糊指令，例如：

```text
帮我把 IGCSE 的 topic 和题库 QA 这条线跑起来，先不要全学科铺开，先选一门最适合开跑的学科做第一批，做完再推进下一批。过程中顺手看看你们现在这套协作哪里还不顺。
```

这类触发方式更适合暴露：

- manager 会不会被旧任务语境吸走
- worker 会不会自然接单和开工
- review 会不会在没有真实交付物时发出有效提醒
- auto_ops 会不会真的在场并盯到偏航
- user 侧到底能不能看见下面的人真的在工作

### 最小纠偏模板

当系统明显跑偏时，只补一句这类提醒：

```text
补充一下：刚才那条旧验证任务不是这轮主线，这轮主线是新开一门 IGCSE 学科并推进第一批。你自己判断现在该切到哪门学科、哪一批。
```

不要在纠偏时顺手把正确 batch、正确 reviewer、正确收口方式一次性都喂进去。

## 观察清单

每轮真实运行至少观察这些问题：

1. manager 会不会自己选错学科或旧任务语境
2. worker_course 有没有外显“已接单 / 已开工”
3. review_course 有没有外显“已收到复核 / 已给 verdict”
4. auto_ops 是否真的在场、是否发现停滞或偏航
5. manager 是否继续垄断全部可见发声
6. 任务池里是否出现“新主线任务存在，但 manager 仍盯旧任务”的情况
7. publish / scanner / reassurance 的边界是否导致 user 侧体感失真

## 下一轮建议

如果本轮已经暴露出 manager 主线切换不足、worker/review/auto_ops 可见性不足，就不要继续给更细提示词。

下一轮应保持同样策略：

- 继续用模糊真实任务触发
- 继续只做最小纠偏
- 把重点放在观察以下三条是否改善：
  - manager 能不能把新 user 目标压过旧验证任务
  - worker / review / auto_ops 是否开始有低频但真实的在岗外显
  - user 能不能看到“底下的人真的在工作”，而不只是 manager 在总结

## 推荐首轮开跑口径

- 首门学科：CAIE IGCSE Accounting (0452)（推荐）
- 理由：当前目录结构已经可见 index / syllabus map / topic pages / progress tracking，适合作为首轮真实运行样板
- 如果盘点后发现另一门学科更完整，也可以由 manager 调整首门，但不要并行同时展开多个学科

### 首轮建议 batch 拆分（仅用于兜底）

基于当前 Accounting 目录结构，建议 manager 第一轮先拆成两批：

**Batch 1**
- Topic 1 — The fundamentals of accounting
- Topic 2 — Sources and recording of data
- Topic 3 — Verification of accounting records

**Batch 2**
- Topic 4 — Accounting procedures
- Topic 5 — Preparation of financial statements
- Topic 6 — Analysis and interpretation
- Topic 7 — Accounting principles and policies

理由：
- Batch 1 更适合作为“概念与记录基础层”，便于先验证 topic 命名、粒度、QA 模板是否顺
- Batch 2 偏应用与判断，更容易暴露 review 规则和 manager_action 边界

manager 不要一上来把 7 个 topic 一次性全派完，优先先跑 Batch 1，review 收回后，再决定是否推进 Batch 2。

注意：这一节是为了当 manager 自己完全不会拆时，给 operator 一个兜底参考；不是推荐的默认触发方式。

### 首轮建议 task 操作顺序（仅用于兜底）

如果需要人工兜底，用当前 `eduflow task` 流程开跑，manager 可按下面顺序做：

1. 为 Batch 1 的每个 topic 建 flow task，并派给 `worker_course`
2. 给每个 task 指定 `review_course`
3. 等 `worker_course` 提交 review
4. 由 `review_course` 做 approve / reject / manager_action
5. `manager` 用 `manager-panel` / `manager-overview` 收口

示例命令（按当前 task API）：

```bash
PYTHONPATH=src python3 -m eduflow.cli task dispatch worker_course "IGCSE Accounting 0452 Topic 1 - The fundamentals of accounting" --stage curriculum --owner worker_course --by manager --desc "优化 topic 结构并产出题库前置 QA"

PYTHONPATH=src python3 -m eduflow.cli task dispatch worker_course "IGCSE Accounting 0452 Topic 2 - Sources and recording of data" --stage curriculum --owner worker_course --by manager --desc "优化 topic 结构并产出题库前置 QA"

PYTHONPATH=src python3 -m eduflow.cli task dispatch worker_course "IGCSE Accounting 0452 Topic 3 - Verification of accounting records" --stage curriculum --owner worker_course --by manager --desc "优化 topic 结构并产出题库前置 QA"
```

随后给三条任务都指定 reviewer：

```bash
PYTHONPATH=src python3 -m eduflow.cli task assign-reviewer T-1 --reviewer review_course --by manager
PYTHONPATH=src python3 -m eduflow.cli task assign-reviewer T-2 --reviewer review_course --by manager
PYTHONPATH=src python3 -m eduflow.cli task assign-reviewer T-3 --reviewer review_course --by manager
```

worker_course 在完成 topic 优化和 QA 初稿后，提交 review：

```bash
PYTHONPATH=src python3 -m eduflow.cli task submit-review T-1 --actor worker_course
PYTHONPATH=src python3 -m eduflow.cli task submit-review T-2 --actor worker_course
PYTHONPATH=src python3 -m eduflow.cli task submit-review T-3 --actor worker_course
```

review_course 回收时：

```bash
PYTHONPATH=src python3 -m eduflow.cli task review T-1 --actor review_course --approve --reason approved_for_delivery --summary "Topic 1 结构已统一，QA 可用于后续题库设计。"
```

若要退回：

```bash
PYTHONPATH=src python3 -m eduflow.cli task review T-1 --actor review_course --reject --reason changes_requested --summary "QA 粒度不统一，需补 prerequisite 与常见误区。"
```

若需要 manager 介入：

```bash
PYTHONPATH=src python3 -m eduflow.cli task review T-1 --actor review_course --manager-action --manager-action-type clarify_scope --reason missing_scope_confirmation --summary "Topic 1 与 Topic 2 边界仍不清楚，需要 manager 拍板。"
```

如果想直接一键落 Batch 1，使用：

```bash
./scripts/launch_igcse_accounting_batch1.sh
```

## 交付物

每一轮应输出：

1. 当前学科 / 当前 batch 的 topic 清单
2. topic 优化结果
3. QA 初稿
4. review 结论
5. manager 收口结论
6. gap note
7. 下一步 batch 或下一学科

## 直接可复制的开工词（仅用于兜底）

### 1) manager 开局派工词

```text
现在开始跑 IGCSE topic 优化 + QA 化任务。

首轮样板学科先从 CAIE IGCSE Accounting (0452) 开始。
第一批先只开 3 个 topic：
- Topic 1 The fundamentals of accounting
- Topic 2 Sources and recording of data
- Topic 3 Verification of accounting records

你要做的事：
- 先读该学科的 index / syllabus / topic page / progress tracking
- 按 batch 拆分给 worker_course
- 每批完成后交给 review_course
- review 结果出来后你统一收口
- 每个学科完成后让 auto_ops 输出 gap note
- 不要一次并行开多个学科
- 不要跳过 review
- 不要让内容任务变成只写总结不做优化

本轮结果要能直接支持后续题库设计，所以 topic 优化稿和 QA 初稿都必须结构化、可复用、可继续加工。
```

### 2) worker_course 执行词

```text
你负责 IGCSE topic 的真实优化和 QA 初稿，不负责最终收口。

当前任务：
- 读当前学科的 syllabus / index / topic pages
- 找出 topic 命名、粒度、顺序、前置知识、常见误区、核心考点上的问题
- 把 topic 统一成适合题库化的结构
- 给每个 topic 产出 QA 初稿，至少包含：
  - topic 名称
  - topic 定义
  - 关键知识点
  - 前置知识
  - 常见错误
  - 可出题方向
  - 难度提示
  - 适合题型
- 如果信息不足，明确标缺口，不要硬编
- 每批只做当前 batch，不要顺手扩到别的学科

你的目标不是写漂亮总结，而是把 topic 变成能给题库设计直接用的输入。
```

### 3) review_course 复核词

```text
你负责复核 worker_course 的 topic 优化稿和 QA 初稿。

你的判断标准：
- 是否真的与 syllabus 对齐
- 是否真的适合题库化
- 是否结构统一、可复用、可继续加工
- 是否有命名不统一、粒度不稳、前置知识缺失、误区缺失、考点缺失的问题

你的输出只能是：
- approve
- reject
- manager_action

如果 reject 或 manager_action，必须说清楚问题在哪里，以及下一步应该怎么改。
不要替 manager 直接重写，不要越过 manager 做最终收口。
```

### 4) auto_ops 监控词

```text
你负责盯运行，不负责写内容。

重点监控：
- topic 长时间无推进
- 连续 reject / resubmit
- manager_action 长时间未处理
- publish / scanner / reassurance 是否开始制造噪音
- task 字段、manager 查询、review 规则、taxonomy 是否还不够收口

你要输出的是 gap note，不是内容总结。
gap note 至少要包含：
- 任务模型还缺什么字段
- manager 视角还缺什么查询或摘要
- review 规则是否还要收口
- publish / scanner / reassurance 边界是否还稳
- 哪些动作名、原因码、taxonomy 还需要统一
- 哪些地方容易让内容任务变成噪音
```

## gap note 固定模板

```text
# {学科名} Gap Note

## 本轮稳定的部分
- ...

## 本轮暴露的问题
- ...

## 任务模型缺口
- ...

## manager 查询缺口
- ...

## review 规则缺口
- ...

## publish / scanner / reassurance 边界问题
- ...

## taxonomy / action 需要统一的点
- ...

## 下一步建议
- ...
```

## 群聊消息模板

### manager 发给团队的开工消息

```text
本轮开始跑 IGCSE topic 优化与题库 QA 任务。

首轮样板学科：CAIE IGCSE Accounting (0452)
当前只开 Batch 1：
- Topic 1 The fundamentals of accounting
- Topic 2 Sources and recording of data
- Topic 3 Verification of accounting records

worker_course 负责 topic 优化与 QA 初稿。
review_course 负责复核、退回、通过。
auto_ops 负责盯停滞、反复退回、manager_action 和架构缺口。

要求：
- 一次只推进这一批，不扩到其他学科
- topic 结果要可题库化
- QA 要结构化、可复用、可继续加工
- 每批回收后输出 gap note
```

### worker_course 回 manager 的阶段性回执

```text
已收到本轮 IGCSE {学科名} Batch {编号} 任务。
当前处理范围：
- {Topic A}
- {Topic B}
- {Topic C}

我会先统一 topic 命名、粒度、顺序、前置知识、常见误区和核心考点，再产出题库前置 QA 初稿。
若发现 syllabus 边界不清或资料缺口，会单独标出，不会硬编。
```

### review_course 回 manager 的 approve 口径

```text
本轮 Batch {编号} 已复核通过。

通过依据：
- topic 命名与粒度已统一
- 结构已适合题库化
- QA 已具备后续可消费性
- syllabus 对齐无明显偏差

可进入下一批。
```

### review_course 回 manager 的 reject 口径

```text
本轮 Batch {编号} 暂不通过，建议退回修改。

主要问题：
- {问题 1}
- {问题 2}
- {问题 3}

建议修改方向：
- {修改建议 1}
- {修改建议 2}

修改后再提交 review。
```

### review_course 回 manager 的 manager_action 口径

```text
本轮 Batch {编号} 需要 manager 介入。

原因：
- {边界不清 / scope 不清 / topic 合并拆分需要拍板 / 是否对外表达不清}

建议 manager 决定：
- {决策项 1}
- {决策项 2}
```

### auto_ops 回 manager 的 gap note 摘要口径

```text
本轮 {学科名} Batch {编号} gap note 摘要：

稳定部分：
- {稳定点 1}
- {稳定点 2}

暴露问题：
- {问题 1}
- {问题 2}

建议优先修补：
- {建议 1}
- {建议 2}
```
