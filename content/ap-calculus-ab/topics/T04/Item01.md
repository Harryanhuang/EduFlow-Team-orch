---
id: T04-Item01
difficulty: F
calculator: no-calc
type: mcq
---
Let $f(x) = x^3 - 2x - 1$. The function $f$ is continuous on the closed interval $[1, 3]$. Given that $f(1) = -2$ and $f(3) = 20$, which of the following statements is guaranteed by the Intermediate Value Theorem?

## Options
A) There exists $c \in (1, 3)$ such that $f'(c) = 0$.
B) There exists $c \in (1, 3)$ such that $f(c) = 0$.
C) There exists $c \in (1, 3)$ such that $f(c) = -3$.
D) $f$ attains its absolute maximum on $[1, 3]$ at $x = 3$.

## Answer
B

## Explanation
The Intermediate Value Theorem states that if $f$ is continuous on $[a, b]$ and $k$ is any number between $f(a)$ and $f(b)$, then there exists at least one $c \in (a, b)$ such that $f(c) = k$. Here $f(1) = -2 < 0 < 20 = f(3)$, so $k = 0$ lies between $f(1)$ and $f(3)$. Therefore, there exists $c \in (1, 3)$ such that $f(c) = 0$. Option A is the Mean Value Theorem conclusion (not IVT). Option C is false since $-3 < f(1)$, so $-3$ is not between $f(1)$ and $f(3)$. Option D concerns the Extreme Value Theorem, not IVT.
