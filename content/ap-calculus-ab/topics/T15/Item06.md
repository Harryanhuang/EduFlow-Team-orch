---
id: T15-Item06
difficulty: S
calculator: no-calc
type: mcq
---
The table gives values of a differentiable function $f$ at selected points.

| $x$ | 0 | 2 | 5 | 8 | 10 |
|------|---|---|---|---|----|
| $f(x)$ | 3 | 7 | 4 | 10 | 6 |

What is the smallest number of values $c$ in $(0, 10)$ that must satisfy $f'(c) = 0$?

## Options
A) 0
B) 1
C) 2
D) 3

## Answer
C) 2

## Explanation
Since $f$ is differentiable (hence continuous), we apply Rolle's Theorem on subintervals where $f$ takes the same value. Note $f(0) = 3$ and $f(5) = 4$ and $f(10) = 6$ — none equal. But $f(0) = 3$, $f(2) = 7$, $f(5) = 4$. By the Intermediate Value Theorem, since $f$ is continuous, there exists some $a$ in $(0, 2)$ where $f(a) = 4$ (since $f(0) = 3 < 4 < 7 = f(2)$). Since $f(a) = f(5) = 4$ with $a \in (0, 2)$ and $5 > 2$, by Rolle's Theorem there is at least one $c_1$ in $(a, 5)$ where $f'(c_1) = 0$.

Also, $f(5) = 4 < 6 = f(10)$ and $f(2) = 7 > 6$. By IVT, some $b$ in $(2, 5)$ has $f(b) = 6 = f(10)$. By Rolle's Theorem, there is at least one $c_2$ in $(b, 10)$ where $f'(c_2) = 0$.

Thus at least 2 values of $c$ must satisfy $f'(c) = 0$.
