# EduFlow Production Topology Audit

## Verdict

**FAIL / BLOCKED** as of `2026-07-12T11:00:03+08:00`.

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

The audit observed 11 panes and correlated each pane PID against `ps`. The three
required human-review samples are below. They are evidence placeholders for the
G-1 review record, not PASS assertions.

| Pane | PID | Pane cwd | tmux current runtime | Manual review |
|---|---:|---|---|---|
| `EduFlowTeam:manager.0` | `92675` | production checkout above | `2.1.207` | **PENDING** — cwd and PID correlated; exact CLI binary/version and sanitized startup entry still require review |
| `EduFlowTeam:worker_course.0` | `92872` | production checkout above | `2.1.207` | **PENDING** — cwd and PID correlated; exact CLI binary/version and sanitized startup entry still require review |
| `EduFlowTeam:worker_review.0` | `5260` | production checkout above | `2.1.207` | **PENDING** — cwd and PID correlated; exact CLI binary/version and sanitized startup entry still require review |

An additional live pane, `EduFlowTeam:Hermes.0` (PID `92228`), reported cwd
`/Volumes/Halobster/Obsidian Edu`, not the audited production checkout. This is
an explicit `pane_cwd_drift` failure.

## Blocking findings

1. `daemon_pid_not_live`: router PID `7193`.
2. `daemon_pid_not_live`: task-publish PID `30779`.
3. `daemon_pid_not_live`: watchdog PID `30780`.
4. `pane_cwd_drift`: `EduFlowTeam:Hermes.0`.

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
