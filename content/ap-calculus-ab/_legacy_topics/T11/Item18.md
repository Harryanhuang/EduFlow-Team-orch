---
id: T11-Item18
difficulty: C
calculator: calc
type: frq
---
A particle moves along a line so that its position at time $t \geq 0$ is given by $s(t) = t \arctan t - \frac{1}{2}\ln(1 + t^2)$.

(a) Find the velocity $v(t) = s'(t)$.
(b) Find the acceleration $a(t) = s''(t)$.
(c) Is the particle speeding up or slowing down at $t = 1$? Justify your answer.
(d) Find the third derivative $s'''(t)$.

## Answer
(a) $v(t) = \arctan t$
(b) $a(t) = \frac{1}{1 + t^2}$
(c) At $t = 1$: $v(1) = \arctan(1) = \frac{\pi}{4} > 0$ and $a(1) = \frac{1}{2} > 0$. Since $v$ and $a$ have the same sign, the particle is speeding up.
(d) $s'''(t) = \frac{-2t}{(1 + t^2)^2}$

## Explanation
(a) $s'(t) = \arctan t + t \cdot \frac{1}{1+t^2} - \frac{1}{2} \cdot \frac{2t}{1+t^2} = \arctan t + \frac{t}{1+t^2} - \frac{t}{1+t^2} = \arctan t$. (b) $v'(t) = \frac{1}{1+t^2} = a(t)$. (c) $v(1) = \pi/4 > 0$, $a(1) = 1/2 > 0$; same sign means speeding up. (d) $a'(t) = \frac{d}{dt}[(1+t^2)^{-1}] = -(1+t^2)^{-2} \cdot 2t = \frac{-2t}{(1+t^2)^2}$.
