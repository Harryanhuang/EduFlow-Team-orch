---
name: igcse-9subject-sprint-lessons
description: Lessons learned from the 2026-06-22 igcse-9subject-sprint + QBank end-to-end execution (10 subjects: 0606/0610/0620/0625/0450/0452/0455/0580/0653/0478, 3356 items, QBank unified_manifest 2576 rows/3385 questions). Use when planning or executing multi-subject sprint workflows with worker_course + review_course + worker_qbank.
metadata:
  type: experience
  generated_by: manager (Plan B after Luke_recorder lazy-mode failure)
  date: 2026-06-22
---

# igcse-9subject-sprint Lessons Learned

## Sprint Outcome

- 10 subjects × 3356 items produced end-to-end in single session
- QBank unified_manifest.csv: 2576 rows, 3385 questions, errors=0
- workflow_id: `igcse-9subject-sprint`
- Boss-driven, single-boss-scope, no ad-hoc

## Critical Patterns

### 1. Single-subject focus vs parallel

- Boss rule: "一科做完再做下一科" — process subjects serially, NOT in parallel
- Order: 0606 → 0653 → 0478 (C-class completion)
- Each subject: reach ~300+ items before moving to next

### 2. worker_course context blow-up

- Symptom: context reaches 100% → API Error 400 invalid params
- Recovery: worker_builder must restart pane (preserves files but loses in-context state)
- Mitigation: keep batch ≤5 topics per cycle, use Python scripts instead of CLI Edit

### 3. Tone token cleanup is mandatory

- review_course will REJECT items with: Wait/Actually/Let me redo/Let me recalculate/Need to redo/ERROR
- ALLOWED: Verify:/Check:/Substitute:/Solve:/Try: (math teaching steps)
- Pre-clear before sending to review_course

### 4. Manifest generation pattern

- Initial manifest often outdated after expansion
- Regenerate after expansion completes, BEFORE final review
- worker_builder Python: iterate items/ directory, emit manifest rows

### 5. Review verdict authority

- review_course controls PASS verdict — never bypass
- CONDITIONAL PASS = minor cleanup needed, not failure
- Worker must fix ALL flagged items before T-XX PASS

### 6. QBank integration sequence

- worker_qbank: read existing unified_manifest.csv, merge new subject manifests
- Biology parser bug: "Foundationoundation" etc. → regex fix to "Foundation"
- 367 → 56 errors typical after cleanup; remaining = items-layer expected duplicates

## Workflow Conventions

- workflow_id: `igcse-9subject-sprint`
- Tasks: T-25 (Biology), T-26 (Bio Node 4), T-27 (Math), T-28 (Physics), T-29 (0606), T-30 (0653), T-31 (0478)
- Gates: review_handoff_gate (per subject)
- Subject codes: igcse-{subject}-{code}

## Manager Red Lines Violated (Lessons)

1. Manager must NEVER execute Python/file edits directly — always dispatch to worker_course or worker_builder
2. Manager must NEVER trust worker_course "完成" without file verification
3. Manager must NEVER skip final review verdict even when in a hurry
4. Manager must verify items count by reading files, not trusting reports

## Recovery Patterns

- worker_course crash: worker_builder restarts pane, files preserved
- review_course stale evidence: peek pane for actual content before trusting reports
- worker_course silence on task: peek pane + send urgent status request
- file mismatch: worker_builder Python script for batch fixes

## Related

- See: existing CL\nAUDE.md building rules (test gate, simplicity gate)
- See: `{{name:boss-broadcaster-collector}}` for boss chat filtering
