# EduFlow Control-Plane SLO and Failure Budgets

**Status:** pending owner approval and independent REVIEW

**Owner:** `control_plane_owner`
**Measurement rule:** measure from durable machine events. Logs, prompts, cached verdicts, and chat claims do not satisfy an SLO.

Gate G-1 is blocked: `runtime_operator` is not provisioned and approval evidence is missing. The targets below are proposed contract values from the master plan, not an approved or currently enforced production SLO.

## Proposed SLOs

| SLO id | Initial objective | Start / terminal evidence | Budget consequence |
|---|---|---|---|
| `high_priority_durable_persist` | 99.9% persisted within 10 seconds | ingress received / canonical durable message id | Miss is retryable; never advance cursor/seen before persistence |
| `retryable_delivery_terminal_result` | durable success or dead-letter within 5 minutes | first retryable failure / delivered or dead-letter event | Deadline exhaustion enters human takeover and blocks new automated delivery actions |
| `runtime_switch_terminal_result` | proved or failed within 3 minutes; never indefinitely pending | switch prepared / proved or failed event sharing one switch id | Exhaustion enters human takeover and blocks new automatic switches |
| `workflow_handoff_ack` | high-priority handoff acknowledged within 5 minutes | persisted handoff / acknowledgment event | Escalate to owner; no inferred ACK from unread/read or free text |
| `orphan_detection` | orphaned Loop or Workflow detected within 2 inspection cycles | lease/heartbeat loss / reconciliation finding | Freeze affected automation and assign recovery owner |
| `unauthorized_control_action_rejection` | 100% rejected and audited before side effects | structured control request / denied audit event | Any miss is a security incident; automation stops fail closed |

These are the six proposed initial objectives from the master plan. G-1 drafts policy and has a runtime takeover primitive; message, Loop, and Workflow enforcement lands only in their scheduled Gates and must not be reported as implemented before then.

## Circuit-breaker thresholds

| Budget id | Threshold | Transition and scope |
|---|---|---|
| `runtime_switch` | 3 consecutive failed automatic recovery attempts for the same agent/runtime recovery chain | Enter `active`; stop all new automatic runtime-switch side effects. Count only a durable switch event whose mode is automatic and terminal result is failed. A successful proved automatic recovery resets that chain to zero. A manual authorized override does not increment or reset the automatic budget and is audited separately. |
| `message_retry` | No durable success or dead-letter by 5 minutes | Enter `active`; stop new automated delivery attempts until durable reconciliation. Enforcement is a G0 deliverable. |
| `loop_failure` | Same Loop fails 3 consecutive recovery runs without progress evidence | Enter `active`; stop new automatic Loop recovery. Enforcement is a G2 deliverable. |
| `workflow_repair` | Same Workflow requires more than 2 consecutive repair cycles without a new REVIEW verdict | Enter `active`; stop new automatic repair transitions. Enforcement is a G3 deliverable. |

The durable state sequence is `inactive -> active -> recovering -> inactive`. Budget exhaustion must persist the reason, source, structured actor, entry time, recovery steps, and generation. While `active` or `recovering`, every guarded automatic action must stop before side effects. Read-only status remains available. A stale generation cannot resume work.

The runtime rule above is the proposed semantic target. Current G-1 code can enter takeover when one automatic failover reports at least three attempts and has a separate switch cooldown; it does not yet persist a cross-operation consecutive-failure counter with the reset/manual semantics above. `G1-Runtime-Authority`, owned by `runtime_operator` with `control_plane_owner` approval, must implement that counter from durable switch events. Removal test: `python3 -m pytest tests/integration/test_control_plane_authorization.py -k runtime_failure_budget_semantics` must pass before this limitation can be closed; until that stable test exists and passes, cross-operation budget enforcement is not an acceptance claim.

## Transition criteria

1. `inactive -> active`: a budget is exhausted, an ambiguous/corrupt state is read, or an authorized actor explicitly enters takeover. Record the specific scope and safe recovery steps.
2. `active -> recovering`: an authorized admin or runtime operator supplies structured actor, reason, expected generation, and recovery steps after the required human checkpoint. This is not success.
3. `recovering -> inactive`: current G-1 CLI persists the requested recovery state and audit transition; it does not machine-verify probes or the supplied steps. The authorized human checkpoint must independently inspect and record the required evidence before invoking it. Automatic probe-gated recovery is a `G1-Runtime-Authority` deliverable, not current behavior.
4. Any transition ambiguity, audit failure, authorization failure, or concurrent generation change remains blocked and is escalated to `control_plane_owner`.

SLO changes are control-plane decisions. They require measurement evidence, an owner, an expiry when temporary, an executable removal/rollback test, formal REVIEW, and manager CLOSEOUT.
