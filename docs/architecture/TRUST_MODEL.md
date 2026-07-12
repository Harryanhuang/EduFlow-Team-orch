# EduFlow Control-Plane Trust Model

**Status:** pending owner approval and independent REVIEW

**Owner:** `control_plane_owner`
**Fail-closed rule:** an unknown identity, missing structured actor, empty allowlist, or ambiguous authority denies every write or control action and emits an audit event.

This document states the intended authority boundary. It does not assert that later-Gate RBAC enforcement is already implemented. Prompt text is not an authority source.

Gate G-1 is blocked: `runtime_operator` is not provisioned and approval evidence is missing. This draft cannot satisfy AC-G-1-04 or authorize a production mutation until the owner approval and independent `worker_review` verdict are recorded in the Gate acceptance package.

## Authority matrix

Every cell is explicit. “None” means denied, not inherited authority.

| Identity or role | Tools | Credentials | Files | External systems |
|---|---|---|---|---|
| `member` | Read-only, allowlisted Feishu commands only; no shell or control writes | None; sender identity may be resolved but is not a reusable credential | No direct filesystem access | Read-only Feishu responses in the originating scope |
| `operator` | Allowlisted operational writes such as `/send`; operator cannot clear or runtime-switch | Narrow Feishu actor identity only; no runtime/provider/admin secret | No direct config, state, source, verdict, or credential-file writes | Scoped Feishu send only; no destructive administration |
| `admin` | Destructive control actions only after RBAC, structured actor, target, reason, and result audit | Admin identity plus the minimum credential for the approved action; never provider secrets by default | Approved control/config paths only; no business verdict edits | Approved control-plane administration; production rotation/switch requires its checkpoint |
| `manager` | Dispatch, assignment, and CLOSEOUT gate tools; no artifact implementation tools | Assignment/closeout identity only | Task/workflow read model and authorized closeout event; no source or business artifact writes | Task dispatch and final CLOSEOUT communication only |
| `worker` | Assigned execution and self-check tools | Capability-scoped credential only when the assignment requires it | Assigned task/artifact scope only; no formal verdict or closeout writes | Assignment-scoped systems only; no formal REVIEW/CLOSEOUT |
| `reviewer` | Read/test/review tools and formal REVIEW API | Review identity; read-only test credentials where unavoidable | Candidate artifact and evidence read; REVIEW event write; no direct producer edits | Formal review channel only; cannot approve own production work |
| `builder` | Build, packaging, validation, and deployment-preparation tools | Build credential scoped to approved registry; no business-data credential | Build manifests/artifacts only; no business content or verdict writes | Approved package registry/staging only; no production business operation |
| `runtime_operator` | Runtime inspect, verify, switch, recover, and human-takeover tools; structured actor required | Runtime/provider credential scoped per agent and action; no business verdict credential | Runtime state/audit/config scope only; no task verdict or artifact writes | Runtime/provider control only; cannot REVIEW or CLOSEOUT |
| `recorder` | Append and query authorized records; no dispatch, approval, runtime switch, or candidate promotion | Append-only recorder identity | Event/audit append path only; no mutation of source records | Audit/event sink only; no workflow or business decisions |

`admin` and `runtime_operator` control actions require a non-empty structured actor identity. A display name, free text reason, pane prompt, or inferred shell user is insufficient. Identity and role are separate: being an operator does not imply admin or runtime-operator authority.

## Separation of duties

- Formal REVIEW is owned by `worker_review`; a producer cannot formally review its own artifact.
- CLOSEOUT is owned only by `manager`; manager is dispatch-only and does not produce code or business artifacts.
- A runtime operator cannot modify a business verdict. A recorder cannot dispatch work or approve an evolution candidate. A builder cannot produce business content.
- Credential rotation, production data-source switch, irreversible migration, and security-policy weakening require two-role confirmation by two distinct provisioned actors in distinct accountable roles: the domain owner plus `control_plane_owner`. The same human cannot self-confirm even if assigned both labels; an independent second provisioned actor is mandatory. A missing second actor must fail closed. REVIEW and CLOSEOUT remain distinct confirmations and do not satisfy a domain-owner approval unless those distinct roles are explicitly required by the decision.
- Emergency human takeover may stop automation immediately; resumption requires an authorized structured actor and recorded recovery evidence.

## Prompt-injection damage bounds

Prompt injection is treated as compromise of one assigned Agent, not as authority escalation. The maximum damage must remain bounded to that role's current assignment, capability pack, file scope, and external-system scope. It must not expose shared provider/admin credentials, alter Authority/Role definitions, switch runtime, write formal REVIEW/CLOSEOUT, or reach unrelated tasks. Later Gates must enforce these boundaries in code; until then, unrestricted panes are a known platform risk and are not evidence of compliance.

Credentials that must never enter an Agent pane environment are Feishu app secrets, shared admin/runtime-operator credentials, credential-rotation material, encryption KEK/DEK or recovery keys, Git hosting admin tokens, and unrelated agents' provider credentials. A task-specific credential may enter only through an approved capability with least scope and redacted audit.

## Default decision

Unknown identity, unknown target, missing owner, expired authority, missing audit storage, or role conflict => fail closed, make no external side effect, and surface an operator-readable reason.
