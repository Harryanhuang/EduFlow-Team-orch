# Examples

## Correct Classification

### Example C1

Input:
> Explain how the structure of the ileum is adapted for absorption of digested food.

Expected route:
- skill_id: `dse-biology-ca`
- topic_id: `animal_life_processes`
- expected_confidence_min: `0.75`
- threshold_source: `assessment.confidence_thresholds.classification_minimum`

Evidence:
- Absorption and structural adaptations of the small intestine are learning outcomes in Compulsory Part III.b (p.26).

Common wrong classification:
- `cells_molecules`, because membrane transport is cellular, but the ileum as an organ belongs to animal life processes.

### Example C2

Input:
> Describe the role of ADH in osmoregulation.

Expected route:
- skill_id: `dse-biology-ca`
- topic_id: `human_physiology_regulation`
- expected_confidence_min: `0.75`
- threshold_source: `assessment.confidence_thresholds.classification_minimum`

Evidence:
- ADH and nephron function are subtopic V.a in the elective Human Physiology: Regulation and Control (p.38).

Common wrong classification:
- `homeostasis`, because basic osmoregulation is introduced there, but detailed ADH/kidney control is elective.

### Example C3

Input:
> A quadrat survey is used to estimate the population size of a plant species. State two precautions that should be taken to ensure reliable results.

Expected route:
- skill_id: `dse-biology-ca`
- topic_id: `ecosystems`
- expected_confidence_min: `0.75`
- threshold_source: `assessment.confidence_thresholds.classification_minimum`

Evidence:
- Ecological surveying methods are part of Compulsory Part III.f (p.30).

Common wrong classification:
- `applied_ecology`, because fieldwork appears there too, but basic quadrat methods are compulsory ecology.

## Misclassification

### Example M1

Input:
> Compare the use of agar plates and optical density to measure the growth of a bacterial population.

Expected route:
- skill_id: `dse-biology-ca`
- topic_id: `microbes_humans`
- reason: Measurement of microbial growth is a learning outcome of Elective Part VII.a Microbiology (p.47).

Common wrong classification:
- `cells_molecules`, because cell division is mentioned, but the context is microbial population growth techniques.

### Example M2

Input:
> Discuss whether cloning of mammals should be permitted for agricultural purposes.

Expected route:
- skill_id: `dse-biology-ca`
- topic_id: `bioengineering`
- reason: Animal cloning and its ethical implications are part of Elective Part VIII (p.51).

Common wrong classification:
- `heredity_evolution`, because genetics underpins cloning, but the focus is biotechnological application and bioethics.

## Out-of-Scope

### Example O1

Input:
> Explain the role of the sodium-potassium pump in establishing the resting potential of a neurone.

Expected result:
- verdict: `out_of_scope`
- action: `extension`
- reason: Detailed membrane potential mechanisms are beyond DSE Biology; compulsory nervous coordination covers reflex arcs and neurone structure at organism level (p.30).

### Example O2

Input:
> Design a school poster campaign to encourage students to eat more fruit.

Expected result:
- verdict: `out_of_scope`
- action: `archive`
- reason: While balanced diet is in scope, poster campaign design is not an assessable biology learning outcome.

## Cross-Topic

### Example X1

Input:
> A genetically modified bacterium is used to produce human insulin. Identify the topics involved.

Expected result:
- primary_topic_id: `bioengineering`
- secondary_topic_ids: [`heredity_evolution`, `microbes_humans`]
- reason: The primary concept is recombinant DNA technology and pharmaceutical production, which are Elective Part VIII (p.51). Molecular genetics (compulsory) and microbial culture (elective) provide supporting knowledge.

## Teacher-Facing (only if enabled)

Not enabled in this package.

## Student-Facing (only if enabled)

Not enabled in this package.

## Parent-Facing (only if enabled)

Not enabled in this package.
