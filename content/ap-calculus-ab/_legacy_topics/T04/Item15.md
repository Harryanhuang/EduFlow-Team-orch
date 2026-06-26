---
id: T04-Item15
difficulty: C
calculator: no-calc
type: frq
---
Let $f(x) = \dfrac{x^3 - 2x^2 - 5x + 6}{x^2 - 1}$.

(a) Find all vertical asymptotes of $f$.
(b) Evaluate $\displaystyle \lim_{x \to \infty} f(x)$ and $\displaystyle \lim_{x \to -\infty} f(x)$.
(c) Does $f$ have a slant (oblique) asymptote? If so, find its equation.

## Answer
(a) Factor: numerator $= (x-1)(x^2 - x - 6) = (x-1)(x-3)(x+2)$. Denominator $= (x-1)(x+1)$. So
$$f(x) = \frac{(x-1)(x-3)(x+2)}{(x-1)(x+1)} = \frac{(x-3)(x+2)}{x+1} \text{ for } x \neq 1.$$
At $x = 1$, the $(x-1)$ factor cancels — removable discontinuity. At $x = -1$, the denominator is zero and the numerator is $(-4)(1) = -4 \neq 0$. Thus $x = -1$ is the only vertical asymptote.

(b) After simplification, $f(x) = \dfrac{x^2 - x - 6}{x + 1}$. By polynomial long division, $x^2 - x - 6 = (x+1)(x - 2) - 4$, so
$$f(x) = x - 2 - \frac{4}{x+1}.$$
Since the degree of the numerator exceeds that of the denominator, the function grows without bound:
$$\lim_{x \to \infty} f(x) = \infty \quad \text{and} \quad \lim_{x \to -\infty} f(x) = -\infty.$$

(c) Yes. From the division above, $f(x) = x - 2 - \frac{4}{x+1}$. As $x \to \pm\infty$, the term $\frac{4}{x+1} \to 0$, so $f(x) - (x - 2) \to 0$. The slant asymptote is $y = x - 2$.
