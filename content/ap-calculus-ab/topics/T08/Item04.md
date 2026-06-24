---
id: T08-Item04
difficulty: F
calculator: no-calc
type: mcq
---
What is d/dx[arcsin(x)]?

## Options
A) 1/sqrt(1 - x^2)
B) -1/sqrt(1 - x^2)
C) 1/(1 + x^2)
D) -1/(1 + x^2)

## Answer
A

## Explanation
The derivative of arcsin(x) is 1/sqrt(1 - x^2), for |x| < 1. This is a standard result derived via implicit differentiation: if y = arcsin(x), then sin(y) = x, so cos(y) * dy/dx = 1, so dy/dx = 1/cos(y) = 1/sqrt(1 - sin^2(y)) = 1/sqrt(1 - x^2).
