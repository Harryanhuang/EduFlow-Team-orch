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

The **DONE evidence** column distinguishes state assertions from normative use
of the word `DONE`. State assertions are resolved one-by-one in the claim
ledger below; a document-level label cannot cover several claims. Normative
tokens define a rule and are `not_applicable (normative)`, not implementation
claims.

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
| `2026-07-11-scheduled-tasks-design.md` | historical | — | P0-P9 exists as out-of-order preexisting implementation: merge `bde14c5c`, acceptance `a64d611c`, code `src/eduflow/scheduling/` plus `src/eduflow/store/scheduled_tasks.py`, tests `tests/unit/test_scheduled_engine.py` plus `tests/integration/test_scheduled_tasks_e2e.py`; it is an independent D scheduler, does not reuse Workflow Instance, and G6 remains unaccepted pending refactor after prior Gates. | n/a |
| `2026-07-11-scheduled-tasks.md` | historical | — | P0-P9 exists as out-of-order preexisting implementation: merge `bde14c5c`, acceptance `a64d611c`, code `src/eduflow/scheduling/` plus `src/eduflow/store/scheduled_tasks.py`, tests `tests/unit/test_scheduled_engine.py` plus `tests/integration/test_scheduled_tasks_e2e.py`; it is an independent D scheduler, does not reuse Workflow Instance, and G6 remains unaccepted pending refactor after prior Gates. | n/a |
| `2026-07-12-eduflow-governed-team-operating-system-master-plan.md` | active | G-1 / Task 3 | Current master implementation authority; later Gates remain blocked until their predecessors pass. | claim ledger (5 claims) |
| `2026-07-12-eduflow-upgrade-acceptance-standard.md` | active | G-1 / Task 3 | Current acceptance authority; defines evidence and veto conditions for every Gate. | not_applicable (normative) |
| `2026-07-12-g-minus-1-production-governance-implementation-plan.md` | active | G-1 / Task 3 | Current scoped execution plan for G-1; Task 3 is the present work boundary. | not_applicable (normative) |

## DONE assertion claim ledger

Machine parsing finds four `DONE` or `DONE/PARTIAL` state rows in the master
plan's current-implementation table. The mixed Flow task row is split into its
verified existing boundary and its incomplete machine-authority target, giving
five independently evaluated claims. Source anchors refer to the master plan.

| Claim ID | Source | Assertion | Status | Code evidence | Commit evidence | Test evidence | Notes |
|---|---|---|---|---|---|---|---|
| `CLM-MASTER-001` | master-plan:L54 | Residency supports warm, resident, cold, sleep, and wake behavior. | verified | `src/eduflow/runtime/residency.py`; `src/eduflow/commands/sleep_idle.py`; `src/eduflow/store/agent_residency.py`; `src/eduflow/commands/wake_alert.py`; `src/eduflow/commands/send.py`; `src/eduflow/store/local_facts.py` | `e904eee4` (warm/resident/cold configuration); `617e298f` (sleep); `78fb55ab` (wake) | `pytest tests/unit/test_residency.py tests/unit/test_residency_sleep.py tests/unit/test_residency_wake.py` | Scoped suite exercises policy, idle sleep, activity stamps, and wake alerts; the three commits distinguish configuration from the later sleep/wake decisions. |
| `CLM-MASTER-002` | master-plan:L55 | Feishu Cards v2 has a schema, role validation, building, and rendering path. | verified | `src/eduflow/feishu/cards_v2.py`; `src/eduflow/feishu/cards_v2_schema.py` | `6dc59418` (v2 origin); `95d72a8d` (escaping/E2E hardening) | `pytest tests/unit/test_cards_v2.py` | Scoped suite covers schema fields, role boundaries, rendering, escaping, and command integration. |
| `CLM-MASTER-003A` | master-plan:L56 | Structured REVIEW verdict authority is distinct from manager subject or batch CLOSEOUT. | verified | `src/eduflow/store/tasks.py` | `425c1a2a` (truth-contract hardening) | `pytest tests/unit/test_store_tasks_authority.py tests/integration/test_loop_engineering_truth_contract.py` | Latest reviewer verdict gates closeout; worker loop evidence cannot replace REVIEW. |
| `CLM-MASTER-003B` | master-plan:L56 | REVIEW and CLOSEOUT authority is backed by the planned Identity and Authority registry. | incomplete | `src/eduflow/store/tasks.py` | `425c1a2a` (current non-registry truth boundary) | `pytest tests/unit/test_store_tasks_authority.py tests/integration/test_loop_engineering_truth_contract.py` | Current checks use task fields and actor names; the G1 registry conversion is not implemented. |
| `CLM-MASTER-004` | master-plan:L58 | Workflow Registry supports list, show, use, validate, candidates, and guarded promotion. | verified | `src/eduflow/commands/workflow.py`; `src/eduflow/store/asset_registry.py` | `7f6ed420` (history-boundary import snapshot); `17760e7c` (registry doctor); `4e6b977e` (recommendation extension) | `pytest tests/unit/test_commands_workflow.py` | The pre-reinitialization origin commit is unavailable, so the ledger names the import boundary plus focused hardening commits. This verifies the current file-backed Definition Registry, not a Workflow Instance engine. |

## Supersession note

The `_副本` file is an earlier draft: unlike the canonical repair package, it
omits later completion and residual-risk annotations. The canonical file is
therefore the explicit replacement. Incorporation into the master plan does
not erase the other historical records or silently convert their claims into
current truth.
