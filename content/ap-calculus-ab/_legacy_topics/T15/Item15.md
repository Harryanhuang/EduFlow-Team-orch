---
id: T15-Item15
difficulty: C
calculator: no-calc
type: frq
---
Consider the function $f(x) = x^3 - 3x + 1$ on the interval $[-2, 2]$.

(a) Show that $f$ satisfies the conditions of the Mean Value Theorem.
(b) Show that there exists exactly one value $c$ in $(0, 2)$ such that $f'(c) = (f(2) - f(-2))/4$.
(c) Using your result from part (b), determine whether $f$ is increasing or decreasing on $(0, c)$ and on $(c, 2)$. Justify your answer.

## Answer
(a) $f(x) = x^3 - 3x + 1$ is a polynomial, so it is continuous on $[-2, 2]$ and differentiable on $(-2, 2)$. MVT applies.
(b) $(f(2) - f(-2))/4 = (3 - (-1))/4 = 4/4 = 1$. So $f'(c) = 1$.
$f'(x) = 3x^2 - 3 = 3(x^2 - 1)$. Set $f'(c) = 1$: $3c^2 - 3 = 1$, $c^2 = 4/3$, $c = 2/\sqrt{3} = 2\sqrt{3}/3 \approx 1.155$.
This is the only solution in $(0, 2)$ since $f'(x) = 3(x^2 - 1)$ is strictly increasing for $x > 0$ and crosses 1 exactly once in $(0, 2)$.
(c) For $x \in (0, c)$: $x < c \approx 1.155$. Since $x^2 < 4/3$ on $(0, c)$, we have $f'(x) = 3x^2 - 3 < 0$, so $f$ is decreasing on $(0, c)$.
For $x \in (c, 2)$: $x > c$, so $x^2 > 4/3$, giving $f'(x) = 3x^2 - 3 > 0$, so $f$ is increasing on $(c, 2)$.

## Explanation
This problem combines MVT with analysis of derivative sign. By finding the unique $c$ where $f'(c)$ equals the average rate of change, we can use the structure of $f'(x) = 3(x^2 - 1)$ to determine monotonicity on either side of $c$. The turning point of $f'$ at $x = 0$ and its symmetry about $x = 0$ also reveal the critical points of $f$ at $x = \pm 1$.
