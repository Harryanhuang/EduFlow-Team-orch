---
id: T18-Item12
difficulty: C
calculator: calc
type: frq
---
A wire of length 60 cm is cut into two pieces. One piece is bent into a circle and the other into a square.

(a) Let $x$ be the circumference of the circle. Express the total area $A$ enclosed by both shapes as a function of $x$.
(b) What value of $x$ minimizes the total area?
(c) What is the minimum total area?

## Answer
(a) $A(x) = \frac{x^2}{4\pi} + \frac{(60 - x)^2}{16}$

(b) $x = \frac{60\pi}{\pi + 4}$

(c) $A_{min} = \frac{900}{\pi + 4}$

## Explanation
(a) Circle circumference $x$, so radius $r = x/(2\pi)$, area $\pi r^2 = x^2/(4\pi)$.
Remaining wire: $60 - x$, used for square perimeter, so side $s = (60 - x)/4$, area $s^2 = (60 - x)^2/16$.
Total area: $A(x) = \frac{x^2}{4\pi} + \frac{(60 - x)^2}{16}$.

(b) $A'(x) = \frac{x}{2\pi} + \frac{2(60 - x)(-1)}{16} = \frac{x}{2\pi} - \frac{60 - x}{8} = 0$.
$\frac{x}{2\pi} = \frac{60 - x}{8}$.
$8x = 2\pi(60 - x)$.
$8x = 120\pi - 2\pi x$.
$x(8 + 2\pi) = 120\pi$.
$x = \frac{120\pi}{8 + 2\pi} = \frac{60\pi}{4 + \pi}$.

(c) $A_{min} = \frac{1}{4\pi}\left(\frac{60\pi}{4+\pi}\right)^2 + \frac{1}{16}\left(60 - \frac{60\pi}{4+\pi}\right)^2 = \frac{3600\pi}{16(4+\pi)^2} + \frac{3600(4)^2}{16(4+\pi)^2} = \frac{3600[\pi + 16]}{16(4+\pi)^2} = \frac{225[\pi + 16]}{(4+\pi)^2} = \frac{225}{\pi + 4}$.
