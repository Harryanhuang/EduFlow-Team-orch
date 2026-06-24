---
id: T19-Item01
difficulty: F
calculator: no-calc
type: mcq
---

A rocket launched straight upward has its velocity (in m/s) recorded at 2-second intervals, as shown in the table below.

| t (s) | 0  | 2  | 4  | 6  | 8  | 10 |
|-------|----|----|----|----|----|----|
| v(t)  | 10 | 24 | 44 | 62 | 78 | 92 |

Using a left Riemann sum with 5 subintervals of equal width, which of the following approximations best estimates the total vertical distance traveled by the rocket over the interval $0 \leq t \leq 10$?

A) 400 m
B) 560 m
C) 640 m
D) 736 m

## Answer

A

## Explanation

With 5 subintervals over $[0, 10]$, each subinterval has width $\Delta t = 2$ seconds.

The left Riemann sum uses the velocity values at the left endpoints $t = 0, 2, 4, 6, 8$:

$$\text{Left sum} = \Delta t \cdot [v(0) + v(2) + v(4) + v(6) + v(8)] = 2 \cdot [10 + 24 + 44 + 62 + 78] = 2 \cdot 218 = 436 \text{ m}$$

Since the velocity function $v(t)$ is increasing over $[0, 10]$ (the rocket is accelerating upward), the left Riemann sum **underestimates** the true distance.

The right Riemann sum gives an overestimate:
$$\text{Right sum} = 2 \cdot [24 + 44 + 62 + 78 + 92] = 2 \cdot 300 = 600 \text{ m}$$

Among the given options, **A) 400 m** is closest to the calculated left sum of 436 m, which makes sense as an underestimate for an increasing velocity function.
