---
id: T17-Item08
difficulty: S
calculator: no-calc
type: mcq
---
Let $f(x) = x^4 - 4x^3$. Which of the following are the $x$-coordinates of all points of inflection of $f$?

A) $x = 0$ only
B) $x = 2$ only
C) $x = 0$ and $x = 2$
D) No points of inflection

## Answer
C

## Explanation
Differentiate twice: $f'(x) = 4x^3 - 12x^2$ and $f''(x) = 12x^2 - 24x = 12x(x - 2)$.

Set $f''(x) = 0$: $x = 0$ or $x = 2$. Test the sign of $f''$ on each interval:
- For $x < 0$ (e.g. $x = -1$): $12(-1)(-3) = 36 > 0$, concave up.
- For $0 < x < 2$ (e.g. $x = 1$): $12(1)(-1) = -12 < 0$, concave down.
- For $x > 2$ (e.g. $x = 3$): $12(3)(1) = 36 > 0$, concave up.

Concavity changes at both $x = 0$ and $x = 2$, so both are points of inflection.
