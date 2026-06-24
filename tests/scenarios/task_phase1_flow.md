# Phase 1 Task Flow Smoke

## 目的

验证 EduFlow team 当前任务系统已经收口为可用的 Phase 1 基线：

- flow task 通过动作化命令推进
- review 路径可闭环
- manager action 与普通 blocked 可区分
- 事件流按状态变化稳定写入

## 适用范围

只验证任务内核与事件真相：

- `eduflow task dispatch`
- `eduflow task flow-transition`
- `eduflow task submit-review`
- `eduflow task assign-reviewer`
- `eduflow task review`
- `eduflow task manager-overview`

不验证：

- Feishu 群消息投递效果
- task publish daemon 长时运行
- scanner 自动升级策略

## 前置条件

1. 已在目标环境完成 `eduflow init`
2. `EDUFLOW_STATE_DIR` 指向一份干净状态目录
3. 可直接运行本地 CLI

## 操作

1. 派一个课程线 flow task：

   ```bash
   eduflow task dispatch worker_course "Draft Unit 1 outline" \
     --stage curriculum \
     --owner worker_course \
     --by manager
   ```

2. 推进到执行中：

   ```bash
   eduflow task flow-transition T-1 --to in_progress --actor worker_course
   ```

3. 指派 reviewer：

   ```bash
   eduflow task assign-reviewer T-1 --reviewer reviewer_amy --by manager
   ```

4. 提交审核：

   ```bash
   eduflow task submit-review T-1 --actor worker_course
   ```

5. 走一遍 reject 路径，再次提交：

   ```bash
   eduflow task review T-1 --actor reviewer_amy --reject
   eduflow task submit-review T-1 --actor worker_course
   ```

6. 再走一遍 manager action 路径：

   ```bash
   eduflow task review T-1 --actor reviewer_amy --manager-action
   eduflow task manager-overview
   ```

7. 新建第二个 flow task，直接走 approve/交付闭环：

   ```bash
   eduflow task dispatch worker_course "Draft Unit 2 outline" \
     --stage curriculum \
     --owner worker_course \
     --by manager
   eduflow task flow-transition T-2 --to in_progress --actor worker_course
   eduflow task assign-reviewer T-2 --reviewer reviewer_amy --by manager
   eduflow task submit-review T-2 --actor worker_course
   eduflow task review T-2 --actor reviewer_amy --approve
   ```

8. 查看任务与事件：

   ```bash
   eduflow task get T-1
   eduflow task get T-2
   ```

   然后直接查看状态目录下的 `task-events.jsonl`。

## 期望

1. `T-1` 在 manager action 路径下：
   - `status = blocked`
   - `verdict = manager_action`
   - `needs_manager_action = true`
   - `blocking_reason` 非空

2. `manager-overview` 中：
   - `manager_action` 至少有 1 条
   - 普通 `blocked` 与 `manager_action` 分桶分开

3. `T-2` 在 approve 路径下：
   - `status = delivered`
   - `verdict = approved`
   - `completed_at` 非空

4. `task-events.jsonl` 中：
   - 每次有效状态变化都有新事件
   - reviewer 指派有单独事件
   - 事件里能看到 `from_status / to_status`
   - 事件里能看到 `meaningful_changes`

## 失败排查

1. 若 `task update` 还能修改 flow task，说明 Phase 1 边界没收紧。
2. 若 `manager_action` 没把任务留在 `blocked`，说明 review 结果映射有误。
3. 若事件流只有 `before/after` 没有标准字段，说明事件真相还没收口。
4. 若 `manager-overview` 把所有 blocked 混在一起，说明 manager action 语义没有落到查询层。

## 不在范围

- 群消息该不该发、什么时候发
- publish cursor 推进策略
- scanner 定时轮询与去重
- n8n / 外部编排接口
