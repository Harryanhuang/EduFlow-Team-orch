# Plan Status Index

This ledger classifies every top-level Markdown file in `docs/plans`. It is an
inventory of plan authority, not proof that planned work was implemented.
Historical and observation records remain useful evidence, but only an
`active` row may direct current implementation, and that row must identify the
current Gate and Task.

Status meanings:

- `historical`: retained context or a completed planning episode; not current
  implementation authority.
- `active`: current implementation authority at the named Gate and Task.
- `superseded`: replaced by the explicitly named plan; retained for provenance.
- `observation-only`: audit or monitoring evidence that cannot authorize a
  production change.

The **DONE evidence** column evaluates `DONE` text embedded in each source
document. `unverified` means the text remains a claim and is not promoted to
implementation truth by this index. A verified claim must name all three of
`code:`, `commit:`, and `test:` evidence. No current source document provides
that complete per-assertion evidence in a form this ledger can safely adopt.

| Plan | Status | Gate / Task | Disposition | DONE evidence |
|---|---|---|---|---|
| `2026-06-19-igcse-topic-multiagent-execution-brief.md` | historical | — | IGCSE execution brief retained as pre-governance operating context; no current authority. | n/a |
| `2026-06-21 EduFlow Team overnight gap repair packages.md` | historical | — | Canonical overnight repair record retained as evidence and incorporated into the 2026-07-12 master plan. | n/a |
| `2026-06-21 EduFlow Team overnight gap repair packages_副本.md` | superseded | — | Superseded by `2026-06-21 EduFlow Team overnight gap repair packages.md` | n/a |
| `2026-06-21-igcse-overnight-monitor-gap-note.md` | observation-only | — | Time-bounded IGCSE monitoring log; findings require revalidation before use. | n/a |
| `2026-06-22-igcse-8h-monitor-gap-note.md` | observation-only | — | Time-bounded IGCSE observation log; it explicitly records observation-only rounds. | n/a |
| `2026-06-23 AP overnight gap repair packages.md` | historical | — | AP repair proposal retained as evidence and incorporated into the 2026-07-12 master plan. | n/a |
| `2026-06-23-ap-overnight-monitor-gap-note.md` | observation-only | — | Time-bounded AP monitoring log; findings require current-state corroboration. | n/a |
| `2026-07-01-claude-squad-agent-orchestrator-gap-report.md` | observation-only | — | Comparative gap analysis retained as research evidence, not implementation authority. | n/a |
| `2026-07-01-ecc-to-eduflow-team-skill-upgrade-plan.md` | historical | — | Earlier Skill upgrade proposal incorporated into the 2026-07-12 master plan. | n/a |
| `2026-07-01-phase0-residency-audit.md` | observation-only | — | Point-in-time residency audit from an older branch baseline; current facts must be re-audited. | n/a |
| `2026-07-02-eduflow-status-trust-baseline.md` | observation-only | — | Point-in-time status-trust baseline retained as audit evidence; it cannot prove current state. | n/a |
| `2026-07-04-loop-engineering-execution-layer.md` | historical | — | Earlier dual-loop implementation design incorporated and re-gated by the 2026-07-12 master plan. | n/a |
| `2026-07-04-loop-engineering-observation-plan.md` | observation-only | — | Source declares itself an operations observation plan rather than coding authority. | n/a |
| `2026-07-07-claudeteam-upstream-borrowing-plan.md` | historical | — | Upstream-borrowing proposal retained as design provenance and incorporated into the master plan. | n/a |
| `2026-07-11-scheduled-tasks-design.md` | historical | — | Confirmed design input for G6; implementation remains gated behind Workflow Instance stability. | n/a |
| `2026-07-11-scheduled-tasks.md` | historical | — | Scheduled-task execution proposal retained as G6 input; it is not authority to bypass prior Gates. | n/a |
| `2026-07-12-eduflow-governed-team-operating-system-master-plan.md` | active | G-1 / Task 3 | Current master implementation authority; later Gates remain blocked until their predecessors pass. | unverified |
| `2026-07-12-eduflow-upgrade-acceptance-standard.md` | active | G-1 / Task 3 | Current acceptance authority; defines evidence and veto conditions for every Gate. | unverified |
| `2026-07-12-g-minus-1-production-governance-implementation-plan.md` | active | G-1 / Task 3 | Current scoped execution plan for G-1; Task 3 is the present work boundary. | unverified |

## Supersession note

The `_副本` file is an earlier draft: unlike the canonical repair package, it
omits later completion and residual-risk annotations. The canonical file is
therefore the explicit replacement. Incorporation into the master plan does
not erase the other historical records or silently convert their claims into
current truth.
