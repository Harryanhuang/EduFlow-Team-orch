# Topic 6.1 — The Binomial Expansion
## Items File

**Item 1 [F]**
Question: Expand (1 + x)³.
Answer: 1 + 3x + 3x² + x³
Difficulty: F
Topic: 6.1
Explanation: Using the binomial expansion or Pascal's triangle (row 3): C(3,0) + C(3,1)x + C(3,2)x² + C(3,3)x³ = 1 + 3x + 3x² + x³.
Tags: binomial expansion, Pascal's triangle, algebra
**Item 2 [F]**
Question: Write down the value of ₅C₂.
Answer: 10
Difficulty: F
Topic: 6.1
Explanation: ₅C₂ = 5!/(2!×3!) = (5×4×3!)/(2×1×3!) = 20/2 = 10.
Tags: binomial coefficient, combinations, nCr
**Item 3 [S]**
Question: Find the coefficient of x⁴ in (1 + x)⁷.
Answer: 35
Difficulty: S
Topic: 6.1
Explanation: General term: T_(r+1) = C(7,r) x^r. For x⁴, r = 4. Coefficient = C(7,4) = 7!/(4!×3!) = (7×6×5×4!)/(4!×6) = 210/6 = 35. Or C(7,4) = C(7,3) = 35.
Tags: binomial expansion, coefficient, general term
**Item 4 [S]**
Question: Expand (2x − 1)⁴.
Answer: 16x⁴ − 32x³ + 24x² − 8x + 1
Difficulty: S
Topic: 6.1
Explanation: (2x − 1)⁴ = C(4,0)(2x)⁴ + C(4,1)(2x)³(−1) + C(4,2)(2x)²(−1)² + C(4,3)(2x)(−1)³ + C(4,4)(−1)⁴ = 1·16x⁴ + 4·8x³(−1) + 6·4x²·1 + 4·2x(−1)³ + 1·1 = 16x⁴ − 32x³ + 24x² − 8x + 1.
Tags: binomial expansion, expanding brackets, algebra
**Item 5 [S]**
Question: Find the term independent of x in (x² + 1/x)⁶.
Answer: 15
Difficulty: S
Topic: 6.1
Explanation: General term: C(6,r)(x²)^(6−r)(1/x)^r = C(6,r)x^(12−2r)·x^(−r) = C(6,r)x^(12−3r). For term independent of x: 12 − 3r = 0 → r = 4. Coefficient: C(6,4) = 15.
Tags: binomial expansion, independent term, general term
**Item 6 [S]**
Question: Expand (1 − 2x)⁵ up to and including the term in x³.
Answer: 1 − 10x + 40x² − 80x³
Difficulty: S
Topic: 6.1
Explanation: (1−2x)⁵ = C(5,0)(1)⁵ + C(5,1)(1)⁴(−2x) + C(5,2)(1)³(−2x)² + C(5,3)(1)²(−2x)³ + ... = 1 + 5(−2x) + 10(4x²) + 10(−8x³) + ... = 1 − 10x + 40x² − 80x³.
Tags: binomial expansion, partial expansion, algebra
**Item 7 [C]**
Question: Find the coefficient of x² in (1 + 2x)⁵.
Answer: 40
Difficulty: C
Topic: 6.1
Explanation: General term: T_(r+1) = C(5,r)(2x)^r = C(5,r)·2^r·x^r. For x²: r = 2. Coefficient = C(5,2)·2² = 10 × 4 = 40.
Tags: binomial expansion, coefficient, general term
**Item 8 [C]**
Question: Using the binomial expansion, show 0.99⁴ ≈ 0.9606 (to 4 d.p.).
Answer: (1−0.01)⁴ ≈ 1 − 4(0.01) + 6(0.01)² − 4(0.01)³ + (0.01)⁴ ≈ 1 − 0.04 + 0.0006 − 0.0000004 + negligible ≈ 0.960596 ≈ 0.9606
Difficulty: C
Topic: 6.1
Explanation: 0.99 = 1 − 0.01. (1−0.01)⁴ = 1 − 4(0.01) + 6(0.01)² − 4(0.01)³ + (0.01)⁴ = 1 − 0.04 + 0.0006 − 0.0000004 + 0.0000000001 ≈ 0.960596. To 4 d.p.: 0.9606.
Tags: binomial approximation, decimal approximation, practical application
**Item 9 [C]**
Question: Prove: Σ C(n,r) = 2ⁿ for any positive integer n.
Answer: Substituting a = 1, b = 1 in the binomial expansion (1+b)^n = Σ C(n,r)a^(n−r)b^r gives (1+1)^n = Σ C(n,r)1^(n−r)1^r = Σ C(n,r). So Σ C(n,r) = 2ⁿ. QED.
Difficulty: C
Topic: 6.1
Explanation: The binomial theorem states: (a + b)^n = Σ C(n,r) a^(n−r) b^r. Setting a = 1, b = 1: (1+1)^n = Σ C(n,r)·1^(n−r)·1^r = Σ C(n,r). So 2ⁿ = Σ C(n,r) for r = 0 to n. QED.
Tags: binomial theorem, proof, summation, identity
