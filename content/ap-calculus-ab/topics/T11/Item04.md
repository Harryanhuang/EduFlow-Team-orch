---
id: T11-Item04
difficulty: F
calculator: no-calc
type: frq
---
Let $f(x) = \sqrt{x} + x$ for $x \geq 0$.

(a) Show that $f$ is invertible on its domain.
(b) Find the value of $(f^{-1})'(2)$.

## Answer
(a) $f'(x) = \frac{1}{2\sqrt{x}} + 1 > 0$ for all $x > 0$, so $f$ is strictly increasing and therefore one-to-one, hence invertible.
(b) Since $f(1) = \sqrt{1} + 1 = 2$, we have $(f^{-1})'(2) = \frac{1}{f'(1)} = \frac{1}{\frac{1}{2} + 1} = \frac{2}{3}$.

## Explanation
To show invertibility, verify $f'(x) > 0$ on the domain, which guarantees strict monotonicity. For part (b), apply $(f^{-1})'(b) = 1/f'(a)$ where $f(a) = b$. By inspection, $f(1) = 2$, so $a = 1$ and $f'(1) = \frac{1}{2} + 1 = \frac{3}{2}$, giving $(f^{-1})'(2) = \frac{2}{3}$.
