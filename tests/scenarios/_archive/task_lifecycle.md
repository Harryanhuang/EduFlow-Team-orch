# Task lifecycle: create → assign → progress → done

## 场景
团队任务卡片：create 派给 agent，update 状态推进，done 标完。验证 `eduflow task` 五个 subcommand 在端到端流程中可用。完全本地 (state_dir/tasks.json)，不碰飞书。

## 范围
- 类型：host-only
- 凭证：none

## Given
- export `EDUFLOW_STATE_DIR=$PWD/state`
- 该目录下没有 `state/tasks.json`

## When

```bash
eduflow task create alice "Fix login bug" --by manager --desc "users can't log in"
eduflow task list
eduflow task update T-1 --status 进行中
eduflow task get T-1
eduflow task list --status 进行中
eduflow task done T-1
eduflow task list
eduflow task list --status 已完成
```

## Then

1. **create** 退出 0，stdout 含 `created T-1: Fix login bug → alice`
2. **list**（无 filter） 退出 0，stdout 含 `1 tasks` 和 `T-1  [待处理]  Fix login bug`
3. **update T-1 --status 进行中** 退出 0，stdout 含 `updated T-1`
4. **get T-1** 退出 0，stdout 含 `T-1`、`assignee: alice`、`by: manager`、`desc: users can't log in`、`[进行中]`
5. **list --status 进行中** 列出 T-1
6. **done T-1** 退出 0；`tasks.json` 中 T-1 的 `status == 已完成`，`completed_at` 非 null
7. **list**（无 filter） 仍列出 T-1（terminal 任务也显示）
8. **list --status 已完成** 列出 T-1
9. **list --status 进行中** 此时为空

## 反例
- `eduflow task update T-99 --status 已完成` → 退出 1，stderr 含 `no such task`
- `eduflow task update T-1 --status bogus` → 退出 1，stderr 含 `invalid status`

## 证据（执行时填）

```
- T_create: …
- T_done: …
- 结果: pass | fail
- 后续: …
```
