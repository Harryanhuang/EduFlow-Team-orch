# EduFlow Control-Plane Ownership

**Status:** pending owner approval and independent REVIEW. Role identifiers are draft governance identities; assignment to a human account must be recorded separately and may not be inferred from a pane.

Gate G-1 is blocked: `runtime_operator` is not provisioned and approval evidence is missing. This draft ownership table does not itself appoint an actor or satisfy the control-plane-owner veto; acceptance requires recorded owner approval, provisioned structured identity where required, independent `worker_review`, and manager CLOSEOUT.

| Domain / decision | Accountable owner | Required duties | Prohibited substitution |
|---|---|---|---|
| Cross-layer schema, authority, success semantics, SLO, and Gate migration | `control_plane_owner` (project owner) | Approve cross-layer contracts, risk acceptance, and production checkpoints | `manager` or implementing Agent cannot substitute |
| Security policy, credential lifecycle, incident acceptance | `security_owner` (project owner until delegated in structured registry) | Approve rotation, access scope, and security exceptions | Operator cannot self-approve |
| Workflow definitions and versions | `workflow_definition_maintainer` | Maintain version/hash, gates, bindings, and migration | Producer cannot silently change active definition |
| Skill registry and capability packs | `skill_registry_maintainer` | Approve status/risk/allowed roles/deprecation | Agent-local installed Skill is not approval |
| State schema and migrations | `schema_migration_owner` | Backup, reconciliation, cutover, forward recovery | No implicit dual-write extension |
| Runtime inspection, switch, and recovery | `runtime_operator` (must be provisioned as structured identity before production mutation) | Execute approved runtime actions and preserve audit | Cannot edit business verdict or REVIEW |
| Formal REVIEW | `worker_review` | Independently test and issue REVIEW verdict | Producer self-review cannot substitute |
| Formal CLOSEOUT | `manager` | Close only from accepted REVIEW and contract evidence; manager is dispatch-only | Manager does not implement artifacts or code |

Required owner vocabulary maps as follows: control-plane owner = `control_plane_owner`; security owner = `security_owner`; workflow definition maintainer = `workflow_definition_maintainer`; Skill registry maintainer = `skill_registry_maintainer`; schema/migration owner = `schema_migration_owner`; runtime operator = `runtime_operator`.

The control-plane owner is the final cross-layer owner. Domain owners retain their specialist approval; manager CLOSEOUT does not erase a required security, runtime, or migration signature. An owner vacancy or unprovisioned identity blocks the corresponding write or production transition.

## RACI boundary

- Implementers produce HANDOFF and self-check evidence only.
- `worker_review` owns REVIEW and must be independent of the producer.
- `manager` dispatches and issues CLOSEOUT only; manager is dispatch-only.
- `runtime_operator` may restore runtime service but cannot change business truth.
- `recorder` may append authorized evidence but cannot dispatch or approve.
- Temporary delegation must be structured, scoped, expiring, auditable, and recorded through the exception process.
