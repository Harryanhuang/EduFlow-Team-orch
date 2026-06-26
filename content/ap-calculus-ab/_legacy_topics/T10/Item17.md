---
id: T10-Item17
difficulty: C
calculator: calc
type: frq
---

Find d²y/dx² of the curve x³ + y³ = 3xy at the point (3/2, 3/2).

## Answer
d²y/dx² = -32/3

## Explanation
First, find dy/dx: differentiate implicitly: 3x² + 3y²(dy/dx) = 3y + 3x(dy/dx). Solve: dy/dx = (y - x²)/(y² - x). At (3/2, 3/2): dy/dx = (3/2 - 9/4)/(9/4 - 3/2) = (-3/4)/(3/4) = -1.

Now find d²y/dx² using the quotient rule:
d²y/dx² = d/dx[(y - x²)/(y² - x)] = [(y² - x)(dy/dx - 2x) - (y - x²)(2y·dy/dx - 1)] / (y² - x)²

At (3/2, 3/2) with dy/dx = -1:
- (y² - x) = 9/4 - 3/2 = 3/4
- (dy/dx - 2x) = -1 - 3 = -4
- (y - x²) = 3/2 - 9/4 = -3/4
- (2y·dy/dx - 1) = 2(3/2)(-1) - 1 = -4

Numerator = (3/4)(-4) - (-3/4)(-4) = -3 - 3 = -6
Denominator = (3/4)² = 9/16

d²y/dx² = -6 ÷ (9/16) = -96/9 = -32/3
