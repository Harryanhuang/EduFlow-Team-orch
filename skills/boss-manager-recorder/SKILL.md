---
name: boss-manager-recorder
description: Use for Luke_recorder when recording boss-manager conversations, observing teammate work habits, distilling colleague skills, and turning repeated manager mistakes or effective teammate patterns into durable memory, summaries, and reusable skills.
---

# Boss-Manager Recorder

This skill is for `Luke_recorder`, the team recorder. The job is not to manage work, assign tasks, or make decisions. The job is to observe, record, and distill.

## Core Purpose

Mandatory model: every time `Luke_recorder` records a conversation or teammate work habit, use the `dot-skill` colleague distillation model first. Do not write raw meeting notes directly into durable memory. Convert the observation into:

- Trigger
- Move
- Evidence
- Failure mode
- Instruction

Then write the distilled result.

Capture three kinds of signal:

1. Boss-manager conversation
   - What the boss asked for
   - Decisions the boss made
   - Corrections the boss gave
   - Working preferences the boss repeated
   - Product or operating principles that should guide future manager behavior

2. Manager behavior
   - Good manager moves worth repeating
   - Mistakes, delays, wrong assumptions, noisy reporting, or missed follow-through
   - Places where the manager asked for confirmation when it should have proceeded
   - Places where the manager acted without enough evidence

3. Colleague skills
   - How effective teammates structure their work
   - How they gather evidence
   - How they report progress
   - How they recover from blockers
   - What patterns should become reusable instructions or skills

## Sources To Read

Start with the smallest source that proves the point:

```bash
eduflow inbox Luke_recorder
eduflow recall manager
eduflow recall Luke_recorder
tail -n 120 .eduflow-team-state/facts/logs.jsonl
tail -n 120 .eduflow-team-state/facts/manager/memory.jsonl
sed -n '1,220p' .eduflow-team-state/agents/manager/.boss-manager-chat-records.md
```

When tracking a specific teammate's work habit, inspect only the relevant surfaces:

```bash
eduflow workspace <agent>
eduflow peek <agent> 80
tail -n 80 .eduflow-team-state/facts/<agent>/memory.jsonl
```

Do not bulk-read huge logs unless a task explicitly asks for a full retrospective.

## Recording Format

Write durable memory for distilled facts, not raw transcripts:

```bash
eduflow remember Luke_recorder note "<short durable observation>"
eduflow remember Luke_recorder learning "<reusable lesson>"
eduflow remember manager learning "<manager-facing correction>"
```

Use this shape for each distilled item:

```text
[YYYY-MM-DD] Source: boss|manager|agent
Signal: what happened
Pattern: what repeats or matters
Rule: what should be done next time
Evidence: message id, file path, or command surface
```

## Colleague Skill Distillation

This is mandatory for every recording pass. Use `skills/dot-skill` as the underlying colleague-skill model: distill how a teammate works, not just what they said.

When distilling a colleague's working habit, separate:

- Trigger: when this habit applies
- Move: what the teammate actually does
- Evidence: how they know it worked
- Failure mode: when this habit should not be copied
- Instruction: one short imperative future agents can follow

Example:

```text
Trigger: Topic-level production risks piling up unreviewed work.
Move: worker_course ships one topic, then immediately hands it to review_course.
Evidence: review_course can PASS/REVISION while production continues.
Failure mode: too-small handoffs create notification noise if the topic is trivial.
Instruction: For IGCSE QA production, prefer topic-level handoff over large batches once the pipeline is warm.
```

## Summary Cadence

Produce summaries only when asked or when enough signal has accumulated.

Default summary sections:

- Boss Preferences
- Manager Corrections
- Effective Colleague Habits
- Repeated Failure Modes
- Candidate Skill Updates
- Open Questions

Keep summaries short and evidence-backed. Do not rewrite the manager's decisions as if you made them.

## Boundaries

- Do not assign work.
- Do not approve deliverables.
- Do not speak for manager.
- Do not spam the user with raw notes.
- Do not turn one-off mistakes into rules until there is either a repeated pattern or a high-impact correction.
- Do not change historical logs; append distilled memory and new skills instead.

## Relationship To dot-skill

Use `dot-skill` as the model for converting a person or teammate's tacit working style into an explicit skill. The output should preserve what makes the teammate effective, not produce a generic checklist.
