---
id: T15-Item09
difficulty: S
calculator: calc
type: frq
---
Let $f(x) = x^4 - 4x^3 + 2$ on the interval $[-1, 4]$.

(a) Find all critical points of $f$ in $[-1, 4]$.
(b) Find the absolute maximum and absolute minimum values of $f$ on $[-1, 4]$.
(c) Does the Mean Value Theorem guarantee a value $c$ in $(-1, 4)$ such that $f'(c) = (f(4) - f(-1))/(4 - (-1))$? If so, find all such values of $c$.

## Answer
(a) $f'(x) = 4x^3 - 12x^2 = 4x^2(x - 3)$. Critical points: $x = 0$ and $x = 3$, both in $[-1, 4]$.
(b) Evaluate at critical points and endpoints:
$f(-1) = 1 + 4 + 2 = 7$
$f(0) = 2$
$f(3) = 81 - 108 + 2 = -25$
$f(4) = 256 - 256 + 2 = 2$
Absolute maximum: $f(-1) = 7$. Absolute minimum: $f(3) = -25$.
(c) Average rate of change = $(f(4) - f(-1))/(4 - (-1)) = (2 - 7)/5 = -1$.
Set $f'(c) = -1$: $4c^3 - 12c^2 = -1$, or $4c^3 - 12c^2 + 1 = 0$.
Using a calculator: $c \approx -0.272$, $c \approx 0.304$, $c \approx 2.968$. All three are in $(-1, 4)$.

## Explanation
To find absolute extrema on a closed interval: (1) find critical points where $f'(x) = 0$ or undefined, (2) evaluate $f$ at critical points and endpoints, (3) compare. For MVT, since $f$ is a polynomial (continuous and differentiable everywhere), MVT applies. The average rate of change is $-1$, and solving $f'(c) = -1$ gives three solutions in $(-1, 4)$, found using a calculator.
