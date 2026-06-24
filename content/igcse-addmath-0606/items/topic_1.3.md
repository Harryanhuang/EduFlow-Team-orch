# Topic 1.3 — Functions: Domain, Range, Inverse, Composite
## Items File

**Item 1 [F]**
Question: If f(x) = 3x − 2, find f(4).
Answer: 10
Difficulty: F
Topic: 1.3
Explanation: Substitute x = 4 into f(x): f(4) = 3(4) − 2 = 12 − 2 = 10.
Tags: functions, evaluation, substitution, linear function
**Item 2 [F]**
Question: State the domain and range of f(x) = 2x + 1.
Answer: Domain: all real numbers (ℝ). Range: all real numbers (ℝ).
Difficulty: F
Topic: 1.3
Explanation: f(x) = 2x+1 is a linear function. Its domain is all real numbers because any real number can be substituted for x. Its range is also all real numbers because as x takes all real values, 2x+1 takes all real values (every real number y has a preimage x = (y−1)/2).
Tags: functions, domain, range, linear function
**Item 3 [S]**
Question: If f(x) = x² − 4 and g(x) = x + 1, find (a) f(g(x)) (b) g(f(x)).
Answer: (a) f(g(x)) = (x+1)² − 4 = x² + 2x − 3; (b) g(f(x)) = (x² − 4) + 1 = x² − 3
Difficulty: S
Topic: 1.3
Explanation: f(g(x)) means apply g first, then f: substitute g(x) = x+1 into f: f(x+1) = (x+1)² − 4 = x²+2x+1−4 = x²+2x−3. g(f(x)) means apply f first, then g: substitute f(x) = x²−4 into g: g(x²−4) = (x²−4)+1 = x²−3. Note: f(g(x)) ≠ g(f(x)) — order matters!
Tags: composite functions, function notation, evaluation
**Item 4 [S]**
Question: Find the inverse function f⁻¹(x) for f(x) = (3x − 1)/2.
Answer: f⁻¹(x) = (2x + 1)/3
Difficulty: S
Topic: 1.3
Explanation: Let y = (3x − 1)/2. Swap x and y: x = (3y − 1)/2. Solve for y: 2x = 3y − 1 → 3y = 2x + 1 → y = (2x + 1)/3. So f⁻¹(x) = (2x + 1)/3.
Tags: inverse function, function notation, algebra, linear function
**Item 5 [S]**
Question: f(x) = x² for x ≥ 0. Find f⁻¹(x) and state its domain.
Answer: f⁻¹(x) = √x. Domain of f⁻¹: x ≥ 0.
Difficulty: S
Topic: 1.3
Explanation: f(x) = x² with domain x ≥ 0 is one-to-one (passes horizontal line test). Let y = x² (with x ≥ 0). Swap: x = y². Solve for y: y = ±√x. Since the original domain required x ≥ 0, the inverse takes non-negative outputs. So y = √x. Domain of f⁻¹ = range of f = [0, ∞). Range of f⁻¹ = domain of f = [0, ∞).
Tags: inverse function, domain restriction, quadratic, square root
**Item 6 [S]**
Question: f(x) = 2x + 3, g(x) = x². Find fg(2) and gf(2).
Answer: fg(2) = 11; gf(2) = 49
Difficulty: S
Topic: 1.3
Explanation: fg(2) = f(g(2)) = f(2²) = f(4) = 2(4)+3 = 11. gf(2) = g(f(2)) = g(2·2+3) = g(7) = 7² = 49.
Tags: composite functions, function notation, evaluation, linear and quadratic
**Item 7 [C]**
Question: f is one-to-one. Given f⁻¹(5) = 3, find f(3).
Answer: f(3) = 5
Difficulty: C
Topic: 1.3
Explanation: By definition of inverse functions: if y = f⁻¹(x), then f(y) = x. Here f⁻¹(5) = 3 means when the input to f⁻¹ is 5, the output is 3. Applying f to both sides: f(f⁻¹(5)) = f(3) → 5 = f(3). So f(3) = 5.
Tags: inverse functions, properties, one-to-one, algebra
**Item 8 [C]**
Question: f(x) = eˣ, g(x) = ln x. Show fg(x) = x and gf(x) = x. What can you conclude?
Answer: fg(x) = f(g(x)) = e^(ln x) = x (for x > 0). gf(x) = g(f(x)) = ln(eˣ) = x. Conclusion: f and g are mutual inverses (g = f⁻¹ and f = g⁻¹).
Difficulty: C
Topic: 1.3
Explanation: fg(x) = f(g(x)) = e^(ln x) = x (definition of natural log: ln(eˣ) = x and e^(ln x) = x for x > 0). gf(x) = g(f(x)) = ln(eˣ) = x (property of logarithms: ln and e are inverse functions). Since both fg(x) = x and gf(x) = x, f and g are inverse functions of each other: g = f⁻¹ and f = g⁻¹.
Tags: inverse functions, exponential, logarithm, mutual inverses, natural log
**Item 9 [C]**
Question: f(x) = (2x − 3)/(x + 1), x ≠ −1. Find f⁻¹(x) and state domain and range of f and f⁻¹.
Answer: f⁻¹(x) = (x + 3)/(2 − x). Domain of f: x ≠ −1. Range of f: y ≠ 2. Domain of f⁻¹: x ≠ 2. Range of f⁻¹: y ≠ −1.
Difficulty: C
Topic: 1.3
Explanation: Let y = (2x−3)/(x+1). Swap: x = (2y−3)/(y+1). Cross-multiply: x(y+1) = 2y−3 → xy + x = 2y − 3 → xy − 2y = −x − 3 → y(x−2) = −x−3 → y = (−x−3)/(x−2) = (x+3)/(2−x). So f⁻¹(x) = (x+3)/(2−x). The horizontal asymptote y=2 of f means range y≠2. The vertical asymptote x=−1 of f means domain x≠−1. Since f⁻¹ swaps domain and range, domain of f⁻¹ = range of f = {x: x≠2}, range of f⁻¹ = domain of f = {y: y≠−1}.
Tags: inverse function, rational function, domain, range, algebra
