---
id: T07-Item14
difficulty: C
calculator: no-calc
type: frq
---
Find all values of $x$ in the interval $[0, 2\pi]$ where the tangent line to $y = x \sin x$ is horizontal. Give exact answers where possible.

## Answer
$f'(x) = \sin x + x \cos x$. Setting $f'(x) = 0$:

$\sin x + x \cos x = 0$

At $x = 0$: $\sin 0 + 0 \cdot \cos 0 = 0 + 0 = 0$. So $x = 0$ is one solution.

For $x \neq 0$ where $\cos x \neq 0$: divide both sides by $\cos x$:

$\tan x = -x$

This transcendental equation has no closed-form solutions. The graph of $y = \tan x$ and $y = -x$ intersect once in $(\frac{\pi}{2}, \pi)$ (approximately $x \approx 2.0288$) and once in $(\frac{3\pi}{2}, 2\pi)$ (approximately $x \approx 4.9132$).

Exact answer: $x = 0$, plus the two solutions of $\tan x = -x$ in the given interval.

## Explanation
This problem requires the product rule, setting the derivative to zero, recognizing a transcendental equation, and reasoning about the number and approximate locations of solutions within a bounded interval.
