# Residency Config — Operator Regression Playbook

> 配套方案: 留学公司知识库/11-Eduflow Team 多智能体项目/2026-07-01 EduFlow 群聊外显与温备驻留方案 v0.1 §设计二
> 实现: `src/eduflow/runtime/residency.py` + `src/eduflow/runtime/config.py` residency loaders + `src/eduflow/commands/team.py` residency 列
> 验收覆盖: `tests/unit/test_residency.py` (21 tests)
> 注意: Phase 2 **只做配置侧**（schema + loader + 显示）。真正的 idle→sleep / wake 收回在 Phase 3。

## Pre-conditions

- 仓库切到 `feat/2026-07-01-residency-phase1` 分支
- `eduflow.toml` 已有 `[team.residency]` 块（本次 Phase 2 新增）
- 9-agent 团队配置存在

## Step 1 — 确认 residency 配置被正确解析

```bash
python3 - <<'PY'
import sys; sys.path.insert(0, 'src')
from eduflow.runtime import config
print('resident agents:', config.load_resident_agents())
for a in ['manager','auto_ops','Luke_recorder','worker_course','review_course',
          'worker_builder','worker_qbank','Hermes','worker_syllabus']:
    p = config.load_residency_policy(a)
    print(f'  {a}: mode={p.mode} idle={p.idle_timeout_s}s handoff={p.handoff_buffer_s}s wake={p.wake_timeout_s}s src={p.source}')
PY
```

**预期:**
- `resident agents: ('manager', 'auto_ops', 'Luke_recorder')`
- manager / auto_ops / Luke_recorder → `mode=resident`
- worker_course / review_course / worker_builder / worker_qbank / Hermes → `mode=warm idle=600`
- worker_syllabus → `mode=warm idle=300 src=agent_override`

## Step 2 — `/team` 面板显示 residency 列

```bash
# 起团队后（或先 seed 几条状态）
eduflow team
```

**预期:** 每行格式为 `name  [常驻|温备]  status  task ...`；
manager 行显示 `常驻`，worker_course 行显示 `温备`。

```bash
eduflow team --json | python3 -m json.tool | head -30
```

**预期:** 每条记录含 `"residency": "常驻"` 或 `"温备"`；旧字段
`status/task/blocker/updated_at_ms/heartbeat_ms` 全部保留（向后兼容）。

## Step 3 — per-agent override 生效

```bash
# worker_syllabus 用 300s idle（比默认 600s 短）
python3 - <<'PY'
import sys; sys.path.insert(0, 'src')
from eduflow.runtime import config
p = config.load_residency_policy('worker_syllabus')
assert p.idle_timeout_s == 300, p.idle_timeout_s
assert p.source == 'agent_override'
print('OK: worker_syllabus idle=300 via per-agent override')
PY
```

## Step 4 — 容错：坏配置不崩溃

```bash
# 临时把 resident_agents 写一个不存在的 agent，确认被过滤
# （用一个临时 toml 验证，不改真实配置）
python3 - <<'PY'
import sys, tempfile, os
sys.path.insert(0, 'src')
# 用临时 state dir 隔离
os.environ['EDUFLOW_CONFIG_FILE'] = '/tmp/eduflow_test.toml'
with open('/tmp/eduflow_test.toml','w') as f:
    f.write('''
[team]
session="X"
[team.residency]
resident_agents=["manager","ghost"]
[team.agents.manager]
cli="claude-code"
''')
# 注意：真实校验以 test_residency.py::test_resident_agents_list_filters_unknown_names 为准
print('见 unit test: 未知 agent 名被过滤')
PY
```

**预期:** 未知 agent 名（ghost）被 `load_resident_agents` 过滤掉，
`/team` 不因坏配置崩溃（degrade 到 `未配置`）。

## 通过条件

- Step 1: 9 个 agent 的 mode/idle/handoff/wake/source 与预期完全一致
- Step 2: `/team` 文本和 JSON 都显示 residency，JSON 向后兼容
- Step 3: worker_syllabus 的 per-agent override 生效
- Step 4: 坏配置被过滤，不崩溃

## 关联文件

- 方案: `2026-07-01 EduFlow 群聊外显与温备驻留方案 v0.1.md` §设计二
- 审计: `docs/plans/2026-07-01-phase0-residency-audit.md`
- residency 模块: `src/eduflow/runtime/residency.py`
- config loader: `src/eduflow/runtime/config.py`（`load_residency_policy` / `load_resident_agents`）
- 配置块: `eduflow.toml` `[team.residency]` + `[team.agents.worker_syllabus.residency]`
- 面板: `src/eduflow/commands/team.py`
- 单元测试: `tests/unit/test_residency.py` (21 tests)

## 下一阶段（Phase 3 预告）

本 Phase 只落配置。Phase 3 会加：
- `sleep_if_idle(agent)`：warm agent 无 active task + 无 unread inbox + 超 idle timeout → graceful exit CLI，保 pane
- `wake(agent)`：复用 `wake_if_dormant`，温备 agent 被派单时自动唤醒
- 周期 sweep：auto_ops / runtime_guard 调用，把 idle warm agent 收回
- `local_facts` 增加 `温备` 状态字面量
