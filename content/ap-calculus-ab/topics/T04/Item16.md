---
id: T04-Item16
difficulty: C
calculator: no-calc
type: frq
---
Let $f(x) = \dfrac{2x^2 + 3x - 5}{x^2 - 4}$.

(a) Find all vertical asymptotes and evaluate the one-sided limits at each.
(b) Find all horizontal asymptotes.
(c) For what value(s) of $x$, if any, does $f(x) = 0$? Use the IVT to determine whether $f$ must have a zero on the interval $(0, 3)$.

## Answer
(a) Factor: $f(x) = \dfrac{(2x + 5)(x - 1)}{(x - 2)(x + 2)}$. Vertical asymptotes at $x = 2$ and $x = -2$ (numerator is nonzero at both: at $x=2$, numerator $= 8 + 6 - 5 = 9$; at $x=-2$, numerator $= 8 - 6 - 5 = -3$).

One-sided limits:
- $\lim_{x \to 2^{+}} f(x)$: numerator $\to 9 > 0$, denominator $(x-2)(x+2) \to 0^{+} \cdot 4 = 0^{+}$, so limit is $+\infty$.
- $\lim_{x \to 2^{-}} f(x)$: numerator $\to 9 > 0$, denominator $\to 0^{-} \cdot 4 = 0^{-}$, so limit is $-\infty$.
- $\lim_{x \to -2^{+}} f(x)$: numerator $\to -3 < 0$, denominator $\to 0^{+} \cdot 0 = 0^{+}$ (since $(x+2) \to 0^{+}$ and $(x-2) \to -4$), so denominator $\to 0^{-}$. Thus limit is $(-3)/(0^{-}) = +\infty$.

Wait, let me be more careful: as $x \to -2^{+}$, $(x+2) \to 0^{+}$ and $(x-2) \to -4$, so $(x-2)(x+2) \to -4 \cdot 0^{+} = 0^{-}$. Numerator $\to -3$. So $(-3)/(0^{-}) = +\infty$.

- $\lim_{x \to -2^{-}} f(x)$: $(x+2) \to 0^{-}$, $(x-2) \to -4$, so $(x-2)(x+2) \to -4 \cdot 0^{-} = 0^{+}$. Numerator $\to -3$. So $(-3)/(0^{+}) = -\infty$.

(b) $\displaystyle \lim_{x \to \pm\infty} \frac{2x^2 + 3x - 5}{x^2 - 4} = \frac{2}{1} = 2$. Horizontal asymptote: $y = 2$.

(c) $f(x) = 0$ when numerator $= 0$: $(2x+5)(x-1) = 0$, so $x = -\frac{5}{2}$ or $x = 1$. 

On $(0, 3)$: $f(0) = \frac{-5}{-4} = \frac{5}{4} > 0$ and $f(3) = \frac{18 + 9 - 5}{9 - 4} = \frac{22}{5} > 0$. Since both $f(0)$ and $f(3)$ are positive, IVT does not guarantee a zero on $(0, 3)$. However, we know $x = 1$ is a zero (from part c). Note: $f$ has a vertical asymptote at $x = 2$, so $f$ is NOT continuous on $[0, 3]$. IVT does not apply on $[0, 3]$ because of the discontinuity at $x = 2$. On $[0, 1]$, $f$ is continuous, $f(0) = 5/4 > 0$, $f(1) = 0$, so $x = 1$ is a root (trivially, since $f(1) = 0$ directly).
