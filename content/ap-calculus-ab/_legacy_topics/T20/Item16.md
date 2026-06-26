---
id: T20-Item16
difficulty: C
calculator: no-calc
type: frq
---
Let $f$ be a function continuous on $[-2, 4]$ with the following properties:

- $f$ is even: $f(-x) = f(x)$ for all $x$
- $\int_0^2 f(x) \, dx = 6$
- $f(x) = 5 - x$ for $2 \leq x \leq 4$

(a) Find $\int_{-2}^0 f(x) \, dx$.

(b) Find $\int_2^4 f(x) \, dx$.

(c) Find $\int_{-2}^4 f(x) \, dx$.

(d) Find the average value of $f$ on $[-2, 4]$.

(e) If $g(x) = \int_0^x f(t) \, dt$, find $g'(2)$.

## Answer
(a) $\int_{-2}^0 f(x) \, dx = 6$ (by evenness)

(b) $\int_2^4 (5-x) \, dx = \left[5x - \frac{x^2}{2}\right]_2^4 = (20-8) - (10-2) = 12 - 8 = 4$

(c) $\int_{-2}^4 f(x) \, dx = \int_{-2}^0 f(x) \, dx + \int_0^2 f(x) \, dx + \int_2^4 f(x) \, dx = 6 + 6 + 4 = 16$

(d) Average value $= \frac{1}{4-(-2)} \cdot 16 = \frac{16}{6} = \frac{8}{3}$

(e) $g'(2) = f(2) = 5 - 2 = 3$

## Explanation
(a) By evenness, $\int_{-2}^0 f(x) \, dx = \int_0^2 f(x) \, dx = 6$

(b) Direct evaluation using the given formula

(c) Using additivity of definite integrals

(d) Average value formula: $\frac{1}{b-a}\int_a^b f(x) \, dx = \frac{1}{6} \cdot 16 = \frac{8}{3}$

(e) By FTC Part 1: $g'(x) = f(x)$, so $g'(2) = f(2) = 3$
