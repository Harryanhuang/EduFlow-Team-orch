# Topic 5.1 — Arithmetic and Geometric Sequences and Series
## Items File

**Item 1 [F]**
Question: Find the 10th term of the arithmetic sequence 3, 7, 11, ...
Answer: 39
Difficulty: F
Topic: 5.1
Explanation: a = 3, d = 4. a₁₀ = a + 9d = 3 + 9(4) = 3 + 36 = 39.
Tags: arithmetic sequence, nth term, sequences
**Item 2 [F]**
Question: Find the sum of the first 8 terms of 2 + 5 + 8 + ...
Answer: 100
Difficulty: F
Topic: 5.1
Explanation: a = 2, d = 3, n = 8. S₈ = n/2[2a + (n−1)d] = 8/2[4 + 7·3] = 4[4+21] = 4 × 25 = 100. Verify: 2+5+8+11+14+17+20+23 = 100.
Tags: arithmetic series, sum, sequences
**Item 3 [S]**
Question: 3rd term is 12 and 6th term is 96 in a geometric sequence. Find r.
Answer: r = 2 or r = −2
Difficulty: S
Topic: 5.1
Explanation: a₂ = ar = 12, a₅ = ar⁴ = 96. Divide: a₅/a₂ = r³ = 96/12 = 8 → r³ = 8 → r = 2. Or r³ = 8 has one real root r = 2. If allowing negative: (−2)³ = −8 ≠ 8, so only r = 2. Check: a₂ = a·2 = 12 → a = 6. a₅ = 6·16 = 96 ✓. So r = 2.
Tags: geometric sequence, common ratio, sequences
**Item 4 [S]**
Question: Sum of first 6 terms of 3 + 6 + 12 + 24 + ...
Answer: 189
Difficulty: S
Topic: 5.1
Explanation: a = 3, r = 2, n = 6. S₆ = a(rⁿ−1)/(r−1) = 3(2⁶−1)/(2−1) = 3(64−1) = 3 × 63 = 189.
Tags: geometric series, sum, sequences
**Item 5 [S]**
Question: a = 5, d = 3. Smallest n such that Sₙ > 200.
Answer: n = 11
Difficulty: S
Topic: 5.1
Explanation: Sₙ = n/2[2a + (n−1)d] = n/2[10 + 3(n−1)] = n(3n+7)/2. Set > 200: n(3n+7) > 400. Test n=10: 370/2=185 < 200 ✗. Test n=11: 440/2=220 > 200 ✓. Smallest n = 11.
Tags: arithmetic series, sum, inequality, sequences
**Item 6 [S]**
Question: Insert two arithmetic means between 4 and 10.
Answer: 6, 8
Difficulty: S
Topic: 5.1
Explanation: Four terms: 4, A, B, 10. d = (10−4)/3 = 6/3 = 2. So A = 4 + 2 = 6, B = 4 + 4 = 8. Sequence: 4, 6, 8, 10.
Tags: arithmetic sequence, arithmetic means, sequences
**Item 7 [C]**
Question: Sum of three consecutive terms is 21, product is 336. Find the terms.
Answer: 7, 8, 6 (or 6, 7, 8)
Difficulty: C
Topic: 5.1
Explanation: Let terms be a−d, a, a+d. Sum: 3a = 21 → a = 7. Product: (7−d)(7)(7+d) = 343 − 7d² = 336 → 7d² = 7 → d² = 1 → d = ±1. So terms: 6, 7, 8 (in ascending order). Check: 6+7+8 = 21 ✓; 6×7×8 = 336 ✓.
Tags: arithmetic sequence, consecutive terms, product, sequences
**Item 8 [C]**
Question: Geometric series a = 5, r = 2. Least n for Sₙ > 1000.
Answer: n = 8
Difficulty: C
Topic: 5.1
Explanation: Sₙ = 5(2ⁿ−1)/(2−1) = 5(2ⁿ−1) > 1000 → 2ⁿ−1 > 200. Test: 2⁶−1=63 ✗, 2⁷−1=127 ✗, 2⁸−1=255 > 200 ✓. S₈ = 5(255) = 1275 > 1000. Smallest n = 8.
Tags: geometric series, sum, inequality, sequences
**Item 9 [C]**
Question: Prove AM ≥ GM for positive a, b.
Answer: (a−b)² ≥ 0 → a²−2ab+b² ≥ 0 → a²+b² ≥ 2ab → (a+b)² ≥ 4ab → (a+b)/2 ≥ √(ab). So AM ≥ GM. Equality iff a = b. QED.
Difficulty: C
Topic: 5.1
Explanation: Starting from the identity (a−b)² ≥ 0 (always true for real a, b): expand to get a² − 2ab + b² ≥ 0. Rearranging: a² + b² ≥ 2ab. Divide by 2: (a²+b²)/2 ≥ ab. Also note: (a+b)² = a²+2ab+b² ≥ 4ab → (a+b)/2 ≥ √(ab). The arithmetic mean (a+b)/2 is always ≥ the geometric mean √(ab). Equality holds iff a = b. QED.
Tags: AM-GM inequality, proof, arithmetic mean, geometric mean
