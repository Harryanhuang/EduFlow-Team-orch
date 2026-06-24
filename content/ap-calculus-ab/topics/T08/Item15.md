---
id: T08-Item15
difficulty: C
calculator: no-calc
type: frq
---
Let f(x) = arcsin(x) + arccos(x).

(a) Find f'(x).
(b) What does your answer to part (a) tell you about f(x)?
(c) Use a known value to determine the exact value of f(x) for all x in [-1, 1].

## Answer
(a) f'(x) = 1/sqrt(1 - x^2) + (-1/sqrt(1 - x^2)) = 0
(b) Since f'(x) = 0 for all x in (-1, 1), f(x) is constant on [-1, 1].
(c) f(0) = arcsin(0) + arccos(0) = 0 + pi/2 = pi/2. Therefore f(x) = pi/2 for all x in [-1, 1].

## Explanation
(a) Differentiate each term: d/dx[arcsin(x)] = 1/sqrt(1 - x^2) and d/dx[arccos(x)] = -1/sqrt(1 - x^2). These cancel to 0.
(b) A function with derivative 0 on an interval is constant on that interval.
(c) Evaluate at any convenient point: x = 0 gives arcsin(0) = 0 and arccos(0) = pi/2, so f(x) = pi/2 everywhere in the domain. This confirms the identity arcsin(x) + arccos(x) = pi/2.
