# Multi-team switch via `eduflow switch`

## 场景

操作员同时管两个 EduFlow 部署 —— 例如 `~/teams/projectA` 和
`~/teams/projectB`，每个目录里有自己的 `team.json` +
`runtime_config.json`，互不干扰。希望在同一台机器上、不同 shell 会话之间
快速切换"当前 active team"。

## 范围

- 类型：local-only （纯 shell + 本地文件，不碰 tmux/Feishu）
- 凭证：无
- 操作员：boss / 任一开发者

## Given

```
~/teams/projectA/
    team.json              # session=ProjectA, agents=...
    runtime_config.json    # chat_id=oc_xxx, lark_profile=projectA
~/teams/projectB/
    team.json              # session=ProjectB, agents=...
    runtime_config.json    # chat_id=oc_yyy, lark_profile=projectB
```

`eduflow` 已通过 pip install -e . 安装在当前 shell 的 PATH。

## When

```bash
# Show what's currently active (no env vars set → defaults)
eduflow switch

# Apply projectA's env to the current shell
eval "$(eduflow switch ~/teams/projectA)"

# Verify the switch
eduflow switch
eduflow health        # state_dir / team.json / runtime_config 都对得上 projectA

# Switch to projectB in a different terminal
eval "$(eduflow switch ~/teams/projectB)"
eduflow health        # 现在指 projectB
```

## Then

无参 `eduflow switch` 输出三行：

```
state_dir:      /home/x/teams/projectA/state
team_file:      /home/x/teams/projectA/team.json
runtime_config: /home/x/teams/projectA/runtime_config.json
```

或在尚未 eval 任何 export 时：

```
state_dir:      (default) /home/x/.eduflow
team_file:      (default) /home/x/team.json
runtime_config: (default) /home/x/runtime_config.json
```

带参 `eduflow switch <dir>` 输出三行 export + 注释行（不 eval 不会改变环境）：

```
export EDUFLOW_STATE_DIR='/home/x/teams/projectA/state'
export EDUFLOW_TEAM_FILE='/home/x/teams/projectA/team.json'
export EDUFLOW_RUNTIME_CONFIG='/home/x/teams/projectA/runtime_config.json'
# Active team: /home/x/teams/projectA
# Apply with: eval "$(eduflow switch /home/x/teams/projectA)"
```

错误路径：

- `eduflow switch /tmp/no-such-dir` → exit 1, stderr `❌ ... does not exist`
- `eduflow switch /tmp/empty` (无 team.json) → exit 1, stderr 提示 `team.json
  not found`，并建议先 `eduflow init` 在该目录里 bootstrap

## Why this is here

多 team 隔离一直是 env-var 驱动 (`EDUFLOW_STATE_DIR`,
`EDUFLOW_TEAM_FILE`, `EDUFLOW_RUNTIME_CONFIG` 三个一组)，操作员手工
export 三遍既容易打错也容易漏掉一项。`eduflow switch` 把"指向某个团队
目录"封装成一行命令，配上 shell `eval` 一句就生效。

不引入持久 active-team 状态文件，是因为多个 shell 平行运行不同 team 的需求
真实存在 —— 任何全局 active flag 都会被并发用法打破。env-var 一进程一份，
每个 shell 自己持有，跨 shell 互不影响。
