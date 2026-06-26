---
id: T16-Item14
difficulty: C
calculator: calc
type: frq
---
Let $f(x) = e^{x^2 - 4x}$.

(a) Find $f'(x)$.
(b) Find all critical points of $f$.
(c) Determine the intervals on which $f$ is increasing and decreasing.
(d) Find all local extrema using the First Derivative Test.
(e) Find the absolute minimum value of $f$ on the interval $[0, 4]$.

## Answer
(a) $f'(x) = (2x - 4)e^{x^2 - 4x}$.
(b) Critical point: $x = 2$.
(c) Decreasing on $(-\infty, 2)$; increasing on $(2, \infty)$.
(d) Local minimum at $x = 2$.
(e) Absolute minimum: $f(2) = e^{-4} = \frac{1}{e^4}$ at $x = 2$.

## Explanation
(a) Chain rule: $f'(x) = e^{x^2-4x} \cdot (2x - 4) = (2x - 4)e^{x^2 - 4x}$.
(b) Set $f'(x) = 0$: $(2x - 4)e^{x^2-4x} = 0$. Since $e^{x^2-4x} > 0$ always, we need $2x - 4 = 0$, so $x = 2$.
(c) Sign of $f'$: For $x < 2$, $2x - 4 < 0$, so $f'(x) < 0$ (decreasing). For $x > 2$, $2x - 4 > 0$, so $f'(x) > 0$ (increasing).
(d) At $x = 2$, $f'$ changes from negative to positive, so local minimum.
(e) On $[0, 4]$, check $x = 0, 2, 4$: $f(0) = e^0 = 1$, $f(2) = e^{-4} \approx 0.018$, $f(4) = e^0 = 1$. Absolute minimum is $e^{-4}$ at $x = 2$.
