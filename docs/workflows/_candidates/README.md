# EduFlow Team Candidate Workflows

`_candidates` stores draft, backlog, and stale candidate workflows that are not yet active registry entries.

## Boundary

- `_candidates` is not part of the active workflow registry.
- `_candidates` does not appear in `eduflowteam workflow list`.
- `_candidates` does not participate in active `eduflowteam workflow validate`.
- `_candidates` does not participate in active `eduflowteam workflow validate --strict`.
- Candidate workflows cannot be used by `task dispatch --workflow`.
- Candidate promotion must be approved through manager closeout.
- `worker_builder` is the candidate maintainer.
- `eduflowteam workflow promote-plan <candidate_id>` is read-only; it does not write files or promote a candidate.
- `eduflowteam workflow promote <candidate_id> --approved-by-manager --write` is the only allowed promotion write path.

## Candidate Status Values

- `draft`: early workflow candidate copied from `_template`.
- `backlog`: useful candidate, not ready for active registry.
- `stale_candidate`: candidate no longer matches current runtime or role boundaries.
- `promotion_ready`: candidate has passed validation and waits for manager closeout.
- `rejected`: manager rejected the candidate as active workflow.
- `case_note_only`: useful evidence, but not a reusable workflow.

Move a candidate from `draft` or `backlog` to `promotion_ready` only after human review confirms:

- the candidate is backed by real-run evidence or a concrete gap note;
- it is not a small variant of an active workflow;
- manager can call it by one stable `workflow_id`;
- manager closeout point and worker_builder followup are explicit;
- active workflow and `task dispatch --workflow` boundaries are explicit;
- `eduflowteam workflow candidate-validate --strict` passes.

## Promotion Requirements

- The candidate comes from real-run evidence or a concrete gap note.
- It is not just a small variant of an existing active workflow.
- manager can call it by stable `workflow_id`.
- `worker_builder` has filled all standard files.
- `eduflowteam workflow candidate-validate` passes.
- `eduflowteam workflow candidate-validate --strict` passes.
- `eduflowteam workflow promote-plan <candidate_id>` shows no validation or active target conflict.
- manager formally approves promotion.

## Promote Plan

Use `eduflowteam workflow promote-plan <candidate_id>` after status is `promotion_ready`.

The command prints:

- current status;
- source path under `_candidates`;
- future active target path;
- manager closeout reminder;
- file mapping for standard workflow files;
- a read-only statement.

It fails if the candidate is missing, incomplete, strict-invalid, not `promotion_ready`, or conflicts with an existing active workflow id.

Promotion is a separate future operation. This directory only stores candidate assets, and promote-plan only reviews them.

## Promotion Write Rules

Use `eduflowteam workflow promote <candidate_id> --approved-by-manager --write` only after:

- status is `promotion_ready`;
- `eduflowteam workflow candidate-validate --strict` passes;
- `eduflowteam workflow promote-plan <candidate_id>` shows no conflict;
- manager closeout explicitly approves promotion.

The write command is intentionally narrow:

- It copies only standard files into `docs/workflows/<candidate_id>/`.
- It converts target `trigger.md` from `调用 candidate workflow: <candidate_id>` to `调用 workflow: <candidate_id>`.
- It does not copy arbitrary extra candidate files.
- It does not overwrite an existing active workflow directory.
- It does not delete or move `_candidates/<candidate_id>/`.
- It does not modify candidate status.

Treat `_candidates/<candidate_id>/` as evidence and source archive even after promotion:

- candidate source remains available for audit and rollback thinking;
- `eduflowteam workflow candidates` may still show the promoted candidate copy;
- `eduflowteam workflow candidate-validate --strict` must continue to pass for that retained source;
- promotion does not dispatch agents, write tasks, send Feishu messages, or execute workflows.

## Promotion Audit Layer

v2.0 keeps promotion audit read-only.

Use `eduflowteam workflow promotion-map` to compare candidate and active registry presence without writing back into candidate files.

Current rule:

- `_candidates/<candidate_id>/` remains the evidence/source archive;
- a matching `docs/workflows/<candidate_id>/` means the workflow has been promoted into the active registry;
- the audit layer does not rewrite candidate status or append `promoted_at`, `promoted_by`, or similar metadata.
