---
id: T24-Item14
difficulty: C
calculator: calc
type: frq
---
A particle moves along a line with velocity v(t) = t squared minus 4t + 3, where v is in meters per second and t is in seconds.

(a) Find all times t in [0, 5] when the particle is moving to the right.
(b) Find the total distance traveled by the particle from t = 0 to t = 5.
(c) A second particle moves with velocity w(t) = 5 minus t. Both particles start at x = 0 at t = 0. Find the time(s) when the particles are at the same position after t = 0.

## Answer
(a) Moving right when v(t) > 0: t squared minus 4t + 3 > 0 factors as (t minus 1)(t minus 3) > 0. Critical points t = 1, 3. Using sign analysis: positive on (0,1) and (3,5], negative on (1,3). At t = 0, v = 3 > 0. So moving right for 0 < t < 1 and 3 < t is less than or equal to 5.

(b) Total distance = integral from 0 to 5 of |v(t)| dt.
v(t) changes sign at t = 1 and t = 3.
Integral from 0 to 1 of (t squared minus 4t + 3) dt = [t cubed/3 minus 2t squared + 3t] from 0 to 1 = 1/3 minus 2 + 3 = 4/3.
Integral from 1 to 3 of negative (t squared minus 4t + 3) dt = negative [t cubed/3 minus 2t squared + 3t] from 1 to 3 = negative [(9 minus 18 + 9) minus (1/3 minus 2 + 3)] = negative [0 minus 4/3] = 4/3.
Integral from 3 to 5 of (t squared minus 4t + 3) dt = [t cubed/3 minus 2t squared + 3t] from 3 to 5 = (125/3 minus 50 + 15) minus (27/3 minus 18 + 9) = (125/3 minus 35) minus 0 = 125/3 minus 35 = (125 minus 105)/3 = 20/3.
Total = 4/3 + 4/3 + 20/3 = 28/3.

(c) Particle 1: x1(t) = integral of v(t) dt = integral of (t squared minus 4t + 3) dt = t cubed/3 minus 2t squared + 3t + C. With x1(0) = 0, C = 0. So x1(t) = t cubed/3 minus 2t squared + 3t.
Particle 2: x2(t) = integral of w(t) dt = integral of (5 minus t) dt = 5t minus t squared/2 + D. With x2(0) = 0, D = 0. So x2(t) = 5t minus t squared/2.
Set equal: t cubed/3 minus 2t squared + 3t = 5t minus t squared/2.
Simplify: t cubed/3 minus 2t squared + 3t minus 5t + t squared/2 = 0 implies t cubed/3 minus (3/2)t squared minus 2t = 0.
Multiply by 6: 2t cubed minus 9t squared minus 12t = 0 implies t(2t squared minus 9t minus 12) = 0.
t = 0 or 2t squared minus 9t minus 12 = 0.
Solve quadratic: t = [9 plus or minus square root of (81 + 96)] / (4) = [9 plus or minus square root of 177] / 4.
Since t > 0, t = [9 + square root of 177] / 4 (approximately 5.575 seconds).
