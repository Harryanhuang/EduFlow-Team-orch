---
id: T13-Item07
difficulty: S
calculator: calc
type: frq
---
A spherical balloon is being inflated. Its volume increases at a rate of 12 cubic inches per minute. At time $t = 0$, the radius is 2 inches.

(a) Write an expression for $\frac{dr}{dt}$ in terms of $r$.

(b) At what time is the radius 5 inches? (Round to 2 decimal places.)

(c) At the instant when $r = 5$ inches, is $\frac{dr}{dt}$ increasing or decreasing? Justify your answer using the expression from part (a).

## Answer
(a) $\frac{dr}{dt} = \frac{3}{\pi r^2}$

(b) $t \approx 13.64$ minutes

(c) $\frac{dr}{dt}$ is decreasing because $\frac{d}{dr}\!\left(\frac{3}{\pi r^2}\right) = -\frac{6}{\pi r^3} < 0$ for all $r > 0$.

## Explanation
(a) $V = \frac{4}{3}\pi r^3 \implies \frac{dV}{dt} = 4\pi r^2 \frac{dr}{dt}$
$12 = 4\pi r^2 \frac{dr}{dt} \implies \frac{dr}{dt} = \frac{12}{4\pi r^2} = \frac{3}{\pi r^2}$

(b) To find $t$: integrate $\frac{dr}{dt} = \frac{3}{\pi r^2}$ or use $V = \frac{4}{3}\pi r^3$.
Initial $V = \frac{4}{3}\pi(2)^3 = \frac{32\pi}{3}$. Final $V = \frac{4}{3}\pi(5)^3 = \frac{500\pi}{3}$.
$\Delta V = \frac{468\pi}{3} = 156\pi$.
$12t = 156\pi \implies t = 13\pi \approx 13.64$ minutes.

(c) Since $\frac{d}{dr}\!\left(\frac{dr}{dt}\right) = -\frac{6}{\pi r^3} < 0$, $\frac{dr}{dt}$ decreases as $r$ increases.
