---
id: T20-Item12
difficulty: S
calculator: calc
type: frq
---
The graph of $y = f(x)$ is shown below for $0 \leq x \leq 10$. The graph consists of line segments and a semicircle. The area of each region is labeled.

(Graph description: From (0,0) to (2,6) is a line; from (2,6) to (6,6) is a horizontal line; from (6,6) to (10,0) is part of a semicircle with radius 4 and center at (6,2). Areas: Region A (triangle, x=0 to x=2, height 6) has area 6; Region B (rectangle, x=2 to x=6, height 6) has area 24; Region C (semicircle above x-axis, x=6 to x=10) has area $8\pi$.)

Let $A(x) = \int_0^x f(t) \, dt$.

(a) Find $A(2)$, $A(6)$, and $A(10)$.

(b) Find $A'(4)$.

(c) On what interval(s) is $A$ increasing?

(d) Find the average value of $f$ on $[0, 10]$.

## Answer
(a) $A(2) = 6$, $A(6) = 30$, $A(10) = 30 + 8\pi$

(b) $A'(4) = 6$

(c) $A$ is increasing on $[0, 6]$ since $f(x) > 0$ there. (On $[6, 10]$, $f(x) \geq 0$, so $A$ is non-decreasing, but strictly increasing where $f(x) > 0$.)

(d) Average value $= \frac{30 + 8\pi}{10} = 3 + \frac{4\pi}{5}$

## Explanation
(a) $A(x)$ represents the accumulated area under $f$ from $0$ to $x$.

$A(2) = \int_0^2 f(t) \, dt = 6$ (area of triangle with base 2, height 6)

$A(6) = \int_0^6 f(t) \, dt = 6 + 24 = 30$ (triangle + rectangle)

$A(10) = \int_0^{10} f(t) \, dt = 30 + 8\pi$ (adding the semicircle area)

(b) By FTC Part 1, $A'(x) = f(x)$. So $A'(4) = f(4) = 6$ (the constant value on $[2, 6]$).

(c) $A$ is increasing when $f(x) > 0$, which occurs on $(0, 10)$ since $f$ is non-negative throughout. The function is strictly increasing on $[0, 6]$ where $f(x) > 0$, and non-decreasing on $[6, 10]$ where $f(x) \geq 0$.

(d) Average value $= \frac{1}{10-0}\int_0^{10} f(x) \, dx = \frac{A(10)}{10} = \frac{30 + 8\pi}{10} = 3 + \frac{4\pi}{5}$
