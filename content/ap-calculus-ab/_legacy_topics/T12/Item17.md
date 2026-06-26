---
id: T12-Item17
difficulty: C
calculator: no-calc
type: frq
---
Two particles move along the $x$-axis. Particle A has position $s_A(t) = 4t - t^2$ and particle B has position $s_B(t) = t^2 - 2t$, both for $t \geq 0$.

(a) At what time(s) do the particles occupy the same position?
(b) At the time(s) found in part (a), are the particles moving in the same direction or in opposite directions? Justify.
(c) Find the maximum distance between the two particles on the interval $0 \leq t \leq 3$.
(d) Is the distance between the particles increasing or decreasing at $t = 1$? Justify.

## Answer
(a) Set $s_A(t) = s_B(t)$: $4t - t^2 = t^2 - 2t \Rightarrow 0 = 2t^2 - 6t \Rightarrow 2t(t - 3) = 0$. So $t = 0$ and $t = 3$.

(b) $v_A(t) = 4 - 2t$ and $v_B(t) = 2t - 2$.
At $t = 0$: $v_A(0) = 4 > 0$, $v_B(0) = -2 < 0$. Opposite directions.
At $t = 3$: $v_A(3) = -2 < 0$, $v_B(3) = 4 > 0$. Opposite directions.

(c) Distance: $D(t) = |s_A(t) - s_B(t)| = |4t - t^2 - t^2 + 2t| = |6t - 2t^2| = 2t|3 - t|$. On $[0, 3]$, $3 - t \geq 0$, so $D(t) = 6t - 2t^2$. To maximize: $D'(t) = 6 - 4t = 0 \Rightarrow t = 3/2$. $D(3/2) = 6(3/2) - 2(9/4) = 9 - 9/2 = 9/2 = 4.5$. At endpoints: $D(0) = 0$, $D(3) = 0$. Maximum distance is $9/2$ units at $t = 3/2$.

(d) $D'(t) = 6 - 4t$. At $t = 1$: $D'(1) = 6 - 4 = 2 > 0$. Since the derivative of distance is positive, the distance between the particles is increasing at $t = 1$.

## Explanation
This problem requires comparing two moving particles. Part (c) is subtle: the distance function $|s_A - s_B|$ must be handled carefully by checking the sign. On $[0, 3]$, $s_A \geq s_B$, so absolute value drops. Part (d) tests whether students can differentiate the distance function rather than just comparing velocities.
