---
id: T08-Item16
difficulty: C
calculator: no-calc
type: frq
---
Find the equation of the tangent line to the curve y = arctan(ln(x)) at x = e.

## Answer
y = x/(2e) - 1/2 + pi/4

## Explanation
The point: at x = e, y = arctan(ln(e)) = arctan(1) = pi/4.
The derivative: apply the chain rule with outer function arctan(u) and inner function u = ln(x).
y'(x) = 1/(1 + (ln(x))^2) * 1/x = 1/(x(1 + (ln(x))^2)).
At x = e: y'(e) = 1/(e(1 + 1^2)) = 1/(2e).
Tangent line using point-slope form: y - pi/4 = 1/(2e)(x - e).
Simplify: y = x/(2e) - 1/2 + pi/4.
