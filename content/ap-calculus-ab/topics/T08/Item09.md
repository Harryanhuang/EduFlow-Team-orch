---
id: T08-Item09
difficulty: S
calculator: no-calc
type: frq
---
Find the derivative of y = arccos(3x). State the domain on which the derivative exists.

## Answer
dy/dx = -3/sqrt(1 - 9x^2), defined for -1/3 < x < 1/3

## Explanation
Outer: arccos(u), inner: u = 3x. d/dx[arccos(u)] = -1/sqrt(1 - u^2) * du/dx = -1/sqrt(1 - 9x^2) * 3 = -3/sqrt(1 - 9x^2).
The derivative exists when 1 - 9x^2 > 0, i.e., 9x^2 < 1, so |x| < 1/3.
