---
id: T20-Item18
difficulty: C
calculator: calc
type: frq
---
Let $f$ be a continuous function on $[-3, 3]$ with $f(-x) = -f(x)$ for all $x$ (i.e., $f$ is odd). The table shows selected values of $f$:

| $x$ | -3 | -2 | -1 | 0 | 1 | 2 | 3 |
|-----|-----|-----|-----|-----|-----|-----|-----|
| $f(x)$ | -4 | -3 | -1 | 0 | 1 | 3 | 4 |

(a) Find $\int_{-3}^0 f(x) \, dx$ and explain using the odd function property.

(b) Find $\int_0^3 f(x) \, dx$ using the given values.

(c) Find $\int_{-3}^3 f(x) \, dx$.

(d) Let $g(x) = \int_{-2}^x f(t) \, dt$. Find $g(3)$ and $g'(-1)$.

(e) Find the average value of $|f(x)|$ on $[-3, 3]$.

## Answer
(a) Using the odd function property with substitution $u = -x$:
$\int_{-3}^0 f(x) \, dx = -\int_3^0 f(-u) \, du = \int_0^3 f(-u) \, du = -\int_0^3 f(u) \, du$
Therefore $\int_{-3}^0 f = -\int_0^3 f$

(b) Using the trapezoid rule approximation: $\int_0^3 f(x) \, dx \approx 6$ (area under curve from 0 to 3)

(c) For an odd function, $\int_{-a}^a f(x) \, dx = 0$. Therefore $\int_{-3}^3 f(x) \, dx = 0$.

(d) $g(x) = \int_{-2}^x f(t) \, dt$
$g(3) = \int_{-2}^3 f(t) \, dt = \int_{-2}^0 f + \int_0^3 f = -6 + 6 = 0$
$g'(-1) = f(-1) = -1$ by FTC Part 1.

(e) By oddness, $|f|$ is even. $\int_{-3}^3 |f(x)| \, dx = 2\int_0^3 |f(x)| \, dx = 2 \cdot 6 = 12$
Average value of $|f| = \frac{12}{6} = 2$.

## Explanation
Key properties used:
- Odd functions: $\int_{-a}^a f = 0$ and $\int_{-a}^0 f = -\int_0^a f$
- FTC Part 1: $\frac{d}{dx}\int_a^x f(t) \, dt = f(x)$
- Average value: $\frac{1}{b-a}\int_a^b f(x) \, dx$
- Evenness of $|f|$ when $f$ is odd
