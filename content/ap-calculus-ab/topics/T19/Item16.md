---
id: T19-Item16
difficulty: S
calculator: calc
type: mcq
---

Let $f$ be a twice-differentiable function on $[0, 4]$ with $f(0) = 3$, $f(2) = 7$, and $f(4) = 5$. Selected values of $f'(x)$ and $f''(x)$ are shown in the tables below.

| $x$ | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| $f'(x)$ | $-1$ | 2 | 5 | 3 | 0 |

| $x$ | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| $f''(x)$ | 4 | 2 | 0 | $-3$ | $-5$ |

The trapezoidal approximation of $\int_0^4 f(x)\,dx$ using the three subintervals $[0, 2]$, $[2, 4]$ (two subintervals of equal width) is compared to the actual value of the integral. Which of the following is true?

A) The trapezoidal approximation is greater than the actual integral, and the error is at most $8$.

B) The trapezoidal approximation is greater than the actual integral, and the error is at most $4$.

C) The trapezoidal approximation is less than the actual integral, and the error is at most $8$.

D) The trapezoidal approximation is less than the actual integral, and the error is at most $4$.

## Answer
A

## Explanation
Using the trapezoidal rule with two subintervals of width $\Delta x = 2$:
$$T_2 = \frac{\Delta x}{2}\big[f(0) + 2f(2) + f(4)\big] = \frac{2}{2}[3 + 2(7) + 5] = 25$$

**Error sign:** The trapezoidal rule error depends on $f''(x)$. From the table:

- On $[0, 2]$: $f''(x)$ is positive (3, 2, 0) $\rightarrow f$ is concave **up** $\rightarrow$ trapezoids lie **above** the curve $\rightarrow$ overestimates on $[0, 2]$
- On $[2, 4]$: $f''(x)$ is negative (0, $-3$, $-5$) $\rightarrow f$ is concave **down** $\rightarrow$ trapezoids lie **below** the curve $\rightarrow$ underestimates on $[2, 4]$

Since $f''(x)$ is larger in magnitude on $[2, 4]$ ($|-5| > |4|$), the negative contribution (underestimate) on $[2, 4]$ is larger in magnitude than the positive contribution (overestimate) on $[0, 2]$, making the overall trapezoidal approximation an overestimate.

**Error bound:** The error bound for the trapezoidal rule with $n = 2$ subintervals is:
$$\left|E_T\right| \leq \frac{K(b-a)^3}{12n^2}$$

where $K$ is the maximum of $|f''(x)|$ on $[0, 4]$. From the table, the largest $|f''(x)|$ is $|-5| = 5$ (at $x = 4$), so $K = 5$.

$$\left|E_T\right| \leq \frac{5(4-0)^3}{12(2)^2} = \frac{5 \cdot 64}{48} = \frac{320}{48} = \frac{20}{3} \approx 6.67$$

Since $6.67 < 8$, the error is at most 8. The approximation is greater than the actual integral, and the error bound of 8 is valid.

**Note:** A more careful analysis could use separate $K$ values for each subinterval, but the overall bound of 8 is guaranteed and valid.
