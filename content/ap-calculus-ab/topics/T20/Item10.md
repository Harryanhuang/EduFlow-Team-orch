---
id: T20-Item10
difficulty: S
calculator: calc
type: frq
---
Consider the piecewise function
$$f(x) = \begin{cases} 2x & \text{for } 0 \leq x \leq 3 \\ 6 - x & \text{for } 3 < x \leq 6 \end{cases}$$

(a) Sketch the graph of $f$ on $[0, 6]$.

(b) Find $\int_0^3 f(x) \, dx$.

(c) Find $\int_3^6 f(x) \, dx$.

(d) Find $\int_0^6 f(x) \, dx$.

## Answer
(a) [Graph showing a line from $(0,0)$ to $(3,6)$, then a line from $(3,3)$ to $(6,0)$]

(b) $\int_0^3 2x \, dx = 9$

(c) $\int_3^6 (6-x) \, dx = 4.5$

(d) $\int_0^6 f(x) \, dx = 13.5$

## Explanation
(b) $\int_0^3 2x \, dx = \left[x^2\right]_0^3 = 9$

(c) $\int_3^6 (6-x) \, dx = \left[6x - \frac{x^2}{2}\right]_3^6 = (36 - 18) - (18 - 4.5) = 18 - 13.5 = 4.5$

(d) By additivity: $\int_0^6 f(x) \, dx = \int_0^3 f(x) \, dx + \int_3^6 f(x) \, dx = 9 + 4.5 = 13.5$

Geometrically, this represents the area of a triangle (base 3, height 6) plus the area of another triangle (base 3, height 3), totaling $9 + 4.5 = 13.5$.
