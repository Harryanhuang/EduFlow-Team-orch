# Topic 8.2 — Applications of Differentiation
## Items File

**Item 1 [F]**
Question: Find the equation of the tangent to y = x² at x = 1.
Answer: y = 2x − 1
Difficulty: F
Topic: 8.2
Explanation: At x = 1: y = 1² = 1. dy/dx = 2x, so at x = 1, gradient m = 2. Tangent: y − 1 = 2(x − 1) → y = 2x − 1.
Tags: differentiation, tangent, equation of tangent
**Item 2 [F]**
Question: Find the stationary points of y = x² − 4x.
Answer: (2, −4)
Difficulty: F
Topic: 8.2
Explanation: dy/dx = 2x − 4. Set dy/dx = 0: 2x − 4 = 0 → x = 2. At x = 2: y = 4 − 8 = −4. Stationary point: (2, −4).
Tags: differentiation, stationary points
**Item 3 [S]**
Question: Find the maximum value of f(x) = 2x³ − 9x² + 12x.
Answer: 5 (local maximum at x = 1)
Difficulty: S
Topic: 8.2
Explanation: f'(x) = 6x² − 18x + 12 = 6(x²−3x+2) = 6(x−1)(x−2). Set = 0: x = 1 or x = 2. f''(x) = 12x − 18. At x = 1: f'' = −6 < 0 → local maximum. f(1) = 2−9+12 = 5.. At x = 2: f'' = 24−18 = 6 > 0 → local minimum. f(2) = 16−36+24 = 4. So maximum value = 5 at x = 1.
Tags: differentiation, maximum value, second derivative test
**Item 4 [S]**
Question: A rectangle has perimeter 20 cm. Find the maximum area.
Answer: 25 cm²
Difficulty: S
Topic: 8.2
Explanation: Let sides be x and y. Perimeter: 2x+2y = 20 → x+y = 10 → y = 10−x. Area A = xy = x(10−x) = 10x−x². dA/dx = 10−2x = 0 → x = 5. d²A/dx² = −2 < 0 → maximum. Area = 5 × 5 = 25 cm².
Tags: optimisation, differentiation, applications
**Item 5 [S]**
Question: Find the equation of the normal to y = x³ − 3x at (1, −2).
Answer: x = 1
Difficulty: S
Topic: 8.2
Explanation: dy/dx = 3x² − 3. At x = 1: dy/dx = 3(1)² − 3 = 0, so the tangent is horizontal. Since the point is (1, −2), the tangent equation is y = −2. The normal is perpendicular to a horizontal tangent, so it is a vertical line through (1, −2). Therefore the normal is x = 1.
Tags: differentiation, normal, tangent
**Item 6 [S]**
Question: Find the stationary points of y = 2x³ − 3x² − 36x and determine their nature.
Answer: x = −2 (max, y = 44), x = 3 (min, y = −81)
Difficulty: S
Topic: 8.2
Explanation: dy/dx = 6x² − 6x − 36 = 6(x² − x − 6) = 6(x − 3)(x + 2) = 0 → x = 3 or x = −2. f''(x) = 12x − 6. At x = 3: f''(3) = 30 > 0 → local minimum. f(3) = 2(27) − 3(9) − 36(3) = 54 − 27 − 108 = −81. At x = −2: f''(−2) = −30 < 0 → local maximum. f(−2) = 2(−8) − 3(4) − 36(−2) = −16 − 12 + 72 = 44. So x = −2 is a local maximum with y = 44; x = 3 is a local minimum with y = −81.
Tags: differentiation, stationary points, nature
**Item 7 [C]**
Question: A cone has volume V. Find the radius and height of the cone with minimum surface area for a fixed volume.
Answer: h = 2r, r = (3V/(2π))^(1/3)
Difficulty: C
Topic: 8.2
Explanation: V = (1/3)πr²h → h = 3V/(πr²). Surface area S = πr² + πrl where l = √(r²+h²). S = πr² + πr√(r²+h²). Substitute h: S(r) = πr² + πr√(r² + 9V²/(π²r⁴)). dS/dr = 0 gives h = 2r. r = (3V/(2π))^(1/3), h = 2(3V/(2π))^(1/3).
Tags: optimisation, differentiation, cone, applications
**Item 8 [C]**
Question: Find the point on the line y = 2x + 3 closest to the origin.
Answer: (−6/5, 3/5)
Difficulty: C
Topic: 8.2
Explanation: Let point be (x, 2x+3). Distance² = x² + (2x+3)² = x² + 4x²+12x+9 = 5x²+12x+9. Minimise: d(dist²)/dx = 10x+12 = 0 → x = −6/5. y = 2(−6/5)+3 = −12/5+15/5 = 3/5. Point: (−6/5, 3/5).
Tags: optimisation, differentiation, geometry
**Item 9 [C]**
Question: Prove the minimum value of x + 4/x for x > 0 is 4.
Answer: AM-GM: x + 4/x ≥ 2√(x·4/x) = 2√4 = 4. Equality when x = 4/x → x² = 4 → x = 2. QED.
Difficulty: C
Topic: 8.2
Explanation: Using AM-GM: for positive x, (x + 4/x)/2 ≥ √(x·4/x) = √4 = 2. So x + 4/x ≥ 4. Equality when x = 4/x → x² = 4 → x = 2. Minimum = 4 at x = 2. Using calculus: f(x) = x+4/x, f'(x) = 1−4/x² = 0 → x² = 4 → x = 2 (x > 0). f''(x) = 8/x³ > 0 → minimum. f(2) = 4.
Tags: optimisation, AM-GM, proof, minimum value
