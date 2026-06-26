---
id: T09-Item11
difficulty: C
calculator: no-calc
type: frq
---
The table below gives selected values of differentiable functions f, g, and h and their derivatives.

| x  | f(x) | f'(x) | g(x) | g'(x) | h(x) | h'(x) |
|----|------|-------|------|-------|------|-------|
| 0  |  2   |   7   |  3   |   5   |  1   |   6   |
| 1  |  5   |   8   |  2   |   3   |  3   |   5   |
| 2  |  9   |   1   |  8   |   2   |  4   |   7   |
| 3  |  6   |   4   |  5   |   6   |  1   |   2   |
| 4  |  7   |   3   |  1   |   4   |  2   |   8   |
| 5  |  3   |   9   |  6   |   7   |  6   |   1   |
| 6  |  8   |   2   |  9   |   5   |  5   |   3   |
| 8  | 10   |   1   |  —   |   —   |  —   |   —   |
| 9  |  4   |   6   |  —   |   —   |  —   |   —   |

**(a)** Let F(x) = f(g(h(x))). Find F'(1). Show the chain of reasoning by identifying each intermediate value from the table.

**(b)** Let G(x) = [f(g(h(x)))]². Find G'(0).

**(c)** Let K(x) = g(f(x)). Find K'(4) if possible. If not possible, explain why.

## Answer

**(a)** By the chain rule for a three-function composition:

F'(x) = f'(g(h(x))) · g'(h(x)) · h'(x)

At x = 1, trace through each layer:
- h(1) = 3, and h'(1) = 5
- g(h(1)) = g(3) = 5, and g'(h(1)) = g'(3) = 6
- f'(g(h(1))) = f'(5) = 9

**F'(1) = 9 · 6 · 5 = 270**

**(b)** G(x) = [f(g(h(x)))]². Using the power rule combined with the chain rule:

G'(x) = 2 · f(g(h(x))) · f'(g(h(x))) · g'(h(x)) · h'(x)

At x = 0, trace through each layer:
- h(0) = 1, and h'(0) = 6
- g(h(0)) = g(1) = 2, and g'(h(0)) = g'(1) = 3
- f(g(h(0))) = f(2) = 9, and f'(g(h(0))) = f'(2) = 1

**G'(0) = 2 · 9 · 1 · 3 · 6 = 324**

**(c)** K(x) = g(f(x)). By the chain rule:

K'(x) = g'(f(x)) · f'(x)

At x = 4:
- f(4) = 7, so we need g'(7)
- f'(4) = 3

The table does not contain g'(7). **K'(4) cannot be determined** from the given information because the derivative of the outer function g at the point f(4) = 7 is not provided in the table.
