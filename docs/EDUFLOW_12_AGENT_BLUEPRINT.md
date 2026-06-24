# EduFlow Team 12-Agent Blueprint

This document defines a practical 12-agent resident layout for EduFlow Team.

The goal is not to make all 12 agents speak all the time. The goal is:

1. every long-term responsibility has a stable owner
2. runtime fallback / cooldown / manager handoff rules stay clear
3. adding agents later does not require rewriting the orchestration model

## Topology

### Layer 1: orchestration

1. `manager`
   - sole user-facing orchestrator
   - sole formal dispatcher
   - sole final business summarizer

### Layer 2: curriculum and quality

2. `worker_curriculum_caie`
   - CAIE / IGCSE / A-Level curriculum production
3. `worker_curriculum_ib`
   - IB / AP / broader international curriculum production
4. `review_curriculum_caie`
   - QA / correctness review for CAIE line
5. `review_curriculum_ib`
   - QA / correctness review for IB/AP line

### Layer 3: admissions and schools

6. `worker_admissions_case`
   - application strategy / case production / process drafting
7. `worker_school_research`
   - school profiling / policy lookup / program comparison

### Layer 4: question bank and knowledge systems

8. `worker_qbank_schema`
   - schema / manifest / import-export / validation
9. `worker_qbank_content`
   - item ingestion / cleanup / content-side qbank processing
10. `worker_knowledge_ops`
   - knowledge base structure / synchronization / archival hygiene

### Layer 5: build and runtime

11. `worker_builder_system`
   - workflow system build / automation / runtime engineering
12. `worker_builder_runtime`
   - incident repair / monitoring / fallback tuning / guardrail maintenance

## Default runtime direction

Recommended default runtime binding pattern:

- high-judgment review / manager lanes:
  - primary: `claude-code`
  - fallback: `codex-cli`

- structured engineering lanes:
  - primary: `codex-cli`
  - fallback: `claude-code`

- high-volume content lanes:
  - primary: `claude-code` or `qwen-code`
  - fallback: `codex-cli`

## Manager policy by lane

Use `runtime_guard.manager_policy` to distinguish who can keep running after
fallback and who must pause for manager review.

Recommended first pass:

- `continue`
  - `worker_qbank_schema`
  - `worker_qbank_content`
  - `worker_knowledge_ops`
  - `worker_builder_system`
  - `worker_builder_runtime`

- `pause`
  - `worker_curriculum_caie`
  - `worker_curriculum_ib`
  - `review_curriculum_caie`
  - `review_curriculum_ib`
  - `worker_admissions_case`
  - `worker_school_research`

Reason:

- content correctness / formal review / admissions judgment are more sensitive
  to runtime drift
- infra / schema / runtime lanes are safer to continue under fallback

## Cooldown interpretation

When an agent enters runtime guard cooldown:

1. automatic switching stops temporarily
2. `needs_manager_action = true`
3. if manager policy is `pause`, that agent is treated as intake-paused
4. manager either:
   - clears guard state after confirming runtime recovered
   - re-dispatches work to sibling agent
   - narrows runtime registry for that lane

## Dispatch guidance

Manager should dispatch by stable lane, not by whichever pane looks idle.

Examples:

- CAIE topic / notes / syllabus alignment
  - `worker_curriculum_caie`
- CAIE correctness / release review
  - `review_curriculum_caie`
- IB/AP content production
  - `worker_curriculum_ib`
- admissions case writing / process sequencing
  - `worker_admissions_case`
- school comparison / requirements research
  - `worker_school_research`
- qbank ingestion / manifest / schema
  - `worker_qbank_schema`
- qbank content cleanup / normalization
  - `worker_qbank_content`
- knowledge base topology / naming / archive cleanup
  - `worker_knowledge_ops`
- workflow feature / automation build
  - `worker_builder_system`
- runtime incident / fallback / watchdog tuning
  - `worker_builder_runtime`

## Migration order

Do not jump from 5 directly to all 12 in one shot.

Recommended rollout:

1. current 5-agent trial
2. split curriculum into production + review pairs
3. add admissions + school research
4. split qbank into schema + content
5. split builder into system + runtime

This keeps every expansion tied to a real lane boundary, not vanity headcount.
