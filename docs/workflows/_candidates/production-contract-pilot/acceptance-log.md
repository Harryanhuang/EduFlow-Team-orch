# Production Contract Pilot — Acceptance Log

> Append-only. One row per real pilot task run. Do not edit historical
> rows; if a row is wrong, add a new row that supersedes it.

## Columns

| Column | Type | Meaning |
|--------|------|---------|
| `run_id` | `P-NN` (sequential) | identifies this run |
| `date` | YYYY-MM-DD | when the run started |
| `task_id` | `T-NN` | the EduFlow task used in this run |
| `kind` | `course / qbank` | surface area |
| `readiness_delivery` | `pass / warn / fail` | from `task readiness-check` |
| `readiness_productivity` | `pass / warn / fail` | from `task readiness-check` |
| `readiness_source` | `pass / warn / fail` | from `task readiness-check` |
| `loop_failed_checks` | int | length of `failed_checks` from `task loop-contract` |
| `evolution_event` | `review_rejected / manager_action / runtime_incident / repair_cycle_ge2 / none` | from `task evolution-packet` |
| `manager_faster` | `True / False` | subjective: was manager dispatch faster than baseline? |
| `worker_less_off_track` | `True / False` | subjective: did worker repair stay focused? |
| `review_more_specific` | `True / False` | subjective: was the review verdict more grounded? |
| `closeout_easier` | `True / False` | subjective: was closeout lighter? |
| `notes` | free text ≤ 280 chars | any extra observation (no PII) |

## Promotion Rule

After 5-10 rows are filled, count how many have `True` in each
subjective column. Promote the pilot if:

- `manager_faster` ≥ 7/10
- `worker_less_off_track` ≥ 6/10
- `review_more_specific` ≥ 6/10
- `closeout_easier` ≥ 5/10

Otherwise retire or iterate on thresholds.

## Rows

| run_id | date | task_id | kind | readiness_delivery | readiness_productivity | readiness_source | loop_failed_checks | evolution_event | manager_faster | worker_less_off_track | review_more_specific | closeout_easier | notes |
|--------|------|---------|------|--------------------|--------------------------|--------------------|--------------------|-------------------|----------------|-----------------------|------------------------|-------------------|--------|
| P-01 | 2026-07-07 | T-122 | course | pass | pass | pass | 1 | review_rejected | True | n/a | True | n/a | first pilot row. Found 2 CLI gaps: `task review --reject` ignored `--required-fix`; `send` ignored `--task-id`. Both fixed same session; loop-contract.delivery now populated when send uses --task-id |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |

## Baseline Observations (2026-07-07)

These rows are **not** counted toward the promotion rule. They capture the
state of active tasks *before* any repair loop begins, so future pilot
rows have a baseline to compare against.

| run_id | date | task_id | kind | readiness_delivery | readiness_productivity | readiness_source | loop_failed_checks | evolution_event | manager_faster | worker_less_off_track | review_more_specific | closeout_easier | notes |
|--------|------|---------|------|--------------------|--------------------------|--------------------|--------------------|-------------------|----------------|-----------------------|----------------------|-------------------|--------|
| B-01 | 2026-07-07 | T-2  | course | pass | warn | warn | 0 | none | n/a | n/a | n/a | n/a | in_progress micro-outline; no repair trigger yet |
| B-02 | 2026-07-07 | T-29 | course | pass | warn | warn | 0 | none | n/a | n/a | n/a | n/a | igcse-subject-launch AddMath 0606 C-class seed; waiting_review_handoff |
| B-03 | 2026-07-07 | T-30 | course | pass | warn | warn | 0 | none | n/a | n/a | n/a | n/a | igcse-subject-launch Combined Science 0653 C-class seed; waiting_review_handoff |
| B-04 | 2026-07-07 | T-31 | course | pass | warn | warn | 0 | none | n/a | n/a | n/a | n/a | igcse-subject-launch Computer Science 0478 C-class seed; waiting_review_handoff |
| B-05 | 2026-07-07 | T-55 | course | pass | warn | warn | 0 | none | n/a | n/a | n/a | n/a | ap-knowledge-base-optimization AP Chemistry full subject sample; submitted_for_review |
| B-06 | 2026-07-07 | T-57 | course | pass | warn | warn | 0 | none | n/a | n/a | n/a | n/a | A-Level Physics 9702 knowledge-base restructure; submitted_for_review |

> `manager_faster / worker_less_off_track / review_more_specific / closeout_easier`
> are marked `n/a` for baseline rows because no repair loop has happened yet.

## Row Entry Examples (do not transcribe literally)

```markdown
| P-01 | 2026-07-07 | T-12 | course | warn | pass | pass | 1 | review_rejected | True | True | False | True | reviewer missed scope file evidence; contract didn't surface `scope_topic` |
| P-02 | 2026-07-07 | T-13 | qbank  | pass | warn | pass | 0 | none            | True | True | True  | False | qbank loop_cycle_count dropped to 1 after repair — no evolution candidate fired |
```

## When to Stop Recording

Stop appending rows once one of the following is true:

1. 10 rows filled → manager team decides promote / retire / iterate
2. A pilot task fails `readiness_overall=fail` for two consecutive runs
   without resolution → pause the pilot and audit the readiness
   classifier thresholds (Package 5)
3. Worker_course reports the contract adds net noise (`worker_less_off_track=False`
   in 4 of 6 rows) → pause the pilot, audit the failed-checks rendering

## Out of Scope

- Notes that include agent runtime URLs, Feishu chat IDs, or any
  production secret. Mask before committing.
- PII. Do not paste student / teacher names into notes.