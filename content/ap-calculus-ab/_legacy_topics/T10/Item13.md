---
id: T10-Item13
difficulty: C
calculator: no-calc
type: frq
---

Given the equation y * e^x = x * e^y, find dy/dx at the point (0, 0).

## Answer
dy/dx = 1

## Explanation
Differentiate both sides implicitly using the product rule.

Left side: d/dx[y * e^x] = (dy/dx) * e^x + y * e^x
Right side: d/dx[x * e^y] = e^y + x * e^y * (dy/dx)

Set equal: (dy/dx) * e^x + y * e^x = e^y + x * e^y * (dy/dx)
(dy/dx) * e^x - x * e^y * (dy/dx) = e^y - y * e^x
dy/dx * (e^x - x * e^y) = e^y - y * e^x
dy/dx = (e^y - y * e^x) / (e^x - x * e^y)

At (0, 0): dy/dx = (e^0 - 0) / (e^0 - 0) = 1/1 = 1.
