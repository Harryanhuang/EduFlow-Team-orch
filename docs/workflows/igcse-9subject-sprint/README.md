# workflow: igcse-9subject-sprint

## Purpose

Unified 8-hour sprint framework for pushing 9 CAIE IGCSE subjects from their
current state toward complete topic outline + QA bank coverage.

9 subjects:
  0452 Accounting / 0606 AddMath / 0610 Biology / 0620 Chemistry
  0653 Combined Science / 0478 Computer Science / 0455 Economics
  0580 Mathematics / 0625 Physics

Each subject follows the same 6-node pipeline regardless of its starting state
(complete outline / partial QA / empty). The pipeline reuses existing workflow
assets: `igcse-subject-launch` for outline + seed, `igcse-item-level-prototype`
for QA depth. No new CLI commands needed.

## Primary Chain

```
manager -> worker_course -> review_course -> manager
          worker_qbank -> review_course -> manager
```

Two parallel tracks per subject:
  Track A (outline): worker_course -> review_course -> manager  [via igcse-subject-launch]
  Track B (QA depth): worker_qbank -> review_course -> manager  [via igcse-item-level-prototype]

Both tracks can run concurrently for different subjects.

## 6-Node Pipeline

### Node 1: Subject Intake & Syllabus Scan
Input: `subject_slug` + `subject_name` (from 9-subject list)

Steps:
1. Read `content/igcse-<slug>/topic-outline.md` (if exists)
2. Read `content/igcse-<slug>/qa-manifest.csv` (if exists)
3. Count: topics_in_outline, topics_with_qa, qa_items, item_files
4. Determine sprint target based on gap:
   - No outline → generate full outline (per igcse-subject-launch trigger)
   - Outline exists → scan for missing topics vs syllabus
   - QA gap < 50% → deepen QA (per igcse-item-level-prototype)
   - QA gap >= 50% → batch-generate QA first, then item-level

Deliverable: per-subject sprint brief (1 paragraph)

### Node 2: Knowledge Structure & Gap Scan
Input: sprint brief from Node 1

Steps:
1. For each subject, scan `content/igcse-<slug>/` for:
   - `topic-outline.md` completeness vs known syllabus
   - `items/` coverage (which topic_ids have items/)
   - `qa/` coverage (which topic_ids have qa/)
   - `qa-manifest.csv` vs actual files (consistency check)
2. Flag:
   - Orphan QA files not in manifest
   - Missing topic-level items/
   - Cross-reference gaps
3. Output: per-subject gap map

### Node 3: QA Generation (per topic)
Input: gap map from Node 2

Steps per topic:
1. Target: 9 QA items per topic (F:2 | S:4 | C:3 difficulty mix)
2. Naming: follow IGCSE_QA_NUMBERING_CONVENTION (Q-<topic-id>-<nn>)
3. Write: `qa-question-level/<slugified-topic>-q<nn>.md`
4. Append to `qa-manifest.csv`
5. Write: `items/<topic>-items.md` (item-level structure)

### Node 4: QA Quality Check
Input: generated QA files

Steps:
1. review_course does file-level scan:
   - Each QA file has: Question, Answer, Explanation, Tags, Difficulty
   - No duplicate Q-IDs within subject
   - Difficulty mix roughly F:2 | S:4 | C:3
   - Tags reference the correct topic
2. review_course verdict: PASS / minor revision / FAIL

### Node 5: Retry on Revision
Input: review_course verdict

Steps:
- If PASS → advance to Node 6
- If minor → worker_course/worker_qbank fixes, resubmit to Node 4
- If FAIL → log root cause, advance to Node 6 with caveats
- Max 2 retries per topic before advancing with open issues

### Node 6: Progress Summary
Triggered: every 30 minutes or when a subject completes a batch

Output format:
```
Subject          | Outline | QA gap | Items | Status
----------------|--------|--------|-------|--------
0452 Accounting  | 5/5    | 280    | 35    | Batch 3/8
0606 AddMath    | 0/10   | —      | 0     | OUTLINE_START
0610 Biology    | 3/3    | 0      | 75    | REVIEW_BATCH_2
0620 Chemistry  | 3/3    | 12     | 78    | QA_DEEPEN
...
```

## Subject Dispatch Template

```
调用 workflow: igcse-subject-launch
对象: <subject_name> (<syllabus_code>)
范围: sprint Node 1 → Node 2 → batch dispatch
需要的 artifact: topic-outline.md / qa-manifest.csv / sprint-brief
```

## 8-Hour Time Budget

Recommended pacing (adjust by actual throughput):
  Hour 0-1:   Biology 样板 run (full pipeline, iron out tooling)
  Hour 1-3:   9 subjects — first outline scan + first QA batch
  Hour 3-5:   review_course batch review, revision round 1
  Hour 5-7:   revision round 2, second QA batch for high-priority subjects
  Hour 7-8:   final summary — all 9 subjects status, open items logged

## QA Naming Convention (per IGCSE_QA_NUMBERING_CONVENTION)

Format: `Q-<topic-id>-<nn>` where nn = 01-09 per topic
Difficulty: F = Foundation, S = Standard, C = Challenge
Target per topic: F:2, S:4, C:3 = 9 items

Examples:
  Q-1.1-01  (Foundation, topic 1.1, question 1)
  Q-1.1-05  (Standard, topic 1.1, question 5)
  Q-1.1-09  (Challenge, topic 1.1, question 9)

## Existing Content Status (as of sprint start, from content/ scan)

Subject             | Outline Domains | QA items | Item files | Sprint Priority
--------------------|---------------|---------|-----------|---------------
0452 Accounting       | 5 domains    | 315    | 35        | P2
0606 AddMath         | —            | —      | —         | P7 NOT STARTED
0610 Biology         | 3 domains    | 367    | 75        | P1 样板 run
0620 Chemistry       | 3 domains    | 343    | 78        | P4
0653 Combined Science | —           | —      | —         | P8 NOT STARTED
0478 Computer Science | —           | —      | —         | P9 NOT STARTED
0455 Economics       | 2 domains    | 234    | 26        | P5
0580 Mathematics     | 3 domains    | 300    | 34        | P6
0625 Physics         | 5 domains    | 414    | 53        | P3 closeout

## Forbidden Moves

- Do not dispatch 9 subjects to the same worker pane simultaneously
- Do not skip review_course verdict even for "minor" fixes
- Do not use batch-closeout for subject closeout
- Do not close a subject until QA coverage >= 60% of topics
- Do not treat worker_course self-reports as evidence — require review_course verdict
- **builder does not抢 manager closeout** — builder owns the framework documentation and runtime monitoring only; all production decisions belong to manager

## Manager Boundary & Reassurance

worker_builder maintains this framework document but does not execute production.
All sprint pacing, subject priority, and closeout decisions belong to manager.
review_course verdicts are the only acceptable evidence for quality gates.
worker_course and worker_qbank submit work but cannot announce launch or close subjects.

## Core Gates

- `dispatch_acceptance_gate`
- `review_handoff_gate`
- `file_evidence_gate`
- `quality_gate`
- `artifact_standard_gate`
- `repair_acceptance_contract`

## Use These Files

- `trigger.md`: manager call examples for each subject dispatch
- `roles.md`: each agent's fixed responsibilities during sprint
- `checklist.md`: pre-dispatch checklist and per-node quality gates
- `handoff-template.md`: copy-ready dispatch/handoff text for manager
