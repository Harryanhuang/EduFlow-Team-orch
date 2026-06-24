# Phase 5 8-Agent Real-Run Gap Note (2026-06-18)

## Run scope

- repo: `EduFlow-Team-orch`
- chat: `EduFlow Team 8-Agent Validation`
- bot profile: `eduflow-team`
- active 8 agents:
  - `manager`
  - `worker_course`
  - `review_course`
  - `auto_ops`
  - `worker_builder`
  - `worker_qbank`
  - `hermes`
  - `anna`

## What proved stable

1. New isolation is real enough to run
   - new Feishu group, new bot profile, new repo config, new isolated state dir all worked together
   - tmux window names and active status rows stayed on new agent names

2. Main course-line task loop is basically valid
   - `manager -> worker_course -> review_course -> manager` was exercised through the task store path
   - `manager-panel` correctly collapsed the final result into a manager-facing summary

3. Formal result still stays with manager
   - final publish to the validation group came from `manager`
   - worker reassurance did not override manager's formal result lane

## Gaps found

### 1. Naming residue gap

- active runtime path was clean after the isolated state reset
- but older state and older docs still contain `curriculum` naming
- concrete evidence:
  - task stage enum still uses `curriculum`, not `course`
  - real run had to use `--stage curriculum`

Meaning:

- agent display names are mostly cleaned up
- domain taxonomy is not fully renamed yet

### 2. Broadcast boundary gap

- worker reassurance is currently too binary:
  - task-store-driven reassurance can be selected by publish logic
  - but `chat.publish.worker_to_user = false` suppresses it at send time
- concrete evidence:
  - `task publish-run --send` selected reassurance rows
  - actual send logs showed `worker_course -> silenced by [chat.publish.worker_to_user]=false`

Meaning:

- the system can decide "this reassurance is worth sending"
- but the final chat policy still collapses all worker-to-user updates into silence

### 3. Worker acceptance visibility gap

- this is the most important new gap from the real run
- `worker_course` received a new manager task and eventually consumed it
- but there was no clean user-visible "已收到，正在处理" style reassurance at the moment of acceptance
- concrete evidence:
  - the pane showed the injected task notice
  - unread inbox later cleared
  - the pane said it would draft the outline and report back
  - but the user did not get a lightweight visible acceptance update from `worker_course`

Meaning:

- current system sits in an awkward middle state:
  - not silent enough to feel intentionally manager-only
  - not expressive enough to provide the reassurance the user wants

Recommended shape:

- allow one lightweight worker acceptance reassurance when:
  - task is freshly accepted
  - there is no manager formal result yet
  - it is the first reassurance for that task in the current short window

### 4. Manager dispatch / worker consumption gap

- `worker_course` did not ignore the task
- but its inbox consumption was delayed and not instantly deterministic
- concrete evidence:
  - after `send`, pane first showed the injected reminder
  - inbox still showed `1 unread`
  - later the pane reported it would draft the outline and message consumption completed

Meaning:

- inject works
- consume loop is still timing-sensitive

### 5. Side-lane wake gap (`hermes` / `anna`)

- lazy wake path originally missed runtime `env_profile`
- that bug was fixed in `src/eduflow/commands/send.py`
- focused regression test was added in `tests/unit/test_commands_messaging.py`
- after the fix, `hermes` and `anna` did inherit the Qwen Anthropic-compatible env vars
- but both still failed at Claude Code startup with outbound Anthropic connection / certificate errors

Meaning:

- the orchestration bug was real and now fixed
- a deeper runtime/provider issue still blocks reliable real-run validation for those two lazy `claude-code` lanes

### 6. Review semantics gap

- the validation approve path used `review_reason=quality_not_met`
- that reason is semantically awkward when the review outcome is actually approve

Meaning:

- taxonomy exists
- but recommended review reasons still need tighter outcome alignment

## Judgment

Current state is good enough to say:

- naming isolation: mostly yes
- new bot isolation: yes
- manager formal result lane: yes
- worker reassurance lane: partially
- side-lane lazy wake reliability: not yet

So this run does **not** justify calling the 8-agent validation fully stable.

It **does** justify the next step becoming narrower and clearer:

## Recommended next phase

### Phase 5A

Make worker reassurance intentional instead of binary silence.

Focus:

1. one visible acceptance reassurance for `worker_*`
2. one visible "handed to manager" reassurance only when it helps
3. keep manager as sole formal result speaker

### Phase 5B

Stabilize lazy `claude-code` lanes under the chosen provider path.

Focus:

1. `hermes` and `anna` must wake without OAuth fallback
2. `hermes` and `anna` must not hit direct Anthropic startup failure when the runtime is meant to use the compatible gateway
3. after that, re-run the same short validation loop

## Files directly involved in this run

- `eduflow.toml`
- `src/eduflow/commands/send.py`
- `tests/unit/test_commands_messaging.py`

