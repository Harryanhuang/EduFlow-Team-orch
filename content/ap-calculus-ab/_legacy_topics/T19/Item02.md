---
id: T19-Item02
difficulty: F
calculator: no-calc
type: mcq
---

A function $f$ is continuous and strictly increasing on the closed interval $[0, 8]$. Selected values of $f$ are shown in the table below.

| $x$    | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|--------|---|---|---|---|---|---|---|---|---|
| $f(x)$ | 2 | 5 | 9 | 14 | 20 | 27 | 35 | 44 | 54 |

Let $L$ denote the approximation of $\\int_0^8 f(x)\\,dx$ obtained using a left Riemann sum with 8 subintervals of equal width, and let $R$ denote the approximation obtained using a right Riemann sum with 8 subintervals of equal width.

Which of the following statements is true?

A) $L = R$, because both use rectangles with the same total area

B) $L < R$, and both approximations are less than $\\int_0^8 f(x)\\,dx$

C) $L < R$, and $L$ is an underestimate while $R$ is an overestimate of $\\int_0^8 f(x)\\,dx$

D) $L < R$, and $L$ is an overestimate while $R$ is an underestimate of $\\int_0^8 f(x)\\,dx$

## Answer

C

## Explanation

Since $f$ is strictly increasing on $[0, 8]$, each left rectangle has height $f(x_{i-1})$ and falls entirely below the curve on that subinterval, while each right rectangle has height $f(x_i)$ and extends entirely above the curve.

Therefore:
- **Left Riemann sum ($L$):** Since each rectangle is below the increasing curve, $L < \\int_0^8 f(x)\\,dx$. The left sum **underestimates** the integral.

- **Right Riemann sum ($R$):** Since each rectangle is above the increasing curve, $R > \\int_0^8 f(x)\\,dx$. The right sum **overestimates** the integral.

This gives us $L < \\int_0^8 f(x)\\,dx < R$, so $L < R$.

Option A is incorrect — while both sums use rectangles of equal width, the heights differ because $f$ is strictly increasing, so $L \\neq R$.

Option B is incorrect because although $L < R$ is true, $R$ is an overestimate, not an underestimate.

Option D is incorrect because it reverses the roles of $L$ and $R$.

The correct answer is **C**: $L < R$, with $L$ underestimating and $R$ overestimating the true integral.

This result generalizes: for a monotonically increasing function on $[a, b]$, left Riemann sums always underestimate and right Riemann sums always overestimate $\\int_a^b f(x)\\,dx$. The opposite is true for monotonically decreasing functions.
