---
id: T16-Item17
difficulty: C
calculator: calc
type: frq
---
The function $f$ is continuous and differentiable on all real numbers. The table below gives values of $f'(x)$ at selected points.

| $x$ | $-3$ | $-2$ | $-1$ | $0$ | $1$ | $2$ | $3$ |
|-----|------|------|------|-----|-----|-----|-----|
| $f'(x)$ | $-4$ | $-1$ | $0$ | $1$ | $3$ | $0$ | $-2$ |

Assume $f'(x)$ is linear between the given data points.

(a) Find the critical points of $f$ on $[-3, 3]$.
(b) On what subinterval(s) of $[-3, 3]$ is $f$ increasing? Justify.
(c) On what subinterval(s) of $[-3, 3]$ is $f$ decreasing? Justify.
(d) Find the $x$-coordinates of all local extrema of $f$ on $[-3, 3]$ and classify each.
(e) What is the absolute maximum value of $f$ on $[-3, 3]$? Justify.

## Answer
(a) Critical points: $x = -1$ and $x = 2$.
(b) $f$ is increasing on $(-1, 2)$. Since $f'(x) > 0$ for all $x$ in $(-1, 2)$ (values $1$ and $3$ are positive, and by linear interpolation $f' > 0$ throughout), $f$ is increasing.
(c) $f$ is decreasing on $(-3, -1)$ and $(2, 3)$. On $(-3, -1)$, $f'(x) < 0$ (values $-4$ and $-1$ are negative, and linear interpolation preserves sign). On $(2, 3)$, $f'(x) < 0$ (values $0$ and $-2$; interpolation gives $f' < 0$ for $x > 2$).
(d) Local minimum at $x = -1$ (derivative changes from negative to positive). Local maximum at $x = 2$ (derivative changes from positive to negative).
(e) Since $f$ is decreasing on $(-3, -1]$ and increasing on $[2, 3)$, the absolute maximum on $[-3, 3]$ occurs at $x = 2$ (one of the endpoints of the increasing region). Since no endpoint value is given, the answer is $f(2)$, which is greater than $f(3)$ and $f(-3)$.

## Explanation
The critical points come directly from the table where $f'(x) = 0$: $x = -1$ and $x = 2$. The sign of $f'$ between critical points is determined by the table values and the fact that $f'$ is linear between known points.
