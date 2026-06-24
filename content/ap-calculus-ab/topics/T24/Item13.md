---
id: T24-Item13
difficulty: C
calculator: calc
type: frq
---
Let R be the region in the first quadrant bounded by the curves y = x squared and y = 8 minus x squared.

(a) Find the area of region R.
(b) Set up, but do not evaluate, the integral that gives the volume of the solid generated when R is revolved about the x-axis using the washer method.
(c) The region R is the base of a solid. For this solid, each cross-section perpendicular to the x-axis is a semicircle whose diameter lies in the base. Find the volume of this solid.

## Answer
(a) Intersection: x squared = 8 minus x squared implies 2x squared = 8 implies x squared = 4 implies x = 2 (in first quadrant). Area = integral from 0 to 2 of [(8 minus x squared) minus x squared] dx = integral of (8 minus 2x squared) dx = [8x minus (2/3)x cubed] from 0 to 2 = 16 minus (2/3)(8) = 16 minus 16/3 = 32/3.

(b) Outer radius R(x) = 8 minus x squared (distance from x-axis to y = 8 minus x squared). Inner radius r(x) = x squared (distance from x-axis to y = x squared). Bounds: x from 0 to 2.
V = pi times integral from 0 to 2 of [(8 minus x squared) squared minus (x squared) squared] dx = pi times integral of [(64 minus 16x squared + x to the fourth) minus x to the fourth] dx = pi times integral from 0 to 2 of (64 minus 16x squared) dx.

(c) Cross-sections perpendicular to x-axis are semicircles with diameter in the base. The diameter is the vertical distance: d = (8 minus x squared) minus x squared = 8 minus 2x squared. Radius of semicircle: r = d/2 = 4 minus x squared. Area of semicircle: A = (1/2) pi r squared = (1/2) pi (4 minus x squared) squared.
V = integral from 0 to 2 of A(x) dx = (pi/2) times integral from 0 to 2 of (4 minus x squared) squared dx = (pi/2) times integral of (16 minus 8x squared + x to the fourth) dx = (pi/2)[16x minus (8/3)x cubed + x to the fifth/5] from 0 to 2 = (pi/2)[32 minus (8/3)(8) + (32)/5] = (pi/2)[32 minus 64/3 + 32/5] = (pi/2)[(480 minus 320 + 192)/15] = (pi/2)(352/15) = 176 pi / 15.
