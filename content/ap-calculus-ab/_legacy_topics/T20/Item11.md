---
id: T20-Item11
difficulty: S
calculator: no-calc
type: mcq
---
If $f$ is an even function continuous on $[-4, 4]$ and $\int_0^4 f(x) \, dx = 7$, then $\int_{-4}^0 f(x) \, dx$ equals

A) $-7$
B) $0$
C) $7$
D) $14$

## Answer
C

## Explanation
For an even function, $f(-x) = f(x)$ for all $x$ in the domain.

The property of definite integrals for even functions is:
$$\int_{-a}^a f(x) \, dx = 2\int_0^a f(x) \, dx$$

Therefore:
$$\int_{-4}^0 f(x) \, dx = \int_0^4 f(x) \, dx = 7$$

This can be verified by substitution: let $u = -x$, then $du = -dx$, and when $x = -4$, $u = 4$; when $x = 0$, $u = 0$:

$$\int_{-4}^0 f(x) \, dx = \int_4^0 f(-u)(-du) = \int_0^4 f(-u) \, du = \int_0^4 f(u) \, du = 7$$
