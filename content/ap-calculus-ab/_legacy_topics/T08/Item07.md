---
id: T08-Item07
difficulty: S
calculator: no-calc
type: frq
---
Let f(x) = e^(sin(2x)). Find f'(x).

## Answer
f'(x) = 2 cos(2x) * e^(sin(2x))

## Explanation
Apply the chain rule twice (nested composition). Outer: e^u, middle: sin(v), inner: v = 2x.
d/dx[e^(sin(2x))] = e^(sin(2x)) * d/dx[sin(2x)] = e^(sin(2x)) * cos(2x) * 2 = 2 cos(2x) * e^(sin(2x)).
