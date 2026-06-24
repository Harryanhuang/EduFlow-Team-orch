# checklist: igcse-item-level-prototype

## Before Prototype Starts

- [ ] Subject or topic-level QA has passed the needed upstream gate.
- [ ] Manager explicitly limits scope to 1-2 topics or files.
- [ ] `worker_qbank` accepted the task.
- [ ] Required item fields are clear: question, answer, explanation, topic, difficulty, type, metadata.

## Before Manager Expands Production

- [ ] `worker_qbank` produced concrete item artifacts, not only commentary.
- [ ] `review_course` reviewed exact item files.
- [ ] Verdict includes solvability and answer/explanation checks.
- [ ] Topic mapping and metadata are checked.
- [ ] `worker_builder` deposited a reusable template or template update.
- [ ] No active quality gate blocks expansion.

## Block Closeout If

- qbank prototype bypasses review.
- review stays at topic summary level.
- prototype silently expands to full production.
- builder has not captured the reusable template.

