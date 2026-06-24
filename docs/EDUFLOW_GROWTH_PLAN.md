# EduFlow Team Growth Plan

This plan turns the current 5-agent trial into a stable 12-agent resident team
without forcing a one-shot cutover.

## Principle

Do not replace the current 5-agent trial all at once.

Use a staged expansion:

1. keep the current 5-agent layout running
2. add only the next lanes that create real clarity
3. expand to 12 only after runtime guard and manager handoff stay calm

## Stage 1: current 5-agent trial

Current recommended operating set:

1. `manager`
2. `worker_curriculum`
3. `review_curriculum`
4. `worker_builder`
5. `worker_qbank`

Goal:

- prove the runtime registry / fallback / watchdog / cooldown chain
- prove manager can coordinate one content lane plus one system lane

Exit criteria:

- runtime guard does not flap repeatedly
- manager can keep summaries understandable
- worker runtime fallback is observable and manageable

## Stage 2: grow from 5 to 8

Add these three lanes first:

6. `worker_curriculum_ib`
7. `worker_admissions_case`
8. `worker_school_research`

Why these three:

- curriculum usually needs at least two subject-matter production lanes
- admissions and school research are business-distinct from content production
- they create real routing clarity for manager

Recommended resulting shape:

- `manager`
- `worker_curriculum_caie`
- `worker_curriculum_ib`
- `review_curriculum`
- `worker_admissions_case`
- `worker_school_research`
- `worker_qbank`
- `worker_builder`

Operational note:

- keep only one review lane in stage 2 unless review volume becomes the bottleneck

## Stage 3: grow from 8 to 12

Split the high-load lanes:

9. `review_curriculum_caie`
10. `review_curriculum_ib`
11. `worker_qbank_schema`
12. `worker_builder_runtime`

And rename the remaining shared lanes into clearer ownership buckets:

- `worker_qbank` -> `worker_qbank_content`
- `worker_builder` -> `worker_builder_system`

End-state 12-agent set:

1. `manager`
2. `worker_curriculum_caie`
3. `worker_curriculum_ib`
4. `review_curriculum_caie`
5. `review_curriculum_ib`
6. `worker_admissions_case`
7. `worker_school_research`
8. `worker_qbank_schema`
9. `worker_qbank_content`
10. `worker_knowledge_ops`
11. `worker_builder_system`
12. `worker_builder_runtime`

## Runtime policy by stage

### Stage 1

- keep most lanes on simple primary/fallback pairs
- do not over-customize per agent yet

### Stage 2

- content lanes: prefer `claude-code` primary
- systems lanes: prefer `codex-cli` primary
- admissions / school research: use `pause` manager policy on cooldown

### Stage 3

- formal review lanes should almost always use `pause`
- schema/runtime/system lanes can usually stay `continue`
- only expand provider diversity after the lane boundaries feel stable

## Manager handoff rule

When an agent enters repeated runtime cooldown:

- if lane policy is `continue`, manager monitors but does not immediately reassign
- if lane policy is `pause`, manager must either:
  - clear guard state after runtime recovers
  - redirect the task to a sibling lane
  - temporarily collapse that lane back into a broader shared worker

## Recommendation

Do not jump from 5 directly to 12.

Best next move:

1. keep the current 5 live
2. prepare the 12-agent naming + config skeleton now
3. expand to 8 first
4. only then split review / qbank / builder into 12
