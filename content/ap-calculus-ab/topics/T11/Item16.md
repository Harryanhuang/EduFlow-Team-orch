---
id: T11-Item16
difficulty: C
calculator: no-calc
type: frq
---
Let $f(x) = x^5 + 3x - 2$.

(a) Prove that $f$ has an inverse function.
(b) Find $(f^{-1})'(2)$.
(c) Find $(f^{-1})''(2)$ using implicit differentiation or the second derivative formula for inverse functions.

## Answer
(a) $f'(x) = 5x^4 + 3 > 0$ for all $x$, so $f$ is strictly increasing, hence one-to-one and invertible.
(b) $f(1) = 1 + 3 - 2 = 2$, so $(f^{-1})'(2) = \frac{1}{f'(1)} = \frac{1}{8}$.
(c) $(f^{-1})''(2) = -\frac{f''(1)}{[f'(1)]^3} = -\frac{20}{512} = -\frac{5}{128}$.

## Explanation
Part (a): $f'(x) = 5x^4 + 3 > 0$ everywhere, so $f$ is strictly increasing and invertible. Part (b): By inspection $f(1) = 2$, so $(f^{-1})'(2) = 1/f'(1) = 1/(5 + 3) = 1/8$. Part (c): The formula $(f^{-1})''(b) = -\frac{f''(a)}{[f'(a)]^3}$ where $f(a) = b$. We have $f''(x) = 20x^3$, so $f''(1) = 20$ and $(f^{-1})''(2) = -\frac{20}{8^3} = -\frac{20}{512} = -\frac{5}{128}$.
