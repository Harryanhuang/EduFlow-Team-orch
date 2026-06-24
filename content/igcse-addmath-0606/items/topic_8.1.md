# Topic 8.1 — Differentiation: First Principles and Polynomial Derivatives
## Items File

**Item 1 [F]**
Question: Using first principles, find the derivative of f(x) = x².
Answer: f'(x) = 2x
Difficulty: F
Topic: 8.1
Explanation: f'(x) = lim[h→0] [(x+h)² − x²]/h = lim[h→0] (2xh + h²)/h = lim[h→0] (2x + h) = 2x.
Tags: differentiation, first principles, power function, limit definition
**Item 2 [F]**
Question: Differentiate: f(x) = 5x³
Answer: f'(x) = 15x²
Difficulty: F
Topic: 8.1
Explanation: Using the power rule: d/dx(xⁿ) = nxⁿ⁻¹. Here n = 3, so f'(x) = 5 × 3x² = 15x².
Tags: differentiation, power rule, polynomial derivatives
**Item 3 [S]**
Question: Find dy/dx for (a) y = 3x⁴ − 2x² + 7x (b) y = (2x + 1)(x − 3)
Answer: (a) dy/dx = 12x³ − 4x + 7; (b) dy/dx = 4x − 5
Difficulty: S
Topic: 8.1
Explanation: (a) Power rule term by term: 3·4x³ − 2·2x + 7 = 12x³ − 4x + 7. (b) Expand first: (2x+1)(x−3) = 2x² − 6x + x − 3 = 2x² − 5x − 3. Then dy/dx = 4x − 5.
Tags: differentiation, power rule, product expansion, polynomial
**Item 4 [S]**
Question: Differentiate using the quotient rule: y = (x² + 1)/(x − 1)
Answer: dy/dx = (x² − 2x − 1)/(x − 1)²
Difficulty: S
Topic: 8.1
Explanation: u = x² + 1, v = x − 1. u' = 2x, v' = 1. dy/dx = (v·u' − u·v')/v² = ((x−1)·2x − (x²+1)·1)/(x−1)² = (2x² − 2x − x² − 1)/(x−1)² = (x² − 2x − 1)/(x − 1)².
Tags: differentiation, quotient rule, rational function
**Item 5 [S]**
Question: If y = (3x − 2)⁵, find dy/dx.
Answer: dy/dx = 15(3x − 2)⁴
Difficulty: S
Topic: 8.1
Explanation: Using the chain rule: dy/dx = 5(3x − 2)⁴ × d/dx(3x − 2) = 5(3x − 2)⁴ × 3 = 15(3x − 2)⁴.
Tags: differentiation, chain rule, power of a function, composite function
**Item 6 [S]**
Question: Find the equation of the tangent to y = x² − 4x at x = 3.
Answer: y = 2x − 3
Difficulty: S
Topic: 8.1
Explanation: At x = 3, y = 9 − 12 = −3. dy/dx = 2x − 4, so at x = 3, gradient = 2(3) − 4 = 2. Tangent: y − (−3) = 2(x − 3) → y + 3 = 2x − 6 → y = 2x − 9. Tags: differentiation, tangent line, applications of differentiation, equation of tangent
**Item 7 [C]**
Question: Using first principles, show d/dx(1/x) = −1/x².
Difficulty: C
Topic: 8.1
Explanation: Apply the limit definition: f'(x) = lim[h→0] [f(x+h) − f(x)]/h. Here f(x) = 1/x. So [1/(x+h) − 1/x]/h = [x − (x+h)]/[x(x+h)h] = −h/[x(x+h)h] = −1/[x(x+h)]. As h → 0, this approaches −1/x². QED.
Tags: differentiation, first principles, reciprocal function, limit definition
**Item 8 [C]**
Question: Differentiate: y = sin(2x² + 3x). Find dy/dx.
Answer: dy/dx = (4x + 3)cos(2x² + 3x)
Difficulty: C
Topic: 8.1
Explanation: Using the chain rule twice: Let u = 2x² + 3x, so y = sin u. dy/du = cos u, du/dx = 4x + 3. Therefore dy/dx = cos(2x² + 3x) × (4x + 3) = (4x + 3)cos(2x² + 3x).
Tags: differentiation, chain rule, trigonometric functions, composite function
**Item 9 [C]**
Question: A particle moves along a line so that its position is s(t) = 2t³ − 9t² + 12t. Find t when the particle is at rest.
Answer: t = 1 or t = 2
Difficulty: C
Topic: 8.1
Explanation: The particle is at rest when velocity v = ds/dt = 0. ds/dt = 6t² − 18t + 12 = 6(t² − 3t + 2) = 6(t − 1)(t − 2). Set equal to zero: t = 1 or t = 2.
Tags: differentiation, kinematics, applications, velocity, rates of change
