---
name: qbank-lifecycle-gates
description: QBank lifecycle state machine and authorization gates. Covers state derivation from verification output, the two-key dedup/import gate, manager panel aggregation, and next-action mapping. Use when orchestrating QBank production across multiple subjects or building automation around QBank status.
metadata:
  type: workflow
  generated_by: worker_qbank
  date: 2026-06-24
---

# QBank Lifecycle State Machine & Authorization Gates

## Lifecycle States

```
           ┌─────────────────────────────────────────┐
           │              (empty subject)             │
           │                    │                     │
           │               ┌────▼────┐               │
           │               │  scan   │               │
           │               └────┬────┘               │
           │          ┌─────────┼─────────┐          │
           │          ▼         ▼         ▼          │
           │     ┌──────────┐ ┌────────┐ ┌────────┐  │
           │     │issue_fix │ │reverify│ │ empty  │  │
           │     └────┬─────┘ └───┬────┘ └────────┘  │
           │          │           │                   │
           │          └─────┬─────┘                   │
           │                ▼                         │
           │      ┌──────────────────┐               │
           │      │ready_for_import  │               │
           │      └────────┬─────────┘               │
           │               ▼                         │
           │   ┌───────────────────────┐             │
           │   │needs_user_authorization│             │
           │   └───────────┬───────────┘             │
           │               ▼                         │
           │         (import applied)                 │
           └─────────────────────────────────────────┘
```

| State | Condition | Priority | Next Action |
|-------|-----------|----------|-------------|
| `scan` | 0 questions, 0 scanned | 1 | Run verification |
| `issue_fix` | FAIL or errors > 0 | 0 (highest) | Fix errors, re-verify |
| `reverify` | Warnings or manifest issues | 2 | Address warnings, re-verify |
| `ready_for_import` | PASS, no blocking issues | 4 | Request authorization |
| `needs_user_authorization` | PASS but not yet authorized | 5 | Wait for user/manager auth |
| `empty` | Subject directory empty/missing | 3 | Produce content first |
| `needs_review` | Pending review_course verdict | 3 | Wait for review |

## State Derivation Logic

```python
def qbank_lifecycle_status(verification_summary):
    """Derive lifecycle state from verification output."""
    total = verification_summary.get('total_questions', 0)
    scanned = verification_summary.get('scanned_files', 0)
    status = verification_summary.get('status', 'FAIL')
    errors = verification_summary.get('errors', 0)
    warnings = verification_summary.get('warnings', 0)
    manifest_issues = verification_summary.get('manifest_issues', 0)

    if total == 0 and scanned == 0:
        return 'scan'
    if status == 'FAIL' or errors > 0:
        return 'issue_fix'
    if warnings > 0 or manifest_issues > 0:
        return 'reverify'
    return 'ready_for_import'
```

## The Two-Key Dedup/Import Gate

Dedup or import apply requires **two independent authorizations**:

```
┌─────────────────────────────────────────┐
│            dedup_import_gate()           │
├─────────────────────────────────────────┤
│                                         │
│  review_course_pass ────┐               │
│                         ├──► ALLOWED    │
│  (user_auth OR mgr_auth)┘               │
│                                         │
│  dry_run ──────────────► ALWAYS ALLOWED │
│  (never counts as auth)                 │
│                                         │
└─────────────────────────────────────────┘
```

| Condition | apply_allowed | mode |
|-----------|--------------|------|
| dry_run requested | True | `dry_run` |
| review_pass=True AND auth=True | True | `apply` |
| review_pass=False | False | blocked |
| review_pass=True AND auth=False | False | blocked |

**Why two keys?** Prevents unilateral destructive operations. The reviewer confirms quality; the user/manager confirms intent.

## Manager Panel Aggregation

For dashboard consumption across all subjects:

```python
def qbank_manager_panel_summary(all_subjects):
    """Aggregate lifecycle states across subjects."""
    PRIORITY = {
        'issue_fix': 0,
        'scan': 1,
        'reverify': 2,
        'needs_review': 3,
        'empty': 3,
        'ready_for_import': 4,
        'needs_user_authorization': 5,
    }
    # most_urgent_action = subject with lowest priority number
    # Also flag: subjects ready for import, subjects blocked
```

## Package vs Subject Scope

**Critical rule**: package-level PASS never propagates to subject-level PASS.

- Package = collection of subjects (e.g., "IGCSE 9-subject sprint")
- Subject = individual (e.g., "igcse-physics-0625")

A package can be marked "all subjects delivered" only when each subject independently passes its verifier. The verifier explicitly tracks scope.

## Batch Closeout vs Subject Closeout

| Type | Scope | Requirements |
|------|-------|-------------|
| Batch closeout | Package level | All subjects reach `ready_for_import` |
| Subject closeout | Single subject | Subject verifier PASS + no legacy fragments + no drift |

**Batch closeout does NOT equal subject closeout.** A package can be batch-closed while individual subjects still have warnings requiring resolution.

## Automation Hooks

Each state maps to an automated next action (see `QBANK_LIFECYCLE_NEXT_ACTIONS` in code):

| State | Automated Action |
|-------|-----------------|
| `scan` | Trigger `qbank_verify.py` |
| `issue_fix` | Notify worker_qbank with error list |
| `reverify` | Re-run verification after fix window |
| `ready_for_import` | Send authorization request to boss |
| `needs_user_authorization` | Wait, poll periodically |

## Related

- [[igcse-qbank-verification]] — the verification that produces the summary consumed by this state machine
- [[qbank-dedup-content-hash]] — the dedup operation gated by this system
- [[ap-qbank-verification]] — AP-specific verification (same gate logic, different verifier)
