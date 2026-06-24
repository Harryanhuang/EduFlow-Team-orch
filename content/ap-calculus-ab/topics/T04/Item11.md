---
id: T04-Item11
difficulty: S
calculator: no-calc
type: mcq
---
The function $g$ is continuous on $[0, 5]$. Selected values are shown:

| $x$ | $0$ | $1$ | $3$ | $5$ |
|---|---|---|---|---|
| $g(x)$ | $-2$ | $4$ | $1$ | $6$ |

By the Intermediate Value Theorem, on which interval is $g(c) = 0$ guaranteed?

## Options
A) $(0, 1)$ only
B) $(1, 3)$ only
C) $(3, 5)$ only
D) $(0, 1)$ and $(1, 3)$

## Answer
A

## Explanation
Apply IVT on each interval:
- $(0, 1)$: $g(0) = -2 < 0 < 4 = g(1)$. IVT guarantees a zero in $(0, 1)$.
- $(1, 3)$: $g(1) = 4 > 0 > 1 = g(3)$. Wait, $1 > 0$, so $0$ is NOT between $1$ and $4$. No guarantee.
- $(3, 5)$: $g(3) = 1 > 0$ and $g(5) = 6 > 0$. Both positive, no sign change. No guarantee.

Only $(0, 1)$ is guaranteed. Answer: A.
