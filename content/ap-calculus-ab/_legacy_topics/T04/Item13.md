---
id: T04-Item13
difficulty: C
calculator: no-calc
type: frq
---
Let $f(x) = \dfrac{1}{x - 1} - \dfrac{1}{x + 2}$. Determine all vertical and horizontal asymptotes of the graph of $f$. Justify your answers using limits.

## Answer
Vertical asymptotes: $x = 1$ and $x = -2$. Horizontal asymptote: $y = 0$.

## Explanation
First combine: $f(x) = \dfrac{(x+2) - (x-1)}{(x-1)(x+2)} = \dfrac{3}{(x-1)(x+2)} = \dfrac{3}{x^2 + x - 2}$.

Vertical asymptotes: The denominator is zero at $x = 1$ and $x = -2$. At each, the numerator is 3 (nonzero), so:
- $\lim_{x \to 1^{\pm}} f(x) = \pm\infty$ (sign depends on direction), confirming $x = 1$ is a vertical asymptote.
- $\lim_{x \to -2^{\pm}} f(x) = \pm\infty$ (sign depends on direction), confirming $x = -2$ is a vertical asymptote.

Horizontal asymptote: The degree of the denominator (2) exceeds the degree of the numerator (0), so:
$$\lim_{x \to \infty} f(x) = \lim_{x \to -\infty} f(x) = 0.$$
Thus $y = 0$ is a horizontal asymptote.
