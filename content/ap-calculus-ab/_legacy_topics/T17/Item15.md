---
id: T17-Item15
difficulty: C
calculator: no-calc
type: frq
---
Let $f(x) = x^{4/3} - 4x^{1/3}$.

**(a)** Find $f'(x)$ and $f''(x)$. Note any values where $f'$, $f''$, or $f$ are not defined.

**(b)** Find all critical points of $f$ and classify each using the Second Derivative Test or the First Derivative Test.

**(c)** Find all points of inflection of $f$. Justify your answer.

**(d)** Sketch the graph of $f$ showing all relevant features: local extrema, points of inflection, and end behavior.

## Answer
**(a)**
$f(x) = x^{4/3} - 4x^{1/3}$

$f'(x) = \frac{4}{3}x^{1/3} - \frac{4}{3}x^{-2/3} = \frac{4}{3}\left(x^{1/3} - \frac{1}{x^{2/3}}\right) = \frac{4}{3}\cdot\frac{x - 1}{x^{2/3}}$

Domain of $f$: all real numbers (since fractional exponents with odd denominators allow negative bases)
Domain of $f'$: all $x \neq 0$
Domain of $f''$: all $x \neq 0$

$f''(x) = \frac{4}{9}x^{-2/3} + \frac{8}{9}x^{-5/3} = \frac{4}{9x^{2/3}} + \frac{8}{9x^{5/3}} = \frac{4(x + 2)}{9x^{5/3}}$

**(b)**
Critical points ($f' = 0$ or undefined):
- $f'(x) = 0$ when $x - 1 = 0$, so $x = 1$
- $f'(x)$ undefined at $x = 0$

At $x = 0$: Check using First Derivative Test.
- For $x < 0$: $f'(x) = \frac{4(x-1)}{3x^{2/3}}$. With $x < 0$, $x^{2/3} > 0$, so sign depends on $(x-1)$ which is negative. So $f'(x) < 0$ for $x < 0$.
- For $0 < x < 1$: $x^{2/3} > 0$, $(x-1) < 0$, so $f'(x) < 0$.

No sign change → not a local extremum.

At $x = 1$: $f''(1) = \frac{4(3)}{9} = \frac{4}{3} > 0$ → local minimum by Second Derivative Test.

**(c)**
Set $f''(x) = 0$: $\frac{4(x + 2)}{9x^{5/3}} = 0$, so $x + 2 = 0$, giving $x = -2$.

Also check $x = 0$ where $f''$ is undefined.

Test sign of $f''$:
- For $x < -2$: $x + 2 < 0$, $x^{5/3} < 0$ (negative base), so $\frac{negative}{negative} > 0$. $f'' > 0$ (concave up)
- For $-2 < x < 0$: $x + 2 > 0$, $x^{5/3} < 0$, so $\frac{positive}{negative} < 0$. $f'' < 0$ (concave down)
- For $x > 0$: $x + 2 > 0$, $x^{5/3} > 0$, so $f'' > 0$ (concave up)

Sign changes at $x = -2$ and $x = 0$, so both are points of inflection.

**(d)**
Key features:
- Point of inflection at $(-2, f(-2)) = (-2, (-2)^{4/3} - 4(-2)^{1/3}) = (-2, 3.52...)$
- Point of inflection at $(0, f(0)) = (0, 0)$
- Local minimum at $(1, f(1)) = (1, -3)$
- Concave up: $(-\infty, -2) \cup (0, \infty)$
- Concave down: $(-2, 0)$

## Explanation
This problem requires careful handling of non-integer exponents, domain analysis, and combining both derivative tests.
