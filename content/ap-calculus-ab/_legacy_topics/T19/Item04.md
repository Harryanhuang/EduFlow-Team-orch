---
id: T19-Item04
difficulty: S
calculator: calc
type: frq
---

A function $f$ is continuous on $[0, 12]$. A scientist uses a midpoint Riemann sum with $n = 4$ subintervals of equal width to estimate $\\int_0^{12} f(x)\\,dx$.

The graph of $f$ is shown below. The parabola opens downward, has its vertex at $x = 6$, crosses the $x$-axis at $x = 0$ and $x = 12$, and has a maximum value of 18 at $x = 6$.

*(Note: The graph shows $f(x) \\geq 0$ on $[0, 12]$, with $f(0) = 0$, $f(6) = 18$, and $f(12) = 0$. The function is symmetric about the vertical line $x = 6$.)*

**Diagram description:**
A continuous, symmetric downward-opening parabola on the coordinate plane. The curve starts at the origin $(0, 0)$, rises to a maximum point at $(6, 18)$, then decreases back to $(12, 0)$. The area under the curve is shaded. The x-axis is labeled from 0 to 12. Gridlines are shown at integer values.

---

**(a)** Using the midpoint Riemann sum with $n = 4$ subintervals, find $M_4$, the approximation of $\\int_0^{12} f(x)\\,dx$.

**(b)** Is $M_4$ an overestimate or an underestimate of $\\int_0^{12} f(x)\\,dx$? Explain your reasoning.

**(c)** The actual value of $\\int_0^{12} f(x)\\,dx$ is 144. Find the percent error of the approximation $M_4$, to the nearest tenth of a percent.

---

## Answer

**(a)** With $n = 4$ subintervals over $[0, 12]$:
$$\\Delta x = \\frac{12-0}{4} = 3$$

The midpoints of each subinterval are: $x_1^* = 1.5$, $x_2^* = 4.5$, $x_3^* = 7.5$, $x_4^* = 10.5$

From the graph (using the symmetry and values):
- $f(1.5) \\approx 10.6$ (interpolating on the parabola)
- $f(4.5) \\approx 16.9$
- $f(7.5) \\approx 16.9$ (symmetric to $f(4.5)$)
- $f(10.5) \\approx 10.6$ (symmetric to $f(1.5)$)

$$M_4 = 3 \\cdot [f(1.5) + f(4.5) + f(7.5) + f(10.5)]$$
$$M_4 = 3 \\cdot [10.6 + 16.9 + 16.9 + 10.6]$$
$$M_4 = 3 \\cdot 55.0 = 165$$

**(b)** $M_4$ is an **overestimate** of $\\int_0^{12} f(x)\\,dx$.

**Reasoning:** The graph of $f$ is a concave down parabola (opens downward). On each subinterval, the midpoint rectangle uses the height at the midpoint of the interval. For a concave down function, the function lies **below** its tangent line at any point. Equivalently, for a concave down function, the midpoint of any chord lies above the curve.

Therefore, each midpoint rectangle has height $f(x_i^*)$ that is **greater than** the average value of $f$ on that subinterval, making $M_4$ systematically overestimate the true area under the curve.

**(c)** Percent error:
$$\\text{Percent Error} = \\left| \\frac{\\text{Approximate} - \\text{Actual}}{\\text{Actual}} \\right| \\times 100\\%$$
$$\\text{Percent Error} = \\left| \\frac{165 - 144}{144} \\right| \\times 100\\%$$
$$\\text{Percent Error} = \\left| \\frac{21}{144} \\right| \\times 100\\% \\approx 0.1458 \\times 100\\% \\approx 14.6\\%$$

## Explanation

**Part (a):** The midpoint Riemann sum formula is $M_n = \\Delta x \\sum_{i=1}^{n} f(x_i^*)$, where $x_i^*$ is the midpoint of the $i$-th subinterval. By reading approximate values from the graph (or using the equation $f(x) = 18 - \\frac{1}{2}(x-6)^2$ derived from the given information), we calculate $M_4 = 165$.

**Part (b):** For a concave down function, the midpoint rule consistently overestimates the integral. This is because the function's graph curves downward, so the midpoint of any segment lies above the actual curve on that interval. The opposite is true for concave up functions.

**Part (c):** The percent error formula compares the absolute difference between the approximation and actual value relative to the actual value. With $M_4 = 165$ and actual $= 144$, the percent error is approximately $14.6\\%$.

*Note: If using the exact parabola $f(x) = 18 - \\frac{1}{2}(x-6)^2$, we would find $f(1.5) = f(10.5) = 10.875$ and $f(4.5) = f(7.5) = 17.4375$, giving $M_4 = 3(56.625) = 169.875$ with a percent error of approximately $18.0\\%$.*
