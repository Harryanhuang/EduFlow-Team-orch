---
id: T02-Item10
difficulty: S
calculator: no-calc
type: frq
---
Evaluate the limit:

$\displaystyle \lim_{x \to 1} \left(\frac{1}{x - 1} - \frac{2}{x^2 - 1}\right)$

## Answer
$\dfrac{1}{2}$

## Explanation
Factor $x^2 - 1 = (x - 1)(x + 1)$ and find a common denominator:

$$\frac{1}{x - 1} - \frac{2}{(x - 1)(x + 1)} = \frac{x + 1}{(x - 1)(x + 1)} - \frac{2}{(x - 1)(x + 1)} = \frac{x + 1 - 2}{(x - 1)(x + 1)}$$

$$= \frac{x - 1}{(x - 1)(x + 1)}$$

For $x \neq 1$:
$$= \frac{1}{x + 1}$$

$$\lim_{x \to 1} \frac{1}{x + 1} = \frac{1}{2}$$
