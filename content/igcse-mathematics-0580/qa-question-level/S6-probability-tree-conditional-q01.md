# Question: Question Q-S6-10
**Difficulty**: Foundation
**Question**: A bag contains 3 red balls and 2 blue balls. One ball is drawn at random. What is the probability of drawing a red ball?
**Answer**: P(red) = 3/5.
**Explanation**: Probability = number of favourable outcomes / total outcomes. A common error is forgetting to count all possible outcomes.
**Tags**: basic-probability, probability, fractions

# Question: Question Q-S6-11
**Difficulty**: Foundation
**Question**: Two coins are tossed. List all possible outcomes and find the probability of getting exactly one head.
**Answer**: Outcomes: HH, HT, TH, TT. P(exactly one head) = 2/4 = 1/2.
**Explanation**: Sample space has 4 equally likely outcomes. A common error is not listing all outcomes systematically.
**Tags**: basic-probability, outcomes, coins

# Question: Question Q-S6-12
**Difficulty**: Standard
**Question**: A dice is rolled. What is the probability of getting an even number or a number greater than 3?
**Answer**: P(even) = {2,4,6} = 3/6 = 1/2. P(>3) = {4,5,6} = 3/6 = 1/2. Union = {2,4,5,6} = 4/6 = 2/3. Using P(A or B) = P(A) + P(B) − P(A and B) = 1/2 + 1/2 − 2/6 = 2/3.
**Explanation**: Use inclusion-exclusion for "or". A common error is adding P(A) and P(B) without subtracting the overlap.
**Tags**: basic-probability, union, dice

# Question: Question Q-S6-13
**Difficulty**: Standard
**Question**: A drawer contains 4 red socks and 6 black socks. Two socks are drawn without replacement. Draw a tree diagram and find the probability that both socks are red.
**Answer**: P(R then R) = (4/10) × (3/9) = 12/90 = 2/15.
**Explanation**: Without replacement means the second probability changes. A common error is using (4/10)² for both draws.
**Tags**: tree-diagram, probability, without-replacement

# Question: Question Q-S6-14
**Difficulty**: Standard
**Question**: A bag has 5 white and 3 green balls. A ball is drawn and not replaced. Then a second ball is drawn. Find P(green then green).
**Answer**: P(G1) = 3/8. P(G2 | G1) = 2/7. P(G and G) = (3/8) × (2/7) = 6/56 = 3/28.
**Explanation**: Conditional probability on the second draw. A common error is forgetting to reduce the total after the first draw.
**Tags**: tree-diagram, conditional-probability, without-replacement

# Question: Question Q-S6-15
**Difficulty**: Challenge
**Question**: In a class, 60% of students play football, 40% play basketball, and 20% play both. A student is selected at random. Find P(plays football given that they play basketball).
**Answer**: P(F | B) = P(F and B) / P(B) = 0.20 / 0.40 = 0.5 or 1/2.
**Explanation**: P(A|B) = P(A and B) / P(B). A common error is confusing P(A|B) with P(B|A).
**Tags**: conditional-probability, Venn-diagram, set-theory

# Question: Question Q-S6-16
**Difficulty**: Challenge
**Question**: A test for a disease affects 1 in 1000 people. The test is 99% accurate (true positive rate). A person tests positive. What is the actual probability they have the disease?
**Answer**: P(disease | positive) = (0.001 × 0.99) / (0.001 × 0.99 + 0.999 × 0.01) = 0.00099 / 0.010989 ≈ 0.090 or 9%.
**Explanation**: This is a Bayesian probability problem. Most people overestimate the probability. A common error is ignoring false positives.
**Tags**: conditional-probability, Bayes-theorem, real-world-probability
