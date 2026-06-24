---
id: T24-Item15
difficulty: C
calculator: calc
type: frq
---
Let f be the function with f(0) = 0 and f prime(x) = 2x + 1 for all x.

(a) Find f(x) for all x.
(b) Let R be the region between the graph of y = f(x) and the line y = x for 0 is less than or equal to x is less than or equal to 2. Find the area of R.
(c) The region R is revolved around the line y = x to generate a solid. Set up the integral that gives the volume of this solid using the method of cylindrical shells. Do not evaluate the integral.

## Answer
(a) f(x) = integral of (2x + 1) dx = x squared + x + C. Using f(0) = 0, we get C = 0. So f(x) = x squared + x.

(b) f(x) minus x = x squared. Since x squared is greater than or equal to 0 for x in [0, 2], f(x) is greater than or equal to x on this interval.
Area = integral from 0 to 2 of [(x squared + x) minus x] dx = integral of x squared dx = [x cubed/3] from 0 to 2 = 8/3.

(c) For cylindrical shells about the line y = x, we use vertical slices. The shell radius is the perpendicular distance from the line y = x to the slice. For a vertical slice at position x, the radius r = |x squared + x minus x| / square root of 2 = x squared / square root of 2 (for x greater than or equal to 0).
The "height" of the shell (the length of the slice perpendicular to the axis) is the projection: the slice is vertical, so the height is the vertical length: (x squared + x) minus x = x squared.
However, for shells about a line at 45 degrees, we must account for the angle. The differential volume element is dV = (2 pi r)(h)(dr)... no.
Standard shell formula for rotation about a line: dV = 2 pi times (radius) times (area of slice).
Here, radius = distance from line y = x to the vertical slice at x = the perpendicular distance to the midpoint of the slice. Midpoint of the slice: y-coordinate = x + x squared/2. Distance = |x + x squared/2 minus x| / square root of 2 = x squared / (2 square root of 2).
dV = 2 pi times (x squared / (2 square root of 2)) times (x squared) dx = (pi / square root of 2) times x to the fourth dx.
V = (pi / square root of 2) times the integral from 0 to 2 of x to the fourth dx.
