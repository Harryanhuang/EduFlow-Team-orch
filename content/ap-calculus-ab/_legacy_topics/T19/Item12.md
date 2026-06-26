---
id: T19-Item12
difficulty: C
calculator: calc
type: frq
---

Let $f$ be a continuous function on $[0, 4]$ with the graph of $f'$ shown below.

*(Note: The graph of f' shows: positive and increasing from (0, 1) to (1, 3), then positive and decreasing from (1, 3) to (2, 1), then negative and decreasing from (2, 1) to (3, -2), then negative and increasing from (3, -2) to (4, -1). The graph crosses the x-axis at x = 2.)*

The derivative of $f$ is shown in the figure. The graph of $y = f'(x)$ has:
- $f'(0) = 1$, $f'(1) = 3$, $f'(2) = 0$, $f'(3) = -2$, $f'(4) = -1$
- Critical points at $x = 1$ (local maximum) and $x = 2$ (zero crossing)
- $f'(x) > 0$ on $(0, 2)$ and $f'(x) < 0$ on $(2, 4)$

![Graph description: f' is positive on (0,2), reaches a maximum of 3 at x=1, and crosses the x-axis at x=2. f' is negative on (2,4), reaching a minimum of -2 at x=3, then increasing to -1 at x=4.]

**(a)** Find the values of the left, right, midpoint, and trapezoidal approximations using $n = 4$ subintervals for $\displaystyle\int_0^4 f'(x)\,dx$.

**(b)** Which of the four approximations ($L_4, R_4, M_4, T_4$) gives the best estimate of $\int_0^4 f'(x)\,dx$? Justify your answer by analyzing the behavior of $f'$ on each subinterval.

**(c)** The function $f$ satisfies $f(0) = 5$. Use your answer from part (a) to find an approximation for $f(4)$.

**(d)** Let $Q(x) = \int_0^x f'(t)\,dt$. Find $Q'(2)$ and $Q''(2)$. Explain the meaning of these values in the context of $f$.

---

## Answer

**(a)** With $n = 4$ subintervals on $[0,4]$: $\Delta x = 1$

Endpoints and midpoints:
- $x_0 = 0$, $x_1 = 1$, $x_2 = 2$, $x_3 = 3$, $x_4 = 4$
- Midpoints: $0.5, 1.5, 2.5, 3.5$

From the graph, we estimate:
- $f'(0) = 1$, $f'(1) = 3$, $f'(2) = 0$, $f'(3) = -2$, $f'(4) = -1$
- $f'(0.5) \approx 2$, $f'(1.5) \approx 2$, $f'(2.5) \approx -1$, $f'(3.5) \approx -1.5$

**Left Riemann sum:**
$$L_4 = \Delta x[f'(0) + f'(1) + f'(2) + f'(3)] = 1[1 + 3 + 0 + (-2)] = 2$$

**Right Riemann sum:**
$$R_4 = \Delta x[f'(1) + f'(2) + f'(3) + f'(4)] = 1[3 + 0 + (-2) + (-1)] = 0$$

**Midpoint Riemann sum:**
$$M_4 = \Delta x[f'(0.5) + f'(1.5) + f'(2.5) + f'(3.5)] = 1[2 + 2 + (-1) + (-1.5)] = 1.5$$

**Trapezoidal rule:**
$$T_4 = \frac{\Delta x}{2}[f'(0) + 2f'(1) + 2f'(2) + 2f'(3) + f'(4)]$$
$$T_4 = \frac{1}{2}[1 + 6 + 0 + (-4) + (-1)] = \frac{1}{2}[2] = 1$$

**(b)** To determine which estimate is best, we analyze the behavior of $f'$ on each subinterval:

**On $[0,1]$:** $f'$ is increasing ($f'' > 0$, concave up). For a concave up function:
- Left Riemann sum **underestimates**
- Right Riemann sum **overestimates**

**On $[1,2]$:** $f'$ is decreasing ($f'' < 0$, concave down). For a concave down function:
- Left Riemann sum **overestimates**
- Right Riemann sum **underestimates**

**On $[2,3]$:** $f'$ is decreasing ($f'' < 0$, concave down). For a concave down function:
- Left Riemann sum **overestimates**
- Right Riemann sum **underestimates**

**On $[3,4]$:** $f'$ is increasing ($f'' > 0$, concave up). For a concave up function:
- Left Riemann sum **underestimates**
- Right Riemann sum **overestimates**

**Error cancellation analysis:**
- $L_4$: Overestimates on $[1,2]$ and $[2,3]$, underestimates on $[3,4]$, but the overestimates may partially cancel. Since $f'$ is small on $[2,3]$, the overestimates there are not large.

- $R_4$: Underestimates on $[1,2]$, $[2,3]$, $[3,4]$, and overestimates only on $[0,1]$. Most subintervals contribute underestimates, making $R_4 = 0$ likely an **underestimate**.

- $M_4$: Generally more accurate because the midpoint samples each subinterval at a point closer to the "average" behavior. For monotonic sections it tends to be accurate; on non-monotonic sections like $[1,3]$ it captures the variation better.

- $T_4$: Generally more accurate than individual left or right sums because it averages left and right endpoints. The trapezoidal rule tends to offset over- and underestimates.

**Best estimate:** The **midpoint Riemann sum** $M_4 = 1.5$ is likely the best estimate because:
1. Midpoint rule typically has smaller error than left, right, or trapezoidal for smooth functions.
2. Unlike $L_4$ and $R_4$ which only use one endpoint per subinterval, $M_4$ uses points closer to the average value.
3. The trapezoidal rule is also reasonable, but the midpoint rule tends to be more accurate for the same number of subintervals.

**(c)** Using the Fundamental Theorem of Calculus:

$$\int_0^4 f'(x)\,dx = f(4) - f(0)$$

With $f(0) = 5$ and using $M_4 \approx 1.5$ as the best estimate for the integral:

$$f(4) - 5 \approx 1.5$$
$$f(4) \approx 6.5$$

Or using $T_4 = 1$:
$$f(4) \approx 6$$

Or using $L_4 = 2$:
$$f(4) \approx 7$$

The midpoint approximation gives $f(4) \approx 6.5$.

**(d)** 

Since $Q(x) = \int_0^x f'(t)\,dt$:

$$Q'(x) = f'(x) \quad \text{(First Fundamental Theorem)}$$
$$Q''(x) = f''(x) \quad \text{(differentiating } f' \text{)}$$

Therefore:
- $Q'(2) = f'(2) = 0$
- $Q''(2) = f''(2)$

Since $f'$ changes from increasing to decreasing at $x = 1$, $x = 1$ is where $f'' = 0$. Between $x = 1$ and $x = 2$, $f'$ is decreasing, so $f''(2) < 0$.

**Interpretation:**
- $Q'(2) = 0$ means that at $x = 2$, the rate of change of the accumulated area $Q$ is zero. Since $Q'(x) = f'(x)$, this means $f(2)$ is at a critical point (local maximum or minimum).
- $Q''(2) < 0$ means $Q$ is concave down at $x = 2$, indicating that the area accumulation is slowing down.
