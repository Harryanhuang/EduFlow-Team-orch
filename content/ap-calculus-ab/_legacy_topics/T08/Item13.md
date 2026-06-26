---
id: T08-Item13
difficulty: C
calculator: no-calc
type: frq
---
Let f(x) = sin(cos(e^(x^2))). Find f'(x).

## Answer
f'(x) = -2x * e^(x^2) * sin(e^(x^2)) * cos(cos(e^(x^2)))

## Explanation
Apply the chain rule through 4 layers:
- Outermost: sin(u), u = cos(e^(x^2)); derivative = cos(u) = cos(cos(e^(x^2)))
- Next: cos(v), v = e^(x^2); derivative = -sin(v) = -sin(e^(x^2))
- Next: e^w, w = x^2; derivative = e^w = e^(x^2)
- Innermost: x^2; derivative = 2x

Multiply all: f'(x) = cos(cos(e^(x^2))) * (-sin(e^(x^2))) * e^(x^2) * 2x = -2x * e^(x^2) * sin(e^(x^2)) * cos(cos(e^(x^2))).
