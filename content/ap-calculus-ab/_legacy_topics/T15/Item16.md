---
id: T15-Item16
difficulty: C
calculator: calc
type: frq
---
A particle moves along the $x$-axis with velocity $v(t) = t^2 - 4t + 3$ (in meters per second), for $0 \le t \le 5$ seconds. At time $t = 0$, the particle is at position $x = 2$ meters.

(a) Find all time intervals in $[0, 5]$ when the particle is moving to the right.
(b) Find the average velocity of the particle on $[0, 5]$.
(c) Use the Mean Value Theorem to show that there must be at least one instant $t = c$ in $(0, 5)$ when the instantaneous velocity equals the average velocity found in part (b).
(d) Find the total distance traveled by the particle on $[0, 5]$.

## Answer
(a) Moving right when $v(t) > 0$: $t^2 - 4t + 3 = (t-1)(t-3) > 0$. So $v(t) > 0$ for $t \in (0, 1) \cup (3, 5]$ and $v(t) < 0$ for $t \in (1, 3)$.
(b) $x(t) = \int v(t)\,dt = t^3/3 - 2t^2 + 3t + C$. With $x(0) = 2$, $C = 2$.
$x(5) = 125/3 - 50 + 15 + 2 = 125/3 - 33 \approx 41.667 - 33 = 8.667$
Average velocity = $(x(5) - x(0))/5 = (x(5) - 2)/5 = (8.667 - 2)/5 \approx 1.333$ m/s.
Exact: $x(5) = 125/3 - 50 + 15 + 2 = 125/3 - 33 = (125 - 99)/3 = 26/3$.
Average velocity = $(26/3 - 2)/5 = (26/3 - 6/3)/5 = (20/3)/5 = 4/3$ m/s.
(c) $v(t)$ is continuous on $[0, 5]$ and differentiable on $(0, 5)$, so MVT applies. There exists $c \in (0, 5)$ with $v(c) = 4/3$. Solving $t^2 - 4t + 3 = 4/3$: $3t^2 - 12t + 9 = 4$, $3t^2 - 12t + 5 = 0$. $t = (12 \pm \sqrt{144 - 60})/6 = (12 \pm \sqrt{84})/6 = (12 \pm 2\sqrt{21})/6 = 2 \pm \sqrt{21}/3$. Both $2 - \sqrt{21}/3 \approx 0.47$ and $2 + \sqrt{21}/3 \approx 3.53$ are in $(0, 5)$.
(d) Distance = $\int_0^5 |v(t)|\,dt = \int_0^1 v(t)\,dt - \int_1^3 v(t)\,dt + \int_3^5 v(t)\,dt$.
$\int_0^5 v(t)\,dt = x(5) - x(0) = 26/3 - 2 = 20/3$.
$\int_1^3 v(t)\,dt = [t^3/3 - 2t^2 + 3t]_1^3 = (9 - 18 + 9) - (1/3 - 2 + 3) = 0 - (1/3 + 1) = -4/3$.
Distance = $20/3 - 2(-4/3) = 20/3 + 8/3 = 28/3 \approx 9.33$ m.

## Explanation
This problem integrates MVT with motion concepts. The average velocity on an interval equals the average rate of change of position, and MVT guarantees an instant where instantaneous velocity equals this average. Separating the integral at the zeros of $v(t)$ gives total distance.
