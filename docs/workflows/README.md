# EduFlow Team Workflow Registry

This directory is the repo-side callable workflow registry for EduFlow Team.

The dated Chinese documents in this folder are the design and evidence layer. The stable slug folders below are the manager-facing call layer:

- `igcse-subject-launch/`
- `igcse-item-level-prototype/`
- `realrun-to-workflow/`

## Manager Call Format

```text
调用 workflow: <workflow_id>
对象: <subject/task/topic>
范围: <scope>
边界: <constraints>
需要的 verdict / artifact: <expected output>
```

## Active Workflows

| workflow_id | Use When | Primary Chain |
| --- | --- | --- |
| `igcse-subject-launch` | A new IGCSE subject moves from candidate to formal launch. | `manager -> worker_course -> review_course -> manager` |
| `igcse-item-level-prototype` | Topic-level QA exists but qbank must verify item-level readiness. | `manager -> worker_qbank -> review_course -> worker_builder -> manager` |
| `realrun-to-workflow` | A real run should be turned into reusable workflow assets. | `manager -> worker_builder -> manager` |
| `ap-knowledge-base-optimization` | AP subject knowledge-base qbank item production or optimization. | `manager -> worker_course -> review_course -> manager` |
| `igcse-9subject-sprint` | Multi-subject IGCSE sprint requiring cross-subject coordination. | `manager -> worker_course -> review_course -> manager` |
| `runtime-failover-hardening` | Runtime failure requires cross-pool switch, env verify, and smoke proof. | `manager -> worker_builder -> auto_ops -> review_course -> manager` |

## Backlog Workflows

- `runtime-recovery-and-resume`
- `quality-gate-intervention`

Backlog workflows are documented in `2026-06-20 EduFlow Team Workflow Backlog 草案.md`.

## Registry Rules

- `manager` calls workflows and owns formal closeout.
- `worker_builder` maintains workflow assets.
- `auto_ops` watches anomalies; it is not the workflow owner.
- Worker/review/qbank status reassurance is allowed only as low-frequency activity proof, not formal verdict or final result language.
- Active workflows must carry gates, forbidden moves, done definition, and common failure modes.

## CLI Use

Use `eduflowteam workflow` as the primary operator entrypoint. `eduflow workflow` remains a legacy alias while the project finishes the name migration.

For local development, this repo also includes `scripts/eduflowteam`, a small shim that points the command at this checkout's `src/` tree. It is useful when the legacy global `eduflow` command still points at an older checkout.

```bash
eduflowteam workflow list
eduflowteam workflow show igcse-subject-launch
eduflowteam workflow trigger igcse-subject-launch
eduflowteam workflow roles igcse-subject-launch
eduflowteam workflow checklist igcse-subject-launch
eduflowteam workflow handoff igcse-subject-launch
eduflowteam workflow files igcse-subject-launch
eduflowteam workflow use igcse-subject-launch
eduflowteam workflow maintainer realrun-to-workflow
eduflowteam workflow template
eduflowteam workflow template trigger
eduflowteam workflow candidates
eduflowteam workflow candidate-show example-draft-workflow
eduflowteam workflow candidate-files example-draft-workflow
eduflowteam workflow candidate-validate
eduflowteam workflow candidate-validate --strict
eduflowteam workflow promotion-map
eduflowteam workflow promotion-map --summary
eduflowteam workflow promotion-map --manager
eduflowteam workflow promotion-map --manager --actionable
eduflowteam workflow promotion-map --manager --ready
eduflowteam workflow promotion-map --manager --summary
eduflowteam workflow promotion-map --state promoted
eduflowteam workflow promote-plan example-draft-workflow
eduflowteam workflow promote example-draft-workflow --approved-by-manager --write
eduflowteam workflow recommend "launch Physics 0625 after Accounting closeout"
eduflowteam workflow gates igcse-subject-launch
eduflowteam workflow closeout igcse-subject-launch
eduflowteam workflow gap-map
eduflowteam workflow validate
eduflowteam workflow validate --strict
```

Practical use:

- Use `recommend` when manager has only a natural task sentence and needs a conservative local workflow suggestion.
- Use `list` to choose the workflow before manager dispatches when recommendation is low-confidence.
- Use `trigger` to copy the manager call text.
- Use `checklist` before manager closeout.
- Use `gates` before dispatch or repair to inspect Core Gates, Forbidden Moves, and Block Closeout If.
- Use `closeout` immediately before manager formal closeout.
- Use `roles` when an agent drifts outside its lane.
- Use `handoff` when manager or builder needs a compact message template.
- Use `use` before manager dispatches; it prints the trigger, primary chain, role summary, closeout checklist, and handoff template in one package.
- Use `maintainer` when `worker_builder` is updating workflow assets.
- Use `template` when `worker_builder` is drafting a new workflow line.
- Use `candidates` to inspect draft/backlog workflow candidates without promoting them.
- Use `candidate-show` and `candidate-files` to review a candidate workflow.
- Use `candidate-validate` before asking manager to consider promotion; candidate triggers use `调用 candidate workflow: <workflow_id>` so they cannot be confused with active workflow calls.
- Use `promotion-map` to audit which workflow ids are still candidate-only, which are active-only, and which have both candidate source plus active target after promotion.
- Use `promotion-map --summary` when manager only needs counts, not the full table.
- Use `promotion-map --manager` when manager wants the most actionable rows first, especially `promotion_ready` candidates that can move toward closeout.
- Use `promotion-map --manager --actionable` as the day-to-day manager queue when you only want candidate-side decision items.
- Use `promotion-map --manager --ready` when manager only wants items that can move into `promote-plan` plus closeout today.
- Use `promotion-map --ready` as shorthand for the same ready queue when you do not need the extra `--manager` spelling.
- Use `promotion-map --manager --summary` when manager wants only the high-level actionable buckets, not row-level detail.
- Use `promotion-map --state <candidate_only|promoted|active_only>` when manager only wants one slice.
- Use `promote-plan` only after a candidate is marked `promotion_ready`; it prints a read-only dry-run plan and file mapping, but does not promote anything.
- Use `promote <candidate_id> --approved-by-manager --write` only after `promote-plan` is clean and manager closeout explicitly approves the write; it is the v1.9 controlled write command.
- Use `gap-map` when turning real-run issues or gap notes back into workflow gates and builder maintenance work.
- Use `validate` after `worker_builder` updates workflow assets.
- Use `validate --strict` before marking a workflow active or after major edits.

When creating task evidence, record the workflow id without starting any automatic engine:

```bash
eduflow task dispatch worker_course "Physics 0625 launch" \
  --stage curriculum \
  --owner worker_course \
  --workflow igcse-subject-launch
```

This only stores `workflow_id` on the task so `task get`, `task list`, `manager-overview`, and `manager-panel` can show which workflow guided the work. It does not dispatch the workflow automatically.

In `manager-overview` and `manager-panel`, tasks with `workflow_id` also show:

- `workflow_gate_hint`: the next likely gate manager should watch.
- `workflow_next_check`: the next local CLI surface to inspect.

These hints are intentionally conservative. They are reminders for manager/operator review, not an execution engine.

## Builder Maintenance Loop

When a real run exposes a repeated issue, `worker_builder` should use:

```bash
eduflowteam workflow gap-map
eduflowteam workflow maintainer <workflow_id>
eduflowteam workflow validate --strict
```

The maintainer package exposes a small maintenance action taxonomy:

- `update_trigger_examples`
- `update_forbidden_moves`
- `update_acceptance_gates`
- `mark_stale_candidate`
- `split_new_workflow_candidate`

Use these actions to decide whether the current workflow needs a small update, should be marked stale, or should split into a new workflow candidate.

## New Workflow Intake

`docs/workflows/_template/` is the standard starting point for new workflow lines. It is a template asset, not an active workflow. `workflow list`, `workflow validate`, and `workflow validate --strict` ignore `_template`; `workflow template` is the read-only viewer for it.

`docs/workflows/_candidates/` is the candidate pool for draft, backlog, and stale candidate workflows. It is also outside the active registry. Candidate workflows are visible through candidate-specific commands, not through `workflow list`.

Standard intake flow:

1. Identify a repeated collaboration pattern from a real run or gap note.
2. manager calls `realrun-to-workflow`.
3. `worker_builder` reads `eduflowteam workflow template` and drafts a new workflow from `_template`.
4. Keep the candidate as `draft` or backlog first; do not mark it active immediately.
5. Place candidate files under `docs/workflows/_candidates/<workflow_id>/`.
6. Run `eduflowteam workflow candidate-validate`.
7. Run `eduflowteam workflow candidate-validate --strict`.
8. Set status to `promotion_ready` only after human review confirms the candidate is callable and not a duplicate.
9. Run `eduflowteam workflow promote-plan <workflow_id>` to inspect the read-only promotion plan.
10. manager confirms promotion through closeout before it enters the active registry.
11. Run `eduflowteam workflow promote <workflow_id> --approved-by-manager --write` to copy the validated candidate into the active registry.

Decision rules:

- Old workflow variant: update the existing workflow when the primary chain and closeout gate are unchanged; use `update_trigger_examples`, `update_forbidden_moves`, or `update_acceptance_gates`.
- New workflow: create a candidate only when the participant chain, manager closeout point, or acceptance gates are materially different.
- Case note only: keep it outside active registry when the issue is one-off, not repeatable, or cannot be called by manager as a workflow.
- Stale candidate: use `mark_stale_candidate` when repeated real runs show an active workflow no longer matches runtime reality.
- Split candidate: use `split_new_workflow_candidate` when one active workflow is carrying two different chains or closeout rules.

New workflow assets must keep these boundaries:

- manager is the workflow caller and formal decision owner.
- `worker_builder` is the workflow maintainer.
- Worker/review/qbank roles stay inside their role lanes.
- `auto_ops` remains watcher / anomaly lane, not the workflow owner.
- Worker reassurance can show activity but must not抢 manager formal verdict, problem explanation, user-facing result, or closeout.
- The workflow is a reusable coordination asset, not an automatic execution engine.
- Candidate workflow trigger examples must use `调用 candidate workflow: <workflow_id>`, not the active `调用 workflow: <workflow_id>` call format.

## Candidate Lifecycle

Candidate workflows move through these statuses:

- `draft`: copied from `_template` and still being shaped.
- `backlog`: useful, but not ready for active registry.
- `stale_candidate`: no longer matches runtime, role boundaries, or current workflow taxonomy.
- `promotion_ready`: validated and waiting for manager closeout.
- `active`: promoted into the active registry after manager closeout.
- `rejected`: manager rejected the candidate as an active workflow.
- `case_note_only`: retained as evidence, not a reusable workflow.

Promotion requires all of the following:

- The candidate comes from a real run or gap note.
- It is not a simple variant of an active workflow.
- manager can call it with one stable sentence and workflow_id.
- `worker_builder` has filled the standard files from `_template`.
- `eduflowteam workflow candidate-validate` passes.
- `eduflowteam workflow candidate-validate --strict` passes.
- `eduflowteam workflow promote-plan <workflow_id>` shows no validation or target conflicts.
- manager closeout explicitly approves promotion.

Promotion audit remains read-only in v2.0:

- `eduflowteam workflow promotion-map` derives linkage from current registry facts.
- It does not write `promoted_at`, `promoted_by`, or any other status back into candidate files.
- Candidate README is still a workflow document, not a state database.

Candidate boundaries:

- Candidate workflows cannot be used as active workflows.
- Candidate workflows must not appear in `eduflowteam workflow list`.
- Candidate workflows must not be accepted by `task dispatch --workflow`.
- Candidate workflows must not automatically dispatch agents.
- Candidate workflows must not bypass manager closeout.

## Promotion Dry-run

`eduflowteam workflow promote-plan <candidate_id>` is a read-only review command for `promotion_ready` candidates.

It checks:

- the candidate exists under `docs/workflows/_candidates/<candidate_id>/`;
- the standard candidate files exist;
- candidate strict validation passes;
- no active workflow already exists at `docs/workflows/<candidate_id>/`;
- the candidate status is exactly `promotion_ready`.

When all checks pass, it prints the source path, target path, required manager closeout reminder, and file mapping for:

- `README.md`
- `trigger.md`
- `roles.md`
- `checklist.md`
- `handoff-template.md`

It does not write files, move files, create active workflow directories, dispatch agents, write tasks, send Feishu messages, or execute workflows. A future write command such as `eduflowteam workflow promote <candidate_id> --approved-by-manager --write` would require separate approval and explicit implementation.

## Promotion Audit Map

`eduflowteam workflow promotion-map` is the v2.0 read-only audit surface for promotion linkage.

It reports each workflow id in one of these link states:

- `candidate_only`: candidate exists under `_candidates/`, but no active workflow exists yet.
- `promoted`: candidate source exists and matching active workflow exists.
- `active_only`: active workflow exists, but there is no matching candidate source in `_candidates/`.

The map is derived from current filesystem state:

- candidate presence comes from `docs/workflows/_candidates/<workflow_id>/`
- active presence comes from `docs/workflows/<workflow_id>/`
- candidate status is read from candidate `README.md` when a candidate exists

This command is intentionally audit-only:

- It does not modify candidate status.
- It does not write `promoted_at`, `promoted_by`, or `promoted_to_active`.
- It does not dispatch agents, write tasks, send Feishu messages, or execute workflows.

Manager-friendly views:

- `eduflowteam workflow promotion-map`
  - full table for active/candidate linkage review
- `eduflowteam workflow promotion-map --summary`
  - compact counts for `candidate_only`, `promoted`, and `active_only`
- `eduflowteam workflow promotion-map --manager`
  - manager-focused queue with priority and suggested next step
- `eduflowteam workflow promotion-map --manager --actionable`
  - manager daily queue focused only on `candidate_only` decision items
- `eduflowteam workflow promotion-map --manager --ready`
  - manager closeout-ready queue focused only on `promotion_ready` candidate items
- `eduflowteam workflow promotion-map --ready`
  - shorthand for the same manager closeout-ready queue
- `eduflowteam workflow promotion-map --manager --summary`
  - compact actionable buckets for closeout, review, and audit load
- `eduflowteam workflow promotion-map --state promoted`
  - filtered table for one link state only

Manager view priority:

- priority `0`: `candidate_only` and `promotion_ready`; ready to move toward `promote-plan` plus manager closeout
- priority `1`: other `candidate_only` rows still in draft/backlog/review
- priority `2`: already `promoted`, mainly for audit and verification
- priority `3`: `active_only`, meaning active workflow exists without candidate source

Manager next-step guidance is also status-aware for `candidate_only` rows:

- `draft`: finish drafting and rerun strict candidate validation
- `backlog`: keep in backlog until new real-run or gap-note evidence appears
- `stale_candidate`: reconfirm runtime fit or retire from active consideration
- `rejected`: keep as rejected evidence unless new real-run evidence appears
- `case_note_only`: retain as evidence, not as a reusable workflow line

Manager summary buckets:

- `ready_for_closeout`: `candidate_only` + `promotion_ready`
- `candidate_review`: `candidate_only` but not yet `promotion_ready`
- `promoted_audit`: already promoted rows still retained for audit
- `active_only_audit`: active rows without `_candidates` source

Actionable mode:

- `--actionable` keeps the view on `candidate_only` rows only
- it is meant for daily manager review, not full registry audit
- it stays read-only and does not change candidate state

Ready mode:

- `--ready` narrows further to `candidate_only` rows with `candidate_status == promotion_ready`
- it is meant for the short list that can move into `promote-plan` and manager closeout now
- when used alone, it defaults to the manager-ready queue rather than the generic table view
- it remains read-only and does not change candidate state

## Promotion Write

`eduflowteam workflow promote <candidate_id> --approved-by-manager --write` is the v1.9 controlled write command.

Guard conditions:

- The candidate must exist under `docs/workflows/_candidates/<candidate_id>/`.
- All standard candidate files must exist.
- `eduflowteam workflow candidate-validate --strict` must pass.
- No active workflow may already exist at `docs/workflows/<candidate_id>/`.
- The candidate status must be exactly `promotion_ready`.
- Both `--approved-by-manager` and `--write` must be present; missing either flag fails safe and writes nothing.

Write rules:

- The command creates `docs/workflows/<candidate_id>/`.
- It copies only the standard files:
  - `README.md`
  - `trigger.md`
  - `roles.md`
  - `checklist.md`
  - `handoff-template.md`
- `trigger.md` is the only transformed file:
  - source: `调用 candidate workflow: <candidate_id>`
  - target: `调用 workflow: <candidate_id>`
- Other standard files are copied as-is.
- The candidate source under `_candidates/<candidate_id>/` is retained unchanged as evidence/source archive.
- The command does not rewrite candidate status and does not delete or move candidate files.

Explicit non-goals:

- It does not dispatch agents.
- It does not write task records.
- It does not send Feishu messages.
- It does not execute workflows automatically.
- It does not overwrite an existing active workflow directory.

Recommended follow-up:

- `eduflowteam workflow validate --strict`
- `eduflowteam workflow list`

## Scaffold Boundary

A future command may be useful:

```bash
eduflowteam workflow scaffold <workflow_id>
```

That command would write files under `docs/workflows/<workflow_id>/`, so it remains intentionally not implemented. v1.9 only adds the narrow promotion write path for already-validated `promotion_ready` candidates.

Outside the guarded `promote ... --approved-by-manager --write` path, this CLI remains read-only. It does not dispatch agents, write tasks, send Feishu messages, or execute workflows automatically.
