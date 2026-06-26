---
id: T19-Item10
difficulty: S
calculator: calc
type: mcq
---

The function $f$ is continuous on $[0, 12]$ and values of $f$ at selected points are shown in the table below.

| $x$ | 0 | 2 | 4 | 6 | 8 | 10 | 12 |
|-----|------|------|------|------|------|------|------|
| $f(x)$ | 3.2 | 4.8 | 5.1 | 4.3 | 3.7 | 4.2 | 5.0 |

Using the trapezoidal rule with $n = 6$ subintervals, what is the approximation of $\displaystyle\int_0^{12} f(x)\,dx$?

A) $47.2$
B) $50.4$
C) $52.8$
D) $55.2$

## Answer

B

## Explanation

The trapezoidal rule with $n$ subintervals of equal width $\Delta x$ is:

$$T_n = \frac{\Delta x}{2}\left[f(x_0) + 2f(x_1) + 2f(x_2) + \cdots + 2f(x_{n-1}) + f(x_n)\right]$$

Here: $a = 0$, $b = 12$, $n = 6$, so $\Delta x = \frac{12-0}{6} = 2$

$$T_6 = \frac{2}{2}\left[3.2 + 2(4.8) + 2(5.1) + 2(4.3) + 2(3.7) + 2(4.2) + 5.0\right]$$

$$T_6 = 1 \times \left[3.2 + 9.6 + 10.2 + 8.6 + 7.4 + 8.4 + 5.0\right]$$

$$T_6 = 3.2 + 9.6 + 10.2 + 8.6 + 7.4 + 8.4 + 5.0 = 50.4$$

The correct answer is **B**.

*Note: Without additional information about the concavity of $f$, we cannot determine whether this is an over- or underestimate.*
