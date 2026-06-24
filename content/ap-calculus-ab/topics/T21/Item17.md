---
id: T21-Item17
difficulty: C
calculator: no-calc
type: frq
---
**Part A:** Evaluate \(\displaystyle \int \frac{5x^2 + 4x - 3}{x^3}\,dx\). Show all work.

**Part B:** Find the exact value of \(\displaystyle \int_0^{\pi/2} \sin^2(x)\,dx\). Show all work.

---

## Answer

**Part A:**

Rewrite: \(\frac{5x^2 + 4x - 3}{x^3} = \frac{5x^2}{x^3} + \frac{4x}{x^3} - \frac{3}{x^3} = 5x^{-1} + 4x^{-2} - 3x^{-3}\)

\[
\int \left(5x^{-1} + 4x^{-2} - 3x^{-3}\right)dx = 5\ln|x| + 4(-x^{-1}) - 3\left(\frac{x^{-2}}{-2}\right) + C
\]

\[
= 5\ln|x| - \frac{4}{x} + \frac{3}{2x^2} + C
\]

**Part B:**

Use the power-reduction identity: \(\sin^2(x) = \frac{1 - \cos(2x)}{2}\)

\[
\int_0^{\pi/2} \sin^2(x)\,dx = \int_0^{\pi/2} \frac{1 - \cos(2x)}{2}\,dx = \frac{1}{2}\int_0^{\pi/2} (1 - \cos(2x))\,dx
\]

\[
= \frac{1}{2}\left[x - \frac{\sin(2x)}{2}\right]_0^{\pi/2} = \frac{1}{2}\left[\frac{\pi}{2} - \frac{\sin(\pi)}{2} - 0\right] = \frac{1}{2}\cdot\frac{\pi}{2} = \frac{\pi}{4}
\]
