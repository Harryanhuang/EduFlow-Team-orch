---
id: T08-Item18
difficulty: C
calculator: no-calc
type: frq
---
Let g(x) = arccos(x) * arcsin(x).

(a) Find g'(x).
(b) Evaluate g'(sqrt(2)/2) exactly.
(c) At x = sqrt(2)/2, is g(x) increasing or decreasing? Justify your answer.

## Answer
(a) g'(x) = arccos(x)/sqrt(1 - x^2) - arcsin(x)/sqrt(1 - x^2) = (arccos(x) - arcsin(x))/sqrt(1 - x^2)
(b) g'(sqrt(2)/2) = 0
(c) Neither — the function has a horizontal tangent at x = sqrt(2)/2 since g'(sqrt(2)/2) = 0.

## Explanation
(a) Product rule: g'(x) = d/dx[arccos(x)] * arcsin(x) + arccos(x) * d/dx[arcsin(x)]
= (-1/sqrt(1 - x^2)) * arcsin(x) + arccos(x) * (1/sqrt(1 - x^2))
= (arccos(x) - arcsin(x))/sqrt(1 - x^2).

(b) At x = sqrt(2)/2: arcsin(sqrt(2)/2) = pi/4 and arccos(sqrt(2)/2) = pi/4.
g'(sqrt(2)/2) = (pi/4 - pi/4)/sqrt(1 - 1/2) = 0/sqrt(1/2) = 0.

(c) Since g'(sqrt(2)/2) = 0, the function has a horizontal tangent there. At this exact point the function is neither increasing nor decreasing (it is a critical point).
