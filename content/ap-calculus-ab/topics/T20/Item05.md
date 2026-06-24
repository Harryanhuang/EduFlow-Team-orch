---
id: T20-Item05
difficulty: F
calculator: no-calc
type: frq
---
Let $g$ be a function defined for all real numbers with $g'(x) = x^2 - 4$ and $g(0) = 3$.

(a) Find $g(x)$.

(b) Evaluate $\int_0^3 (x^2 - 4) \, dx$.

(c) What is the value of $g(3)$?

## Answer
(a) $g(x) = \frac{x^3}{3} - 4x + 3$

(b) $\int_0^3 (x^2 - 4) \, dx = -3$

(c) $g(3) = 0$

## Explanation
(a) Integrating $g'(x) = x^2 - 4$:
$$g(x) = \int (x^2 - 4) \, dx = \frac{x^3}{3} - 4x + C$$
Using $g(0) = 3$: $3 = 0 + 0 + C$, so $C = 3$.
Thus, $g(x) = \frac{x^3}{3} - 4x + 3$.

(b) By FTC Part 2:
$$\int_0^3 (x^2 - 4) \, dx = \left[\frac{x^3}{3} - 4x\right]_0^3 = \left(\frac{27}{3} - 12\right) - (0 - 0) = 9 - 12 = -3$$

(c) Using the result from (a): $g(3) = \frac{27}{3} - 12 + 3 = 9 - 12 + 3 = 0$.

Alternatively, $g(3) = g(0) + \int_0^3 g'(x) \, dx = 3 + (-3) = 0$.
