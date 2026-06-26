---
id: T19-Item09
difficulty: S
calculator: calc
type: frq
---

A particle moves along a straight line with velocity $v(t)$ (in meters per second) given by the graph below for $0 \leq t \leq 8$.

*(Note: The graph shows a curve starting at (0, 2), rising to a peak at approximately (2, 8), descending through (4, 4) and (6, 0), then continuing below the x-axis to approximately (8, -6). The function is continuous and differentiable.)*

A particle moves along a line with velocity $v(t)$ (in m/s) shown in the figure.

![Velocity graph description: v(t) is above the t-axis from t=0 to t=6, with v(0)=2, v(2)=8, v(4)=4, v(6)=0. From t=6 to t=8, v(t) is negative, with v(8)=-6. The graph is continuous and smooth throughout.]

**(a)** Use a left Riemann sum with four subintervals of equal width to estimate the total distance traveled by the particle from $t=0$ to $t=8$.

**(b)** Use a right Riemann sum with four subintervals of equal width to estimate the displacement of the particle from $t=0$ to $t=8$.

**(c)** On the interval $0 \leq t \leq 6$, is the left Riemann sum an overestimate or an underestimate of the actual total distance? Explain your reasoning.

**(d)** Explain what the value $\int_6^8 v(t)\,dt$ represents in the context of the problem.

---

## Answer

**(a)** Left Riemann sum with $\Delta t = 2$:

Distance from left sum (using absolute value of velocities on $[0,6]$):

Using left endpoints on $[0,6]$:
- $[0,2]$: $v(0) = 2$, contribution to distance: $2 \times 2 = 4$
- $[2,4]$: $v(2) = 8$, contribution to distance: $8 \times 2 = 16$
- $[4,6]$: $v(4) = 4$, contribution to distance: $4 \times 2 = 8$

On $[6,8]$, velocity is negative, so distance = $-\int_6^8 v(t)\,dt$

Using left endpoint $v(6) = 0$:
Distance on $[6,8]$: $0 \times 2 = 0$ (underestimate of actual distance)

Total estimated distance $\approx 4 + 16 + 8 + 0 = 28$ meters.

**(b)** Right Riemann sum with $\Delta t = 2$:

Using right endpoints:
- $[0,2]$: $v(2) = 8$, contribution: $8 \times 2 = 16$
- $[2,4]$: $v(4) = 4$, contribution: $4 \times 2 = 8$
- $[4,6]$: $v(6) = 0$, contribution: $0 \times 2 = 0$
- $[6,8]$: $v(8) = -6$, contribution: $-6 \times 2 = -12$

Displacement $\approx 16 + 8 + 0 + (-12) = 12$ meters.

**(c)** On $[0,6]$, $v(t) > 0$ and $v(t)$ is **decreasing** (monotonically decreasing from 8 to 0). For a decreasing function, the left Riemann sum **overestimates** the true area. Since $v$ is above the $x$-axis, distance equals the area under the curve, so the left sum overestimates the true distance.

**(d)** $\int_6^8 v(t)\,dt$ represents the **displacement** (change in position) of the particle from $t=6$ to $t=8$. Since $v(t) < 0$ on this interval, this integral is negative, meaning the particle is moving in the negative direction. The value equals the area of the region below the $t$-axis between $t=6$ and $t=8$, with a negative sign.
