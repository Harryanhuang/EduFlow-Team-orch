# Decision and Exception Process

## Normal decisions

1. Open a decision record with the problem, affected contract/Gate, evidence, alternatives, rollback, and accountable owner.
2. Obtain the applicable domain-owner approval. Cross-layer schema, authority, success semantics, SLO, and migration decisions also require `control_plane_owner`.
3. Implement with RED/GREEN/negative tests and machine evidence.
4. `worker_review` issues formal REVIEW independently.
5. `manager` issues CLOSEOUT from the REVIEW and acceptance contract; manager does not implement the artifact.

Security weakening, credential rotation, irreversible migration, and production source/switch changes require the explicit production checkpoint defined by the acceptance contract. Chat agreement alone is not a decision record.

## Temporary exception schema

Every exception is one bounded record with all fields below:

| Field | Requirement |
|---|---|
| `exception_id` | Unique stable identifier |
| `owner` | Accountable role and provisioned actor |
| `reason` | Evidence-backed need; convenience is insufficient |
| `scope` | Exact commands, identities, data, systems, and Gate affected |
| `introduced_at` | UTC timestamp and revision |
| `expiry` | Mandatory UTC deadline; no “TBD”, “permanent”, or blank value |
| `impact` | Security/data/availability effect and worst case |
| `mitigation` | Compensating control and observable signal |
| `removal_test` | Executable test proving the exception can be removed |
| `approvals` | Domain owner, REVIEW, and manager CLOSEOUT; control-plane/security owner when applicable |

Unbounded exceptions are prohibited. An exception cannot weaken fail-closed identity, durable ACK, secret handling, formal REVIEW ownership, or manager-only CLOSEOUT. Expired exceptions fail CI/acceptance and must be removed or replaced through a new decision; editing the old expiry without new evidence is forbidden.

## Compatibility-specific rule

Compatibility behavior belongs in `COMPATIBILITY_DEBT.md` and additionally requires old/new contract, usage metric, expiry, and removal test. Zero observed usage is not itself removal proof; execute the removal test and regression suite.

## Emergency handling

Human takeover may stop unsafe automation before the record is complete. It cannot authorize resumption. Before recovery, supply structured actor, reason, current generation, recovery evidence, and the required owner decision. Preserve append-only audit and reconcile the full record after containment.
