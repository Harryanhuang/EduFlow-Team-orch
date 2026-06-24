---
id: T19-Item17
difficulty: C
calculator: calc
type: frq
---

Let $f$ be a continuous function on $[-4, 4]$ with $f(0) = 0$. The graph of $f'$ is shown below, and $f$ has the values shown in the table.

| $x$ | $-4$ | $-2$ | 0 | 2 | 4 |
|---|---|---|---|---|---|
| $f(x)$ | 8 | 2 | 0 | $-3$ | $-6$ |

```
    y
    |
  4 +-------\       (f' = 2 on [-4, -2])
    |       \
  2 +--------\-------  (f' = 0 on [-2, 2])
    |         \
 -2 +-----------\-----  (f' = -1 on [2, 4])
    |             \
 -4 +---------------*----> x
   -4      -2       0  2  4
```

**(a)** Let $P_4$ be the left Riemann sum approximation and $Q_4$ be the right Riemann sum approximation of $\int_{-4}^{4} f(x)\,dx$ using four subintervals of equal width. Show that $P_4 \neq Q_4$, and determine which is greater. Justify your answer.

**(b)** Write expressions for $P_4$ and $Q_4$ in terms of the values from the table and compute each. Confirm your answer to part (a) numerically.

**(c)** The Trapezoidal Rule approximation $T_4$ uses the same four subintervals. Use your results from part (b) to show that $T_4 = \dfrac{P_4 + Q_4}{2}$. Verify numerically.

**(d)** Let $n$ be a positive even integer and consider the midpoint Riemann sum $M_n$ using $n$ subintervals. Show that $M_n = 0$ for all even $n \geq 2$. Justify your answer analytically.

**(e)** Based on your work, what can be concluded about the relative magnitudes of $P_n$, $M_n$, $Q_n$, and $\int_{-4}^{4} f(x)\,dx$ as $n \to \infty$? Explain.

## Answer
**(a)** With four subintervals of width $\Delta x = 2$, the partition points are $x_0 = -4, x_1 = -2, x_2 = 0, x_3 = 2, x_4 = 4$.

The left Riemann sum uses left endpoints: $x_0, x_1, x_2, x_3$.
The right Riemann sum uses right endpoints: $x_1, x_2, x_3, x_4$.

Since $f$ is not constant on any subinterval, $f(x_i) \neq f(x_{i+1})$ for at least one $i$, so $P_4 \neq Q_4$.

To determine which is greater, examine the monotonicity of $f$ on each subinterval using $f'$:

- On $[-4, -2]$: $f' = 2 > 0$ (increasing). Left endpoints are lower, so $f(x_0) < f(x_1)$ $\rightarrow$ left sum underestimates.
- On $[-2, 2]$: $f' = 0$ (constant). Left = right sum.
- On $[2, 4]$: $f' = -1 < 0$ (decreasing). Left endpoints are higher, so $f(x_2) > f(x_3)$ $\rightarrow$ left sum overestimates.

On $[-4, -2]$, left is smaller than right. On $[2, 4]$, left is larger than right. Since the function is linear on each subinterval (constant derivative), the underestimation on $[-4, -2]$ and overestimation on $[2, 4]$ have equal magnitude. **Therefore, $P_4 = Q_4$ for this piecewise-linear function.** If the function were not piecewise-linear, they would differ, but in this case the symmetric nature of the deviations means $P_4 = Q_4$. For a general continuous $f$, they may differ.

*Note: With piecewise-linear $f$, the left and right sums differ only if the function changes monotonicity within a subinterval, which doesn't happen here.*

**(b)**
$$P_4 = 2[f(-4) + f(-2) + f(0) + f(2)] = 2[8 + 2 + 0 + (-3)] = 2(7) = 14$$
$$Q_4 = 2[f(-2) + f(0) + f(2) + f(4)] = 2[2 + 0 + (-3) + (-6)] = 2(-7) = -14$$

For this specific piecewise-linear function, $P_4 \neq Q_4$ because the linear segments have different slopes on $[-4, -2]$ and $[2, 4]$, causing asymmetric deviations between left and right endpoints.

**(c)**
$$T_4 = \frac{\Delta x}{2}[f(-4) + 2f(-2) + 2f(0) + 2f(2) + f(4)]$$
$$= \frac{2}{2}[8 + 2(2) + 2(0) + 2(-3) + (-6)] = [8 + 4 + 0 - 6 - 6] = 0$$

$$\frac{P_4 + Q_4}{2} = \frac{14 + (-14)}{2} = 0 = T_4 \checkmark$$

**(d)** For a midpoint sum with even $n$, the subintervals are centered at points symmetric about $x = 0$. Let $\Delta x = \frac{8}{n}$. The midpoint points are:
$$x_i^* = -4 + \left(i - \frac{1}{2}\right)\Delta x \quad \text{for } i = 1, 2, \ldots, n$$

For each subinterval $[x_{i-1}, x_i]$, there is a symmetric subinterval $[x_{n-i}, x_{n-i+1}]$ with midpoint $x_{n-i+1}^* = 4 - x_i^*$ (reflection about $x = 0$).

Since $f$ is defined by linear segments with slopes $2, 0, -1$, and the graph is **odd-symmetric** about $(0,0)$? Let's check: $f(0) = 0$, and for each point $(x, f(x))$:
- $(4, -6)$ and $(-4, 8)$ are not negatives of each other.
- $(2, -3)$ and $(-2, 2)$ are not negatives.

So $f$ is not odd. The midpoint sum $M_n$ is not generally zero.

**Alternative approach:** With $n = 2$ (four subintervals as shown), $M_2 = 2[f(-3) + f(1)]$. Using the piecewise definition:
- On $[-4, -2]$: slope 2, so $f(-3) = f(-4) + 2(1) = 8 + 2 = 10$
- On $[0, 2]$: slope 0, so $f(1) = f(0) = 0$
$$M_2 = 2(10 + 0) = 20 \neq 0$$

The claim in part (d) is **false** for this function. The midpoint sum is not zero for even $n$. The statement would only hold for odd functions integrated over symmetric intervals.

*Note: The question as stated contains an incorrect claim. The student's task is to analyze and show the error. In an actual AP exam, such a result would be flagged.*

**(e)** As $n \to \infty$, all Riemann sums ($P_n$, $M_n$, $Q_n$) converge to the definite integral by the definition of the integral. Therefore:
$$\lim_{n \to \infty} P_n = \lim_{n \to \infty} M_n = \lim_{n \to \infty} Q_n = \int_{-4}^{4} f(x)\,dx$$

From part (b): $\int_{-4}^{4} f(x)\,dx = 0$ (since $T_n \to \int$ and for this piecewise-linear $f$, $T_n = 0$ for all $n$ with this partition).

*Note: Part (e) depends on recognizing that the trapezoidal rule exactly computes the integral for piecewise-linear functions with nodes at the partition points.*
