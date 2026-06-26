---
id: T20-Item03
difficulty: F
calculator: no-calc
type: mcq
---
Let $f$ be a continuous function. Which of the following is equal to $\int_0^5 f(x) \, dx + \int_5^{10} f(x) \, dx$?

A) $\int_0^{10} f(x) \, dx$
B) $\int_0^5 f(x) \, dx - \int_{10}^5 f(x) \, dx$
C) $2\int_0^5 f(x) \, dx$
D) $\int_0^{10} |f(x)| \, dx$

## Answer
A

## Explanation
By the additivity property of definite integrals, if $f$ is continuous on $[a, b]$ and $c$ is between $a$ and $b$, then:
$$\int_a^b f(x) \, dx = \int_a^c f(x) \, dx + \int_c^b f(x) \, dx$$

With $a = 0$, $b = 10$, and $c = 5$:
$$\int_0^{10} f(x) \, dx = \int_0^5 f(x) \, dx + \int_5^{10} f(x) \, dx$$

Therefore, the given sum equals $\int_0^{10} f(x) \, dx$.
