---
id: T02-Item01
difficulty: F
calculator: no-calc
type: mcq
---
Evaluate the limit:

$\displaystyle \lim_{x \to 2} \frac{x^2 - 4}{x - 2}$

## Options
A) 0
B) 2
C) 4
D) Does not exist

## Answer
C) 4

## Explanation
Factor the numerator as a difference of squares: $x^2 - 4 = (x + 2)(x - 2)$.

For $x \neq 2$:
$$\frac{x^2 - 4}{x - 2} = \frac{(x + 2)(x - 2)}{x - 2} = x + 2$$

Since $\lim_{x \to 2} (x + 2)$ is a polynomial, use direct substitution:
$$\lim_{x \to 2} (x + 2) = 2 + 2 = 4$$

The removable discontinuity at $x = 2$ does not affect the limit.
