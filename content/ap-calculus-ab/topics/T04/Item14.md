---
id: T04-Item14
difficulty: C
calculator: no-calc
type: frq
---
Let $f(x) = e^x - 2x - 2$.

(a) Show that the equation $f(x) = 0$ has at least one solution on $[0, 2]$.
(b) Show that the equation $f(x) = 0$ has at least one solution on $[-2, 0]$.
(c) Determine the exact number of solutions $f(x) = 0$ has on $\mathbb{R}$. Justify.

## Answer
(a) $f(0) = 1 - 0 - 2 = -1 < 0$ and $f(2) = e^2 - 4 - 2 = e^2 - 6 \approx 7.389 - 6 > 0$. By IVT, since $f$ is continuous and $f(0) < 0 < f(2)$, there exists $c \in (0, 2)$ such that $f(c) = 0$.

(b) $f(-2) = e^{-2} + 4 - 2 = e^{-2} + 2 > 0$ and $f(0) = -1 < 0$. By IVT, since $f$ is continuous and $f(-2) > 0 > f(0)$, there exists $c \in (-2, 0)$ such that $f(c) = 0$.

(c) Exactly 2 solutions. Since $f'(x) = e^x - 2$, we have $f'(x) = 0$ when $e^x = 2$, i.e., $x = \ln 2$. For $x < \ln 2$, $f'(x) < 0$ (decreasing); for $x > \ln 2$, $f'(x) > 0$ (increasing). So $f$ has exactly one critical point and decreases then increases. By the behavior established in parts (a) and (b), there is one root in $(-2, 0)$ and one root in $(0, 2)$, and since $f$ is monotonic on $(-\infty, \ln 2)$ and $(\ln 2, \infty)$, there can be at most one root in each interval. Thus exactly 2 solutions.
