# EduFlow Production Topology Audit

## Task 2 verdict

**PASS** as of `2026-07-12T12:52:52+08:00` for the production-topology audit
task only: JSON `ok=true`, `errors=[]`, `suspect_processes=[]`, exit code `0`.

This is **not** a G-1 PASS or CLOSEOUT. Other G-1 tasks and the complete Gate
review remain independently required.

## Read-only freshness checkpoint — 2026-07-13T09:43:44+08:00

The topology audit was rerun from the isolated implementation worktree with
explicit production `--checkout`, `--config`, and `--state-dir` arguments.
It returned `ok: true`, zero errors, and zero suspect processes. All three
daemons and all eleven configured live Agent panes resolved to production
commit `bde14c5ce94aacd99ef80f9c11b65092dcf25fc3`, config generation
`edc3a3ac9b8f328e`, and the production state directory. The production
`health --json` refresh returned `ok: true`, `bad: 0`, `warn: 2`; strict
workflow validation passed for six active workflows. This is a point-in-time
read-only observation, not authority, scanner, REVIEW, or CLOSEOUT evidence.

This document is generated from a read-only correlation of git, the deployed
TOML file, PID files, `ps`, and tmux. It is not a declaration of intended
topology. The fresh audit proves this task's runtime topology; it does not make
claims about other G-1 acceptance artifacts.

## Audited deployment identity

| Fact | Observed value |
|---|---|
| Absolute checkout | `/Volumes/Halobster/Obsidian Edu/留学公司知识库/11-Eduflow Team 多智能体项目/EduFlow-Team-orch` |
| Commit SHA | `bde14c5ce94aacd99ef80f9c11b65092dcf25fc3` |
| Config path | `/Volumes/Halobster/Obsidian Edu/留学公司知识库/11-Eduflow Team 多智能体项目/EduFlow-Team-orch/eduflow.toml` |
| Config SHA256 | `edc3a3ac9b8f328eedcf30871c25f38cba8d53c997b872930b4671c02b3f042c` |
| Config generation | `edc3a3ac9b8f328e` |
| State directory | `/Volumes/Halobster/Obsidian Edu/留学公司知识库/11-Eduflow Team 多智能体项目/EduFlow-Team-orch/.eduflow-team-state` |
| Lark profile identifier | `eduflow-team` |
| tmux session | `EduFlowTeam` |

The audit emits identifiers and digests only. It does not emit config bodies,
environment values, credentials, tokens, or sensitive command arguments.

## Daemon correlation

| Daemon | PID file value | Supervision profile | Correlation result |
|---|---:|---|---|
| router | `12500` | watchdog-supervised | **PROVEN** — capital-`Python` kernel entry, Python `3.14.3`, root/config/state/generation and `bde14c5c…` correlate |
| task-publish | `72530` | watchdog-supervised | **PROVEN** — capital-`Python` kernel entry, Python `3.14.3`, root/config/state/generation and `bde14c5c…` correlate |
| watchdog | `72531` | self-supervised | **PROVEN** — capital-`Python` kernel entry, Python `3.14.3`, root/config/state/generation and `bde14c5c…` correlate |

All three PID-file values are live and match strict
`Python -m eduflow.cli <daemon>` entries. Their kernel executable is the same
absolute Homebrew Python 3.14.3 binary; each process independently proves
`EDUFLOW_ROOT`, config, state, generation, Lark profile, tmux session and Git
revision. No daemon fact is copied from the target arguments.

## Live pane manual correlation samples

The audit observed 11 configured-session panes and attempted child-process
correlation against `ps`. The three
required human-review samples are below. They are evidence placeholders for the
G-1 review record, not PASS assertions.

| Pane | tmux PID → CLI PID | Actual cwd / Git | Actual CLI | Correlation |
|---|---:|---|---|---|
| `EduFlowTeam:manager.0` | `92675 → 92686` | production checkout / `bde14c5c…` | `/Users/huanganan/.local/bin/claude 2.1.207` | **PROVEN**, ancestry `92686 → 92675 → 92216 → 1` |
| `EduFlowTeam:worker_course.0` | `92872 → 92883` | production checkout / `bde14c5c…` | `/Users/huanganan/.local/bin/claude 2.1.207` | **PROVEN**, ancestry `92883 → 92872 → 92216 → 1` |
| `EduFlowTeam:worker_review.0` | `5260 → 5260` | production checkout / `bde14c5c…` | `/Users/huanganan/.local/bin/claude 2.1.207` | **PROVEN**, ancestry `5260 → 92216 → 1` |
| `EduFlowTeam:Hermes.0` | `74424 → 74424` | duty cwd `/Volumes/Halobster/Obsidian Edu`; `EDUFLOW_ROOT` proves production checkout / `bde14c5c…` | Python `3.11.15`; `/Users/huanganan/.local/bin/hermes` package `0.16.0` | **PROVEN**, strict adjacent absolute wrapper, ancestry `74424 → 92216 → 1` |

For all three, the process environment independently resolved the config and
state paths shown above; the config content then proved generation
`edc3a3ac9b8f328e`, Lark profile `eduflow-team`, tmux session `EduFlowTeam`,
and configured `claude-code` runtime. Raw process environments and argv are
never written to JSON or this document.

### Independent, redacted commands and results

The following commands deliberately request identifiers only; none prints
process argv, environment values, config bodies, or credentials.

```bash
tmux list-panes -s -t EduFlowTeam \
  -F '#{session_name}:#{window_name}.#{pane_index}|#{pane_pid}|#{pane_current_path}|#{pane_current_command}'
# EduFlowTeam:manager.0|92675|<production-checkout>|2.1.207
# EduFlowTeam:worker_course.0|92872|<production-checkout>|2.1.207
# EduFlowTeam:worker_review.0|5260|<production-checkout>|2.1.207
# EduFlowTeam:Hermes.0|74424|/Volumes/Halobster/Obsidian Edu|python3.11

ps -p 92686,92883,5260 -o pid=,ppid=,comm=
# 92686 92675 /Users/huanganan/.local/bin/claude
# 92883 92872 /Users/huanganan/.local/bin/claude
#  5260 92216 /Users/huanganan/.local/bin/claude

ps -p 12500,72530,72531,74424 -o pid=,ppid=,comm=
# 12500 72531 <absolute Homebrew Python 3.14 executable>
# 72530     1 <absolute Homebrew Python 3.14 executable>
# 72531     1 <absolute Homebrew Python 3.14 executable>
# 74424 92216 /Users/huanganan/.hermes/hermes-agent/venv/bin/python3

for pid in 92686 92883 5260; do lsof -a -p "$pid" -d cwd -Fn; done
# Each n-record: <production-checkout>

for pid in 12500 72530 72531 74424; do lsof -a -p "$pid" -d cwd -Fn; done
# 12500/72530/72531 n-record: <production-checkout>
# 74424 n-record: /Volumes/Halobster/Obsidian Edu (recorded duty cwd)

git -C "<production-checkout>" rev-parse --show-toplevel HEAD
# <production-checkout>
# bde14c5ce94aacd99ef80f9c11b65092dcf25fc3

shasum -a 256 "<production-checkout>/eduflow.toml"
# edc3a3ac9b8f328eedcf30871c25f38cba8d53c997b872930b4671c02b3f042c
```

Hermes intentionally uses a duty cwd outside the checkout. Its actual process
environment proves `EDUFLOW_ROOT`, config and state all resolve to this audited
deployment, so the duty cwd is recorded as `process_cwd` and is not treated as
`pane_cwd_drift`. Package version is read as a single line through the actual
venv Python's `importlib.metadata`, never by accepting Hermes's multi-line
`--version` output. The same probe proves the venv `sysconfig` scripts path and
the distribution's `hermes` console entrypoint; the argv path
`/Users/huanganan/.local/bin/hermes` resolves to that exact
`scripts/hermes`, rather than merely sharing its basename.

## Reconciliation and fresh result

The production reconciliation used graceful termination for the confirmed
orphan while preserving the configured Hermes pane:

```bash
kill -TERM 98906
# orphan 98906: present -> absent
# configured Hermes: 74424 -> 74424 (preserved)
# router: 72529 -> 85686
# task-publish: 72530 -> 72530
# watchdog: 72531 -> 72531

python3 scripts/audit_production_topology.py --json \
  --checkout "<production-checkout>" \
  --config "<production-checkout>/eduflow.toml" \
  --state-dir "<production-checkout>/.eduflow-team-state"
# generated_at: 2026-07-12T12:52:52+08:00
# ok: true
# errors: []
# suspect_processes: []
# exit: 0
```

The earlier transient legacy PID `78495` and orphan PID `98906` are absent from
the fresh process scan. No topology blocking finding remains.

### All configured agent correlations

| Agent | Actual CLI PID | Configured pane | Runtime proof |
|---|---:|---|---|
| Hermes | `74424` | `EduFlowTeam:Hermes.0` | Hermes Agent `0.16.0` / Python `3.11.15` |
| Luke_recorder | `92362` | `EduFlowTeam:Luke_recorder.0` | Claude Code `2.1.207` |
| Monica | `92460` | `EduFlowTeam:Monica.0` | Claude Code `2.1.207` |
| Sophon | `32292` | `EduFlowTeam:Sophon.0` | Claude Code `2.1.207` |
| manager | `92686` | `EduFlowTeam:manager.0` | Claude Code `2.1.207` |
| worker_builder | `92774` | `EduFlowTeam:worker_builder.0` | Claude Code `2.1.207` |
| worker_course | `92883` | `EduFlowTeam:worker_course.0` | Claude Code `2.1.207` |
| worker_review | `5260` | `EduFlowTeam:worker_review.0` | Claude Code `2.1.207` |
| worker_school | `93092` | `EduFlowTeam:worker_school.0` | Claude Code `2.1.207` |
| worker_syllabus | `93695` | `EduFlowTeam:worker_syllabus.0` | Claude Code `2.1.207` |
| worker_teacher | `94169` | `EduFlowTeam:worker_teacher.0` | Claude Code `2.1.207` |

Fresh counts: `pane_count=11`, `agent_count=11`; every configured pane has one
strict actual CLI correlation and no extra scoped agent remains.

The global scan may also observe unrelated standalone CLI processes, but they
do not become findings unless they have
an EduFlow scope marker: their cwd/config/state did not match this deployment,
they were outside configured pane ancestry, and they were not explicit
`eduflow.cli agent` entries. They are therefore non-blocking and omitted from
`suspect_processes`; basename alone is not treated as ownership evidence.

No missing fact is inferred. Unknown runtime, checkout, revision, command,
config generation, or process correlation makes the machine-readable audit
`ok=false` and returns a non-zero exit status.

## Reproduction

Run from the implementation checkout:

```bash
python3 scripts/audit_production_topology.py \
  --checkout "/Volumes/Halobster/Obsidian Edu/留学公司知识库/11-Eduflow Team 多智能体项目/EduFlow-Team-orch" \
  --config "/Volumes/Halobster/Obsidian Edu/留学公司知识库/11-Eduflow Team 多智能体项目/EduFlow-Team-orch/eduflow.toml" \
  --state-dir "/Volumes/Halobster/Obsidian Edu/留学公司知识库/11-Eduflow Team 多智能体项目/EduFlow-Team-orch/.eduflow-team-state"
```

Expected current Task 2 result: JSON `ok=true`, exit code `0`, eleven correlated
configured agents, and no suspects/errors. A future runtime change must be
re-audited; this Task 2 result must not be presented as the whole G-1 verdict.
