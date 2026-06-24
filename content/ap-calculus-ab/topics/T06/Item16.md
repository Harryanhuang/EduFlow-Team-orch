---
id: T06-Item16
difficulty: C
calculator: no-calc
type: frq
---
The graph of a differentiable function f passes through the point (1, 3). The derivative of f is given by f'(x) = 2x + 1/x for x > 0.

(a) Find the equation of the tangent line to f at x = 1.
(b) Use the tangent line from part (a) to approximate f(1.1).
(c) Is this approximation an overestimate or underestimate? Justify using f''(x).
(d) Find f(x).

## Answer
(a) Slope at x = 1: f'(1) = 2 + 1 = 3. Tangent line: y - 3 = 3(x - 1), so y = 3x.
(b) f(1.1) approximately 3(1.1) = 3.3.
(c) f''(x) = 2 - 1/x^2. At x = 1: f''(1) = 2 - 1 = 1 > 0. Since f is concave up at x = 1, the tangent line lies below the curve, so the approximation is an underestimate.
(d) f(x) = integral of (2x + 1/x) dx = x^2 + ln(x) + C. Since f(1) = 3: 1 + 0 + C = 3, so C = 2. Thus f(x) = x^2 + ln(x) + 2.

## Explanation
The tangent line uses point-slope form with the derivative as slope. Concavity (f'') determines whether a tangent line approximation over- or underestimates. Finding f(x) from f'(x) requires antidifferentiation, using the known point to solve for C.
