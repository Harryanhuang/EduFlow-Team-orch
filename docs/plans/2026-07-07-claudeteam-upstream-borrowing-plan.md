# ClaudeTeam Upstream Borrowing Plan

Date: 2026-07-07

Source compared: `zylMozart/ClaudeTeam` current `main` plus sampled branches:

- `expert/taskflow-iso`
- `integration/team-control-taskflow-hirefix`
- `feat/team-control-commands`
- `feat/server-status-and-tmux`

EduFlow baseline: current local `EduFlow-Team-orch`, where the task model,
manager panel, review gate, runtime guard, memory, and education-production
workflow are already much heavier than upstream.

## Goal

Borrow the upstream ideas that improve operator visibility, runtime reliability,
and deployment safety without replacing EduFlow's existing task truth layer.

The main rule: upstream is a source of small proven operator surfaces, not a
new architecture to copy wholesale.

## CTO Quality Charter

Every upgrade must pass three lenses before implementation:

1. User lens: does this make the boss/operator's next action clearer?
2. Runtime lens: does this make the team more observable, recoverable, or safer?
3. Maintenance lens: does this reduce long-term confusion instead of adding
   another surface to remember?

An upgrade is not high quality just because tests pass. It is high quality only
when a real operator can use it under pressure without reading source code, and
when a future maintainer can tell which state is authoritative.

Default quality bar:

- one upgrade changes one behavior class only;
- read-only surfaces stay read-only;
- role boundaries are preserved;
- failure is visible, not silent;
- rollback path is named before code changes;
- verification includes command output or tests that exercise the operator
  surface, not only internal helpers.

## User Perspective

Primary users:

- Boss/operator: wants to know whether the team is alive, what is being worked
  on, who needs a decision, and whether output can be trusted.
- Manager agent: needs a clean route from incoming work to dispatch, review,
  evidence, and closeout.
- Worker agents: need unambiguous task ownership and no surprise state changes
  from display-only commands.
- Reviewer (`worker_review`): needs review ownership to stay separate from final
  manager closeout.
- Future maintainer: needs one source of truth per state and small diffs with
  clear tests.

User-quality questions for every proposed upgrade:

- What does the operator do faster after this?
- What confusing screen, command, or state does this remove or clarify?
- What wrong action does this prevent?
- What does the operator see when it fails?
- Does this preserve the REVIEW vs CLOSEOUT boundary?

If an upgrade cannot answer these questions, it should stay in research, not
implementation.

## Upgrade Quality Gates

Each implementation phase must have a short gate record before code changes:

- Problem: one sentence, user-facing.
- Borrowed idea: exact upstream behavior or principle being borrowed.
- EduFlow fit: why it belongs in EduFlow's current architecture.
- Non-goal: what we explicitly will not build.
- User acceptance: what the boss/operator can now do.
- Technical acceptance: tests, command checks, state invariants.
- Rollback: which files/flags revert it.
- Drift risk: what external behavior can invalidate it.

These gates keep the plan from becoming a feature wishlist.

## Upgrade Lanes

Use lanes to keep blast radius clear:

- Lane A: documentation and operator map. Lowest risk; can ship first.
- Lane B: read-only operator surfaces (`/task`, help text, dashboards). Low risk
  if no state mutation is added.
- Lane C: runtime classification (`/team` marker-free state). Medium risk; needs
  pane-state fixtures and latency checks.
- Lane D: router/catchup behavior. Medium/high risk; needs replay harness before
  production changes.
- Lane E: chat-driven lifecycle controls. High risk; default-deny and explicit
  approval only.

Do not mix lanes C/D/E with unrelated UI polish in the same upgrade.

## Current Finding

Upstream is simpler and more productized around a general ClaudeTeam runtime.
EduFlow is more specialized and already contains deeper task/review/workflow
logic. The useful borrowing direction is therefore:

- take small command surfaces that make operation easier;
- reuse marker-free runtime checks where they are more robust;
- keep EduFlow's task schema, review roles, evidence gates, and manager closeout
  boundaries intact;
- avoid adding a second task store or parallel lifecycle vocabulary.

## Productization and Remote-Control Parity Target

Parity with ClaudeTeam should not mean copying its command list. For EduFlow,
the product target is:

> The boss/operator can judge team state, advance work, detect risk, and recover
> the team from Feishu without knowing EduFlow's internal file/state layout.

EduFlow should reach that target by making its existing deeper production
capabilities easier to operate, not by adding a parallel generic team layer.

Required efforts:

1. One boss home surface.
   - Use `/home` as the boss/operator entrypoint.
   - Keep `/sophon` as the Sophon ops-watch entrypoint. `/home` may show only
     a minimal team-alive signal plus a route to `/sophon`; full runtime risk
     belongs to `/sophon`.
   - `/home` must not add a new aggregation layer. Every field needs a named
     existing source before implementation.
   - First `/home` version should show only team alive and boss decisions
     needed. Add task progress, review queue, and closeout queue only after the
     source-of-truth map is accepted.
2. Productized first-run and readiness path.
   - Turn setup into a checklist/wizard-like route before adding more runtime
     code.
   - Distinguish `health green` from `team ready`.
   - Require manager roll-call, pane auth readiness, and Feishu loop evidence
     before declaring the team usable.
3. Remote-control maturity levels.
   - Level 1 read-only: `/home`, `/sophon`, `/team`, `/task`, `/employees`,
     `/health`, `/tmux`.
   - Level 2 low-risk actions: wake, compact, stop, clear/reidentify, and
     manager dispatch helpers.
   - Level 3 high-risk actions: restart, shutdown, runtime switch, and login.
   - Level 3 remains default-deny, separately approved, audited, and reversible
     where possible.
4. Existing deep capabilities become product paths.
   - "Can this task close?" routes to the closeout lane.
   - "Can I trust this output?" routes to evidence readiness.
   - "Who should review?" routes to the REVIEW lane.
   - "Is the system broken?" routes to the runtime lane.
5. Reliability before remote power.
   - Catchup replay, router merge/dedup proof, and marker-free pane state should
     precede high-side-effect remote controls.
   - Each Feishu command needs the smallest operator-facing test that proves the
     claim it makes.

Non-goals:

- Do not create new CLI adapters in this cycle.
- Do not add `/login` until credential isolation and per-agent auth behavior are
  proven.
- Do not let `/task`, `/team`, `/sophon`, or the boss home imply approval or
  closeout.
- Do not add a new dashboard if one existing surface can be clarified.

## Evening Upgrade Queue

Park these for the next unified upgrade pass:

1. Documentation only: write the blocking maps before code.
   - `/home` source-of-truth map: field, existing source, forbidden duplicate
     source, owner surface.
   - `/sophon` boundary note: ops-watch only, no business conclusion, no
     closeout.
   - operator question map: "team alive", "what is happening", "who needs me",
     "what is blocked", "what can close".
2. Catchup mini-proof before any `/home` boss-decision lane.
   - Prove router restart plus same-minute REST history does not drop boss
     decisions.
   - Prove a missed websocket row is recovered or visibly marked missing.
   - Keep this limited to the `/home` boss-decisions-needed path; full catchup
     hardening stays later.
3. Minimal `/home`, read-only.
   - Show only team alive and boss decisions needed.
   - Reuse existing manager-panel/task query helpers; do not create a new read
     model or parse inbox ad hoc in slash code.
   - Do not show verdict and closeout in one visual lane.
4. `/sophon` and `/help` cleanup.
   - Add explicit `/sophon` scope wording.
   - Keep `/ops` and `/ops-dashboard` as hidden compatibility aliases only.
   - Put `/home`, `/sophon`, and `/task` first in help by operator question.
5. Hide renamed/archived roles from active operator views.
   - `auto_ops` remains historical/audit vocabulary only.
   - Active roster and help text should say `Sophon`.
   - Historical aliases can remain searchable, but not visible as current team
     members.
6. Expand only after the maps hold.
   - Add review queue and closeout queue after their sources are named.
   - Add `/task` attention colors only after every state has an SLA/color rule.
   - Add full runtime risk only in `/sophon`, not embedded in `/home`.
7. Upgrade by operator question, not by command inventory.
   - "What is happening now?" -> `/home`.
   - "Is the runtime healthy?" -> `/sophon` or `/health`.
   - "What task is where?" -> `/task`.
   - "Can this be trusted or closed?" -> REVIEW/CLOSEOUT lane.

Acceptance for the evening pass:

- `/help` points first to `/home` and `/sophon`, not legacy `/ops`.
- `/home` has a render assertion for team alive and boss decisions needed.
- `/sophon` has a scope note that it watches operations only.
- Default dashboard load has a timeout check or test proving it does not depend
  on the deep manager-action scanner.
- The REVIEW/CLOSEOUT boundary remains explicit: `worker_review` gives REVIEW,
  `manager` gives CLOSEOUT.

## Claude Code Package Execution Plan

Use this section as the execution handoff. Complete packages in order and stop
after each package for verification. Do not skip ahead to UI work before the
source map and catchup mini-proof are in place.

Global constraints:

- Do not add a CLI adapter, dependency, or second read model.
- Do not create a second task lifecycle or dashboard vocabulary.
- Keep `/home` read-only.
- Keep `/sophon` ops-watch only: no business conclusion, no closeout.
- Keep `worker_review` as REVIEW owner and `manager` as CLOSEOUT owner.
- Each package must end with `git diff --check` and the smallest relevant test
  command.

### Package 1: Source Maps Only

Goal: block duplicate facts before code exists.

Files:

- Modify: `docs/plans/2026-07-07-claudeteam-upstream-borrowing-plan.md`

Work:

- Add a `/home source-of-truth map` table with columns:
  - field;
  - existing source/helper/command;
  - forbidden duplicate source;
  - owner surface;
  - status: `now`, `later`, or `blocked`.
- Mark only these fields as first-version `now`:
  - `team_alive`;
  - `boss_decisions_needed`, only if an existing manager-facing source is
    named.
- Mark these fields as `later` until their sources are named:
  - review queue;
  - closeout queue;
  - task progress;
  - runtime risk.
- Add `/sophon` boundary wording: runtime risk belongs in `/sophon`; `/home`
  may show only alive/not alive plus a route to `/sophon`.
- Add operator question map:
  - "Is the team alive?";
  - "What is happening?";
  - "Who needs me?";
  - "What is blocked?";
  - "What can close?".

Forbidden:

- Do not implement `/home`.
- Do not parse inbox ad hoc from slash code.
- Do not add a new file just to hold this map.

Verification:

- `git diff --check`
- `rg -n "source-of-truth map|forbidden duplicate source|worker_review|CLOSEOUT" docs/plans/2026-07-07-claudeteam-upstream-borrowing-plan.md`

### Package 2: Catchup Mini-Proof

Goal: prove the boss-decision lane is not silently wrong after restart.

Files:

- Inspect: `src/eduflow/feishu/catchup.py`
- Inspect: `src/eduflow/feishu/subscribe.py`
- Inspect: `src/eduflow/feishu/router.py`
- Test: `tests/unit/test_feishu_catchup.py`
- Test: `tests/unit/test_feishu_router.py`

Work:

- Add the smallest replay tests for:
  - router restart plus same-minute REST history keeps the boss decision;
  - websocket miss plus catchup replay recovers the boss decision or makes the
    miss visible;
  - duplicate live plus catchup message id applies once.
- Fix only the shared router/catchup/subscribe path if a test fails.

Forbidden:

- Do not patch `/home` or slash handlers to compensate.
- Do not implement full catchup hardening here.
- Do not change fresh-deploy no-history behavior unless the test proves it is
  broken.

Verification:

- First run the new focused test and confirm it fails before implementation.
- After the fix:
  - `python3 -m pytest tests/unit/test_feishu_catchup.py tests/unit/test_feishu_router.py -q`
  - `git diff --check`

### Package 3: Minimal `/home`

Goal: ship the smallest boss homepage that cannot drift from existing truth.

Files:

- Modify: `src/eduflow/feishu/slash.py`
- Test: `tests/unit/test_feishu_slash.py`
- Touch shared helpers only if Package 1 names an existing owner and the helper
  already belongs there.

Work:

- `/home` renders only:
  - team alive;
  - boss decisions needed.
- If `boss_decisions_needed` has no stable existing helper, render a blocked
  source note instead of inventing one.
- Keep review queue, closeout queue, task progress, and runtime risk out of
  `/home` for this package.
- Keep verdict and closeout visually separate; do not show a combined progress
  lane.

Forbidden:

- Do not create `home_read_model.py` or similar.
- Do not add action buttons.
- Do not include closeout wording except as a route to manager-owned surfaces.

Verification:

- Add/adjust `/home` render tests for team alive and boss decisions needed.
- Add an assertion that `/home` does not imply approval or closeout.
- Run:
  - `python3 -m pytest tests/unit/test_feishu_slash.py -q`
  - `git diff --check`

### Package 4: `/sophon` Boundary and Help Order

Goal: make entrypoint roles obvious to the operator.

Files:

- Modify: `src/eduflow/feishu/slash.py`
- Test: `tests/unit/test_feishu_slash.py`
- Modify docs only if the UI wording changes the operator map.

Work:

- Add fixed `/sophon` wording:
  - "ops-watch only";
  - business conclusions go through manager;
  - closeout goes through manager flow.
- Reorder help by operator question:
  - `/home` boss homepage;
  - `/sophon` ops-watch;
  - `/task` task scan;
  - manager-panel/manager-owned path for decisions and evidence.
- Keep `/ops` and `/ops-dashboard` as hidden compatibility aliases only.

Forbidden:

- Do not change runtime behavior.
- Do not add Level 2 or Level 3 remote controls.

Verification:

- `python3 -m pytest tests/unit/test_feishu_slash.py -q`
- `git diff --check`

### Package 5: Final Gate

Goal: prove the narrow rollout did not blur state or ownership.

Run:

- `python3 -m pytest tests/unit/test_feishu_slash.py tests/unit/test_feishu_catchup.py tests/unit/test_feishu_router.py -q`
- If task helpers changed:
  - `python3 -m pytest tests/unit/test_commands_task.py -q`
- `git diff --check`

Final report must include:

- changed files;
- fields still marked `later` or `blocked`;
- whether a new source of truth was added. Expected answer: no;
- confirmation that REVIEW/CLOSEOUT ownership stayed unchanged;
- skipped items: review queue, closeout queue, runtime risk, and Level 2/3
  remote controls.

## Candidate Scorecard

Before approving a borrowed feature, score it on five axes:

| Axis | Good Signal | Bad Signal |
| --- | --- | --- |
| Operator clarity | Reduces steps or removes ambiguity | Adds another command with overlapping purpose |
| Runtime safety | Makes failures visible or recoverable | Hides failures behind a prettier card |
| State integrity | Reads from existing source of truth | Creates a second state vocabulary |
| Maintenance cost | Small, tested, local change | Depends on fast-moving external CLI behavior |
| Role boundary | Preserves manager/reviewer/worker duties | Lets status surfaces imply approval or closeout |

Decision rule:

- Ship now: strong operator clarity, low state risk, clear tests.
- Prototype first: runtime behavior change with uncertain live edge cases.
- Defer: useful but not on the critical operator path.
- Reject: creates parallel truth, weakens role boundaries, or needs ongoing
  maintenance without a clear owner.

Initial classification:

| Candidate | Decision | Reason |
| --- | --- | --- |
| Boss home / operator command center | Ship/prototype in Lane A/B | Needed to match upstream product clarity while using EduFlow's richer state |
| Lightweight task window | Ship/prototype in Lane B | Clear operator value, read-only if constrained |
| Marker-free `/team` | Prototype in Lane C | Better principle, but needs pane edge-case proof |
| Catchup hardening | Prototype in Lane D | High reliability value, must prove dedup path |
| Team control slash | Defer to Lane E | Useful but high side-effect risk |
| New CLI adapters | Reject for this cycle | Not a current bottleneck; maintenance heavy |
| Deployment checklist | Ship in Lane A | Low risk and directly improves user confidence |

## High-Value Borrowing Candidates

### 1. Lightweight Task Window

Upstream has `/task [all]`: a read-only Feishu card grouped by task status,
with terminal tasks folded by default.

Why it is useful:

- it gives the boss/operator a fast phone-readable task window;
- it does not mutate task state;
- it complements, rather than replaces, detailed manager views.

EduFlow adaptation:

- keep `manager-panel` as the decision/check/closeout surface;
- add or keep a separate lightweight task window for quick scanning;
- use EduFlow flow statuses (`assigned`, `in_progress`, `submitted_for_review`,
  `blocked`, `delivered`, `failed`, `cancelled`) instead of upstream's simpler
  `待处理 / 进行中 / 需审批 / 已完成 / 已取消`.

Priority: P1.

Risk: low, if kept read-only.

Acceptance:

- no task mutation;
- terminal rows folded by default;
- `all` expands terminal rows;
- attention color is deferred until every task state has an SLA/color rule.

### 2. Marker-Free Pane State

Upstream `pane_probe` judges pane state from:

- foreground process;
- pane output motion.

It avoids scraping volatile TUI strings. EduFlow already has similar logic in
`runtime/agent_reaper.py`, but `/team` still uses `feishu/pane_state.py` text
parsing.

EduFlow adaptation:

- do not import upstream `pane_probe` as a second implementation;
- extract or reuse the local marker-free probe path already present in
  `agent_reaper`;
- migrate `/team` to the marker-free classifier;
- keep lazy-agent and fired-agent special cases.

Priority: P1.

Risk: medium, because `/team` tests currently encode the old glyph behavior.

Acceptance:

- `/team` remains green for idle/busy/lazy/fired expected states;
- dead static shell panes still turn yellow;
- multi-agent probing does not add N x sleep latency;
- tests cover live config edits, lazy flags, no-window, dead shell, busy pane.

### 3. Router Catchup Hardening

Upstream catchup has several production-safety refinements:

- persist `create_time_ms` alongside rendered `create_time`;
- use a bounded lookback window so out-of-order missed messages are replayed;
- cap large catchup backlogs and seed cursor forward;
- replay same-minute messages oldest-first;
- warn when history fetch fails.

EduFlow already has `recent_window_lines`, so this should be merged carefully
instead of copied blindly.

Priority: P1.

Risk: medium. Catchup touches message replay, so false positives can duplicate
manager inbox rows if dedup is wrong.

Acceptance:

- fresh deploy still does not replay arbitrary history;
- restart gap messages are recovered;
- same-minute REST history does not get dropped because of cursor sub-minute
  precision;
- large backlog is capped loudly, never silently;
- router dedup is confirmed after catchup and recent-window backfill merge.

### 4. Team Control Slash Commands

Upstream includes chat-driven `/shutdown`, `/restart`, and `/login`, guarded by
explicit `[controls]` flags.

Value:

- useful for remote operations when shell access is inconvenient;
- especially helpful for restarting a team from Feishu.

EduFlow adaptation:

- do not enable by default;
- require explicit config flags;
- require confirmation for shutdown;
- never allow `/login` for CLIs whose credentials are not isolated per agent;
- write audit events before and after execution.

Priority: P2.

Risk: high if enabled casually.

Acceptance:

- default-deny;
- cross-chat guard remains in router;
- detached runner survives killing the router;
- completion notification is best-effort;
- tests prove disabled state, confirmation state, and allowed state.

### 5. CLI Adapter Expansion

Upstream has adapters for `opencode`, `openclaw`, `pi`, `trae`, `minimax`,
and `codewhale`.

Value:

- broadens provider options;
- many are OpenAI-compatible endpoint friendly;
- adapter files document hard-won launch details.

EduFlow adaptation:

- do not include new CLI adapters in the current upgrade route;
- keep upstream adapter implementations as references only;
- revisit only if a named CLI becomes an explicit production requirement.

Priority: out of scope for this plan.

Risk: medium to high. Adapters rot quickly when external CLIs change.

Acceptance:

- no adapter code is imported during this borrowing cycle;
- if revisited later, the proposal must name the concrete CLI, production use
  case, auth model, launch proof, and maintenance owner.

### 6. Deployment Verification Discipline

Upstream deployment docs emphasize that green infra health is not enough.
Operators must inspect each pane and verify that each CLI actually launched,
authenticated, consumed identity, and can answer in chat.

EduFlow adaptation:

- create or update an EduFlow operator checklist;
- distinguish infra health from team readiness;
- require pane evidence and group-message evidence before declaring success.

Priority: P2.

Risk: low.

Acceptance:

- checklist covers `health`, `/team`, `peek`, manager roll-call, worker inbox,
  and `say --to user`;
- checklist explicitly says not to trust pane existence alone.

## What Not To Borrow

Do not copy upstream's simpler task store into EduFlow.

Reasons:

- EduFlow already has flow-task schema v2, review gates, manager closeout,
  evidence account, publish gate, memory capsules, and workflow-specific
  semantics.
- A second status vocabulary would confuse manager/operator behavior.
- Upstream `需审批` maps only loosely to EduFlow's `blocked`,
  `manager_action`, and review verdict states.

Do not enable high-risk slash controls before a safety design review.

Do not add new CLI adapters unless there is a named CLI the user actually wants
to run in production.

## Suggested Execution Order

### Phase 0: Decision Record

Write a short accepted/rejected matrix for each borrowing candidate using the
Upgrade Quality Gates.

Output:

- this plan;
- a follow-up issue list or checklist.
- a one-page gate record before any Lane B/C/D/E implementation.

### Phase 1: Blocking Information Architecture

Before adding more surfaces, define the default operator route and the source of
truth for each future `/home` field. This phase is documentation only.

Deliverable:

- `/home source-of-truth map`;
- `/sophon` boundary note;
- operator question map;
- explicit `later` or `blocked` status for fields that do not yet have a stable
  existing source.

Definition of done:

- `/home` has named existing sources for its first-version fields;
- review queue, closeout queue, task progress, and runtime risk are not
  implemented until their sources are named;
- `/sophon` owns runtime risk;
- no new command or read model is introduced.

### Phase 2: Catchup Mini-Proof for `/home`

Before implementing a boss-decision lane, prove the router/catchup path will not
silently drop or duplicate boss decisions after restart.

Deliverable:

- focused replay tests for same-minute REST history, missed websocket row, and
  duplicate live/catchup message id;
- fixes only in the shared catchup/router/subscribe path if the tests fail.

Definition of done:

- the focused replay tests pass;
- fresh deploy no-history behavior is unchanged;
- `/home` and slash code are not used to compensate for router issues.

### Phase 3: Minimal Read-Only Operator Surface

Implement only the first safe `/home` and entrypoint wording.

Scope:

- `/home`: team alive plus boss decisions needed only;
- `/sophon`: ops-watch wording and existing fast ops snapshot;
- `/help`: grouped by operator question;
- `/task`: remain read-only; defer attention colors until SLA/color rules are
  written.

Definition of done:

- `/home` does not show review queue, closeout queue, task progress, or full
  runtime risk;
- `/home` has render tests for team alive and boss decisions needed;
- `/sophon` explicitly says it does not make business conclusions or close out
  work;
- `/ops` and `/ops-dashboard` remain compatibility aliases only.

### Phase 4: Runtime Reliability

Migrate `/team` to marker-free pane state using EduFlow's existing local
probe logic.

Verification:

- existing `/team` tests updated to process/motion semantics;
- latency does not scale linearly with agent count.

Definition of done:

- one test proves static shell is dead;
- one test proves moving shell is busy, not dead;
- one test proves lazy no-window/shell stays non-alarming;
- one test proves fired/retired agents are not confused with crashed agents.

### Phase 4B: Full Router Catchup Risk Burn-Down

After the `/home` mini-proof, do not treat upstream catchup as a simple copy.
Prove the full interaction between:

- `pending_lines`;
- `recent_window_lines`;
- router merge ordering;
- persisted seen ids;
- inbox append/read side effects.

This directly addresses the least-confident point in the reflection.

Deliverable:

- a replay matrix covering normal restart, websocket miss, same-minute REST
  history, cursor timezone shift, oversized backlog, and duplicate merge;
- a dry-run harness or focused tests that feed recorded/synthetic Feishu rows
  through the actual router merge path;
- a decision on whether catchup warnings should go to stderr only, manager inbox,
  or a Feishu card.

Implementation after proof:

- merge upstream catchup hardening with EduFlow's recent-window backfill;
- avoid double replay by proving dedup with actual event-line shape;
- keep fresh deploy no-history behavior.

Verification:

- cursor epoch-ms;
- lookback recovery;
- backlog cap;
- same-minute ordering;
- router merge/dedup behavior.

Definition of done:

- replay matrix has expected and observed results;
- every replayed row has a stable message id in the merge path;
- failure to fetch history is visible to logs or operator surface;
- no fresh deploy history replay regression.

### Phase 5: Productized Setup and Remote Control

Add deployment/readiness checklist.

Remote controls should be introduced by maturity level, not as a single feature
drop:

- Level 1: read-only remote observation is always available.
- Level 2: low-risk actions can be available when already supported locally.
- Level 3: restart, shutdown, runtime switch, and login require a separate
  safety design.

Only after readiness docs, boss home, `/team`, `/task`, and catchup proof are
stable should EduFlow decide whether `/shutdown`, `/restart`, or `/login` are
worth building.

Definition of done:

- checklist distinguishes infra health from team readiness;
- checklist requires pane evidence and chat evidence;
- lifecycle slash commands remain default-deny unless a separate safety design
  is approved.
- Level 3 controls write audit events and have a named rollback/shell fallback.

### Deferred: CLI Adapter Expansion

Do not implement new adapters in this cycle. The current EduFlow agent mix is
already broad enough, and adapter maintenance is not the bottleneck.

## Open Decisions

- Should the lightweight task window be named `/task`, `/tasks`, or folded into
  `/manager-overview`?
- Which fields belong on `/home` versus `/sophon` once the first shared
  dashboard version proves useful?
- Which remote controls belong in Level 2 for EduFlow: wake, compact, stop,
  clear, reidentify, dispatch, or runtime verify?
- Should `/team` expose only glyphs, or also show the raw classifier
  (`idle/busy/dead/no_window`) for debugging?
- Should catchup backlog caps notify manager inbox, stdout only, or Feishu card?
- Should team-control slash commands be supported in EduFlow at all, or kept as
  shell-only operations?
- New CLI adapters are explicitly out of scope unless a future production need
  names one.

## Cross-Cutting Safeguards

### Catchup Safety Gate

Any catchup change must pass through a replay-first gate before production
behavior changes.

Required cases:

- no cursor: no history replay;
- cursor with millisecond epoch: same-minute REST rows survive;
- cursor rendered under different timezone: persisted epoch wins;
- websocket missed a row before the cursor: bounded lookback recovers it;
- `recent_window_lines` and `pending_lines` return the same message: router
  applies it once;
- backlog over cap: newest bounded set replays, cursor moves forward, warning is
  visible;
- bot/user send_as mismatch: catchup failure is loud.

### Operator Map Gate

Any new command or card must declare which operator question it answers:

- team health;
- task state;
- decision needed;
- evidence/closeout;
- runtime recovery.

If it does not answer one of these, it should not be added.

### REVIEW vs CLOSEOUT Boundary Gate

Every borrowed or new feature must preserve this boundary:

- `worker_review` emits REVIEW verdicts;
- `manager` owns CLOSEOUT;
- `/task` and `/team` are read-only status surfaces;
- `/manager-panel` is the decision/evidence surface;
- no slash command should silently close out work unless it is explicitly a
  manager closeout command.

Acceptance:

- tests and docs use `worker_review`, not historical `review_course`, for new
  review/check work;
- closeout wording only appears on manager-owned paths;
- task windows do not imply approval or closeout.

### Drift Watch

The plan should assume external surfaces drift.

Monthly or release-triggered checks:

- run `/team`, `/task`, `/tmux manager`, `/review-queue`, `/manager-panel` in a
  real or near-real harness;
- verify pane classification after CLI upgrades;
- verify Feishu timestamp/catchup fixture shape against current lark-cli output;
- verify auth/login prompts do not change the operator checklist;
- record any CLI/TUI drift as a small compatibility note before changing code.

## Release Checklist

For each accepted upgrade, do not call it complete until all are true:

- User path: the operator-facing command or doc is easy to find.
- Evidence: tests or command output prove the exact operator claim.
- State: no new source of truth was added unless explicitly approved.
- Boundary: REVIEW and CLOSEOUT ownership remain unchanged.
- Failure mode: failure is visible and has a next action.
- Rollback: affected files and revert path are known.
- Scope: no unrelated refactor or adapter expansion is included.

## Rollout Strategy

Roll out in this order:

1. Documentation/operator map and `/home` source-of-truth map first.
2. Catchup mini-proof for the `/home` boss-decision lane.
3. Minimal read-only `/home`, `/sophon`, and `/help` wording.
4. Runtime classification only after the operator surfaces stop drifting.
5. Full catchup hardening after the mini-proof is stable.
6. High-side-effect controls only after separate approval.

Stop after each lane and review real operator friction before continuing. The
goal is not to finish the list; the goal is to make the next operational minute
clearer and safer.

## Reflection

### What am I least confident about right now?

I am least confident about the real production behavior of Feishu catchup under
EduFlow's current router merge path. Upstream's fix is well motivated, and
EduFlow has overlapping protection through `recent_window_lines`, but the exact
interaction between catchup, recent-window backfill, persisted seen ids, and
manager inbox side effects needs live or high-fidelity replay before I would
call it safe.

The second uncertainty is `/team` state classification. Marker-free probing is
more robust in principle, but EduFlow has OMX HUD pane handling, lazy residency,
runtime failover, and provider-specific panes. A naive swap could make the card
look cleaner while hiding an edge case the current text parser happens to catch.

Plan response:

- Phase 2 adds the minimal catchup proof needed before `/home` reads boss
  decisions.
- Phase 4B keeps the full catchup replay matrix before broader production
  behavior changes.
- Phase 4 requires `/team` tests for lazy, fired, no-window, dead shell, and busy
  pane states before migrating classification.

### What is my biggest omission? What might I not be noticing?

The biggest possible omission is user workflow shape. I compared code surfaces,
but the real value may not be any single command. It may be the way upstream
makes the operator journey simple: `/team`, `/task`, `/tmux`, `/health`, and
deployment docs form one mental model. EduFlow has more power, but may be harder
to operate because the views are split across manager-panel, ops-dashboard,
review-queue, supervisor-check, publish-run, and task commands.

So the hidden issue may be information architecture, not missing features.
Before adding more commands, we should decide the operator's default route:

- quick status;
- task state;
- decision needed;
- evidence/closeout;
- runtime recovery.

If that route is unclear, new features will make EduFlow feel richer but not
easier.

Plan response:

- Phase 1 is now operator information architecture, before more feature work.
- The Operator Map Gate blocks commands that do not answer a clear operator
  question.

### If this plan fails in three months, what is the most likely reason?

The most likely failure mode is drift from external CLIs and runtime behavior.
Claude/Codex/Kimi/Qwen style TUIs, auth flows, Feishu API output, and terminal
process behavior can change. A plan that looks correct by code comparison can
fail if it relies on today's prompt text, process names, login screens, or
message timestamp formats.

The second likely failure is over-borrowing. If EduFlow imports upstream features
without pruning them to its production workflow, it may gain more command
surface but lose role clarity. The specific danger is blurring:

- `worker_review` gives REVIEW verdicts;
- `manager` owns CLOSEOUT;
- task windows are read-only status surfaces;
- manager-panel is the decision/evidence surface.

If those boundaries blur, the system will look more capable while becoming less
trustworthy.

Plan response:

- The REVIEW vs CLOSEOUT Boundary Gate is now a cross-cutting safeguard.
- Drift Watch turns external CLI/Feishu/TUI changes into a recurring check
  instead of an implicit hope.

## Lane A: Source-of-truth Map (Package 1 deliverable)

This section pins each `/home` (and adjacent operator surface) field to a
named existing source. No `/home` field may be added before its row exists
here. A field whose row is `blocked` may NOT be rendered with a temp
parser; the card must show the explicit "source-of-truth map blocked"
note until a stable helper is named.

### /home source-of-truth map

| field | existing source/helper/command | forbidden duplicate source | owner surface | status |
| --- | --- | --- | --- | --- |
| `team_alive` | reuse the existing `/team` snapshot helper — `eduflow.feishu.slash._live_agents()` reads live config + `pane_state.parse()` + `local_facts.get_status()`; for fast path, the `eduflow task ops-dashboard --json` payload's `summary` + `residency` block (built by `_build_ops_dashboard` in `commands/task.py`) already aggregates agent alive/not-alive state | do NOT parse chat inbox ad hoc from `/home`; do NOT call `tmux.capture_pane` directly from `/home` without going through `_live_agents` | `/home` (read-only) | `now` |
| `boss_decisions_needed` | the existing `eduflow.store.tasks.manager_overview()` helper, specifically its `manager_action` bucket (filtered: `status="blocked" AND needs_manager_action=True`); supervisor-style enrichment via `task_event_scanner.scan_manager_anomalies()` finding category `manager_action_pending` / `manager_action_overdue` — both are already wired into `commands/task.py` `_cmd_manager_overview` and `_cmd_manager_actions` | do NOT re-parse inbox from slash code; do NOT introduce a new `home_decisions.py` read model; do NOT compose a "decisions" row from raw task rows in `slash.py` | `/home` (read-only) → `/manager-panel` for apply | `now` |
| `review queue` | existing `tasks.list_review_queue()` + `scan_manager_anomalies()` `safe_task_review_approve` packets; surfaced today by `/review-queue` and `manager-panel` | do NOT re-implement review-queue selection in `slash.py` | `/task` (later) | `later` |
| `closeout queue` | existing `tasks.subject_closeout_status()` `closeout_ready` rows + `tasks.manager_overview()` `subject_closeout` bucket; surfaced today by `manager-panel` "Subject Closeout" section | do NOT compute closeout readiness in `slash.py`; do NOT show a unified "review + closeout" progress bar — verdict and closeout must stay as separate fields, NOT one visual lane | `/manager-panel` only | `later` |
| `task progress` | existing `tasks.manager_overview()` `in_progress` / `awaiting_review` buckets; surfaced today by `/manager-overview` | do NOT surface aggregated task progress on `/home` for v1; attention color is deferred until every state has an SLA/color rule (still TODO) | `/task` (later) | `later` |
| `runtime risk` | existing `task_event_scanner.scan_manager_anomalies()` (`worker_context_exhausted`, `worker_high_priority_unacked_while_producing`, `stale_status_surface`, etc.) + `runtime/agent_reaper.py` recovery findings; surfaced today by `manager-panel` "Context Guard Blockers" and `/health` | do NOT embed full runtime risk in `/home`; `/home` may show ONLY alive/not alive + a route to `/sophon` | `/sophon` (ops-watch) | `later` |

### /sophon boundary wording

- `/sophon` is ops-watch only.
- It shows runtime health, residency, context guard, and recovery signals.
- It MUST NOT make business conclusions ("ship this subject", "approve
  this batch").
- It MUST NOT closeout work. CLOSEOUT goes through manager flow
  (`worker_review` emits REVIEW; `manager` owns CLOSEOUT).
- Full runtime risk lives in `/sophon`, not in `/home`. `/home` may show
  alive/not-alive plus a single link to `/sophon`.

### Operator question map

| operator question | entrypoint | reads from |
| --- | --- | --- |
| "Is the team alive?" | `/home` | `manager_overview()` residency + `_live_agents()` |
| "What is happening?" | `/home` (later) / `/task` | `manager_overview()` buckets (later) |
| "Who needs me?" | `/home` | `manager_overview()` `manager_action` + `scan_manager_anomalies()` `manager_action_pending/overdue` |
| "What is blocked?" | `/manager-panel` | `manager_overview()` `blocked` + `manager-action` packets |
| "What can close?" | `/manager-panel` | `subject_closeout_status()` `closeout_ready` rows |
| "Is the runtime healthy?" | `/sophon` / `/health` | `agent_reaper` + `scan_manager_anomalies()` context-guard |

### Forbidden duplicate source guard

For every `/home` field the rule is: **a second parallel parser is
forbidden**. If a future contributor cannot reuse the existing helper
because of a shape mismatch, the fix is to update the existing helper
or extend it, NOT to write a new `home_*.py` module. `/home` may only
call into `eduflow.store.tasks.manager_overview`,
`eduflow.store.task_event_scanner.scan_manager_anomalies`, or the
already-existing team snapshot path used by `/team` and `/employees`.

### REVIEW vs CLOSEOUT boundary preserved

- `worker_review` is the REVIEW verdict owner. Surface it as a worker
  in the team roster but never as the source of closeout decisions.
- `manager` is the CLOSEOUT owner. CLOSEOUT action wording only appears
  on manager-owned surfaces (`/manager-panel`,
  `eduflow task manager-closeout`, `eduflow task manager-action-apply`).
- `/home` never implies approval or closeout. It routes the operator to
  the right manager surface.
- New review/check code uses `worker_review`, not historical
  `review_course`, per the agent rename gate.

### Later / blocked status tracker

After Package 1 lands, the open rows are:

| field | status | next step |
| --- | --- | --- |
| `review queue` | `later` | needs SLA + color rule, then `/task` add |
| `closeout queue` | `later` | belongs on `/manager-panel`; not on `/home` |
| `task progress` | `later` | needs SLA + color rule; `/task` add |
| `runtime risk` | `later` | full risk belongs on `/sophon`; `/home` only links |
| `/task` attention color | `later` | wait for SLA/color rule across every state |
| boss-decision Lane B/C/D/E | `later` | after catchup mini-proof + marker-free `/team` |
