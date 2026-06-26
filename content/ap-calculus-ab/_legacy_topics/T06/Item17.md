---
id: T06-Item17
difficulty: C
calculator: no-calc
type: frq
---
Let f(x) = e^x - x^2.

(a) Find f'(x) and f''(x).
(b) Show that f has no critical points in the interval (0, 2). Justify.
(c) Find the equation of the normal line to f at x = 0.
(d) For x > 0, compare the growth rates of e^x and x^2. Explain using derivatives.

## Answer
(a) f'(x) = e^x - 2x, f''(x) = e^x - 2.
(b) Consider $g(x) = f'(x) = e^x - 2x$. Then $g(0) = 1 > 0$ and $g'(x) = e^x - 2 = 0$ at $x = \ln 2 \approx 0.693$, where $g$ attains its minimum on $[0, 2]$. The minimum value is $g(\ln 2) = 2 - 2\ln 2 \approx 0.614 > 0$. Therefore $f'(x) > 0$ throughout $(0, 2)$, so $f$ has no critical points there and is strictly increasing on the interval.

(c) At x = 0: f(0) = 1 - 0 = 1, f'(0) = 1. Normal line slope = -1/f'(0) = -1. Normal line: y - 1 = -1(x - 0), so y = -x + 1.
(d) For large x, e^x grows much faster than x^2. This is seen because d/dx[e^x] = e^x while d/dx[x^2] = 2x, and e^x / (2x) goes to infinity as x goes to infinity.

## Explanation
The normal line is perpendicular to the tangent line, so its slope is the negative reciprocal of f'. Comparing growth rates uses the fact that exponential functions eventually dominate polynomial functions, visible in their derivatives.
