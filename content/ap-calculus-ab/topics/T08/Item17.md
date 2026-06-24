---
id: T08-Item17
difficulty: C
calculator: calc
type: frq
---
A particle moves along a line with position s(t) = ln(arctan(t)), for t > 0.

(a) Find the velocity v(t) = s'(t).
(b) At what time t is the velocity equal to 2/pi?
(c) Find the acceleration a(t) = v'(t).

## Answer
(a) v(t) = 1/((1 + t^2)*arctan(t))
(b) t = 1
(c) a(t) = -[2t*arctan(t) + 1] / [(1 + t^2)^2 * (arctan(t))^2]

## Explanation
(a) Chain rule: outer function is ln(u), inner function is u = arctan(t).
s'(t) = 1/arctan(t) * 1/(1 + t^2) = 1/((1 + t^2)*arctan(t)).

(b) Set v(t) = 2/pi: 1/((1 + t^2)*arctan(t)) = 2/pi, so (1 + t^2)*arctan(t) = pi/2.
At t = 1: (1 + 1) * arctan(1) = 2 * (pi/4) = pi/2. So t = 1.

(c) v(t) = 1/((1 + t^2)*arctan(t)). Apply the quotient rule.
d/dt[(1 + t^2)*arctan(t)] = 2t*arctan(t) + (1 + t^2)*(1/(1 + t^2)) = 2t*arctan(t) + 1.
So a(t) = v'(t) = -[2t*arctan(t) + 1] / [(1 + t^2)^2 * (arctan(t))^2].
