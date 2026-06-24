---
id: T12-Item15
difficulty: C
calculator: no-calc
type: frq
---
A particle moves along the $x$-axis with velocity $v(t) = 2\sin(t) - 1$ for $0 \leq t \leq 2\pi$.

(a) On what intervals is the particle moving to the right? On what intervals is it moving to the left?
(b) What is the acceleration of the particle at $t = \pi/6$?
(c) Find the total distance traveled by the particle from $t = 0$ to $t = 2\pi$.
(d) At what time(s) is the speed of the particle equal to 1?

## Answer
(a) Moving right when $v(t) > 0$: $2\sin(t) - 1 > 0 \Rightarrow \sin(t) > 1/2$. On $[0, 2\pi]$, this holds for $\pi/6 < t < 5\pi/6$. Moving left when $v(t) < 0$: this holds for $0 \leq t < \pi/6$ and $5\pi/6 < t \leq 2\pi$.

(b) $a(t) = v'(t) = 2\cos(t)$. At $t = \pi/6$: $a(\pi/6) = 2\cos(\pi/6) = 2 \cdot \frac{\sqrt{3}}{2} = \sqrt{3}$.

(c) Direction changes at $t = \pi/6$ and $t = 5\pi/6$. Position: $s(t) = \int v(t)\, dt = -2\cos(t) - t + C$.
- $s(0) = -2 + C$
- $s(\pi/6) = -2\cos(\pi/6) - \pi/6 + C = -\sqrt{3} - \pi/6 + C$
- $s(5\pi/6) = -2\cos(5\pi/6) - 5\pi/6 + C = \sqrt{3} - 5\pi/6 + C$
- $s(2\pi) = -2 - 2\pi + C$

Total distance = $|s(\pi/6) - s(0)| + |s(5\pi/6) - s(\pi/6)| + |s(2\pi) - s(5\pi/6)|$
= $|-\sqrt{3} - \pi/6 + 2| + |\sqrt{3} - 5\pi/6 + \sqrt{3} + \pi/6| + |-2 - 2\pi - \sqrt{3} + 5\pi/6|$
= $|2 - \sqrt{3} - \pi/6| + |2\sqrt{3} - 2\pi/3| + |-2 - \sqrt{3} - 7\pi/6|$

(d) Speed = $|v(t)| = 1 \Rightarrow v(t) = 1$ or $v(t) = -1$.
Case 1: $2\sin(t) - 1 = 1 \Rightarrow \sin(t) = 1 \Rightarrow t = \pi/2$.
Case 2: $2\sin(t) - 1 = -1 \Rightarrow \sin(t) = 0 \Rightarrow t = 0, \pi, 2\pi$.

So speed equals 1 at $t = 0, \pi/2, \pi, 2\pi$.

## Explanation
Part (a) tests solving trigonometric inequalities. Part (c) is the standard total-distance computation. Part (d) tests the distinction between velocity and speed: speed = 1 when the magnitude of velocity is 1, requiring solving both $v = 1$ and $v = -1$.
