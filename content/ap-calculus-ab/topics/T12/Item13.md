---
id: T12-Item13
difficulty: C
calculator: no-calc
type: frq
---
A particle moves along the $x$-axis with acceleration given by $a(t) = 6t - 12$ for $t \geq 0$. At $t = 0$, the particle has velocity $v(0) = 8$ and position $s(0) = 3$.

(a) Find the velocity function $v(t)$ and the position function $s(t)$.
(b) At what time(s) is the particle at rest?
(c) What is the total distance traveled by the particle from $t = 0$ to $t = 6$?
(d) Is the speed of the particle increasing or decreasing at $t = 3$? Justify your answer.

## Answer
(a) $v(t) = \int a(t)\, dt = \int (6t - 12)\, dt = 3t^2 - 12t + C$. Using $v(0) = 8$: $C = 8$. So $v(t) = 3t^2 - 12t + 8$.

$s(t) = \int v(t)\, dt = \int (3t^2 - 12t + 8)\, dt = t^3 - 6t^2 + 8t + D$. Using $s(0) = 3$: $D = 3$. So $s(t) = t^3 - 6t^2 + 8t + 3$.

(b) Set $v(t) = 0$: $3t^2 - 12t + 8 = 0$. Using the quadratic formula: $t = \frac{12 \pm \sqrt{144 - 96}}{6} = \frac{12 \pm \sqrt{48}}{6} = \frac{12 \pm 4\sqrt{3}}{6} = 2 \pm \frac{2\sqrt{3}}{3}$. So $t \approx 0.845$ and $t \approx 3.155$.

(c) The particle changes direction at $t_1 = 2 - \frac{2\sqrt{3}}{3}$ and $t_2 = 2 + \frac{2\sqrt{3}}{3}$. Evaluate:
- $s(0) = 3$
- $s(t_1) = t_1^3 - 6t_1^2 + 8t_1 + 3$
- $s(t_2) = t_2^3 - 6t_2^2 + 8t_2 + 3$
- $s(6) = 216 - 216 + 48 + 3 = 51$

Total distance = $|s(t_1) - s(0)| + |s(t_2) - s(t_1)| + |s(6) - s(t_2)|$.

(d) Speed is increasing when velocity and acceleration have the same sign. At $t = 3$: $v(3) = 27 - 36 + 8 = -1 < 0$ and $a(3) = 18 - 12 = 6 > 0$. Since $v(3) < 0$ and $a(3) > 0$, they have opposite signs, so the speed is **decreasing** at $t = 3$.

## Explanation
This is a multi-step particle motion problem requiring integration from acceleration to velocity to position, solving a quadratic with radicals, and applying the key principle that speed increases when $v$ and $a$ share signs and decreases when they differ. Part (d) is a common conceptual trap: students often think $a > 0$ always means "speeding up."
