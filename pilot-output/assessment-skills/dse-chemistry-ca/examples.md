# Examples

## Correct Classification

### Example C1

Input:
> Calculate the empirical formula of magnesium oxide from experimental masses.

Expected route:
- skill_id: `dse-chemistry-ca`
- topic_id: `chem-metals`
- expected_confidence_min: `0.75`
- threshold_source: `assessment.confidence_thresholds.classification_minimum`

Evidence:
- Empirical formula calculation is a learning outcome of the Metals topic (p.28).

Common wrong classification:
- `chem-microscopic-world-i`, because formulae are introduced there, but empirical/molecular formula calculations are in Metals.

### Example C2

Input:
> Explain why ammonia is a polar molecule.

Expected route:
- skill_id: `dse-chemistry-ca`
- topic_id: `chem-microscopic-world-ii`
- expected_confidence_min: `0.75`
- threshold_source: `assessment.confidence_thresholds.classification_minimum`

Evidence:
- Polarity of molecules is covered in Microscopic World II (p.39-41).

Common wrong classification:
- `chem-microscopic-world-i`, because bonding is introduced there, but polarity requires electronegativity and IMF concepts from topic 6.

### Example C3

Input:
> Describe the Haber process and explain the choice of temperature and pressure.

Expected route:
- skill_id: `dse-chemistry-ca`
- topic_id: `chem-elective-industrial`
- expected_confidence_min: `0.75`
- threshold_source: `assessment.confidence_thresholds.classification_minimum`

Evidence:
- Haber process, rate/equilibrium trade-offs and industrial conditions are in Industrial Chemistry (p.63-66).

Common wrong classification:
- `chem-chemical-equilibrium`, because equilibrium principles are used, but the industrial process context and optimisation belong to the elective.

## Misclassification

### Example M1

Input:
> A student writes that increasing temperature increases the yield of an exothermic reversible reaction. Explain why this is incorrect.

Expected route:
- skill_id: `dse-chemistry-ca`
- topic_id: `chem-chemical-equilibrium`
- reason: The item concerns temperature effect on equilibrium position and Kc, which is a Chemical Equilibrium learning outcome (p.52-54). It is not primarily about reaction rate.

Common wrong classification:
- `chem-reaction-kinetics`, because temperature affects rate, but the question is about yield/equilibrium.

### Example M2

Input:
> Compare the use of IR spectroscopy and chemical tests to identify the functional groups in an unknown organic compound.

Expected route:
- skill_id: `dse-chemistry-ca`
- topic_id: `chem-elective-analytical`
- reason: Instrumental methods (IR) and functional group tests are in Analytical Chemistry (p.72-77), not the compulsory organic chemistry topic.

Common wrong classification:
- `chem-carbon-compounds`, because the compound is organic, but the focus is analytical identification methods.

## Out-of-Scope

### Example O1

Input:
> Explain the molecular orbital theory of bonding in the oxygen molecule.

Expected result:
- verdict: `out_of_scope`
- action: `extension`
- reason: Molecular orbital theory is beyond DSE Chemistry; the compulsory bonding topic uses simple electron diagrams and Lewis structures (p.19-24).

### Example O2

Input:
> Design a marketing campaign to promote recycling of plastic bottles in your school.

Expected result:
- verdict: `out_of_scope`
- action: `archive`
- reason: While green chemistry and recycling are mentioned, designing a marketing campaign is not an assessable chemistry learning outcome.

## Cross-Topic

### Example X1

Input:
> A titration is carried out to find the concentration of ethanoic acid in vinegar using sodium hydroxide. Identify the topics involved.

Expected result:
- primary_topic_id: `chem-acids-bases`
- secondary_topic_ids: [`chem-carbon-compounds`]
- reason: The primary concept is acid-base titration and molarity (p.30-33). The analyte is an organic acid, so carbon compounds knowledge is secondary.

