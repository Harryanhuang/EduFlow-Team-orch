---
id: T04-Item06
difficulty: S
calculator: no-calc
type: mcq
---
The function $f$ is continuous on $[0, 4]$. Selected values of $f$ are shown in the table:

| $x$ | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| $f(x)$ | $-3$ | $1$ | $-2$ | $5$ | $0$ |

What is the least number of times the equation $f(x) = 0$ is guaranteed to have a solution on $[0, 4]$ by the Intermediate Value Theorem?

## Options
A) 1
B) 2
C) 3
D) 4

## Answer
C

## Explanation
Apply IVT on each subinterval where $f$ changes sign:
- On $[0, 1]$: $f(0) = -3 < 0 < 1 = f(1)$, so at least one root.
- On $[1, 2]$: $f(1) = 1 > 0 > -2 = f(2)$, so at least one root.
- On $[2, 3]$: $f(2) = -2 < 0 < 5 = f(3)$, so at least one root.
- On $[3, 4]$: $f(3) = 5 > 0 = f(4)$. Since $f(4) = 0$ exactly, $x = 4$ is a root. However, IVT guarantees a root strictly between endpoints only when the target value is strictly between $f(a)$ and $f(b)$. Here $f(4) = 0$ is already a root.

So IVT guarantees 3 roots in the open intervals $(0,1)$, $(1,2)$, $(2,3)$, plus $x = 4$ is itself a root. The minimum number guaranteed by sign changes alone is 3.
