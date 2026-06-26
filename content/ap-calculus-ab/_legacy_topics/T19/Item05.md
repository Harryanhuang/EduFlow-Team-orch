---
id: T19-Item05
difficulty: C
calculator: calc
type: frq
---

A particle moves along the $x$-axis. Its velocity at time $t$ (in seconds) is given by $v(t) = 3t^2 - 2t$ for $0 \\leq t \\leq 5$, where $v(t)$ is measured in meters per second.

**Diagram description:**
A coordinate plane showing the velocity function $v(t) = 3t^2 - 2t$. The graph is a parabola opening upward, crossing the t-axis at $t = 0$ and $t = \\frac{2}{3}$. Between $t = 0$ and $t = \\frac{2}{3}$, the velocity is negative (particle moving left). Between $t = \\frac{2}{3}$ and $t = 5$, the velocity is positive (particle moving right). The graph has a minimum at $t = \\frac{1}{3}$ with value $v(\\frac{1}{3}) = -\\frac{1}{3}$.

---

**(a)** Write a Riemann sum that represents the position of the particle at time $t = 5$, given that the initial position is $s(0) = 0$. Your answer should be in sigma notation.

**(b)** Use the Riemann sum from part (a) with $n = 10$ subintervals of equal width to approximate the position $s(5)$. Show the setup for your calculation.

**(c)** The actual position of the particle at $t = 5$ is $s(5) = 57.5$ meters. What is the percent error of your approximation in part (b)? Round your answer to the nearest tenth of a percent.

**(d)** Find $\\int_0^5 |v(t)|\\,dt$ and interpret this value in the context of the particle's motion.

---

## Answer

**(a)** The position function is the antiderivative of velocity:
$$s(t) = s(0) + \\int_0^t v(x)\\,dx = \\int_0^t (3x^2 - 2x)\\,dx$$

Using a Riemann sum with $n$ subintervals:
$$\\int_0^5 v(t)\\,dt \\approx \\sum_{i=1}^{n} v(t_i^*) \\Delta t$$

where $\\Delta t = \\frac{5-0}{n} = \\frac{5}{n}$ and $t_i^*$ is a sample point in the $i$-th subinterval.

For the position at $t = 5$:
$$s(5) \\approx \\sum_{i=1}^{n} v\\left(\\frac{5i}{n}\\right) \\cdot \\frac{5}{n}$$

Using right endpoints, the Riemann sum is:
$$\\sum_{i=1}^{n} \\left[3\\left(\\frac{5i}{n}\\right)^2 - 2\\left(\\frac{5i}{n}\\right)\\right] \\cdot \\frac{5}{n} = \\sum_{i=1}^{n} \\left(\\frac{375i^2}{n^3} - \\frac{50i}{n^2}\\right)$$

**(b)** With $n = 10$:
$$\\Delta t = \\frac{5}{10} = 0.5$$

Using right endpoints, $t_i = 0.5i$ for $i = 1, 2, \\ldots, 10$:

| $i$ | $t_i$ | $v(t_i) = 3t_i^2 - 2t_i$ |
|-----|-------|--------------------------|
| 1   | 0.5   | $3(0.25) - 2(0.5) = 0.75 - 1.00 = -0.25$ |
| 2   | 1.0   | $3(1) - 2(1) = 3 - 2 = 1.00$ |
| 3   | 1.5   | $3(2.25) - 2(1.5) = 6.75 - 3.00 = 3.75$ |
| 4   | 2.0   | $3(4) - 2(2) = 12 - 4 = 8.00$ |
| 5   | 2.5   | $3(6.25) - 2(2.5) = 18.75 - 5.00 = 13.75$ |
| 6   | 3.0   | $3(9) - 2(3) = 27 - 6 = 21.00$ |
| 7   | 3.5   | $3(12.25) - 2(3.5) = 36.75 - 7.00 = 29.75$ |
| 8   | 4.0   | $3(16) - 2(4) = 48 - 8 = 40.00$ |
| 9   | 4.5   | $3(20.25) - 2(4.5) = 60.75 - 9.00 = 51.75$ |
| 10  | 5.0   | $3(25) - 2(5) = 75 - 10 = 65.00$ |

$$s(5) \\approx 0.5 \\cdot \\sum_{i=1}^{10} v(t_i) = 0.5 \\cdot (-0.25 + 1.00 + 3.75 + 8.00 + 13.75 + 21.00 + 29.75 + 40.00 + 51.75 + 65.00)$$
$$s(5) \\approx 0.5 \\cdot 233.75 = 116.875 \\text{ meters}$$

**(c)** Percent error:
$$\\text{Percent Error} = \\left| \\frac{116.875 - 57.5}{57.5} \\right| \\times 100\\% = \\left| \\frac{59.375}{57.5} \\right| \\times 100\\% \\approx 103.3\\%$$

**(d)** $\\int_0^5 |v(t)|\\,dt$ represents the **total distance traveled** (not net displacement).

Finding the integral:
$$\\int_0^5 |v(t)|\\,dt = \\int_0^{2/3} -(3t^2 - 2t)\\,dt + \\int_{2/3}^5 (3t^2 - 2t)\\,dt$$

Since $v(t) = 3t^2 - 2t = t(3t - 2)$ is negative on $(0, 2/3)$ and positive on $(2/3, 5)$:

$$\\int_0^{2/3} -(3t^2 - 2t)\\,dt = -\\left[t^3 - t^2\\right]_0^{2/3} = -\\left[\\frac{8}{27} - \\frac{4}{9}\\right] = -\\left[\\frac{8 - 12}{27}\\right] = \\frac{4}{27}$$

$$\\int_{2/3}^5 (3t^2 - 2t)\\,dt = \\left[t^3 - t^2\\right]_{2/3}^5 = (125 - 25) - \\left(\\frac{8}{27} - \\frac{4}{9}\\right) = 100 - \\frac{8 - 12}{27} = 100 + \\frac{4}{27} = \\frac{2704}{27}$$

$$\\int_0^5 |v(t)|\\,dt = \\frac{4}{27} + \\frac{2704}{27} = \\frac{2708}{27} \\approx 100.296 \\text{ meters}$$

**Interpretation:** The particle travels approximately 100.3 meters total, but its net displacement is only 57.5 meters because it first moved 4/27 meters to the left before moving significantly to the right.

## Explanation

**Part (a):** The fundamental theorem connects velocity and position: $s(t) = s(0) + \\int_0^t v(x)\\,dx$. Writing this as a Riemann sum demonstrates understanding of the limit definition of the definite integral.

**Part (b):** The calculation uses right endpoints. Note that the first term ($v(0.5) = -0.25$) is negative, representing leftward motion. The sum of all velocity values (weighted by $\\Delta t$) gives net displacement.

**Part (c):** The large error (103.3%) occurs because $n = 10$ is insufficient for this rapidly-changing cubic velocity function. Increasing $n$ would improve the approximation.

**Part (d):** This part distinguishes between **net displacement** $\\int v(t)\\,dt$ and **total distance** $\\int |v(t)|\\,dt$. The particle reverses direction at $t = 2/3$ (when $v(t) = 0$), so the integral must be split to account for negative velocity (leftward motion).
