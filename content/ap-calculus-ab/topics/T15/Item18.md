---
id: T15-Item18
difficulty: C
calculator: calc
type: frq
---
Consider $f(x) = \begin{cases} x^3 & \text{if } 0 \le x \le 1 \\ 2x - x^2 & \text{if } 1 < x \le 3 \end{cases}$

(a) Is $f$ continuous at $x = 1$? Show your work.
(b) Does the Mean Value Theorem apply to $f$ on $[0, 3]$? Justify your answer.
(c) If MVT applies, find all values $c$ in $(0, 3)$ such that $f'(c) = (f(3) - f(0))/(3 - 0)$.
(d) Find the absolute maximum and absolute minimum of $f$ on $[0, 3]$, or state that they do not exist.

## Answer
(a) $\lim_{x \to 1^-} f(x) = 1^3 = 1$, $\lim_{x \to 1^+} f(x) = 2(1) - 1^2 = 1$, $f(1) = 1$. Since all three match, $f$ is continuous at $x = 1$.
(b) MVT requires differentiability on the open interval $(0, 3)$. At $x = 1$, $f$ is continuous but we must check differentiability.
Left derivative at 1: $\lim_{h \to 0^+} (f(1+h) - f(1))/h = \lim ( (1+h)^3 - 1 )/h = 3$.
Right derivative at 1: $\lim_{h \to 0^+} (f(1+h) - f(1))/h = \lim ( 2(1+h) - (1+h)^2 - 1 )/h = \lim (2 + 2h - 1 - 2h - h^2 - 1)/h = \lim (-h^2)/h = 0$.
Since $3 \neq 0$, $f$ is not differentiable at $x = 1$. MVT does NOT apply on $[0, 3]$.
(c) Since MVT does not apply, we cannot guarantee such a $c$. However, we can check if any $c$ satisfies $f'(c) = 1$ (the average rate of change):
$(f(3) - f(0))/3 = (6 - 9 - 0)/3 = -3/3 = -1$.
For $x \in [0, 1]$: $f'(x) = 3x^2 \ge 0$, no solution equals $-1$.
For $x \in (1, 3]$: $f'(x) = 2 - 2x = -1$ when $x = 1.5$. $1.5 \in (1, 3)$.
So $c = 1.5$ satisfies $f'(c) = -1$, even though MVT does not strictly apply.
(d) Evaluate at critical points (where $f' = 0$ or undefined):
On $[0, 1]$: $f'(x) = 3x^2$, critical at $x = 0$. $f(0) = 0$.
On $(1, 3]$: $f'(x) = 2 - 2x = 0$ at $x = 1$. Endpoint $x = 3$: $f(3) = 6 - 9 = -3$.
Evaluate: $f(0) = 0$, $f(1) = 1$, $f(1.5) = 3 - 2.25 = 0.75$, $f(3) = -3$.
Absolute maximum: $f(1) = 1$. Absolute minimum: $f(3) = -3$.

## Explanation
This problem explores a piecewise function where the MVT hypothesis fails at the boundary between pieces (differentiable nowhere at $x = 1$). Despite this, we can still analyze absolute extrema by examining critical points and endpoints. The function attains its maximum at the "corner" $x = 1$ and its minimum at $x = 3$.
