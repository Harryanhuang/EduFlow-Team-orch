---
id: T04-Item08
difficulty: S
calculator: no-calc
type: mcq
---
Evaluate $\displaystyle \lim_{x \to 1} \frac{x^2 - 3x + 2}{x^2 - 1}$.

## Options
A) $-\dfrac{1}{2}$
B) $0$
C) $\dfrac{1}{2}$
D) The limit does not exist.

## Answer
A

## Explanation
Direct substitution gives $\frac{0}{0}$, an indeterminate form. Factor:
$$\frac{x^2 - 3x + 2}{x^2 - 1} = \frac{(x-1)(x-2)}{(x-1)(x+1)} = \frac{x-2}{x+1} \quad \text{for } x \neq 1.$$
Now $\displaystyle \lim_{x \to 1} \frac{x-2}{x+1} = \frac{1-2}{1+1} = -\frac{1}{2}$.
