---
id: T16-Item16
difficulty: C
calculator: calc
type: frq
---
Let $f(x) = \frac{\ln x}{x^2}$ for $x > 0$.

(a) Find $f'(x)$ using the quotient rule.
(b) Find all critical points of $f$.
(c) Determine the intervals on which $f$ is increasing and decreasing.
(d) Find all local extrema using the First Derivative Test.
(e) Find the $x$-coordinate of the absolute maximum of $f$ on the interval $[1, e]$.

## Answer
(a) $f'(x) = \frac{1 - 2\ln x}{x^3}$.
(b) Critical point: $x = \sqrt{e}$.
(c) Increasing on $(0, \sqrt{e})$; decreasing on $(\sqrt{e}, \infty)$.
(d) Local maximum at $x = \sqrt{e}$.
(e) Absolute maximum on $[1, e]$ occurs at $x = \sqrt{e}$ (approximately 1.6487).

## Explanation
(a) Quotient rule: $f'(x) = \frac{x^2 \cdot \frac{1}{x} - \ln x \cdot 2x}{x^4} = \frac{x - 2x\ln x}{x^4} = \frac{1 - 2\ln x}{x^3}$.
(b) Set $f'(x) = 0$: $\frac{1 - 2\ln x}{x^3} = 0$ gives $1 - 2\ln x = 0$, so $\ln x = \frac{1}{2}$, and $x = e^{1/2} = \sqrt{e}$.
(c) For $0 < x < \sqrt{e}$, $\ln x < \frac{1}{2}$, so $1 - 2\ln x > 0$ and $f'(x) > 0$: increasing. For $x > \sqrt{e}$, $f'(x) < 0$: decreasing.
(d) $f'$ changes from $+$ to $-$ at $x = \sqrt{e}$, so local maximum.
(e) Evaluate at $x = 1$: $f(1) = 0$; at $x = \sqrt{e}$: $f(\sqrt{e}) = \frac{\ln(\sqrt{e})}{e} = \frac{1/2}{e} = \frac{1}{2e}$; at $x = e$: $f(e) = \frac{1}{e^2}$. The maximum is $\frac{1}{2e}$ at $x = \sqrt{e}$.
