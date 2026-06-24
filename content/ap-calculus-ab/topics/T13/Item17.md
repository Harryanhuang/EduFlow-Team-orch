---
id: T13-Item17
difficulty: C
calculator: calc
type: frq
---
A ship at point $A$ sails north at 20 km/h and a second ship at point $B$ sails east at 15 km/h. Point $B$ is located 60 km east and 80 km north of point $A$. Both ships travel at constant speeds.

(a) Let $d$ be the distance between the ships. Write $d^2$ as a function of time $t$ (in hours).

(b) How fast is the distance between the ships changing when $t = 2$ hours?

(c) As $t \to \infty$, what does $\frac{dd}{dt}$ approach? Explain your reasoning.

## Answer
(a) $d^2 = 625t^2 - 1400t + 10000$

(b) $\frac{dd}{dt} = \frac{55}{\sqrt{97}} \approx 5.58$ km/h

(c) $\frac{dd}{dt} \to 25$ km/h as $t \to \infty$

## Explanation
(a) Place $A$ at $(0,0)$. Then $A$ moves north: position = $(0, 20t)$. Ship $B$ starts at $(60, 80)$ and moves east: position = $(60+15t, 80)$.
$d^2 = (15t+60)^2 + (20t-80)^2 = 225t^2 + 1800t + 3600 + 400t^2 - 3200t + 6400 = 625t^2 - 1400t + 10000$.

(b) Differentiating: $2d\frac{dd}{dt} = 1250t - 1400$, so $\frac{dd}{dt} = \frac{1250t - 1400}{2d}$.
At $t = 2$: $d^2 = 625(4) - 1400(2) + 10000 = 9700$, so $d = 10\sqrt{97}$.
$\frac{dd}{dt} = \frac{2500 - 1400}{20\sqrt{97}} = \frac{1100}{20\sqrt{97}} = \frac{55}{\sqrt{97}} \approx 5.58$ km/h.

(c) $\frac{dd}{dt} = \frac{1250t - 1400}{2\sqrt{625t^2 - 1400t + 10000}} = \frac{1250 - 1400/t}{2\sqrt{625 - 1400/t + 10000/t^2}}$.
As $t \to \infty$, this approaches $\frac{1250}{2 \cdot 25} = 25$ km/h.
