---
id: T12-Item08
difficulty: S
calculator: no-calc
type: frq
---
The position of a particle moving along a straight line is given by $s(t) = t^3 - 9t^2 + 24t - 10$ for $t \geq 0$, where $s$ is measured in meters and $t$ in seconds.

(a) Find the velocity and acceleration functions.
(b) For what values of $t$ is the particle at rest?
(c) Find the total distance traveled by the particle from $t = 0$ to $t = 5$.

## Answer
(a) $v(t) = s'(t) = 3t^2 - 18t + 24$; $a(t) = v'(t) = 6t - 18$

(b) Set $v(t) = 0$: $3t^2 - 18t + 24 = 0 \Rightarrow t^2 - 6t + 8 = 0 \Rightarrow (t - 2)(t - 4) = 0$. The particle is at rest at $t = 2$ and $t = 4$.

(c) The particle changes direction at $t = 2$ and $t = 4$. Compute position at critical times:
- $s(0) = -10$
- $s(2) = 8 - 36 + 48 - 10 = 10$
- $s(4) = 64 - 144 + 96 - 10 = 6$
- $s(5) = 125 - 225 + 120 - 10 = 10$

Total distance = $|s(2) - s(0)| + |s(4) - s(2)| + |s(5) - s(4)| = |10 - (-10)| + |6 - 10| + |10 - 6| = 20 + 4 + 4 = 28$ meters.

## Explanation
Part (a) uses the power rule. Part (b) requires solving a quadratic. Part (c) requires identifying direction-change points, evaluating position at each, and summing absolute displacements. A common error is to compute $s(5) - s(0) = 20$, which gives displacement, not total distance.
