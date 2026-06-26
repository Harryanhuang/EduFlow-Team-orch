---
id: T19-Item06
difficulty: C
calculator: calc
type: frq
---

The function $f$ is continuous on $[-2, 4]$. The graph of $f$ consists of two line segments and a semicircle, as described below.

**Diagram description:**
A coordinate plane with x-axis ranging from -2 to 4 and y-axis ranging from -4 to 6. The graph of $f$ consists of:

1. A line segment from $(-2, 4)$ to $(0, -2)$. This line passes through points and has a slope of $\frac{-2-4}{0-(-2)} = -3$, so the equation is $f(x) = -3x - 2$.

2. A semicircle centered at $(2, 0)$ with radius 2, from $x = 0$ to $x = 4$. The upper half of the semicircle: $f(x) = \sqrt{4 - (x-2)^2}$. This portion is above the x-axis and reaches a maximum of $f(2) = 2$.

The graph is continuous at $x = 0$ (both pieces equal $-2$), and at $x = 4$ the semicircle meets the x-axis.

---

**(a)** Write expressions for $L$, $R$, and $T$ that approximate $\\int_{-2}^4 f(x)\\,dx$ using $n = 6$ subintervals of equal width. Evaluate each approximation.

**(b)** The actual value of $\\int_{-2}^4 f(x)\\,dx$ is $\\pi + 2$. Determine which of $L$, $R$, or $T$ is the best approximation. Justify your answer.

**(c)** Find $\\int_{-2}^4 |f(x)|\\,dx$ and interpret this value geometrically.

**(d)** Let $g(x) = \\int_{-2}^x f(t)\\,dt$. Find $g'(2)$ and explain what $g'(2)$ represents in the context of this problem.

---

## Answer

**(a)** With $n = 6$ subintervals over $[-2, 4]$:
$$\\Delta x = \\frac{4 - (-2)}{6} = \\frac{6}{6} = 1$$

The partition points are: $x_0 = -2$, $x_1 = -1$, $x_2 = 0$, $x_3 = 1$, $x_4 = 2$, $x_5 = 3$, $x_6 = 4$

The function values at partition points (using $f(x) = -3x - 2$ for $x < 0$ and $f(x) = \\sqrt{4-(x-2)^2}$ for $x \\geq 0$):

| $x_i$ | $f(x_i)$ | Calculation |
|-------|----------|-------------|
| $-2$  | $4$      | $-3(-2) - 2 = 6 - 2 = 4$ |
| $-1$  | $1$      | $-3(-1) - 2 = 3 - 2 = 1$ |
| $0$   | $-2$     | Semicircle value: $\\sqrt{4-4} = 0$, but also $f(0) = -3(0) - 2 = -2$ (continuous) |
| $1$   | $\\sqrt{3} \\approx 1.732$ | $\\sqrt{4-1} = \\sqrt{3}$ |
| $2$   | $2$      | $\\sqrt{4-0} = 2$ |
| $3$   | $\\sqrt{3} \\approx 1.732$ | $\\sqrt{4-1} = \\sqrt{3}$ |
| $4$   | $0$      | $\\sqrt{4-4} = 0$ |

**Left Riemann sum:**
$$L = \\Delta x \\cdot [f(x_0) + f(x_1) + f(x_2) + f(x_3) + f(x_4) + f(x_5)]$$
$$L = 1 \\cdot [4 + 1 + (-2) + \\sqrt{3} + 2 + \\sqrt{3}]$$
$$L = 5 + 2\\sqrt{3} \\approx 5 + 3.464 = 8.464$$

**Right Riemann sum:**
$$R = \\Delta x \\cdot [f(x_1) + f(x_2) + f(x_3) + f(x_4) + f(x_5) + f(x_6)]$$
$$R = 1 \\cdot [1 + (-2) + \\sqrt{3} + 2 + \\sqrt{3} + 0]$$
$$R = 1 + 2\\sqrt{3} \\approx 1 + 3.464 = 4.464$$

**Trapezoidal rule:**
$$T = \\frac{\\Delta x}{2} \\cdot [f(x_0) + 2f(x_1) + 2f(x_2) + 2f(x_3) + 2f(x_4) + 2f(x_5) + f(x_6)]$$
$$T = \\frac{1}{2}[4 + 2(1) + 2(-2) + 2\\sqrt{3} + 2(2) + 2\\sqrt{3} + 0]$$
$$T = \\frac{1}{2}[4 + 2 - 4 + 2\\sqrt{3} + 4 + 2\\sqrt{3}]$$
$$T = \\frac{1}{2}[6 + 4\\sqrt{3}] = 3 + 2\\sqrt{3} \\approx 3 + 3.464 = 6.464$$

**(b)** The actual value is $\\pi + 2 \\approx 3.142 + 2 = 5.142$.

Comparing:
- $L \\approx 8.464$ (error: $+3.322$)
- $R \\approx 4.464$ (error: $-0.678$)
- $T \\approx 6.464$ (error: $+1.322$)

The **right Riemann sum $R$** is the best approximation because:

1. The function $f$ changes concavity on $[-2, 4]$ (from linear/decreasing to semicircular/concave down), so no single approximation method guarantees the most accuracy.

2. However, $R$ is closest to the actual value. We can also analyze this: on $[-2, -1]$, $f$ is linear and decreasing, so the left rectangle overestimates and right underestimates. On $[-1, 0]$, again linear and decreasing. On $[0, 2]$, the semicircle is concave down, so both left and right rectangles underestimate, but right is less of an underestimate. On $[2, 4]$, the semicircle continues to decrease.

3. Given the actual value of $\\pi + 2 \\approx 5.142$, the right sum $R \\approx 4.464$ has the smallest absolute error.

**(c)** Finding $\\int_{-2}^4 |f(x)|\\,dx$:

The semicircle portion $f(x) = \\sqrt{4-(x-2)^2}$ is always nonnegative on $[0, 4]$. The linear segment from $(-2, 4)$ to $(0, -2)$ crosses the x-axis at $x = -\\frac{2}{3}$, so it is positive on $[-2, -\\frac{2}{3})$ and negative on $[-\\frac{2}{3}, 0)$.

So $|f(x)| = \\begin{cases} -f(x) = 3x + 2 & \\text{for } -2 \\leq x < -\\frac{2}{3} \\\\ f(x) = -3x - 2 & \\text{for } -\\frac{2}{3} \\leq x < 0 \\\\ f(x) = \\sqrt{4-(x-2)^2} & \\text{for } 0 \\leq x \\leq 4 \\end{cases}$

Computing the three pieces:
$$\\int_{-2}^4 |f(x)|\\,dx = \\int_{-2}^{-2/3} (-3x-2)\\,dx + \\int_{-2/3}^0 (3x+2)\\,dx + \\int_0^4 \\sqrt{4-(x-2)^2}\\,dx$$

$$= -\\left[\\frac{3x^2}{2} + 2x\\right]_{-2}^{-2/3} + \\left[\\frac{3x^2}{2} + 2x\\right]_{-2/3}^0 + \\frac{1}{2}\\pi(2)^2$$

$$= -\\left(\\frac{2}{3} - \\frac{4}{3} - 6 + 4\\right) + \\left(0 - \\left(\\frac{2}{3} - \\frac{4}{3}\\right)\\right) + 2\\pi$$

$$= -\\left(-\\frac{8}{3} - 2\\right) + \\left(\\frac{2}{3}\\right) + 2\\pi = \\frac{8}{3} + 2 + \\frac{2}{3} + 2\\pi$$

$$= \\frac{10}{3} + 2\\pi \\approx 3.333 + 6.283 = 9.616$$

**Geometric interpretation:** $\\int_{-2}^4 |f(x)|\\,dx$ represents the total area between $f(x)$ and the $x$-axis, counting negative areas as positive. This equals the sum of the triangular area (above axis) from the line segment, the triangular area (below axis) from the same segment, and the area of the semicircle.

**(d)** By the Fundamental Theorem of Calculus, Part 1:
$$g'(x) = \\frac{d}{dx}\\left[\\int_{-2}^x f(t)\\,dt\\right] = f(x)$$

Therefore:
$$g'(2) = f(2) = 2$$

**Interpretation:** $g'(2)$ represents the instantaneous rate of change of the accumulation function $g(x)$ at $x = 2$. Geometrically, it is the height of $f$ at $x = 2$. Contextually, if $g(x)$ represents the net area under $f$ from $-2$ to $x$, then $g'(2)$ tells us that when $x = 2$, the area is increasing at a rate of 2 square units per unit increase in $x$.

## Explanation

**Part (a):** The calculations use the partition points and the appropriate formulas for left, right, and trapezoidal approximations. The function changes definition at $x = 0$, requiring careful evaluation.

**Part (b):** While the trapezoidal rule is generally more accurate than individual left or right sums, in this case the right sum happens to be closest to the actual value due to the specific behavior of $f$ on each subinterval.

**Part (c):** This integral separates the regions where $f$ is positive and negative, taking absolute values. The semicircle area is exactly half the area of a full circle of radius 2.

**Part (d):** This applies the Fundamental Theorem of Calculus directly: $\\frac{d}{dx}\\int_a^x f(t)\\,dt = f(x)$. The value $f(2) = 2$ is read directly from the graph (the maximum height of the semicircle).
