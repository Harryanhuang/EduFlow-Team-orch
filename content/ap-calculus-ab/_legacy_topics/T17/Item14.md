---
id: T17-Item14
difficulty: C
calculator: no-calc
type: frq
---
Consider the function $f(x) = \sin x + \cos x$ on the interval $[0, 2\pi]$.

**(a)** Find $f''(x)$.

**(b)** Determine the points where $f$ has points of inflection on $[0, 2\pi]$. Justify your answer.

**(c)** Determine all local extrema of $f$ on $[0, 2\pi]$ using the Second Derivative Test.

**(d)** Describe the concavity of $f$ on $[0, 2\pi]$.

## Answer
**(a)**
$f'(x) = \cos x - \sin x$
$f''(x) = -\sin x - \cos x = -(\sin x + \cos x)$

**(b)**
Set $f''(x) = 0$: $-(\sin x + \cos x) = 0$, so $\sin x + \cos x = 0$

This gives $\tan x = -1$, so $x = \frac{3\pi}{4}, \frac{7\pi}{4}$ in $[0, 2\pi]$.

Test concavity change:
- At $x = \frac{3\pi}{4}$: $f''$ changes from negative to positive
- At $x = \frac{7\pi}{4}$: $f''$ changes from positive to negative

Both are points of inflection.

**(c)**
Set $f'(x) = 0$: $\cos x - \sin x = 0$, so $\cos x = \sin x$, giving $\tan x = 1$.

So $x = \frac{\pi}{4}, \frac{5\pi}{4}$ in $[0, 2\pi]$.

Using the Second Derivative Test:
- $f''(\frac{\pi}{4}) = -(\frac{\sqrt{2}}{2} + \frac{\sqrt{2}}{2}) = -\sqrt{2} < 0$ → local maximum
- $f''(\frac{5\pi}{4}) = -(-\frac{\sqrt{2}}{2} - \frac{\sqrt{2}}{2}) = \sqrt{2} > 0$ → local minimum

**(d)**
$f''(x) < 0$ (concave down) on $(\frac{3\pi}{4}, \frac{7\pi}{4})$
$f''(x) > 0$ (concave up) on $(0, \frac{3\pi}{4}) \cup (\frac{7\pi}{4}, 2\pi)$

## Explanation
This problem combines trigonometric derivatives with full concavity and extrema analysis on a closed interval.
