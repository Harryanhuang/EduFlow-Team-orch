---
id: T15-Item05
difficulty: F
calculator: calc
type: frq
---
Let $f(x) = x^3 - 2x$ on the interval $[0, 2]$.

(a) Verify that $f$ satisfies the conditions of the Mean Value Theorem on $[0, 2]$.
(b) Find the average rate of change of $f$ over $[0, 2]$.
(c) Find the value(s) of $c$ in $(0, 2)$ guaranteed by the Mean Value Theorem.

## Answer
(a) $f$ is a polynomial, so it is continuous on $[0, 2]$ and differentiable on $(0, 2)$. MVT conditions are satisfied.
(b) Average rate of change = $(f(2) - f(0))/(2 - 0) = (8 - 4 - 0)/2 = 4/2 = 2$
(c) $f'(x) = 3x^2 - 2$. Set $f'(c) = 2$: $3c^2 - 2 = 2$, so $3c^2 = 4$, $c^2 = 4/3$, $c = 2/\sqrt{3} = 2\sqrt{3}/3 \approx 1.155$. Since $2\sqrt{3}/3 \approx 1.155$ is in $(0, 2)$, this is the value guaranteed by MVT.

## Explanation
The function $f(x) = x^3 - 2x$ is a polynomial, so it is continuous and differentiable everywhere. The average rate of change is $(f(2) - f(0))/(2-0) = (4 - 0)/2 = 2$. Setting $f'(c) = 3c^2 - 2 = 2$ gives $c^2 = 4/3$, so $c = 2/\sqrt{3}$ (positive root only, since $c \in (0, 2)$). This value $2\sqrt{3}/3 \approx 1.155$ lies in the open interval $(0, 2)$.
