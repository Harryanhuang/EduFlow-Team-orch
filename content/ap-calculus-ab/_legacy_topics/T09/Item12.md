---
id: T09-Item12
difficulty: C
calculator: no-calc
type: frq
---
Let y = f(u) where u = g(x). The following values are given:

f'(3) = 5, g(2) = 3, g'(2) = −4, f''(3) = 2, g''(2) = −3

**(a)** Find dy/dx at x = 2.

**(b)** Find d²y/dx² at x = 2. Show all steps in differentiating the composition twice.

Now consider a second composition: let z = p(q(x)), with the following additional values:

q(1) = 2, q'(1) = 3, q''(1) = 4, p(2) = 5, p'(2) = −2, p''(2) = 7

**(c)** Find d²z/dx² at x = 1.

**(d)** Compare your answers to parts (b) and (c). Which composition has the larger second derivative in magnitude? What does this tell you about the concavity of each composition at the given point?

## Answer

**(a)** By the chain rule:

dy/dx = f'(u) · du/dx = f'(g(x)) · g'(x)

At x = 2:
- g(2) = 3, so f'(g(2)) = f'(3) = 5
- g'(2) = −4

**dy/dx |_(x=2) = 5 · (−4) = −20**

**(b)** To find the second derivative, differentiate dy/dx = f'(g(x)) · g'(x) using the product rule:

d²y/dx² = d/dx[f'(g(x)) · g'(x)]
         = d/dx[f'(g(x))] · g'(x) + f'(g(x)) · d/dx[g'(x)]

Apply the chain rule to d/dx[f'(g(x))]:
- d/dx[f'(g(x))] = f''(g(x)) · g'(x)

Substitute:

d²y/dx² = f''(g(x)) · g'(x) · g'(x) + f'(g(x)) · g''(x)
         = f''(g(x)) · [g'(x)]² + f'(g(x)) · g''(x)

At x = 2:
- g(2) = 3
- f''(3) = 2
- [g'(2)]² = (−4)² = 16
- f'(3) = 5
- g''(2) = −3

d²y/dx² |_(x=2) = 2 · 16 + 5 · (−3) = 32 − 15 = **17**

**(c)** For z = p(q(x)), the second derivative follows the same formula:

d²z/dx² = p''(q(x)) · [q'(x)]² + p'(q(x)) · q''(x)

At x = 1:
- q(1) = 2
- p''(2) = 7
- [q'(1)]² = 3² = 9
- p'(q(1)) = p'(2) = −2
- q''(1) = 4

d²z/dx² |_(x=1) = 7 · 9 + (−2) · 4 = 63 − 8 = **55**

**(d)** Comparing the two second derivatives:
- |d²y/dx²| at x = 2: |17| = 17
- |d²z/dx²| at x = 1: |55| = 55

**The composition z = p(q(x)) has the larger second derivative in magnitude.**

Both second derivatives are positive (17 and 55), so both compositions are **concave up** at their respective points. The larger magnitude of d²z/dx² = 55 means that z = p(q(x)) is curving upward more sharply at x = 1 than y = f(g(x)) curves upward at x = 2. In other words, the rate of change of z is increasing faster than the rate of change of y at the respective points.
