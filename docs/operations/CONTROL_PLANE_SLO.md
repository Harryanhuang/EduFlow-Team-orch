# EduFlow Control-Plane SLO and Failure Budgets

**Status:** approved initial G-1 policy

**Owner:** `control_plane_owner`
**Measurement rule:** measure from durable machine events. Logs, prompts, cached verdicts, and chat claims do not satisfy an SLO.

## Approved SLOs

| SLO id | Initial objective | Start / terminal evidence | Budget consequence |
|---|---|---|---|
| `high_priority_durable_persist` | 99.9% persisted within 10 seconds | ingress received / canonical durable message id | Miss is retryable; never advance cursor/seen before persistence |
| `retryable_delivery_terminal_result` | durable success or dead-letter within 5 minutes | first retryable failure / delivered or dead-letter event | Deadline exhaustion enters human takeover and blocks new automated delivery actions |
| `runtime_switch_terminal_result` | proved or failed within 3 minutes; never indefinitely pending | switch prepared / proved or failed event sharing one switch id | Exhaustion enters human takeover and blocks new automatic switches |
| `workflow_handoff_ack` | high-priority handoff acknowledged within 5 minutes | persisted handoff / acknowledgment event | Escalate to owner; no inferred ACK from unread/read or free text |
| `orphan_detection` | orphaned Loop or Workflow detected within 2 inspection cycles | lease/heartbeat loss / reconciliation finding | Freeze affected automation and assign recovery owner |
| `unauthorized_control_action_rejection` | 100% rejected and audited before side effects | structured control request / denied audit event | Any miss is a security incident; automation stops fail closed |

These are the six approved initial objectives from the master plan. G-1 establishes policy and the runtime takeover primitive; message, Loop, and Workflow enforcement lands only in their scheduled Gates and must not be reported as implemented before then.

## Circuit-breaker thresholds

| Budget id | Threshold | Transition and scope |
|---|---|---|
| `runtime_switch` | One recovery operation exhausts 3 attempts, or 3 switches for one agent within 600 seconds | Enter `active`; stop all new automatic runtime-switch side effects. Existing cooldown remains 900 seconds but does not substitute for takeover. |
| `message_retry` | No durable success or dead-letter by 5 minutes | Enter `active`; stop new automated delivery attempts until durable reconciliation. Enforcement is a G0 deliverable. |
| `loop_failure` | Same Loop fails 3 consecutive recovery runs without progress evidence | Enter `active`; stop new automatic Loop recovery. Enforcement is a G2 deliverable. |
| `workflow_repair` | Same Workflow requires more than 2 consecutive repair cycles without a new REVIEW verdict | Enter `active`; stop new automatic repair transitions. Enforcement is a G3 deliverable. |

The durable state sequence is `inactive -> active -> recovering -> inactive`. Budget exhaustion must persist the reason, source, structured actor, entry time, recovery steps, and generation. While `active` or `recovering`, every guarded automatic action must stop before side effects. Read-only status remains available. A stale generation cannot resume work.

## Transition criteria

1. `inactive -> active`: a budget is exhausted, an ambiguous/corrupt state is read, or an authorized actor explicitly enters takeover. Record the specific scope and safe recovery steps.
2. `active -> recovering`: an authorized admin or runtime operator supplies structured actor, reason, expected generation, and recovery steps. This is not success.
3. `recovering -> inactive`: the recovery state and audit event persist atomically and required probes pass. A persistence/probe failure remains fail closed.
4. Any transition ambiguity, audit failure, authorization failure, or concurrent generation change remains blocked and is escalated to `control_plane_owner`.

SLO changes are control-plane decisions. They require measurement evidence, an owner, an expiry when temporary, an executable removal/rollback test, formal REVIEW, and manager CLOSEOUT.
