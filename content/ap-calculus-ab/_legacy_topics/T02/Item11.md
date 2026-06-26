---
id: T02-Item11
difficulty: S
calculator: no-calc
type: mcq
---
Let $f(x) = x^2 \sin\left(\dfrac{1}{x}\right)$ for $x \neq 0$. Evaluate:

$\displaystyle \lim_{x \to 0} f(x)$

## Options
A) $-1$
B) $0$
C) $1$
D) Does not exist

## Answer
B) 0

## Explanation
Apply the Squeeze Theorem. Since $-1 \leq \sin\left(\dfrac{1}{x}\right) \leq 1$ for all $x \neq 0$:

$$-x^2 \leq x^2 \sin\left(\frac{1}{x}\right) \leq x^2$$

Both bounding functions satisfy:
$$\lim_{x \to 0} (-x^2) = 0 \quad \text{and} \quad \lim_{x \to 0} x^2 = 0$$

By the Squeeze Theorem:
$$\lim_{x \to 0} x^2 \sin\left(\frac{1}{x}\right) = 0$$
