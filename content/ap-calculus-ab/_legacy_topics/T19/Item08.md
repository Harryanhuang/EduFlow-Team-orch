---
id: T19-Item08
difficulty: F
calculator: no-calc
type: mcq
---

Let $f$ be a continuous function on $[-3,5]$ with $\int_{-3}^5 f(x)\,dx = 12$ and $\int_{-3}^1 f(x)\,dx = -4$. What is the area of the region bounded by $y=f(x)$ and the $x$-axis on $[1,5]$?

A) $4$
B) $8$
C) $16$
D) $20$

## Answer

C

## Explanation

The definite integral $\int_a^b f(x)\,dx$ gives the **signed area** (positive above the $x$-axis, negative below).

Given:
- $\int_{-3}^5 f(x)\,dx = 12$ (total signed area)
- $\int_{-3}^1 f(x)\,dx = -4$ (signed area from $-3$ to $1$, below axis)

Using additivity of integrals:
$$\int_{-3}^5 f(x)\,dx = \int_{-3}^1 f(x)\,dx + \int_1^5 f(x)\,dx$$

$$12 = (-4) + \int_1^5 f(x)\,dx$$

$$\int_1^5 f(x)\,dx = 16$$

Since the integral from $-3$ to $5$ is positive (net area above axis), and the portion from $-3$ to $1$ is negative (below axis), the portion from $1$ to $5$ must be positive. Therefore, the area on $[1,5]$ is $16$.

The correct answer is **C**.
