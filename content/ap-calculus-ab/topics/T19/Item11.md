---
id: T19-Item11
difficulty: C
calculator: calc
type: frq
---

The function $f$ is continuous on $[1, 9]$. A graph of $f$ is shown below.

*(Note: The graph shows f(x) starting at (1, 7), decreasing to a local minimum at approximately (3, 2), then increasing to a local maximum at approximately (6, 8), and finally decreasing to (9, 3). The function is above the x-axis throughout.)*

A continuous function $f$ is defined on $[1, 9]$. The graph of $y = f(x)$ has:
- A local minimum at $x = 3$ with $f(3) = 2$
- A local maximum at $x = 6$ with $f(6) = 8$
- $f(1) = 7$, $f(9) = 3$

![Graph description: f is above the x-axis on [1,9]. From x=1 to x=3, f decreases from 7 to 2. From x=3 to x=6, f increases from 2 to 8. From x=6 to x=9, f decreases from 8 to 3. The function is continuous and smooth with no sharp corners.]

**(a)** Use a midpoint Riemann sum with four subintervals of equal width to estimate $\displaystyle\int_1^9 f(x)\,dx$.

**(b)** Is your estimate from part (a) guaranteed to be an overestimate or an underestimate? Explain, referencing the concavity of $f$ on each subinterval.

**(c)** Let $g(x) = \int_1^x f(t)\,dt$ for $1 \leq x \leq 9$. Find $g'(6)$ and explain what this value represents in the context of the original problem.

**(d)** Use the Fundamental Theorem of Calculus to find the average value of $f$ on $[1, 9]$ in terms of $g(9)$.

---

## Answer

**(a)** Midpoint Riemann sum with $n=4$ subintervals on $[1,9]$:

$\Delta x = \frac{9-1}{4} = 2$

Midpoints: $x_1^* = 2$, $x_2^* = 4$, $x_3^* = 6$, $x_4^* = 8$

Midpoint Riemann sum:
$$M_4 = 2[f(2) + f(4) + f(6) + f(8)]$$

From the graph (values estimated from the sketch):
- $f(2) \approx 4.5$ (midway between 7 at $x=1$ and 2 at $x=3$)
- $f(4) \approx 5$ (midway between 2 at $x=3$ and 8 at $x=6$)
- $f(6) = 8$ (given)
- $f(8) \approx 5.5$ (midway between 8 at $x=6$ and 3 at $x=9$)

$$M_4 \approx 2[4.5 + 5 + 8 + 5.5] = 2(23) = 46$$

**(b)** To determine if the midpoint sum over- or underestimates, we analyze concavity on each subinterval:

- On $[1,3]$: $f$ is decreasing, and the graph is **concave up** (it's a decreasing curve that bends upward toward the minimum at $x=3$). Midpoint rule **underestimates** area when $f'' > 0$.

- On $[3,6]$: $f$ is increasing, and the graph is **concave up** (the increasing curve is bending upward toward the maximum at $x=6$). Midpoint rule **underestimates** area when $f'' > 0$.

- On $[6,9]$: $f$ is decreasing, and the graph is **concave down** (decreasing curve bending downward). Midpoint rule **overestimates** area when $f'' < 0$.

Since $f$ is concave up on $[1,6]$ (where most of the area is) and concave down only on $[6,9]$, the midpoint sum is **more likely an underestimate**, but we cannot guarantee this without exact values. The error on $[6,9]$ could offset the underestimates on $[1,6]$, or the magnitude of the error could favor either conclusion.

*Note: A rigorous justification requires knowing the exact concavity on each subinterval. Based on the visual description provided, the midpoint rule generally underestimates on concave-up intervals, which comprise $[1,6]$.*

**(c)** By the Fundamental Theorem of Calculus:

$$g'(x) = f(x)$$

Therefore:
$$g'(6) = f(6) = 8$$

This value represents the **instantaneous rate of change** of the accumulated area function $g$ at $x = 6$. In context, it represents the value of $f$ at $x = 6$. Since $g(x) = \int_1^x f(t)\,dt$ represents the area under $f$ from $1$ to $x$, $g'(6) = 8$ tells us that at $x = 6$, the area is increasing at a rate of $8$ square units per unit increase in $x$.

**(d)** The average value of $f$ on $[1, 9]$ is:

$$\text{Average value} = \frac{1}{9-1}\int_1^9 f(x)\,dx = \frac{1}{8}\int_1^9 f(x)\,dx = \frac{1}{8}\,g(9)$$

Since $g(9) = \int_1^9 f(x)\,dx$, the average value is $\dfrac{g(9)}{8}$.
