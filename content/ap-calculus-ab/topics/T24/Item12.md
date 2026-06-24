---
id: T24-Item12
difficulty: S
calculator: calc
type: frq
---
A particle moves along the x-axis with acceleration a(t) = 6t minus 2, initial velocity v(0) = 3, and initial position x(0) = negative 1.

(a) Find the velocity v(t) for t greater than or equal to 0.
(b) Find the position x(t) for t greater than or equal to 0.
(c) Find the total distance traveled by the particle from t = 0 to t = 3.

## Answer
(a) v(t) = integral of a(t) dt = integral of (6t minus 2) dt = 3t squared minus 2t + C. Using v(0) = 3, we get C = 3. So v(t) = 3t squared minus 2t + 3.

(b) x(t) = integral of v(t) dt = integral of (3t squared minus 2t + 3) dt = t cubed minus t squared + 3t + C. Using x(0) = negative 1, we get C = negative 1. So x(t) = t cubed minus t squared + 3t minus 1.

(c) Distance = integral from 0 to 3 of |v(t)| dt. Find when v(t) = 0: 3t squared minus 2t + 3 = 0. Discriminant: 4 minus 36 = negative 32, which is less than 0. So v(t) has no real roots and is always positive (since leading coefficient is positive). Therefore |v(t)| = v(t) for all t.
Distance = integral from 0 to 3 of (3t squared minus 2t + 3) dt = [t cubed minus t squared + 3t] from 0 to 3 = 27 minus 9 + 9 = 27.
