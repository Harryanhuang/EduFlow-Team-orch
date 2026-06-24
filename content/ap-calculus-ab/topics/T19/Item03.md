---
id: T19-Item03
difficulty: S
calculator: calc
type: mcq
---

The function $f$ is continuous on $[0, 6]$. Values of $f$ at equally spaced points are shown in the table below.

| $x$    | 0   | 1   | 2   | 3   | 4   | 5   | 6   |
|--------|-----|-----|-----|-----|-----|-----|-----|
| $f(x)$ | 3.2 | 4.8 | 5.9 | 6.2 | 5.8 | 4.3 | 2.7 |

Using the trapezoidal rule with $n = 6$ subintervals, which of the following approximations equals $\\int_0^6 f(x)\\,dx$?

A) $3.2 + 4.8 + 5.9 + 6.2 + 5.8 + 4.3$

B) $1(4.8 + 5.9 + 6.2 + 5.8 + 4.3 + 2.7)$

C) $\\dfrac{1}{2}(3.2 + 2 \\cdot 4.8 + 2 \\cdot 5.9 + 2 \\cdot 6.2 + 2 \\cdot 5.8 + 2 \\cdot 4.3 + 2.7)$

D) $\\dfrac{1}{2}(3.2 + 4.8 + 5.9 + 6.2 + 5.8 + 4.3 + 2.7)$

## Answer

C

## Explanation

The trapezoidal rule with $n$ subintervals of equal width $\\Delta x$ over $[a, b]$ is:

$$T_n = \\frac{\\Delta x}{2}\\left[f(x_0) + 2f(x_1) + 2f(x_2) + \\cdots + 2f(x_{n-1}) + f(x_n)\\right]$$

Here, $n = 6$ subintervals over $[0, 6]$, so $\\Delta x = \\frac{6-0}{6} = 1$.

The formula becomes:
$$T_6 = \\frac{1}{2}\\left[f(0) + 2f(1) + 2f(2) + 2f(3) + 2f(4) + 2f(5) + f(6)\\right]$$

Substituting the values from the table:
$$T_6 = \\frac{1}{2}\\left[3.2 + 2(4.8) + 2(5.9) + 2(6.2) + 2(5.8) + 2(4.3) + 2.7\\right]$$

This matches option **C**.

Option A is simply the sum of the interior function values — it doesn't account for the trapezoidal weighting.

Option B is the right Riemann sum (using the right endpoint of each subinterval), not the trapezoidal rule.

Option D is the midpoint rule (simple average of all values), which is not the trapezoidal approximation.

Computing the numerical value:
$$T_6 = \\frac{1}{2}[3.2 + 9.6 + 11.8 + 12.4 + 11.6 + 8.6 + 2.7] = \\frac{1}{2}[59.9] = 29.95$$
