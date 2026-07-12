# Compatibility Debt Ledger

No compatibility path is implied by this ledger. Entries describe currently observed or master-plan-mandated migration debt; later Gate implementation must update evidence and may not claim a shim exists solely because it is listed here. No fail-open compatibility is permitted. No `skipped => ready` compatibility is permitted.

| compatibility_id | old_contract | new_contract | why_still_needed | owner | usage_metric | introduced_at | expires_at | removal_test |
|---|---|---|---|---|---|---|---|---|
| `COMPAT-ROLE-001` | `review_course` role alias | Formal REVIEW role resolves to `worker_review` | Historical configs/docs may still reference the alias | `control_plane_owner` + `workflow_definition_maintainer` | Repository and runtime-config reference count; target zero new references and zero live bindings | Before G-1 baseline | 2026-10-12 | CI reference scan rejects `review_course` outside this ledger/migration fixture; role/workflow suites pass |
| `COMPAT-CARDS-001` | Legacy Feishu cards | Cards v2 only | Existing callers require inventory before deletion | `control_plane_owner` | Production call-site count and emitted legacy-card event count; target zero | Before G-1 baseline | 2026-10-12 | Remove legacy path in disposable branch; cards/router suites and reference scan pass |
| `COMPAT-STATE-001` | JSON/file truth and planned JSON/SQLite dual-write | Transactional SQLite WAL truth with derived read models | G4 migration cannot cut over before Workflow schema stabilizes and reconciliation is zero-diff | `schema_migration_owner` | Reconciliation mismatch count; required zero for approved observation window | Planned, not yet introduced | 2026-11-30 | Fault-injected migration/reconcile/cutover tests pass with JSON writes disabled |
| `COMPAT-WORKFLOW-001` | Historical workflow aliases | Versioned Workflow Definition id/version/hash | Active reference inventory and migration mapping are not yet complete | `workflow_definition_maintainer` | Alias resolution count per definition; target zero | Before G-1 baseline | 2026-10-31 | Strict workflow validation rejects aliases and all production definitions/instances validate |
| `COMPAT-MEMORY-001` | Local `eduflow.memory` / legacy DB import paths | Single approved Flow Memory store/interface | Sibling-repository checkpoint and data migration are pending | `schema_migration_owner` | Legacy import/read count and reconciliation diff; target zero | Before G-1 baseline | 2026-11-30 | Clean install and migrated fixture operate with legacy import shim removed; reconciliation is zero |

## Enforcement

Each entry must retain all schema fields: `compatibility_id`, `old_contract`, `new_contract`, `why_still_needed`, `owner`, `usage_metric`, `introduced_at`, `expires_at`, and `removal_test`. The owner reviews usage at every dependent Gate. Missing/expired data blocks merge; extension requires a new bounded decision, fresh evidence, REVIEW, and CLOSEOUT.
