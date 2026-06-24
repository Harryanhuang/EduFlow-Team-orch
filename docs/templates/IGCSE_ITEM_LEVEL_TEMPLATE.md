# IGCSE Item-Level Question Entity Template

基于已通过 `review_course` 质检的 Physics 0625 原型抽象：

- `Q-1.1-01` from `content/igcse-physics-0625/qa/1-1-physical-quantities-measurement.md`
- `Q-1.2-01` from `content/igcse-physics-0625/qa/1-2-speed-velocity-acceleration-graphs.md`

边界：本模板只抽象已通过的 Foundation 计算 / 单位换算型 item 结构，不自行扩展到选择题、配图题、作图题、多步骤实验题等未验证题型。

## Markdown Entity

```md
### Question <Question ID>
**Difficulty**: <Foundation | Standard | Challenge>
**Question**: <student-facing question stem>
**Answer**: <canonical final answer>
**Explanation**: <method, calculation or reasoning, plus common error note when useful>
**Tags**: <tag-1>, <tag-2>, <tag-3>
```

## Field Rules

### Question ID

- Format: `Q-<topic-id>-<nn>`
- Examples:
  - `Q-1.1-01`
  - `Q-1.2-01`
- The topic ID must match `topic-outline.md`, `qa-manifest.csv`, and the parent QA file.
- Use two-digit ordinals within a topic: `01`, `02`, `03`.

### Difficulty

- Allowed values:
  - `Foundation`
  - `Standard`
  - `Challenge`
- For a first item prototype, default to `Foundation` unless review_course explicitly validates a higher difficulty.

### Question

- Student-facing prompt only.
- Include all quantities and units needed to answer.
- Do not include solution hints unless the item is intentionally scaffolded and review has approved that pattern.

### Answer

- Canonical final answer only.
- Include units where required.
- Keep the answer concise; working belongs in `Explanation`.

### Explanation

- State the method or formula.
- Show the key calculation or reasoning step.
- Mention one common error when the reviewed prototype contains or implies one.
- Keep explanation aligned with the exact question; do not add extra syllabus coverage.

### Tags

- Comma-separated kebab-case tags.
- Tags should map to knowledge points or skills.
- Examples:
  - `si-units`
  - `unit-conversion`
  - `length-measurement`
  - `acceleration`
  - `kinematics`
  - `formula-application`

## Knowledge Mapping

Each item must be traceable to:

| Field | Source |
|------|--------|
| `subject_slug` | course directory, e.g. `igcse-physics-0625` |
| `topic_id` | parent topic ID, e.g. `1.1` |
| `topic_name` | parent QA title / manifest topic name |
| `qa_file` | parent QA file path |
| `question_id` | item heading, e.g. `Q-1.1-01` |
| `difficulty` | item `Difficulty` field |
| `tags` | item `Tags` field |

## Optional Manifest Row

When item-level indexing is needed, use one row per item:

```csv
subject_slug,topic_id,topic_name,qa_file,question_id,difficulty,question_type,tags,review_state,source_status,notes
igcse-physics-0625,1.1,Physical quantities SI units measuring length and time,qa/1-1-physical-quantities-measurement.md,Q-1.1-01,Foundation,calculation,"si-units;unit-conversion;length-measurement",passed,reviewed-prototype,
```

## Preflight Checklist

- [ ] `Question ID` matches parent topic ID
- [ ] `Difficulty` uses the allowed enum
- [ ] `Question` is answerable without hidden context
- [ ] `Answer` includes correct unit when needed
- [ ] `Explanation` shows the method and common error where useful
- [ ] `Tags` are kebab-case and map to knowledge points
- [ ] The item does not introduce an unreviewed question type
