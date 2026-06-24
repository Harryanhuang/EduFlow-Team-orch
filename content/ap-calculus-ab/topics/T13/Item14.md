---
id: T13-Item14
difficulty: C
calculator: no-calc
type: frq
---
A point moves along the curve $y^2 = x^3$ in the first quadrant. When the point is at $(4, 8)$, its $x$-coordinate is increasing at 6 units per second.

(a) Find $\frac{dy}{dt}$ at $(4, 8)$.

(b) Is the $y$-coordinate increasing or decreasing at this instant? Explain.

(c) At what rate is the distance from the origin $d = \sqrt{x^2 + y^2}$ changing at $(4, 8)$?

## Answer
(a) $\frac{dy}{dt} = 18$ units/s

(b) Increasing, since $\frac{dy}{dt} > 0$.

(c) $\frac{dd}{dt} = \frac{42}{\sqrt{5}} \approx 18.78$ units/s

## Explanation
(a) $y^2 = x^3$. Differentiating: $2y\frac{dy}{dt} = 3x^2\frac{dx}{dt}$.
At $(4, 8)$: $2(8)\frac{dy}{dt} = 3(16)(6) = 288$, so $\frac{dy}{dt} = 18$.

(b) Since $\frac{dy}{dt} = 18 > 0$, the $y$-coordinate is increasing.

(c) $d^2 = x^2 + y^2 \implies 2d\frac{dd}{dt} = 2x\frac{dx}{dt} + 2y\frac{dy}{dt}$.
At $(4, 8)$: $d = \sqrt{16 + 64} = \sqrt{80} = 4\sqrt{5}$.
$2(4\sqrt{5})\frac{dd}{dt} = 2(4)(6) + 2(8)(18) = 48 + 288 = 336$.
$\frac{dd}{dt} = \frac{336}{8\sqrt{5}} = \frac{42}{\sqrt{5}} \approx 18.78$ units/s.
