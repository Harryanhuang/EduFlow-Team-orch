---
id: T06-Item18
difficulty: C
calculator: no-calc
type: frq
---
A function f is defined by f(x) = ax^3 + bx^2 + cx + d, where a, b, c, d are constants. It is known that:
- f(0) = 1
- f'(0) = 2
- f has an inflection point at x = 1
- f'(1) = -1

(a) Find the values of a, b, c, and d.
(b) Write the equation of the tangent line to f at x = 1.
(c) On what intervals is f concave up? Concave down?

## Answer
(a) f(x) = ax^3 + bx^2 + cx + d, f'(x) = 3ax^2 + 2bx + c, f''(x) = 6ax + 2b.
f(0) = d = 1.
f'(0) = c = 2.
Inflection at x = 1: f''(1) = 6a + 2b = 0, so 3a + b = 0, meaning b = -3a.
f'(1) = 3a + 2b + c = 3a + 2(-3a) + 2 = 3a - 6a + 2 = -3a + 2 = -1, so -3a = -3, a = 1.
Then b = -3(1) = -3.
So f(x) = x^3 - 3x^2 + 2x + 1.

(b) f(1) = 1 - 3 + 2 + 1 = 1. f'(1) = -1. Tangent line: y - 1 = -1(x - 1), so y = -x + 2.

(c) f''(x) = 6x - 6 = 6(x - 1). f''(x) > 0 when x > 1 (concave up). f''(x) < 0 when x < 1 (concave down).

## Explanation
Using given conditions as a system of equations determines the coefficients. The inflection point occurs where f''(x) = 0, which partitions the domain into concave up and concave down regions.
