---
id: T07-Item16
difficulty: C
calculator: no-calc
type: frq
---
Let $f(x) = \dfrac{\sin x \cdot \cos x}{1 + \sin x}$.

(a) Find $f'(x)$.
(b) Find the equation of the tangent line to the graph of $f$ at $x = 0$.
(c) Is the function increasing or decreasing at $x = \frac{\pi}{6}$? Justify your answer.

## Answer
(a) Using the quotient rule with $u = \sin x \cos x = \frac{1}{2}\sin(2x)$ and $v = 1 + \sin x$:

$u' = \cos^2 x - \sin^2 x = \cos(2x)$, $v' = \cos x$.

$f'(x) = \frac{\cos(2x)(1 + \sin x) - \sin x \cos x \cdot \cos x}{(1 + \sin x)^2}$

$= \frac{\cos(2x) + \cos(2x)\sin x - \sin x \cos^2 x}{(1 + \sin x)^2}$

(b) At $x = 0$: $f(0) = \frac{0 \cdot 1}{1 + 0} = 0$.

$f'(0) = \frac{\cos(0)(1 + 0) - 0}{(1 + 0)^2} = \frac{1}{1} = 1$.

Tangent line: $y = x$.

(c) At $x = \frac{\pi}{6}$: $\sin(\frac{\pi}{6}) = \frac{1}{2}$, $\cos(\frac{\pi}{6}) = \frac{\sqrt{3}}{2}$, $\cos(\frac{\pi}{3}) = \frac{1}{2}$.

$f'(\frac{\pi}{6}) = \frac{\frac{1}{2}(1 + \frac{1}{2}) - \frac{1}{2} \cdot \frac{\sqrt{3}}{2} \cdot \frac{\sqrt{3}}{2}}{(1 + \frac{1}{2})^2} = \frac{\frac{3}{4} - \frac{3}{4}}{\frac{9}{4}} = 0$.

So the function has a horizontal tangent at $x = \frac{\pi}{6}$ (neither increasing nor decreasing).

## Explanation
This problem requires the product rule (for the numerator) combined with the quotient rule, then evaluation at specific points. Part (c) requires simplifying a nontrivial expression to determine the sign of $f'$.
