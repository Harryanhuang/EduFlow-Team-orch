---
id: T02-Item16
difficulty: C
calculator: no-calc
type: frq
---
Let $f(x) = \begin{cases} \dfrac{x^2 - ax}{x - 2} & \text{if } x \neq 2 \\ b & \text{if } x = 2 \end{cases}$

Find the values of $a$ and $b$ such that $\displaystyle \lim_{x \to 2} f(x)$ exists and $f$ is continuous at $x = 2$.

## Answer
$a = 2$, $b = 2$

## Explanation
For the limit to exist, the numerator must equal $0$ when $x = 2$:

$2^2 - 2a = 0$
$4 - 2a = 0$
$a = 2$

With $a = 2$: $x^2 - 2x = x(x - 2)$

$$\lim_{x \to 2} \frac{x(x - 2)}{x - 2} = \lim_{x \to 2} x = 2$$

For continuity at $x = 2$, we need $f(2) = \lim_{x \to 2} f(x)$, so $b = 2$.
