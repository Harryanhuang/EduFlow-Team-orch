# EduFlow Production Topology Audit

## Verdict

**FAIL / BLOCKED** as of `2026-07-12T12:45:08+08:00`.

This document is generated from a read-only correlation of git, the deployed
TOML file, PID files, `ps`, and tmux. It is not a declaration of intended
topology. The audit returned exit code `1`; production truth is not sufficiently
correlated to satisfy G-1.

## Audited deployment identity

| Fact | Observed value |
|---|---|
| Absolute checkout | `/Volumes/Halobster/Obsidian Edu/留学公司知识库/11-Eduflow Team 多智能体项目/EduFlow-Team-orch` |
| Commit SHA | `bde14c5ce94aacd99ef80f9c11b65092dcf25fc3` |
| Config path | `/Volumes/Halobster/Obsidian Edu/留学公司知识库/11-Eduflow Team 多智能体项目/EduFlow-Team-orch/eduflow.toml` |
| Config SHA256 | `00773fbb4eb5ed7f7f2cd5a2b416613229eda3880ffd0e506d8643ef9b8f9b74` |
| Config generation | `00773fbb4eb5ed7f` |
| State directory | `/Volumes/Halobster/Obsidian Edu/留学公司知识库/11-Eduflow Team 多智能体项目/EduFlow-Team-orch/.eduflow-team-state` |
| Lark profile identifier | `eduflow-team` |
| tmux session | `EduFlowTeam` |

The audit emits identifiers and digests only. It does not emit config bodies,
environment values, credentials, tokens, or sensitive command arguments.

## Daemon correlation

| Daemon | PID file value | Supervision profile | Correlation result |
|---|---:|---|---|
| router | `72529` | watchdog-supervised | **PROVEN** — capital-`Python` kernel entry, Python `3.14.3`, root/config/state/generation and `bde14c5c…` correlate |
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
`00773fbb4eb5ed7f`, Lark profile `eduflow-team`, tmux session `EduFlowTeam`,
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

ps -p 72529,72530,72531,74424 -o pid=,ppid=,comm=
# 72529     1 <absolute Homebrew Python 3.14 executable>
# 72530     1 <absolute Homebrew Python 3.14 executable>
# 72531     1 <absolute Homebrew Python 3.14 executable>
# 74424 92216 /Users/huanganan/.hermes/hermes-agent/venv/bin/python3

for pid in 92686 92883 5260; do lsof -a -p "$pid" -d cwd -Fn; done
# Each n-record: <production-checkout>

for pid in 72529 72530 72531 74424; do lsof -a -p "$pid" -d cwd -Fn; done
# 72529/72530/72531 n-record: <production-checkout>
# 74424 n-record: /Volumes/Halobster/Obsidian Edu (recorded duty cwd)

git -C "<production-checkout>" rev-parse --show-toplevel HEAD
# <production-checkout>
# bde14c5ce94aacd99ef80f9c11b65092dcf25fc3

shasum -a 256 "<production-checkout>/eduflow.toml"
# 00773fbb4eb5ed7f7f2cd5a2b416613229eda3880ffd0e506d8643ef9b8f9b74
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

## Blocking findings

1. `orphan_agent`: PID `98906`, a strict Python/Hermes wrapper with EduFlow
   scope evidence, is not associated with a configured tmux pane. Its exact
   argv and environment remain redacted.

The earlier transient legacy PID `78495` is no longer present in the
`12:36:21+08:00` audit and therefore is not carried forward as a live finding.

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

Expected current result: JSON `ok=false`, exit code `1`. Daemon and configured
Hermes reconciliation now pass; the globally detected unassociated Hermes
process keeps G-1 blocked. Re-run after it is owned or removed;
do not manually change this verdict without preserving new JSON evidence.
