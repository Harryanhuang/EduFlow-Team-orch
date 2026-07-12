# EduFlow Production Topology Audit

## Verdict

**FAIL / BLOCKED** as of `2026-07-12T11:47:35+08:00`.

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
| router | `7193` | watchdog-supervised | **FAIL** — PID absent from process table; checkout, Python runtime, CLI runtime, and startup entry cannot be proven |
| task-publish | `30779` | watchdog-supervised | **FAIL** — PID absent from process table; checkout, Python runtime, CLI runtime, and startup entry cannot be proven |
| watchdog | `30780` | self-supervised | **FAIL** — PID absent from process table; checkout, Python runtime, CLI runtime, and startup entry cannot be proven |

These are dead/stale PID-file findings, not proof that the services are healthy
under another PID. G-1 must remain blocked until the daemon lifecycle is
reconciled and a subsequent audit correlates live PIDs with their exact startup
entries and runtimes.

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

ps -p 92686,92883,5260 -o pid=,ppid=,comm=
# 92686 92675 /Users/huanganan/.local/bin/claude
# 92883 92872 /Users/huanganan/.local/bin/claude
#  5260 92216 /Users/huanganan/.local/bin/claude

for pid in 92686 92883 5260; do lsof -a -p "$pid" -d cwd -Fn; done
# Each n-record: <production-checkout>

git -C "<production-checkout>" rev-parse --show-toplevel HEAD
# <production-checkout>
# bde14c5ce94aacd99ef80f9c11b65092dcf25fc3

shasum -a 256 "<production-checkout>/eduflow.toml"
# 00773fbb4eb5ed7f7f2cd5a2b416613229eda3880ffd0e506d8643ef9b8f9b74
```

An additional live pane, `EduFlowTeam:Hermes.0` (PID `92228`), reported cwd
`/Volumes/Halobster/Obsidian Edu`, not the audited production checkout. This is
an explicit `pane_cwd_drift` failure.

## Blocking findings

1. `daemon_pid_not_live`: router PID `7193`.
2. `daemon_pid_not_live`: task-publish PID `30779`.
3. `daemon_pid_not_live`: watchdog PID `30780`.
4. `pane_cwd_drift` and configured-entry mismatch: `EduFlowTeam:Hermes.0`.

The global scan also observed unrelated standalone CLI processes, but none had
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

Expected current result: JSON `ok=false`, exit code `1`. Re-run after runtime
reconciliation; do not manually change this verdict to PASS without preserving
the new JSON evidence and reviewer correlation.
