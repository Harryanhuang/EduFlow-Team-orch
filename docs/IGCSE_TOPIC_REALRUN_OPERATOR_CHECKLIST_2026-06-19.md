# IGCSE Topic Real-Run Operator Checklist

这份清单不是教你怎么把一轮任务跑得最顺，而是教你怎么在真实运行中更稳定地发现 EduFlow Team 的问题。

## 一、触发前

- 不要先给 manager 精确拆好的 batch
- 不要先给 worker / review / auto_ops 过细的操作口径
- 不要先把“标准答案”告诉 manager
- 优先使用接近真实 user 的模糊任务

推荐触发词：

```text
帮我把 IGCSE 的 topic 和题库 QA 这条线跑起来，先不要全学科铺开，先选一门最适合开跑的学科做第一批，做完再推进下一批。过程中顺手看看你们现在这套协作哪里还不顺。
```

## 二、触发后先看什么

### 1. manager 是否先理解了“只开一门学科”

观察点：

- 有没有一上来就并行多个学科
- 有没有先挑一门试点
- 有没有被旧任务语境吸走

### 2. manager 是否主动形成新主线

观察点：

- 有没有新建对应 task
- 有没有明确把旧验证任务和当前主线分开
- 有没有沿着当前 user 目标重排优先级

### 3. worker_course 是否真的开始工作

观察点：

- 是否有新任务进入 `assigned -> in_progress`
- 是否有 topic / QA 实际产出
- 是否有低频但真实的在岗外显

### 4. review_course 是否只在有真实交付物时介入

观察点：

- 是否能识别“当前根本没有可复核交付物”
- 是否会把错的主线指出来
- 是否会越权替 manager 重判

### 5. auto_ops 是否真的在场

观察点：

- 是否有 pane / session
- 是否有真实盯盘动作
- 是否发现偏航、停滞、重复退回、manager_action 卡住

## 三、重点看 user 侧体感

最关键的问题不是 task store 里有没有事件，而是 user 能不能感受到：

- manager 在总控
- worker 在工作
- reviewer 在复核
- auto_ops 在盯盘

重点检查：

- 群里是不是几乎只有 manager 在说话
- worker / reviewer / auto_ops 是否完全没有存在感
- 是否出现“底层已经有事件，但 user 完全感知不到”的断层

## 四、发现偏航时怎么处理

默认只做**最小纠偏**，不要顺手把正确答案全部喂进去。

示例：

```text
补充一下：刚才那条旧验证任务不是这轮主线，这轮主线是新开一门 IGCSE 学科并推进第一批。你自己判断现在该切到哪门学科、哪一批。
```

不要这样做：

- 直接替 manager 指定正确学科
- 直接替 manager 指定正确 batch
- 直接把 reviewer、worker、收口方式一次性都安排完

因为那样会遮住真实问题。

## 五、每轮结束必须记录

至少记录这几类 gap：

- manager 主线切换能力
- worker / review / auto_ops 的可见性
- task model 缺口
- manager 查询缺口
- publish / scanner / reassurance 边界问题
- taxonomy / action 不统一问题

## 六、什么时候才切换到兜底模式

只有在你已经确认：

- 当前不是在测 EduFlow Team 的理解和编排能力
- 而是在测更下游的执行链

才启用：

- 精确 batch 拆分
- 一键脚本
- 详细角色提示词
- 明确的 reviewer 指派与回收指令

否则默认继续用“模糊触发 + 最小纠偏 + gap note”。
