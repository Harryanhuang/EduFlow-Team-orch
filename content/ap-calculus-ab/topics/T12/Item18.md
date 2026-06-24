---
id: T12-Item18
difficulty: C
calculator: no-calc
type: frq
---
A cylindrical tank with a radius of 3 meters is being filled with water. The volume of water in the tank at time $t$ minutes is $V(t)$ cubic meters, and the height of the water is $h(t)$ meters. Water flows into the tank at a rate of $V'(t) = 45 - 3t$ cubic meters per minute for $0 \leq t \leq 15$. The tank is empty at $t = 0$.

(a) Find the height of the water at $t = 5$ minutes.
(b) At what rate is the height of the water changing at $t = 8$ minutes? Include units.
(c) At what time $t$ is the height of the water increasing most rapidly?
(d) A second tank (identical dimensions) is being filled at a rate of $V_2'(t) = 30$ cubic meters per minute. At what time do the two tanks contain the same volume of water?

## Answer
(a) $V(5) = \int_0^5 (45 - 3t)\, dt = [45t - \frac{3}{2}t^2]_0^5 = 225 - \frac{75}{2} = 225 - 37.5 = 187.5$ m$^3$. Volume of a cylinder: $V = \pi r^2 h = 9\pi h$. So $h(5) = \frac{187.5}{9\pi} = \frac{187.5}{9\pi} \approx 6.63$ meters.

(b) $V'(8) = 45 - 24 = 21$ m$^3$/min. Since $V(t) = 9\pi h(t)$, we have $V'(t) = 9\pi h'(t)$. So $h'(8) = \frac{V'(8)}{9\pi} = \frac{21}{9\pi} = \frac{7}{3\pi} \approx 0.743$ meters per minute.

(c) The height increases most rapidly when $h'(t)$ is maximized. Since $h'(t) = \frac{V'(t)}{9\pi} = \frac{45 - 3t}{9\pi}$, and this is a decreasing linear function of $t$, the maximum occurs at $t = 0$: $h'(0) = \frac{45}{9\pi} = \frac{5}{\pi}$ meters per minute.

(d) $V_1(t) = 45t - \frac{3}{2}t^2$ and $V_2(t) = 30t$. Set equal: $45t - \frac{3}{2}t^2 = 30t \Rightarrow 15t = \frac{3}{2}t^2 \Rightarrow t^2 = 10t \Rightarrow t = 0$ or $t = 10$. At $t = 10$ minutes, both tanks contain 300 m$^3$.

## Explanation
This is a contextual rate problem connecting volume and height through the geometry of a cylinder. Part (b) tests related rates: knowing that $V' = 9\pi h'$. Part (c) tests that "most rapidly increasing" means maximizing the rate (not finding where it equals zero). Part (d) requires setting up and solving a simple quadratic.
