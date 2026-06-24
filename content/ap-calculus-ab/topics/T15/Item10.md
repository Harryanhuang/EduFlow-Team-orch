---
id: T15-Item10
difficulty: S
calculator: no-calc
type: mcq
---
A train travels along a straight track. At time $t = 0$ the train is at position $s = 0$, and at time $t = 2$ hours it is at position $s = 120$ miles. Which of the following must be true?

## Options
A) There is some instant $t$ in $(0, 2)$ when the train's velocity is exactly 60 mph.
B) The train's velocity is always 60 mph.
C) There is some instant $t$ in $(0, 2)$ when the train's acceleration is zero.
D) Both A and C

## Answer
A) There is some instant $t$ in $(0, 2)$ when the train's velocity is exactly 60 mph.

## Explanation
This is a direct application of the Mean Value Theorem (MVT) for integrals (average value form). If the train's position function $s(t)$ is continuous on $[0, 2]$ and differentiable on $(0, 2)$, then MVT guarantees a value $c$ in $(0, 2)$ such that:
$s'(c) = (s(2) - s(0))/(2 - 0) = (120 - 0)/2 = 60$ mph.
The velocity at some instant must be exactly 60 mph. Option C ("acceleration is zero") is not guaranteed by MVT. Option D is therefore incorrect.
