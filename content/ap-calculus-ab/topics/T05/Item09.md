---
id: T05-Item09
difficulty: S
calculator: calc
type: frq
---
The table below gives values of a differentiable function $f(x)$ at selected points.

| $x$   | 1.9  | 1.99 | 2.0  | 2.01 | 2.1  |
|-------|------|------|------|------|------|
| $f(x)$| 3.61 | 3.9601 | 4.00 | 4.0401 | 4.41 |

(a) Approximate $f'(2)$ using the average rate of change over the interval $[1.99, 2.01]$.

(b) Approximate $f'(2)$ using the average rate of change over the interval $[1.9, 2.1]$.

(c) Which approximation is likely more accurate? Explain.

## Answer
(a) $\dfrac{f(2.01) - f(1.99)}{2.01 - 1.99} = \dfrac{4.0401 - 3.9601}{0.02} = \dfrac{0.08}{0.02} = 4.00$

(b) $\dfrac{f(2.1) - f(1.9)}{2.1 - 1.9} = \dfrac{4.41 - 3.61}{0.2} = \dfrac{0.80}{0.2} = 4.00$

(c) The approximation in part (a) is likely more accurate because it uses a smaller interval centered at $x = 2$. The symmetric difference quotient with a smaller $h$ value gives a better approximation of the instantaneous rate of change, assuming the function is smooth.

## Explanation
Both approximations happen to give 4.00 because the underlying function is $f(x) = x^2$, whose derivative at $x = 2$ is exactly 4. In general, part (a) would be preferred since the symmetric difference quotient with $h = 0.01$ is a second-order approximation to the derivative, while part (b) uses $h = 0.1$.
