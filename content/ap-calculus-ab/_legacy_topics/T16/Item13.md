---
id: T16-Item13
difficulty: C
calculator: calc
type: frq
---
Let $f(x) = x^3 - 3x^2 - 9x + 4$.

(a) Find $f'(x)$.
(b) Find all critical points of $f$.
(c) Determine the intervals on which $f$ is increasing and decreasing.
(d) Find all local extrema using the First Derivative Test.
(e) Find the absolute maximum and minimum values of $f$ on the closed interval $[-2, 4]$.

## Answer
(a) $f'(x) = 3x^2 - 6x - 9 = 3(x^2 - 2x - 3) = 3(x + 1)(x - 3)$.
(b) Critical points: $x = -1$ and $x = 3$.
(c) Increasing on $(-\infty, -1) \cup (3, \infty)$; decreasing on $(-1, 3)$.
(d) Local maximum at $x = -1$; local minimum at $x = 3$.
(e) Absolute maximum: $f(-1) = 9$ at $x = -1$; absolute minimum: $f(-2) = 6$ at $x = -2$.

## Explanation
(a) $f'(x) = 3x^2 - 6x - 9$.
(b) Set $f'(x) = 0$: $3(x + 1)(x - 3) = 0$, so $x = -1$ and $x = 3$.
(c) Sign chart: For $x < -1$, both factors $(x+1)$ and $(x-3)$ are negative, product positive; increasing. For $-1 < x < 3$, $(x+1) > 0$ and $(x-3) < 0$, product negative; decreasing. For $x > 3$, both positive; increasing.
(d) At $x = -1$, $f'$ changes from $+$ to $-$: local maximum. At $x = 3$, $f'$ changes from $-$ to $+$: local minimum.
(e) Evaluate at endpoints and critical points in $[-2, 4]$: $f(-2) = -8 - 12 + 18 + 4 = 2$, $f(-1) = -1 - 3 + 9 + 4 = 9$, $f(3) = 27 - 27 - 27 + 4 = -23$, $f(4) = 64 - 48 - 36 + 4 = -16$. Absolute maximum is 9 at $x = -1$; absolute minimum is $-23$ at $x = 3$.
