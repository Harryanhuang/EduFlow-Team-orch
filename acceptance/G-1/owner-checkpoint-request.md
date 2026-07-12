# G-1 Project Owner Checkpoint Request

Submission target: `73e7b3f4cd47cbc48b985ccbf261266fe38b02d2`
Result: PENDING

Please provide or confirm these three checkpoints with a durable reference
(approval record ID, or signed document path plus identity, time, and applicable
revision). Do not include credential values.

1. **Identity appointment:** appoint a real, structured, provisioned
   `runtime_operator` actor ID. Confirm that it is limited to runtime
   inspect/verify/switch/recover/human-takeover authority. A placeholder,
   display name, or shell user is not acceptable.
2. **Governance approval:** an authorized project/control-plane/security owner
   approves `docs/architecture/TRUST_MODEL.md`,
   `docs/governance/OWNERSHIP.md`,
   `docs/operations/CONTROL_PLANE_SLO.md`, and
   `docs/operations/HUMAN_TAKEOVER_RUNBOOK.md`, including the
   `control_plane_owner` and escalation path.
3. **Tool/source approval:** approve the exact type checker and module scope,
   TruffleHog or Gitleaks, `pip-audit`, and the Node registry/advisory source
   (approve `registry.npmmirror.com` or name an alternative). Authorize
   read-only scans whose evidence records tool version, command, exit status,
   time, and covered revision.

After these checkpoints, G-1 still requires a final evidence refresh, a formal
`worker_review` REVIEW bound to the final committed HEAD, and only after PASS a
manager CLOSEOUT. This request does not authorize external sends, credential
rotation, history rewrite, production source switching, or irreversible
migration.
