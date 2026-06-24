# Topic 2.2 — Exponential and Logarithmic Equations
## Items File

**Item 1 [F]**
Question: Solve: 4ˣ = 64
Answer: x = 3
Difficulty: F
Topic: 2.2
Explanation: Write 64 as a power of 4: 4³ = 64. So 4ˣ = 4³ → x = 3.
Tags: exponential equations, solving equations, indices
**Item 2 [F]**
Question: Solve: log₄ x = 3
Answer: x = 64
Difficulty: F
Topic: 2.2
Explanation: log₄ x = 3 means 4³ = x. So x = 64.
Tags: logarithmic equations, solving equations, conversion
**Item 3 [S]**
Question: Solve: 2ˣ = 10 (answer to 3 significant figures)
Answer: x ≈ 3.32
Difficulty: S
Topic: 2.2
Explanation: Take log₁₀ of both sides: x log₁₀ 2 = log₁₀ 10 = 1. So x = 1 / log₁₀ 2 = 1 / 0.3010 ≈ 3.322. To 3 s.f.: 3.32.
Tags: exponential equations, logarithms, solving equations, significant figures
**Item 4 [S]**
Question: Solve: log(x + 1) = 2
Answer: x = 99
Difficulty: S
Topic: 2.2
Explanation: log(x+1) = 2 means 10² = x+1 (base 10). So x+1 = 100 → x = 99.
Tags: logarithmic equations, solving equations, base 10
**Item 5 [S]**
Question: Solve: log₂(x + 3) + log₂ x = 3
Answer: x = 1
Difficulty: S
Topic: 2.2
Explanation: Combine logs: log₂[(x+3)·x] = 3 → (x+3)·x = 2³ = 8 → x² + 3x − 8 = 0 → (x+4)(x−1) = 0 → x = 1 or x = −4. Since log₂ x requires x > 0, only x = 1 is valid.
Tags: logarithmic equations, product law, solving equations, domain restriction
**Item 6 [S]**
Question: Using change of base, evaluate log₄ 8.
Answer: 3/2 or 1.5
Difficulty: S
Topic: 2.2
Explanation: log₄ 8 = (log₁₀ 8)/(log₁₀ 4) = (0.9031)/(0.6021) ≈ 1.5. Or using natural log: ln 8 / ln 4 = (ln 2³)/(ln 2²) = (3 ln 2)/(2 ln 2) = 3/2.
Tags: change of base, logarithms, evaluation, calculation
**Item 7 [C]**
Question: Solve: 3^(2x) − 4 · 3ˣ + 3 = 0
Answer: x = 0 or x = 1
Difficulty: C
Topic: 2.2
Explanation: Let y = 3ˣ. Then 3^(2x) = (3ˣ)² = y². The equation becomes: y² − 4y + 3 = 0 → (y−3)(y−1) = 0 → y = 3 or y = 1. Back-substitute: 3ˣ = 3 → x = 1; 3ˣ = 1 → x = 0. Both valid (positive).
Tags: exponential equations, quadratic substitution, solving equations
**Item 8 [C]**
Question: Solve simultaneously: 2^(x+y) = 16 and x − y = 2
Answer: x = 3, y = 1
Difficulty: C
Topic: 2.2
Explanation: 2^(x+y) = 16 = 2⁴ → x + y = 4. Together with x − y = 2, solve simultaneously: adding: 2x = 6 → x = 3. Then y = 4 − x = 4 − 3 = 1. Verify: 2^(3+1) = 2⁴ = 16 ✓; x − y = 3 − 1 = 2 ✓.
Tags: simultaneous equations, exponential equations, algebra
**Item 9 [C]**
Question: Prove the change of base formula: logₐ x = (logᵦ x)/(logᵦ a)
Answer: Let logᵦ x = m → x = βᵐ. Let logᵦ a = n → a = βⁿ. Then logₐ x = logₐ (βᵐ) = m · logₐ β = m / logᵦ a (since logₐ β = 1/logᵦ a). So logₐ x = m/n = (logᵦ x)/(logᵦ a). QED.
Difficulty: C
Topic: 2.2
Explanation: Let logᵦ x = m, so x = βᵐ. Let logᵦ a = n, so a = βⁿ. Then logₐ x = logₐ(βᵐ) = m · logₐ β. But logₐ β · logᵦ a = 1 (property of change of base, since logₐ β = 1/logᵦ a). So logₐ x = m / n = (logᵦ x)/(logᵦ a). QED. This formula allows us to evaluate logarithms in any base using a convenient calculator base (usually 10 or e).
Tags: change of base, logarithm formula, proof, algebra
